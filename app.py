import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ── Page & auto-refresh ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Z&E Modern Dashboard",
    layout="wide",
    page_icon="📈"
)
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard (Modern)")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ── Load data ───────────────────────────────────────────────────────────────────
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar: navigation & filter ────────────────────────────────────────────────
st.sidebar.title("Navigation")
menu     = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 Recommendations"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids      = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# ── Filter data for selection ───────────────────────────────────────────────────
monthly_f = monthly.copy()
daily_f   = daily.copy()
if selected != "All":
    fid        = int(selected)
    monthly_f  = monthly_f[monthly_f["Firm ID"] == fid]
    daily_f    = daily_f[daily_f["Firm ID"] == fid]

# ── 🏠 Overview ─────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":
    st.header("🏠 Overview")
    ytd       = (daily_f["Revenue (KM)"].sum() if selected!="All" else daily["Revenue (KM)"].sum())
    avg_month = (monthly_f["Monthly Revenue"].mean() if selected!="All" else monthly["Monthly Revenue"].mean())
    col1, col2 = st.columns(2)
    col1.metric("YTD Revenue (KM)", f"{ytd:,.2f}")
    col2.metric("Avg Monthly Rev (KM)", f"{avg_month:,.2f}")
    st.subheader("📁 Registered Firms")
    st.dataframe(firms, use_container_width=True)

# ── 📈 Monthly Trend ────────────────────────────────────────────────────────────
elif menu == "📈 Monthly Trend":
    st.header("📈 Monthly Revenue Trend")
    fig = px.line(
        monthly_f,
        x="Month", y="Monthly Revenue",
        color="Firm ID" if selected=="All" else None,
        markers=True, template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── 🛒 Daily Sales ──────────────────────────────────────────────────────────────
elif menu == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (
        daily_f.groupby("Product")[["Quantity","Revenue (KM)"]]
        .sum().reset_index()
    )
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    fig2 = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

# ── 💡 Recommendations ─────────────────────────────────────────────────────────
else:
    st.header("💡 Detailed Business Recommendations")
    if selected == "All":
        st.info("Select a single firm to see tailored recommendations.")
    elif daily_f.empty:
        st.warning("No sales data available for this firm to generate recommendations.")
    else:
        # performance comparison
        latest_date = daily_f["Date"].max()
        yest = (
            daily_f[daily_f["Date"] == latest_date]
            .groupby("Product")["Revenue (KM)"]
            .sum().reset_index(name="Yest Rev")
        )
        avg_p = (
            daily_f.groupby("Product")["Revenue (KM)"]
            .mean().reset_index(name="Avg Rev")
        )
        perf = yest.merge(avg_p, on="Product")
        perf["Delta"] = (perf["Yest Rev"] - perf["Avg Rev"]).round(2)
        worst = perf.nsmallest(1, "Delta").iloc[0]
        best  = perf.nlargest(1,  "Delta").iloc[0]

        firm_name = firms.loc[firms["Firm ID"] == int(selected), "Firm Name"].iloc[0]
        industry  = firms.loc[firms["Firm ID"] == int(selected), "Industry"].iloc[0]

        st.subheader(f"Performance for **{firm_name}** on {latest_date.date()}")
        st.markdown(f"- **Worst performer:** {worst['Product']} (Δ {worst['Delta']:.2f} KM vs avg)")
        st.markdown(f"- **Best performer:** {best['Product']} (Δ +{best['Delta']:.2f} KM vs avg)")

        # industry-specific recommendations
        st.markdown(f"### Industry: {industry}")
        if industry == "Cafe":
            st.markdown("""
- Launch a **‘Happy Hour’** for **%s** between 3–5 PM to boost off-peak sales.
- Bundle **%s** with pastries to increase ticket size by 10%%.
- Implement a **loyalty card**: 5th drink free to drive repeat visits.
- Negotiate bulk coffee bean orders to reduce COGS by 8%%.
""" % (worst["Product"], best["Product"]))
        elif industry == "Retail":
            st.markdown("""
- Bundle slow-moving **%s** with a best-seller at a 5%% discount.
- Feature **%s** prominently in window displays and online ads.
- Introduce a **points-based loyalty program** for repeat purchases.
- Renegotiate supplier contracts to lower staple costs by 6%%.
""" % (worst["Product"], best["Product"]))
        elif industry == "Salon":
            st.markdown("""
- Offer a **15%% weekday discount** on **%s** to fill appointment gaps.
- Promote premium **%s** packages (e.g., haircut + styling) at a 10%% premium.
- Launch a **referral program**: refer a friend for a free manicure.
- Source quality hair-color supplies to cut costs by 7%%.
""" % (worst["Product"], best["Product"]))
        else:
            st.markdown("""
- Regularly review product performance and adjust prices ±5%%.
- Optimize inventory by focusing on top 20%% of SKUs.
""")
