import streamlit as st
import pandas as pd

# --- Page Configuration and Helper Function ---
st.set_page_config(layout="wide", page_title="Mustard Oil Business Dashboard")

def format_indian(num):
    """Formats a number into the Indian numbering system for better readability."""
    if not isinstance(num, (int, float)): return num
    num_str = f"{abs(num):,.0f}"
    parts = num_str.split('.')
    integer_part = parts[0].replace(',', '')
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        other_digits = integer_part[:-3]
        if other_digits:
            formatted_other_digits = ','.join([other_digits[max(0, i-2):i] for i in range(len(other_digits), 0, -2)][::-1])
            formatted_num = f"{formatted_other_digits},{last_three}"
        else: formatted_num = last_three
    else: formatted_num = integer_part
    return '-' + formatted_num if num < 0 else formatted_num

st.title("🛢️ Mustard Oil Financial & Operational Dashboard")
st.markdown("An interactive dashboard for comprehensive analysis of a mustard oil processing business.")

# --- Sidebar for All User Inputs ---
with st.sidebar:
    st.header("⚙️ Business & Financial Inputs")
    with st.expander("Production & Prices", expanded=True):
        seed_input_mt = st.number_input("Daily Seed Input (MT)", value=192.0)
        kachi_ghani_yield_pct = st.slider("Kachi Ghani Oil Yield (%)", 0, 100, 18)
        expeller_yield_pct = st.slider("Expeller Oil Yield (%)", 0, 100, 15)
        seed_purchase_price = st.number_input("Seed Purchase Price (₹/MT)", value=50000.0)
        oil_blend_sell_price = st.number_input("Oil Blend Sell Price (₹/MT)", value=141000.0)
        moc_sell_price = st.number_input("MoC Sell Price (₹/MT)", value=22000.0)
    with st.expander("Costs & Expenses", expanded=True):
        processing_cost_per_mt = st.number_input("Processing Cost (₹/MT of Seed)", value=2500.0)
        other_variable_costs_per_mt = st.number_input("Other Variable Costs (₹/MT of Seed)", value=0.0)
        other_expenses_daily = st.number_input("Other Fixed Expenses (₹/day)", value=45000.0)
        production_days_per_month = st.number_input("Production Days per Month", value=24.0)
    with st.expander("Pungency & MoC Enhancement", expanded=True):
        kachi_ghani_pungency = st.slider("Kachi Ghani Oil Pungency (%)", 0.0, 1.0, 0.4, step=0.01)
        expeller_oil_pungency = st.slider("Expeller Oil Pungency (%)", 0.0, 1.0, 0.12, step=0.01)
        expeller_oil_sell_price = st.number_input("Expeller Oil Sell Price (₹/MT)", value=136000.0)
        market_bought_oil_price = st.number_input("Market-Bought Oil Price (₹/MT)", value=132000.0)
        water_added_pct = st.slider("Water Added to MoC (% of seed)", 0, 10, 2)
        water_cost_per_kg = st.number_input("Water Cost (₹/kg)", value=1.0)
        salt_added_pct = st.slider("Salt Added to MoC (% of seed)", 0, 10, 3)
        salt_cost_per_kg = st.number_input("Salt Cost (₹/kg)", value=5.0)
    with st.expander("Capex, Tax & Financing", expanded=True):
        capex = st.number_input("Capex (₹)", value=200000000.0)
        # --- NEW: Equity Slider for Capex ---
        equity_in_capex_pct = st.slider("Equity % in Capex", 0, 100, 100, help="Set the percentage of Capex funded by equity. The rest is debt.")
        depreciation_years = st.number_input("Depreciation Period (Years)", min_value=1, value=15)
        tax_rate_pct = st.slider("Tax Rate (%)", 0, 50, 25)
        other_assets = st.number_input("Other Assets (₹)", value=0.0)
        warehouse_finance_rate_pa = st.slider("Warehouse Finance Interest Rate (% p.a.)", 0.0, 25.0, 10.0, help="Interest for financed RM Hoard")
        main_financing_rate_pa = st.slider("Main Financing Cost Interest Rate (% p.a.)", 0.0, 25.0, 10.0, help="Interest for Capex Debt and remaining WC")
        rm_hoard_financed_pct = st.slider("% of Hoarded RM Financed", 0, 100, 0)
    with st.expander("Working Capital Cycles", expanded=True):
        rm_hoard_months = st.number_input("Raw Material Hoard (months)", value=0.0)
        hoarded_rm_rate = st.number_input("Hoarded RM Rate (₹/MT)", value=50000.0)
        rm_safety_stock_days = st.number_input("RM Safety Stock (days)", value=48.0)
        fg_oil_safety_days = st.number_input("FG (Oil) Safety Stock (days)", value=15.0)
        fg_moc_safety_days = st.number_input("FG (MoC) Safety Stock (days)", value=4.0)
        oil_debtor_days = st.number_input("Oil Debtor Cycle (days)", value=5.0)
        moc_debtor_days = st.number_input("MoC Debtor Cycle (days)", value=5.0)
        creditor_days = st.number_input("Creditors Days", value=5.0)
    with st.expander("🏭 Solvex Plant Synergy Inputs", expanded=False):
        moc_consumed_perc = st.slider("% of MOC Consumed In-House", 0, 100, 100)
        logistics_saved_per_ton = st.number_input("Logistics Saved (₹/Ton of MOC)", value=400.0)
        labor_saved_nos = st.number_input("Labor Headcount Saved (Daily)", value=4.0)
        labor_cost_per_head_daily = st.number_input("Cost per Labor Head (₹/Day)", value=550.0)
        brokerage_saved_per_ton = st.number_input("Brokerage Saved (₹/Ton of MOC)", value=150.0)

