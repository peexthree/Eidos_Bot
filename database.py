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
import html
import traceback
import threading
from config import ITEMS_INFO, INVENTORY_LIMIT
from content_presets import CONTENT_DATA, VILLAINS_DATA, OLD_VILLAINS_NAMES

DATABASE_URL = os.environ.get('DATABASE_URL')

# Global Connection Pool
_formatted_db_url = None
_pool_lock = threading.Lock()

# --- SCHEMA DEFINITIONS ---
TABLE_SCHEMAS = {
    'players': {
        'uid': ('BIGINT', None), # PK, handled by CREATE TABLE usually
        'username': ('TEXT', None),
        'first_name': ('TEXT', None),
        'path': ('TEXT', "'general'"),
        'xp': ('BIGINT', '0'),
        'biocoin': ('BIGINT', '0'),
        'level': ('INTEGER', '1'),
        'streak': ('INTEGER', '1'),
        'last_active': ('TIMESTAMPTZ', 'CURRENT_TIMESTAMP'),
        'cryo': ('BIGINT', '0'),
        'accel': ('INTEGER', '0'),
        'decoder': ('INTEGER', '0'),
        'accel_exp': ('BIGINT', '0'),
        'referrer': ('TEXT', None),
        'ref_profit_xp': ('BIGINT', '0'),
        'ref_profit_coins': ('BIGINT', '0'),
        'generated_ref_xp': ('BIGINT', '0'),
        'generated_ref_coins': ('BIGINT', '0'),
        'last_protocol_time': ('BIGINT', '0'),
        'last_signal_time': ('BIGINT', '0'),
        'notified': ('BOOLEAN', 'TRUE'),
        'max_depth': ('INTEGER', '0'),
        'ref_count': ('INTEGER', '0'),
        'know_count': ('INTEGER', '0'),
        'total_spent': ('BIGINT', '0'),
        'raid_count_today': ('INTEGER', '0'),
        'last_raid_date': ('TIMESTAMPTZ', 'CURRENT_TIMESTAMP'),
        'is_admin': ('BOOLEAN', 'FALSE'),
        'encrypted_cache_unlock_time': ('BIGINT', '0'),
        'encrypted_cache_type': ('TEXT', 'NULL'),
        'shadow_broker_expiry': ('BIGINT', '0'),
        'anomaly_buff_expiry': ('BIGINT', '0'),
        'anomaly_buff_type': ('TEXT', 'NULL'),
        'proxy_expiry': ('BIGINT', '0'),
        'is_active': ('BOOLEAN', 'TRUE'),
        'kills': ('INTEGER', '0'),
        'raids_done': ('INTEGER', '0'),
        'perfect_raids': ('INTEGER', '0'),
        'quiz_wins': ('INTEGER', '0'),
        'messages': ('INTEGER', '0'),
        'likes': ('INTEGER', '0'),
        'purchases': ('INTEGER', '0'),
        'found_zero': ('BOOLEAN', 'FALSE'),
        'is_glitched': ('BOOLEAN', 'FALSE'),
        'found_devtrace': ('BOOLEAN', 'FALSE'),
        'night_visits': ('INTEGER', '0'),
        'clicks': ('INTEGER', '0'),
        'onboarding_stage': ('INTEGER', '0'),
        'onboarding_start_time': ('BIGINT', '0'),
        'is_quarantined': ('BOOLEAN', 'FALSE'),
        'quarantine_end_time': ('BIGINT', '0'),
        'quiz_history': ('TEXT', "''"),
        'deck_level': ('INTEGER', '1'),
        'deck_config': ('TEXT', "'{\"1\": \"soft_brute_v1\", \"2\": null, \"3\": null}'"),
        'shield_until': ('BIGINT', '0'),
        'last_hack_target': ('BIGINT', '0'),
        'active_hardware': ('TEXT', "'{}'")
    },
    'raid_sessions': {
        'uid': ('BIGINT', None), # PK
        'depth': ('BIGINT', '0'), # Fixed to BIGINT
        'signal': ('BIGINT', '100'), # Fixed to BIGINT
        'start_time': ('BIGINT', '0'),
        'buffer_xp': ('BIGINT', '0'), # Fixed to BIGINT
        'buffer_coins': ('BIGINT', '0'), # Fixed to BIGINT
        'current_enemy_id': ('BIGINT', 'NULL'), # Fixed to BIGINT
        'current_enemy_hp': ('BIGINT', 'NULL'), # Fixed to BIGINT
        'kills': ('INTEGER', '0'),
        'riddles_solved': ('INTEGER', '0'),
        'current_riddle_answer': ('TEXT', 'NULL'),
        'next_event_type': ('TEXT', 'NULL'),
        'current_event_type': ('TEXT', 'NULL'),
        'event_streak': ('INTEGER', '0'),
        'buffer_items': ('TEXT', "''"),
        'is_elite': ('BOOLEAN', 'FALSE'),
        'mechanic_data': ('JSONB', "'{}'")
    },
    'inventory': {
        'id': ('SERIAL', None), # PK
        'uid': ('BIGINT', None),
        'item_id': ('TEXT', None),
        'quantity': ('INTEGER', '1'),
        'durability': ('INTEGER', '100'),
        'custom_data': ('TEXT', 'NULL')
    },
    'user_equipment': {
        'uid': ('BIGINT', None),
        'slot': ('TEXT', None),
        'item_id': ('TEXT', None),
        'durability': ('INTEGER', '10'),
        'custom_data': ('TEXT', 'NULL')
    },
    'bot_states': {
        'uid': ('BIGINT', None), # PK
        'state': ('TEXT', None),
        'data': ('TEXT', None)
    },
    'user_shadow_metrics': {
        'uid': ('BIGINT', None), # PK
        'total_coins_earned': ('BIGINT', '0'),
        'total_coins_spent': ('BIGINT', '0'),
        'hoarded_consumables': ('INTEGER', '0'),
        'shop_visits_without_purchase': ('INTEGER', '0'),
        'safe_zone_raids': ('INTEGER', '0'),
        'high_risk_raids': ('INTEGER', '0'),
        'escapes_at_full_hp': ('INTEGER', '0'),
        'items_lost_on_death': ('INTEGER', '0'),
        'consecutive_deaths': ('INTEGER', '0'),
        'entries_with_critical_hp': ('INTEGER', '0'),
        'hack_random_uses': ('INTEGER', '0'),
        'night_sessions_count': ('INTEGER', '0'),
        'marathon_sessions_count': ('INTEGER', '0'),
        'total_sessions': ('INTEGER', '0'),
        'days_active': ('INTEGER', '0'),
        'glitch_victim_answers': ('INTEGER', '0'),
        'glitch_greed_answers': ('INTEGER', '0'),
        'glitch_stoic_answers': ('INTEGER', '0'),
        'glitch_chaos_answers': ('INTEGER', '0'),
        'referrals_invited': ('INTEGER', '0'),
        'syndicate_profit_collected': ('BIGINT', '0'),
        'fast_sync_clicks': ('INTEGER', '0'),
        'rapid_menu_clicks': ('INTEGER', '0'),
        'last_hard_glitch_time': ('INTEGER', '0'),
        'max_streak_achieved': ('INTEGER', '0'),
        'streaks_broken_count': ('INTEGER', '0')
    },
    'user_dossiers': {
        'uid': ('BIGINT', None), # PK
        'dossier_text': ('TEXT', None),
        'generated_at': ('TIMESTAMPTZ', 'CURRENT_TIMESTAMP')
    },
    'villains': {
        'id': ('SERIAL', None), # PK
        'name': ('TEXT', None), # Unique
        'level': ('INTEGER', '1'),
        'hp': ('INTEGER', '10'),
        'atk': ('INTEGER', '1'),
        'def': ('INTEGER', '0'),
        'xp_reward': ('INTEGER', '0'),
        'coin_reward': ('INTEGER', '0'),
        'description': ('TEXT', "''"),
        'image': ('TEXT', 'NULL')
    },
    'achievements': {
        'uid': ('BIGINT', None),
        'ach_id': ('TEXT', None),
        'created_at': ('TIMESTAMP', 'CURRENT_TIMESTAMP')
    },
    'content': {
        'id': ('SERIAL', None),
        'type': ('TEXT', None),
        'path': ('TEXT', "'general'"),
        'level': ('INTEGER', '1'),
        'text': ('TEXT', None) # Unique
    },
    'raid_content': {
        'id': ('SERIAL', None),
        'text': ('TEXT', None),
        'type': ('TEXT', "'neutral'"),
        'val': ('INTEGER', '0')
    },
    'user_knowledge': {
        'uid': ('BIGINT', None),
        'content_id': ('INTEGER', None)
    },
    'unlocked_protocols': {
        'uid': ('BIGINT', None),
        'protocol_id': ('INTEGER', None)
    },
    'diary': {
        'id': ('SERIAL', None),
        'uid': ('BIGINT', None),
        'entry': ('TEXT', None),
        'created_at': ('TIMESTAMP', 'CURRENT_TIMESTAMP')
    },
    'death_loot': {
        'id': ('SERIAL', None),
        'depth': ('INTEGER', '0'),
        'amount': ('INTEGER', '0'),
        'created_at': ('BIGINT', '0'),
        'original_owner_name': ('TEXT', 'NULL')
    },
    'raid_graves': {
        'id': ('SERIAL', None),
        'depth': ('INTEGER', '0'),
        'loot_json': ('TEXT', "'{}'"),
        'owner_name': ('TEXT', 'NULL'),
        'message': ('TEXT', "''"),
        'created_at': ('BIGINT', '0')
    },
    'logs': {
        'id': ('SERIAL', None),
        'uid': ('BIGINT', None),
        'action': ('TEXT', None),
        'details': ('TEXT', None),
        'timestamp': ('TIMESTAMP', 'CURRENT_TIMESTAMP')
    },
    'pvp_logs': {
        'id': ('SERIAL', None),
        'attacker_uid': ('BIGINT', None),
        'target_uid': ('BIGINT', None),
        'stolen_coins': ('INTEGER', '0'),
        'success': ('BOOLEAN', 'FALSE'),
        'timestamp': ('BIGINT', '0'),
        'is_revenged': ('BOOLEAN', 'FALSE'),
        'is_anonymous': ('BOOLEAN', 'FALSE')
    },
    'history': {
        'id': ('SERIAL', None),
        'uid': ('BIGINT', None),
        'archived_data_json': ('TEXT', None),
        'reset_date': ('TIMESTAMP', 'CURRENT_TIMESTAMP')
    }
}

