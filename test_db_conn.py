import os
import psycopg2
import sys

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to DB...")
try:
    conn = psycopg2.connect(db_url, connect_timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(f"Result: {cur.fetchone()}")
    cur.close()
    conn.close()
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
