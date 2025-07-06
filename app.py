import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import requests
from streamlit_autorefresh import st_autorefresh

# ── Load DeepSeek configuration ─────────────────────────────────────────────────
# In .streamlit/secrets.toml:
# [deepseek]
# api_key = "YOUR_DEEPSEEK_API_KEY"
# base_url = "https://api.deepseek.com"

deepseek_key = st.secrets['deepseek']['api_key']
deepseek_base = st.secrets['deepseek']['base_url'].rstrip('/')

# ── Streamlit page setup & refresh ───────────────────────────────────────────────
st.set_page_config(page_title="Z&E AI Dashboard", layout="wide", page_icon="🤖")
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard with AI Recommendations")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ── Load data ─────────────────────────────────────────────────────────────────────
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar: navigation & firm filter ─────────────────────────────────────────────
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 AI Insights"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
firm_ids = firms["Firm ID"].astype(str).tolist()
selected  = st.sidebar.selectbox("Firm ID", ["All"] + firm_ids)

# ── Data filtering ─────────────────────────────────────────────────────────────────
if selected == "All":
    mdf = monthly.copy()
    ddf = daily.copy()
else:
    fid = int(selected)
    mdf = monthly[monthly["Firm ID"] == fid].copy()
    ddf = daily[daily["Firm ID"] == fid].copy()

# ── Overview ──────────────────────────────────────────────────────────────────────
if page == "🏠 Overview":
    st.header("🏠 Overview")
    total_ytd   = ddf["Revenue (KM)"].sum()
    avg_monthly = mdf["Monthly Revenue"].mean()
    c1, c2 = st.columns(2)
    c1.metric("YTD Revenue (KM)", f"{total_ytd:,.2f}")
    c2.metric("Avg Monthly Rev (KM)", f"{avg_monthly:,.2f}")
    st.subheader("📁 Firms")
    st.dataframe(firms, use_container_width=True)

# ── Monthly Trend ───────────────────────────────────────────────────────────────
elif page == "📈 Monthly Trend":
    st.header("📈 Monthly Revenue Trend")
    fig = px.line(mdf, x="Month", y="Monthly Revenue",
                  color="Firm ID" if selected == "All" else None,
                  markers=True, template="plotly_dark")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── Daily Sales ─────────────────────────────────────────────────────────────────
elif page == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (ddf.groupby("Product")[['Quantity', 'Revenue (KM)']]
               .sum().reset_index())
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    bar = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(bar, use_container_width=True)

# ── AI Insights ─────────────────────────────────────────────────────────────────
else:
    st.header("💡 AI-Generated Insights")
    if selected == "All":
        st.info("Select a firm to view AI-driven recommendations.")
    elif ddf.empty:
        st.warning("No sales data available for this firm.")
    else:
        # prepare context
        firm = firms[firms["Firm ID"] == fid].iloc[0]
        latest_date = ddf["Date"].max()
        today_rev   = ddf[ddf["Date"] == latest_date]["Revenue (KM)"].sum()
        avg_rev     = ddf.groupby("Date")["Revenue (KM)"].sum().mean()

        # cache AI calls for 10 minutes
        @st.cache_data(ttl=600)
        def fetch_insights():
            prompt = f"""
You are a data-driven business consultant.
Company: {firm['Firm Name']}
Industry: {firm['Industry']}
Bank package: {firm['Bank']} / {firm['Package']}
Account balance: {firm['Account Balance (KM)']} KM
Date: {latest_date.date()}
Today's revenue: {today_rev:.2f} KM
Average daily revenue: {avg_rev:.2f} KM

Provide 4–5 actionable bullet points to:
- Increase revenue (pricing, promos)
- Reduce costs (fees, suppliers)
- Improve retention (loyalty, upsells)
""".strip()
            url = f"{deepseek_base}/v1/chat/completions"
            headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat-1.0", "messages": [
                {"role": "system", "content": "You are a helpful business advisor."},
                {"role": "user",   "content": prompt}
            ]}
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json().get("choices", [])[0].get("message", {}).get("content", "No insight returned.")

        insights = fetch_insights()
        st.markdown(insights)
