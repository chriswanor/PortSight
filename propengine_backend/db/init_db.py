import os
from sqlalchemy import engine_from_config, text, inspect
from db.connection import engine

def init_db():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        print("Database already initilized")
        for table in existing_tables:
            print(f"   • {table}")
        print("Skipping initilization")
        return

    sql_path = os.path.join(os.path.dirname(__file__), "models.sql")

    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    with open(sql_path, "r") as file:
        sql_script = file.read()

    with engine.connect() as conn:
        for statement in sql_script.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"Error executing statement: {stmt}")
        conn.commit()

        print("database intialized successfully from models.sql")

    if __name__ == "__main__":
        init_db()


