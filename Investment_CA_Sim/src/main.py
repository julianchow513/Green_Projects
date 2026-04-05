import numpy as np
from scipy.optimize import minimize
from withdrawals import run_simulation_wrapper
from deposit import run_savings_wrapper_yearly
import nevergrad as ng
from tax_calc import calculate_tax_numba

# --- Helper Functions ---

def run_accumulation(allocation, starting_balances, annual_growth, current_age, target_retirement_age):
    """
    Run yearly accumulation of savings accounts.
    """
    return run_savings_wrapper_yearly(
        starting_balances,
        allocation,
        target_retirement_age,
        annual_growth,
        current_age
    )

def run_retirement(accounts_post_savings, annual_growth, inflation, target_retirement_age, predicted_death_age, target_net_annual):
    """
    Simulate withdrawals during retirement.
    Returns success flag and ending balance.
    """
    return run_simulation_wrapper(
        accounts_post_savings,
        target_retirement_age,
        predicted_death_age,
        annual_growth,
        inflation,
        target_net_annual
    )


def compute_savings_after_rrsp(rrsp, gross_salary, post_tax_budget, calculate_tax):
    """
    Compute net savings available for other accounts after RRSP and post-tax spending.
    """
    taxable_salary = gross_salary - rrsp
    net_salary = taxable_salary - calculate_tax(taxable_salary)
    savings = net_salary - post_tax_budget
    return savings


def sequential_allocation_valid(x, gross_salary, post_tax_budget, tfsa_max, espp_max, calculate_tax):
    rrsp, tfsa, espp, taxable = x

    # Step 1: after RRSP contribution
    remaining_savings = compute_savings_after_rrsp(rrsp, gross_salary, post_tax_budget, calculate_tax)
    if remaining_savings < 0:
        return -1.0

    # Step 2: TFSA
    if tfsa > min(tfsa_max, remaining_savings):
        return -1.0
    remaining_savings -= tfsa

    # Step 3: ESPP
    if espp > min(espp_max, remaining_savings):
        return -1.0
    remaining_savings -= espp

    # Step 4: Taxable
    if taxable > remaining_savings:
        return -1.0

    return 1.0


def objective_allocation(x, starting_balances, annual_growth, current_age,
                         target_retirement_age, predicted_death_age, inflation,
                         annual_salary):
    """
    Objective function: negative of final retirement balance (maximize balance).
    """
    candidate_allocation = {
        "rrsp": x[0],
        "tfsa": x[1],
        "espp": x[2],
        "taxable": x[3]
    }

    # Step 1: accumulate savings
    accounts_post_savings = run_savings_wrapper_yearly(
        starting_balances,
        candidate_allocation,
        target_retirement_age,
        annual_growth,
        current_age
    )

    # Step 2: simulate retirement
    success, final_balance = run_simulation_wrapper(
        accounts_post_savings,
        target_retirement_age,
        predicted_death_age,
        annual_growth,
        inflation,
        target_net_annual=annual_salary
    )

    # Penalize failure
    if not success:
        return 1e6

    return -final_balance


# --- Optimizer Wrapper ---

def optimize_allocation_modular(starting_balances, annual_salary, post_tax_budget,
                                current_allocation, annual_growth, current_age,
                                target_retirement_age, predicted_death_age, inflation,
                                calculate_tax):
    """
    Optimizes allocations with sequential RRSP -> other accounts logic.
    """

    # Absolute maxima
    rrsp_min, rrsp_max = 2000, 15300
    tfsa_max = 7000
    espp_max = 0.15 * annual_salary

    budget_vars = ["rrsp", "tfsa", "espp", "taxable"]

    # Nevergrad parameter space with bounds
    bounds = [(rrsp_min, rrsp_max), (0, tfsa_max), (0, espp_max), (0, annual_salary)]
    low = [b[0] for b in bounds]
    high = [b[1] for b in bounds]

    init = [(l + h)/2 for l, h in zip(low, high)]
    parametrization = ng.p.Array(init=init, lower=low, upper=high)

    # Sequential constraint
    parametrization.register_cheap_constraint(
        lambda x: sequential_allocation_valid(
            x, annual_salary, post_tax_budget, tfsa_max, espp_max, calculate_tax
        )
    )

    # Optimizer
    optimizer = ng.optimizers.OnePlusOne(parametrization=parametrization, budget=500)

    # Minimize objective
    recommendation = optimizer.minimize(
        lambda x: objective_allocation(
            x, starting_balances, annual_growth, current_age,
            target_retirement_age, predicted_death_age, inflation, annual_salary
        )
    )

    optimized_allocation = {budget_vars[i]: recommendation.value[i] for i in range(len(bounds))}
    optimized_balance = -recommendation.loss

    return optimized_allocation, optimized_balance


MKT_GROWTH = 0.1435
MKT_YIELD  = 0.0113
LYFT_1YR   = 0.1620
USD_CAD_FX = 1.3948


if __name__ == "__main__":
    # --- INPUT VARIABLES ---
    annual_salary = 170_000
    post_tax_budget = 52_800  # yearly spending outside accounts
    current_age = 25
    target_retirement_age = 55
    predicted_death_age = 90
    annual_growth = 0.07
    inflation = 0.03

    # Starting balances
    starting_balances = {
        "tfsa": {"balance": 40_000},
        "rrsp": {"balance": 16_000},
        "taxable": {"balance": 36_000, "acb": 36_000},
        "espp": {"balance": 5441, "acb": 5441}
    }

    # Current allocations (initial guess)
    current_allocation = {
        "rrsp": 10_000,
        "tfsa": 7_000,
        "taxable": 5_000,
        "espp": 5441
    }

    # --- RUN OPTIMIZER ---
    optimized_allocation, optimized_balance = optimize_allocation_modular(
        starting_balances,
        annual_salary,
        post_tax_budget,
        current_allocation,
        annual_growth,
        current_age,
        target_retirement_age,
        predicted_death_age,
        inflation,
        calculate_tax_numba
    )

    # --- OUTPUT RESULTS ---
    print("Optimized Allocation:")
    for account, amount in optimized_allocation.items():
        print(f"{account}: {amount:,.2f}")
    print(f"Expected Ending Balance: {optimized_balance:,.2f}")

