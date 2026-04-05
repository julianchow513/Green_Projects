def calculate_espp_utility_refined(contribution_cad, start_price, end_price, marginal_rate, years, annual_growth):
    """
    Calculates Net Wealth from ESPP after Income Tax (Year 0) and Capital Gains Tax (Year N).
    """
    # --- 1. PURCHASE LOGIC (Year 0) ---
    # Purchase price is 15% off the lower of start/end (Lookback)
    base_price = min(start_price, end_price)
    purchase_price = base_price * 0.85
    
    # Shares purchased with your CAD contribution
    shares = contribution_cad / purchase_price
    
    # Market Value at the moment of purchase
    market_value_at_purchase = shares * end_price
    
    # Taxable Employment Benefit (The 15% discount)
    # This is taxed as regular income in Ontario immediately
    employment_benefit = market_value_at_purchase - contribution_cad
    income_tax_owed = employment_benefit * marginal_rate
    
    # Your Adjusted Cost Base (ACB) for CRA purposes is the Market Value at Purchase
    acb = market_value_at_purchase

    # --- 2. GROWTH & EXIT LOGIC (Year N) ---
    # The value grows over the time horizon
    final_value_pre_tax = market_value_at_purchase * ((1 + annual_growth) ** years)
    
    # Total Capital Gain realized at Year N
    capital_gain = final_value_pre_tax - acb
    
    # Capital Gains Tax calculation (50% inclusion rate in Canada)
    # We assume marginal_rate remains the same at exit for this model
    capital_gains_tax = (capital_gain * 0.50) * marginal_rate
    
    # --- 3. FINAL NET WEALTH ---
    # Total Value - Exit Tax - The initial income tax you paid on the discount
    net_wealth = final_value_pre_tax - capital_gains_tax - income_tax_owed
    
    return net_wealth


def calculate_tfsa_utility(contribution_cad, years, annual_growth):
    """
    Calculates Net Wealth for a TFSA contribution.
    Note: Since contributions are after-tax, the 'cost' to the user 
    is the full contribution_cad.
    """
    # 1. Compounded Growth (No annual tax drag)
    final_value = contribution_cad * ((1 + annual_growth) ** years)
    
    # 2. Exit Logic
    # In Canada, withdrawals are 100% tax-free. 
    # There is no capital gains tax and no income tax.
    net_wealth = final_value
    
    return net_wealth

def calculate_nrsp_utility(contribution_cad, years, annual_growth, dividend_yield, marginal_rate):
    """
    Calculates Net Wealth for a Taxable NRSP account.
    Accounts for Annual Dividend Tax (Drag) and Terminal Capital Gains Tax.
    """
    # 1. Calculate Annual Tax Drag
    # Dividends are taxed every year. For US stocks (like LYFT or SPY), 
    # these are 'Non-Eligible' and taxed at your full marginal rate.
    annual_tax_on_dividends = dividend_yield * marginal_rate
    
    # The 'Effective' growth rate is the market growth minus the tax leak
    # We also subtract a small 0.3% for internal fund turnover/rebalancing taxes
    effective_annual_growth = annual_growth - annual_tax_on_dividends - 0.003
    
    # 2. Compounded Growth over Time Horizon
    final_value_pre_exit_tax = contribution_cad * ((1 + effective_annual_growth) ** years)
    
    # 3. Capital Gains Tax at Year N
    # Your Adjusted Cost Base (ACB) is simply what you put in.
    total_capital_gain = final_value_pre_exit_tax - contribution_cad
    
    # Inclusion rate is 50% for the first $250k of gains in a year (2026 rules)
    capital_gains_tax = (total_capital_gain * 0.50) * marginal_rate
    
    # 4. Net Wealth
    net_wealth = final_value_pre_exit_tax - capital_gains_tax
    
    return net_wealth

def calculate_rrsp_utility(contribution_cad, years, annual_growth, current_marginal_rate, retirement_marginal_rate):
    """
    Calculates Net Wealth for an RRSP contribution.
    - current_marginal_rate: Your tax bracket today (e.g., 45-53% at Lyft).
    - retirement_marginal_rate: Your expected tax bracket at withdrawal.
    """
    # 1. THE TAX SHIELD (The 'Refund')
    # Since RRSP is pre-tax, a $10,000 contribution triggers an immediate 
    # cash refund based on your highest tax bracket.
    tax_refund = contribution_cad * current_marginal_rate
    
    # 2. TOTAL INVESTED CAPITAL
    # To compare fairly with after-tax accounts (TFSA/ESPP), we assume 
    # the refund is also invested and grows at the same rate.
    total_invested = contribution_cad + tax_refund
    
    # 3. COMPOUNDED GROWTH (No annual tax drag)
    # Like the TFSA, the RRSP grows tax-free internally.
    final_pot_pre_tax = total_invested * ((1 + annual_growth) ** years)
    
    # 4. EXIT LOGIC (The 'Deferred' Tax)
    # Unlike Capital Gains (50% inclusion), RRSP withdrawals are taxed 
    # as 100% regular income at your future retirement rate.
    exit_tax = final_pot_pre_tax * retirement_marginal_rate
    
    # 5. NET WEALTH
    net_wealth = final_pot_pre_tax - exit_tax
    
    return net_wealth