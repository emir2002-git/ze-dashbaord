import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh
import openai

# ── Auto-refresh every 60 seconds ───────────────────────────────────────────────
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E AI Dashboard", layout="wide")
st.title("📊 Z&E Dashboard with AI Recommendations")
st.caption(f"Last refresh: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")

# ── Load base tables ────────────────────────────────────────────────────────────
firms = pd.read_csv("firms_complex.csv")
pos = pd.read_csv("pos_complex.csv", parse_dates=["Date"])

# ── Sidebar: Firm filter ────────────────────────────────────────────────────────
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Choose a Firm ID", ["All"] + firm_ids)

# ── Display firms ───────────────────────────────────────────────────────────────
st.subheader("📁 Registered Firms")
if selected == "All":
    st.dataframe(firms, use_container_width=True)
else:
    st.dataframe(firms[firms["Firm ID"].astype(str) == selected], use_container_width=True)

# ── Compute daily & avg revenue ─────────────────────────────────────────────────
daily = (
    pos.groupby(["Firm ID", "Date"])["Revenue (KM)"]
       .sum()
       .reset_index(name="Daily Revenue")
)
avg = (
    daily.groupby("Firm ID")["Daily Revenue"]
         .mean()
         .reset_index(name="Avg Daily Revenue")
)
combined = (
    daily.merge(avg, on="Firm ID")
         .merge(firms[["Firm ID", "Firm Name", "Bank", "Package", "Account Balance (KM)"]], on="Firm ID")
)
combined["Suggestion"] = combined.apply(
    lambda row: "Below avg – consider promotions or price cuts"
    if row["Daily Revenue"] < row["Avg Daily Revenue"]
    else "On track or above avg",
    axis=1
)

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

# ── AI-Driven Business Recommendations ───────────────────────────────────────────
st.subheader("🤖 AI-Driven Recommendations")
if selected != "All":
    firm = firms[firms["Firm ID"].astype(str) == selected].iloc[0].to_dict()
    recent = combined[combined["Firm ID"].astype(str) == selected].sort_values("Date").iloc[-1].to_dict()
    prompt = f"""
You are a business consultant AI. 
The company '{firm['Firm Name']}' with bank '{firm['Bank']}' on the '{firm['Package']}' package,
account balance {firm['Account Balance (KM)']} KM.
Their most recent daily revenue on {recent['Date']} was {recent['Daily Revenue']:.2f} KM,
historical daily average is {recent['Avg Daily Revenue']:.2f} KM.
Provide actionable suggestions to improve profitability: 
– Price adjustments 
– Bank/package changes 
– Cost optimizations.
Respond in bullet points.
"""
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
            max_tokens=300
        )
        ai_suggestions = response.choices[0].message.content
        st.markdown(ai_suggestions)
    except Exception as e:
        st.error(f"AI recommendation error: {e}")
