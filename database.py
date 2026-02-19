import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import time
import logging
from datetime import datetime
import re
from config import ITEMS_INFO, INVENTORY_LIMIT
from content_presets import CONTENT_DATA

DATABASE_URL = os.environ.get('DATABASE_URL')

@contextmanager
def db_session():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        yield conn
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"/// DB ERROR: {e}")
    finally:
        if conn: conn.close()

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

def init_db():
    with db_session() as conn:
        if not conn: return
        with conn.cursor() as cur:
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
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS raid_count_today INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_raid_date DATE DEFAULT CURRENT_DATE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS biocoin INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE")
            except: pass

            cur.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    uid BIGINT, item_id TEXT, quantity INTEGER DEFAULT 1, durability INTEGER DEFAULT 100,
                    PRIMARY KEY(uid, item_id)
                );
            ''')
            try:
                cur.execute("SELECT 1 FROM pg_constraint WHERE conname = 'inventory_uid_item_id_key'")
                if not cur.fetchone():
                    cur.execute("""
                        CREATE TEMP TABLE IF NOT EXISTS inv_backup AS
                        SELECT uid, item_id, SUM(quantity) as q, MAX(durability) as d
                        FROM inventory GROUP BY uid, item_id
                    """)
                    cur.execute("TRUNCATE inventory CASCADE")
                    cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) SELECT uid, item_id, q, d FROM inv_backup")
                    cur.execute("DROP TABLE inv_backup")
                    cur.execute("ALTER TABLE inventory ADD CONSTRAINT inventory_uid_item_id_key UNIQUE (uid, item_id)")
                    conn.commit()
            except: conn.rollback()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id SERIAL PRIMARY KEY, type TEXT, path TEXT DEFAULT 'general', level INTEGER DEFAULT 1, text TEXT UNIQUE
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS raid_content (
                    id SERIAL PRIMARY KEY, text TEXT, type TEXT DEFAULT 'neutral', val INTEGER DEFAULT 0
                );
            ''')

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
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS buffer_items TEXT DEFAULT ''")
                cur.execute("ALTER TABLE raid_sessions ADD COLUMN IF NOT EXISTS is_elite BOOLEAN DEFAULT FALSE")
            except: conn.rollback()

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
    populate_villains()
    populate_content()

