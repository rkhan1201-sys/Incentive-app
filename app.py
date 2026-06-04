import streamlit as st
import pandas as pd
import numpy as np

# Set up page config
st.set_page_config(page_title="Incentive Policy Modeler", layout="wide")

st.title("📊 Incentive Policy Simulation Tool")
st.markdown("### Assurance Farm Cafe — Higher Management Decision Dashboard")
st.write("Use this interactive model to safely modify sales performance tiers and multipliers while verifying the baseline protection rule.")

# 1. LOAD AND CLEAN DATA FROM THE REFERENCE FILE
@st.cache_data
def load_and_process_data():
    filepath = "Incentive Calc sheet.xlsx"
    df_calc = pd.read_excel(filepath, sheet_name='Incentive Calc')
    
    data_rows = []
    current_outlet = None

    for idx, row in df_calc.iterrows():
        if idx < 6:
            continue
        
        val_b = str(row['Unnamed: 1']).strip()
        val_c = str(row['Unnamed: 2']).strip()
        
        # Track active outlet location
        if val_b != 'nan' and val_b != 'Totals' and 'Name of Outlet' not in val_b:
            current_outlet = val_b
        
        # Extract calendar months evaluated in the workbook
        if val_c in ['Jan', 'Feb', 'Mar', 'Apr']:
            prev_inc = row['Unnamed: 6']
            # Clean and parse numeric values safely
            try:
                actual_sales = float(row['Unnamed: 3']) if pd.notna(row['Unnamed: 3']) else 0.0
                target_sales = float(row['Unnamed: 4']) if pd.notna(row['Unnamed: 4']) else 0.0
                prev_incentive = float(prev_inc) if pd.notna(prev_inc) else 0.0
            except:
                continue
                
            achieved_pct = (actual_sales / target_sales * 100) if target_sales > 0 else 0.0
            
            data_rows.append({
                'Outlet': current_outlet if current_outlet else "Unknown Outlet",
                'Month': val_c,
                'Actual Sales': actual_sales,
                'Target': target_sales,
                'Target Achieved %': achieved_pct,
                'Prev Incentive': prev_incentive
            })
            
    return pd.DataFrame(data_rows)

try:
    df_base = load_and_process_data()
except Exception as e:
    st.error(f"Error loading 'Incentive Calc sheet.xlsx': {e}. Please ensure the file is in the same folder.")
    st.stop()

# 2. SIDEBAR - DYNAMIC CONTROL PANEL FOR MANAGEMENT
st.sidebar.header("⚙️ Policy Configurations")
st.sidebar.markdown("Adjust targets and multipliers below to check financial impacts instantly.")

st.sidebar.subheader("Tier Multipliers (%)")
m1 = st.sidebar.slider("Tier 1: 50%-59% Multiplier", 0.0, 3.0, 0.50, step=0.05) / 100
m2 = st.sidebar.slider("Tier 2: 60%-69% Multiplier", 0.0, 3.0, 0.75, step=0.05) / 100
m3 = st.sidebar.slider("Tier 3: 70%-79% Multiplier", 0.0, 3.0, 1.00, step=0.05) / 100
m4 = st.sidebar.slider("Tier 4: 80%-89% Multiplier", 0.0, 3.0, 1.25, step=0.05) / 100
m5 = st.sidebar.slider("Tier 5: 90%-99% Multiplier", 0.0, 5.0, 1.50, step=0.05) / 100
m6 = st.sidebar.slider("Tier 6: 100%-109% Multiplier", 0.0, 10.0, 5.00, step=0.1) / 100
m7 = st.sidebar.slider("Tier 7: 110%-119% Multiplier", 0.0, 12.0, 6.00, step=0.1) / 100
m8 = st.sidebar.slider("Tier 8: 120%+ Multiplier", 0.0, 15.0, 7.00, step=0.1) / 100

# 3. CORE SIMULATION ENGINE
def calculate_new_incentive(achieved_pct, actual_sales):
    if achieved_pct >= 120: return actual_sales * m8
    elif achieved_pct >= 110: return actual_sales * m7
    elif achieved_pct >= 100: return actual_sales * m6
    elif achieved_pct >= 90: return actual_sales * m5
    elif achieved_pct >= 80: return actual_sales * m4
    elif achieved_pct >= 70: return actual_sales * m3
    elif achieved_pct >= 60: return actual_sales * m2
    elif achieved_pct >= 50: return actual_sales * m1
    return 0.0

# Apply policy rules
df_sim = df_base.copy()
df_sim['Proposed Incentive'] = df_sim.apply(lambda r: calculate_new_incentive(r['Target Achieved %'], r['Actual Sales']), axis=1)
df_sim['Variance'] = df_sim['Proposed Incentive'] - df_sim['Prev Incentive']
df_sim['Status'] = df_sim['Variance'].apply(lambda v: "🔴 Below Policy" if v < 0 else "✅ Safe")

# Group data by Outlet for corporate reporting
df_outlet = df_sim.groupby('Outlet').agg({
    'Actual Sales': 'sum',
    'Prev Incentive': 'sum',
    'Proposed Incentive': 'sum',
    'Variance': 'sum'
}).reset_index()

df_outlet['Status'] = df_outlet['Variance'].apply(lambda v: "🔴 Violates Guardrail" if v < 0 else "✅ Compliant")

# 4. EXECUTIVE SUMMARY METRICS
total_old = df_sim['Prev Incentive'].sum()
total_new = df_sim['Proposed Incentive'].sum()
net_change = total_new - total_old
violations_count = (df_outlet['Variance'] < 0).sum()

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Past Payout", f"{total_old:,.2f} BDT")
with c2:
    st.metric("Proposed Policy Payout", f"{total_new:,.2f} BDT", delta=f"{net_change:,.2f} BDT", delta_color="inverse")
with c3:
    if violations_count > 0:
        st.error(f"⚠️ {violations_count} Outlets Below Baseline!")
    else:
        st.success("🎉 All outlets meet or exceed baseline!")

st.markdown("---")

# 5. DATA VIEWS
tab1, tab2 = st.tabs(["Store Performance Summary", "Granular Monthly Ledger"])

with tab1:
    st.subheader("Outlet-wise Impact Summary")
    st.write("Review the net effect of the parameters across total accumulated windows:")
    
    # Apply beautiful conditional row coloring for management presentation
    def style_summary(val):
        color = 'background-color: #ffcccc' if val == "🔴 Violates Guardrail" else 'background-color: #d4edda'
        return color

    st.dataframe(
        df_outlet.style.map(style_summary, subset=['Status'])
        .format({'Actual Sales': '{:,.2f}', 'Prev Incentive': '{:,.2f}', 'Proposed Incentive': '{:,.2f}', 'Variance': '{:,.2f}'}),
        use_container_width=True
    )

with tab2:
    st.subheader("Month-by-Month Simulation Tracking")
    st.write("Deep dive into specific operational months to look for baseline errors:")
    
    def style_granular(val):
        return 'background-color: #ffcccc' if val == "🔴 Below Policy" else ''

    st.dataframe(
        df_sim.style.map(style_granular, subset=['Status'])
        .format({'Actual Sales': '{:,.2f}', 'Target': '{:,.2f}', 'Target Achieved %': '{:.2f}%', 'Prev Incentive': '{:,.2f}', 'Proposed Incentive': '{:,.2f}', 'Variance': '{:,.2f}'}),
        use_container_width=True
    )
