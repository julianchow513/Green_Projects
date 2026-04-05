from numba import njit
from tax_calc import calculate_tax_numba

@njit
def run_retirement_simulation_numba(
    tfsa, rrsp, taxable, taxable_acb,
    months,
    monthly_growth,
    monthly_net,
    inflation,
):
    current_year_income = 0.0

    for month in range(months):

        if month % 12 == 0:
            current_year_income = 0.0

        year = month // 12
        net_needed = monthly_net * ((1 + inflation) ** year)
        remaining_net = net_needed

        total_balance = tfsa + rrsp + taxable

        months_left = months - month
        if total_balance < net_needed * min(3, months_left):
            return False, 0.0

        # --- TAXABLE ---
        if remaining_net > 0 and taxable > 0:
            acb_ratio = taxable_acb / taxable if taxable > 0 else 0.0

            low = remaining_net
            high = remaining_net * 2

            for _ in range(8):
                mid = (low + high) / 2

                gain = mid * (1 - acb_ratio)
                taxable_gain = gain * 0.5

                tax = calculate_tax_numba(current_year_income + taxable_gain) - calculate_tax_numba(current_year_income)
                net = mid - tax

                if net >= remaining_net:
                    high = mid
                else:
                    low = mid

            gross = high if high < taxable else taxable

            gain = gross * (1 - acb_ratio)
            taxable_gain = gain * 0.5

            tax = calculate_tax_numba(current_year_income + taxable_gain) - calculate_tax_numba(current_year_income)
            net = gross - tax

            prev_balance = taxable
            taxable -= gross
            taxable_acb -= taxable_acb * (gross / prev_balance)

            current_year_income += taxable_gain
            remaining_net -= net

        # --- RRSP ---
        if remaining_net > 0 and rrsp > 0:
            low = remaining_net
            high = remaining_net * 2

            for _ in range(8):
                mid = (low + high) / 2

                tax = calculate_tax_numba(current_year_income + mid) - calculate_tax_numba(current_year_income)
                net = mid - tax

                if net >= remaining_net:
                    high = mid
                else:
                    low = mid

            gross = high if high < rrsp else rrsp

            tax = calculate_tax_numba(current_year_income + gross) - calculate_tax_numba(current_year_income)
            net = gross - tax

            rrsp -= gross
            current_year_income += gross
            remaining_net -= net

        # --- TFSA ---
        if remaining_net > 0 and tfsa > 0:
            withdraw = remaining_net if remaining_net < tfsa else tfsa
            tfsa -= withdraw
            remaining_net -= withdraw

        if remaining_net > 0:
            return False, 0.0

        growth = 1 + monthly_growth
        tfsa *= growth
        rrsp *= growth
        taxable *= growth

    return True, tfsa + rrsp + taxable

def run_simulation_wrapper(accounts, target_retirement_age, predicted_death_age, annual_growth, inflation, target_net_annual):
    months = int((predicted_death_age - target_retirement_age) * 12)
    monthly_growth = (1 + annual_growth) ** (1/12) - 1
    monthly_net = target_net_annual / 12

    taxable = accounts["taxable"]["balance"] + accounts["espp"]["balance"]
    taxable_acb = accounts["taxable"]["acb"] + accounts["espp"]["acb"]

    return run_retirement_simulation_numba(
        accounts["tfsa"]["balance"],
        accounts["rrsp"]["balance"],
        taxable,
        taxable_acb,
        months,
        monthly_growth,
        monthly_net,
        inflation
    )