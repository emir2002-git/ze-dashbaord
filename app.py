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

# ── Show firms ─────────────────────────────────────────────────────────────────
st.subheader("📁 Registered Firms")
if selected == "All":
    st.dataframe(firms, use_container_width=True)
else:
    st.dataframe(firms[firms["Firm ID"].astype(str) == selected], use_container_width=True)

# ── Compute daily & average revenue ─────────────────────────────────────────────
daily = (
    pos
    .groupby(["Firm ID","Date"])["Revenue (KM)"]
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

# ── System suggestion column (just a flag) ──────────────────────────────────────
combined["Sys Flag"] = combined.apply(
    lambda r: "Below avg" if r["Daily Revenue"] < r["Avg Daily Revenue"] else "Ok",
    axis=1
)

# ── Filter by selection ─────────────────────────────────────────────────────────
if selected != "All":
    combined = combined[combined["Firm ID"].astype(str) == selected]

# ── Show combined revenue table ─────────────────────────────────────────────────
st.subheader("🔀 Daily Revenue vs. Avg")
st.dataframe(
    combined[
        [
            "Firm ID","Firm Name","Date",
            "Daily Revenue","Avg Daily Revenue","Sys Flag"
        ]
    ],
    use_container_width=True
)

# ── AI-Driven Business Recommendations ───────────────────────────────────────────
st.subheader("🤖 AI-Driven Recommendations")
if selected != "All":
    # build the prompt with firm & recent stats
    firm = firms[firms["Firm ID"].astype(str) == selected].iloc[0]
    latest = combined.sort_values("Date").iloc[-1]
    prompt = f"""
You are a business consultant AI for small micro-businesses.
Company: {firm['Firm Name']}
Bank: {firm['Bank']} (package: {firm['Package']})
Account balance: {firm['Account Balance (KM)']} KM 
Most recent daily revenue on {latest['Date']}: {latest['Daily Revenue']:.2f} KM
Historical average daily revenue: {latest['Avg Daily Revenue']:.2f} KM

Provide 3–5 actionable recommendations to increase profitability:
- Suggested price adjustments
- Potential bank/package changes for lower fees
- Cost optimizations or staffing tips
- Any AI-driven insights
Respond as a numbered bullet list.
""".strip()

  try:
    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content": prompt}],
        temperature=0.7,
        max_tokens=300
    )
    ai_text = res.choices[0].message.content
    st.markdown(ai_text)
except openai.error.InvalidRequestError as e:
    if e.error and e.error.get("code") == "insufficient_quota":
        st.error("⚠️ OpenAI quota exceeded. Showing rule-based suggestions instead.")
        # rule-based fallback:
        if latest["Daily Revenue"] < latest["Avg Daily Revenue"]:
            st.markdown(
                "- Below average revenue – consider lowering costs or running a promotion.\n"
                "- Review your pricing: you could raise prices by 3–5% on best-sellers.\n"
                "- Compare banking fees: switching to Addiko’s “Mini” package could save you 20 KM/mo.\n"
            )
        else:
            st.success("✅ Revenue is healthy. Consider expanding your product range or marketing.")
    else:
        st.error(f"AI recommendation error: {e}")
