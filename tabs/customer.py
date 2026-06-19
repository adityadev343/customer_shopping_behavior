import streamlit as st
import plotly.express as px
import pandas as pd
from config import HIGH_SPENDER_PERCENTILE

def render_customer_tab(df, next_key):
    st.subheader("Customer Segmentation & Value")
    colE, colF = st.columns(2)

    with colE:
        # Customers by Gender
        cust_gender = df.groupby("gender")["customer_id"].nunique().reset_index()
        fig = px.pie(cust_gender, names="gender", values="customer_id", title="Customers by Gender")
        st.plotly_chart(fig, use_container_width=True, key=next_key("cust_gender"))
        if not cust_gender.empty and len(cust_gender) == 2:
            total_cust = cust_gender["customer_id"].sum()
            female_cust = cust_gender[cust_gender["gender"] == "Female"]["customer_id"].values[0] if "Female" in cust_gender["gender"].values else 0
            male_cust = cust_gender[cust_gender["gender"] == "Male"]["customer_id"].values[0] if "Male" in cust_gender["gender"].values else 0
            pct_female = (female_cust / total_cust * 100) if total_cust > 0 else 0
            pct_male = (male_cust / total_cust * 100) if total_cust > 0 else 0
            st.info(f"💡 **Insight:** {pct_female:.1f}% of customers are female, {pct_male:.1f}% male. Tailor loyalty programs to the gender with higher AOV.")

        # Customer Segments
        seg_counts = df.groupby("segment")["customer_id"].nunique().reset_index()
        fig = px.bar(seg_counts, x="segment", y="customer_id", title="Customer Segments", color="segment")
        st.plotly_chart(fig, use_container_width=True, key=next_key("seg_counts"))
        if not seg_counts.empty:
            loyal_customers = seg_counts[seg_counts["segment"] == "Loyal"]["customer_id"].values[0] if "Loyal" in seg_counts["segment"].values else 0
            total_customers = seg_counts["customer_id"].sum()
            loyal_pct = (loyal_customers / total_customers * 100) if total_customers > 0 else 0
            rev_loyal = df[df["segment"] == "Loyal"]["purchase_amount"].sum()
            revenue_from_loyal = (rev_loyal / df["purchase_amount"].sum() * 100) if df["purchase_amount"].sum() > 0 else 0
            st.info(f"💡 **Insight:** Loyal customers ({loyal_pct:.1f}% of base) drive {revenue_from_loyal:.1f}% of revenue. Invest in retention, not just acquisition.")

        # Avg Spend by Segment
        avg_spend_seg = df.groupby("segment")["purchase_amount"].mean().reset_index()
        fig = px.bar(avg_spend_seg, x="segment", y="purchase_amount", title="Avg Spend by Segment")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_seg"))
        if not avg_spend_seg.empty:
            loyal_avg = avg_spend_seg[avg_spend_seg["segment"] == "Loyal"]["purchase_amount"].values[0] if "Loyal" in avg_spend_seg["segment"].values else 0
            new_avg = avg_spend_seg[avg_spend_seg["segment"] == "New"]["purchase_amount"].values[0] if "New" in avg_spend_seg["segment"].values else 0
            st.info(f"💡 **Insight:** Loyal customers spend ${loyal_avg:.0f} on average vs ${new_avg:.0f} for new. A welcome series could convert new→returning faster.")

    with colF:
        # Avg Spend by Subscription
        avg_spend_sub = df.groupby("subscription_status")["purchase_amount"].mean().reset_index()
        fig = px.bar(avg_spend_sub, x="subscription_status", y="purchase_amount", title="Avg Spend by Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_sub"))
        if not avg_spend_sub.empty and len(avg_spend_sub) == 2:
            sub_avg = avg_spend_sub[avg_spend_sub["subscription_status"] == "Yes"]["purchase_amount"].values[0] if "Yes" in avg_spend_sub["subscription_status"].values else 0
            non_sub_avg = avg_spend_sub[avg_spend_sub["subscription_status"] == "No"]["purchase_amount"].values[0] if "No" in avg_spend_sub["subscription_status"].values else 0
            st.info(f"💡 **Insight:** Subscribers spend ${sub_avg:.0f} vs ${non_sub_avg:.0f} for non‑subscribers. Consider a 10% discount to convert non‑subscribers.")

        # Avg Spend by Age Group (line)
        avg_spend_age = df.groupby("age_group")["purchase_amount"].mean().reset_index()
        fig = px.line(avg_spend_age, x="age_group", y="purchase_amount", markers=True, title="Avg Spend by Age Group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("avg_spend_age"))
        if not avg_spend_age.empty and len(avg_spend_age) >= 3:
            peak_age = avg_spend_age.loc[avg_spend_age["purchase_amount"].idxmax(), "age_group"]
            peak_spend = avg_spend_age["purchase_amount"].max()
            drop_age = avg_spend_age.loc[avg_spend_age["purchase_amount"].idxmin(), "age_group"]
            st.info(f"💡 **Insight:** Spend peaks at {peak_age} (${peak_spend:.0f}) and drops after {drop_age}. Investigate if product mix or pricing causes the drop.")

        # Avg CLV Proxy by Age & Subscription
        clv_age_sub = df.groupby(["age_group", "subscription_status"])["purchase_amount"].mean().reset_index()
        fig = px.bar(clv_age_sub, x="age_group", y="purchase_amount", color="subscription_status", barmode="group", title="Avg CLV Proxy by Age & Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("clv_age_sub"))
        if not clv_age_sub.empty:
            top_row = clv_age_sub.loc[clv_age_sub["purchase_amount"].idxmax()]
            top_age_sub_group = f"{top_row['age_group']} ({top_row['subscription_status']})"
            top_clv = top_row["purchase_amount"]
            st.info(f"💡 **Insight:** Subscribers in **{top_age_sub_group}** have the highest CLV proxy (${top_clv:.0f}). Prioritize subscription campaigns for that age group.")

    # Top 10% highest-spending customers
    st.subheader("Top 10% Highest-Spending Customers")
    cust_total = df.groupby("customer_id")["purchase_amount"].sum().reset_index()
    threshold = cust_total["purchase_amount"].quantile(HIGH_SPENDER_PERCENTILE)
    top10pct = cust_total[cust_total["purchase_amount"] >= threshold].merge(
        df[["customer_id", "gender", "age_group", "subscription_status"]].drop_duplicates(), on="customer_id"
    )
    st.dataframe(top10pct.head(10), use_container_width=True)

    # Key Rates (fixed)
    st.subheader("Key Metrics")
    avg_purchases_per_customer = df.groupby("customer_id").size().mean()
    disc_usage_rate = (df["discount_applied"] == "Yes").mean() * 100
    promo_usage_rate = (df["promo_code_used"] == "Yes").mean() * 100
    colG, colH, colI = st.columns(3)
    colG.metric("Avg Purchases per Customer", f"{avg_purchases_per_customer:.2f}")
    colH.metric("Discount Usage Rate", f"{disc_usage_rate:.1f}%")
    colI.metric("Promo Code Usage Rate", f"{promo_usage_rate:.1f}%")
    st.info(f"💡 **Insight:** Customers purchase on average {avg_purchases_per_customer:.2f} times. The industry benchmark varies – aim to increase this through retention programs.")
    st.info(f"💡 **Insight:** {disc_usage_rate:.1f}% of transactions use a discount. High may erode margins, low may leave sales on table – test A/B.")

    avg_prev_sub = df.groupby("subscription_status")["previous_purchases"].mean().reset_index()
    st.subheader("Avg Previous Purchases by Subscription")
    st.dataframe(avg_prev_sub, use_container_width=True)

    # === COHORT HEATMAP (new) ===
    st.subheader("Cohort: Average Spend by Age Group and Season")
    cohort_data = df.groupby(["age_group", "season"])["purchase_amount"].mean().reset_index()
    pivot = cohort_data.pivot(index="age_group", columns="season", values="purchase_amount")
    fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Viridis",
                    title="Average Spend by Age Group and Season")
    st.plotly_chart(fig, use_container_width=True, key=next_key("cohort_heatmap"))
    if not cohort_data.empty:
        max_row = cohort_data.loc[cohort_data["purchase_amount"].idxmax()]
        st.info(f"💡 **Insight:** The highest average spend (${max_row['purchase_amount']:.0f}) occurs for **{max_row['age_group']}** in **{max_row['season']}**. Target this cohort with seasonal campaigns.")