def init_pool():
    global _formatted_db_url
    if not _formatted_db_url:
        with _pool_lock:
            if not _formatted_db_url:
                try:
                    import urllib.parse
                    raw_url = DATABASE_URL
                    if raw_url:
                        parsed = urllib.parse.urlparse(raw_url)
                        if "supabase" in parsed.netloc and parsed.port == 5432:
                            new_netloc = parsed.netloc.replace(":5432", ":6543")
                            parsed = parsed._replace(netloc=new_netloc)

                        query_params = urllib.parse.parse_qs(parsed.query)
                        if 'pgbouncer' in query_params:
                            del query_params['pgbouncer']
                        parsed = parsed._replace(query=urllib.parse.urlencode(query_params, doseq=True))
                        _formatted_db_url = urllib.parse.urlunparse(parsed)

                    print("/// DB URL FORMATTED (SUPABASE TRANSACTIONS ENABLED)")
                except Exception as e:
                    print(f"/// DB URL INIT ERROR: {e}")

def reset_pool():
    pass

@contextmanager
def db_session():
    if not _formatted_db_url:
        init_pool()

    conn = None

    try:
        conn = psycopg2.connect(_formatted_db_url, options='-c lock_timeout=5000 -c statement_timeout=5000')
        yield conn
        conn.commit()
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"/// DB CONNECTION ERROR: {e}")
        print(traceback.format_exc())
        raise e
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"/// DB ERROR: {e}")
        print(traceback.format_exc())
        raise e
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


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






