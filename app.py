
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Page config
st.set_page_config(
    page_title="Z&E Modern Dashboard",
    layout="wide",
    page_icon="📈"
)
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard (Modern)")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Load data
firms = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# Sidebar navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 Recommendations"])
# Sidebar filter
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# Filter data
monthly_f = monthly.copy()
daily_f = daily.copy()
if selected != "All":
    monthly_f = monthly_f[monthly_f["Firm ID"] == int(selected)]
    daily_f = daily_f[daily_f["Firm ID"] == int(selected)]

if menu == "🏠 Overview":
    st.header("🏠 Overview")
    # Metrics
    total_ytd = daily_f["Revenue (KM)"].sum() if selected!="All" else daily["Revenue (KM)"].sum()
    avg_month = monthly_f["Monthly Revenue"].mean() if not monthly_f.empty else monthly["Monthly Revenue"].mean()
    col1, col2 = st.columns(2)
    col1.metric("YTD Revenue (KM)", f"{total_ytd:,.2f}")
    col2.metric("Avg Monthly Rev (KM)", f"{avg_month:,.2f}")
    # Firms table
    st.subheader("All Firms")
    st.dataframe(firms, use_container_width=True)

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

elif menu == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (
        daily_f.groupby("Product")[["Quantity","Revenue (KM)"]]
        .sum()
        .reset_index()
    )
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    fig2 = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

elif menu == "💡 Recommendations":
    st.header("💡 Product Performance Insights")
    if daily_f.empty:
        st.warning("No sales data available.")
    else:
        yesterday = daily_f["Date"].max()
        yest = (daily_f[daily_f["Date"] == yesterday]
                .groupby("Product")["Revenue (KM)"]
                .sum().reset_index(name="Yest Rev"))
        avg_p = (daily_f.groupby("Product")["Revenue (KM)"]
                 .mean().reset_index(name="Avg Rev"))
        perf = yest.merge(avg_p, on="Product")
        perf["Delta"] = (perf["Yest Rev"] - perf["Avg Rev"]).round(2)
        worst = perf.nsmallest(1, "Delta").iloc[0]
        best = perf.nlargest(1, "Delta").iloc[0]
        st.write(f"**Worst performer:** {worst['Product']} (Δ {worst['Delta']:.2f} KM)")
        st.write(f"**Best performer:** {best['Product']} (Δ {best['Delta']:.2f} KM)")
