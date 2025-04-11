import streamlit as st
import pandas as pd
import numpy as np
import cvxpy as cp
import plotly.express as px

st.set_page_config(page_title="Bay Street Hospitality Scoring", layout="wide")
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="https://raw.githubusercontent.com/your-repo/baylogo.png" style="height:60px;" />
    <!-- Explainer video removed --> 
    title="Bay Street Hospitality Explainer" frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen></iframe>
</div>
""", unsafe_allow_html=True)

st.title("🏨 Bay Street Hospitality Investment Scoring Dashboard")

# Tabs for Scoring vs Optimization
tab1, tab2 = st.tabs(["🔍 Deal Scoring", "📊 Portfolio Optimizer"])

# ---------------------- TAB 1: SCORING ------------------------
with tab1:
    st.sidebar.header("📝 Input New Investment")

    deal_name = st.sidebar.text_input("Investment Name")
    asset_type = st.sidebar.selectbox("Asset Type", ["Hotel", "Operator", "Developer", "Operator & Developer", "Portfolio of Hotels", "REIT", "Opportunistic", "Ticker Symbol"])
    region = st.sidebar.selectbox("Region", ["Americas", "Europe", "APAC", "ME", "ASEAN", "Opportunistic"])
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
    aha = projected_irr - (8 + illiquidity_premium)  # Assuming 8% benchmark
    bas = aha / volatility if volatility != 0 else 0

    # Weights
    weights = {
        "IRR": 0.25, "CoC": 0.15, "AHA": 0.20, "BAS": 0.20, "ESG": 0.10,
        "CoInvest": 0.05, "OpLev": 0.02, "BrandRep": 0.02, "MgmtTrans": 0.01
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

    st.metric("📊 Bay Score", f"{round(bay_score, 2)} / 100")
    st.metric("📈 AHA", f"{round(aha, 2)}%")
    st.metric("📉 BAS", f"{round(bas, 2)}")

    if "deals" not in st.session_state:
        st.session_state["deals"] = []

    if st.sidebar.button("➕ Add Deal"):
        st.session_state["deals"].append({
            "Deal": deal_name,
            "Region": region,
            "AHA": round(aha, 2),
            "BAS": round(bas, 2),
            "IRR": projected_irr,
            "CoC Yield": coc_yield,
            "Volatility": volatility,
            "LSD": illiquidity_premium,
            "Bay Score": round(bay_score, 2),
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

# ---------------------- TAB 2: OPTIMIZER ------------------------
with tab2:
    st.sidebar.header("⚙️ Optimization Constraints")
    max_volatility = st.sidebar.slider("Max Portfolio Volatility (%)", 5.0, 25.0, 12.0)
    max_lsd = st.sidebar.slider("Max Portfolio LSD", 0.0, 10.0, 3.0)
    min_bay_score = st.sidebar.slider("Minimum Deal Bay Score", 0, 100, 75)
    objective = st.sidebar.selectbox("Objective Function", ["Maximize AHA", "Maximize Bay Score"])

    if "deals" in st.session_state and len(st.session_state["deals"]) > 0:
        df = pd.DataFrame(st.session_state["deals"])
        filtered_df = df[df["Bay Score"] >= min_bay_score].copy()
        n = len(filtered_df)

        if n == 0:
            st.warning("No deals meet the Bay Score threshold.")
        else:
            w = cp.Variable(n)
            if objective == "Maximize AHA":
                obj = cp.Maximize(filtered_df["AHA"].values @ w)
            else:
                obj = cp.Maximize(filtered_df["Bay Score"].values @ w)

            constraints = [
                cp.sum(w) == 1,
                w >= 0,
                (filtered_df["Volatility"].values @ w) <= max_volatility,
                (filtered_df["LSD"].values @ w) <= max_lsd
            ]

            prob = cp.Problem(obj, constraints)
            prob.solve()

            if prob.status == "optimal":
                filtered_df["Weight"] = np.round(w.value, 4)
                filtered_df = filtered_df[filtered_df["Weight"] > 0.001]
                st.subheader("📈 Optimized Portfolio Allocation")
                st.dataframe(filtered_df)

                fig = px.bar(filtered_df, x="Deal", y="Weight", color="Bay Score",
                             title="Optimized Deal Weights by Bay Score")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("⚠️ Optimization failed. Try relaxing constraints.")
    else:
        st.info("No deal data available. Please add deals in the Scoring tab.")


# ---------------------- TAB 3: BACKTEST ------------------------
with st.tabs(["🔍 Deal Scoring", "📊 Portfolio Optimizer", "🕰️ Backtest Engine"])[2]:
    st.header("🕰️ Historical Backtest Engine")
    st.markdown("Upload historical public REIT data to simulate AHA, BAS, and Bay Score over time.")

    uploaded_file_bt = st.file_uploader("Upload a CSV of public REIT returns", type="csv", key="bt_file")

    if uploaded_file_bt:
        df_bt = pd.read_csv(uploaded_file_bt)

        # Check columns
        expected_bt_cols = ["Date", "Ticker", "Return (%)", "Volatility (%)", "Benchmark Return (%)"]
        if all(col in df_bt.columns for col in expected_bt_cols):
            df_bt["AHA"] = df_bt["Return (%)"] - df_bt["Benchmark Return (%)"]
            df_bt["BAS"] = df_bt["AHA"] / df_bt["Volatility (%)"]
            df_bt["Bay Score"] = (
                (df_bt["Return (%)"] / 15 * 0.25) +
                (df_bt["AHA"] / 4 * 0.20) +
                (df_bt["BAS"] / 0.6 * 0.25)
            ) * 100  # Simplified version

            st.success("✅ Backtest results calculated.")
            st.dataframe(df_bt)

            st.subheader("📈 Bay Score Trend")
            fig_bs = px.line(df_bt, x="Date", y="Bay Score", color="Ticker", title="Bay Score Over Time")
            st.plotly_chart(fig_bs, use_container_width=True)

            st.subheader("📊 AHA vs BAS Scatter")
            fig_scatter = px.scatter(df_bt, x="BAS", y="AHA", color="Ticker", hover_name="Date",
                                     title="AHA vs BAS: Public Tickers Over Time")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.error(f"Missing columns. Please include: {', '.join(expected_bt_cols)}")
    else:
        st.info("Upload a CSV with columns: Date, Ticker, Return (%), Volatility (%), Benchmark Return (%)")


# ---------------------- TAB 4: BULK UPLOAD & AUTO-SCORE ------------------------
with st.tabs(["🔍 Deal Scoring", "📊 Portfolio Optimizer", "🕰️ Backtest Engine", "📥 Bulk Upload & Auto-Score"])[3]:
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
