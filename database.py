import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import time
import logging
import random
from datetime import datetime
import re
import traceback
from config import ITEMS_INFO, INVENTORY_LIMIT
from content_presets import CONTENT_DATA, VILLAINS_DATA, OLD_VILLAINS_NAMES

DATABASE_URL = os.environ.get('DATABASE_URL')

# Global Connection Pool
pg_pool = None

def init_pool():
    global pg_pool
    if not pg_pool:
        try:
            pg_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=DATABASE_URL,
                sslmode='require',
                options='-c lock_timeout=10000'
            )
            print("/// DB POOL INITIALIZED")
        except Exception as e:
            print(f"/// DB POOL INIT ERROR: {e}")

@contextmanager
def db_session():
    if not pg_pool:
        init_pool()

    conn = None
    try:
        if pg_pool:
            conn = pg_pool.getconn()
            yield conn
            conn.commit()
        else:
            yield None
    except Exception as e:
        if conn: conn.rollback()
        print(f"/// DB ERROR: {e}")
        print(traceback.format_exc())
    finally:
        if conn and pg_pool:
            pg_pool.putconn(conn)

@contextmanager
def db_cursor(cursor_factory=None):
    with db_session() as conn:
        if conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur
        else:
            yield None

def admin_exec_query(query, params=None):
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                return "OK (No return data)"
    except Exception as e:
        return f"ERROR: {e}"

def admin_force_delete_item(uid, item_id):
    with db_cursor() as cur:
        if not cur: return False
        # Fallback to delete all instances if legacy item_id logic is used
        cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
        return cur.rowcount > 0

def get_all_tables():
    with db_cursor() as cur:
        if not cur: return []
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return [row[0] for row in cur.fetchall()]