def populate_villains():
    VILLAINS_DATA = [
        {"name": "🦠 Цифровой Паразит", "level": 1, "hp": 30, "atk": 5, "def": 0, "xp": 10, "coin": 5, "desc": "Мелкий вредоносный скрипт."},
        {"name": "👻 Призрак Глитча", "level": 1, "hp": 40, "atk": 7, "def": 2, "xp": 15, "coin": 8, "desc": "Искаженная тень удаленного файла."},
        {"name": "🚁 Дрон-Страж", "level": 2, "hp": 60, "atk": 10, "def": 5, "xp": 30, "coin": 15, "desc": "Автоматическая система защиты."},
        {"name": "💣 Логическая Бомба", "level": 2, "hp": 50, "atk": 15, "def": 0, "xp": 35, "coin": 20, "desc": "Нестабильный код."},
        {"name": "⛏ Крипто-Майнер", "level": 3, "hp": 80, "atk": 12, "def": 5, "xp": 40, "coin": 50, "desc": "Вор ресурсов."},
        {"name": "🐉 Спам-Гидра", "level": 3, "hp": 100, "atk": 15, "def": 5, "xp": 50, "coin": 25, "desc": "Отрежь один баннер - всплывут два."},
        {"name": "❌ Фатальный Сбой", "level": 4, "hp": 120, "atk": 18, "def": 10, "xp": 80, "coin": 40, "desc": "Воплощение ошибки."},
        {"name": "🗡 Ассасин Даркнета", "level": 4, "hp": 110, "atk": 22, "def": 5, "xp": 90, "coin": 60, "desc": "Скрытный убийца."},
        {"name": "🧠 ИИ-Доминатор", "level": 5, "hp": 180, "atk": 25, "def": 15, "xp": 200, "coin": 100, "desc": "Мятежный ИИ."},
        {"name": "⬛ Стиратель", "level": 6, "hp": 250, "atk": 30, "def": 20, "xp": 300, "coin": 200, "desc": "Сущность пустоты."},
        # NEW VILLAINS (REBALANCED)
        {"name": "👻 Нейро-Призрак", "level": 7, "hp": 350, "atk": 35, "def": 25, "xp": 400, "coin": 250, "desc": "Фантом нейросети."},
        {"name": "💀 Кибер-Лич", "level": 8, "hp": 450, "atk": 40, "def": 30, "xp": 500, "coin": 350, "desc": "Восставший из удаленных."},
        {"name": "🏗 Архитектор Кошмаров", "level": 9, "hp": 600, "atk": 45, "def": 40, "xp": 700, "coin": 500, "desc": "Строит лабиринты страха."},
        {"name": "🍽 Пожиратель Кода", "level": 10, "hp": 800, "atk": 50, "def": 50, "xp": 1000, "coin": 800, "desc": "Уничтожитель миров."},
        {"name": "🛡 Страж Ядра", "level": 12, "hp": 1200, "atk": 65, "def": 60, "xp": 1500, "coin": 1200, "desc": "Охраняет самое ценное."},
        {"name": "⚛️ Омни-Синтез", "level": 15, "hp": 2000, "atk": 80, "def": 80, "xp": 2500, "coin": 2000, "desc": "Слияние всех ошибок."},
        {"name": "🤖 Бог Машины", "level": 20, "hp": 3500, "atk": 110, "def": 120, "xp": 5000, "coin": 4000, "desc": "Deus Ex Machina."},
        {"name": "🌌 Пустотный Странник", "level": 25, "hp": 5000, "atk": 140, "def": 150, "xp": 8000, "coin": 6000, "desc": "Пришел из-за грани."},
        {"name": "🌀 Энтропия", "level": 30, "hp": 8000, "atk": 180, "def": 200, "xp": 10000, "coin": 10000, "desc": "Хаос воплоти."}
    ]

    OLD_NAMES = tuple([
        "Цифровой Паразит", "Призрак Глитча", "Дрон-Страж", "Логическая Бомба",
        "Крипто-Майнер", "Спам-Гидра", "Фатальный Сбой", "Ассасин Даркнета",
        "ИИ-Доминатор", "Стиратель", "Нейро-Призрак", "Кибер-Лич",
        "Архитектор Кошмаров", "Пожиратель Кода", "Страж Ядра", "Омни-Синтез",
        "Бог Машины", "Пустотный Странник", "Энтропия",
        "Data Leech", "Glitch Phantom"
    ])

    with db_session() as conn:
        with conn.cursor() as cur:
            # Delete old versions to force update with icons
            try:
                cur.execute("DELETE FROM villains WHERE name IN %s", (OLD_NAMES,))
            except Exception as e:
                print(f"Cleanup Error: {e}")

            for v in VILLAINS_DATA:
                cur.execute("""
                    INSERT INTO villains (name, level, hp, atk, def, xp_reward, coin_reward, description)
                    VALUES (%(name)s, %(level)s, %(hp)s, %(atk)s, %(def)s, %(xp)s, %(coin)s, %(desc)s)
                    ON CONFLICT (name) DO UPDATE SET level = EXCLUDED.level, hp = EXCLUDED.hp, atk = EXCLUDED.atk, def = EXCLUDED.def, xp_reward = EXCLUDED.xp_reward, coin_reward = EXCLUDED.coin_reward, description = EXCLUDED.description
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

def reset_daily_stats(uid):
    with db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET raid_count_today = 0, last_raid_date = CURRENT_DATE WHERE uid = %s", (uid,))

def add_item(uid, item_id, qty=1):
    with db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
        if cur.fetchone()[0] >= INVENTORY_LIMIT: return False
        durability = ITEMS_INFO.get(item_id, {}).get('durability', 100)
        cur.execute("""
            INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, %s, %s)
            ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + %s
        """, (uid, item_id, qty, durability, qty))
        return True

def get_inventory(uid, cursor=None):
    query = "SELECT * FROM inventory WHERE quantity > 0 AND uid = %s"
    if cursor:
        cursor.execute(query, (uid,))
        return cursor.fetchall()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute(query, (uid,))
        return cur.fetchall()

def use_item(uid, item_id, qty=1, cursor=None):
    if cursor:
        cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE uid = %s AND item_id = %s RETURNING quantity", (qty, uid, item_id))
        res = cursor.fetchone()

        quantity = None
        if res:
            if isinstance(res, dict): quantity = res['quantity']
            else: quantity = res[0]

        if quantity is not None and quantity <= 0:
            cursor.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
        return True

    with db_cursor() as cur:
        if not cur: return False
        cur.execute("UPDATE inventory SET quantity = quantity - %s WHERE uid = %s AND item_id = %s RETURNING quantity", (qty, uid, item_id))
        res = cur.fetchone()
        if res and res[0] <= 0:
            cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
        return True

def decrease_durability(uid, item_id, amount=1):
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

def get_inventory_size(uid):
    with db_cursor() as cur:
        if not cur: return 0
        cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
        return cur.fetchone()[0]

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

def get_item_count(uid, item_id, cursor=None):
    query = "SELECT quantity FROM inventory WHERE uid=%s AND item_id=%s"
    if cursor:
        cursor.execute(query, (uid, item_id))
        res = cursor.fetchone()
        if not res: return 0
        if isinstance(res, dict): return res['quantity']
        return res[0]

    with db_cursor() as cur:
        if not cur: return 0
        cur.execute(query, (uid, item_id))
        res = cur.fetchone()
        return res[0] if res else 0

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

def get_leaderboard(limit=10):
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        cur.execute("SELECT first_name, xp, level, max_depth FROM users ORDER BY max_depth DESC, xp DESC LIMIT %s", (limit,))
        return cur.fetchall()

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
    # Find closest level match, then random among ties
    query = "SELECT * FROM villains ORDER BY ABS(level - %s) ASC, RANDOM() LIMIT 1"

    if cursor:
        cursor.execute(query, (level,))
        return cursor.fetchone()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute(query, (level,))
        return cur.fetchone()

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
        env_admin = os.environ.get('ADMIN_ID', '5178416366')
        if str(uid) == str(env_admin):
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
