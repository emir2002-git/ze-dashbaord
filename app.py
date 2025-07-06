

import streamlit as st
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
import pandas as pd
import datetime
import requests
import io
import os
# ── LIVE DATA SOURCES ────────────────────────────────
FIRMES_CSV_URL = "https://…/export?format=csv&gid=0"
POS_CSV_URL    = "https://…/export?format=csv&gid=0"


# Show when this run happened:
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"Last refresh: {now}")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E Live Dashboard", layout="wide")
st.title("📊 Z&E Live Dashboard for Micro Businesses")
st.markdown("Data refreshes every minute automatically.\n\n")


# ── Load Firms ─────────────────────────────────────────────────────────────────
resp = requests.get(FIRMES_CSV_URL)
resp.encoding = "utf-8"
firms = pd.read_csv(io.StringIO(resp.text))
st.subheader("📁 Registered Firms")
st.write(f"_Firms data fetched at: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}_")
st.dataframe(firms, use_container_width=True)

# ── Load POS Sales (with live upload) ───────────────────────────────────────────
st.subheader("📥 Upload New POS Data (optional)")
uploaded = st.file_uploader("Upload a CSV file with POS data", type="csv")

if uploaded:
    try:
        r = requests.get(POS_CSV_URL)
        r.encoding = "utf-8"
        pos = pd.read_csv(io.StringIO(r.text), parse_dates=["Datum"])
        st.success("✅ New POS data loaded in memory")
    except Exception as e:
        st.error(f"❌ Could not read uploaded file: {e}")
        pos = pd.read_csv(POS_CSV_URL, parse_dates=["Datum"])
else:
    pos = pd.read_csv(POS_CSV_URL, parse_dates=["Datum"])


pos_ts = datetime.datetime.fromtimestamp(os.path.getmtime("pos.csv"))
st.write(f"_POS data fetched at: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}_")
st.subheader("🛒 POS Sales Data")
st.dataframe(pos, use_container_width=True)

# ── Compute Revenue ─────────────────────────────────────────────────────────────
pos["Revenue"] = pos["Cijena (KM)"] * pos["Količina"]

# ── Real-time Revenue Metrics ──────────────────────────────────────────────────
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

today_rev = pos[pos["Datum"].dt.date == today]["Revenue"].sum()
yesterday_rev = pos[pos["Datum"].dt.date == yesterday]["Revenue"].sum()

first_of_month = today.replace(day=1)
last_month_end = first_of_month - datetime.timedelta(days=1)
last_month_start = last_month_end.replace(day=1)

current_month_rev = pos[pos["Datum"].dt.date >= first_of_month]["Revenue"].sum()
last_month_rev = pos[
    (pos["Datum"].dt.date >= last_month_start) &
    (pos["Datum"].dt.date <= last_month_end)
]["Revenue"].sum()

st.subheader("📈 Real-time Revenue Metrics")
col1, col2 = st.columns(2)
col1.metric(
    label="Today's Revenue (KM)",
    value=f"{today_rev:.2f}",
    delta=f"{today_rev - yesterday_rev:.2f}"
)
col2.metric(
    label="This Month's Revenue (KM)",
    value=f"{current_month_rev:.2f}",
    delta=f"{current_month_rev - last_month_rev:.2f}"
)

# ── Daily Revenue Trend Chart ──────────────────────────────────────────────────
st.subheader("📊 Daily Revenue Trend")
daily = pos.groupby(pos["Datum"].dt.date)["Revenue"].sum().reset_index()
daily = daily.rename(columns={"Datum": "Date"}).set_index("Date")
st.line_chart(daily)

# ── Business Recommendations ────────────────────────────────────────────────────
st.subheader("🔍 Business Recommendations")
for _, row in firms.iterrows():
    name = row["Naziv firme"]
    hist_rev = row["POS promet KM"]
    if hist_rev < 6000:
        st.warning(f"⚠️ *{name}* is underperforming against historical revenue.")
    elif hist_rev > 10000:
        st.success(f"✅ *{name}* has strong historical performance. Consider a price increase.")
    else:
        st.info(f"ℹ️ *{name}* is performing within expected range.")




