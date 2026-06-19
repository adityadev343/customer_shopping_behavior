import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import re
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from data_loader import load_data
from tabs import (
    render_revenue_tab,
    render_customer_tab,
    render_product_tab,
    render_discount_promo_tab,
    render_shipping_tab,
    render_geographic_tab,
    render_payment_tab,
    render_advanced_tab,
    render_ai_sql_tab,
)
from config import TOP_N_LOCATIONS

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

# Use session state for filter defaults so reset works
if "filter_defaults" not in st.session_state:
    st.session_state["filter_defaults"] = {
        "gender": df["gender"].unique().tolist(),
        "age_group": df["age_group"].unique().tolist(),
        "category": df["category"].unique().tolist(),
        "season": df["season"].unique().tolist(),
        "subscription": df["subscription_status"].unique().tolist(),
        "discount": df["discount_applied"].unique().tolist(),
        "promo": df["promo_code_used"].unique().tolist(),
        "shipping": df["shipping_type"].unique().tolist(),
        "location": [],
    }

gender = st.sidebar.multiselect(
    "Gender", options=df["gender"].unique(),
    default=st.session_state["filter_defaults"]["gender"],
    key="gender"
)
age_group = st.sidebar.multiselect(
    "Age Group", options=df["age_group"].unique(),
    default=st.session_state["filter_defaults"]["age_group"],
    key="age_group"
)
category = st.sidebar.multiselect(
    "Category", options=df["category"].unique(),
    default=st.session_state["filter_defaults"]["category"],
    key="category"
)
season = st.sidebar.multiselect(
    "Season", options=df["season"].unique(),
    default=st.session_state["filter_defaults"]["season"],
    key="season"
)
subscription = st.sidebar.multiselect(
    "Subscription", options=df["subscription_status"].unique(),
    default=st.session_state["filter_defaults"]["subscription"],
    key="subscription"
)
discount = st.sidebar.multiselect(
    "Discount Applied", options=df["discount_applied"].unique(),
    default=st.session_state["filter_defaults"]["discount"],
    key="discount"
)
promo = st.sidebar.multiselect(
    "Promo Code Used", options=df["promo_code_used"].unique(),
    default=st.session_state["filter_defaults"]["promo"],
    key="promo"
)
shipping = st.sidebar.multiselect(
    "Shipping Type", options=df["shipping_type"].unique(),
    default=st.session_state["filter_defaults"]["shipping"],
    key="shipping"
)
location = st.sidebar.multiselect(
    f"Location (Top {TOP_N_LOCATIONS})",
    options=df["location"].value_counts().head(TOP_N_LOCATIONS).index.tolist(),
    default=st.session_state["filter_defaults"]["location"],
    key="location"
)

# Reset Filters button
if st.sidebar.button("🔄 Reset Filters"):
    for key, default in st.session_state["filter_defaults"].items():
        st.session_state[key] = default
    st.rerun()

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

# -------------------- KPIs (fixed CLV) --------------------
total_revenue = filtered_df["purchase_amount"].sum()
total_transactions = len(filtered_df)
avg_order_value = filtered_df["purchase_amount"].mean()
unique_customers = filtered_df["customer_id"].nunique()

# Fixed CLV proxy: aggregate per customer
customer_clv = (
    filtered_df.groupby("customer_id")
    .agg(total_spend=("purchase_amount", "sum"),
         prev_purchases=("previous_purchases", "first"))
)
avg_clv_proxy = (customer_clv["total_spend"] * customer_clv["prev_purchases"]).mean()

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

# Render each tab
with tabs[0]:
    render_revenue_tab(filtered_df, next_key)

with tabs[1]:
    render_customer_tab(filtered_df, next_key)

with tabs[2]:
    render_product_tab(filtered_df, next_key)

with tabs[3]:
    render_discount_promo_tab(filtered_df, next_key)

with tabs[4]:
    render_shipping_tab(filtered_df, next_key)

with tabs[5]:
    render_geographic_tab(filtered_df, next_key)

with tabs[6]:
    render_payment_tab(filtered_df, next_key)

with tabs[7]:
    render_advanced_tab(filtered_df, next_key)

with tabs[8]:
    render_ai_sql_tab(filtered_df, next_key)
