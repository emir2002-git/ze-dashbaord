import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# ── Auto-refresh every 60 seconds ───────────────────────────────────────────────
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E Final Dashboard", layout="wide")
st.title("📊 Z&E Final Dashboard")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# ── Load base tables ────────────────────────────────────────────────────────────
firms = pd.read_csv("firms_complex.csv")
pos   = pd.read_csv("pos_complex.csv", parse_dates=["Date"])

# ── Sidebar: Firm filter ────────────────────────────────────────────────────────
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Choose a Firm ID", ["All"] + firm_ids)

# ── Show raw firms table ────────────────────────────────────────────────────────
st.subheader("📁 Registered Firms")
if selected == "All":
    st.dataframe(firms, use_container_width=True)
else:
    st.dataframe(firms[firms["Firm ID"].astype(str) == selected], use_container_width=True)

# ── Compute daily & avg revenue ─────────────────────────────────────────────────
# 1) daily sums
daily = (
    pos.groupby(["Firm ID", "Date"])["Revenue (KM)"]
       .sum()
       .reset_index(name="Daily Revenue")
)

# 2) historical average per firm
avg = (
    daily.groupby("Firm ID")["Daily Revenue"]
         .mean()
         .reset_index(name="Avg Daily Revenue")
)

# 3) merge & add firm name
combined = (
    daily.merge(avg, on="Firm ID")
         .merge(firms[["Firm ID", "Firm Name"]], on="Firm ID")
)

# 4) generate suggestion
def make_suggestion(row):
    return (
        "Below avg – consider promotions or price cuts"
        if row["Daily Revenue"] < row["Avg Daily Revenue"]
        else "On track or above avg"
    )

combined["Suggestion"] = combined.apply(make_suggestion, axis=1)

# 5) apply sidebar filter
if selected != "All":
    combined = combined[combined["Firm ID"].astype(str) == selected]

# ── Show combined suggestions ──────────────────────────────────────────────────
st.subheader("🔀 Daily Revenue vs. Avg & Suggestions")
st.dataframe(
    combined[[
        "Firm ID", "Firm Name", "Date",
        "Daily Revenue", "Avg Daily Revenue", "Suggestion"
    ]],
    use_container_width=True
)

# ── Optional: plot a trend for the selected firm ────────────────────────────────
if selected != "All":
    st.subheader(f"📈 Revenue Trend for Firm {selected}")
    trend = combined[["Date", "Daily Revenue"]].set_index("Date")
    st.line_chart(trend)
