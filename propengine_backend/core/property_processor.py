from sqlalchemy import text
from db.connection import engine

def process_owned_property(data):
    name = data.get("name", "Unnamed Property")
    print(f"Processing owned property: {name}")

    insert_property_query = text("""
        INSERT INTO properties (
            portfolio_id, name, address, city, state, zip,
            current_value, current_rent, current_expense, vacancy_rate, tax_expense_annual
        )
        VALUES (
            :portfolio_id, :name, :address, :city, :state, :zip,
            :current_value, :current_rent, :current_expense, :vacancy_rate, :tax_expense_annual
        )
    """)

    with engine.begin() as conn:
        # Insert into properties
        result = conn.execute(insert_property_query, {
            "portfolio_id": 1,
            "name": name,
            "address": data.get("address"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip": data.get("zip"),
            "current_value": data.get("current_value"),
            "current_rent": data.get("current_rent"),
            "current_expense": data.get("current_expense"),
            "vacancy_rate": data.get("vacancy_rate"),
            "tax_expense_annual": data.get("tax_expense_annual"),
        })

        property_id = result.lastrowid

        insert_proforma_query = text("""
            INSERT INTO proforma_data (
                property_id, purchase_price, expected_rent, expected_expenses, 
                capex_budget, ltv, loan_rate, amort_years, target_irr, target_coc, exit_cap_rate
            )
            VALUES (
                :property_id, :purchase_price, :expected_rent, :expected_expenses,
                :capex_budget, :ltv, :loan_rate, :amort_years, :target_irr, :target_coc, :exit_cap_rate
            )
        """)

        conn.execute(insert_proforma_query, {
            "property_id": property_id,
            "purchase_price": data.get("purchase_price"),
            "expected_rent": data.get("expected_rent"),
            "expected_expenses": data.get("expected_expenses"),
            "capex_budget": data.get("capex_budget"),
            "ltv": data.get("ltv"),
            "loan_rate": data.get("loan_rate"),
            "amort_years": data.get("amort_years"),
            "target_irr": data.get("target_irr"),
            "target_coc": data.get("target_coc"),
            "exit_cap_rate": data.get("exit_cap_rate"),
        })

    return {
        "status": "success",
        "property_type": "owned",
        "property_id": property_id,
        "name": name,
        "message": "Property and proforma data stored successfully."
    }