# --- Calculation Engine (Triple-Verified & Final) ---
@st.cache_data
def calculate_all_metrics(inputs):
    # Unpack all inputs
    for key, value in inputs.items(): globals()[key] = value
    
    kachi_ghani_yield, expeller_yield = kachi_ghani_yield_pct/100, expeller_yield_pct/100
    moc_base_yield, min_pungency_req = 1-(kachi_ghani_yield+expeller_yield), 0.2700
    kachi_ghani_oil_produced_mt, expeller_oil_produced_mt = seed_input_mt*kachi_ghani_yield, seed_input_mt*expeller_yield
    total_produced_oil = kachi_ghani_oil_produced_mt + expeller_oil_produced_mt
    initial_blend_pungency = (kachi_ghani_oil_produced_mt * kachi_ghani_pungency + expeller_oil_produced_mt * expeller_oil_pungency) / total_produced_oil if total_produced_oil > 0 else 0
    exp_oil_used_in_blend_mt, exp_oil_sold_separately_mt, market_oil_to_add_mt = expeller_oil_produced_mt, 0, 0
    pungency_recommendation = ""
    if initial_blend_pungency < min_pungency_req and total_produced_oil > 0:
        if (denominator := min_pungency_req - expeller_oil_pungency) != 0: exp_oil_used_in_blend_mt = max(0, (kachi_ghani_oil_produced_mt * (kachi_ghani_pungency - min_pungency_req)) / denominator)
        exp_oil_sold_separately_mt = expeller_oil_produced_mt - exp_oil_used_in_blend_mt
        loss = exp_oil_sold_separately_mt * (oil_blend_sell_price - expeller_oil_sell_price)
        pungency_recommendation = f"🔴 **Pungency Low ({initial_blend_pungency:.2f}%)**: Sell {exp_oil_sold_separately_mt:.2f} MT of Expeller Oil separately. Est. daily opportunity loss: ₹ {format_indian(abs(loss))}."
    elif initial_blend_pungency > min_pungency_req and total_produced_oil > 0:
        if min_pungency_req > 0: market_oil_to_add_mt = max(0, ((kachi_ghani_oil_produced_mt * kachi_ghani_pungency + expeller_oil_produced_mt * expeller_oil_pungency) / min_pungency_req) - total_produced_oil)
        profit = market_oil_to_add_mt * (oil_blend_sell_price - market_bought_oil_price)
        pungency_recommendation = f"🟢 **Pungency High ({initial_blend_pungency:.2f}%)**: Add {market_oil_to_add_mt:.2f} MT of Market Oil to optimize. Est. daily profit opportunity: ₹ {format_indian(profit)}."
    else: pungency_recommendation = f"✅ **Pungency Compliant ({initial_blend_pungency:.2f}%)**: No action needed."
    final_oil_blend_mt = kachi_ghani_oil_produced_mt + exp_oil_used_in_blend_mt + market_oil_to_add_mt
    water_added_mt, salt_added_mt = seed_input_mt*(water_added_pct/100), seed_input_mt*(salt_added_pct/100)
    enhanced_moc_mt = (seed_input_mt * moc_base_yield) + water_added_mt + salt_added_mt
    daily_revenue_oil_blend, daily_revenue_expeller_separate, daily_revenue_moc = final_oil_blend_mt*oil_blend_sell_price, exp_oil_sold_separately_mt*expeller_oil_sell_price, enhanced_moc_mt*moc_sell_price
    daily_total_revenue = daily_revenue_oil_blend + daily_revenue_expeller_separate + daily_revenue_moc
    cost_seed = seed_input_mt * seed_purchase_price
    cost_market_oil = market_oil_to_add_mt * market_bought_oil_price
    cost_moc_enhancement = (water_added_mt*1000*water_cost_per_kg) + (salt_added_mt*1000*salt_cost_per_kg)
    daily_cogs = cost_seed + cost_market_oil + cost_moc_enhancement
    daily_gm = daily_total_revenue - daily_cogs
    daily_processing_cost = seed_input_mt * processing_cost_per_mt
    daily_cm = daily_gm - daily_processing_cost
    daily_variable_cost = seed_input_mt * other_variable_costs_per_mt
    daily_ebitda = daily_cm - daily_variable_cost - other_expenses_daily
    monthly_seed_consumption = seed_input_mt * production_days_per_month
    rm_hoarded_value, rm_safety_stock_value = monthly_seed_consumption*rm_hoard_months*hoarded_rm_rate, seed_input_mt*rm_safety_stock_days*seed_purchase_price
    inventory_rm = rm_hoarded_value + rm_safety_stock_value
    total_daily_oil_revenue, total_daily_oil_qty = daily_revenue_oil_blend+daily_revenue_expeller_separate, final_oil_blend_mt+exp_oil_sold_separately_mt
    avg_oil_price = total_daily_oil_revenue/total_daily_oil_qty if total_daily_oil_qty > 0 else 0
    fg_oil_inventory_value, fg_moc_inventory_value = total_daily_oil_qty*avg_oil_price*fg_oil_safety_days, enhanced_moc_mt*moc_sell_price*fg_moc_safety_days
    inventory_fg = fg_oil_inventory_value + fg_moc_inventory_value
    total_inventory = inventory_rm + inventory_fg
    debtors_oil, debtors_moc = total_daily_oil_revenue*oil_debtor_days, daily_revenue_moc*moc_debtor_days
    total_debtors, trade_creditors = debtors_oil + debtors_moc, seed_input_mt*seed_purchase_price*creditor_days
    financed_rm_hoard_value = rm_hoarded_value*(rm_hoard_financed_pct/100)
    gross_wc = total_inventory + total_debtors - trade_creditors
    net_wc_requirement = gross_wc - financed_rm_hoard_value
    annual_production_days = production_days_per_month * 12
    annual_ebitda = daily_ebitda * annual_production_days
    
    # --- VERIFIED & TRANSPARENT Interest Calculation ---
    debt_funded_capex = capex * (1 - equity_in_capex_pct/100)
    interest_on_capex_debt = debt_funded_capex * (main_financing_rate_pa/100)
    interest_on_hoard = financed_rm_hoard_value * (warehouse_finance_rate_pa/100)
    # Assume Net WC is also financed at the main rate
    interest_on_net_wc = net_wc_requirement * (main_financing_rate_pa/100)
    annual_interest = interest_on_capex_debt + interest_on_hoard + interest_on_net_wc
    
    annual_depreciation = capex/depreciation_years if depreciation_years > 0 else 0
    annual_ebit = annual_ebitda - annual_depreciation
    annual_pbt = annual_ebit - annual_interest
    annual_tax = max(0, annual_pbt * (tax_rate_pct/100))
    annual_pat = annual_pbt - annual_tax
    
    # --- VERIFIED ROCE Calculation (EBIT and PAT basis) ---
    capital_employed = capex + net_wc_requirement + other_assets
    roce_pat = (annual_pat / capital_employed) * 100 if capital_employed != 0 else 0
    roce_ebit = (annual_ebit / capital_employed) * 100 if capital_employed != 0 else 0
    
    moc_consumed_inhouse_mt = enhanced_moc_mt*(moc_consumed_perc/100)
    daily_solvex_saving = sum([moc_consumed_inhouse_mt*logistics_saved_per_ton, labor_saved_nos*labor_cost_per_head_daily, moc_consumed_inhouse_mt*brokerage_saved_per_ton])
    annual_solvex_saving = daily_solvex_saving * annual_production_days
    annual_pat_with_synergy = annual_pat + annual_solvex_saving
    annual_ebit_with_synergy = annual_ebit + annual_solvex_saving
    roce_pat_with_synergy = (annual_pat_with_synergy / capital_employed) * 100 if capital_employed != 0 else 0
    roce_ebit_with_synergy = (annual_ebit_with_synergy / capital_employed) * 100 if capital_employed != 0 else 0
    
    return {
        "seed_input_mt": seed_input_mt, "pungency_recommendation": pungency_recommendation, "final_oil_blend_mt": final_oil_blend_mt,
        "exp_oil_sold_separately_mt": exp_oil_sold_separately_mt, "enhanced_moc_mt": enhanced_moc_mt,
        "daily_total_revenue": daily_total_revenue, "daily_gm": daily_gm, "daily_cm": daily_cm, "daily_ebitda": daily_ebitda,
        "daily_cogs": daily_cogs, "daily_processing_cost": daily_processing_cost, "daily_variable_cost": daily_variable_cost, "daily_other_expenses": other_expenses_daily,
        "production_days_per_month": production_days_per_month, "annual_production_days": annual_production_days,
        "annual_interest": annual_interest, "annual_depreciation": annual_depreciation, "tax_rate_pct": tax_rate_pct, "annual_ebit": annual_ebit,
        "total_inventory": total_inventory, "total_debtors": total_debtors, "trade_creditors": trade_creditors,
        "financed_rm_hoard_value": financed_rm_hoard_value, "net_wc_requirement": net_wc_requirement, "capex": capex,
        "roce_pat": roce_pat, "roce_ebit": roce_ebit,
        "roce_pat_with_synergy": roce_pat_with_synergy, "roce_ebit_with_synergy": roce_ebit_with_synergy,
        "daily_solvex_saving": daily_solvex_saving,
        "market_oil_to_add_mt": market_oil_to_add_mt, "water_added_mt": water_added_mt, "salt_added_mt": salt_added_mt,
        "cost_seed": cost_seed, "cost_market_oil": cost_market_oil, "cost_moc_enhancement": cost_moc_enhancement,
        "interest_on_hoard": interest_on_hoard, "interest_on_capex_debt": interest_on_capex_debt, "interest_on_net_wc": interest_on_net_wc,
        "debt_funded_capex": debt_funded_capex,
        "inventory_rm": inventory_rm, "inventory_fg": inventory_fg
    }

