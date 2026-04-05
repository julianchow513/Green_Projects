import pytest
from src.tax_calc import calculate_tax_numba, marginal_tax_rate_numba

def test_zero_income():
    assert calculate_tax_numba(0) >= 0.0

def test_low_income():
    # Income below first Ontario bracket
    income = 15000
    # Federal tax slice: 15000 - 0 = 15000 * 0.14 - 16452*0.14 = negative, so max(0, fed_tax)=0
    # Ontario tax slice: 15000 - 0 = 15000 * 0.0505 - 12989*0.0505 = 10.055 approx
    # OHP: income <= 20000 => 0
    expected_tax = max(0, (15000*0.14 - 16452*0.14)) + max(0, (15000*0.0505 - 12989*0.0505)) + 0
    assert calculate_tax_numba(income) == expected_tax

def test_middle_income():
    income = 50000
    tax = calculate_tax_numba(income)
    # Check that tax is positive
    assert tax > 0
    # Optional: check approximate range
    assert 7000 < tax < 12000  # approximate sanity check

def test_high_income():
    income = 250000
    tax = calculate_tax_numba(income)
    # Sanity check: tax should be in the expected high range
    assert tax > 60000

def test_ohp_thresholds():
    # Check Ontario Health Premium brackets
    thresholds = [
        (20000, 0),
        (36000, 300),
        (48000, 450),
        (72000, 600),
        (200000, 750),
        (500000, 900)
    ]
    
    for income, expected_ohp in thresholds:
        tax = calculate_tax_numba(income)
        # Extract OHP component by subtracting federal and provincial tax portion
        fed_brackets = (
            (58523.0, 0.14),
            (117045.0, 0.205),
            (181440.0, 0.26),
            (258482.0, 0.29),
            (1e12, 0.33),
        )
        on_brackets = (
            (53891.0, 0.0505),
            (107785.0, 0.0915),
            (150000.0, 0.1116),
            (220000.0, 0.1216),
            (1e12, 0.1316),
        )

        # Compute fed + on tax to isolate OHP
        fed_tax = 0.0
        prev = 0.0
        for limit, rate in fed_brackets:
            if income > prev:
                taxable_slice = min(income - prev, limit - prev)
                fed_tax += taxable_slice * rate
                prev = limit
        fed_tax -= 16452 * 0.14
        fed_tax = max(0, fed_tax)

        on_tax = 0.0
        prev = 0.0
        for limit, rate in on_brackets:
            if income > prev:
                taxable_slice = min(income - prev, limit - prev)
                on_tax += taxable_slice * rate
                prev = limit
        on_tax -= 12989 * 0.0505
        on_tax = max(0, on_tax)

        ohp = tax - (fed_tax + on_tax)
        assert ohp == expected_ohp


def test_zero_income():
    # At 0 income, rate should be 0
    assert marginal_tax_rate_numba(0) == 0.0

@pytest.mark.parametrize("income,expected_range", [
    (10000, (0.19, 0.20)),      # realistic low-income marginal rate
    (50000, (0.19, 0.21)),
    (60000, (0.29, 0.30)),
    (120000, (0.37, 0.38)),
    (200000, (0.41, 0.42)),
    (300000, (0.46, 0.47)),
])
def test_marginal_rate_ranges(income, expected_range):
    rate = marginal_tax_rate_numba(income)
    # Sanity: rate should be in expected approximate range
    assert expected_range[0] <= rate <= expected_range[1]

def test_bracket_boundaries():
    # Federal first bracket top: 58523
    rate_at_top = marginal_tax_rate_numba(58523)
    rate_just_above = marginal_tax_rate_numba(58524)
    assert rate_at_top < rate_just_above

    # Ontario first bracket top: 53891
    rate_at_top = marginal_tax_rate_numba(53891)
    rate_just_above = marginal_tax_rate_numba(53892)
    assert rate_at_top < rate_just_above

def test_high_income_rate():
    # Very high income should return max federal + Ontario
    rate = marginal_tax_rate_numba(1_000_000)
    # Federal top: 0.33, Ontario top: 0.1316
    expected = 0.33 + 0.1316
    # Numba might give float imprecision
    assert abs(rate - expected) < 1e-6