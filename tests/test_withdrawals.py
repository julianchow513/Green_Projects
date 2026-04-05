import pytest
from src.withdrawals import run_retirement_simulation_numba, run_simulation_wrapper

# Mock account data for testing
accounts_template = {
    "tfsa": {"balance": 500_000.0},
    "rrsp": {"balance": 500_000.0},
    "taxable": {"balance": 200_000.0, "acb": 100_000.0},
    "espp": {"balance": 0.0, "acb": 0.0},
}

def test_simulation_sufficient_funds():
    """Simulation should succeed when funds are plenty"""
    accounts = accounts_template.copy()
    success, final_balance = run_retirement_simulation_numba(
        tfsa=accounts["tfsa"]["balance"],
        rrsp=accounts["rrsp"]["balance"],
        taxable=accounts["taxable"]["balance"],
        taxable_acb=accounts["taxable"]["acb"],
        months=12*30,  # 30 years
        monthly_growth=0.005,  # ~6% annual
        monthly_net=2000.0,
        inflation=0.02
    )
    assert success is True
    assert final_balance > 0.0

def test_simulation_insufficient_funds():
    """Simulation should fail when withdrawals exceed balances"""
    accounts = {
        "tfsa": {"balance": 10_000.0},
        "rrsp": {"balance": 10_000.0},
        "taxable": {"balance": 5_000.0, "acb": 2_500.0},
        "espp": {"balance": 0.0, "acb": 0.0},
    }
    success, final_balance = run_retirement_simulation_numba(
        tfsa=accounts["tfsa"]["balance"],
        rrsp=accounts["rrsp"]["balance"],
        taxable=accounts["taxable"]["balance"],
        taxable_acb=accounts["taxable"]["acb"],
        months=12*30,
        monthly_growth=0.0,
        monthly_net=5000.0,  # too high
        inflation=0.02
    )
    assert success is False
    assert final_balance == 0.0

def test_simulation_zero_months():
    """Simulation with zero months should succeed trivially"""
    accounts = accounts_template.copy()
    success, final_balance = run_retirement_simulation_numba(
        tfsa=accounts["tfsa"]["balance"],
        rrsp=accounts["rrsp"]["balance"],
        taxable=accounts["taxable"]["balance"],
        taxable_acb=accounts["taxable"]["acb"],
        months=0,
        monthly_growth=0.01,
        monthly_net=1000.0,
        inflation=0.02
    )
    assert success is True
    expected_balance = accounts["tfsa"]["balance"] + accounts["rrsp"]["balance"] + accounts["taxable"]["balance"]
    assert final_balance == expected_balance

def test_simulation_zero_growth():
    """Simulation should still succeed if withdrawals are covered, even with zero growth"""
    accounts = {
        "tfsa": {"balance": 500_000.0},
        "rrsp": {"balance": 500_000.0},
        "taxable": {"balance": 200_000.0, "acb": 100_000.0},
        "espp": {"balance": 0.0, "acb": 0.0},
    }
    monthly_net = 3_000.0
    months = 12*10  # 10 years
    success, final_balance = run_retirement_simulation_numba(
        tfsa=accounts["tfsa"]["balance"],
        rrsp=accounts["rrsp"]["balance"],
        taxable=accounts["taxable"]["balance"],
        taxable_acb=accounts["taxable"]["acb"],
        months=months,
        monthly_growth=0.0,
        monthly_net=monthly_net,
        inflation=0.0
    )
    assert success is True
    # Final balance should be total - total withdrawals
    total_start = 500_000 + 500_000 + 200_000
    total_withdraw = monthly_net * months
    assert final_balance <= total_start - total_withdraw + 1e-2

def test_run_simulation_wrapper_integration():
    """Integration test with wrapper"""
    accounts = accounts_template.copy()
    success, final_balance = run_simulation_wrapper(
        accounts,
        target_retirement_age=65,
        predicted_death_age=95,
        annual_growth=0.06,
        inflation=0.02,
        target_net_annual=36_000.0
    )
    assert isinstance(success, bool)
    assert final_balance >= 0.0