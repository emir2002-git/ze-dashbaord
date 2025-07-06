import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import openai
from openai import OpenAI

# ── OpenAI client ───────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets["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"])

# ── Page setup & auto-refresh ────────────────────────────────────────────────────
st.set_page_config(page_title="Z&E AI Dashboard", layout="wide", page_icon="🤖")
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard with AI & ChatGPT Link")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ── Load data ───────────────────────────────────────────────────────────────────
firms   = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily   = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# ── Sidebar: navigation & firm filter ────────────────────────────────────────────
st.sidebar.title("Navigation")
menu     = st.sidebar.radio(
    "Go to",
    ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 AI Recommendations"]
)
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids      = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# ── Filter data ─────────────────────────────────────────────────────────────────
if selected == "All":
    monthly_f = monthly.copy()
    daily_f   = daily.copy()
else:
    fid       = int(selected)
    monthly_f = monthly[monthly["Firm ID"] == fid].copy()
    daily_f   = daily[daily["Firm ID"]   == fid].copy()

# ── 🏠 Overview ─────────────────────────────────────────────────────────────────
if menu == "🏠 Overview":
    st.header("🏠 Overview")
    total_ytd   = daily_f["Revenue (KM)"].sum()
    avg_monthly = monthly_f["Monthly Revenue"].mean()
    col1, col2  = st.columns(2)
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
        color="Firm ID" if selected == "All" else None,
        markers=True, template="plotly_dark"
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── 🛒 Daily Sales ──────────────────────────────────────────────────────────────
elif menu == "🛒 Daily Sales":
    st.header("🛒 Daily Sales by Product (Last 30 days)")
    summary = (
        daily_f.groupby("Product")[["Quantity", "Revenue (KM)"]]
        .sum()
        .reset_index()
    )
    summary["Revenue (KM)"] = summary["Revenue (KM)"].round(2)
    st.dataframe(summary, use_container_width=True)
    fig2 = px.bar(summary, x="Product", y="Revenue (KM)", template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

# ── 💡 AI Recommendations ────────────────────────────────────────────────────────
else:
    st.header("💡 AI-Powered Recommendations")
    if selected == "All":
        st.info("Select a single firm to get AI suggestions.")
    elif daily_f.empty:
        st.warning("No sales data available for this firm.")
    else:
        firm      = firms.loc[firms["Firm ID"] == fid].iloc[0]
        latest_dt = daily_f["Date"].max()
        today_rev = daily_f[daily_f["Date"] == latest_dt]["Revenue (KM)"].sum()
        avg_rev   = daily_f.groupby("Date")["Revenue (KM)"].sum().mean()

        prompt = f"""
You are a business consultant AI.
Company: {firm['Firm Name']}
Industry: {firm['Industry']}
Bank package: {firm['Bank']} / {firm['Package']}
Account balance: {firm['Account Balance (KM)']} KM

On {latest_dt.date()}, total revenue was {today_rev:.2f} KM.
Historical average daily revenue is {avg_rev:.2f} KM.

Provide 4–6 actionable bullet-point recommendations to:
- Increase revenue (pricing, promotions, product mix)
- Reduce costs (bank fees, suppliers, staffing)
- Improve customer retention (loyalty, upsells)
""".strip()

        for model in ("gpt-3.5-turbo", "gpt-4o-mini"):
            try:
                res = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role":"system","content":"You are a helpful business advisor."},
                        {"role":"user","content":prompt}
                    ],
                    temperature=0.7,
                    max_tokens=250
                )
                st.markdown(res.choices[0].message.content)
                break
            except Exception as e:
                err = str(e).lower()
                if "model_not_found" in err or "insufficient_quota" in err:
                    st.warning(f"{model} unavailable, trying next…")
                    continue
                st.error(f"AI error ({model}): {e}")
                break
        else:
            st.error("AI unavailable—showing rule-based advice.")
            if today_rev < avg_rev:
                st.markdown("""
1. Launch a limited-time “Happy Hour” on slow items.
2. Increase prices by 3–5% on best-sellers to boost margins.
3. Negotiate a lower-fee bank package.
4. Optimize staffing to peak hours only.
""")
            else:
                st.markdown("""
1. Maintain pricing but monitor competitors.
2. Run a small digital marketing campaign.
3. Implement a customer loyalty program.
4. Review supplier contracts for discounts.
""")

    # ── ChatGPT “New Chat” Link ──────────────────────────────────────────────────
    st.markdown("---")
    chat_link = "https://chatgpt.com/c/686acbe1-4328-8005-872c-36e6acf6f179"
    st.markdown(
        f"[💬 Continue in ChatGPT]({chat_link})",
        unsafe_allow_html=True
    )
