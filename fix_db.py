import os
import psycopg2
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')

def fix_bot_states():
    print("/// Fixing bot_states table...")
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Check if constraint exists
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'bot_states'::regclass AND contype = 'p';
        """)
        if cur.fetchone():
            print("/// bot_states already has PRIMARY KEY. Skipping.")
        else:
            print("/// No PRIMARY KEY found on bot_states. Fixing...")

            # Deduplicate first
            print("/// Removing duplicates...")
            cur.execute("""
                DELETE FROM bot_states a USING bot_states b
                WHERE a.ctid < b.ctid AND a.uid = b.uid;
            """)

            # Add Primary Key
            print("/// Adding PRIMARY KEY...")
            cur.execute("ALTER TABLE bot_states ADD PRIMARY KEY (uid);")
            conn.commit()
            print("/// bot_states fixed!")

    except Exception as e:
        print(f"/// Error fixing bot_states: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def fix_inventory():
    print("/// Checking inventory table...")
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Check if 'id' column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='inventory' AND column_name='id'")
        if not cur.fetchone():
            print("/// Inventory table missing 'id' column! Checks required.")
        else:
            print("/// Inventory table has 'id' column. V2 schema active.")

        # Check for legacy unique constraint that might block multiple items
        # The migration code attempts to drop 'inventory_uid_item_id_key'
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'inventory'::regclass AND contype = 'u';
        """)
        constraints = cur.fetchall()
        for con in constraints:
            name = con[0]
            print(f"/// Found UNIQUE constraint on inventory: {name}")
            # We should drop unique constraints on (uid, item_id) for V2
            if 'uid' in name and 'item' in name:
                 print(f"/// Dropping legacy constraint {name}...")
                 cur.execute(f"ALTER TABLE inventory DROP CONSTRAINT {name}")
                 conn.commit()
                 print("/// Dropped.")

    except Exception as e:
        print(f"/// Error checking inventory: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    if not DATABASE_URL:
        print("Error: DATABASE_URL not set")
        sys.exit(1)
    fix_bot_states()
    fix_inventory()
