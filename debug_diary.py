import database as db
import psycopg2

def inspect_diary():
    print("--- Inspecting Diary Table ---")
    with db.db_cursor() as cur:
        if not cur:
            print("Failed to connect")
            return

        # Check column definition
        cur.execute("""
            SELECT column_name, column_default, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'diary' AND column_name = 'created_at'
        """)
        col_info = cur.fetchone()
        print(f"Column Info: {col_info}")

        # Check for NULLs
        cur.execute("SELECT count(*) FROM diary WHERE created_at IS NULL")
        null_count = cur.fetchone()[0]
        print(f"Rows with NULL created_at: {null_count}")

        # Try inserting
        print("--- Testing Insert ---")
        try:
            # We'll use a fake uid for testing
            test_uid = 123456789
            db.add_diary_entry(test_uid, "Test Entry")

            cur.execute("SELECT created_at FROM diary WHERE uid = %s AND entry = 'Test Entry' ORDER BY id DESC LIMIT 1", (test_uid,))
            res = cur.fetchone()
            print(f"Inserted entry created_at: {res[0]}")

            # Cleanup
            cur.execute("DELETE FROM diary WHERE uid = %s", (test_uid,))
        except Exception as e:
            print(f"Insert failed: {e}")

if __name__ == "__main__":
    inspect_diary()
