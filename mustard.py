import streamlit as st

def format_cr(n):
    try:
        n = float(n)
    except:
        return n
    return f"₹{n/1e7:.2f} Cr"

def format_inr(n):
    try:
        n = float(n)
    except:
        return n
    return f"₹{n:,.0f}"

st.set_page_config(page_title="Mustard Plant Dashboard", layout="wide")

# --- Soft blue background, no image ---
st.markdown("""
    <style>
    .stApp {
        background-color: #e8f0fe;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 Mustard Seed Processing Dashboard")

# --- Input Section: Grouped ---
st.header("Inputs")

colq, colr, coly, colm = st.columns([1.5,1.2,1.2,1.2])

with colq:
    st.subheader("Quantities & Yields")
    seed_input = st.number_input("Seed Input (MT)", min_value=0.0, value=200.0, format="%.2f")
    kg_oil_yield_pct = st.number_input("Kachi Ghani Oil Yield (% of seeds)", min_value=0.0, max_value=100.0, value=18.0, format="%.2f")
    exp_oil_yield_pct = st.number_input("Expeller Oil Yield (% of seeds)", min_value=0.0, max_value=100.0, value=15.0, format="%.2f")
    market_oil = st.number_input("Market-Bought Oil (MT)", min_value=0.0, value=0.0, format="%.2f")
    moc_base_yield_pct = 100.0 - (kg_oil_yield_pct + exp_oil_yield_pct)
    st.markdown(f"**MoC Base Yield (% of seeds):** {moc_base_yield_pct:.2f}")

with colr:
    st.subheader("Rates / Prices")
    seed_price = st.number_input("Seed Purchase Price (₹/MT)", min_value=0.0, value=57000.0, format="%.2f")
    hoarded_rm_rate = st.number_input("Hoarded RM Rate (₹/MT)", min_value=0.0, value=57000.0, format="%.2f")
    oil_sell_price = st.number_input("Oil Blend Sell Price (₹/MT)", min_value=0.0, value=138000.0, format="%.2f")
    exp_oil_sell_price = st.number_input("Expeller Oil Sell Price (₹/MT)", min_value=0.0, value=135500.0, format="%.2f")
    market_oil_price = st.number_input("Market-Bought Oil Price (₹/MT)", min_value=0.0, value=133000.0, format="%.2f")
    moc_sell_price = st.number_input("MoC Sell Price (₹/MT)", min_value=0.0, value=22500.0, format="%.2f")

with coly:
    st.subheader("Yields / Pungency")
    kg_pungency = st.number_input("Kachi Ghani Oil Pungency (%)", min_value=0.0, value=0.4, format="%.4f")
    exp_pungency = st.number_input("Expeller Oil Pungency (%)", min_value=0.0, value=0.12, format="%.4f")

with colm:
    st.subheader("MoC Enhancement")
    water_pct = st.number_input("Water Added (% of seed input)", min_value=0.0, value=2.0, format="%.2f")
    water_cost = st.number_input("Water Cost (₹/kg)", min_value=0.0, value=1.0, format="%.2f")
    salt_pct = st.number_input("Salt Added (% of seed input)", min_value=0.0, value=3.0, format="%.2f")
    salt_cost = st.number_input("Salt Cost (₹/kg)", min_value=0.0, value=5.0, format="%.2f")

st.markdown("---")

# --- Section: Processing & Revenue Logic ---
kg_oil = seed_input * (kg_oil_yield_pct / 100)
exp_oil = seed_input * (exp_oil_yield_pct / 100)
total_oil = kg_oil + exp_oil + market_oil

# Blend Pungency Calculation
blend_pungency = (
    (kg_oil * kg_pungency) +
    (exp_oil * exp_pungency) +
    (market_oil * 0)
) / total_oil if total_oil else 0.0

st.subheader("Blend Pungency")
st.markdown(f"**Blend Pungency:** {blend_pungency:.4f} %")

# --- Pungency Adjustment Logic ---
pungency_ok = abs(blend_pungency - 0.27) < 1e-6 or blend_pungency == 0.27

recommendation_msg = ""
exp_oil_used_in_blend = exp_oil
exp_oil_sold_separately = 0
market_oil_needed = 0
market_oil_profit = 0
exp_oil_loss = 0

if blend_pungency < 0.27 and total_oil > 0:
    if kg_pungency == exp_pungency:
        max_exp_oil_blend = 0
    else:
        max_exp_oil_blend = max(0, ((kg_oil * (kg_pungency - 0.27)) / (0.27 - exp_pungency)))
        max_exp_oil_blend = min(exp_oil, max_exp_oil_blend)
    exp_oil_used_in_blend = max_exp_oil_blend
    exp_oil_sold_separately = exp_oil - exp_oil_used_in_blend
    exp_oil_loss = exp_oil_sold_separately * (oil_sell_price - exp_oil_sell_price)
    recommendation_msg = (
        f"⚠️ **Blend pungency is below 0.27.**\n\n"
        f"To achieve compliance, reduce expeller oil in blend to **{exp_oil_used_in_blend:.2f} MT**. "
        f"Excess expeller oil (**{exp_oil_sold_separately:.2f} MT**) will be sold separately, resulting in a loss of "
        f"{format_inr(exp_oil_loss)} per day."
    )
elif blend_pungency > 0.27 and total_oil > 0:
    numerator = (kg_oil * kg_pungency) + (exp_oil * exp_pungency)
    denominator = 0.27
    if denominator > 0:
        market_oil_needed = max(0, (numerator / denominator) - (kg_oil + exp_oil))
    else:
        market_oil_needed = 0
    market_oil_profit = (oil_sell_price - market_oil_price) * market_oil_needed
    recommendation_msg = (
        f"ℹ️ **Blend pungency is above 0.27.**\n\n"
        f"To optimize cost, you may add **{market_oil_needed:.2f} MT** of market oil (0% pungency) to bring the blend to 0.27. "
        f"This could add a profit of {format_inr(market_oil_profit)} per day. "
        f"(This is a recommendation; you may choose to act or ignore.)"
    )
else:
    recommendation_msg = "✅ **Blend pungency is at the required 0.27. No adjustment needed.**"

st.info(recommendation_msg)

# --- Revenue Calculations ---
oil_blend = kg_oil + exp_oil_used_in_blend + market_oil
oil_blend_revenue = oil_blend * oil_sell_price
exp_oil_revenue = exp_oil_sold_separately * exp_oil_sell_price

# MoC Enhancement
base_moc = seed_input * (moc_base_yield_pct / 100)
water_moc = seed_input * (water_pct / 100)
salt_moc = seed_input * (salt_pct / 100)
enhanced_moc = base_moc + water_moc + salt_moc
moc_enhance_cost = (water_moc * water_cost) + (salt_moc * salt_cost)
moc_revenue = enhanced_moc * moc_sell_price

# --- Section: Costing & Margins ---
processing_cost = st.number_input("Processing Cost (₹/MT)", min_value=0.0, value=1300.0, format="%.2f")
other_variable_costs = st.number_input("Other Variable Costs (₹/MT)", min_value=0.0, value=2300.0, format="%.2f")

# COGS Calculation
cogs_ops = (seed_input * seed_price) + (market_oil * market_oil_price) + (seed_input * processing_cost) + (seed_input * other_variable_costs)
cogs_moc_enhance = moc_enhance_cost
cogs_total = cogs_ops + cogs_moc_enhance

expenses = seed_input * (processing_cost + other_variable_costs)

total_revenue = oil_blend_revenue + exp_oil_revenue + moc_revenue
gross_margin = total_revenue - cogs_total
gm_percent = (gross_margin / total_revenue) * 100 if total_revenue else 0
contribution_margin = gross_margin  # Placeholder for now
cm_percent = gm_percent

# --- Monthly & Annual Projections ---
prod_days = st.number_input("Production Days per Month", min_value=1, value=24)
capex = st.number_input("Capex (₹)", min_value=0.0, value=170000000.0, format="%.2f")
depreciation = capex / 96
st.markdown(f"**Depreciation (₹/month):** {depreciation:,.0f}")
tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=25.0, format="%.2f")
other_assets = st.number_input("Other Assets (₹)", min_value=0.0, value=0.0, format="%.2f")

monthly_revenue = total_revenue * prod_days
monthly_cogs = cogs_total * prod_days
monthly_expenses = expenses * prod_days
monthly_gross_margin = gross_margin * prod_days
monthly_ebitda = monthly_gross_margin - depreciation
monthly_ebit = monthly_ebitda
monthly_pbt = monthly_ebit
monthly_tax = monthly_pbt * (tax_rate / 100)
monthly_pat = monthly_pbt - monthly_tax

annual_revenue = monthly_revenue * 12
annual_cogs = monthly_cogs * 12
annual_expenses = monthly_expenses * 12
annual_gross_margin = monthly_gross_margin * 12
annual_ebitda = monthly_ebitda * 12
annual_ebit = monthly_ebit * 12
annual_pbt = monthly_pbt * 12
annual_pat = monthly_pat * 12

gm_percent_annual = (annual_gross_margin / annual_revenue) * 100 if annual_revenue else 0
cogs_percent = (cogs_total / total_revenue) * 100 if total_revenue else 0
expenses_percent = (expenses / total_revenue) * 100 if total_revenue else 0
gm_percent_daily = gm_percent
cogs_percent_annual = (annual_cogs / annual_revenue) * 100 if annual_revenue else 0
expenses_percent_annual = (annual_expenses / annual_revenue) * 100 if annual_revenue else 0

ebitda_percent = (monthly_ebitda / monthly_revenue * 100) if monthly_revenue else 0
pbt_percent = (monthly_pbt / monthly_revenue * 100) if monthly_revenue else 0
pat_percent = (monthly_pat / monthly_revenue * 100) if monthly_revenue else 0

ebitda_percent_annual = (annual_ebitda / annual_revenue * 100) if annual_revenue else 0
pbt_percent_annual = (annual_pbt / annual_revenue * 100) if annual_revenue else 0
pat_percent_annual = (annual_pat / annual_revenue * 100) if annual_revenue else 0

# --- Working Capital & Warehouse Financing ---
st.header("Working Capital & Warehouse Financing")

col15, col16, col17 = st.columns(3)
with col15:
    hoard_months = st.number_input("Raw Material Hoard (months)", min_value=0.0, value=6.0)
    financed_pct = st.number_input("% Financed (RM Hoard)", min_value=0.0, max_value=100.0, value=80.0)
    warehouse_int_rate = st.number_input("Warehouse Finance Interest Rate (% p.a.)", min_value=0.0, max_value=100.0, value=12.0)
    rm_safety_stock_days = st.number_input("RM Safety Stock (days)", min_value=0, value=24)
    creditors_days = st.number_input("Creditors Days", min_value=0, value=15)

with col16:
    fg_oil_ss_days = st.number_input("FG (Oil) Safety Stock (days)", min_value=0, value=15)
    fg_moc_ss_days = st.number_input("FG (MoC) Safety Stock (days)", min_value=0, value=5)

with col17:
    debtor_oil_days = st.number_input("Oil Debtor Cycle (days)", min_value=0, value=5)
    debtor_moc_days = st.number_input("MoC Debtor Cycle (days)", min_value=0, value=5)

# Working Capital Calculations

daily_seed_consumption = seed_input
monthly_seed_consumption = daily_seed_consumption * prod_days

# RM Inventory
rm_hoarded_qty = monthly_seed_consumption * hoard_months
rm_hoarded_val = rm_hoarded_qty * hoarded_rm_rate
rm_safety_stock_qty = daily_seed_consumption * rm_safety_stock_days
rm_safety_stock_val = rm_safety_stock_qty * seed_price

# FG Inventory
daily_oil_output = oil_blend
daily_moc_output = enhanced_moc
fg_oil_inventory = daily_oil_output * fg_oil_ss_days * oil_sell_price
fg_moc_inventory = daily_moc_output * fg_moc_ss_days * moc_sell_price

# Debtors
oil_debtors = daily_oil_output * oil_sell_price * debtor_oil_days
moc_debtors = daily_moc_output * moc_sell_price * debtor_moc_days
total_debtors = oil_debtors + moc_debtors

# Creditors
creditors = daily_seed_consumption * creditors_days * seed_price

# Inventory
total_inventory = rm_hoarded_val + rm_safety_stock_val + fg_oil_inventory + fg_moc_inventory

# Total Working Capital
total_wc = total_inventory + total_debtors - creditors

# Interest Cost (unchanged)
rm_financed = rm_hoarded_qty * (financed_pct / 100)
interest_cost = (rm_financed * hoarded_rm_rate) * (warehouse_int_rate / 100) * (hoard_months / 12)

# --- ROCE Calculation ---
roce_numerator = annual_ebit
roce_denominator = capex + total_wc + other_assets
roce_percent = (roce_numerator / roce_denominator) * 100 if roce_denominator else 0

# --- OUTPUT SECTION ---

st.header("Key Financials (All values in ₹ Cr unless otherwise specified)")

col1, col2 = st.columns([2,1])

with col1:
    st.markdown("### Daily, Monthly, Annual Margin Calculation")

    st.write(f"**Daily Revenue:** {format_cr(total_revenue)}")
    st.write(f"**Monthly Revenue:** {format_cr(total_revenue * prod_days)}")
    st.write(f"**Annual Revenue:** {format_cr(total_revenue * prod_days * 12)}")
    st.write("---")

    st.write(f"**COGS (Daily):** {format_cr(cogs_total)} ({(cogs_total/total_revenue*100) if total_revenue else 0:.2f}%)")
    st.write(f"**COGS (Monthly):** {format_cr(cogs_total * prod_days)} ({(cogs_total * prod_days / (total_revenue * prod_days) * 100) if total_revenue else 0:.2f}%)")
    st.write(f"**COGS (Annual):** {format_cr(cogs_total * prod_days * 12)} ({(cogs_total * prod_days * 12 / (total_revenue * prod_days * 12) * 100) if total_revenue else 0:.2f}%)")
    st.write(f"**Expenses (Daily):** {format_cr(expenses)} ({(expenses/total_revenue*100) if total_revenue else 0:.2f}%)")
    st.write(f"**Expenses (Monthly):** {format_cr(expenses * prod_days)} ({(expenses * prod_days / (total_revenue * prod_days) * 100) if total_revenue else 0:.2f}%)")
    st.write(f"**Expenses (Annual):** {format_cr(expenses * prod_days * 12)} ({(expenses * prod_days * 12 / (total_revenue * prod_days * 12) * 100) if total_revenue else 0:.2f}%)")
    st.write("---")

    # GM
    st.write(f"**Gross Margin (GM) (Daily):** {format_cr(gross_margin)}  ({gm_percent:.2f}%)")
    st.write(f"**Gross Margin (GM) (Monthly):** {format_cr(gross_margin * prod_days)}  ({gm_percent:.2f}%)")
    st.write(f"**Gross Margin (GM) (Annual):** {format_cr(gross_margin * prod_days * 12)}  ({gm_percent:.2f}%)")
    # CM
    st.write(f"**Contribution Margin (CM) (Daily):** {format_cr(contribution_margin)}  ({cm_percent:.2f}%)")
    st.write(f"**Contribution Margin (CM) (Monthly):** {format_cr(contribution_margin * prod_days)}  ({cm_percent:.2f}%)")
    st.write(f"**Contribution Margin (CM) (Annual):** {format_cr(contribution_margin * prod_days * 12)}  ({cm_percent:.2f}%)")
    # EBITDA
    st.write(f"**EBITDA (Daily):** {format_cr(gross_margin - depreciation / prod_days)}  ({((gross_margin - depreciation / prod_days) / total_revenue * 100) if total_revenue else 0:.2f}%)")
    st.write(f"**EBITDA (Monthly):** {format_cr(monthly_ebitda)}  ({ebitda_percent:.2f}%)")
    st.write(f"**EBITDA (Annual):** {format_cr(annual_ebitda)}  ({ebitda_percent_annual:.2f}%)")

with col2:
    st.markdown("### Revenue Breakdown")
    st.write(f"**Kachi Ghani Oil Output (MT):** {kg_oil:.2f}")
    st.write(f"**Expeller Oil Output (MT):** {exp_oil:.2f}")
    st.write(f"**Oil Blend Revenue:** {format_cr(oil_blend_revenue)}")
    st.write(f"**Expeller Oil Revenue:** {format_cr(exp_oil_revenue)}")
    st.write(f"**MoC Output (MT):** {enhanced_moc:.2f}")
    st.write(f"**MoC Revenue:** {format_cr(moc_revenue)}")
    st.write("---")
    st.write(f"**Total Revenue:** {format_cr(total_revenue)}")
    st.write("---")
    st.markdown(f"<span style='font-size:12px;'>MoC Cost from Ops: {format_cr(cogs_ops)}<br>Enhancement Cost: {format_cr(cogs_moc_enhance)}</span>", unsafe_allow_html=True)

st.markdown("---")

st.header("Working Capital Breakup")

colA, colB, colC, colD = st.columns(4)
with colA:
    st.metric("Debtors (₹ Cr)", format_cr(total_debtors))
with colB:
    st.metric("Creditors (₹ Cr)", format_cr(creditors))
with colC:
    st.metric("Inventory (₹ Cr)", format_cr(total_inventory))
with colD:
    st.metric("Total Working Capital (₹ Cr)", format_cr(total_wc))

st.markdown("---")

st.header("ROCE Calculation")
st.markdown(f"""
- **EBIT (Annual):** {format_cr(roce_numerator)}
- **Capex:** {format_cr(capex)}
- **Working Capital:** {format_cr(total_wc)}
- **Other Assets:** {format_cr(other_assets)}
- **ROCE (%):** **{roce_percent:.2f}%**
""")

st.info("All calculations update in real time as you change inputs. All numbers are shown in ₹ Cr for clarity.")

