import streamlit as st
import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


st.set_page_config(page_title="Bay Street Hospitality Scoring", layout="wide")


# Bay Street logo branding
st.markdown('''
<div style="display:flex; align-items:center; justify-content:space-between;">
   <img src="https://cdn.prod.website-files.com/66ec88f6d7b63833eb28d6a7/66ec8de11054852c315965b0_BAY%20STREET%20HOSPITALITY-03-p-800.png" style="height:60px;" />
</div>
''', unsafe_allow_html=True)


st.title("🏨 Bay Street Hospitality Investment Scoring Dashboard")


# GSheet connection
def get_gsheet_connection():
   scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
   creds = ServiceAccountCredentials.from_json_keyfile_dict(
       dict(st.secrets["google_sheets"]), scope
   )
   client = gspread.authorize(creds)
  
   # Replace this line:
   # return client.open("Bay Street Investment Tracker").worksheet("Investments")


   # With this:
   return client.open_by_key("1c2gQT1fSznq4crXa8c2C-urSs_fEj6PysvTM4zxXrwg").worksheet("Investments")


# Load all rows
def load_investments_from_gsheet(sheet):
   data = sheet.get_all_records()
   return pd.DataFrame(data)


# Add row to sheet
def add_investment_to_sheet(sheet, investment):
   sheet.append_row(investment)


# Overwrite a specific row in the sheet
def update_investment_in_gsheet(sheet, row_idx, investment):
   sheet.delete_row(row_idx)
   sheet.insert_row(investment, row_idx)




# investment Input & Scoring UI (Part 2)
st.sidebar.header("📝 Input New Investment")


investment_name = st.sidebar.text_input("Investment Name")
asset_type = st.sidebar.selectbox("Asset Type", ["Hotel", "Operator", "Developer", "Operator & Developer", "Portfolio of Hotels", "REIT", "Opportunistic", "Ticker Symbol"])
region = st.sidebar.selectbox("Region", ["Americas", "Europe", "APAC", "ME", "ASEAN", "Opportunistic"])
public_private = st.sidebar.radio("Public or Private?", ["Public", "Private"])
saved_by = st.sidebar.text_input("Saved By (Initials or Email)", value="")


projected_irr = st.sidebar.number_input("Projected IRR (%)", min_value=0.0, max_value=100.0, value=12.0)
coc_yield = st.sidebar.number_input("Cash-on-Cash Yield (%)", min_value=0.0, max_value=100.0, value=6.0)
volatility = st.sidebar.number_input("Volatility Estimate (%)", min_value=0.0, max_value=100.0, value=10.0)
illiquidity_premium = st.sidebar.number_input("Illiquidity Premium (%)", min_value=0.0, max_value=10.0, value=2.0)
esg_score = st.sidebar.slider("ESG Impact Score (1–5)", 1, 5, 3)
sponsor_coinvest = st.sidebar.number_input("Sponsor Co-Investment (%)", min_value=0.0, max_value=100.0, value=5.0)


op_leverage = st.sidebar.radio("Operational Leverage?", ["Y", "N"])
brand_reposition = st.sidebar.radio("Brand Repositioning Opportunity?", ["Y", "N"])
mgmt_transition = st.sidebar.radio("Management Transition?", ["Y", "N"])


# Core calculations
aha = projected_irr - (8 + illiquidity_premium)
bas = aha / volatility if volatility != 0 else 0


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




# Part 3: Load + Edit investments + Filters
sheet = get_gsheet_connection()


if st.button("🔄 Refresh investments from Google Sheets"):
   st.session_state["gsheet_investments"] = load_investments_from_gsheet(sheet)
   st.success("✅ Refreshed Investments from Google Sheets")


if "gsheet_investments" not in st.session_state:
   st.session_state["gsheet_investments"] = load_investments_from_gsheet(sheet)


