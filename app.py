
import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Z&E Live Dashboard", layout="wide")
st.title("📊 Z&E Live Dashboard for Micro Businesses")
st.markdown("Automatic data refresh simulation and real-time comparisons")

# Refresh button
if st.button("🔄 Refresh Data"):
    st.experimental_rerun()

# Load firm data
firms = pd.read_csv("firme.csv")
st.subheader("📁 Registered Firms")
st.dataframe(firms, use_container_width=True)
firm_mod = datetime.datetime.fromtimestamp(os.path.getmtime("firme.csv"))
st.caption(f"Firms file last updated: {firm_mod.strftime('%Y-%m-%d %H:%M:%S')}")

# Load POS data (with live upload fallback)
uploaded_file = st.file_uploader("📥 Upload New POS CSV", type="csv")
if uploaded_file:
    try:
        pos = pd.read_csv(uploaded_file, parse_dates=["Datum"])
        st.success("✅ New POS data uploaded!")
    except Exception as e:
        st.error(f"❌ Error reading uploaded file: {e}")
        pos = pd.read_csv("pos.csv", parse_dates=["Datum"])
else:
    pos = pd.read_csv("pos.csv", parse_dates=["Datum"])

pos_mod = datetime.datetime.fromtimestamp(os.path.getmtime("pos.csv"))
st.caption(f"POS file last updated: {pos_mod.strftime('%Y-%m-%d %H:%M:%S')}")

# Compute Revenue
pos["Revenue"] = pos["Cijena (KM)"] * pos["Količina"]

# Real-time Metrics
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
today_rev = pos[pos["Datum"].dt.date == today]["Revenue"].sum()
yesterday_rev = pos[pos["Datum"].dt.date == yesterday]["Revenue"].sum()

st.subheader("📈 Real-time Revenue Metrics")
col1, col2 = st.columns(2)
col1.metric("Today's Revenue (KM)", f"{today_rev:.2f}", delta=f"{today_rev - yesterday_rev:.2f}")
# Monthly comparison
first_day = today.replace(day=1)
last_month_end = first_day - datetime.timedelta(days=1)
last_month_start = last_month_end.replace(day=1)
current_month_rev = pos[pos["Datum"].dt.date >= first_day]["Revenue"].sum()
last_month_rev = pos[(pos["Datum"].dt.date >= last_month_start) & (pos["Datum"].dt.date <= last_month_end)]["Revenue"].sum()
col2.metric("This Month Revenue (KM)", f"{current_month_rev:.2f}", delta=f"{current_month_rev - last_month_rev:.2f}")

# Daily revenue trend
st.subheader("📊 Daily Revenue Trend")
daily_rev = pos.groupby(pos["Datum"].dt.date)["Revenue"].sum().reset_index()
daily_rev = daily_rev.rename(columns={"Datum": "Date"})
daily_rev = daily_rev.set_index("Date")
st.line_chart(daily_rev)

# Business Recommendations
st.subheader("🔍 Business Recommendations")
for _, row in firms.iterrows():
    if row["POS promet KM"] < 6000:
        st.warning(f"⚠️ {row['Naziv firme']} is underperforming based on historical revenue.")
    elif row["POS promet KM"] > 10000:
        st.success(f"✅ {row['Naziv firme']} has strong historical performance. Consider price increase.")
    else:
        st.info(f"ℹ️ {row['Naziv firme']} is performing within expected range.")