def init_db():
    print("/// DEBUG: init_db started")
    with db_session() as conn:
        if not conn: return
        with conn.cursor() as cur:
            print("/// DEBUG: creating users table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    uid BIGINT PRIMARY KEY,
                    username TEXT, first_name TEXT, path TEXT DEFAULT 'general',
                    xp INTEGER DEFAULT 0, biocoin INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1,
                    last_active DATE DEFAULT CURRENT_DATE,
                    cryo INTEGER DEFAULT 0, accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0,
                    accel_exp BIGINT DEFAULT 0, referrer TEXT,
                    ref_profit_xp INTEGER DEFAULT 0, ref_profit_coins INTEGER DEFAULT 0,
                    last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0,
                    notified BOOLEAN DEFAULT TRUE, max_depth INTEGER DEFAULT 0,
                    ref_count INTEGER DEFAULT 0, know_count INTEGER DEFAULT 0, total_spent INTEGER DEFAULT 0,
                    raid_count_today INTEGER DEFAULT 0, last_raid_date DATE DEFAULT CURRENT_DATE,
                    is_admin BOOLEAN DEFAULT FALSE
                );
            ''')
            try:
                print("/// DEBUG: migrating users columns")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS raid_count_today INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_raid_date DATE DEFAULT CURRENT_DATE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS biocoin INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS encrypted_cache_unlock_time BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS encrypted_cache_type TEXT DEFAULT NULL")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS shadow_broker_expiry BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS anomaly_buff_expiry BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS anomaly_buff_type TEXT DEFAULT NULL")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS proxy_expiry BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                # New Stats for Achievements
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS kills INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS raids_done INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS perfect_raids INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_wins INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS messages INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS purchases INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS found_zero BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_glitched BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS found_devtrace BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS night_visits INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS clicks INTEGER DEFAULT 0")
                # Onboarding & Quarantine
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_stage INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_start_time BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_quarantined BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quarantine_end_time BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_history TEXT DEFAULT ''")
                # PVP v2.0
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deck_level INTEGER DEFAULT 1")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deck_config TEXT DEFAULT '{\"1\": \"soft_brute_v1\", \"2\": null, \"3\": null}'")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS shield_until BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_hack_target BIGINT DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS active_hardware TEXT DEFAULT '{}'")
            except: pass

            print("/// DEBUG: creating death_loot table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS death_loot (
                    id SERIAL PRIMARY KEY,
                    depth INTEGER,
                    amount INTEGER,
                    created_at BIGINT,
                    original_owner_name TEXT
                );
            ''')

            print("/// DEBUG: creating raid_graves table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raid_graves (
                    id SERIAL PRIMARY KEY,
                    depth INTEGER,
                    loot_json TEXT,
                    owner_name TEXT,
                    message TEXT,
                    created_at BIGINT
                );
            ''')

            print("/// DEBUG: creating logs table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    uid BIGINT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            print("/// DEBUG: creating pvp_logs table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pvp_logs (
                    id SERIAL PRIMARY KEY,
                    attacker_uid BIGINT,
                    target_uid BIGINT,
                    stolen_coins INTEGER,
                    success BOOLEAN,
                    timestamp BIGINT,
                    is_revenged BOOLEAN DEFAULT FALSE,
                    is_anonymous BOOLEAN DEFAULT FALSE
                );
            ''')

            print("/// DEBUG: creating history table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id SERIAL PRIMARY KEY,
                    uid BIGINT,
                    archived_data_json TEXT,
                    reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # --- INVENTORY MIGRATION V2 ---
            # We need to support unique item instances.
            # 1. Check if 'id' column exists.
            needs_migration = False
            try:
                cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='inventory' AND column_name='id'")
                if not cur.fetchone():
                    needs_migration = True
            except: pass

            if needs_migration:
                print("/// DEBUG: MIGRATING INVENTORY TO V2 (Instance Based)")
                try:
                    # 1. Rename old table
                    cur.execute("ALTER TABLE inventory RENAME TO inventory_old")
                    # 2. Create new table
                    cur.execute('''
                        CREATE TABLE inventory (
                            id SERIAL PRIMARY KEY,
                            uid BIGINT,
                            item_id TEXT,
                            quantity INTEGER DEFAULT 1,
                            durability INTEGER DEFAULT 100
                        )
                    ''')
                    # 3. Copy data and EXPAND stacks
                    # Using generate_series to unroll quantity into individual rows with quantity 1
                    cur.execute("""
                        INSERT INTO inventory (uid, item_id, quantity, durability)
                        SELECT uid, item_id, 1, durability
                        FROM inventory_old
                        CROSS JOIN generate_series(1, quantity)
                    """)
                    # 4. Drop old table
                    cur.execute("DROP TABLE inventory_old")
                    conn.commit()
                except Exception as e:
                    print(f"/// MIGRATION ERROR: {e}")
                    conn.rollback()

            # --- FIX: REMOVE LEGACY CONSTRAINTS ---
            try:
                print("/// DEBUG: Removing legacy unique constraints on inventory")
                cur.execute("ALTER TABLE inventory DROP CONSTRAINT IF EXISTS inventory_uid_item_id_key")
                cur.execute("DROP INDEX IF EXISTS inventory_uid_item_id_key")
                conn.commit()
            except Exception as e:
                print(f"/// CONSTRAINT DROP ERROR: {e}")
                conn.rollback()

            # Ensure user_equipment has durability
            try:
                cur.execute("ALTER TABLE user_equipment ADD COLUMN IF NOT EXISTS durability INTEGER DEFAULT 10")
            except: pass

            print("/// DEBUG: creating content table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id SERIAL PRIMARY KEY, type TEXT, path TEXT DEFAULT 'general', level INTEGER DEFAULT 1, text TEXT UNIQUE
                );
            ''')

            print("/// DEBUG: creating raid_content table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raid_content (
                    id SERIAL PRIMARY KEY, text TEXT, type TEXT DEFAULT 'neutral', val INTEGER DEFAULT 0
                );
            ''')

            print("/// DEBUG: creating raid_sessions table")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raid_sessions (
                    uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100,
                    start_time BIGINT, buffer_xp INTEGER DEFAULT 0, buffer_coins INTEGER DEFAULT 0
                );
            ''')
            try:
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS current_enemy_id INTEGER DEFAULT NULL")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS current_enemy_hp INTEGER DEFAULT NULL")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS kills INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS riddles_solved INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS current_riddle_answer TEXT DEFAULT NULL")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS next_event_type TEXT DEFAULT NULL")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS event_streak INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS buffer_items TEXT DEFAULT ''")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS is_elite BOOLEAN DEFAULT FALSE")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS mechanic_data TEXT DEFAULT '{}'")
            except: conn.rollback()

            print("/// DEBUG: creating remaining tables (user_knowledge...)")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_knowledge (
                    uid BIGINT, content_id INTEGER, PRIMARY KEY(uid, content_id)
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS unlocked_protocols (
                    uid BIGINT, protocol_id INTEGER, PRIMARY KEY(uid, protocol_id)
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_equipment (
                    uid BIGINT, slot TEXT, item_id TEXT, PRIMARY KEY(uid, slot)
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS diary (
                    id SERIAL PRIMARY KEY, uid BIGINT, entry TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    uid BIGINT, ach_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id)
                );
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS villains (
                    id SERIAL PRIMARY KEY, name TEXT, level INTEGER, hp INTEGER, atk INTEGER, def INTEGER,
                    xp_reward INTEGER, coin_reward INTEGER, description TEXT, UNIQUE(name)
                );
            ''')
            try:
                cur.execute("ALTER TABLE villains ADD COLUMN IF NOT EXISTS image TEXT")
            except: pass

            # --- BOT STATES (FSM) ---
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bot_states (
                    uid BIGINT PRIMARY KEY,
                    state TEXT,
                    data TEXT
                );
            ''')

    print("/// DEBUG: populating villains")
    populate_villains()
    print("/// DEBUG: populating content")
    populate_content()
    print("/// DEBUG: init_db finished")

# --- STATE MANAGEMENT ---
def set_state(uid, state, data=None):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_states (uid, state, data) VALUES (%s, %s, %s)
                ON CONFLICT (uid) DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data
            """, (uid, state, data))

def get_state(uid):
    with db_cursor() as cur:
        if not cur: return None
        cur.execute("SELECT state, data FROM bot_states WHERE uid = %s", (uid,))
        res = cur.fetchone()
        if res:
            return res[0]
        return None

def get_full_state(uid):
    with db_cursor() as cur:
        if not cur: return None
        cur.execute("SELECT state, data FROM bot_states WHERE uid = %s", (uid,))
        res = cur.fetchone()
        return res if res else None

def delete_state(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bot_states WHERE uid = %s", (uid,))

def populate_villains():
    with db_session() as conn:
        with conn.cursor() as cur:
            # Delete old versions to force update with icons
            try:
                cur.execute("DELETE FROM villains WHERE name IN %s", (OLD_VILLAINS_NAMES,))
            except Exception as e:
                print(f"Cleanup Error: {e}")

            for v in VILLAINS_DATA:
                cur.execute("""
                    INSERT INTO villains (name, level, hp, atk, def, xp_reward, coin_reward, description, image)
                    VALUES (%(name)s, %(level)s, %(hp)s, %(atk)s, %(def)s, %(xp)s, %(coin)s, %(desc)s, %(image)s)
                    ON CONFLICT (name) DO UPDATE SET level = EXCLUDED.level, hp = EXCLUDED.hp, atk = EXCLUDED.atk, def = EXCLUDED.def, xp_reward = EXCLUDED.xp_reward, coin_reward = EXCLUDED.coin_reward, description = EXCLUDED.description, image = EXCLUDED.image
                """, v)

def get_user(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
        return cur.fetchone()

def add_user(uid, username, first_name, referrer=None):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (uid, username, first_name, referrer, last_active) VALUES (%s, %s, %s, %s, CURRENT_DATE) ON CONFLICT (uid) DO NOTHING", (uid, username, first_name, referrer))
            if referrer and str(referrer) != str(uid):
                cur.execute("UPDATE users SET ref_count = ref_count + 1 WHERE uid = %s", (referrer,))

def update_user(uid, **kwargs):
    if not kwargs: return
    set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
    values = list(kwargs.values()) + [uid]
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", values)

def set_user_active(uid, status):
    update_user(uid, is_active=status)

def add_xp_to_user(uid, amount):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (amount, uid))
            cur.execute("SELECT referrer FROM users WHERE uid = %s", (uid,))
            res = cur.fetchone()
            if res and res[0]:
                ref_id = res[0]
                profit = int(amount * 0.1)
                if profit > 0:
                    cur.execute("UPDATE users SET xp = xp + %s, ref_profit_xp = ref_profit_xp + %s WHERE uid = %s", (profit, profit, ref_id))

def increment_user_stat(uid, stat, amount=1):
    # Safe allow-list for stats
    ALLOWED_STATS = ['kills', 'raids_done', 'perfect_raids', 'quiz_wins', 'messages', 'likes', 'purchases', 'night_visits', 'clicks']
    if stat not in ALLOWED_STATS: return False

    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {stat} = {stat} + %s WHERE uid = %s", (amount, uid))
            return cur.rowcount > 0

def set_user_stat(uid, stat, value):
    # Safe allow-list for boolean flags
    ALLOWED_STATS = ['found_zero', 'is_glitched', 'found_devtrace']
    if stat not in ALLOWED_STATS: return False

    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {stat} = %s WHERE uid = %s", (value, uid))
            return cur.rowcount > 0

def reset_daily_stats(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET raid_count_today = 0, last_raid_date = CURRENT_DATE WHERE uid = %s", (uid,))

def add_item(uid, item_id, qty=1, cursor=None, specific_durability=None):
    # Import locally to avoid circular deps if any
    from config import EQUIPMENT_DB, CURSED_CHEST_DROPS

    def _add_logic(cur):
        is_equipment = item_id in EQUIPMENT_DB

        # Check limits only if creating NEW entry/stack
        # For equipment, every item is a new entry.
        # For consumables, only if not exists.

        check_limit = False
        if is_equipment:
            check_limit = True
        else:
            cur.execute("SELECT 1 FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
            if not cur.fetchone():
                check_limit = True

        if check_limit:
            cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
            res = cur.fetchone()
            count = res[0] if res else 0
            if count >= INVENTORY_LIMIT:
                return False

        if is_equipment:
            # Equipment: Always insert new row with unique durability
            if specific_durability:
                durability = specific_durability
            elif item_id in CURSED_CHEST_DROPS:
                durability = 50
            else:
                durability = random.randint(5, 10)

            # Insert QTY times
            for _ in range(qty):
                cur.execute("""
                    INSERT INTO inventory (uid, item_id, quantity, durability)
                    VALUES (%s, %s, 1, %s)
                """, (uid, item_id, durability))
        else:
            # Consumable: Stack
            # PK is id, so we can't use ON CONFLICT(uid, item_id)
            cur.execute("SELECT id, quantity FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
            row = cur.fetchone()
            if row:
                inv_id, current_qty = row
                cur.execute("UPDATE inventory SET quantity = quantity + %s WHERE id = %s", (qty, inv_id))
            else:
                cur.execute("""
                    INSERT INTO inventory (uid, item_id, quantity, durability)
                    VALUES (%s, %s, %s, 100)
                """, (uid, item_id, qty))

        return True

    if cursor:
        return _add_logic(cursor)

    with db_cursor() as cur:
        if not cur: return False
        return _add_logic(cur)

def get_inventory(uid, cursor=None):
    # Returns list including 'id' for handling individual items
    query = "SELECT id, uid, item_id, quantity, durability FROM inventory WHERE quantity > 0 AND uid = %s ORDER BY item_id ASC"
    if cursor:
        cursor.execute(query, (uid,))
        return cursor.fetchall()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute(query, (uid,))
        return cur.fetchall()

def use_item(uid, item_id, qty=1, cursor=None):
    # This function is mostly used for consumables/currencies/logic
    # For equipment 'dismantle', we should use a specific function or logic, but
    # legacy calls use this. We need to handle stack vs individual.
    # If item_id is passed, and multiple exist, which one to use?
    # Default to "First found" for consumables/legacy compatibility.

    def _use_logic(cur):
        cur.execute("SELECT id, quantity FROM inventory WHERE uid=%s AND item_id=%s ORDER BY id LIMIT 1", (uid, item_id))
        row = cur.fetchone()
        if not row: return False

        inv_id, quantity = row
        # Handling row dict or tuple
        if isinstance(row, dict):
            inv_id = row['id']
            quantity = row['quantity']

        if quantity >= qty:
            new_qty = quantity - qty
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id = %s", (inv_id,))
            else:
                cur.execute("UPDATE inventory SET quantity = %s WHERE id = %s", (new_qty, inv_id))
            return True
        else:
            # Not enough in this stack?
            # Current logic implies singular consumable stacks.
            return False

    if cursor:
        return _use_logic(cursor)

    with db_cursor() as cur:
        if not cur: return False
        return _use_logic(cur)

def decrease_durability(uid, slot, amount=1):
    # Updates durability in user_equipment directly
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT durability, item_id FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        res = cur.fetchone()
        if not res: return False

        dur, item_id = res
        if dur is None: dur = 10 # Fallback

        new_dur = max(0, dur - amount)
        cur.execute("UPDATE user_equipment SET durability = %s WHERE uid=%s AND slot=%s", (new_dur, uid, slot))

        return True # Just decrease, don't auto-unequip here (handled by raid logic or check)

def get_inventory_size(uid):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
        return cur.fetchone()[0]

def equip_item(uid, inv_id, slot):
    # inv_id is the primary key in inventory table
    try:
        with db_cursor() as cur:
            if not cur: return False

            # 1. Get item from inventory
            cur.execute("SELECT item_id, durability, quantity FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
            res = cur.fetchone()
            if not res: return False
            item_id, durability, qty = res

            # 2. Check if slot is occupied
            cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()

            if old:
                # Unequip old item -> Move to Inventory
                old_item_id, old_dur = old
                if old_dur is None: old_dur = 10
                cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, %s)", (uid, old_item_id, old_dur))

            # 3. Equip new item
            # upsert into user_equipment
            cur.execute("""
                INSERT INTO user_equipment (uid, slot, item_id, durability) VALUES (%s, %s, %s, %s)
                ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, durability = EXCLUDED.durability
            """, (uid, slot, item_id, durability))

            # 4. Remove from inventory (or decrement)
            if qty > 1:
                cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id=%s", (inv_id,))
            else:
                cur.execute("DELETE FROM inventory WHERE id=%s", (inv_id,))

            return True
    except Exception as e:
        print(f"Equip Error: {e}")
        return False

def unequip_item(uid, slot):
    try:
        with db_cursor() as cur:
            if not cur: return False

            cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if not old: return False

            item_id, durability = old
            if durability is None: durability = 10

            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))

            # Move to inventory
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, %s)", (uid, item_id, durability))
            return True
    except Exception as e:
        print(f"Unequip Error: {e}")
        return False

def get_equipped_items(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT slot, item_id, durability FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cur.fetchall()}

def get_equipped_item_in_slot(uid, slot):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cur.fetchone()

def break_equipment_randomly(uid):
    # Reduces durability of a random item. If 0, unequip it.
    # Returns the item_id that broke (hit 0), or None.
    with db_cursor() as cur:
        if not cur: return None

        # Select random equipped item
        cur.execute("SELECT slot, item_id, durability FROM user_equipment WHERE uid=%s ORDER BY RANDOM() LIMIT 1", (uid,))
        res = cur.fetchone()
        if not res: return None

        slot, item_id, durability = res
        if durability is None: durability = 10

        new_dur = max(0, durability - 1)
        cur.execute("UPDATE user_equipment SET durability = %s WHERE uid=%s AND slot=%s", (new_dur, uid, slot))

        if new_dur == 0:
            # Move to inventory (Broken)
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, 0)", (uid, item_id))
            return item_id # Signal that it broke

        return None

def repair_item(uid, inv_id):
    from config import CURSED_CHEST_DROPS
    with db_cursor() as cur:
        if not cur: return False

        cur.execute("SELECT item_id FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
        res = cur.fetchone()
        if not res: return False

        item_id = res[0]
        max_dur = 50 if item_id in CURSED_CHEST_DROPS else 10

        cur.execute("UPDATE inventory SET durability = %s WHERE id=%s", (max_dur, inv_id))
        return True

def dismantle_item(uid, inv_id):
    # Deletes item or decrements stack
    with db_cursor() as cur:
        if not cur: return False

        cur.execute("SELECT quantity FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
        res = cur.fetchone()
        if not res: return False
        qty = res[0]

        if qty > 1:
             cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id=%s", (inv_id,))
             return True
        else:
             cur.execute("DELETE FROM inventory WHERE id=%s", (inv_id,))
             return cur.rowcount > 0

def get_item_count(uid, item_id, cursor=None):
    query = "SELECT SUM(quantity) as total FROM inventory WHERE uid=%s AND item_id=%s"

    def _extract(res):
        if not res: return 0
        if isinstance(res, dict):
            val = res.get('total')
        else:
            val = res[0]
        return int(val) if val is not None else 0

    if cursor:
        cursor.execute(query, (uid, item_id))
        res = cursor.fetchone()
        return _extract(res)

    with db_cursor() as cur:
        if not cur: return 0
        cur.execute(query, (uid, item_id))
        res = cur.fetchone()
        return _extract(res)

def check_achievement_exists(uid, ach_id):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
        return cur.fetchone() is not None

def grant_achievement(uid, ach_id, bonus_xp):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, ach_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
            return True
        return False

def get_archived_protocols(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("""
            SELECT c.text FROM content c
            JOIN unlocked_protocols up ON c.id = up.protocol_id
            WHERE up.uid = %s
        """, (uid,))
        return cur.fetchall()

def get_unlocked_protocols(uid):
    return get_archived_protocols(uid)

def save_knowledge(uid, content_id):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
        cur.execute("INSERT INTO unlocked_protocols (uid, protocol_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE users SET know_count = know_count + 1 WHERE uid = %s", (uid,))

def get_leaderboard(limit=10, sort_by='xp'):
    order_clause = "xp DESC, level DESC, uid ASC"
    if sort_by == 'depth':
        order_clause = "max_depth DESC, xp DESC, uid ASC"
    elif sort_by == 'biocoin':
        order_clause = "biocoin DESC, xp DESC, uid ASC"

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        # Using format string for ORDER BY is necessary as it cannot be parameterized directly.
        # sort_by is controlled by code logic, not user input directly (enum-like), so it's safe-ish.
        query = f"SELECT uid, first_name, username, xp, level, max_depth, biocoin, path FROM users ORDER BY {order_clause} LIMIT %s"
        cur.execute(query, (limit,))
        return cur.fetchall()

def get_user_rank(uid, sort_by='xp'):
    # Determine the comparison logic based on sort_by
    # Tuples (primary, secondary) used for strict ranking
    if sort_by == 'depth':
        # Rank by (max_depth, xp)
        query = """
            SELECT COUNT(*) + 1
            FROM users
            WHERE (max_depth, xp) > (SELECT max_depth, xp FROM users WHERE uid = %s)
        """
    elif sort_by == 'biocoin':
        # Rank by (biocoin, xp)
        query = """
            SELECT COUNT(*) + 1
            FROM users
            WHERE (biocoin, xp) > (SELECT biocoin, xp FROM users WHERE uid = %s)
        """
    else:
        # Default: Rank by (xp, level)
        query = """
            SELECT COUNT(*) + 1
            FROM users
            WHERE (xp, level) > (SELECT xp, level FROM users WHERE uid = %s)
        """

    with db_cursor() as cur:
        if not cur: return 0
        cur.execute(query, (uid,))
        res = cur.fetchone()
        return res[0] if res else 0

def add_diary_entry(uid, text):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("INSERT INTO diary (uid, entry) VALUES (%s, %s)", (uid, text))

def get_diary_entries(uid, limit=5, offset=0):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT entry, created_at FROM diary WHERE uid = %s ORDER BY created_at DESC LIMIT %s OFFSET %s", (uid, limit, offset))
        return cur.fetchall()

def get_diary_count(uid):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("SELECT COUNT(*) FROM diary WHERE uid = %s", (uid,))
        return cur.fetchone()[0]

def get_referrals_stats(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT username, first_name, level, ref_profit_xp, ref_profit_coins FROM users WHERE referrer = %s ORDER BY ref_profit_xp DESC LIMIT 20", (str(uid),))
        return cur.fetchall()

def get_user_achievements(uid):
    with db_cursor() as cur:
        if not cur: return []
        cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
        return [row[0] for row in cur.fetchall()]

def get_random_villain(level=1, cursor=None):
    # Find random villain in range [level-15, level] to add variety
    min_lvl = max(1, level - 15)
    max_lvl = level
    query = "SELECT * FROM villains WHERE level BETWEEN %s AND %s ORDER BY RANDOM() LIMIT 1"
    fallback_query = "SELECT * FROM villains ORDER BY ABS(level - %s) ASC, RANDOM() LIMIT 1"

    if cursor:
        cursor.execute(query, (min_lvl, max_lvl))
        res = cursor.fetchone()
        if not res:
            cursor.execute(fallback_query, (level,))
            res = cursor.fetchone()
        return res

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute(query, (min_lvl, max_lvl))
        res = cur.fetchone()
        if not res:
            cur.execute(fallback_query, (level,))
            res = cursor.fetchone()
        return res

def update_raid_enemy(uid, enemy_id, hp):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, hp, uid))

def clear_raid_enemy(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))

def get_raid_session_enemy(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT current_enemy_id, current_enemy_hp, is_elite FROM raid_sessions WHERE uid = %s", (uid,))
        return cur.fetchone()

def get_villain_by_id(vid, cursor=None):
    if cursor:
        cursor.execute("SELECT * FROM villains WHERE id = %s", (vid,))
        return cursor.fetchone()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM villains WHERE id = %s", (vid,))
        return cur.fetchone()

def admin_add_content(c_type, text):
    with db_cursor() as cur:
        if not cur: return
        if c_type == 'raid':
            cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
        else:
            cur.execute("INSERT INTO content (type, path, text) VALUES (%s, 'general', %s)", (c_type, text))

def populate_content():
    with db_session() as conn:
        with conn.cursor() as cur:
            for level, items in CONTENT_DATA.items():
                for item in items:
                    cur.execute("""
                        INSERT INTO content (type, path, level, text)
                        SELECT %s, %s, %s, %s
                        WHERE NOT EXISTS (SELECT 1 FROM content WHERE text = %s)
                    """, (item['type'], item['path'], level, item['text'], item['text']))

def get_archived_protocols_paginated(uid, limit=5, offset=0):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("""
            SELECT c.text, c.type, c.level
            FROM content c
            JOIN unlocked_protocols up ON c.id = up.protocol_id
            WHERE up.uid = %s
            ORDER BY c.id DESC
            LIMIT %s OFFSET %s
        """, (uid, limit, offset))
        return cur.fetchall()

def get_archived_protocols_count(uid):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("""
            SELECT COUNT(*)
            FROM content c
            JOIN unlocked_protocols up ON c.id = up.protocol_id
            WHERE up.uid = %s
        """, (uid,))
        return cur.fetchone()[0]

def admin_get_users_dossier(limit=50):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return "❌ No DB Connection"
        cur.execute("""
            SELECT uid, first_name, username, level, xp, path,
                   streak, max_depth, last_active
            FROM users
            ORDER BY last_active DESC
            LIMIT %s
        """, (limit,))
        users = cur.fetchall()
        report = "📂 <b>DOSSIER: USERS LIST</b>\n\n"
        for u in users:
            active = u['last_active'].strftime('%d.%m') if u['last_active'] else "N/A"
            report += (f"👤 <b>{u['first_name']}</b> (@{u['username']})\n"
                       f"   Lvl {u['level']} | {u['xp']} XP | {u['path'].upper()}\n"
                       f"   Streak: {u['streak']} | Depth: {u['max_depth']}m | Last: {active}\n"
                       f"   🆔 <code>{u['uid']}</code>\n\n")
        return report

def admin_add_riddle_to_db(text):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
        return True

def admin_add_signal_to_db(text, level=1, c_type='protocol', path='general'):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)",
                    (c_type, path, text, level))
        return True

def set_user_admin(uid, status):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET is_admin = %s WHERE uid = %s", (status, uid))

def get_admins():
    with db_cursor() as cur:
        if not cur: return []
        cur.execute("SELECT uid FROM users WHERE is_admin = TRUE")
        return [row[0] for row in cur.fetchall()]

def is_user_admin(uid):
    # Check env var first
    try:
        env_admin = os.environ.get('ADMIN_ID')
        if env_admin and str(uid) == str(env_admin):
             return True
    except: pass

    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT is_admin FROM users WHERE uid = %s", (uid,))
        res = cur.fetchone()
        return res[0] if res else False

def get_random_raid_advice(level, cursor=None):
    query = "SELECT text FROM content WHERE type='advice' AND path='raid_general' AND level=%s ORDER BY RANDOM() LIMIT 1"

    if cursor:
        cursor.execute(query, (level,))
        res = cursor.fetchone()
        if not res: return None
        # Handle both RealDictCursor and normal cursor
        if isinstance(res, dict): return res['text']
        return res[0]

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute(query, (level,))
        res = cur.fetchone()
        return res['text'] if res else None

def get_random_user_for_hack(exclude_uid):
    with db_cursor() as cur:
        if not cur: return None
        cur.execute("SELECT uid FROM users WHERE uid != %s ORDER BY RANDOM() LIMIT 1", (exclude_uid,))
        res = cur.fetchone()
        return res[0] if res else None

def get_death_loot_at_depth(depth):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM death_loot WHERE depth = %s ORDER BY created_at DESC LIMIT 1", (depth,))
        return cur.fetchone()

def claim_death_loot(loot_id):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("DELETE FROM death_loot WHERE id = %s", (loot_id,))
        return cur.rowcount > 0

def log_death_loot(depth, amount, owner_name):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("INSERT INTO death_loot (depth, amount, created_at, original_owner_name) VALUES (%s, %s, %s, %s)",
                    (depth, amount, int(time.time()), owner_name))

def get_shadow_broker_status(uid):
    u = get_user(uid)
    if not u: return 0
    return u.get('shadow_broker_expiry', 0)

def set_shadow_broker(uid, expiry):
    update_user(uid, shadow_broker_expiry=expiry)

def log_action(uid, action, details):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO logs (uid, action, details) VALUES (%s, %s, %s)", (uid, action, details))

def save_raid_grave(depth, loot_json, owner_name, message=""):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO raid_graves (depth, loot_json, owner_name, message, created_at) VALUES (%s, %s, %s, %s, %s)",
                        (depth, loot_json, owner_name, message, int(time.time())))

def get_random_grave(depth):
    # Find a grave within reasonable depth range (+- 50m)
    min_d = max(0, depth - 50)
    max_d = depth + 50
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM raid_graves WHERE depth BETWEEN %s AND %s ORDER BY RANDOM() LIMIT 1", (min_d, max_d))
        return cur.fetchone()

def delete_grave(grave_id):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM raid_graves WHERE id = %s", (grave_id,))
            return cur.rowcount > 0

def save_history(uid, data_json):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO history (uid, archived_data_json) VALUES (%s, %s)", (uid, data_json))

def hard_reset_user(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            # Clear Inventory
            cur.execute("DELETE FROM inventory WHERE uid = %s", (uid,))
            # Clear Equipment
            cur.execute("DELETE FROM user_equipment WHERE uid = %s", (uid,))
            # Clear Raid Sessions
            cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
            # Reset User Stats
            cur.execute("""
                UPDATE users SET
                xp = 0, level = 1, biocoin = 0,
                streak = 1, max_depth = 0,
                raid_count_today = 0,
                path = 'general',
                encrypted_cache_unlock_time = 0,
                encrypted_cache_type = NULL,
                shadow_broker_expiry = 0,
                anomaly_buff_expiry = 0,
                anomaly_buff_type = NULL
                WHERE uid = %s
            """, (uid,))

def set_onboarding_stage(uid, stage):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET onboarding_stage = %s WHERE uid = %s", (stage, uid))

def quarantine_user(uid, duration_hours=24):
    hard_reset_user(uid)
    end_time = int(time.time() + (duration_hours * 3600))
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET
                is_quarantined = TRUE,
                quarantine_end_time = %s,
                onboarding_stage = 0,
                onboarding_start_time = 0
                WHERE uid = %s
            """, (end_time, uid))

def add_quiz_history(uid, question_id):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET quiz_history = quiz_history || %s || ',' WHERE uid = %s", (str(question_id), uid))

def delete_user_fully(uid):
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # Delete from all tables where uid is a foreign key or primary key
                tables = [
                    "inventory", "user_equipment", "raid_sessions", "bot_states",
                    "achievements", "diary", "history", "logs", "user_knowledge",
                    "unlocked_protocols", "users"
                ]
                for table in tables:
                    cur.execute(f"DELETE FROM {table} WHERE uid = %s", (uid,))
        return True
    except Exception as e:
        print(f"Delete Error: {e}")
        return False

# --- PVP HELPERS ---

def add_pvp_log(attacker_uid, target_uid, stolen_coins, success, is_revenged=False, is_anonymous=False):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pvp_logs (attacker_uid, target_uid, stolen_coins, success, timestamp, is_revenged, is_anonymous)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (attacker_uid, target_uid, stolen_coins, success, int(time.time()), is_revenged, is_anonymous))
            return cur.fetchone()[0]

def get_pvp_history(uid, limit=10):
    """
    Returns list of attacks AGAINST this user (Vendetta list).
    Only returns successful attacks that haven't been revenged yet?
    Or all attacks?
    Prompt: "VENDETTA — List of those who hacked you in last 24h."
    """
    cutoff = int(time.time()) - 86400 # 24h
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("""
            SELECT p.*, u.username, u.first_name, u.level
            FROM pvp_logs p
            JOIN users u ON p.attacker_uid = u.uid
            WHERE p.target_uid = %s
              AND p.timestamp > %s
              AND p.success = TRUE
              AND p.is_revenged = FALSE
              AND p.is_anonymous = FALSE
            ORDER BY p.timestamp DESC
            LIMIT %s
        """, (uid, cutoff, limit))
        return cur.fetchall()

def check_pvp_cooldown(attacker_uid, target_uid, duration=43200):
    """
    Checks if attacker has attacked target within duration (12h).
    Returns True if ON COOLDOWN (cannot attack).
    """
    cutoff = int(time.time()) - duration
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("""
            SELECT 1 FROM pvp_logs
            WHERE attacker_uid = %s AND target_uid = %s AND timestamp > %s
        """, (attacker_uid, target_uid, cutoff))
        return cur.fetchone() is not None

def get_revenge_target(log_id):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM pvp_logs WHERE id = %s", (log_id,))
        return cur.fetchone()

def mark_log_revenged(log_id):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE pvp_logs SET is_revenged = TRUE WHERE id = %s", (log_id,))
