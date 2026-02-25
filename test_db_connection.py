import os
import psycopg2
import sys

# Get URL from env or use a placeholder for testing syntax
DATABASE_URL = os.environ.get('DATABASE_URL')

def test_connection():
    if not DATABASE_URL:
        print("/// SKIP: DATABASE_URL not set. Cannot test connection.")
        return

    print(f"/// TESTING CONNECTION TO: {DATABASE_URL.split('@')[-1]}") # Log host only

    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode='require',
            connect_timeout=10
        )
        print("/// CONNECTION SUCCESSFUL!")

        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()
        print(f"/// DB VERSION: {ver[0]}")

        conn.close()
        print("/// CONNECTION CLOSED.")

    except Exception as e:
        print(f"/// CONNECTION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
