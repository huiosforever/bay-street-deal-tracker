
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Bay Street Hospitality Scoring", layout="wide")

st.title("🏨 Bay Street Hospitality Investment Scoring Dashboard")

# Sidebar: Deal Input
st.sidebar.header("📝 Input New Deal")

deal_name = st.sidebar.text_input("Deal Name")
asset_type = st.sidebar.selectbox("Asset Type", ["Hotel", "Platform", "Mixed"])
region = st.sidebar.selectbox("Region", ["Americas", "Europe", "APAC", "ME", "ASEAN"])
public_private = st.sidebar.radio("Public or Private?", ["Public", "Private"])

projected_irr = st.sidebar.number_input("Projected IRR (%)", min_value=0.0, max_value=100.0, value=12.0)
coc_yield = st.sidebar.number_input("Cash-on-Cash Yield (%)", min_value=0.0, max_value=100.0, value=6.0)
volatility = st.sidebar.number_input("Volatility Estimate (%)", min_value=0.0, max_value=100.0, value=10.0)
illiquidity_premium = st.sidebar.number_input("Illiquidity Premium (%)", min_value=0.0, max_value=10.0, value=2.0)
esg_score = st.sidebar.slider("ESG Impact Score (1–5)", 1, 5, 3)
sponsor_coinvest = st.sidebar.number_input("Sponsor Co-Investment (%)", min_value=0.0, max_value=100.0, value=5.0)

op_leverage = st.sidebar.radio("Operational Leverage?", ["Y", "N"])
brand_reposition = st.sidebar.radio("Brand Repositioning Opportunity?", ["Y", "N"])
mgmt_transition = st.sidebar.radio("Management Transition?", ["Y", "N"])

# Calculated Metrics
aha = projected_irr - (8 + illiquidity_premium)  # Assuming 8% composite benchmark IRR
bas = aha / volatility if volatility != 0 else 0

# Bay Score Calculation
weights = {
    "IRR": 0.25,
    "CoC": 0.15,
    "AHA": 0.20,
    "BAS": 0.20,
    "ESG": 0.10,
    "CoInvest": 0.05,
    "OpLev": 0.02,
    "BrandRep": 0.02,
    "MgmtTrans": 0.01
}

bay_score = (
    (min(projected_irr / 15, 1) * weights["IRR"]) +
    (min(coc_yield / 8, 1) * weights["CoC"]) +
    (min(aha / 4, 1) * weights["AHA"]) +
    (min(bas / 0.6, 1) * weights["BAS"]) +
    (esg_score / 5 * weights["ESG"]) +
    (min(sponsor_coinvest / 10, 1) * weights["CoInvest"]) +
    ((1 if op_leverage == "Y" else 0) * weights["OpLev"]) +
    ((1 if brand_reposition == "Y" else 0) * weights["BrandRep"]) +
    ((1 if mgmt_transition == "Y" else 0) * weights["MgmtTrans"])
) * 100

# Display result
st.metric("📊 Bay Score", f"{round(bay_score, 2)} / 100")
st.metric("📈 AHA", f"{round(aha, 2)}%")
st.metric("📉 BAS", f"{round(bas, 2)}")

# Save and visualize deals
if "deals" not in st.session_state:
    st.session_state["deals"] = []

if st.sidebar.button("➕ Add Deal"):
    st.session_state["deals"].append({
        "Deal": deal_name,
        "Region": region,
        "IRR": projected_irr,
        "CoC Yield": coc_yield,
        "AHA": aha,
        "BAS": bas,
        "Volatility": volatility,
        "Bay Score": bay_score,
        "ESG": esg_score
    })

if st.session_state["deals"]:
    df = pd.DataFrame(st.session_state["deals"])
    st.subheader("📋 Deal Comparison Table")
    st.dataframe(df.sort_values("Bay Score", ascending=False), use_container_width=True)

    st.subheader("📈 AHA vs Volatility")
    fig1 = px.scatter(df, x="Volatility", y="AHA", size="Bay Score", color="Deal", hover_name="Deal")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📈 Bay Score vs BAS")
    fig2 = px.scatter(df, x="BAS", y="Bay Score", size="IRR", color="Deal", hover_name="Deal")
    st.plotly_chart(fig2, use_container_width=True)
