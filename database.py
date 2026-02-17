import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from config import DATABASE_URL, ITEMS_INFO, INVENTORY_LIMIT

# =============================================================
# 🔌 ПОДКЛЮЧЕНИЕ
# =============================================================

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"/// CRITICAL DB ERROR: {e}")
        return None

@contextmanager
def db_session():
    """Context manager for database connections. Ensures connection is closed and handles commits/rollbacks."""
    conn = get_db_connection()
    if conn is None:
        yield None
        return
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"/// DB SESSION ERROR: {e}")
        raise
    finally:
        conn.close()

@contextmanager
def db_cursor(cursor_factory=None):
    """Context manager for database cursors. Automatically handles connection and transaction."""
    with db_session() as conn:
        if conn is None:
            yield None
            return
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur

def get_item_count(uid, item_id):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("SELECT quantity FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
        res = cur.fetchone()
        return res[0] if res else 0

# =============================================================
# 🛠 ИНИЦИАЛИЗАЦИЯ (СТРУКТУРА МИРА)
# =============================================================

def init_db():
    with db_session() as conn:
        if not conn: return
        with conn.cursor() as cur:
            # 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
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
                    ref_count INTEGER DEFAULT 0, know_count INTEGER DEFAULT 0, total_spent INTEGER DEFAULT 0
                );
            ''')

            # 2. ИНВЕНТАРЬ [RPG]
            cur.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    uid BIGINT, item_id TEXT, quantity INTEGER DEFAULT 1, durability INTEGER DEFAULT 100,
                    PRIMARY KEY(uid, item_id)
                );
            ''')

            # --- FIX: INVENTORY CONSTRAINT ---
            try:
                cur.execute("SELECT 1 FROM pg_constraint WHERE conname = 'inventory_uid_item_id_key'")
                if not cur.fetchone():
                    print("/// FIXING INVENTORY SCHEMA...")
                    # Aggregate duplicates
                    cur.execute("""
                        CREATE TEMP TABLE IF NOT EXISTS inv_backup AS
                        SELECT uid, item_id, SUM(quantity) as q, MAX(durability) as d
                        FROM inventory GROUP BY uid, item_id
                    """)
                    cur.execute("TRUNCATE inventory CASCADE")
                    cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) SELECT uid, item_id, q, d FROM inv_backup")
                    cur.execute("DROP TABLE inv_backup")
                    # Add unique constraint
                    cur.execute("ALTER TABLE inventory ADD CONSTRAINT inventory_uid_item_id_key UNIQUE (uid, item_id)")
                    conn.commit()
                    print("/// INVENTORY SCHEMA FIXED.")
            except Exception as e:
                print(f"/// SCHEMA FIX ERROR: {e}")
                conn.rollback()

            # 3. ЭКИПИРОВКА [RPG]
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_equipment (
                    uid BIGINT, slot TEXT, item_id TEXT, PRIMARY KEY(uid, slot)
                );
            ''')

            # 4. РЕЙДЫ (СЕССИИ)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raid_sessions (
                    uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100,
                    buffer_xp INTEGER DEFAULT 0, buffer_coins INTEGER DEFAULT 0, start_time BIGINT
                );
            ''')

            # 5. ОСТАЛЬНЫЕ ТАБЛИЦЫ
            cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
            cur.execute('''CREATE TABLE IF NOT EXISTS user_knowledge (uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, content_id));''')
            cur.execute('''CREATE TABLE IF NOT EXISTS diary (id SERIAL PRIMARY KEY, uid BIGINT, entry TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
            cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
            cur.execute('''CREATE TABLE IF NOT EXISTS raid_content (id SERIAL PRIMARY KEY, text TEXT, type TEXT, val INTEGER DEFAULT 0);''')
            cur.execute('''CREATE TABLE IF NOT EXISTS raid_hints (id SERIAL PRIMARY KEY, text TEXT);''')

            # [NEW] Таблица разблокированных протоколов для Архива
            cur.execute('''CREATE TABLE IF NOT EXISTS unlocked_protocols (uid BIGINT, protocol_id INTEGER, PRIMARY KEY(uid, protocol_id));''')

            # Автоматическое добавление недостающих колонок
            alter_queries = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS biocoin INTEGER DEFAULT 0;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS ref_profit_coins INTEGER DEFAULT 0;",
                "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;",
                "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS durability INTEGER DEFAULT 100;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_raid_date DATE DEFAULT CURRENT_DATE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS raid_entry_count INTEGER DEFAULT 0;"
            ]
            for q in alter_queries:
                try:
                    cur.execute(q)
                    conn.commit()
                except:
                    conn.rollback()
    populate_content()

# =============================================================
# 👤 ПОЛЬЗОВАТЕЛИ
# =============================================================

def get_user(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
        return cur.fetchone()

def update_user(uid, **kwargs):
    with db_cursor() as cur:
        if not cur: return
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [uid]
        cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", values)

def add_xp_to_user(uid, amount):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (amount, uid))

def add_referral_profit(uid, xp_amount, coin_amount):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("UPDATE users SET ref_profit_xp = ref_profit_xp + %s, ref_profit_coins = ref_profit_coins + %s WHERE uid = %s", (xp_amount, coin_amount, uid))

# =============================================================
# 🎒 ИНВЕНТАРЬ И ЭКИПИРОВКА
# =============================================================

def get_inventory_size(uid):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("SELECT COUNT(*) FROM inventory WHERE uid=%s", (uid,))
        return cur.fetchone()[0]

def add_item(uid, item_id, qty=1):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT quantity FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
        exists = cur.fetchone()
        if not exists:
            cur.execute("SELECT COUNT(*) FROM inventory WHERE uid=%s", (uid,))
            if cur.fetchone()[0] >= INVENTORY_LIMIT: return False

        durability = ITEMS_INFO.get(item_id, {}).get('durability', 100)
        cur.execute("""
            INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, %s, %s)
            ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + %s
        """, (uid, item_id, qty, durability, qty))
        return True

def get_inventory(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT * FROM inventory WHERE quantity > 0 AND uid = %s", (uid,))
        return cur.fetchall()

def use_item(uid, item_id, qty=1):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("UPDATE inventory SET quantity = quantity - %s WHERE uid = %s AND item_id = %s RETURNING quantity", (qty, uid, item_id))
        res = cur.fetchone()
        if res and res[0] <= 0:
            cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
        return True

def decrease_durability(uid, item_id, amount=1):
    """Снижает прочность. Реальная логика: если 0 - ломается 1 шт из стака."""
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT durability, quantity FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
        res = cur.fetchone()
        if not res: return False

        new_dur = res[0] - amount
        if new_dur <= 0:
            if res[1] > 1:
                base_dur = ITEMS_INFO.get(item_id, {}).get('durability', 100)
                cur.execute("UPDATE inventory SET quantity = quantity - 1, durability = %s WHERE uid=%s AND item_id=%s", (base_dur, uid, item_id))
            else:
                cur.execute("DELETE FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
            return False
        else:
            cur.execute("UPDATE inventory SET durability = %s WHERE uid=%s AND item_id=%s", (new_dur, uid, item_id))
            return True

def equip_item(uid, item_id, slot):
    try:
        with db_cursor() as cur:
            if not cur: return False
            cur.execute("SELECT item_id FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if old:
                cur.execute("""INSERT INTO inventory (uid, item_id, quantity) VALUES (%s, %s, 1) 
                               ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + 1""", (uid, old[0]))
            cur.execute("""INSERT INTO user_equipment (uid, slot, item_id) VALUES (%s, %s, %s)
                           ON CONFLICT (uid, slot) DO UPDATE SET item_id = %s""", (uid, slot, item_id, item_id))
            cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE uid=%s AND item_id=%s", (uid, item_id))
            cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s AND quantity <= 0", (uid, item_id))
            return True
    except: return False

def unequip_item(uid, slot):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT item_id FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        old = cur.fetchone()
        if not old: return False
        cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        cur.execute("""INSERT INTO inventory (uid, item_id, quantity) VALUES (%s, %s, 1)
                       ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + 1""", (uid, old[0]))
        return True

def get_equipped_items(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT slot, item_id FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cur.fetchall()}

def break_equipment_randomly(uid):
    with db_cursor() as cur:
        if not cur: return None
        cur.execute("SELECT slot, item_id FROM user_equipment WHERE uid=%s ORDER BY RANDOM() LIMIT 1", (uid,))
        item = cur.fetchone()
        if item:
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, item[0]))
            return item[1]
        return None

# =============================================================
# 🏆 АЧИВКИ, ЗНАНИЯ, АРХИВ
# =============================================================

def check_achievement_exists(uid, ach_id):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
        return cur.fetchone() is not None

def grant_achievement(uid, ach_id, bonus_xp):
    """Реальная запись достижения"""
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, ach_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
            return True
        return False

def get_archived_protocols(uid):
    """Реальное чтение из unlocked_protocols"""
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

def get_leaderboard(limit=10):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT first_name, xp, level, max_depth FROM users ORDER BY max_depth DESC, xp DESC LIMIT %s", (limit,))
        return cur.fetchall()

def add_diary_entry(uid, text):
    with db_cursor() as cur:
        if not cur: return
        cur.execute("INSERT INTO diary (uid, entry) VALUES (%s, %s)", (uid, text))

def get_diary_entries(uid, limit=5):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT entry, created_at FROM diary WHERE uid = %s ORDER BY created_at DESC LIMIT %s", (uid, limit))
        return cur.fetchall()

def get_referrals_stats(uid):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT username, first_name, level, ref_profit_xp, ref_profit_coins FROM users WHERE referrer = %s ORDER BY ref_profit_xp DESC LIMIT 20", (str(uid),))
        return cur.fetchall()

def admin_exec_query(query):
    with db_session() as conn:
        if not conn: return "❌ No Connection"
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    return str(cur.fetchall())[:3500]
                else:
                    return f"✅ DONE. Rows: {cur.rowcount}"
        except Exception as e: return f"❌ ERROR: {e}"

def admin_add_content(c_type, text):
    with db_cursor() as cur:
        if not cur: return
        if c_type == 'raid':
            cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
        else:
            cur.execute("INSERT INTO content (type, path, text) VALUES (%s, 'general', %s)", (c_type, text))

def populate_content():
    """Заполнение базы контентом для уровней 5+"""
    from content_presets import CONTENT_DATA
    try:
        with db_cursor() as cur:
            if not cur: return
            for lvl, items in CONTENT_DATA.items():
                for item in items:
                    cur.execute("SELECT 1 FROM content WHERE text = %s", (item['text'],))
                    if not cur.fetchone():
                        cur.execute("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)",
                                    (item['type'], item['path'], item['text'], lvl))
                        print(f"/// ADDED CONTENT LVL {lvl}: {item['text'][:20]}...")
    except Exception as e:
        print(f"/// CONTENT POPULATION ERROR: {e}")

def get_user_achievements(uid):
    with db_cursor() as cur:
        if not cur: return []
        cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
        return [row[0] for row in cur.fetchall()]

# =============================================================
# 🛠 АДМИН-ИНСТРУМЕНТЫ (НОВЫЕ)
# =============================================================

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
        # Пытаемся распарсить ответ для проверки, но сохраняем как есть
        # Логика бота сама разберет (Ответ: ...)
        cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
        return True

def admin_add_signal_to_db(text, level=1, c_type='protocol', path='general'):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)",
                    (c_type, path, text, level))
        return True
