import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 60 seconds
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# Page config
st.set_page_config(page_title="Z&E AutoAccountant Dashboard", layout="wide")
st.title("📊 Z&E AutoAccountant Dashboard")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# Load data
firms = pd.read_csv("firms_complex.csv")
pos = pd.read_csv("pos_complex.csv", parse_dates=["Date"])

# Sidebar filter
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Choose a Firm ID", ["All"] + firm_ids)

# Display firm registry
st.subheader("📁 Registered Firms")
if selected == "All":
    st.dataframe(firms, use_container_width=True)
else:
    st.dataframe(firms[firms["Firm ID"].astype(str) == selected], use_container_width=True)

# Compute daily revenue and average
daily = pos.groupby(["Firm ID", "Date"])["Revenue (KM)"].sum().reset_index(name="Daily Revenue")
avg = daily.groupby("Firm ID")["Daily Revenue"].mean().reset_index(name="Avg Daily Revenue")
combined = daily.merge(avg, on="Firm ID").merge(
    firms[["Firm ID","Firm Name","Bank","Package","Account Balance (KM)"]],
    on="Firm ID", how="left"
)

# Filter combined data
if selected != "All":
    combined = combined[combined["Firm ID"].astype(str) == selected]

# Show combined table
st.subheader("🔀 Daily Revenue vs. Average")
st.dataframe(combined[["Firm ID","Firm Name","Date","Daily Revenue","Avg Daily Revenue"]], use_container_width=True)

# System recommendations
st.subheader("💡 System Recommendations")
if selected == "All":
    st.info("Select a single firm to see tailored recommendations.")
elif combined.empty:
    st.warning("No POS data available for this firm to generate recommendations.")
else:
    latest = combined.sort_values("Date").iloc[-1]
    dr = latest["Daily Revenue"]
    ar = latest["Avg Daily Revenue"]
    firm_name = latest["Firm Name"]
    date_str = latest["Date"]
    if dr < ar:
        st.warning(f"⚠️ {firm_name} revenue on {date_str} is below average.")
        st.markdown(
            "- Run a limited-time promotion to boost sales.
"
            "- Consider increasing prices by 3–5% on best-selling items.
"
            "- Compare and switch to a lower-cost bank package.
"
            "- Optimize staffing in low-traffic periods."
        )
    else:
        st.success(f"✅ {firm_name} revenue on {date_str} meets or exceeds average.")
        st.markdown(
            "- Maintain current pricing, monitor competitor rates.
"
            "- Invest in targeted marketing campaigns.
"
            "- Explore premium product offerings with higher margins.
"
            "- Negotiate with your bank for loyalty discounts."
        )
