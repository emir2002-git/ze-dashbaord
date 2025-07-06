import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import openai
from streamlit_autorefresh import st_autorefresh

# ── Load OpenAI key (v0.28.0 style) ───────────────────────────────────────────────
# secrets.toml must have [openai] api_key = "sk-…"
openai.api_key = st.secrets["openai"]["api_key"]

# ── Page setup & auto-refresh ─────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E AI Dashboard", layout="wide", page_icon="🤖")
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard with AI Insights")
st.caption("Last refresh: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ── Data loading ─────────────────────────────────────────────────────────────────
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar navigation & firm filter ──────────────────────────────────────────────
st.sidebar.title("Navigation")
page     = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 AI Insights"])
st.sidebar.markdown("---")
st.sidebar.subheader("Select Firm")
ids      = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# ── Filter by firm ─────────────────────────────────────────────────────────────────
if selected == "All":
    mf, df = monthly.copy(), daily.copy()
else:
    fid = int(selected)
    mf     = monthly[monthly["Firm ID"] == fid].copy()
    df     = daily[daily["Firm ID"]   == fid].copy()

# ── Overview ─────────────────────────────────────────────────────────────────────
if page == "🏠 Overview":
    st.header("🏠 Overview")
    ytd   = df["Revenue (KM)"].sum()
    avg_m = mf["Monthly Revenue"].mean()
    c1, c2 = st.columns(2)
    c1.metric("YTD Rev (KM)", f"{ytd:,.2f}")
    c2.metric("Avg Monthly Rev (KM)", f"{avg_m:,.2f}")
    st.subheader("Registered Firms")
    st.dataframe(firms, use_container_width=True)

# ── Monthly Trend ────────────────────────────────────────────────────────────────
elif page == "📈 Monthly Trend":
    st.header("📈 Monthly Revenue Trend")
    fig = px.line(mf, x="Month", y="Monthly Revenue",
                  color="Firm ID" if selected == "All" else None,
                  markers=True, template="plotly_dark")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── Daily Sales ──────────────────────────────────────────────────────────────────
elif page == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (
        df.groupby("Product")[["Quantity","Revenue (KM)"]]
          .sum()
          .reset_index()
    )
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    bar = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(bar, use_container_width=True)

# ── AI Insights ─────────────────────────────────────────────────────────────────
else:
    st.header("💡 AI-Generated Insights")
    if selected == "All":
        st.info("Select a firm to view AI insights.")
    elif df.empty:
        st.warning("No POS data for this firm.")
    else:
        firm       = firms[firms["Firm ID"] == fid].iloc[0]
        last_date  = df["Date"].max()
        today_rev  = df[df["Date"] == last_date]["Revenue (KM)"].sum()
        avg_rev    = df.groupby("Date")["Revenue (KM)"].sum().mean()

        prompt = f\"\"\"You are an expert business consultant AI.
Company: {firm['Firm Name']}
Industry: {firm['Industry']}
Bank & Package: {firm['Bank']} / {firm['Package']}
Account Balance: {firm['Account Balance (KM)']:.2f} KM

On {last_date.date()}, revenue was {today_rev:.2f} KM.
Average daily revenue: {avg_rev:.2f} KM.

Provide 4–6 actionable bullet points to:
- Increase revenue (pricing, promotions)
- Reduce costs (bank fees, suppliers)
- Improve customer retention (loyalty, upsells)
\"\"\".strip()

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a helpful business advisor."},
                {"role":"user","content":prompt}
            ],
            temperature=0.7,
            max_tokens=250,
        )
        advice = response.choices[0].message.content
        st.markdown(advice)
