import streamlit as st
import plotly.express as px
from config import TOP_N_STATES

def render_geographic_tab(df, next_key):
    st.subheader("Geographic Insights")
    colR, colS = st.columns(2)

    with colR:
        # Top N States by Revenue
        loc_rev = df.groupby("location")["purchase_amount"].sum().nlargest(TOP_N_STATES).reset_index()
        fig = px.bar(loc_rev, x="location", y="purchase_amount", title=f"Top {TOP_N_STATES} States by Revenue")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_rev"))
        if not loc_rev.empty:
            top_state = loc_rev.iloc[0]["location"]
            pct = (loc_rev.iloc[0]["purchase_amount"] / df["purchase_amount"].sum()) * 100
            st.info(f"💡 **Insight:** **{top_state}** alone accounts for {pct:.1f}% of total revenue. Diversify geographically or double down with local ads.")

        # Top N States by Average Rating
        loc_rating = df.groupby("location")["review_rating"].mean().nlargest(TOP_N_STATES).reset_index()
        fig = px.bar(loc_rating, x="location", y="review_rating", title=f"Top {TOP_N_STATES} States by Average Rating")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_rating"))

    with colS:
        # Top N States by AOV
        loc_aov = df.groupby("location")["purchase_amount"].mean().nlargest(TOP_N_STATES).reset_index()
        fig = px.bar(loc_aov, x="location", y="purchase_amount", title=f"Top {TOP_N_STATES} States by AOV")
        st.plotly_chart(fig, use_container_width=True, key=next_key("loc_aov"))
        if not loc_aov.empty:
            state_aov = loc_aov.iloc[0]["location"]
            aov_val = loc_aov.iloc[0]["purchase_amount"]
            overall_avg = df["purchase_amount"].mean()
            pct_higher = ((aov_val - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
            st.info(f"💡 **Insight:** **{state_aov}** has AOV ${aov_val:.0f} – {pct_higher:.0f}% above average. Study what's working there and replicate.")

        # Top N States by Subscription Adoption %
        sub_by_state = df.groupby("location")["subscription_status"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
        sub_by_state.columns = ["location", "sub_pct"]
        sub_by_state = sub_by_state.nlargest(TOP_N_STATES, "sub_pct")
        fig = px.bar(sub_by_state, x="location", y="sub_pct", title=f"Top {TOP_N_STATES} States by Subscription Adoption %")
        st.plotly_chart(fig, use_container_width=True, key=next_key("sub_by_state"))
        if not sub_by_state.empty and len(sub_by_state) >= 2:
            top_sub_state = sub_by_state.iloc[0]["location"]
            top_pct = sub_by_state.iloc[0]["sub_pct"]
            low_sub_state = sub_by_state.iloc[-1]["location"]
            low_pct = sub_by_state.iloc[-1]["sub_pct"]
            st.info(f"💡 **Insight:** **{top_sub_state}** has {top_pct:.0f}% subscription rate vs **{low_sub_state}** with {low_pct:.0f}%. Run a state‑specific subscription campaign.")

    # Discount Usage by State
    disc_by_state = df.groupby("location")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
    disc_by_state.columns = ["location", "disc_pct"]
    disc_by_state = disc_by_state.nlargest(TOP_N_STATES, "disc_pct")
    fig = px.bar(disc_by_state, x="location", y="disc_pct", title=f"Top {TOP_N_STATES} States by Discount Usage %")
    st.plotly_chart(fig, use_container_width=True, key=next_key("disc_by_state"))

    # Most Popular Shipping Method per Top 5 Revenue States
    st.subheader("Most Popular Shipping Method per Top 5 Revenue States")
    top5_states = loc_rev["location"].head(5).tolist() if not loc_rev.empty else []
    if top5_states:
        ship_state = df[df["location"].isin(top5_states)].groupby(["location", "shipping_type"]).size().reset_index(name="count")
        ship_state = ship_state.sort_values(["location", "count"], ascending=[True, False])
        ship_state_top = ship_state.groupby("location").head(1)
        st.dataframe(ship_state_top, use_container_width=True)
    else:
        st.info("Not enough location data.")