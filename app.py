import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.set_page_config(page_title="Z&E Realistic Dashboard", layout="wide")
st.title("📊 Z&E Dashboard (Realistic Metrics)")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# Load data
firms = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# Sidebar filter
st.sidebar.subheader("Filter by Firm")
ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# Firms overview
st.subheader("🏢 Firms Overview")
# compute last month vs average monthly
avg_month = monthly.groupby("Firm ID")["Monthly Revenue"].mean().reset_index(name="Avg Month")
last_month = monthly[monthly["Month"] == monthly["Month"].max()]
overview = last_month.merge(avg_month, on="Firm ID").merge(firms[["Firm ID","Firm Name"]],on="Firm ID")
overview["Delta"] = overview["Monthly Revenue"] - overview["Avg Month"]
overview["Monthly Revenue"] = overview["Monthly Revenue"].round(2)
overview["Avg Month"] = overview["Avg Month"].round(2)
overview["Delta"] = overview["Delta"].round(2)
if selected!="All":
    overview = overview[overview["Firm ID"].astype(str)==selected]
st.dataframe(overview[["Firm ID","Firm Name","Monthly Revenue","Avg Month","Delta"]],use_container_width=True)

# Monthly trend chart
st.subheader("📈 Monthly Revenue Trend")
trend = monthly.copy()
trend["Monthly Revenue"] = trend["Monthly Revenue"].round(2)
if selected!="All":
    trend = trend[trend["Firm ID"].astype(str)==selected]
trend = trend.set_index("Month")["Monthly Revenue"]
st.line_chart(trend)

# Daily product summary
st.subheader("📊 Daily Sales by Product (Last 30 days)")
prod = daily.copy()
prod["Revenue (KM)"] = prod["Revenue (KM)"].round(2)
if selected!="All":
    prod = prod[prod["Firm ID"].astype(str)==selected]
summary = prod.groupby("Product")[["Quantity","Revenue (KM)"]].sum().reset_index()
summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
st.dataframe(summary, use_container_width=True)

# Suggest product to promote or discount
st.subheader("💡 Product Performance Insights")
if not summary.empty:
    yesterday = (daily["Date"].max())
    yest = prod[prod["Date"]==yesterday].groupby("Product")["Revenue (KM)"].sum().reset_index(name="Yest Rev")
    avg_p = prod.groupby("Product")["Revenue (KM)"].mean().reset_index(name="Avg Rev")
    perf = yest.merge(avg_p,on="Product")
    perf["Delta"] = (perf["Yest Rev"] - perf["Avg Rev"]).round(2)
    low = perf.sort_values("Delta").iloc[0]
    high = perf.sort_values("Delta", ascending=False).iloc[0]
    st.write(f"Worst performing: **{low['Product']}** (Δ {low['Delta']:.2f} KM vs average)")
    st.write(f"Best performing: **{high['Product']}** (Δ {high['Delta']:.2f} KM vs average)")
