import streamlit as st
import plotly.express as px

def render_payment_tab(df, next_key):
    st.subheader("Payment Method & Purchase Behavior")
    colT, colU = st.columns(2)

    with colT:
        pay_count = df["payment_method"].value_counts().reset_index()
        pay_count.columns = ["payment_method", "transaction_count"]
        st.dataframe(pay_count, use_container_width=True)

        # Revenue by Payment Method (pie)
        rev_pay2 = df.groupby("payment_method")["purchase_amount"].sum().reset_index()
        fig = px.pie(rev_pay2, names="payment_method", values="purchase_amount", title="Revenue by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("rev_pay2"))
        if not rev_pay2.empty:
            top_payment = rev_pay2.loc[rev_pay2["purchase_amount"].idxmax(), "payment_method"]
            pct = (rev_pay2["purchase_amount"].max() / rev_pay2["purchase_amount"].sum() * 100)
            cheaper_payment = rev_pay2.loc[rev_pay2["purchase_amount"].idxmin(), "payment_method"] if len(rev_pay2) > 1 else top_payment
            st.info(f"💡 **Insight:** **{top_payment}** handles {pct:.0f}% of revenue. If its fees are high, incentivize **{cheaper_payment}** with small discounts.")

        # AOV by Payment Method
        aov_pay = df.groupby("payment_method")["purchase_amount"].mean().reset_index()
        fig = px.bar(aov_pay, x="payment_method", y="purchase_amount", title="AOV by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("aov_pay"))
        if not aov_pay.empty:
            high_aov_method = aov_pay.loc[aov_pay["purchase_amount"].idxmax(), "payment_method"]
            aov_high = aov_pay["purchase_amount"].max()
            st.info(f"💡 **Insight:** **{high_aov_method}** users spend ${aov_high:.0f} – promote this method for high‑ticket items.")

    with colU:
        # Discount Usage % by Payment Method
        disc_pay = df.groupby("payment_method")["discount_applied"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
        disc_pay.columns = ["payment_method", "discount_pct"]
        fig = px.bar(disc_pay, x="payment_method", y="discount_pct", title="Discount Usage % by Payment Method")
        st.plotly_chart(fig, use_container_width=True, key=next_key("disc_pay"))
        if not disc_pay.empty:
            method = disc_pay.loc[disc_pay["discount_pct"].idxmax(), "payment_method"]
            pct = disc_pay["discount_pct"].max()
            st.info(f"💡 **Insight:** **{method}** users apply discounts {pct:.0f}% of the time – they are price‑sensitive. Offer loyalty rewards instead.")

        # Payment Method Preference by Age Group
        age_pay = df.groupby(["age_group", "payment_method"]).size().reset_index(name="count")
        fig = px.bar(age_pay, x="age_group", y="count", color="payment_method", title="Payment Method Preference by Age Group")
        st.plotly_chart(fig, use_container_width=True, key=next_key("age_pay"))

    # Purchase Frequency Distribution
    st.subheader("Purchase Frequency Distribution")
    freq_dist = df["frequency_of_purchases"].value_counts().reset_index()
    freq_dist.columns = ["frequency", "count"]
    fig = px.bar(freq_dist, x="frequency", y="count", title="How Often Customers Buy")
    st.plotly_chart(fig, use_container_width=True, key=next_key("freq_dist"))