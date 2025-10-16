"""
Data schemas and models for property calculations
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class PropertyAssumptions:
    """Property assumptions for financial modeling"""
    # Basic property info
    property_sf: float
    purchase_price: float
    date_of_close: date
    
    # Financial assumptions
    ltv: float  # Loan-to-value ratio
    interest_rate: float
    amortization_years: int
    hold_period_months: int
    
    # Income assumptions
    gross_potential_rent_per_sf_per_year: float
    total_other_income_per_sf_per_year: float
    general_vacancy_rate: float
    annual_rent_growth_rate: float
    annual_other_income_growth_rate: float
    
    # Expense assumptions
    operating_expenses_per_sf_per_year: float
    capital_reserve_per_sf_per_year: float
    annual_expense_growth_rate: float
    capital_reserve_growth_rate: float
    
    # Sale assumptions (non-defaults)
    exit_cap_rate: float
    cost_of_sale_percentage: float
    
    # Closing costs (non-defaults)
    closing_costs: float
    loan_origination_fee: float
    
    # Capital improvements (defaults after all required fields)
    total_capital_improvements: float = 0.0
    capital_improvement_start_month: int = 1
    capital_improvement_end_month: int = 0


@dataclass
class PropertyMetrics:
    """Calculated property metrics"""
    # Going-in metrics
    going_in_cap_rate: float
    going_in_dscr: float
    going_in_debt_yield: float
    loan_constant: float
    year1_op_ex_ratio: float
    
    # Exit metrics
    exit_ltv: float
    
    # Return metrics
    unlevered_irr: Optional[float]
    levered_irr: Optional[float]
    unlevered_equity_multiple: float
    levered_equity_multiple: float
    avg_unlevered_coc: float
    avg_levered_coc: float
    
    # Cash flows
    monthly_cash_flows: dict
    equity_cash_flows: dict
    cash_on_cash_table: dict


@dataclass
class PortfolioMetrics:
    """Portfolio-level aggregated metrics"""
    total_equity: float
    total_value: float
    total_debt: float
    avg_irr_actual: float
    avg_irr_target: float
    avg_dscr: float
    avg_ltv: float
    variance_irr: float
    variance_noi: float
