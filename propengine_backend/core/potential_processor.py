from sqlalchemy import text
from db.connection import engine
from services.calc_engine import calculate_property_analysis
from datetime import date


def process_potential_property(data):
    name = data.get("name", "Unnamed Property")
    print(f"Processing potential property: {name}")

    # Calculate property metrics using the enhanced calculation engine
    calculated_metrics = None
    try:
        # Convert input data to PropertyAssumptions format
        assumptions_dict = _convert_to_assumptions(data)
        calculated_metrics = calculate_property_analysis(assumptions_dict)
        print(f"Successfully calculated metrics for potential property: {name}")
    except Exception as e:
        print(f"Error calculating metrics for potential property {name}: {str(e)}")
        calculated_metrics = None

    # Store potential property data
    insert_potential_query = text("""
        INSERT INTO potential_properties (
            portfolio_id, name, address, city, state, zip,
            purchase_price_assumed, rent_assumed, expenses_assumed,
            loan_rate_assumed, ltv_assumed, hold_years_assumed, sale_price_assumed
        )
        VALUES (
            :portfolio_id, :name, :address, :city, :state, :zip,
            :purchase_price_assumed, :rent_assumed, :expenses_assumed,
            :loan_rate_assumed, :ltv_assumed, :hold_years_assumed, :sale_price_assumed
        )
    """)

    with engine.begin() as conn:
        result = conn.execute(insert_potential_query, {
            "portfolio_id": 1,
            "name": name,
            "address": data.get("address"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip": data.get("zip"),
            "purchase_price_assumed": data.get("purchase_price"),
            "rent_assumed": data.get("expected_rent"),
            "expenses_assumed": data.get("expected_expenses"),
            "loan_rate_assumed": data.get("loan_rate"),
            "ltv_assumed": data.get("ltv"),
            "hold_years_assumed": data.get("hold_period_months", 60) / 12,
            "sale_price_assumed": calculated_metrics["cash_flows"]["equity"].get("SaleProceeds", 0) if calculated_metrics else None,
        })

        potential_id = result.lastrowid

    return {
        "status": "success",
        "property_type": "potential",
        "potential_id": potential_id,
        "name": name,
        "message": "Potential property analyzed and stored successfully.",
        "calculated_metrics": calculated_metrics,
        "investment_summary": {
            "projected_irr": calculated_metrics["return_metrics"]["levered_irr"] if calculated_metrics else None,
            "projected_coc": calculated_metrics["return_metrics"]["avg_levered_coc"] if calculated_metrics else None,
            "going_in_cap_rate": calculated_metrics["going_in_metrics"]["cap_rate"] if calculated_metrics else None,
            "going_in_dscr": calculated_metrics["going_in_metrics"]["dscr"] if calculated_metrics else None,
            "equity_multiple": calculated_metrics["return_metrics"]["levered_equity_multiple"] if calculated_metrics else None,
        }
    }


def _convert_to_assumptions(data):
    """Convert input data to PropertyAssumptions format for potential properties"""
    return {
        "property_sf": data.get("property_sf", 1000),
        "purchase_price": data.get("purchase_price", 0),
        "date_of_close": data.get("date_of_close", date.today()),
        "ltv": data.get("ltv", 0.75),
        "interest_rate": data.get("loan_rate", 0.05),
        "amortization_years": data.get("amort_years", 30),
        "hold_period_months": data.get("hold_period_months", 60),
        "gross_potential_rent_per_sf_per_year": data.get("expected_rent", 0) / data.get("property_sf", 1000),
        "total_other_income_per_sf_per_year": data.get("other_income_per_sf", 0),
        "general_vacancy_rate": data.get("vacancy_rate", 0.05),
        "annual_rent_growth_rate": data.get("rent_growth_rate", 0.03),
        "annual_other_income_growth_rate": data.get("other_income_growth_rate", 0.02),
        "operating_expenses_per_sf_per_year": data.get("expected_expenses", 0) / data.get("property_sf", 1000),
        "capital_reserve_per_sf_per_year": data.get("capex_budget", 0) / data.get("property_sf", 1000) / 5,  # Annualized
        "annual_expense_growth_rate": data.get("expense_growth_rate", 0.03),
        "capital_reserve_growth_rate": data.get("capex_growth_rate", 0.02),
        "total_capital_improvements": data.get("capex_budget", 0),
        "capital_improvement_start_month": data.get("capex_start_month", 1),
        "capital_improvement_end_month": data.get("capex_end_month", 12),
        "exit_cap_rate": data.get("exit_cap_rate", 0.05),
        "cost_of_sale_percentage": data.get("cost_of_sale", 0.03),
        "closing_costs": data.get("closing_costs", data.get("purchase_price", 0) * 0.02),
        "loan_origination_fee": data.get("loan_origination_fee", 0.01),
    }