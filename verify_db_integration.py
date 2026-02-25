import os
import psycopg2
import sys

def verify_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL is not set!")
        return

    # Mask password for safety
    masked_url = db_url
    try:
        if "@" in db_url:
            user_pass, host_db = db_url.rsplit("@", 1)
            if ":" in user_pass:
                u, p = user_pass.split(":", 1)
                masked_url = f"{u}:***@{host_db}"
    except:
        masked_url = "FAILED_TO_MASK"

    print(f"/// CHECKING DATABASE INTEGRATION...")
    print(f"/// URL: {masked_url}")

    try:
        conn = psycopg2.connect(db_url)
        print("✅ Connection Successful!")

        with conn.cursor() as cur:
            # Check Tables
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = [row[0] for row in cur.fetchall()]
            print(f"/// Tables Found: {tables}")

            if 'raid_sessions' in tables:
                cur.execute("SELECT count(*) FROM raid_sessions")
                count = cur.fetchone()[0]
                print(f"✅ 'raid_sessions' table exists. Rows: {count}")
            else:
                print("❌ 'raid_sessions' table MISSING!")

            if 'players' in tables:
                cur.execute("SELECT count(*) FROM players")
                count = cur.fetchone()[0]
                print(f"✅ 'players' table exists. Rows: {count}")
            else:
                print("❌ 'players' table MISSING!")

            # Check specific user data integrity if possible?
            # We don't have user IDs here.

        conn.close()
        print("/// DATABASE VERIFICATION COMPLETE.")

    except Exception as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}")

if __name__ == "__main__":
    verify_db()
