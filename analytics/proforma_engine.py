"""
Proforma Engine
===============
Builds monthly operating and equity-level proforma cash flows
based on user-provided acquisition and loan assumptions.

Input:
    dict of assumptions (same structure as JSON input)

Output:
    monthly_cf : DataFrame of monthly operating cash flows
    equity_cf  : DataFrame of equity-level cash flows for IRR, EM, etc.
"""

# --------------------------------------------------------
# Imports
# --------------------------------------------------------
import pandas as pd
import numpy as np
import numpy_financial as npf
from dateutil.relativedelta import relativedelta


# --------------------------------------------------------
# Helper: Safe numeric conversion
# --------------------------------------------------------
def _to_float(val):
    """Safely convert any numeric type to float."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0


# --------------------------------------------------------
# Main Proforma Builder
# --------------------------------------------------------
def build_proforma(a: dict):
    """
    Builds monthly proforma based only on acquisition assumptions.
    """
    print("🧮 [Proforma Engine] Building cash flow model...")

    # Convert to floats
    def f(x): return float(x or 0)

    date_of_close = pd.Timestamp(a.get("date_of_close"))
    hold_years = int(f(a.get("hold_period_years", 10)))
    hold_months = hold_years * 12

    purchase_price = f(a.get("purchase_price"))
    closing_costs = purchase_price * f(a.get("closing_costs", 0.02))
    rent_base = f(a.get("rent_immediately_after_purchase"))
    vacancy = f(a.get("vacancy_immediately_after_purchase", 0.05))
    other_income = f(a.get("other_income_immediately_after_purchase", 0))
    expense_base = f(a.get("operating_expenses_after_purchase"))
    capex_initial = f(a.get("capital_expense_after_purchase"))

    rent_growth = f(a.get("expected_rent_growth", 0.04))
    expense_growth = f(a.get("expected_expense_growth", 0.025))
    capex_growth = f(a.get("expected_capex_growth", 0.02))
    appreciation = f(a.get("expected_appreciation", 0.054))

    exit_cap = f(a.get("exit_cap_rate_expectation", 0.055))
    cost_of_sale = f(a.get("cost_of_sale_percentage", 0.05))

    ltv = f(a.get("ltv", 0.7))
    interest_rate = f(a.get("interest_rate", 0.045))
    amort_years = int(f(a.get("amortization_years", 30)))

    loan_amount = purchase_price * ltv
    monthly_rate = interest_rate / 12
    nper = amort_years * 12

    idx = pd.date_range(date_of_close + relativedelta(months=1), periods=hold_months, freq="M")
    df = pd.DataFrame(index=idx)
    df["MonthNum"] = np.arange(1, len(df) + 1)
    df["YearsFrac"] = (df["MonthNum"] - 1) / 12

    # --- Income & Expenses ---
    df["GrossPotentialRent"] = rent_base * (1 + rent_growth) ** df["YearsFrac"]
    df["VacancyLoss"] = -df["GrossPotentialRent"] * vacancy
    df["OtherIncome"] = other_income * (1 + rent_growth) ** df["YearsFrac"]
    df["NetRentalRevenue"] = df["GrossPotentialRent"] + df["VacancyLoss"] + df["OtherIncome"]

    df["OperatingExpenses"] = -expense_base * (1 + expense_growth) ** df["YearsFrac"]
    df["NetOperatingIncome"] = df["NetRentalRevenue"] + df["OperatingExpenses"]

    df["CapitalExpenses"] = -capex_initial * (1 + capex_growth) ** df["YearsFrac"]
    df["CashFlowBeforeDebtService"] = df["NetOperatingIncome"] + df["CapitalExpenses"]

    # --- Debt Service ---
    if loan_amount > 0:
        df["InterestPayment"] = npf.ipmt(monthly_rate, df["MonthNum"], nper, loan_amount)
        df["PrincipalPayment"] = npf.ppmt(monthly_rate, df["MonthNum"], nper, loan_amount)
    else:
        df["InterestPayment"] = df["PrincipalPayment"] = 0

    df["CashFlowAfterDebtService"] = df["CashFlowBeforeDebtService"] + df["InterestPayment"] + df["PrincipalPayment"]

    # --- Sale ---
    f12_noi = df["NetOperatingIncome"].iloc[-12:].sum()
    sale_price = f12_noi / exit_cap if exit_cap != 0 else 0
    sale_cost = sale_price * cost_of_sale
    loan_payoff = max(loan_amount - (-df["PrincipalPayment"].sum()), 0)

    eq_index = [date_of_close] + list(df.index)
    eq = pd.DataFrame(index=pd.Index(eq_index, name="Date"))
    eq["UnleveredCashFlow"] = 0.0
    eq["LeveredCashFlow"] = 0.0
    eq.iloc[0] = [-purchase_price - closing_costs, -purchase_price - closing_costs + loan_amount]
    eq.loc[df.index, "UnleveredCashFlow"] = df["CashFlowBeforeDebtService"].values
    eq.loc[df.index, "LeveredCashFlow"] = df["CashFlowAfterDebtService"].values
    eq.iloc[-1] += [sale_price - sale_cost, sale_price - sale_cost - loan_payoff]

    print("✅ [Proforma Engine] Cash flow model built successfully.")
    return df, eq

if __name__ == "__main__":
    sample_data = {
        "purchase_price": 700000,
        "ltv": 0.7,
        "interest_rate": 0.045,
        "amortization_years": 30,
        "hold_period_years": 10,
        "date_of_close": "2020-01-01",
        "current_rent": 6200,
        "current_expense": 3100,
        "current_vacancy_rate": 0.05,
        "capital_expense_after_purchase": 8000,
        "expected_rent_growth": 0.04,
        "expected_expense_growth": 0.025,
        "expected_capex_growth": 0.02,
        "expected_appreciation": 0.054,
        "exit_cap_rate_expectation": 0.055,
        "cost_of_sale_percentage": 0.05,
        "loan_origination_fee": 0.01,
    }

    monthly_cf, equity_cf = build_proforma(sample_data)

    print("\n--- Monthly CF (Preview) ---")
    print(monthly_cf.head(3))
    print("\n--- Equity CF (Preview) ---")
    print(equity_cf.head(3))
