
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Z&E Business Assistant", layout="wide")
st.title("📊 Z&E Dashboard for Micro Businesses")

# Load data
firme = pd.read_csv("firme.csv")
pos = pd.read_csv("pos.csv")

# Show firm data
st.subheader("📁 All Registered Firms")
st.dataframe(firme)

# Show POS data
st.subheader("🛒 POS Sales Data")
st.dataframe(pos)

# Generate recommendations
st.subheader("🔍 Business Recommendations")
for i, row in firme.iterrows():
    if row["POS promet KM"] < 6000:
        st.warning(f"⚠️ {row['Naziv firme']} has low revenue. Consider a promotion or price drop.")
    elif row["POS promet KM"] > 10000:
        st.success(f"✅ {row['Naziv firme']} is performing well. You may increase prices by 3–5%.")
    else:
        st.info(f"ℹ️ {row['Naziv firme']} is stable.")
