import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import openai
from streamlit_autorefresh import st_autorefresh

# ── Page setup & auto-refresh ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Z&E AI Dashboard",
    layout="wide",
    page_icon="🤖"
)
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard with AI Suggestions")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ── Load data ───────────────────────────────────────────────────────────────────
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar: navigation & firm filter ────────────────────────────────────────────
st.sidebar.title("Navigation")
menu     = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 Recommendations"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids      = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# ── Prepare filtered data ────────────────────────────────────────────────────────
monthly_f = monthly.copy()
daily_f   = daily.copy()
if selected != "All":
    fid        = int(selected)
    monthly_f  = monthly_f[monthly_f["Firm ID"] == fid]
    daily_f    = daily_f[daily_f["Firm ID"] == fid]

# ── 🏠 Overview ─────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":
    st.header("🏠 Overview")
    total_ytd    = daily_f["Revenue (KM)"].sum() if selected!="All" else daily["Revenue (KM)"].sum()
    avg_monthly  = monthly_f["Monthly Revenue"].mean() if selected!="All" else monthly["Monthly Revenue"].mean()
    col1, col2   = st.columns(2)
    col1.metric("YTD Revenue (KM)", f"{total_ytd:,.2f}")
    col2.metric("Avg Monthly Rev (KM)", f"{avg_monthly:,.2f}")
    st.subheader("📁 Registered Firms")
    st.dataframe(firms, use_container_width=True)

# ── 📈 Monthly Trend ────────────────────────────────────────────────────────────
elif menu == "📈 Monthly Trend":
    st.header("📈 Monthly Revenue Trend")
    fig = px.line(
        monthly_f,
        x="Month", y="Monthly Revenue",
        color="Firm ID" if selected=="All" else None,
        markers=True, template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── 🛒 Daily Sales ──────────────────────────────────────────────────────────────
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

# ── 💡 Recommendations ─────────────────────────────────────────────────────────
else:
    st.header("💡 AI-Powered Recommendations")
    if selected == "All":
        st.info("Select a single firm to get AI suggestions.")
    elif daily_f.empty:
        st.warning("No sales data available for this firm.")
    else:
        firm = firms[firms["Firm ID"] == int(selected)].iloc[0]
        latest_date = daily_f["Date"].max()
        today_rev   = daily_f[daily_f["Date"] == latest_date]["Revenue (KM)"].sum()
        avg_rev     = daily_f.groupby("Date")["Revenue (KM)"].sum().mean()
        prompt = f"""
You are an expert small-business consultant.
Company: {firm['Firm Name']}
Industry: {firm['Industry']}
Bank package: {firm['Bank']} / {firm['Package']}
Account balance: {firm['Account Balance (KM)']} KM

On {latest_date.date()}, total revenue was {today_rev:.2f} KM.
Historical average daily revenue is {avg_rev:.2f} KM.

Please provide 4-6 actionable bullet-point recommendations to:
- Increase revenue (pricing, promotions, product mix)
- Reduce costs (supplier, bank fees, operations)
- Improve customer retention (loyalty, upsells)

Respond concisely with each action on its own line.
""".strip()

        openai.api_key = st.secrets["OPENAI_API_KEY"]
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"system","content":"You are a helpful business advisor."},
                          {"role":"user","content":prompt}],
                temperature=0.7,
                max_tokens=300
            )
            suggestions = resp.choices[0].message.content
            st.markdown(suggestions)
        except Exception as e:
            st.error(f"AI call failed: {e}")
