import streamlit as st
import pandas as pd
import datetime
import openai
from streamlit_autorefresh import st_autorefresh

# ── Auto-refresh every 60 seconds ───────────────────────────────────────────────
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="📊 Z&E AI Dashboard", layout="wide")
st.title("📊 Z&E Dashboard with AI Recommendations")
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
st.subheader("🔀 Daily Revenue vs. Avg")
st.dataframe(
    combined[
        [
            "Firm ID", "Firm Name", "Date",
            "Daily Revenue", "Avg Daily Revenue"
        ]
    ],
    use_container_width=True
)

# ── AI-Driven Business Recommendations ───────────────────────────────────────────
st.subheader("🤖 AI-Driven Recommendations")
if selected == "All":
    st.info("Select a single firm to see AI-driven recommendations.")
else:
    # Build prompt
    firm = firms[firms["Firm ID"].astype(str) == selected].iloc[0]
    latest = combined.sort_values("Date").iloc[-1]
    prompt = f"""
You are a business consultant AI.
Company: {firm['Firm Name']}
Bank: {firm['Bank']} (package: {firm['Package']})
Account balance: {firm['Account Balance (KM)']} KM 
Most recent daily revenue on {latest['Date']}: {latest['Daily Revenue']:.2f} KM
Historical average daily revenue: {latest['Avg Daily Revenue']:.2f} KM

Provide 3-5 actionable recommendations to increase profitability:
- Suggested price adjustments
- Bank/package changes for lower fees
- Cost optimizations
Respond in a numbered list.
""".strip()

    # Set API key
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    try:
        # Use gpt-3.5-turbo for better quota
        res = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
            max_tokens=300
        )
        ai_text = res.choices[0].message.content
        st.markdown(ai_text)
    except Exception as e:
        # Fallback: rule-based suggestions
        st.error(f"AI error: {e}")
        st.markdown("### Rule-based recommendations:")
        if latest["Daily Revenue"] < latest["Avg Daily Revenue"]:
            st.markdown(
                "1. Daily revenue is below average — run a limited-time promotion.\n"
                "2. Consider increasing prices by 3–5% on your best-selling items.\n"
                "3. Review and switch to a lower-fee bank/package if possible.\n"
                "4. Optimize staffing to off-peak hours to save costs.\n"
            )
        else:
            st.markdown(
                "1. Revenue is healthy — explore expanding your product line.\n"
                "2. Invest in small marketing campaigns to boost traffic.\n"
                "3. Negotiate with your bank for loyalty discounts on your current package.\n"
            )

