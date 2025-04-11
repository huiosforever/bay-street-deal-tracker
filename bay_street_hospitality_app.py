import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import cvxpy as cp

st.set_page_config(page_title="Bay Street Hospitality Scoring", layout="wide")

# Branding with logo only (no video)
st.markdown("""
    <div style="display:flex; align-items:center;">
        <img src="https://cdn.prod.website-files.com/66ec88f6d7b63833eb28d6a7/66ec8de11054852c315965b0_BAY%20STREET%20HOSPITALITY-03.png" style="height:60px;" />
    </div>
""", unsafe_allow_html=True)

st.title("🏨 Bay Street Hospitality Investment Scoring Dashboard")

# Tabs structure
tabs = st.tabs(["🔍 Deal Scoring", "📊 Portfolio Optimizer", "🕰️ Backtest Engine", "📥 Bulk Upload & Auto-Score"])

# ---------------------- TAB 4: BULK UPLOAD & AUTO-SCORE ------------------------
with tabs[3]:
    st.header("📥 Bulk Deal Upload + Auto-Scoring")
    uploaded_bulk = st.file_uploader("Upload a CSV file with your deal data", type=["csv"], key="bulk_uploader")

    required_columns = ["Deal", "IRR", "CoC Yield", "Volatility", "LSD", "ESG", "Sponsor Co-Invest", "OpLev", "BrandRep", "MgmtTrans"]

    if uploaded_bulk:
        df_bulk = pd.read_csv(uploaded_bulk)

        if all(col in df_bulk.columns for col in required_columns):
            df_bulk["AHA"] = df_bulk["IRR"] - (8 + df_bulk["LSD"])
            df_bulk["BAS"] = df_bulk["AHA"] / df_bulk["Volatility"].replace(0, 0.0001)

            # Apply Bay Score formula
            df_bulk["Bay Score"] = (
                (df_bulk["IRR"] / 15 * 0.25) +
                (df_bulk["CoC Yield"] / 8 * 0.15) +
                (df_bulk["AHA"] / 4 * 0.20) +
                (df_bulk["BAS"] / 0.6 * 0.20) +
                (df_bulk["ESG"] / 5 * 0.10) +
                (df_bulk["Sponsor Co-Invest"] / 10 * 0.05) +
                (df_bulk["OpLev"].apply(lambda x: 1 if str(x).lower() in ["y", "yes", "true"] else 0) * 0.02) +
                (df_bulk["BrandRep"].apply(lambda x: 1 if str(x).lower() in ["y", "yes", "true"] else 0) * 0.02) +
                (df_bulk["MgmtTrans"].apply(lambda x: 1 if str(x).lower() in ["y", "yes", "true"] else 0) * 0.01)
            ) * 100

            st.success("✅ Deals scored successfully!")
            st.dataframe(df_bulk)

            fig_bulk = px.scatter(df_bulk, x="BAS", y="Bay Score", color="Deal", size="IRR", title="Bay Score vs BAS")
            st.plotly_chart(fig_bulk, use_container_width=True)
        else:
            st.error("CSV must include columns: " + ", ".join(required_columns))
    else:
        st.info("Upload a CSV file with IRR, Volatility, CoC Yield, ESG, Co-Invest, etc.")
