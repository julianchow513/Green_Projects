from numba import njit

@njit
def run_savings_simulation_yearly_primitive(
    tfsa_balance,
    rrsp_balance,
    taxable_balance,
    taxable_acb,
    espp_balance,
    espp_acb,
    tfsa_contrib,
    rrsp_contrib,
    taxable_contrib,
    espp_contrib,
    years,
    annual_growth
):
    discount = 0.15  # ESPP discount

    for _ in range(years):
        # --- ACCOUNT CONTRIBUTIONS ---
        tfsa_balance += tfsa_contrib
        rrsp_balance += rrsp_contrib

        taxable_balance += taxable_contrib
        taxable_acb += taxable_contrib

        espp_balance += espp_contrib
        espp_acb += espp_contrib * (1 - discount)

        # --- ANNUAL GROWTH ---
        growth = 1 + annual_growth
        tfsa_balance *= growth
        rrsp_balance *= growth
        taxable_balance *= growth
        espp_balance *= growth

    return tfsa_balance, rrsp_balance, taxable_balance, taxable_acb, espp_balance, espp_acb


def run_savings_wrapper_yearly(accounts, allocation, target_retirement_age, annual_growth, current_age):
    years = target_retirement_age - current_age

    # unwrap balances
    tfsa = accounts["tfsa"]["balance"]
    rrsp = accounts["rrsp"]["balance"]
    taxable = accounts["taxable"]["balance"]
    taxable_acb = accounts["taxable"]["acb"]
    espp = accounts["espp"]["balance"]
    espp_acb = accounts["espp"]["acb"]

    # unwrap contributions
    tfsa_contrib = allocation.get("tfsa", 0.0)
    rrsp_contrib = allocation.get("rrsp", 0.0)
    taxable_contrib = allocation.get("taxable", 0.0)
    espp_contrib = allocation.get("espp", 0.0)

    # run simulation
    tfsa, rrsp, taxable, taxable_acb, espp, espp_acb = run_savings_simulation_yearly_primitive(
        tfsa, rrsp, taxable, taxable_acb, espp, espp_acb,
        tfsa_contrib, rrsp_contrib, taxable_contrib, espp_contrib,
        years, annual_growth
    )

    # wrap results back into dict
    return {
        "tfsa": {"balance": tfsa},
        "rrsp": {"balance": rrsp},
        "taxable": {"balance": taxable, "acb": taxable_acb},
        "espp": {"balance": espp, "acb": espp_acb},
    }