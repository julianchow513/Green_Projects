from tax_calc import calculate_tax_numba, marginal_tax_rate_numba
from accounts import *


MKT_GROWTH = 0.1435
MKT_YIELD  = 0.0113
LYFT_1YR   = 0.1620
USD_CAD_FX = 1.3948


allocation = {
    "rrsp" : 30000,
    "tfsa" : 7000,
    "taxable" : 1000,
    "espp" : 5000
}



starting_balances = {
    "tfsa": {
        "balance": 10000
    },
    "rrsp": {
        "balance": 5000
    },
    "taxable": {
        "balance": 5000,
        "acb": 5000   # critical for capital gains later
    },
    "espp": {
        "balance": 0,
        "acb": 0
    }
}

annual_salary=120000
annual_rsu=40000
rsu_schedule=[0,1,0,0,1,0,0,1,0,0,1,0]

current_age=25
target_retirement_age=55
predicted_death_age=90

annual_growth=0.06
inflation=0.03