def fix_user_equipment_schema():
    print("/// DEBUG: Checking user_equipment constraints...")
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # Check for PK
                cur.execute("""
                    SELECT conname FROM pg_constraint
                    JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                    WHERE pg_class.relname = 'user_equipment' AND pg_constraint.contype = 'p';
                """)
                if cur.fetchone():
                    return # Exists

                print("/// FIX: Adding PRIMARY KEY to user_equipment(uid, slot)...")

                # Remove duplicates (arbitrary choice if duplicates exist)
                # We can use CTID to keep one.
                cur.execute("""
                    DELETE FROM user_equipment a USING user_equipment b
                    WHERE a.ctid < b.ctid AND a.uid = b.uid AND a.slot = b.slot;
                """)

                # Add constraint
                cur.execute("ALTER TABLE user_equipment ADD PRIMARY KEY (uid, slot);")
                conn.commit()
    except Exception as e:
        print(f"/// FIX USER_EQUIPMENT ERROR: {e}")

def fix_data_consistency():
    print("/// DEBUG: Checking for NULL values in critical columns...")
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # Players table fixes
                # List of columns that must be 0 if NULL
                cols_to_fix = [
                    'accel_exp', 'last_protocol_time', 'last_signal_time',
                    'anomaly_buff_expiry', 'shadow_broker_expiry',
                    'encrypted_cache_unlock_time', 'onboarding_start_time',
                    'quarantine_end_time'
                ]

                for col in cols_to_fix:
                    try:
                        cur.execute(f"UPDATE players SET {col} = 0 WHERE {col} IS NULL")
                    except Exception as e:
                        print(f"/// FIX WARN: Could not update {col}: {e}")

                # Ensure core stats are never NULL
                try:
                    cur.execute("UPDATE players SET xp = 0 WHERE xp IS NULL")
                    cur.execute("UPDATE players SET biocoin = 0 WHERE biocoin IS NULL")
                    cur.execute("UPDATE players SET level = 1 WHERE level IS NULL")
                except Exception as e:
                    print(f"/// FIX WARN: Could not update core stats: {e}")

                conn.commit()
                print("/// FIX: Data consistency check complete.")
    except Exception as e:
        print(f"/// FIX DATA CONSISTENCY ERROR: {e}")