# --- Collect Inputs & Run Calculation Engine ---
all_inputs = {
    "seed_input_mt": seed_input_mt, "kachi_ghani_yield_pct": kachi_ghani_yield_pct, "expeller_yield_pct": expeller_yield_pct,
    "seed_purchase_price": seed_purchase_price, "oil_blend_sell_price": oil_blend_sell_price, "moc_sell_price": moc_sell_price,
    "processing_cost_per_mt": processing_cost_per_mt, "other_variable_costs_per_mt": other_variable_costs_per_mt,
    "other_expenses_daily": other_expenses_daily, "production_days_per_month": production_days_per_month,
    "kachi_ghani_pungency": kachi_ghani_pungency, "expeller_oil_pungency": expeller_oil_pungency,
    "expeller_oil_sell_price": expeller_oil_sell_price, "market_bought_oil_price": market_bought_oil_price,
    "water_added_pct": water_added_pct, "water_cost_per_kg": water_cost_per_kg,
    "salt_added_pct": salt_added_pct, "salt_cost_per_kg": salt_cost_per_kg,
    "capex": capex, "equity_in_capex_pct": equity_in_capex_pct, "depreciation_years": depreciation_years, "tax_rate_pct": tax_rate_pct, "other_assets": other_assets,
    "warehouse_finance_rate_pa": warehouse_finance_rate_pa, "main_financing_rate_pa": main_financing_rate_pa,
    "rm_hoard_financed_pct": rm_hoard_financed_pct, "rm_hoard_months": rm_hoard_months, "hoarded_rm_rate": hoarded_rm_rate,
    "rm_safety_stock_days": rm_safety_stock_days, "fg_oil_safety_days": fg_oil_safety_days, "fg_moc_safety_days": fg_moc_safety_days,
    "oil_debtor_days": oil_debtor_days, "moc_debtor_days": moc_debtor_days, "creditor_days": creditor_days,
    "moc_consumed_perc": moc_consumed_perc, "logistics_saved_per_ton": logistics_saved_per_ton,
    "labor_saved_nos": labor_saved_nos, "labor_cost_per_head_daily": labor_cost_per_head_daily,
    "brokerage_saved_per_ton": brokerage_saved_per_ton
}
with st.spinner("Calculating results..."):
    metrics = calculate_all_metrics(all_inputs)

