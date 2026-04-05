import pytest
from Investment_CA_Sim.src.deposit import run_savings_wrapper_yearly

@pytest.fixture
def base_accounts():
    """Provide a baseline accounts dictionary for testing."""
    return {
        "tfsa": {"balance": 50_000.0},
        "rrsp": {"balance": 50_000.0},
        "taxable": {"balance": 50_000.0, "acb": 25_000.0},
        "espp": {"balance": 0.0, "acb": 0.0},
    }

@pytest.fixture
def base_allocation():
    """Provide a baseline allocation dictionary for testing."""
    return {
        "tfsa": 10_000.0,
        "rrsp": 5_000.0,
        "taxable": 15_000.0,
        "espp": 20_000.0,
    }

def test_zero_growth(base_accounts, base_allocation):
    """Balances should only grow by contributions if annual growth is 0."""
    result = run_savings_wrapper_yearly(base_accounts, base_allocation, target_retirement_age=66, annual_growth=0.0, current_age=65)
    
    # Only one year of contributions
    assert result["tfsa"]["balance"] == base_accounts["tfsa"]["balance"] + base_allocation["tfsa"]
    assert result["rrsp"]["balance"] == base_accounts["rrsp"]["balance"] + base_allocation["rrsp"]
    assert result["taxable"]["balance"] == base_accounts["taxable"]["balance"] + base_allocation["taxable"]
    assert result["taxable"]["acb"] == base_accounts["taxable"]["acb"] + base_allocation["taxable"]
    assert result["espp"]["balance"] == base_accounts["espp"]["balance"] + base_allocation["espp"]
    assert result["espp"]["acb"] == base_accounts["espp"]["acb"] + base_allocation["espp"] * 0.85  # accounting for discount

def test_multiple_years_growth(base_accounts, base_allocation):
    """Balances should compound with multiple years of growth."""
    years = 3
    current_age = 30
    target_age = current_age + years
    annual_growth = 0.10  # 10%
    
    result = run_savings_wrapper_yearly(base_accounts, base_allocation, target_retirement_age=target_age, annual_growth=annual_growth, current_age=current_age)
    
    # Check that balances are greater than initial + contributions due to growth
    assert result["tfsa"]["balance"] > base_accounts["tfsa"]["balance"] + base_allocation["tfsa"] * years
    assert result["rrsp"]["balance"] > base_accounts["rrsp"]["balance"] + base_allocation["rrsp"] * years
    assert result["taxable"]["balance"] > base_accounts["taxable"]["balance"] + base_allocation["taxable"] * years
    assert result["taxable"]["acb"] == base_accounts["taxable"]["acb"] + base_allocation["taxable"] * years
    assert result["espp"]["balance"] > base_accounts["espp"]["balance"] + base_allocation["espp"] * years
    assert result["espp"]["acb"] == base_accounts["espp"]["acb"] + base_allocation["espp"] * 0.85 * years

def test_no_allocation(base_accounts):
    """If no contributions are made, only growth affects balances."""
    allocation = {}
    years = 2
    growth = 0.05  # 5%
    current_age = 40
    target_age = current_age + years
    
    result = run_savings_wrapper_yearly(base_accounts, allocation, target_retirement_age=target_age, annual_growth=growth, current_age=current_age)
    
    # Balances should grow only by the factor of (1 + growth) ** years
    assert result["tfsa"]["balance"] == pytest.approx(base_accounts["tfsa"]["balance"] * (1 + growth) ** years)
    assert result["rrsp"]["balance"] == pytest.approx(base_accounts["rrsp"]["balance"] * (1 + growth) ** years)
    assert result["taxable"]["balance"] == pytest.approx(base_accounts["taxable"]["balance"] * (1 + growth) ** years)
    assert result["taxable"]["acb"] == base_accounts["taxable"]["acb"]  # no new contributions
    assert result["espp"]["balance"] == pytest.approx(base_accounts["espp"]["balance"] * (1 + growth) ** years)
    assert result["espp"]["acb"] == base_accounts["espp"]["acb"]

def test_espp_discount(base_accounts):
    """Ensure ESPP discount is correctly applied to ACB."""
    allocation = {"espp": 10_000.0}
    result = run_savings_wrapper_yearly(base_accounts, allocation, target_retirement_age=31, annual_growth=0.0, current_age=30)
    
    assert result["espp"]["acb"] == allocation["espp"] * 0.85
    assert result["espp"]["balance"] == allocation["espp"]