def fix_missing_defaults():
    print("/// DEBUG: Fixing missing DEFAULT values and NULL timestamps...")
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # 1. Diary
                try:
                    cur.execute("UPDATE diary SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                    cur.execute("ALTER TABLE diary ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP")
                except Exception as e:
                    print(f"/// FIX ERROR (diary): {e}")

                # 2. Achievements
                try:
                    cur.execute("UPDATE achievements SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                    cur.execute("ALTER TABLE achievements ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP")
                except Exception as e:
                    print(f"/// FIX ERROR (achievements): {e}")

                # 3. Logs
                try:
                    cur.execute("UPDATE logs SET timestamp = CURRENT_TIMESTAMP WHERE timestamp IS NULL")
                    cur.execute("ALTER TABLE logs ALTER COLUMN timestamp SET DEFAULT CURRENT_TIMESTAMP")
                except Exception as e:
                    print(f"/// FIX ERROR (logs): {e}")

                # 4. History
                try:
                    cur.execute("UPDATE history SET reset_date = CURRENT_TIMESTAMP WHERE reset_date IS NULL")
                    cur.execute("ALTER TABLE history ALTER COLUMN reset_date SET DEFAULT CURRENT_TIMESTAMP")
                except Exception as e:
                    print(f"/// FIX ERROR (history): {e}")

                conn.commit()
                print("/// FIX: Missing defaults fixed.")
    except Exception as e:
        print(f"/// FIX MISSING DEFAULTS ERROR: {e}")

def fix_pvp_logs_schema():
    print("/// DEBUG: Fixing pvp_logs schema (ID and Sequence)...")
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # 1. Delete rows with NULL ID (Bad Data)
                cur.execute("DELETE FROM pvp_logs WHERE id IS NULL")
                deleted = cur.rowcount
                if deleted > 0:
                    print(f"/// FIX: Deleted {deleted} corrupt PVP logs.")

                # 2. Ensure Sequence exists and is attached
                # Check if 'id' has a default value
                cur.execute("SELECT column_default FROM information_schema.columns WHERE table_name='pvp_logs' AND column_name='id'")
                res = cur.fetchone()
                if res and res[0] is None:
                    print("/// FIX: pvp_logs 'id' missing sequence. Repairing...")
                    try:
                        cur.execute("CREATE SEQUENCE IF NOT EXISTS pvp_logs_id_seq")
                        # Sync sequence
                        cur.execute("SELECT MAX(id) FROM pvp_logs")
                        max_id = cur.fetchone()[0]
                        if max_id is None: max_id = 0
                        cur.execute(f"SELECT setval('pvp_logs_id_seq', {max_id + 1}, false)")
                        # Set default
                        cur.execute("ALTER TABLE pvp_logs ALTER COLUMN id SET DEFAULT nextval('pvp_logs_id_seq')")
                        # Add PK if missing
                        cur.execute("""
                            SELECT conname FROM pg_constraint
                            JOIN pg_class ON pg_constraint.conrelid = pg_class.oid
                            WHERE pg_class.relname = 'pvp_logs' AND pg_constraint.contype = 'p';
                        """)
                        if not cur.fetchone():
                            cur.execute("ALTER TABLE pvp_logs ADD PRIMARY KEY (id)")
                        conn.commit()
                        print("/// FIX: pvp_logs schema repaired.")
                    except Exception as e:
                        print(f"/// FIX ERROR (pvp_logs schema): {e}")
                        conn.rollback()

    except Exception as e:
        print(f"/// FIX PVP LOGS ERROR: {e}")


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

def get_user(uid, cursor=None):
    def _execute_logic(cur, uid):
        cur.execute("SELECT * FROM players WHERE uid = %s", (uid,))
        res = cur.fetchone()
        if res:
            if hasattr(res, 'keys'):
                return dict(res)
            else:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, res))
        return None

    if cursor:
        return _execute_logic(cursor, uid)
    else:
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            if not cur: return None
            return _execute_logic(cur, uid)

