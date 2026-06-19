import streamlit as st
import plotly.express as px
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import HIGH_SPENDER_PERCENTILE

def render_shipping_tab(df, next_key):
    st.subheader("Shipping & Logistics")
    ship_perf = (
        df.groupby("shipping_type")
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
        st.info(f"💡 **Insight:** **{top_ship_method}** drives ${rev_ship:,.0f} with AOV ${aov_ship:.0f}. **{low_ship_method}** underperforms – consider removal or price adjustment.")

    colP, colQ = st.columns(2)
    with colP:
        # Shipping Method Usage by Category
        ship_cat = df.groupby(["shipping_type", "category"]).size().reset_index(name="count")
        fig = px.bar(ship_cat, x="shipping_type", y="count", color="category", title="Shipping Method Usage by Category", barmode="stack")
        st.plotly_chart(fig, use_container_width=True, key=next_key("ship_cat"))
        if not ship_cat.empty:
            top_cat = df["category"].value_counts().idxmax()
            top_ship = ship_cat[ship_cat["category"] == top_cat].sort_values("count", ascending=False).iloc[0]["shipping_type"]
            pct = (ship_cat[(ship_cat["category"] == top_cat) & (ship_cat["shipping_type"] == top_ship)]["count"].values[0] / df[df["category"] == top_cat].shape[0]) * 100
            st.info(f"💡 **Insight:** **{top_cat}** buyers prefer **{top_ship}** (used {pct:.0f}% of transactions). Ensure that method is fast and cheap for that category.")

    with colQ:
        # Shipping Preference of Top 10% Spenders
        cust_total_ship = df.groupby("customer_id")["purchase_amount"].sum().reset_index()
        threshold_high = cust_total_ship["purchase_amount"].quantile(HIGH_SPENDER_PERCENTILE)
        high_value_custs = cust_total_ship[cust_total_ship["purchase_amount"] >= threshold_high]["customer_id"].unique()
        hv_ship = df[df["customer_id"].isin(high_value_custs)]["shipping_type"].value_counts().reset_index()
        hv_ship.columns = ["shipping_type", "count"]
        fig = px.bar(hv_ship, x="shipping_type", y="count", title="Shipping Preference of Top 10% Spenders")
        st.plotly_chart(fig, use_container_width=True, key=next_key("hv_ship"))
        if not hv_ship.empty:
            preferred_ship = hv_ship.iloc[0]["shipping_type"]
            st.info(f"💡 **Insight:** High‑value customers prefer **{preferred_ship}** – offer it as a free shipping threshold to increase basket size.")
