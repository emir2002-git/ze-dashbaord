import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Page config
st.set_page_config(
    page_title="Z&E Modern Dashboard",
    layout="wide",
    page_icon="📈"
)
st_autorefresh(interval=60_000, limit=None, key="auto_refresh")
st.title("📊 Z&E Dashboard (Modern)")
st.markdown("**Last refresh:** " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Load data
firms = pd.read_csv("firms_complex.csv")
monthly = pd.read_csv("monthly_summary.csv")
daily = pd.read_csv("pos_daily.csv", parse_dates=["Date"])

# Sidebar navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["🏠 Overview", "📈 Monthly Trend", "🛒 Daily Sales", "💡 Recommendations"])
# Sidebar filter
st.sidebar.markdown("---")
st.sidebar.subheader("Filter by Firm")
ids = firms["Firm ID"].astype(str).tolist()
selected = st.sidebar.selectbox("Firm ID", ["All"] + ids)

# Filter data for selected firm
monthly_f = monthly.copy()
daily_f = daily.copy()
if selected != "All":
    monthly_f = monthly_f[monthly_f["Firm ID"] == int(selected)]
    daily_f = daily_f[daily_f["Firm ID"] == int(selected)]

# Pages
if menu == "💡 Recommendations":
    st.header("💡 Detailed Business Recommendations")
    if selected == "All":
        st.info("Select a single firm to see tailored recommendations.")
    elif daily_f.empty:
        st.warning("No sales data available for this firm to generate recommendations.")
    else:
        # Compute yesterday vs average performance
        latest_date = daily_f["Date"].max()
        yest = (daily_f[daily_f["Date"] == latest_date]
                .groupby("Product")["Revenue (KM)"]
                .sum().reset_index(name="Yest Rev"))
        avg_p = (daily_f.groupby("Product")["Revenue (KM)"]
                 .mean().reset_index(name="Avg Rev"))
        perf = yest.merge(avg_p, on="Product")
        perf["Delta"] = (perf["Yest Rev"] - perf["Avg Rev"]).round(2)
        worst = perf.nsmallest(1, "Delta").iloc[0]
        best = perf.nlargest(1, "Delta").iloc[0]
        st.subheader(f"Recent Performance for {firms.loc[firms['Firm ID']==int(selected), 'Firm Name'].iloc[0]} on {latest_date.date()}")
        st.markdown(f"- **Worst performer:** {worst['Product']} (Δ {worst['Delta']:.2f} KM vs avg)")
        st.markdown(f"- **Best performer:** {best['Product']} (Δ +{best['Delta']:.2f} KM vs avg)")
        
        # Tailored recommendations by industry
        industry = firms.loc[firms["Firm ID"] == int(selected), "Industry"].iloc[0]
        recs = []
        recs.append(f"### Industry: {industry}")
        if industry == "Cafe":
            recs.append(f"- Run a 'Happy Hour' promotion for **{worst['Product']}** between 3–5 PM to boost off-peak sales.")
            recs.append(f"- Create combo deals pairing **{best['Product']}** with pastries to increase average ticket size.")
            recs.append("- Introduce a loyalty card offering every 5th drink free to drive repeat business.")
            recs.append("- Negotiate bulk coffee bean orders to lower cost of goods sold by 10%.")
        elif industry == "Retail":
            recs.append(f"- Bundle **{worst['Product']}** with top-sellers to clear slow-moving stock.")
            recs.append(f"- Feature **{best['Product']}** in window displays and social media ads.")
            recs.append("- Implement a store loyalty program with point-based discounts on repeat purchases.")
            recs.append("- Review supplier contracts for everyday staples to secure bulk discounts.")
        elif industry == "Salon":
            recs.append(f"- Offer a midweek discount on **{worst['Product']}** services to fill appointment gaps.")
            recs.append(f"- Promote package deals for **{best['Product']}**, e.g. haircut + styling at a slight premium.")
            recs.append("- Introduce a referral program: refer a friend for a free manicure service.")
            recs.append("- Source cost-effective hair color supplies without sacrificing quality.")
        else:
            recs.append("- Monitor product performance weekly and adjust pricing ±5% as needed.")
        
        for line in recs:
            st.markdown(line)

# (Keep other pages unchanged)...
