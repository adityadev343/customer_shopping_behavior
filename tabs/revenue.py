import streamlit as st
import plotly.express as px

def render_revenue_tab(df, next_key):
    st.subheader("Revenue Breakdown")
    colA, colB = st.columns(2)

    with colA:
        # Revenue by Gender
        rev_gender = df.groupby("gender")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_gender, names="gender", values="purchase_amount", title="Revenue by Gender")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_gender"))
        if not rev_gender.empty and len(rev_gender) == 2:
            top = rev_gender.loc[rev_gender["purchase_amount"].idxmax(), "gender"]
            total = rev_gender["purchase_amount"].sum()
            top_pct = (rev_gender.loc[rev_gender["gender"] == top, "purchase_amount"].values[0] / total) * 100
            other = rev_gender.loc[rev_gender["gender"] != top, "gender"].values[0]
            st.info(f"💡 **Insight:** {top} customers contribute {top_pct:.1f}% of total revenue. Consider targeted campaigns for {other} to balance revenue.")

        # Revenue by Age Group
        rev_age = df.groupby("age_group")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_age, x="age_group", y="purchase_amount", title="Revenue by Age Group", color="age_group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_age"))
        if not rev_age.empty:
            top_age = rev_age.loc[rev_age["purchase_amount"].idxmax(), "age_group"]
            top_rev = rev_age["purchase_amount"].max()
            low_age = rev_age.loc[rev_age["purchase_amount"].idxmin(), "age_group"]
            st.info(f"💡 **Insight:** The **{top_age}** age group spends the most (${top_rev:,.0f}). The **{low_age}** group has the lowest revenue – consider testing a youth‑friendly promo or product mix.")

        # Revenue by Payment Method
        rev_pay = df.groupby("payment_method")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_pay, names="payment_method", values="purchase_amount", title="Revenue by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_pay"))
        if not rev_pay.empty:
            top_pay = rev_pay.loc[rev_pay["purchase_amount"].idxmax(), "payment_method"]
            total_pay = rev_pay["purchase_amount"].sum()
            pct = (rev_pay.loc[rev_pay["payment_method"] == top_pay, "purchase_amount"].values[0] / total_pay) * 100
            cheap_pay = rev_pay.loc[rev_pay["purchase_amount"].idxmin(), "payment_method"] if len(rev_pay) > 1 else top_pay
            st.info(f"💡 **Insight:** {top_pay} handles {pct:.0f}% of revenue. If its fees are high, consider incentivising {cheap_pay} with small discounts.")

    with colB:
        # Revenue by Category
        rev_cat = df.groupby("category")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_cat, x="category", y="purchase_amount", title="Revenue by Category", color="category")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_cat"))
        if not rev_cat.empty and len(rev_cat) >= 2:
            top_cat = rev_cat.loc[rev_cat["purchase_amount"].idxmax(), "category"]
            top_rev = rev_cat["purchase_amount"].max()
            sorted_cat = rev_cat.sort_values("purchase_amount", ascending=False)
            second_cat = sorted_cat.iloc[1]["category"]
            second_rev = sorted_cat.iloc[1]["purchase_amount"]
            pct_diff = ((top_rev - second_rev) / second_rev * 100) if second_rev > 0 else 0
            st.info(f"💡 **Insight:** {top_cat} leads with ${top_rev:,.0f}. {second_cat} is {pct_diff:.0f}% behind – consider bundling them in promotions.")

        # Revenue by Season
        rev_season = df.groupby("season")["purchase_amount"].sum().reset_index()
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
        rev_sub = df.groupby("subscription_status")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_sub, names="subscription_status", values="purchase_amount", title="Revenue by Subscription")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_sub"))
        if not rev_sub.empty and len(rev_sub) == 2:
            sub_rev = rev_sub[rev_sub["subscription_status"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_sub["subscription_status"].values else 0
            non_rev = rev_sub[rev_sub["subscription_status"] == "No"]["purchase_amount"].values[0] if "No" in rev_sub["subscription_status"].values else 0
            total = sub_rev + non_rev
            sub_pct = (sub_rev / total * 100) if total > 0 else 0
            st.info(f"💡 **Insight:** Subscribers generate {sub_pct:.1f}% of revenue. Growing the subscription base could lift overall revenue.")

    # Top 10 Products by Revenue
    st.subheader("Top 10 Products by Revenue")
    prod_rev = df.groupby("item_purchased")["purchase_amount"].sum().nlargest(10).reset_index()
    fig = px.bar(prod_rev, x="purchase_amount", y="item_purchased", orientation="h", title="Top 10 Products")
    st.plotly_chart(fig, use_container_width=True, key=next_key("top10_products"))
    if not prod_rev.empty:
        top_product = prod_rev.iloc[0]["item_purchased"]
        top_rev = prod_rev.iloc[0]["purchase_amount"]
        st.info(f"💡 **Insight:** The top product, **{top_product}**, alone brings ${top_rev:,.0f}. Stock it aggressively and use it in cross‑sell bundles.")

    # Bottom 10 Products by Revenue
    st.subheader("Bottom 10 Products by Revenue")
    prod_rev_bottom = df.groupby("item_purchased")["purchase_amount"].sum().nsmallest(10).reset_index()
    fig = px.bar(prod_rev_bottom, x="purchase_amount", y="item_purchased", orientation="h", title="Bottom 10 Products")
    st.plotly_chart(fig, use_container_width=True, key=next_key("bottom10_products"))
    if not prod_rev_bottom.empty:
        worst_product = prod_rev_bottom.iloc[0]["item_purchased"]
        worst_rev = prod_rev_bottom.iloc[0]["purchase_amount"]
        st.info(f"💡 **Insight:** **{worst_product}** is the worst performer (${worst_rev:.0f}). Consider discontinuing or discounting to clear stock.")

    colC, colD = st.columns(2)
    with colC:
        # Revenue with/without Discount
        rev_disc = df.groupby("discount_applied")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_disc, x="discount_applied", y="purchase_amount", title="Revenue with/without Discount")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_discount"))
        if not rev_disc.empty and len(rev_disc) == 2:
            disc_rev = rev_disc[rev_disc["discount_applied"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_disc["discount_applied"].values else 0
            total_rev = rev_disc["purchase_amount"].sum()
            disc_rev_pct = (disc_rev / total_rev * 100) if total_rev > 0 else 0
            aov_disc = df[df["discount_applied"] == "Yes"]["purchase_amount"].mean() if not df[df["discount_applied"] == "Yes"].empty else 0
            aov_no_disc = df[df["discount_applied"] == "No"]["purchase_amount"].mean() if not df[df["discount_applied"] == "No"].empty else 0
            aov_gap = aov_no_disc - aov_disc
            st.info(f"💡 **Insight:** Discounted purchases generate {disc_rev_pct:.1f}% of total revenue, but AOV is ${aov_gap:.0f} lower than non‑discounted. Test smaller discounts to protect margins.")

    with colD:
        # Revenue with/without Promo
        rev_promo = df.groupby("promo_code_used")["purchase_amount"].sum().reset_index()
        fig = px.bar(rev_promo, x="promo_code_used", y="purchase_amount", title="Revenue with/without Promo")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_promo"))
        if not rev_promo.empty and len(rev_promo) == 2:
            promo_rev = rev_promo[rev_promo["promo_code_used"] == "Yes"]["purchase_amount"].values[0] if "Yes" in rev_promo["promo_code_used"].values else 0
            total_rev = rev_promo["purchase_amount"].sum()
            promo_rev_pct = (promo_rev / total_rev * 100) if total_rev > 0 else 0
            aov_promo = df[df["promo_code_used"] == "Yes"]["purchase_amount"].mean() if not df[df["promo_code_used"] == "Yes"].empty else 0
            aov_no_promo = df[df["promo_code_used"] == "No"]["purchase_amount"].mean() if not df[df["promo_code_used"] == "No"].empty else 0
            aov_diff = aov_promo - aov_no_promo
            direction = "higher" if aov_diff > 0 else "lower"
            st.info(f"💡 **Insight:** Promo code users account for {promo_rev_pct:.1f}% of revenue. Their AOV is ${abs(aov_diff):.0f} {direction} – adjust promo strategy accordingly.")
