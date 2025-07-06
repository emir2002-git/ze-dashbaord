import streamlit as st
import pandas as pd
import datetime
import numpy as np
from streamlit_autorefresh import st_autorefresh

# ── Auto-refresh ────────────────────────────────────────────────────────────────
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# ── Page setup ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E Advanced Dashboard", layout="wide")
st.title("📊 Z&E Advanced Dashboard")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# ── Load data ───────────────────────────────────────────────────────────────────
firms = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
pos_daily = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + firm_ids)

# ── Monthly Revenue Chart ──────────────────────────────────────────────────────
st.subheader("📅 Monthly Revenue (Last 12 months)")
if selected != "All":
    df_m = monthly[monthly["Firm ID"].astype(str)==selected]
else:
    df_m = monthly.groupby("Month")["Monthly Revenue (KM)"].sum().reset_index()
df_m = df_m.sort_values("Month")
st.line_chart(data=df_m.set_index("Month")["Monthly Revenue (KM)"])

# ── Daily Sales Table ──────────────────────────────────────────────────────────
st.subheader("📆 Daily Sales Last Month by Product")
if selected != "All":
    df_d = pos_daily[pos_daily["Firm ID"].astype(str)==selected]
else:
    df_d = pos_daily.copy()
# pivot table: product vs sum qty, revenue
pivot = df_d.groupby("Product").agg({"Quantity":"sum","Revenue (KM)":"sum"}).reset_index()
pivot.columns = ["Product","Total Quantity","Total Revenue (KM)"]
st.dataframe(pivot, use_container_width=True)

# ── Suggestions ────────────────────────────────────────────────────────────────
st.subheader("💡 Product Performance Suggestions")
if selected != "All":
    # compute avg daily revenue per product over month
    days = df_d["Date"].nunique()
    avg_rev = pivot.copy()
    avg_rev["Avg Daily Revenue"] = (avg_rev["Total Revenue (KM)"]/days).round(2)
    # find yesterday's revenue by product
    latest_date = df_d["Date"].max()
    yest = df_d[df_d["Date"]==latest_date].groupby("Product")["Revenue (KM)"].sum().reset_index()
    yest.columns = ["Product","Yesterday Revenue"]
    sugg = avg_rev.merge(yest, on="Product", how="left").fillna(0)
    # compute variance
    sugg["Variance (%)"] = ((sugg["Yesterday Revenue"] - sugg["Avg Daily Revenue"])/sugg["Avg Daily Revenue"]*100).round(1)
    # display table
    st.dataframe(sugg, use_container_width=True)
    # suggest best and worst
    worst = sugg.nsmallest(1, "Variance (%)").iloc[0]
    best = sugg.nlargest(1, "Variance (%)").iloc[0]
    st.warning(f"👎 *{worst['Product']}* is down {abs(worst['Variance (%)'])}% vs. average. Consider promotions.")
    st.success(f"👍 *{best['Product']}* is up {best['Variance (%)']}% vs. average. Focus inventory on it.")
else:
    st.info("Select a firm to see product suggestions.")