def add_user(uid, username, first_name, referrer=None):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO players (uid, username, first_name, referrer, last_active) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) ON CONFLICT (uid) DO NOTHING", (uid, username, first_name, referrer))
            if referrer and str(referrer) != str(uid):
                cur.execute("UPDATE players SET ref_count = ref_count + 1 WHERE uid = %s", (referrer,))

def update_user(uid, cursor=None, **kwargs):
    if not kwargs: return

    # [MODULE 2] Track specific changes dynamically if needed,
    # but currently most things are tracked explicitly via update_shadow_metric.

    set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
    values = list(kwargs.values()) + [uid]

    if cursor:
        cursor.execute(f"UPDATE players SET {set_clause} WHERE uid = %s", values)
        return

    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE players SET {set_clause} WHERE uid = %s", values)

def set_user_active(uid, status):
    update_user(uid, is_active=status)

def add_xp_to_user(uid, amount, cursor=None):
    def _execute_logic(cur):
        profit = 0
        ref_id = None
        actual_amount = amount

        if amount > 0:
            cur.execute("SELECT referrer FROM players WHERE uid = %s", (uid,))
            res = cur.fetchone()

            if res and res[0]:
                ref_id = res[0]
                profit = int(amount * 0.1)
                actual_amount = amount - profit

        cur.execute("UPDATE players SET xp = xp + %s WHERE uid = %s", (actual_amount, uid))

        if profit > 0 and ref_id:
            cur.execute("UPDATE players SET xp = xp + %s, ref_profit_xp = ref_profit_xp + %s WHERE uid = %s", (profit, profit, ref_id))
            cur.execute("UPDATE players SET generated_ref_xp = generated_ref_xp + %s WHERE uid = %s", (profit, uid))

    if cursor:
        _execute_logic(cursor)
    else:
        with db_session() as conn:
            with conn.cursor() as cur:
                _execute_logic(cur)

def increment_user_stat(uid, stat, amount=1, cursor=None):
    # Safe allow-list for stats
    ALLOWED_STATS = ['kills', 'raids_done', 'perfect_raids', 'quiz_wins', 'messages', 'likes', 'purchases', 'night_visits', 'clicks']
    if stat not in ALLOWED_STATS: return False

    def _execute_logic(cur, uid, amount):
        cur.execute(f"UPDATE players SET {stat} = {stat} + %s WHERE uid = %s", (amount, uid))
        return cur.rowcount > 0

    if cursor:
        return _execute_logic(cursor, uid, amount)
    else:
        with db_session() as conn:
            with conn.cursor() as cur:
                return _execute_logic(cur, uid, amount)

def set_user_stat(uid, stat, value):
    # Safe allow-list for boolean flags
    ALLOWED_STATS = ['found_zero', 'is_glitched', 'found_devtrace']
    if stat not in ALLOWED_STATS: return False

    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE players SET {stat} = %s WHERE uid = %s", (value, uid))
            return cur.rowcount > 0

