import pytest
import numpy as np
from Investment_CA_Sim.src.main import (
    compute_savings_after_rrsp,
    sequential_allocation_valid,
    objective_allocation,
    optimize_allocation_modular
)

# --- Mock functions ---
def mock_tax(x):
    # simple 10% flat tax
    return 0.1 * x

def mock_run_savings_wrapper_yearly(starting_balances, allocation, target_retirement_age, annual_growth, current_age):
    # just increment each account by allocation for testing
    return {k: starting_balances.get(k, 0) + v for k, v in allocation.items()}

def mock_run_simulation_wrapper(accounts_post_savings, target_retirement_age, predicted_death_age,
                                annual_growth, inflation, target_net_annual):
    # Simple success/final_balance mock
    total_balance = sum(accounts_post_savings.values())
    success = total_balance >= target_net_annual  # succeed if enough balance
    return success, total_balance


# --- Tests ---

def test_compute_savings_after_rrsp():
    gross_salary = 100000
    rrsp = 15000
    post_tax_budget = 50000
    net_savings = compute_savings_after_rrsp(rrsp, gross_salary, post_tax_budget, mock_tax)
    expected_taxable = gross_salary - rrsp
    expected_net_salary = expected_taxable - mock_tax(expected_taxable)
    expected_savings = expected_net_salary - post_tax_budget
    assert net_savings == expected_savings

def test_sequential_allocation_valid_feasible():
    x = [10000, 5000, 5000, 1000]
    gross_salary = 100000
    post_tax_budget = 50000
    tfsa_max = 7000
    espp_max = 0.15 * gross_salary
    assert sequential_allocation_valid(x, gross_salary, post_tax_budget, tfsa_max, espp_max, mock_tax) > 0

def test_sequential_allocation_valid_infeasible():
    x = [100000, 5000, 5000, 1000]  # RRSP too high
    gross_salary = 100000
    post_tax_budget = 50000
    tfsa_max = 7000
    espp_max = 0.15 * gross_salary
    assert sequential_allocation_valid(x, gross_salary, post_tax_budget, tfsa_max, espp_max, mock_tax) < 0

def test_objective_allocation_success(monkeypatch):
    # patch the external wrapper functions
    monkeypatch.setattr("Investment_CA_Sim.src.main.run_savings_wrapper_yearly", mock_run_savings_wrapper_yearly)
    monkeypatch.setattr("Investment_CA_Sim.src.main.run_simulation_wrapper", mock_run_simulation_wrapper)

    x = [10000, 5000, 5000, 5000]
    starting_balances = {"rrsp": 0, "tfsa": 0, "espp": 0, "taxable": 0}
    result = objective_allocation(x, starting_balances, annual_growth=0.05,
                                  current_age=30, target_retirement_age=65,
                                  predicted_death_age=90, inflation=0.02,
                                  annual_salary=20000)
    assert isinstance(result, (int, float))
    assert result < 1e6  # should not be penalized

def test_optimize_allocation_modular_basic(monkeypatch):
    # patch the wrappers to deterministic mocks
    monkeypatch.setattr("Investment_CA_Sim.src.main.run_savings_wrapper_yearly", mock_run_savings_wrapper_yearly)
    monkeypatch.setattr("Investment_CA_Sim.src.main.run_simulation_wrapper", mock_run_simulation_wrapper)

    starting_balances = {"rrsp": 0, "tfsa": 0, "espp": 0, "taxable": 0}
    optimized_allocation, optimized_balance = optimize_allocation_modular(
        starting_balances=starting_balances,
        annual_salary=100000,
        post_tax_budget=5000,
        current_allocation={"rrsp": 0, "tfsa": 0, "espp": 0, "taxable": 0},
        annual_growth=0.05,
        current_age=30,
        target_retirement_age=65,
        predicted_death_age=90,
        inflation=0.02,
        calculate_tax=mock_tax
    )
    # Validate allocation keys and that values are numeric
    assert set(optimized_allocation.keys()) == {"rrsp", "tfsa", "espp", "taxable"}
    for val in optimized_allocation.values():
        assert isinstance(val, float)
    assert isinstance(optimized_balance, float)