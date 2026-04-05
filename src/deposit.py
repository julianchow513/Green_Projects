from numba import njit

@njit
def run_savings_simulation_yearly(
    accounts,
    allocation,       # dict with annual contributions per account in dollars
    years,
    annual_growth
):
    # Copy initial balances/ACBs
    tfsa = accounts["tfsa"]["balance"]
    rrsp = accounts["rrsp"]["balance"]
    taxable = accounts["taxable"]["balance"]
    taxable_acb = accounts["taxable"]["acb"]
    espp = accounts["espp"]["balance"]
    espp_acb = accounts["espp"]["acb"]


    for _ in range(years):

        # --- ACCOUNT CONTRIBUTIONS ---
        tfsa += allocation.get("tfsa", 0.0)
        rrsp += allocation.get("rrsp", 0.0)

        taxable_contrib = allocation.get("taxable", 0.0)
        taxable += taxable_contrib
        taxable_acb += taxable_contrib

        espp_cash = allocation.get("espp", 0.0)
        discount = 0.15
        espp_acb += espp_cash * (1 - discount)
        espp += espp_cash

        # --- ANNUAL GROWTH ---
        growth = 1 + annual_growth
        tfsa *= growth
        rrsp *= growth
        taxable *= growth
        espp *= growth

    # Return balances and ACBs
    return {
        "tfsa": {"balance": tfsa},
        "rrsp": {"balance": rrsp},
        "taxable": {"balance": taxable, "acb": taxable_acb},
        "espp": {"balance": espp, "acb": espp_acb},
    }


def run_savings_wrapper_yearly(accounts, allocation, target_retirement_age, annual_growth, current_age):
    years = target_retirement_age - current_age
    return run_savings_simulation_yearly(
        accounts,
        allocation,
        years,
        annual_growth
    )