def reset_daily_stats(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE players SET raid_count_today = 0, last_raid_date = CURRENT_TIMESTAMP WHERE uid = %s", (uid,))

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
            count = (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0
            if int(count or 0) >= int(INVENTORY_LIMIT or 20):
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
                    INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                    VALUES (%s, %s, 1, %s, NULL)
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
                    INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                    VALUES (%s, %s, %s, 100, NULL)
                """, (uid, item_id, qty))

        return True

    if cursor:
        return _add_logic(cursor)

    with db_cursor() as cur:
        if not cur: return False
        return _add_logic(cur)

def get_inventory(uid, cursor=None):
    # Returns list including 'id' for handling individual items
    query = "SELECT id, uid, item_id, quantity, durability, custom_data FROM inventory WHERE quantity > 0 AND uid = %s ORDER BY item_id ASC"

    def _execute_logic(cur, uid):
        cur.execute(query, (uid,))
        res = cur.fetchall()
        if res and not hasattr(res[0], 'keys'):
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in res]
        return [dict(row) for row in res] if res else []

    if cursor:
        return _execute_logic(cursor, uid)
    else:
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            if not cur: return []
            return _execute_logic(cur, uid)

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
            cur.execute("SELECT item_id, durability, quantity, custom_data FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
            res = cur.fetchone()
            if not res: return False
            item_id, durability, qty, custom_data = res

            # 2. Check if slot is occupied
            cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()

            if old:
                # Unequip old item -> Move to Inventory
                old_item_id, old_dur, old_custom = old
                if old_dur is None: old_dur = 10
                cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, %s, %s)", (uid, old_item_id, old_dur, old_custom))

            # 3. Equip new item
            # upsert into user_equipment
            cur.execute("""
                INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, durability = EXCLUDED.durability, custom_data = EXCLUDED.custom_data
            """, (uid, slot, item_id, durability, custom_data))

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

            cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if not old: return False

            item_id, durability, custom_data = old
            if durability is None: durability = 10

            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))

            # Move to inventory directly to preserve custom_data
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, %s, %s)", (uid, item_id, durability, custom_data))

            return True
    except Exception as e:
        print(f"Unequip Error: {e}")
        return False

def get_equipped_items(uid, cursor=None):
    if cursor:
        cursor.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cursor.fetchall()}

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cur.fetchall()}

def get_equipped_item_in_slot(uid, slot, cursor=None):
    if cursor:
        cursor.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cursor.fetchone()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
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
            cur.execute("SELECT custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cd_res = cur.fetchone()
            custom_data = cd_res[0] if cd_res else None
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, 0, %s)", (uid, item_id, custom_data))
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
        if not res:
            return 0
        if isinstance(res, dict):
            val = res.get('total')
        else:
            val = res[0]
        return int(val) if val is not None else 0

    if cursor:
        cursor.execute(query, (uid, item_id))
        return _extract(cursor.fetchone())

    with db_cursor() as cur:
        if not cur:
            return 0
        cur.execute(query, (uid, item_id))
        return _extract(cur.fetchone())

def check_achievement_exists(uid, ach_id):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
        return cur.fetchone() is not None

def grant_achievement(uid, ach_id, bonus_xp):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO achievements (uid, ach_id, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) ON CONFLICT DO NOTHING", (uid, ach_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE players SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
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
            cur.execute("UPDATE players SET know_count = know_count + 1 WHERE uid = %s", (uid,))

def get_leaderboard(limit=10, sort_by='xp'):
    order_clause = "xp DESC, level DESC, uid ASC"
    if sort_by == 'depth':
        order_clause = "max_depth DESC, xp DESC, uid ASC"
    elif sort_by == 'biocoin':
        order_clause = "biocoin DESC, xp DESC, uid ASC"
    elif sort_by == 'spent':
        order_clause = "COALESCE(total_spent, 0) DESC, xp DESC, uid ASC"

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        # Using format string for ORDER BY is necessary as it cannot be parameterized directly.
        # sort_by is controlled by code logic, not user input directly (enum-like), so it's safe-ish.
        # Join with user_equipment to fetch eidos_shard custom_data
        query = f"""
            SELECT p.uid, p.first_name, p.username, COALESCE(p.xp, 0) as xp, COALESCE(p.level, 1) as level,
                   COALESCE(p.max_depth, 0) as max_depth, COALESCE(p.biocoin, 0) as biocoin, COALESCE(p.total_spent, 0) as total_spent, p.path,
                   ue.custom_data as eidos_custom_data
            FROM players p
            LEFT JOIN user_equipment ue ON p.uid = ue.uid AND ue.slot = 'eidos_shard'
            ORDER BY {order_clause.replace('uid', 'p.uid').replace('xp', 'p.xp').replace('level', 'p.level').replace('max_depth', 'p.max_depth').replace('biocoin', 'p.biocoin').replace('total_spent', 'p.total_spent')} LIMIT %s
        """
        cur.execute(query, (limit,))
        return cur.fetchall()

def get_user_rank(uid, sort_by='xp'):
    # Determine the comparison logic based on sort_by
    # Tuples (primary, secondary) used for strict ranking
    if sort_by == 'depth':
        # Rank by (max_depth, xp)
        query = """
            SELECT COUNT(*) + 1
            FROM players
            WHERE (max_depth, xp) > (SELECT max_depth, xp FROM players WHERE uid = %s)
        """
    elif sort_by == 'biocoin':
        # Rank by (biocoin, xp)
        query = """
            SELECT COUNT(*) + 1
            FROM players
            WHERE (biocoin, xp) > (SELECT biocoin, xp FROM players WHERE uid = %s)
        """
    elif sort_by == 'spent':
        query = """
            SELECT COUNT(*) + 1
            FROM players
            WHERE (total_spent, xp) > (SELECT total_spent, xp FROM players WHERE uid = %s)
        """
    else:
        # Default: Rank by (xp, level)
        query = """
            SELECT COUNT(*) + 1
            FROM players
            WHERE (xp, level) > (SELECT xp, level FROM players WHERE uid = %s)
        """

    with db_cursor() as cur:
        if not cur: return 0
        cur.execute(query, (uid,))
        res = cur.fetchone()
        return (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0

def add_diary_entry(uid, text):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("INSERT INTO diary (uid, entry, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP)", (uid, text))

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
        cur.execute("SELECT username, first_name, level, generated_ref_xp, generated_ref_coins FROM players WHERE referrer = %s ORDER BY generated_ref_xp DESC LIMIT 20", (str(uid),))
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
        if not cur:
            return None
        cur.execute("SELECT * FROM villains WHERE id = %s", (vid,))
        return cur.fetchone()

def admin_add_content(c_type, text):
    with db_cursor() as cur:
        if not cur: return
        if c_type == 'raid':
            cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
        else:
            cur.execute("INSERT INTO content (type, path, text) VALUES (%s, 'general', %s)", (c_type, text))

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
            FROM players
            ORDER BY last_active DESC
            LIMIT %s
        """, (limit,))
        users = cur.fetchall()
        report = "📂 <b>DOSSIER: USERS LIST</b>\n\n"
        for u in users:
            active = u['last_active'].strftime('%d.%m') if u['last_active'] else "N/A"
            safe_name = html.escape(u['first_name'] or "Unknown")
            path_str = str(u.get('path') or 'general').upper()
            report += (f"👤 <b>{safe_name}</b> (@{u['username']})\n"
                       f"   Lvl {u['level']} | {u['xp']} XP | {path_str}\n"
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
            cur.execute("UPDATE players SET is_admin = %s WHERE uid = %s", (status, uid))

def get_admins():
    with db_cursor() as cur:
        if not cur: return []
        cur.execute("SELECT uid FROM players WHERE is_admin = TRUE")
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
        cur.execute("SELECT is_admin FROM players WHERE uid = %s", (uid,))
        res = cur.fetchone()
        return (res[0] if isinstance(res, tuple) else res.get("is_admin")) if res else False

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
        cur.execute("SELECT uid FROM players WHERE uid != %s ORDER BY RANDOM() LIMIT 1", (exclude_uid,))
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

def log_death_loot(depth, amount, owner_name, cursor=None):
    if cursor:
        cursor.execute("INSERT INTO death_loot (depth, amount, created_at, original_owner_name) VALUES (%s, %s, %s, %s)",
                    (depth, amount, int(time.time()), owner_name))
    else:
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

def log_action(uid, action, details, cursor=None):
    def _execute_logic(cur, uid, action, details):
        cur.execute("INSERT INTO logs (uid, action, details, timestamp) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)", (uid, action, details))

    if cursor:
        return _execute_logic(cursor, uid, action, details)
    else:
        with db_session() as conn:
            with conn.cursor() as cur:
                return _execute_logic(cur, uid, action, details)

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
            cur.execute("INSERT INTO history (uid, archived_data_json, reset_date) VALUES (%s, %s, CURRENT_TIMESTAMP)", (uid, data_json))

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
                UPDATE players SET
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
            cur.execute("UPDATE players SET onboarding_stage = %s WHERE uid = %s", (stage, uid))

def quarantine_user(uid, duration_hours=24):
    hard_reset_user(uid)
    end_time = int(time.time() + (duration_hours * 3600))
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE players SET
                is_quarantined = TRUE,
                quarantine_end_time = %s,
                onboarding_stage = 0,
                onboarding_start_time = 0
                WHERE uid = %s
            """, (end_time, uid))

def add_quiz_history(uid, question_id):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE players SET quiz_history = quiz_history || %s || ',' WHERE uid = %s", (str(question_id), uid))

def delete_user_fully(uid):
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                # Delete from all tables where uid is a foreign key or primary key
                tables = [
                    "inventory", "user_equipment", "raid_sessions", "bot_states",
                    "achievements", "diary", "history", "logs", "user_knowledge",
                    "unlocked_protocols", "players"
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

def get_pvp_history(uid, limit=20):
    """
    Returns list of attacks AGAINST this user (Vendetta list).
    Returns ALL non-anonymous attacks in last 24h (Revenged, Failed, Success).
    """
    cutoff = int(time.time()) - 86400 # 24h
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("""
            SELECT p.*, u.username, u.first_name, u.level
            FROM pvp_logs p
            JOIN players u ON p.attacker_uid = u.uid
            WHERE p.target_uid = %s
              AND p.timestamp > %s
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

def update_shadow_metric(uid, metric_name, amount=1):
    """Updates a specific metric in user_shadow_metrics. Amount can be negative or positive."""
    if metric_name not in TABLE_SCHEMAS.get('user_shadow_metrics', {}):
        print(f"/// ERROR: Invalid shadow metric '{metric_name}'")
        return

    with db_session() as conn:
        with conn.cursor() as cur:
            # Ensure the row exists
            cur.execute("INSERT INTO user_shadow_metrics (uid) VALUES (%s) ON CONFLICT DO NOTHING", (uid,))
            # Update the metric
            cur.execute(f"UPDATE user_shadow_metrics SET {metric_name} = {metric_name} + %s WHERE uid = %s", (amount, uid))
            conn.commit()

def set_shadow_metric(uid, metric_name, value):
    """Sets a specific metric in user_shadow_metrics to an absolute value."""
    if metric_name not in TABLE_SCHEMAS.get('user_shadow_metrics', {}):
        print(f"/// ERROR: Invalid shadow metric '{metric_name}'")
        return

    with db_session() as conn:
        with conn.cursor() as cur:
            # Ensure the row exists
            cur.execute("INSERT INTO user_shadow_metrics (uid) VALUES (%s) ON CONFLICT DO NOTHING", (uid,))
            # Set the metric
            cur.execute(f"UPDATE user_shadow_metrics SET {metric_name} = %s WHERE uid = %s", (value, uid))
            conn.commit()

def get_user_shadow_metrics(uid):
    """Returns the user shadow metrics dictionary."""
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT * FROM user_shadow_metrics WHERE uid = %s", (uid,))
        res = cur.fetchone()
        return dict(res) if res else {}

def fast_populate_villains():
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM villains")
                res = cur.fetchone()
                count = (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0
                if count > 0:
                    print(f"/// DEBUG: Skipping populate_villains (found {count} entries)")
                    return
                populate_villains()
    except Exception as e:
        print(f"/// ERR fast_populate_villains: {e}")

def fast_populate_content():
    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM content")
                res = cur.fetchone()
                count = (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0
                if count > 0:
                    print(f"/// DEBUG: Skipping populate_content (found {count} entries)")
                    return
                populate_content()
    except Exception as e:
        print(f"/// ERR fast_populate_content: {e}")


def admin_clear_user_raid(uid):
    with db_cursor() as cur:
        if cur:
            cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
            return True
    return False

def admin_clear_all_glitches():
    import time
    with db_cursor() as cur:
        if cur:
            cur.execute("DELETE FROM bot_states WHERE state = 'glitch_question'")
            count = cur.rowcount
            cur.execute("UPDATE user_shadow_metrics SET last_hard_glitch_time = %s", (int(time.time()),))
            return count
    return 0
