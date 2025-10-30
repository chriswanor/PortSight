import json
import os
from schema.input_format_schema import PropertyJSONInput
from db.mysql import get_connection, get_or_create_portfolio
from ingestion.owned_processor import run_owned_pipeline
#from ingestion.potential_processor import run_potential_pipeline

# --------------------------------------------------------
#  STEP 1: Load JSON
# --------------------------------------------------------
def load_json(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded JSON from {file_path}")
    return data


# --------------------------------------------------------
#  STEP 2: Validate JSON
# --------------------------------------------------------
def validate_json(data: dict) -> dict:
    validated = PropertyJSONInput(**data)
    print("JSON format and field types validated successfully.")
    
    # Convert Pydantic model back to dict with float values (not Decimal)
    try:
        result = validated.model_dump()  # Pydantic v2
    except AttributeError:
        result = validated.dict()  # Pydantic v1
    
    # Convert all Decimal values to float
    from decimal import Decimal
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
    
    return result


# --------------------------------------------------------
#  STEP 3: Portfolio Handling
# --------------------------------------------------------
def ensure_portfolio(conn, portfolio_name: str):
    portfolio_id = get_or_create_portfolio(conn, portfolio_name)
    print(f"Portfolio ready (ID: {portfolio_id})")
    return portfolio_id


# --------------------------------------------------------
#  STEP 4: Main Processing
# --------------------------------------------------------
def process_property(file_path: str):
    """Main ingestion entry point."""
    try:
        raw_data = load_json(file_path)
        data_dict = validate_json(raw_data)  # Already returns a dict with float values

        conn = get_connection()
        portfolio_id = ensure_portfolio(conn, data_dict["portfolio_name"])

        if data_dict["ownership_type"] == "owned":
            print("Owned property detected. Executing owned pipeline...")
            run_owned_pipeline(conn, portfolio_id, data_dict)

        elif data_dict["ownership_type"] == "potential":
            print("Potential property detected. Executing potential pipeline...")
            run_potential_pipeline(conn, portfolio_id, data_dict)

        else:
            print("Unknown ownership_type. Must be 'owned' or 'potential'.")

    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        try:
            conn.close()
            print("Database connection closed.")
        except:
            pass


if __name__ == "__main__":
    path = input("Enter path to property JSON: ").strip()
    process_property(path)
