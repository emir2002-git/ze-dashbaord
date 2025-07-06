
import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# Auto-refresh
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.set_page_config(page_title="Z&E Advanced Dashboard", layout="wide")
st.title("📊 Z&E Advanced Dashboard")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# Load data
firms = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
pos_daily = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# Sidebar filter
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Choose Firm ID", ["All"] + firm_ids)

# Overview for all firms
st.subheader("📋 Firms Overview")
# Compute last month period
last_month = monthly["Month"].max()
avg_month = monthly.groupby("Firm ID")["Revenue (KM)"].mean().reset_index(name="Avg Monthly")
last = monthly[monthly["Month"] == last_month][["Firm ID", "Revenue (KM)"]].rename(columns={"Revenue (KM)": "Last Month Revenue"})
overview = firms.merge(avg_month, on="Firm ID").merge(last, on="Firm ID")
overview["Performance"] = overview.apply(lambda r: "Up" if r["Last Month Revenue"] >= r["Avg Monthly"] else "Down", axis=1)
st.dataframe(overview, use_container_width=True)

# Monthly trends chart
st.subheader("📈 Monthly Revenue Trends")
pivot = monthly.pivot(index="Month", columns="Firm ID", values="Revenue (KM)")
st.line_chart(pivot)

# Daily product summary for last month
st.subheader("🛒 Daily Sales by Product (last 30 days)")
if selected == "All":
    df_daily = pos_daily.copy()
else:
    df_daily = pos_daily[pos_daily["Firm ID"].astype(str) == selected]
prod_summary = df_daily.groupby("Product")[["Quantity", "Revenue (KM)"]].sum().reset_index()
st.dataframe(prod_summary.sort_values("Revenue (KM)", ascending=False), use_container_width=True)

# Product performance suggestions
st.subheader("🤔 Product Performance Suggestions")
# Compute average daily per product and yesterday's revenue
yesterday = df_daily["Date"].max()
avg_daily = df_daily.groupby("Product")["Revenue (KM)"].mean()
yest_rev = df_daily[df_daily["Date"] == yesterday].groupby("Product")["Revenue (KM)"].sum()
perf = pd.DataFrame({"Avg": avg_daily, "Yesterday": yest_rev}).fillna(0)
perf["Delta"] = perf["Yesterday"] - perf["Avg"]
st.dataframe(perf.reset_index(), use_container_width=True)
# Suggestions
st.markdown("**Worst performers (delta < 0)**")
for prod, row in perf.iterrows():
    if row["Delta"] < 0:
        st.markdown(f"- `{prod}`: yesterday {row['Yesterday']:.2f} vs avg {row['Avg']:.2f} KM; consider promotion.")

st.markdown("**Top performers (delta >= 0)**")
for prod, row in perf.iterrows():
    if row["Delta"] >= 0:
        st.markdown(f"- `{prod}`: strong performance yesterday ({row['Yesterday']:.2f} KM).")

