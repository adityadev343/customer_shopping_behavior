import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import re

from data_loader import load_data
from ai_assistant import (
    get_gemini_api_keys,
    call_gemini_with_fallback,
    get_schema_description,
    build_sql_generation_prompt,
    parse_sql_from_response,
    build_insight_prompt,
)

st.set_page_config(
    page_title="Shopping Behavior Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- DATA LOADING --------------------
df = load_data()

# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/shopping-cart--v1.png", width=80)
st.sidebar.title("🔍 Control Panel")
st.sidebar.markdown("---")

gender = st.sidebar.multiselect("Gender", options=df["gender"].unique(), default=df["gender"].unique())
age_group = st.sidebar.multiselect("Age Group", options=df["age_group"].unique(), default=df["age_group"].unique())
category = st.sidebar.multiselect("Category", options=df["category"].unique(), default=df["category"].unique())
season = st.sidebar.multiselect("Season", options=df["season"].unique(), default=df["season"].unique())
subscription = st.sidebar.multiselect("Subscription", options=df["subscription_status"].unique(), default=df["subscription_status"].unique())
discount = st.sidebar.multiselect("Discount Applied", options=df["discount_applied"].unique(), default=df["discount_applied"].unique())
promo = st.sidebar.multiselect("Promo Code Used", options=df["promo_code_used"].unique(), default=df["promo_code_used"].unique())
shipping = st.sidebar.multiselect("Shipping Type", options=df["shipping_type"].unique(), default=df["shipping_type"].unique())
location = st.sidebar.multiselect("Location (Top 20)", options=df["location"].value_counts().head(20).index.tolist(), default=[])

filtered_df = df[
    (df["gender"].isin(gender))
    & (df["age_group"].isin(age_group))
    & (df["category"].isin(category))
    & (df["season"].isin(season))
    & (df["subscription_status"].isin(subscription))
    & (df["discount_applied"].isin(discount))
    & (df["promo_code_used"].isin(promo))
    & (df["shipping_type"].isin(shipping))
]
if location:
    filtered_df = filtered_df[filtered_df["location"].isin(location)]

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please adjust your selections.")
    st.stop()

# -------------------- KPIs --------------------
total_revenue = filtered_df["purchase_amount"].sum()
total_transactions = len(filtered_df)
avg_order_value = filtered_df["purchase_amount"].mean()
unique_customers = filtered_df["customer_id"].nunique()
avg_clv_proxy = (filtered_df["purchase_amount"] * filtered_df["previous_purchases"]).mean()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
col2.metric("🧾 Transactions", f"{total_transactions:,}")
col3.metric("🛒 Avg Order Value", f"${avg_order_value:.2f}")
col4.metric("👥 Unique Customers", f"{unique_customers:,}")
col5.metric("📈 Avg CLV Proxy", f"${avg_clv_proxy:.2f}")

st.markdown("---")

# -------------------- TABS --------------------
tabs = st.tabs(
    [
        "📈 Revenue",
        "👥 Customer",
        "🏷️ Product",
        "🎯 Discount & Promo",
        "🚚 Shipping",
        "🌍 Geographic",
        "💳 Payment",
        "🧠 Advanced",
        "🤖 AI SQL Assistant",
    ]
)

# Chart key counter (ensures unique keys for Plotly)
if "_chart_counter" not in st.session_state:
    st.session_state["_chart_counter"] = 0

def next_key(base):
    st.session_state["_chart_counter"] += 1
    return f"{base}_{st.session_state['_chart_counter']}"

# ==================== REVENUE TAB ====================
with tabs[0]:
    st.subheader("Revenue Breakdown")
    colA, colB = st.columns(2)

    with colA:
        # Revenue by Gender
        rev_gender = filtered_df.groupby("gender")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_gender, names="gender", values="purchase_amount", title="Revenue by Gender")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_gender"))
        if not rev_gender.empty and len(rev_gender) == 2:
            top = rev_gender.loc[rev_gender["purchase_amount"].idxmax(), "gender"]
            total = rev_gender["purchase_amount"].sum()
            top_pct = (rev_gender.loc[rev_gender["gender"] == top, "purchase_amount"].values[0] / total) * 100
            other = rev_gender.loc[rev_gender["gender"] != top, "gender"].values[0]
            st.info(f"💡 **Insight:** {top} customers contribute {top_pct:.1f}% of total revenue. Targeted campaigns for {other} could balance revenue.")

        # Revenue by Age Group
        rev_age = filtered_df.groupby("age_group")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_age, x="age_group", y="purchase_amount", title="Revenue by Age Group", color="age_group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_age"))
        if not rev_age.empty:
            top_age = rev_age.loc[rev_age["purchase_amount"].idxmax(), "age_group"]
            top_rev = rev_age["purchase_amount"].max()
            low_age = rev_age.loc[rev_age["purchase_amount"].idxmin(), "age_group"]
            st.info(f"💡 **Insight:** The {top_age} age group spends the most (${top_rev:,.0f}). However, {low_age} has the lowest revenue – test a youth‑friendly promo.")

        # Revenue by Payment Method
        rev_pay = filtered_df.groupby("payment_method")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_pay, names="payment_method", values="purchase_amount", title="Revenue by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_pay"))
        if not rev_pay.empty:
            top_pay = rev_pay.loc[rev_pay["purchase_amount"].idxmax(), "payment_method"]
            total_pay = rev_pay["purchase_amount"].sum()
            pct = (rev_pay.loc[rev_pay["payment_method"] == top_pay, "purchase_amount"].values[0] / total_pay) * 100
            cheap_pay = rev_pay.loc[rev_pay["purchase_amount"].idxmin(), "payment_method"] if len(rev_pay) > 1 else top_pay
            st.info(f"💡 **Insight:** {top_pay} handles {pct:.0f}% of revenue. If its fees are high, incentivize {cheap_pay} with small discounts.")

    with colB:
        # Revenue by Category
        rev_cat = filtered_df.groupby("category")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_cat, x="category", y="purchase_amount", title="Revenue by Category", color="category")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_cat"))
        if not rev_cat.empty and len(rev_cat) >= 2:
            top_cat = rev_cat.loc[rev_cat["purchase_amount"].idxmax(), "category"]
            top_rev = rev_cat["purchase_amount"].max()
            sorted_cat = rev_cat.sort_values("purchase_amount", ascending=False)
            second_cat = sorted_cat.iloc[1]["category"]
            second_rev = sorted_cat.iloc[1]["purchase_amount"]
            pct_diff = (top_rev - second_rev) / second_rev * 100 if second_rev > 0 else 0
            st.info(f"💡 **Insight:** {top_cat} leads with ${top_rev:,.0f}. {second_cat} is only {pct_diff:.0f}% behind – consider bundling them.")

        # Revenue by Season
        rev_season = filtered_df.groupby("season")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_season, x="season", y="purchase_amount", title="Revenue by Season", color="season")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_season"))
        if not rev_season.empty and len(rev_season) >= 2:
            top_season = rev_season.loc[rev_season["purchase_amount"].idxmax(), "season"]
            low_season = rev_season.loc[rev_season["purchase_amount"].idxmin(), "season"]
            top_rev = rev_season["purchase_amount"].max()
            low_rev = rev_season["purchase_amount"].min()
            pct_higher = ((top_rev - low_rev) / low_rev * 100) if low_rev > 0 else 0
            st.info(f"💡 **Insight:** {top_season} generates {pct_higher:.0f}% more revenue than {low_season}. Plan inventory and ad spend accordingly.")

        # Revenue by Subscription
        rev_sub = filtered_df.groupby("subscription_status")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_sub, names="subscription_status", values="purchase_amount", title="Revenue by Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_sub"))
        if not rev_sub.empty and len(rev_sub) == 2:
            sub_rev = rev_sub[rev_sub["subscription_status"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_sub["subscription_status"].values else 0
            non_rev = rev_sub[rev_sub["subscription_status"] == "No"]["purchase_amount"].values[0] if "No" in rev_sub["subscription_status"].values else 0
            total = sub_rev + non_rev
            sub_pct = (sub_rev / total * 100) if total > 0 else 0
            st.info(f"💡 **Insight:** Subscribers generate {sub_pct:.1f}% of revenue. Growing subscription could lift revenue further.")

    # Top 10 Products by Revenue
    st.subheader("Top 10 Products by Revenue")
    prod_rev = filtered_df.groupby("item_purchased")["purchase_amount"].sum().nlargest(10).reset_index()
    fig = px.bar(prod_rev, x="purchase_amount", y="item_purchased", orientation="h", title="Top 10 Products")
    st.plotly_chart(fig, use_container_width=True, key=next_key("top10_products"))
    if not prod_rev.empty:
        top_product = prod_rev.iloc[0]["item_purchased"]
        top_rev = prod_rev.iloc[0]["purchase_amount"]
        st.info(f"💡 **Insight:** The top product, {top_product}, alone brings ${top_rev:,.0f}. Stock it aggressively and use it in cross‑sell bundles.")

    # Bottom 10 Products by Revenue
    st.subheader("Bottom 10 Products by Revenue")
    prod_rev_bottom = filtered_df.groupby("item_purchased")["purchase_amount"].sum().nsmallest(10).reset_index()
    fig = px.bar(prod_rev_bottom, x="purchase_amount", y="item_purchased", orientation="h", title="Bottom 10 Products")
    st.plotly_chart(fig, use_container_width=True, key=next_key("bottom10_products"))
    if not prod_rev_bottom.empty:
        worst_product = prod_rev_bottom.iloc[0]["item_purchased"]
        worst_rev = prod_rev_bottom.iloc[0]["purchase_amount"]
        st.info(f"💡 **Insight:** {worst_product} is the worst performer (${worst_rev:.0f}). Consider discontinuing or discounting to clear stock.")

    colC, colD = st.columns(2)
    with colC:
        # Revenue with/without Discount
        rev_disc = filtered_df.groupby("discount_applied")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_disc, x="discount_applied", y="purchase_amount", title="Revenue with/without Discount")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_discount"))
        if not rev_disc.empty and len(rev_disc) == 2:
            disc_rev = rev_disc[rev_disc["discount_applied"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_disc["discount_applied"].values else 0
            total_rev = rev_disc["purchase_amount"].sum()
            disc_rev_pct = (disc_rev / total_rev * 100) if total_rev > 0 else 0
            aov_disc = filtered_df[filtered_df["discount_applied"] == "Yes"]["purchase_amount"].mean() if not filtered_df[filtered_df["discount_applied"] == "Yes"].empty else 0
            aov_no_disc = filtered_df[filtered_df["discount_applied"] == "No"]["purchase_amount"].mean() if not filtered_df[filtered_df["discount_applied"] == "No"].empty else 0
            aov_gap = aov_no_disc - aov_disc
            st.info(f"💡 **Insight:** Discounted purchases generate {disc_rev_pct:.1f}% of total revenue, but AOV is ${aov_gap:.0f} lower. Test smaller discounts to protect margins.")
    with colD:
        # Revenue with/without Promo
        rev_promo = filtered_df.groupby("promo_code_used")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_promo, x="promo_code_used", y="purchase_amount", title="Revenue with/without Promo")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_promo"))
        if not rev_promo.empty and len(rev_promo) == 2:
            promo_rev = rev_promo[rev_promo["promo_code_used"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_promo["promo_code_used"].values else 0
            total_rev = rev_promo["purchase_amount"].sum()
            promo_rev_pct = (promo_rev / total_rev * 100) if total_rev > 0 else 0
            aov_promo = filtered_df[filtered_df["promo_code_used"] == "Yes"]["purchase_amount"].mean() if not filtered_df[filtered_df["promo_code_used"] == "Yes"].empty else 0
            aov_no_promo = filtered_df[filtered_df["promo_code_used"] == "No"]["purchase_amount"].mean() if not filtered_df[filtered_df["promo_code_used"] == "No"].empty else 0
            aov_diff = aov_promo - aov_no_promo
            direction = "higher" if aov_diff > 0 else "lower"
            st.info(f"💡 **Insight:** Promo code users account for {promo_rev_pct:.1f}% of revenue. Their AOV is ${abs(aov_diff):.0f} {direction} – adjust promo strategy.")

# ==================== CUSTOMER TAB ====================
with tabs[1]:
    st.subheader("Customer Segmentation & Value")
    colE, colF = st.columns(2)

    with colE:
        # Customers by Gender
        cust_gender = filtered_df.groupby("gender")["customer_id"].nunique().reset_index()
        fig = px.pie(cust_gender, names="gender", values="customer_id", title="Customers by Gender")
        st.plotly_chart(fig, use_container_width=True, key=next_key("cust_gender"))
        if not cust_gender.empty and len(cust_gender) == 2:
            total_cust = cust_gender["customer_id"].sum()
            female_cust = cust_gender[cust_gender["gender"] == "Female"]["customer_id"].values[0] if "Female" in cust_gender["gender"].values else 0
            male_cust = cust_gender[cust_gender["gender"] == "Male"]["customer_id"].values[0] if "Male" in cust_gender["gender"].values else 0
            pct_female = (female_cust / total_cust * 100) if total_cust > 0 else 0
            pct_male = (male_cust / total_cust * 100) if total_cust > 0 else 0
            st.info(f"💡 **Insight:** {pct_female:.1f}% of customers are female, {pct_male:.1f}% male. If one gender has higher AOV, tailor loyalty programs.")

        # Customer Segments
        seg_counts = filtered_df.groupby("segment")["customer_id"].nunique().reset_index()
        fig = px.bar(seg_counts, x="segment", y="customer_id", title="Customer Segments", color="segment")
        st.plotly_chart(fig, use_container_width=True, key=next_key("seg_counts"))
        if not seg_counts.empty:
            loyal_pct = (seg_counts[seg_counts["segment"] == "Loyal"]["customer_id"].values[0] / seg_counts["customer_id"].sum() * 100) if "Loyal" in seg_counts["segment"].values else 0
            rev_loyal = filtered_df[filtered_df["segment"] == "Loyal"]["purchase_amount"].sum()
            revenue_from_loyal = (rev_loyal / filtered_df["purchase_amount"].sum() * 100) if filtered_df["purchase_amount"].sum() > 0 else 0
            st.info(f"💡 **Insight:** Loyal customers ({loyal_pct:.1f}% of base) drive {revenue_from_loyal:.1f}% of revenue. Invest in retention, not just acquisition.")

        # Avg Spend by Segment
        avg_spend_seg = filtered_df.groupby("segment")["purchase_amount"].mean().reset_index()
        fig = px.bar(avg_spend_seg, x="segment", y="purchase_amount", title="Avg Spend by Segment")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_seg"))
        if not avg_spend_seg.empty:
            loyal_avg = avg_spend_seg[avg_spend_seg["segment"] == "Loyal"]["purchase_amount"].values[0] if "Loyal" in avg_spend_seg["segment"].values else 0
            new_avg = avg_spend_seg[avg_spend_seg["segment"] == "New"]["purchase_amount"].values[0] if "New" in avg_spend_seg["segment"].values else 0
            st.info(f"💡 **Insight:** Loyal customers spend ${loyal_avg:.0f} on average vs ${new_avg:.0f} for new. A welcome series could convert new→returning faster.")

    with colF:
        # Avg Spend by Subscription
        avg_spend_sub = filtered_df.groupby("subscription_status")["purchase_amount"].mean().reset_index()
        fig = px.bar(avg_spend_sub, x="subscription_status", y="purchase_amount", title="Avg Spend by Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_sub"))
        if not avg_spend_sub.empty and len(avg_spend_sub) == 2:
            sub_avg = avg_spend_sub[avg_spend_sub["subscription_status"] == "Yes"]["purchase_amount"].values[0] if "Yes" in avg_spend_sub["subscription_status"].values else 0
            non_sub_avg = avg_spend_sub[avg_spend_sub["subscription_status"] == "No"]["purchase_amount"].values[0] if "No" in avg_spend_sub["subscription_status"].values else 0
            st.info(f"💡 **Insight:** Subscribers spend ${sub_avg:.0f} vs ${non_sub_avg:.0f} for non‑subscribers. Offer a 10% discount to convert non‑subscribers.")

        # Avg Spend by Age Group (line)
        avg_spend_age = filtered_df.groupby("age_group")["purchase_amount"].mean().reset_index()
        fig = px.line(avg_spend_age, x="age_group", y="purchase_amount", markers=True, title="Avg Spend by Age Group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_age"))
        if not avg_spend_age.empty and len(avg_spend_age) >= 3:
            peak_age = avg_spend_age.loc[avg_spend_age["purchase_amount"].idxmax(), "age_group"]
            peak_spend = avg_spend_age["purchase_amount"].max()
            drop_age = avg_spend_age.loc[avg_spend_age["purchase_amount"].idxmin(), "age_group"]
            st.info(f"💡 **Insight:** Spend peaks at {peak_age} (${peak_spend:.0f}) and drops after {drop_age}. Investigate if product mix or pricing causes the drop.")

        # Avg CLV Proxy by Age & Subscription
        clv_age_sub = filtered_df.groupby(["age_group", "subscription_status"])["purchase_amount"].mean().reset_index()
        fig = px.bar(clv_age_sub, x="age_group", y="purchase_amount", color="subscription_status", barmode="group", title="Avg CLV Proxy by Age & Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("clv_age_sub"))
        if not clv_age_sub.empty:
            top_row = clv_age_sub.loc[clv_age_sub["purchase_amount"].idxmax()]
            top_age_sub_group = f"{top_row['age_group']} ({top_row['subscription_status']})"
            top_clv = top_row["purchase_amount"]
            st.info(f"💡 **Insight:** Subscribers in {top_age_sub_group} have CLV proxy ${top_clv:.0f} – highest of all. Prioritize subscription campaigns for that age group.")

    # Top 10% highest-spending customers
    st.subheader("Top 10% Highest-Spending Customers")
    cust_total = filtered_df.groupby("customer_id")["purchase_amount"].sum().reset_index()
    threshold = cust_total["purchase_amount"].quantile(0.9)
    top10pct = cust_total[cust_total["purchase_amount"] >= threshold].merge(
        filtered_df[["customer_id", "gender", "age_group", "subscription_status"]].drop_duplicates(), on="customer_id"
    )
    st.dataframe(top10pct.head(10), use_container_width=True)

    # Key Rates
    st.subheader("Key Rates")
    repeat_rate = (filtered_df.groupby("customer_id").size() > 1).mean() * 100
    disc_usage_rate = (filtered_df["discount_applied"] == "Yes").mean() * 100
    promo_usage_rate = (filtered_df["promo_code_used"] == "Yes").mean() * 100
    colG, colH, colI = st.columns(3)
    colG.metric("Repeat Purchase Rate", f"{repeat_rate:.1f}%")
    colH.metric("Discount Usage Rate", f"{disc_usage_rate:.1f}%")
    colI.metric("Promo Code Usage Rate", f"{promo_usage_rate:.1f}%")
    st.info(f"💡 **Insight:** {repeat_rate:.1f}% of customers buy again. Industry average is ~30% – you are {'above' if repeat_rate > 30 else 'below'}.")
    st.info(f"💡 **Insight:** {disc_usage_rate:.1f}% of transactions use a discount. High may erode margins, low may leave sales on table – test A/B.")

    avg_prev_sub = filtered_df.groupby("subscription_status")["previous_purchases"].mean().reset_index()
    st.subheader("Avg Previous Purchases by Subscription")
    st.dataframe(avg_prev_sub, use_container_width=True)

# ==================== PRODUCT TAB ====================
with tabs[2]:
    st.subheader("Product Performance")
    prod_perf = (
        filtered_df.groupby("item_purchased")
        .agg(revenue=("purchase_amount", "sum"), transactions=("purchase_amount", "count"), avg_rating=("review_rating", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    st.dataframe(prod_perf.head(10), use_container_width=True)

    colJ, colK = st.columns(2)
    with colJ:
        # Highest Rated Products
        high_rated = prod_perf[prod_perf["transactions"] >= 30].nlargest(5, "avg_rating")[["item_purchased", "avg_rating", "transactions"]]
        st.subheader("Highest Rated Products")
        st.dataframe(high_rated)
        if not high_rated.empty:
            top_rated_product = high_rated.iloc[0]["item_purchased"]
            avg_rating = high_rated.iloc[0]["avg_rating"]
            trans_count = high_rated.iloc[0]["transactions"]
            st.info(f"💡 **Insight:** {top_rated_product} has {avg_rating:.1f}⭐ with {trans_count} transactions – a clear winner. Feature it prominently.")

        # Most Popular Size per Category
        size_cat = filtered_df.groupby(["category", "size"]).size().reset_index(name="count")
        size_cat_top = size_cat.sort_values(["category", "count"], ascending=[True, False]).groupby("category").head(1)
        st.subheader("Most Popular Size per Category")
        st.dataframe(size_cat_top)
        if not size_cat_top.empty:
            for _, row in size_cat_top.iterrows():
                category_name = row["category"]
                size_name = row["size"]
                pct = (row["count"] / filtered_df[filtered_df["category"] == category_name].shape[0]) * 100
                st.info(f"💡 **Insight:** In {category_name}, size {size_name} dominates ({pct:.0f}% of sales). Stock more of it and reduce others.")

    with colK:
        # Lowest Rated Products
        low_rated = prod_perf[prod_perf["transactions"] >= 30].nsmallest(5, "avg_rating")[["item_purchased", "avg_rating", "transactions"]]
        st.subheader("Lowest Rated Products")
        st.dataframe(low_rated)
        if not low_rated.empty:
            low_rated_product = low_rated.iloc[0]["item_purchased"]
            avg_rating = low_rated.iloc[0]["avg_rating"]
            st.info(f"💡 **Insight:** {low_rated_product} rates {avg_rating:.1f}⭐. Check recent reviews; consider a quality fix or replacement.")

        # Most Popular Color per Category
        color_cat = filtered_df.groupby(["category", "color"]).size().reset_index(name="count")
        color_cat_top = color_cat.sort_values(["category", "count"], ascending=[True, False]).groupby("category").head(1)
        st.subheader("Most Popular Color per Category")
        st.dataframe(color_cat_top)
        if not color_cat_top.empty:
            for _, row in color_cat_top.iterrows():
                category_name = row["category"]
                color_name = row["color"]
                st.info(f"💡 **Insight:** {color_name} is the top color for {category_name} – use it in hero images and bundles.")

    colL, colM = st.columns(2)
    with colL:
        # Avg Purchase by Size
        avg_size = filtered_df.groupby("size")["purchase_amount"].mean().reset_index()
        st.subheader("Avg Purchase by Size")
        st.dataframe(avg_size)
        if not avg_size.empty and len(avg_size) >= 2:
            size_highest = avg_size.loc[avg_size["purchase_amount"].idxmax(), "size"]
            aov_highest = avg_size["purchase_amount"].max()
            size_lowest = avg_size.loc[avg_size["purchase_amount"].idxmin(), "size"]
            aov_lowest = avg_size["purchase_amount"].min()
            st.info(f"💡 **Insight:** Size {size_highest} yields ${aov_highest:.0f} vs ${aov_lowest:.0f} for size {size_lowest}. Review pricing per size.")

    with colM:
        avg_color = filtered_df.groupby("color")["purchase_amount"].mean().nlargest(5).reset_index()
        st.subheader("Top 5 Colors by Avg Purchase")
        st.dataframe(avg_color)

    # Product Affinity
    st.subheader("Product Affinity (Customers who bought X also bought Y)")
    top_products = prod_perf.nlargest(5, "transactions")["item_purchased"].tolist()
    affinity_data = []
    for prod in top_products:
        cust_ids = filtered_df[filtered_df["item_purchased"] == prod]["customer_id"].unique()
        other_prods = filtered_df[filtered_df["customer_id"].isin(cust_ids) & (filtered_df["item_purchased"] != prod)]["item_purchased"].value_counts().head(3)
        for other, cnt in other_prods.items():
            affinity_data.append({"Base Product": prod, "Also Bought": other, "Count": cnt})
    if affinity_data:
        affinity_df = pd.DataFrame(affinity_data)
        st.dataframe(affinity_df, use_container_width=True)
        if not affinity_df.empty:
            base = affinity_df.iloc[0]["Base Product"]
            also = affinity_df.iloc[0]["Also Bought"]
            st.info(f"💡 **Insight:** Customers who bought {base} are more likely to buy {also}. Create a 'frequently bought together' bundle.")
    else:
        st.info("Not enough data for affinity analysis with current filters.")

# ==================== DISCOUNT & PROMO TAB ====================
with tabs[3]:
    st.subheader("Discount & Promotion Effectiveness")
    colN, colO = st.columns(2)

    with colN:
        # AOV: Discount vs No Discount
        aov_disc = filtered_df.groupby("discount_applied")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_disc, x="discount_applied", y="purchase_amount", title="AOV: Discount vs No Discount")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_disc"))
        if not aov_disc.empty and len(aov_disc) == 2:
            aov_no_disc = aov_disc[aov_disc["discount_applied"] == "No"]["purchase_amount"].values[0] if "No" in aov_disc["discount_applied"].values else 0
            aov_disc_val = aov_disc[aov_disc["discount_applied"] == "Yes"]["purchase_amount"].values[0] if "Yes" in aov_disc["discount_applied"].values else 0
            st.info(f"💡 **Insight:** AOV without discount is ${aov_no_disc:.0f} vs ${aov_disc_val:.0f} with discount. {'Discount lowers AOV – use sparingly.' if aov_disc_val < aov_no_disc else 'Discount raises AOV – consider expanding.'}")

        # % of Revenue from Discounted Purchases by Category
        disc_rev_cat = filtered_df.groupby(["category", "discount_applied"])["purchase_amount"].sum().reset_index()
        total_rev_cat = filtered_df.groupby("category")["purchase_amount"].sum().reset_index().rename(columns={"purchase_amount": "total"})
        disc_rev_cat = disc_rev_cat.merge(total_rev_cat, on="category")
        disc_rev_cat["pct"] = 100 * disc_rev_cat["purchase_amount"] / disc_rev_cat["total"]
        disc_rev_cat = disc_rev_cat[disc_rev_cat["discount_applied"] == "Yes"]
        fig = px.bar(disc_rev_cat, x="category", y="pct", title="% of Revenue from Discounted Purchases by Category")
        st.plotly_chart(fig, use_container_width=True, key=next_key("disc_rev_cat"))
        if not disc_rev_cat.empty:
            top_cat_disc = disc_rev_cat.loc[disc_rev_cat["pct"].idxmax(), "category"]
            top_pct = disc_rev_cat["pct"].max()
            low_cat_disc = disc_rev_cat.loc[disc_rev_cat["pct"].idxmin(), "category"]
            st.info(f"💡 **Insight:** {top_cat_disc} has {top_pct:.0f}% of revenue from discounts – margins may be thin there. {low_cat_disc} uses few discounts – try a small test.")

    with colO:
        # AOV: Promo vs No Promo
        aov_promo = filtered_df.groupby("promo_code_used")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_promo, x="promo_code_used", y="purchase_amount", title="AOV: Promo vs No Promo")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_promo"))

        # Top 5 Products by Discount Usage %
        prod_disc = (
            filtered_df.groupby("item_purchased")
            .agg(total=("purchase_amount", "count"), disc=("discount_applied", lambda x: (x == "Yes").sum()))
            .reset_index()
        )
        prod_disc["discount_pct"] = 100 * prod_disc["disc"] / prod_disc["total"]
        top_disc_prod = prod_disc.nlargest(5, "discount_pct")[["item_purchased", "discount_pct"]]
        st.subheader("Top 5 Products by Discount Usage %")
        st.dataframe(top_disc_prod)
        if not top_disc_prod.empty:
            top_disc_product = top_disc_prod.iloc[0]["item_purchased"]
            pct = top_disc_prod.iloc[0]["discount_pct"]
            st.info(f"💡 **Insight:** {top_disc_product} is discounted in {pct:.0f}% of its sales. If it's still profitable, keep; else reduce discount depth.")

    # Avg Rating: Discount vs No Discount
    rating_disc = filtered_df.groupby("discount_applied")["review_rating"].mean().reset_index()
    fig = px.bar(rating_disc, x="discount_applied", y="review_rating", title="Avg Rating: Discount vs No Discount")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rating_disc"))
    if not rating_disc.empty and len(rating_disc) == 2:
        rating_disc_val = rating_disc[rating_disc["discount_applied"] == "Yes"]["review_rating"].values[0] if "Yes" in rating_disc["discount_applied"].values else 0
        rating_no_disc = rating_disc[rating_disc["discount_applied"] == "No"]["review_rating"].values[0] if "No" in rating_disc["discount_applied"].values else 0
        rating_gap = rating_disc_val - rating_no_disc
        direction = "higher" if rating_gap > 0 else "lower"
        st.info(f"💡 **Insight:** Discounted products rate {abs(rating_gap):.1f}⭐ {direction} than non‑discounted. Quality perception may vary.")

    # Discount Usage by Subscription Status
    sub_disc = filtered_df.groupby("subscription_status")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
    sub_disc.columns = ["subscription_status", "discount_usage_pct"]
    st.subheader("Discount Usage by Subscription Status")
    st.dataframe(sub_disc)
    if not sub_disc.empty and len(sub_disc) == 2:
        sub_type = sub_disc[sub_disc["subscription_status"] == "Yes"]["subscription_status"].values[0] if "Yes" in sub_disc["subscription_status"].values else ""
        pct_usage = sub_disc[sub_disc["subscription_status"] == "Yes"]["discount_usage_pct"].values[0] if "Yes" in sub_disc["subscription_status"].values else 0
        st.info(f"💡 **Insight:** {sub_type} subscribers use discounts {pct_usage:.0f}% of the time. Tailor discount offers to each group.")

    # Additional combo charts
    rev_combo = filtered_df.groupby(["promo_code_used", "discount_applied"])["purchase_amount"].sum().reset_index()
    fig = px.bar(rev_combo, x="promo_code_used", y="purchase_amount", color="discount_applied", barmode="group", title="Revenue by Promo & Discount Combination")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rev_combo"))

    season_disc = filtered_df.groupby(["season", "discount_applied"])["purchase_amount"].mean().reset_index()
    fig = px.bar(season_disc, x="season", y="purchase_amount", color="discount_applied", barmode="group", title="AOV by Season: Discount vs No Discount")
    st.plotly_chart(fig, use_container_width=True, key=next_key("season_disc"))

# ==================== SHIPPING TAB ====================
with tabs[4]:
    st.subheader("Shipping & Logistics")
    ship_perf = (
        filtered_df.groupby("shipping_type")
        .agg(revenue=("purchase_amount", "sum"), orders=("purchase_amount", "count"), aov=("purchase_amount", "mean"), avg_rating=("review_rating", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    st.dataframe(ship_perf, use_container_width=True)
    if not ship_perf.empty and len(ship_perf) >= 2:
        top_ship_method = ship_perf.iloc[0]["shipping_type"]
        rev_ship = ship_perf.iloc[0]["revenue"]
        aov_ship = ship_perf.iloc[0]["aov"]
        low_ship_method = ship_perf.iloc[-1]["shipping_type"]
        st.info(f"💡 **Insight:** {top_ship_method} drives ${rev_ship:,.0f} with AOV ${aov_ship:.0f}. {low_ship_method} underperforms – consider removal or price adjustment.")

    colP, colQ = st.columns(2)
    with colP:
        # Shipping Method Usage by Category
        ship_cat = filtered_df.groupby(["shipping_type", "category"]).size().reset_index(name="count")
        fig = px.bar(ship_cat, x="shipping_type", y="count", color="category", title="Shipping Method Usage by Category", barmode="stack")
        st.plotly_chart(fig, use_container_width=True, key=next_key("ship_cat"))
        if not ship_cat.empty:
            top_cat = filtered_df["category"].value_counts().idxmax()
            top_ship = ship_cat[ship_cat["category"] == top_cat].sort_values("count", ascending=False).iloc[0]["shipping_type"]
            pct = (ship_cat[(ship_cat["category"] == top_cat) & (ship_cat["shipping_type"] == top_ship)]["count"].values[0] / filtered_df[filtered_df["category"] == top_cat].shape[0]) * 100
            st.info(f"💡 **Insight:** {top_cat} buyers prefer {top_ship} (used {pct:.0f}% of transactions). Ensure that method is fast and cheap for that category.")

    with colQ:
        # Shipping Preference of Top 10% Spenders
        cust_total_ship = filtered_df.groupby("customer_id")["purchase_amount"].sum().reset_index()
        threshold_high = cust_total_ship["purchase_amount"].quantile(0.9)
        high_value_custs = cust_total_ship[cust_total_ship["purchase_amount"] >= threshold_high]["customer_id"].unique()
        hv_ship = filtered_df[filtered_df["customer_id"].isin(high_value_custs)]["shipping_type"].value_counts().reset_index()
        hv_ship.columns = ["shipping_type", "count"]
        fig = px.bar(hv_ship, x="shipping_type", y="count", title="Shipping Preference of Top 10% Spenders")
        st.plotly_chart(fig, use_container_width=True, key=next_key("hv_ship"))
        if not hv_ship.empty:
            preferred_ship = hv_ship.iloc[0]["shipping_type"]
            st.info(f"💡 **Insight:** High‑value customers prefer {preferred_ship} – offer it as a free shipping threshold to increase basket size.")

# ==================== GEOGRAPHIC TAB ====================
with tabs[5]:
    st.subheader("Geographic Insights")
    colR, colS = st.columns(2)

    with colR:
        # Top 10 States by Revenue
        loc_rev = filtered_df.groupby("location")["purchase_amount"].sum().nlargest(10).reset_index()
        fig = px.bar(loc_rev, x="location", y="purchase_amount", title="Top 10 States by Revenue")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_rev"))
        if not loc_rev.empty:
            top_state = loc_rev.iloc[0]["location"]
            pct = (loc_rev.iloc[0]["purchase_amount"] / filtered_df["purchase_amount"].sum()) * 100
            st.info(f"💡 **Insight:** {top_state} alone accounts for {pct:.1f}% of total revenue. Diversify geographically or double down with local ads.")

        # Top 10 States by Average Rating
        loc_rating = filtered_df.groupby("location")["review_rating"].mean().nlargest(10).reset_index()
        fig = px.bar(loc_rating, x="location", y="review_rating", title="Top 10 States by Average Rating")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_rating"))

    with colS:
        # Top 10 States by AOV
        loc_aov = filtered_df.groupby("location")["purchase_amount"].mean().nlargest(10).reset_index()
        fig = px.bar(loc_aov, x="location", y="purchase_amount", title="Top 10 States by AOV")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_aov"))
        if not loc_aov.empty:
            state_aov = loc_aov.iloc[0]["location"]
            aov_val = loc_aov.iloc[0]["purchase_amount"]
            overall_avg = filtered_df["purchase_amount"].mean()
            pct_higher = ((aov_val - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
            st.info(f"💡 **Insight:** {state_aov} has AOV ${aov_val:.0f} – {pct_higher:.0f}% above average. Study what's working there and replicate.")

        # Top 10 States by Subscription Adoption %
        sub_by_state = filtered_df.groupby("location")["subscription_status"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
        sub_by_state.columns = ["location", "sub_pct"]
        sub_by_state = sub_by_state.nlargest(10, "sub_pct")
        fig = px.bar(sub_by_state, x="location", y="sub_pct", title="Top 10 States by Subscription Adoption %")
        st.plotly_chart(fig, use_container_width=True, key=next_key("sub_by_state"))
        if not sub_by_state.empty and len(sub_by_state) >= 2:
            top_sub_state = sub_by_state.iloc[0]["location"]
            top_pct = sub_by_state.iloc[0]["sub_pct"]
            low_sub_state = sub_by_state.iloc[-1]["location"]
            low_pct = sub_by_state.iloc[-1]["sub_pct"]
            st.info(f"💡 **Insight:** {top_sub_state} has {top_pct:.0f}% subscription rate vs {low_sub_state} with {low_pct:.0f}%. Run a state‑specific subscription campaign.")

    # Discount Usage by State
    disc_by_state = filtered_df.groupby("location")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
    disc_by_state.columns = ["location", "disc_pct"]
    disc_by_state = disc_by_state.nlargest(10, "disc_pct")
    fig = px.bar(disc_by_state, x="location", y="disc_pct", title="Top 10 States by Discount Usage %")
    st.plotly_chart(fig, use_container_width=True, key=next_key("disc_by_state"))

    # Most Popular Shipping Method per Top 5 Revenue States
    st.subheader("Most Popular Shipping Method per Top 5 Revenue States")
    top5_states = loc_rev["location"].head(5).tolist() if not loc_rev.empty else []
    if top5_states:
        ship_state = filtered_df[filtered_df["location"].isin(top5_states)].groupby(["location", "shipping_type"]).size().reset_index(name="count")
        ship_state = ship_state.sort_values(["location", "count"], ascending=[True, False])
        ship_state_top = ship_state.groupby("location").head(1)
        st.dataframe(ship_state_top, use_container_width=True)
    else:
        st.info("Not enough location data.")

# ==================== PAYMENT TAB ====================
with tabs[6]:
    st.subheader("Payment Method & Purchase Behavior")
    colT, colU = st.columns(2)

    with colT:
        pay_count = filtered_df["payment_method"].value_counts().reset_index()
        pay_count.columns = ["payment_method", "transaction_count"]
        st.dataframe(pay_count, use_container_width=True)

        # Revenue by Payment Method (pie)
        rev_pay2 = filtered_df.groupby("payment_method")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_pay2, names="payment_method", values="purchase_amount", title="Revenue by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_pay2"))
        if not rev_pay2.empty:
            top_payment = rev_pay2.loc[rev_pay2["purchase_amount"].idxmax(), "payment_method"]
            pct = (rev_pay2["purchase_amount"].max() / rev_pay2["purchase_amount"].sum() * 100)
            cheaper_payment = rev_pay2.loc[rev_pay2["purchase_amount"].idxmin(), "payment_method"] if len(rev_pay2) > 1 else top_payment
            st.info(f"💡 **Insight:** {top_payment} handles {pct:.0f}% of revenue. If its fees are high, incentivize {cheaper_payment} with small discounts.")

        # AOV by Payment Method
        aov_pay = filtered_df.groupby("payment_method")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_pay, x="payment_method", y="purchase_amount", title="AOV by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_pay"))
        if not aov_pay.empty:
            high_aov_method = aov_pay.loc[aov_pay["purchase_amount"].idxmax(), "payment_method"]
            aov_high = aov_pay["purchase_amount"].max()
            st.info(f"💡 **Insight:** {high_aov_method} users spend ${aov_high:.0f} – promote this method for high‑ticket items.")

    with colU:
        # Discount Usage % by Payment Method
        disc_pay = filtered_df.groupby("payment_method")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
        disc_pay.columns = ["payment_method", "discount_pct"]
        fig = px.bar(disc_pay, x="payment_method", y="discount_pct", title="Discount Usage % by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("disc_pay"))
        if not disc_pay.empty:
            method = disc_pay.loc[disc_pay["discount_pct"].idxmax(), "payment_method"]
            pct = disc_pay["discount_pct"].max()
            st.info(f"💡 **Insight:** {method} users apply discounts {pct:.0f}% of the time – they are price‑sensitive. Offer loyalty rewards instead.")

        # Payment Method Preference by Age Group
        age_pay = filtered_df.groupby(["age_group", "payment_method"]).size().reset_index(name="count")
        fig = px.bar(age_pay, x="age_group", y="count", color="payment_method", title="Payment Method Preference by Age Group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("age_pay"))

    # Purchase Frequency Distribution
    st.subheader("Purchase Frequency Distribution")
    freq_dist = filtered_df["frequency_of_purchases"].value_counts().reset_index()
    freq_dist.columns = ["frequency", "count"]
    fig = px.bar(freq_dist, x="frequency", y="count", title="How Often Customers Buy")
    st.plotly_chart(fig, use_container_width=True, key=next_key("freq_dist"))

# ==================== ADVANCED TAB ====================
with tabs[7]:
    st.subheader("Advanced Analytics")
    clv_seg = filtered_df.groupby("segment")["purchase_amount"].mean().reset_index()
    fig = px.bar(clv_seg, x="segment", y="purchase_amount", title="Avg CLV Proxy by Customer Segment")
    st.plotly_chart(fig, use_container_width=True, key=next_key("clv_seg"))

    # Correlation Matrix
    st.subheader("Correlation Matrix")
    num_cols = ["age", "purchase_amount", "review_rating", "previous_purchases"]
    corr = filtered_df[num_cols].corr()
    fig = px.imshow(corr, text_auto=True, title="Feature Correlations", color_continuous_scale="RdBu_r")
    st.plotly_chart(fig, use_container_width=True, key=next_key("corr"))
    if not corr.empty:
        corr_vals = corr.unstack().reset_index()
        corr_vals.columns = ["var1", "var2", "corr"]
        corr_vals = corr_vals[corr_vals["var1"] != corr_vals["var2"]]
        top_corr = corr_vals.loc[corr_vals["corr"].abs().idxmax()]
        top_corr_pair = f"{top_corr['var1']} and {top_corr['var2']}"
        corr_val = top_corr["corr"]
        st.info(f"💡 **Insight:** {top_corr_pair} has a correlation of {corr_val:.2f}. For example, previous purchases and purchase amount move together – retention drives revenue.")

    # Revenue by Season (trend)
    st.subheader("Revenue by Season (as trend proxy)")
    rev_season_trend = filtered_df.groupby("season")["purchase_amount"].sum().reset_index()
    fig = px.line(rev_season_trend, x="season", y="purchase_amount", markers=True, title="Revenue Trend Across Seasons")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rev_season_trend"))
    if not rev_season_trend.empty and len(rev_season_trend) >= 2:
        low_season = rev_season_trend.loc[rev_season_trend["purchase_amount"].idxmin(), "season"]
        high_season = rev_season_trend.loc[rev_season_trend["purchase_amount"].idxmax(), "season"]
        low_rev = rev_season_trend["purchase_amount"].min()
        high_rev = rev_season_trend["purchase_amount"].max()
        pct_change = ((high_rev - low_rev) / low_rev * 100) if low_rev > 0 else 0
        trend_direction = "increases" if high_rev > low_rev else "decreases"
        st.info(f"💡 **Insight:** Revenue {trend_direction} from {low_season} to {high_season} by {pct_change:.0f}%. Plan hiring and inventory accordingly.")

    # Potential Revenue Lift metric
    non_sub_avg = filtered_df[filtered_df["subscription_status"] == "No"]["purchase_amount"].mean() if not filtered_df[filtered_df["subscription_status"] == "No"].empty else 0
    sub_avg = filtered_df[filtered_df["subscription_status"] == "Yes"]["purchase_amount"].mean() if not filtered_df[filtered_df["subscription_status"] == "Yes"].empty else 0
    non_sub_count = filtered_df[filtered_df["subscription_status"] == "No"]["customer_id"].nunique()
    potential_lift = (sub_avg - non_sub_avg) * non_sub_count
    st.metric("Potential Revenue Lift (if all non-subscribers become subscribers)", f"${potential_lift:,.0f}")

# ==================== AI SQL ASSISTANT TAB ====================
with tabs[8]:
    st.subheader("🤖 Ask a business question in plain English")

    # Get API keys (from st.secrets)
    api_keys = get_gemini_api_keys()
    if not api_keys:
        st.warning("No Gemini API keys found. Please set GEMINI_API_KEY_1, etc. in .streamlit/secrets.toml")
        api_keys = ["dummy"]  # fallback to avoid errors

    schema_text = get_schema_description(df)  # use full df for schema

    user_question = st.text_area(
        "Please write here:",
        placeholder="Example: Show me total revenue by category for female customers in California",
        height=100,
    )

    col_gen, col_clear = st.columns(2)
    with col_gen:
        if st.button("✨ Generate SQL", use_container_width=True):
            if not user_question.strip():
                st.error("Please enter a question first.")
            else:
                prompt = build_sql_generation_prompt(user_question, schema_text)
                with st.spinner("Processing..."):
                    response = call_gemini_with_fallback(prompt, api_keys)
                    if response:
                        refusal_phrases = [
                            "Please ask a relevant business question",
                            "I cannot answer this because the dataset lacks",
                        ]
                        is_refusal = any(phrase in response for phrase in refusal_phrases)
                        if is_refusal:
                            st.warning(response)
                        else:
                            generated_sql = parse_sql_from_response(response)
                            st.session_state["generated_sql"] = generated_sql
                            st.session_state["sql_editor"] = generated_sql
                            st.success("SQL generated successfully! You can edit it below.")
                            st.rerun()
                    else:
                        st.error("All API keys failed. Please check your keys and try again.")

    with col_clear:
        if st.button("🗑️ Clear SQL", use_container_width=True):
            st.session_state.pop("generated_sql", None)
            st.session_state.pop("sql_editor", None)
            st.rerun()

    if "sql_editor" not in st.session_state:
        if "generated_sql" in st.session_state:
            st.session_state["sql_editor"] = st.session_state["generated_sql"]
        else:
            st.session_state["sql_editor"] = "SELECT * FROM df LIMIT 10"

    sql_query = st.text_area("SQL Query (editable)", key="sql_editor", height=150)

    if st.button("▶️ Execute Query", use_container_width=True):
        if not sql_query.strip():
            st.error("SQL query is empty.")
        else:
            try:
                conn = duckdb.connect()
                conn.register("df", filtered_df)
                result_df = conn.execute(sql_query).fetchdf()
                st.success(f"Query returned {len(result_df)} rows.")
                st.dataframe(result_df, use_container_width=True)

                # AI business insights on result
                if not result_df.empty and len(result_df) <= 50:
                    with st.spinner("🤖 Generating business insights from the result..."):
                        insight_prompt = build_insight_prompt(user_question, result_df)
                        insight_response = call_gemini_with_fallback(insight_prompt, api_keys)
                        if insight_response:
                            st.info(f"💼 **Business Insight:**\n\n{insight_response}")
                        else:
                            st.warning("AI insight generation failed (API issue).")
                elif len(result_df) > 50:
                    st.info("📊 Result is large (>50 rows). AI insights not generated to avoid hallucination. Consider summarizing your query (e.g., GROUP BY, LIMIT).")
                else:
                    st.info("No data to generate insights.")
            except Exception as e:
                st.error(f"SQL execution error: {e}")

    st.markdown("---")
    st.caption("💡 Tip: You can manually edit the SQL before executing.")