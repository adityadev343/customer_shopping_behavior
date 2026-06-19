import streamlit as st
import plotly.express as px
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import MIN_TRANSACTIONS_FOR_RATING

def render_product_tab(df, next_key):
    st.subheader("Product Performance")
    prod_perf = (
        df.groupby("item_purchased")
        .agg(revenue=("purchase_amount", "sum"), transactions=("purchase_amount", "count"), avg_rating=("review_rating", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    st.dataframe(prod_perf.head(10), use_container_width=True)

    colJ, colK = st.columns(2)
    with colJ:
        # Highest Rated Products (min transactions)
        high_rated = prod_perf[prod_perf["transactions"] >= MIN_TRANSACTIONS_FOR_RATING].nlargest(5, "avg_rating")[["item_purchased", "avg_rating", "transactions"]]
        st.subheader("Highest Rated Products")
        st.dataframe(high_rated)
        if not high_rated.empty:
            top_rated_product = high_rated.iloc[0]["item_purchased"]
            avg_rating = high_rated.iloc[0]["avg_rating"]
            trans_count = high_rated.iloc[0]["transactions"]
            st.info(f"💡 **Insight:** **{top_rated_product}** has {avg_rating:.1f}⭐ with {trans_count} transactions – a clear winner. Feature it prominently.")

        # Most Popular Size per Category
        size_cat = df.groupby(["category", "size"]).size().reset_index(name="count")
        size_cat_top = size_cat.sort_values(["category", "count"], ascending=[True, False]).groupby("category").head(1)
        st.subheader("Most Popular Size per Category")
        st.dataframe(size_cat_top)
        if not size_cat_top.empty:
            for _, row in size_cat_top.iterrows():
                category_name = row["category"]
                size_name = row["size"]
                pct = (row["count"] / df[df["category"] == category_name].shape[0]) * 100
                st.info(f"💡 **Insight:** In **{category_name}**, size **{size_name}** dominates ({pct:.0f}% of sales). Stock more of it and reduce others.")

    with colK:
        # Lowest Rated Products
        low_rated = prod_perf[prod_perf["transactions"] >= MIN_TRANSACTIONS_FOR_RATING].nsmallest(5, "avg_rating")[["item_purchased", "avg_rating", "transactions"]]
        st.subheader("Lowest Rated Products")
        st.dataframe(low_rated)
        if not low_rated.empty:
            low_rated_product = low_rated.iloc[0]["item_purchased"]
            avg_rating = low_rated.iloc[0]["avg_rating"]
            st.info(f"💡 **Insight:** **{low_rated_product}** rates {avg_rating:.1f}⭐. Check recent reviews; consider a quality fix or replacement.")

        # Most Popular Color per Category
        color_cat = df.groupby(["category", "color"]).size().reset_index(name="count")
        color_cat_top = color_cat.sort_values(["category", "count"], ascending=[True, False]).groupby("category").head(1)
        st.subheader("Most Popular Color per Category")
        st.dataframe(color_cat_top)
        if not color_cat_top.empty:
            for _, row in color_cat_top.iterrows():
                category_name = row["category"]
                color_name = row["color"]
                st.info(f"💡 **Insight:** **{color_name}** is the top color for **{category_name}** – use it in hero images and bundles.")

    colL, colM = st.columns(2)
    with colL:
        # Avg Purchase by Size
        avg_size = df.groupby("size")["purchase_amount"].mean().reset_index()
        st.subheader("Avg Purchase by Size")
        st.dataframe(avg_size)
        if not avg_size.empty and len(avg_size) >= 2:
            size_highest = avg_size.loc[avg_size["purchase_amount"].idxmax(), "size"]
            aov_highest = avg_size["purchase_amount"].max()
            size_lowest = avg_size.loc[avg_size["purchase_amount"].idxmin(), "size"]
            aov_lowest = avg_size["purchase_amount"].min()
            st.info(f"💡 **Insight:** Size **{size_highest}** yields ${aov_highest:.0f} vs ${aov_lowest:.0f} for size **{size_lowest}**. Review pricing per size.")

    with colM:
        avg_color = df.groupby("color")["purchase_amount"].mean().nlargest(5).reset_index()
        st.subheader("Top 5 Colors by Avg Purchase")
        st.dataframe(avg_color)
    
    # Product Affinity
    st.subheader("Product Affinity (Customers who bought X also bought Y)")
    top_products = prod_perf.nlargest(5, "transactions")["item_purchased"].tolist()
    affinity_data = []
    for prod in top_products:
        cust_ids = df[df["item_purchased"] == prod]["customer_id"].unique()
        other_prods = df[df["customer_id"].isin(cust_ids) & (df["item_purchased"] != prod)]["item_purchased"].value_counts().head(3)
        for other, cnt in other_prods.items():
            affinity_data.append({"Base Product": prod, "Also Bought": other, "Count": cnt})
    
    if affinity_data:
        affinity_df = pd.DataFrame(affinity_data)
        st.dataframe(affinity_df, use_container_width=True)
        
        if not affinity_df.empty:
            base = affinity_df.iloc[0]["Base Product"]
            also = affinity_df.iloc[0]["Also Bought"]
            st.info(f"💡 **Insight:** Customers who bought **{base}** are more likely to buy **{also}**. Create a 'frequently bought together' bundle.")
        else:
            st.info("Not enough data for affinity analysis with current filters.")
    else:
        st.info("Not enough data for affinity analysis with current filters.")