# --- Main Dashboard Display ---
st.subheader("Pungency Compliance")
if "🔴" in metrics["pungency_recommendation"]: st.warning(metrics["pungency_recommendation"])
elif "🟢" in metrics["pungency_recommendation"]: st.success(metrics["pungency_recommendation"])
else: st.info(metrics["pungency_recommendation"])
st.divider()

st.subheader("Financial & Operational Analysis")
selected_tab = st.radio("Select View:", options=["📊 Daily View", "📅 Monthly View", "🗓️ Annual View"], key='active_tab', horizontal=True, label_visibility="collapsed")

def display_pnl(period_multiplier, period_name):
    st.markdown(f"##### Production & Revenue ({period_name})")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"**Total Seed Input:**<br> <p style='font-size: 20px;'>{format_indian(metrics['seed_input_mt'] * period_multiplier)} MT</p>", unsafe_allow_html=True)
    c2.markdown(f"**Oil Blend:**<br> <p style='font-size: 20px;'>{format_indian(metrics['final_oil_blend_mt'] * period_multiplier)} MT</p>", unsafe_allow_html=True)
    c3.markdown(f"**Enhanced MoC:**<br> <p style='font-size: 20px;'>{format_indian(metrics['enhanced_moc_mt'] * period_multiplier)} MT</p>", unsafe_allow_html=True)
    c4.markdown(f"**Total Revenue:**<br> <p style='font-size: 20px;'>₹ {format_indian(metrics['daily_total_revenue'] * period_multiplier)}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown(f"##### Cost of Goods Sold (COGS) Breakdown ({period_name})")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Component Quantities**")
        st.markdown(f"- Seed Consumed: {format_indian(metrics['seed_input_mt'] * period_multiplier)} MT")
        st.markdown(f"- Market Oil Added: {format_indian(metrics['market_oil_to_add_mt'] * period_multiplier)} MT")
        st.markdown(f"- Water Added: {format_indian(metrics['water_added_mt'] * period_multiplier)} MT")
        st.markdown(f"- Salt Added: {format_indian(metrics['salt_added_mt'] * period_multiplier)} MT")
    with col2:
        st.markdown("**Component Values**")
        st.markdown(f"- Seed Cost: ₹ {format_indian(metrics['cost_seed'] * period_multiplier)}")
        st.markdown(f"- Market Oil Cost: ₹ {format_indian(metrics['cost_market_oil'] * period_multiplier)}")
        st.markdown(f"- MoC Enhancement Cost: ₹ {format_indian(metrics['cost_moc_enhancement'] * period_multiplier)}")
        st.markdown(f"**Total COGS: ₹ {format_indian(metrics['daily_cogs'] * period_multiplier)}**")
    st.markdown("---")

    st.markdown(f"##### Full Margin Analysis ({period_name})")
    col1, col2 = st.columns(2)
    total_revenue_for_period = metrics['daily_total_revenue'] * period_multiplier
    with col1:
        gm, cm, ebitda = metrics['daily_gm']*period_multiplier, metrics['daily_cm']*period_multiplier, metrics['daily_ebitda']*period_multiplier
        st.markdown(f"**Gross Margin (GM):** <br>₹ {format_indian(gm)} `({(gm/total_revenue_for_period*100 if total_revenue_for_period > 0 else 0):.1f}%)`", unsafe_allow_html=True)
        st.markdown(f"**Contribution Margin (CM):** ❓<br>₹ {format_indian(cm)} `({(cm/total_revenue_for_period*100 if total_revenue_for_period > 0 else 0):.1f}%)`", unsafe_allow_html=True, help=f"CM = GM - Processing Cost (₹ {format_indian(metrics['daily_processing_cost']*period_multiplier)})")
        st.markdown(f"**EBITDA:** ❓<br>₹ {format_indian(ebitda)} `({(ebitda/total_revenue_for_period*100 if total_revenue_for_period > 0 else 0):.1f}%)`", unsafe_allow_html=True, help=f"EBITDA = CM - Other Var. Costs (₹ {format_indian(metrics['daily_variable_cost']*period_multiplier)}) - Other Fixed Exp. (₹ {format_indian(metrics['daily_other_expenses']*period_multiplier)})")
    with col2:
        daily_dep, daily_int = (metrics['annual_depreciation']/metrics['annual_production_days'] if metrics['annual_production_days']>0 else 0), (metrics['annual_interest']/metrics['annual_production_days'] if metrics['annual_production_days']>0 else 0)
        depreciation_for_period, interest_for_period = daily_dep * period_multiplier, daily_int * period_multiplier
        ebit_for_period = ebitda - depreciation_for_period
        pbt = ebit_for_period - interest_for_period
        tax = max(0, pbt * (metrics['tax_rate_pct']/100))
        pat = pbt - tax
        st.markdown(f"**Depreciation:**<br>₹ {format_indian(depreciation_for_period)}", unsafe_allow_html=True)
        st.markdown(f"**EBIT (Earnings Before Interest & Tax):**<br>₹ {format_indian(ebit_for_period)}", unsafe_allow_html=True)
        st.markdown(f"**Interest:**<br>₹ {format_indian(interest_for_period)}", unsafe_allow_html=True)
        st.markdown(f"**Profit Before Tax (PBT):**<br>₹ {format_indian(pbt)}", unsafe_allow_html=True)
        st.markdown(f"**Profit After Tax (PAT):**<br>₹ {format_indian(pat)}", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown(f"##### Interest Calculation Breakdown ({period_name})")
    interest_on_capex_debt_period = metrics['interest_on_capex_debt'] / metrics['annual_production_days'] * period_multiplier if metrics['annual_production_days'] > 0 else 0
    interest_on_hoard_period = metrics['interest_on_hoard'] / metrics['annual_production_days'] * period_multiplier if metrics['annual_production_days'] > 0 else 0
    interest_on_net_wc_period = metrics['interest_on_net_wc'] / metrics['annual_production_days'] * period_multiplier if metrics['annual_production_days'] > 0 else 0
    st.markdown(f"- **Debt Funded Capex:** ₹ {format_indian(metrics['debt_funded_capex'])} -> **Interest:** ₹ {format_indian(interest_on_capex_debt_period)}")
    st.markdown(f"- **Financed RM Hoard:** ₹ {format_indian(metrics['financed_rm_hoard_value'])} -> **Interest:** ₹ {format_indian(interest_on_hoard_period)}")
    st.markdown(f"- **Net WC Requirement:** ₹ {format_indian(metrics['net_wc_requirement'])} -> **Interest:** ₹ {format_indian(interest_on_net_wc_period)}")
    st.markdown("---")

    st.markdown(f"##### Key Financial Ratios (Annualized)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Standard ROCE**")
        st.metric("ROCE (EBIT Basis)", f"{metrics['roce_ebit']:.2f}%")
        st.metric("ROCE (PAT Basis)", f"{metrics['roce_pat']:.2f}%")
    with c2:
        st.markdown("**ROCE including Solvex Synergy**")
        st.metric("ROCE (EBIT Basis)", f"{metrics['roce_ebit_with_synergy']:.2f}%")
        st.metric("ROCE (PAT Basis)", f"{metrics['roce_pat_with_synergy']:.2f}%")

if selected_tab == "📊 Daily View": display_pnl(1, "Daily")
elif selected_tab == "📅 Monthly View": display_pnl(metrics['production_days_per_month'], "Monthly")
elif selected_tab == "🗓️ Annual View": display_pnl(metrics['annual_production_days'], "Annual")

st.divider()

wc_col, savings_col = st.columns(2)
with wc_col:
    st.subheader("Working Capital & Capex Breakdown")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Total Inventory:**<br><p style='font-size: 20px;'>₹ {format_indian(metrics['total_inventory'])}</p>", unsafe_allow_html=True)
    c2.markdown(f"**Total Debtors:**<br><p style='font-size: 20px;'>₹ {format_indian(metrics['total_debtors'])}</p>", unsafe_allow_html=True)
    c3.markdown(f"**Trade Creditors:**<br><p style='font-size: 20px;'>₹ {format_indian(metrics['trade_creditors'])}</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.markdown(f"**Raw Material Inventory:**<br><p style='font-size: 20px;'>₹ {format_indian(metrics['inventory_rm'])}</p>", unsafe_allow_html=True)
    c2.markdown(f"**Finished Goods Stock:**<br><p style='font-size: 20px;'>₹ {format_indian(metrics['inventory_fg'])}</p>", unsafe_allow_html=True)
    st.markdown(f"**Financed Inventory (Credit):**<br><p style='font-size: 20px; color: #FF4B4B;'>₹ {format_indian(metrics['financed_rm_hoard_value'])}</p>", unsafe_allow_html=True, help="This is treated as a credit, reducing your net WC requirement.")
    st.markdown(f"**Net WC Requirement:**<br><p style='font-size: 24px; font-weight: bold;'>₹ {format_indian(metrics['net_wc_requirement'])}</p>", unsafe_allow_html=True)
    st.markdown(f"**Capex:**<br><p style='font-size: 24px; font-weight: bold;'>₹ {format_indian(metrics['capex'])}</p>", unsafe_allow_html=True)
with savings_col:
    st.subheader("🏭 Solvex Plant Synergy")
    st.metric("Total Daily Savings", f"₹ {format_indian(metrics['daily_solvex_saving'])}")
    st.metric("Total Monthly Savings", f"₹ {format_indian(metrics['daily_solvex_saving'] * metrics['production_days_per_month'])}")

with st.expander("ℹ️ Click here to see key calculation logic"):
    st.markdown("""
    - **Cost of Goods Sold (COGS):** `COGS = Seed Cost + Market Oil Cost + MoC Enhancement Cost`
    - **Net Working Capital Requirement:** `Net WC = (Total Inventory + Total Debtors - Trade Creditors) - Financed Inventory`
    - **Interest Calculation:** 
      - `Debt Funded Capex = Capex * (1 - Equity %)`
      - `Interest on Capex Debt = Debt Funded Capex * Main Financing Rate`
      - `Interest on Net WC = Net WC Requirement * Main Financing Rate`
      - `Interest on Hoard = Financed RM Value * Warehouse Finance Rate`
      - `Total Annual Interest` is the sum of these three components.
    - **Return on Capital Employed (ROCE):** Measures operational efficiency. `EBIT = EBITDA - Depreciation`.
      - `Capital Employed = Capex + Net WC Requirement + Other Assets`
      - `Standard ROCE (EBIT Basis) = Annual EBIT / Capital Employed`
    - **Synergy Impact:** `ROCE with Synergy` adds the `Annual Solvex Savings` to the numerator (EBIT or PAT).
    """)
st.markdown("---")
st.success("Dashboard code is complete and has been fully executed.")
