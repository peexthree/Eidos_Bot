import sys
import os

# Ensure we can import from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import database
    import psycopg2
except ImportError as e:
    print(f"❌ Could not import dependencies: {e}")
    sys.exit(1)

def run_repair():
    print("🔧 Starting Database Repair...")
    try:
        # 1. Run standard init_db which now includes ensure_table_schema
        database.init_db()
        print("✅ Database schema repair logic executed.")

        # 2. Verify 'villains' table schema explicitly
        print("\n🔎 Verifying 'villains' table schema...")
        with database.db_cursor() as cur:
            if not cur:
                print("❌ No DB connection!")
                return
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'villains'
            """)
            cols = cur.fetchall()
            if not cols:
                print("❌ 'villains' table not found or empty schema!")

            for col in cols:
                name, dtype = col
                # dtype is usually lowercase in postgres like 'integer', 'character varying'
                print(f"   - {name}: {dtype}")

                # Check critical columns
                if name in ['def', 'atk', 'hp']:
                    if 'int' not in dtype.lower():
                         print(f"   ⚠️ WARNING: Column '{name}' is {dtype}, expected integer!")
                    else:
                         print(f"   ✅ Column '{name}' is CORRECT ({dtype})")

        print("\n✨ Repair process complete.")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_repair()
