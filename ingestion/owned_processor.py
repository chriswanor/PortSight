"""
Owned Property Processor
========================
Handles the full processing pipeline for OWNED properties.

Pipeline Overview:
1️⃣ Insert property record into `properties`
2️⃣ Insert acquisition data into `acquisition_data`
3️⃣ Generate and insert proforma + return metrics data into `proforma_data`
4️⃣ (Later) Fetch and insert market data into `market_data`
5️⃣ (Later) Update portfolio-level summaries
6️⃣ (Later) Generate AI investment recommendation

Each step is modular and can be tested independently.
"""

# --------------------------------------------------------
# Imports
# --------------------------------------------------------
from mysql.connector import Error
from db.mysql import get_connection, get_or_create_portfolio
from analytics.return_metrics_engine import generate_return_metrics


# --------------------------------------------------------
# STEP 1: Insert Property
# --------------------------------------------------------
def insert_property(conn, portfolio_id: int, data: dict) -> int:
    print("\n🧱 [Step 1] Inserting property record...")

    cursor = conn.cursor()

    sql = """
    INSERT INTO properties (
        portfolio_id, name, address, city, state, zip,
        property_type, bedrooms, bathrooms, year_built, property_sf,
        current_value, current_rent, current_expense, current_vacancy_rate, current_tax_annual,
        current_loan_balance, current_loan_rate, current_loan_remaining_years,
        acquisition_date, notes
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        portfolio_id,
        data.get("name"),
        data.get("address"),
        data.get("city"),
        data.get("state"),
        data.get("zip"),
        data.get("property_type"),
        data.get("bedrooms"),
        data.get("bathrooms"),
        data.get("year_built"),
        data.get("property_sf"),
        data.get("current_value"),
        data.get("current_rent"),
        data.get("current_expense"),
        data.get("current_vacancy_rate"),
        data.get("current_tax_annual"),
        data.get("current_loan_balance"),
        data.get("current_loan_rate"),
        data.get("current_loan_remaining_years"),
        data.get("acquisition_date"),
        data.get("notes"),
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        property_id = cursor.lastrowid
        print(f"✅ Property inserted successfully with ID: {property_id}")
        return property_id
    except Exception as e:
        print(f"❌ Error inserting property: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()


# --------------------------------------------------------
# STEP 2: Insert Acquisition Data
# --------------------------------------------------------
def insert_acquisition_data(conn, property_id: int, data: dict):
    print("\n💼 [Step 2] Inserting acquisition data...")

    cursor = conn.cursor()

    sql = """
    INSERT INTO acquisition_data (
        property_id, purchase_price, closing_costs, date_of_close, property_sf,
        rent_immediately_after_purchase, vacancy_immediately_after_purchase,
        other_income_immediately_after_purchase, operating_expenses_after_purchase,
        capital_expense_after_purchase, tax_assessment_price_immediately_after_purchase,
        capital_expenses_right_after_purchase,
        exit_cap_rate_expectation, hold_period_years, cost_of_sale_percentage,
        ltv, loan_origination_fee, interest_rate, amortization_years,
        expected_rent_growth, expected_expense_growth, expected_capex_growth, expected_appreciation
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        property_id,
        data.get("purchase_price"),
        data.get("closing_costs"),
        data.get("date_of_close"),
        data.get("property_sf"),
        data.get("rent_immediately_after_purchase"),
        data.get("vacancy_immediately_after_purchase"),
        data.get("other_income_immediately_after_purchase"),
        data.get("operating_expenses_after_purchase"),
        data.get("capital_expense_after_purchase"),
        data.get("tax_assessment_price_immediately_after_purchase"),
        data.get("capital_expenses_right_after_purchase"),
        data.get("exit_cap_rate_expectation"),
        data.get("hold_period_years"),
        data.get("cost_of_sale_percentage"),
        data.get("ltv"),
        data.get("loan_origination_fee"),
        data.get("interest_rate"),
        data.get("amortization_years"),
        0.04,   # expected_rent_growth
        0.025,  # expected_expense_growth
        0.02,   # expected_capex_growth
        0.054   # expected_appreciation
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        acquisition_id = cursor.lastrowid
        print(f"✅ Acquisition data inserted successfully (ID: {acquisition_id})")
        return acquisition_id
    except Exception as e:
        print(f"❌ Error inserting acquisition data: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def insert_proforma_data(conn, property_id: int, metrics: dict):
    """
    Step 3: Insert Proforma + Return Metrics Data
    =============================================
    Inserts computed return metrics from the Return Metrics Engine into `proforma_data`.

    Schema alignment (matches current table definition):
        - property_id
        - going_in_cap_rate, loan_constant, going_in_dscr, going_in_debt_yield
        - unlevered_irr, avg_unlevered_coc, unlevered_equity_multiple
        - levered_irr, avg_levered_coc, levered_equity_multiple
        - exit_ltv, year1_op_ex_ratio
        - projected_sale_price, net_sale_proceeds
    """

    print("\n📈 [Step 3] Inserting proforma + return metrics data...")

    cursor = conn.cursor()

    sql = """
    INSERT INTO proforma_data (
        property_id,
        going_in_cap_rate, loan_constant, going_in_dscr, going_in_debt_yield,
        unlevered_irr, avg_unlevered_coc, unlevered_equity_multiple,
        levered_irr, avg_levered_coc, levered_equity_multiple,
        exit_ltv, year1_op_ex_ratio,
        projected_sale_price, net_sale_proceeds
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s
    )
    """

    # Cleanly extract all values, defaulting to None if missing
    values = (
        property_id,
        metrics.get("going_in_cap_rate"),
        metrics.get("loan_constant"),
        metrics.get("going_in_dscr"),
        metrics.get("going_in_debt_yield"),
        metrics.get("unlevered_irr"),
        metrics.get("avg_unlevered_coc"),
        metrics.get("unlevered_equity_multiple"),
        metrics.get("levered_irr"),
        metrics.get("avg_levered_coc"),
        metrics.get("levered_equity_multiple"),
        metrics.get("exit_ltv"),
        metrics.get("year1_op_ex_ratio"),
        metrics.get("projected_sale_price"),
        metrics.get("net_sale_proceeds"),
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        print("✅ [Step 3] Proforma and return metrics inserted successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ [Step 3] Error inserting proforma data: {type(e).__name__}: {e}")
        print("   ↳ Check that column names and data types match the `proforma_data` schema.")
    finally:
        cursor.close()



def run_owned_pipeline(conn, portfolio_id: int, data: dict):
    """
    Controls the full owned-property ingestion workflow.
    Each step can later be modularly enabled/disabled for testing.
    """
    print("\n🚀 [Owned Property Pipeline] Starting full ingestion pipeline...")

    # STEP 1: Insert Property
    property_id = insert_property(conn, portfolio_id, data)
    if not property_id:
        print("❌ Pipeline stopped — property insertion failed.")
        return

    # STEP 2: Insert Acquisition Data
    acquisition_id = insert_acquisition_data(conn, property_id, data)
    if not acquisition_id:
        print("❌ Pipeline stopped — acquisition data insertion failed.")
        return

    # STEP 3: Generate Proforma and Metrics
    from analytics.return_metrics_engine import generate_return_metrics
    print("\n⚙️ Generating return metrics...")
    metrics = generate_return_metrics(data)
    insert_proforma_data(conn, property_id, metrics)

    print("\n✅ [Pipeline Complete] Property successfully processed and stored.")


# --------------------------------------------------------
# STANDALONE EXECUTION TEST
# --------------------------------------------------------
if __name__ == "__main__":
    conn = get_connection()
    portfolio_id = get_or_create_portfolio(conn, "Core Residential Portfolio")

    sample_data = {
        "ownership_type": "owned",
        "portfolio_name": "Core Residential Portfolio",
        "name": "Maplewood Apartments",
        "address": "123 Maple St",
        "city": "Minneapolis",
        "state": "MN",
        "zip": "55401",
        "property_type": "Multi-Family",
        "bedrooms": 8,
        "bathrooms": 4.0,
        "year_built": 1985,
        "property_sf": 4500,
        "current_value": 750000,
        "current_rent": 6200,
        "current_expense": 3100,
        "current_vacancy_rate": 0.05,
        "current_tax_annual": 12000,
        "current_loan_balance": 420000,
        "current_loan_rate": 0.045,
        "current_loan_remaining_years": 18,
        "acquisition_date": "2019-08-01",
        "purchase_price": 700000,
        "closing_costs": 0.02,
        "date_of_close": "2019-08-01",
        "rent_immediately_after_purchase": 5800,
        "capital_expense_after_purchase": 8000,
        "tax_assessment_price_immediately_after_purchase": 690000,
        "capital_expenses_right_after_purchase": 2000,
        "exit_cap_rate_expectation": 0.055,
        "hold_period_years": 10,
        "cost_of_sale_percentage": 0.05,
        "ltv": 0.70,
        "loan_origination_fee": 0.01,
        "interest_rate": 0.045,
        "amortization_years": 30,
    }

    run_owned_pipeline(conn, portfolio_id, sample_data)
