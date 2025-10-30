from db.mysql import get_connection, ping

def main():
    print("🔍 Testing database connection...")

    ping()

    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("📊 Tables found:", [t[0] for t in tables])
        conn.close()
        print("✅ Connection closed cleanly.")

if __name__ == "__main__":
    main()


