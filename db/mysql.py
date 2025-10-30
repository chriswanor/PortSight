import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if conn.is_connected():
            print("Connected to MySQL database")
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None


def get_or_create_portfolio(conn, portfolio_name):
    cursor = conn.cursor()
    cursor.execute("SELECT portfolio_id FROM portfolios WHERE name = %s", (portfolio_name,))
    result = cursor.fetchone()
    if result:
        portfolio_id = result[0]
        print(f"Found existing portfolio '{portfolio_name}' (ID: {portfolio_id})")
    else:
        cursor.execute("INSERT INTO portfolios (name) VALUES (%s)", (portfolio_name,))
        conn.commit()
        portfolio_id = cursor.lastrowid
        print(f"Created new portfolio '{portfolio_name}' (ID: {portfolio_id})")
    cursor.close()
    return portfolio_id
