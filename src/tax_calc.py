from numba import njit

@njit
def calculate_tax_numba(taxable_income):
    fed_brackets = (
        (58523.0, 0.14),
        (117045.0, 0.205),
        (181440.0, 0.26),
        (258482.0, 0.29),
        (1e12, 0.33),
    )

    fed_tax = 0.0
    prev = 0.0

    for limit, rate in fed_brackets:
        if taxable_income > prev:
            taxable_slice = min(taxable_income - prev, limit - prev)
            fed_tax += taxable_slice * rate
            prev = limit

    fed_tax -= 16452 * 0.14

    # --- Ontario ---
    on_brackets = (
        (53891.0, 0.0505),
        (107785.0, 0.0915),
        (150000.0, 0.1116),
        (220000.0, 0.1216),
        (1e12, 0.1316),
    )

    on_tax = 0.0
    prev = 0.0

    for limit, rate in on_brackets:
        if taxable_income > prev:
            taxable_slice = min(taxable_income - prev, limit - prev)
            on_tax += taxable_slice * rate
            prev = limit

    on_tax -= 12989 * 0.0505

    # Ontario health premium
    if taxable_income <= 20000:
        ohp = 0.0
    elif taxable_income <= 36000:
        ohp = 300.0
    elif taxable_income <= 48000:
        ohp = 450.0
    elif taxable_income <= 72000:
        ohp = 600.0
    elif taxable_income <= 200000:
        ohp = 750.0
    else:
        ohp = 900.0

    return max(0.0, fed_tax) + max(0.0, on_tax) + ohp

@njit
def marginal_tax_rate_numba(income):
    if income <= 0:
        return 0.0  # zero income has zero marginal rate
    
    # --- Federal ---
    fed_brackets = (
        (58523.0, 0.14),
        (117045.0, 0.205),
        (181440.0, 0.26),
        (258482.0, 0.29),
        (1e12, 0.33),
    )
    rate = 0.0
    for limit, r in fed_brackets:
        if income <= limit:
            rate = r
            break
    else:
        rate = 0.33
    fed_rate = rate  # do NOT adjust for first bracket credit
    
    # --- Ontario ---
    on_brackets = (
        (53891.0, 0.0505),
        (107785.0, 0.0915),
        (150000.0, 0.1116),
        (220000.0, 0.1216),
        (1e12, 0.1316),
    )
    rate = 0.0
    for limit, r in on_brackets:
        if income <= limit:
            rate = r
            break
    else:
        rate = 0.1316
    on_rate = rate  # do NOT adjust for first bracket credit
    
    return fed_rate + on_rate