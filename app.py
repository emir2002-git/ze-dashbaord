import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# New OpenAI client import
from openai import OpenAI

# Instantiate OpenAI client (reads API key from st.secrets)
client = OpenAI()

# Page config and auto-refresh
st.set_page_config(
    page_title="Z&E AI Dashboard",
    layout="wide",
    page_icon="🤖"
)
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard with AI Suggestions")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Load data
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# Sidebar: navigation & firm filter
st.sidebar.title("Navigation")
menu     = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 Recommendations"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids      = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# Prepare filtered data with explicit indexing
if selected != "All":
    fid       = int(selected)
    monthly_f = monthly[monthly["Firm ID"] == fid].copy()
    daily_f   = daily[daily["Firm ID"] == fid].copy()
else:
    monthly_f = monthly.copy()
    daily_f   = daily.copy()

# 🏠 Overview
if menu == "🏠 Overview":
    st.header("🏠 Overview")
    total_ytd   = daily_f["Revenue (KM)"].sum()
    avg_monthly = monthly_f["Monthly Revenue"].mean()
    c1, c2      = st.columns(2)
    c1.metric("YTD Revenue (KM)", f"{total_ytd:,.2f}")
    c2.metric("Avg Monthly Rev (KM)", f"{avg_monthly:,.2f}")
    st.subheader("📁 Registered Firms")
    st.dataframe(firms, use_container_width=True)

# 📈 Monthly Trend
elif menu == "📈 Monthly Trend":
    st.header("📈 Monthly Revenue Trend")
    fig = px.line(
        monthly_f,
        x="Month", y="Monthly Revenue",
        color="Firm ID" if selected == "All" else None,
        markers=True, template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# 🛒 Daily Sales
elif menu == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (
        daily_f.groupby("Product")[["Quantity","Revenue (KM)"]]
        .sum().reset_index()
    )
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    fig2 = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

# 💡 AI Recommendations
else:
    st.header("💡 AI-Powered Recommendations")
    if selected == "All":
        st.info("Select a single firm to get AI suggestions.")
    elif daily_f.empty:
        st.warning("No sales data available for this firm.")
    else:
        # Build prompt
        firm = firms[firms["Firm ID"] == int(selected)].iloc[0]
        latest_date = daily_f["Date"].max()
        today_rev   = daily_f[daily_f["Date"] == latest_date]["Revenue (KM)"].sum()
        avg_rev     = daily_f.groupby("Date")["Revenue (KM)"].sum().mean()
        prompt = f"""
You are a business consultant AI.
Company: {firm['Firm Name']}
Industry: {firm['Industry']}
Bank package: {firm.get('Bank', 'N/A')} / {firm.get('Package', 'N/A')}
Account balance: {firm.get('Account Balance (KM)', 0):,.2f} KM

On {latest_date.date()}, total revenue was {today_rev:,.2f} KM.
Historical average daily revenue is {avg_rev:,.2f} KM.

Provide 4–6 actionable recommendations to:
- Increase revenue (pricing, promotions, product mix)
- Reduce costs (bank fees, supplier expenses, operations)
- Improve customer retention (loyalty, upsells)

Respond as bullet points.
""".strip()

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a helpful business advisor."},
                    {"role":"user","content":prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            ai_out = response.choices[0].message.content
            st.markdown(ai_out)
        except Exception as e:
            st.error(f"AI call failed: {e}")
