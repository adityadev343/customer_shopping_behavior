import streamlit as st
import plotly.express as px

def render_discount_promo_tab(df, next_key):
    st.subheader("Discount & Promotion Effectiveness")
    colN, colO = st.columns(2)

    with colN:
        # AOV: Discount vs No Discount
        aov_disc = df.groupby("discount_applied")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_disc, x="discount_applied", y="purchase_amount", title="AOV: Discount vs No Discount")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_disc"))
        if not aov_disc.empty and len(aov_disc) == 2:
            aov_no_disc = aov_disc[aov_disc["discount_applied"] == "No"]["purchase_amount"].values[0] if "No" in aov_disc["discount_applied"].values else 0
            aov_disc_val = aov_disc[aov_disc["discount_applied"] == "Yes"]["purchase_amount"].values[0] if "Yes" in aov_disc["discount_applied"].values else 0
            st.info(f"💡 **Insight:** AOV without discount is ${aov_no_disc:.0f} vs ${aov_disc_val:.0f} with discount. {'Discount lowers AOV – use sparingly.' if aov_disc_val < aov_no_disc else 'Discount raises AOV – consider expanding.'}")

        # % of Revenue from Discounted Purchases by Category
        disc_rev_cat = df.groupby(["category", "discount_applied"])["purchase_amount"].sum().reset_index()
        total_rev_cat = df.groupby("category")["purchase_amount"].sum().reset_index().rename(columns={"purchase_amount": "total"})
        disc_rev_cat = disc_rev_cat.merge(total_rev_cat, on="category")
        disc_rev_cat["pct"] = 100 * disc_rev_cat["purchase_amount"] / disc_rev_cat["total"]
        disc_rev_cat = disc_rev_cat[disc_rev_cat["discount_applied"] == "Yes"]
        fig = px.bar(disc_rev_cat, x="category", y="pct", title="% of Revenue from Discounted Purchases by Category")
        st.plotly_chart(fig, use_container_width=True, key=next_key("disc_rev_cat"))
        if not disc_rev_cat.empty:
            top_cat_disc = disc_rev_cat.loc[disc_rev_cat["pct"].idxmax(), "category"]
            top_pct = disc_rev_cat["pct"].max()
            low_cat_disc = disc_rev_cat.loc[disc_rev_cat["pct"].idxmin(), "category"]
            st.info(f"💡 **Insight:** **{top_cat_disc}** has {top_pct:.0f}% of revenue from discounts – margins may be thin there. **{low_cat_disc}** uses few discounts – try a small test.")

    with colO:
        # AOV: Promo vs No Promo
        aov_promo = df.groupby("promo_code_used")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_promo, x="promo_code_used", y="purchase_amount", title="AOV: Promo vs No Promo")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_promo"))

        # Top 5 Products by Discount Usage %
        prod_disc = (
            df.groupby("item_purchased")
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
            st.info(f"💡 **Insight:** **{top_disc_product}** is discounted in {pct:.0f}% of its sales. If it's still profitable, keep; else reduce discount depth.")

    # Avg Rating: Discount vs No Discount
    rating_disc = df.groupby("discount_applied")["review_rating"].mean().reset_index()
    fig = px.bar(rating_disc, x="discount_applied", y="review_rating", title="Avg Rating: Discount vs No Discount")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rating_disc"))
    if not rating_disc.empty and len(rating_disc) == 2:
        rating_disc_val = rating_disc[rating_disc["discount_applied"] == "Yes"]["review_rating"].values[0] if "Yes" in rating_disc["discount_applied"].values else 0
        rating_no_disc = rating_disc[rating_disc["discount_applied"] == "No"]["review_rating"].values[0] if "No" in rating_disc["discount_applied"].values else 0
        rating_gap = rating_disc_val - rating_no_disc
        direction = "higher" if rating_gap > 0 else "lower"
        st.info(f"💡 **Insight:** Discounted products rate {abs(rating_gap):.1f}⭐ {direction} than non‑discounted. Quality perception may vary.")

    # Discount Usage by Subscription Status
    sub_disc = df.groupby("subscription_status")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
    sub_disc.columns = ["subscription_status", "discount_usage_pct"]
    st.subheader("Discount Usage by Subscription Status")
    st.dataframe(sub_disc)
    if not sub_disc.empty and len(sub_disc) == 2:
        sub_type = sub_disc[sub_disc["subscription_status"] == "Yes"]["subscription_status"].values[0] if "Yes" in sub_disc["subscription_status"].values else ""
        pct_usage = sub_disc[sub_disc["subscription_status"] == "Yes"]["discount_usage_pct"].values[0] if "Yes" in sub_disc["subscription_status"].values else 0
        st.info(f"💡 **Insight:** {sub_type} subscribers use discounts {pct_usage:.0f}% of the time. Tailor discount offers to each group.")

    # Additional combo charts
    rev_combo = df.groupby(["promo_code_used", "discount_applied"])["purchase_amount"].sum().reset_index()
    fig = px.bar(rev_combo, x="promo_code_used", y="purchase_amount", color="discount_applied", barmode="group", title="Revenue by Promo & Discount Combination")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rev_combo"))

    season_disc = df.groupby(["season", "discount_applied"])["purchase_amount"].mean().reset_index()
    fig = px.bar(season_disc, x="season", y="purchase_amount", color="discount_applied", barmode="group", title="AOV by Season: Discount vs No Discount")
    st.plotly_chart(fig, use_container_width=True, key=next_key("season_disc"))