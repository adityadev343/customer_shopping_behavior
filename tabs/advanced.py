import streamlit as st
import plotly.express as px

def render_advanced_tab(df, next_key):
    st.subheader("Advanced Analytics")
    clv_seg = df.groupby("segment")["purchase_amount"].mean().reset_index()
    fig = px.bar(clv_seg, x="segment", y="purchase_amount", title="Avg CLV Proxy by Customer Segment")
    st.plotly_chart(fig, use_container_width=True, key=next_key("clv_seg"))

    # Correlation Matrix
    st.subheader("Correlation Matrix")
    num_cols = ["age", "purchase_amount", "review_rating", "previous_purchases"]
    corr = df[num_cols].corr()
    fig = px.imshow(corr, text_auto=True, title="Feature Correlations", color_continuous_scale="RdBu_r")
    st.plotly_chart(fig, use_container_width=True, key=next_key("corr"))
    if not corr.empty:
        corr_vals = corr.unstack().reset_index()
        corr_vals.columns = ["var1", "var2", "corr"]
        corr_vals = corr_vals[corr_vals["var1"] != corr_vals["var2"]]
        top_corr = corr_vals.loc[corr_vals["corr"].abs().idxmax()]
        top_corr_pair = f"{top_corr['var1']} and {top_corr['var2']}"
        corr_val = top_corr["corr"]
        st.info(f"💡 **Insight:** **{top_corr_pair}** has a correlation of {corr_val:.2f}. For example, previous purchases and purchase amount move together – retention drives revenue.")

    # Revenue by Season (trend)
    st.subheader("Revenue by Season (as trend proxy)")
    rev_season_trend = df.groupby("season")["purchase_amount"].sum().reset_index()
    fig = px.line(rev_season_trend, x="season", y="purchase_amount", markers=True, title="Revenue Trend Across Seasons")
    st.plotly_chart(fig, use_container_width=True, key=next_key("rev_season_trend"))
    if not rev_season_trend.empty and len(rev_season_trend) >= 2:
        low_season = rev_season_trend.loc[rev_season_trend["purchase_amount"].idxmin(), "season"]
        high_season = rev_season_trend.loc[rev_season_trend["purchase_amount"].idxmax(), "season"]
        low_rev = rev_season_trend["purchase_amount"].min()
        high_rev = rev_season_trend["purchase_amount"].max()
        pct_change = ((high_rev - low_rev) / low_rev * 100) if low_rev > 0 else 0
        trend_direction = "increases" if high_rev > low_rev else "decreases"
        st.info(f"💡 **Insight:** Revenue {trend_direction} from **{low_season}** to **{high_season}** by {pct_change:.0f}%. Plan hiring and inventory accordingly.")

    # Potential Revenue Lift metric
    non_sub_avg = df[df["subscription_status"] == "No"]["purchase_amount"].mean() if not df[df["subscription_status"] == "No"].empty else 0
    sub_avg = df[df["subscription_status"] == "Yes"]["purchase_amount"].mean() if not df[df["subscription_status"] == "Yes"].empty else 0
    non_sub_count = df[df["subscription_status"] == "No"]["customer_id"].nunique()
    potential_lift = (sub_avg - non_sub_avg) * non_sub_count
    st.metric("Potential Revenue Lift (if all non-subscribers become subscribers)", f"${potential_lift:,.0f}")