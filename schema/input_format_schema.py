from pydantic import BaseModel, Field, condecimal, constr
from typing import Literal

class PropertyJSONInput(BaseModel):
    """Validates structure and field types for ingestion."""

    # ----------------------------
    # Core Metadata
    # ----------------------------
    ownership_type: Literal["owned", "potential"]
    portfolio_name: constr(strip_whitespace=True, min_length=1)
    name: constr(strip_whitespace=True, min_length=1)
    address: constr(strip_whitespace=True, min_length=1)
    city: constr(strip_whitespace=True, min_length=1)
    state: constr(strip_whitespace=True, min_length=1)
    zip: constr(strip_whitespace=True, min_length=1)
    property_type: constr(strip_whitespace=True, min_length=1)

    bedrooms: int = Field(..., ge=0)
    bathrooms: condecimal(max_digits=3, decimal_places=1)
    year_built: int = Field(..., ge=1800)
    property_sf: int = Field(..., gt=0)

    # ----------------------------
    # Current Property Snapshot (optional, not used in proforma)
    # ----------------------------
    current_value: condecimal(max_digits=15, decimal_places=2)
    current_tax_annual: condecimal(max_digits=12, decimal_places=2)
    current_loan_balance: condecimal(max_digits=15, decimal_places=2)
    current_loan_rate: condecimal(ge=0, le=1, max_digits=6, decimal_places=4)
    current_loan_remaining_years: int = Field(..., gt=0)

    # ----------------------------
    # Acquisition Inputs
    # ----------------------------
    acquisition_date: constr(strip_whitespace=True, min_length=4)
    purchase_price: condecimal(max_digits=15, decimal_places=2)
    closing_costs: condecimal(ge=0, le=1, max_digits=5, decimal_places=4)
    date_of_close: constr(strip_whitespace=True, min_length=4)

    rent_immediately_after_purchase: condecimal(max_digits=12, decimal_places=2)
    vacancy_immediately_after_purchase: condecimal(ge=0, le=1, max_digits=6, decimal_places=4)
    other_income_immediately_after_purchase: condecimal(max_digits=12, decimal_places=2)
    operating_expenses_after_purchase: condecimal(max_digits=12, decimal_places=2)
    capital_expense_after_purchase: condecimal(max_digits=12, decimal_places=2)
    tax_assessment_price_immediately_after_purchase: condecimal(max_digits=15, decimal_places=2)
    capital_expenses_right_after_purchase: condecimal(max_digits=12, decimal_places=2)

    exit_cap_rate_expectation: condecimal(ge=0, le=1, max_digits=6, decimal_places=4)
    hold_period_years: int = Field(..., gt=0)
    cost_of_sale_percentage: condecimal(ge=0, le=1, max_digits=5, decimal_places=4)
    ltv: condecimal(ge=0, le=1, max_digits=6, decimal_places=4)
    loan_origination_fee: condecimal(max_digits=6, decimal_places=4)
    interest_rate: condecimal(ge=0, le=1, max_digits=6, decimal_places=4)
    amortization_years: int = Field(..., gt=0)
