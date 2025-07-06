import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# ── Auto-refresh every 60 seconds ───────────────────────────────────────────────
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="📊 Z&E Business Dashboard", layout="wide")
st.title("📊 Z&E Dashboard with Recommendations")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# ── Load data ───────────────────────────────────────────────────────────────────
firms = pd.read_csv("firms_complex.csv")
pos   = pd.read_csv("pos_complex.csv", parse_dates=["Date"])

# ── Sidebar: firm filter ────────────────────────────────────────────────────────
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Choose a Firm ID", ["All"] + firm_ids)

# ── Display firms ───────────────────────────────────────────────────────────────
st.subheader("📁 Registered Firms")
if selected == "All":
    st.dataframe(firms, use_container_width=True)
else:
    st.dataframe(
        firms[firms["Firm ID"].astype(str) == selected],
        use_container_width=True
    )

# ── Compute daily & average revenue ─────────────────────────────────────────────
daily = (
    pos
    .groupby(["Firm ID", "Date"])["Revenue (KM)"]
    .sum()
    .reset_index(name="Daily Revenue")
)
avg = (
    daily
    .groupby("Firm ID")["Daily Revenue"]
    .mean()
    .reset_index(name="Avg Daily Revenue")
)
combined = (
    daily
    .merge(avg, on="Firm ID")
    .merge(
        firms[["Firm ID","Firm Name","Bank","Package","Account Balance (KM)"]],
        on="Firm ID",
        how="left"
    )
)

# ── Filter by selection ─────────────────────────────────────────────────────────
if selected != "All":
    combined = combined[combined["Firm ID"].astype(str) == selected]

# ── Show combined revenue table ─────────────────────────────────────────────────
st.subheader("🔀 Daily Revenue vs. Average")
st.dataframe(
    combined[
        [
            "Firm ID", "Firm Name", "Date",
            "Daily Revenue", "Avg Daily Revenue"
        ]
    ],
    use_container_width=True
)

# ── Rule-Based Business Recommendations ────────────────────────────────────────
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

    st.markdown(f"### Recommendations for **{firm_name}** on {latest['Date']}")
    if dr < ar:
        st.warning("⚠️ Today's revenue is below average.")
        st.markdown("""
- **Run a limited-time promotion** (e.g., “Happy Hour” discounts) to boost traffic.
- **Raise prices by 3–5%** on best-selling items to improve margins.
- **Compare banking fees** and consider switching to a lower-cost package.
- **Optimize staffing**, reducing hours during low-traffic periods to cut costs.
""")
    else:
        st.success("✅ Today's revenue meets or exceeds average.")
        st.markdown("""
- **Maintain current pricing**, but monitor competitor rates.
- **Invest in marketing** (social media ads or loyalty programs) to grow further.
- **Explore premium product lines** with higher margins.
- **Negotiate with your bank** for loyalty discounts or cashback on transactions.
""")