if "gsheet_investments" in st.session_state and not st.session_state["gsheet_investments"].empty:
   df_all = st.session_state["gsheet_investments"]
  
   st.subheader("📂 All Investments from Google Sheets")


   # Filter options
   region_filter = st.selectbox("🌍 Filter by Region", ["All"] + sorted(df_all["Region"].unique()))
   type_filter = st.selectbox("🏢 Filter by Asset Type", ["All"] + sorted(df_all["Asset Type"].unique()))
   esg_filter = st.slider("🌱 Min ESG Score", 1, 5, 3)


   filtered_df = df_all.copy()
   if region_filter != "All":
       filtered_df = filtered_df[filtered_df["Region"] == region_filter]
   if type_filter != "All":
       filtered_df = filtered_df[filtered_df["Asset Type"] == type_filter]
   filtered_df = filtered_df[filtered_df["ESG Score"] >= esg_filter]


   st.dataframe(filtered_df)


   # Dropdown to select existing investment
   st.subheader("✏️ Edit Existing investment")
   selected_investment = st.selectbox("Select investment to Edit", options=filtered_df["Investment Name"].unique())


   if selected_investment:
       investment_row = df_all[df_all["Investment Name"] == selected_investment].iloc[0]
       st.write("Selected investment Details:")
       st.json(investment_row.to_dict())
       st.warning("✳️ Editing in UI is not yet live — save to Google Sheets manually if needed.")




# Part 4: Portfolio Optimizer using investments from Google Sheets
import cvxpy as cp
import plotly.express as px


st.subheader("📊 Optimizer: Build Portfolio from Saved Investments")


if not st.session_state["gsheet_Investments"].empty:
   df_opt = st.session_state["gsheet_Investments"].copy()


   st.sidebar.header("⚙️ Optimization Constraints")
   max_volatility = st.sidebar.slider("Max Portfolio Volatility (%)", 5.0, 25.0, 12.0)
   max_lsd = st.sidebar.slider("Max Portfolio LSD (%)", 0.0, 10.0, 3.0)
   min_bay_score = st.sidebar.slider("Minimum Bay Score", 0, 100, 70)
   objective = st.sidebar.selectbox("Objective Function", ["Maximize AHA", "Maximize Bay Score"])


   df_opt = df_opt[df_opt["Bay Score"] >= min_bay_score]
   n = len(df_opt)


   if n == 0:
       st.warning("No investments meet the filter criteria.")
   else:
       w = cp.Variable(n)
       if objective == "Maximize AHA":
           obj = cp.Maximize(df_opt["AHA"].values @ w)
       else:
           obj = cp.Maximize(df_opt["Bay Score"].values @ w)


       constraints = [
           cp.sum(w) == 1,
           w >= 0,
           (df_opt["Volatility (%)"].values @ w) <= max_volatility,
           (df_opt["Illiquidity Premium (%)"].values @ w) <= max_lsd
       ]


       prob = cp.Problem(obj, constraints)
       prob.solve()


       if prob.status == "optimal":
           df_opt["Weight"] = np.round(w.value, 4)
           df_opt = df_opt[df_opt["Weight"] > 0.001]
           st.success("✅ Optimization successful.")
           st.dataframe(df_opt)


           fig = px.bar(df_opt, x="Investment Name", y="Weight", color="Bay Score", title="Optimized Portfolio Weights")
           st.plotly_chart(fig, use_container_width=True)
       else:
           st.error("❌ Optimization failed. Try loosening constraints.")
else:
   st.info("Please load investments from Google Sheets first.")




# Part 5: Backtest Visualizer from Saved investments
import plotly.express as px


st.subheader("📈 Backtest Visualizer")


if not st.session_state["gsheet_Investments"].empty:
   df_viz = st.session_state["gsheet_Investments"].copy()
  
   st.markdown("Visualize Bay Score, AHA, and BAS from saved investments in Google Sheets.")


   fig1 = px.scatter(df_viz, x="Volatility (%)", y="AHA", color="Region", size="Bay Score", hover_name="Investment Name",
                     title="AHA vs Volatility")
   st.plotly_chart(fig1, use_container_width=True)


   fig2 = px.scatter(df_viz, x="BAS", y="Bay Score", color="Asset Type", size="IRR (%)", hover_name="Investment Name",
                     title="Bay Score vs BAS")
   st.plotly_chart(fig2, use_container_width=True)


   fig3 = px.line(df_viz.sort_values("Date Added"), x="Date Added", y="Bay Score", color="Investment Name",
                  title="Bay Score Trend Over Time")
   st.plotly_chart(fig3, use_container_width=True)
else:
   st.info("📂 No investments loaded. Please load from Google Sheets first.")



