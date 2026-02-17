import psycopg2
from psycopg2.extras import RealDictCursor
import os
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

def get_item_count(uid, item_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT quantity FROM inventory WHERE uid=%s AND item_id=%s", (uid, item_id))
        res = cur.fetchone()
        return res[0] if res else 0
# =============================================================
# 🛠 ИНИЦИАЛИЗАЦИЯ (СТРУКТУРА МИРА)
# =============================================================

def init_db():
    conn = get_db_connection()
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
            "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS durability INTEGER DEFAULT 100;"
        ]
        for q in alter_queries:
            try:
                cur.execute(q)
                conn.commit()
            except:
                conn.rollback()
        # --- МИГРАЦИЯ (ЛЕЧЕНИЕ СТАРЫХ БАЗ) ---
        patch_cols = [
            ("users", "biocoin", "INTEGER DEFAULT 0"),
            ("users", "ref_profit_xp", "INTEGER DEFAULT 0"),
            ("users", "ref_profit_coins", "INTEGER DEFAULT 0"),
            ("users", "max_depth", "INTEGER DEFAULT 0"),
            ("inventory", "quantity", "INTEGER DEFAULT 1"),
            ("inventory", "durability", "INTEGER DEFAULT 100"),
            ("raid_sessions", "buffer_coins", "INTEGER DEFAULT 0")
        ]
        
        for table, col, dtype in patch_cols:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {dtype};")
            except:
                conn.rollback()
            else:
                conn.commit()

        # --- SEEDING (ЗАПОЛНЕНИЕ, ЕСЛИ ПУСТО) ---
        cur.execute("SELECT COUNT(*) FROM content")
        if cur.fetchone()[0] == 0:
            base_content = [
                ('protocol', 'general', '<b>СИСТЕМА:</b> Мир — это код.', 1),
                ('signal', 'general', 'Слушай тишину.', 1)
            ]
            cur.executemany("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)", base_content)
            
        conn.commit()
    conn.close()
    print("/// DATABASE ENGINE: SYNCHRONIZED (v7.5 FIXED).")

# =============================================================
# 👤 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# =============================================================

def get_user(uid):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
            return cur.fetchone()
    finally: conn.close()

def create_user(uid, username, first_name, referrer=None):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING", (uid, username, first_name, referrer))
            if referrer:
                cur.execute("UPDATE users SET ref_count = ref_count + 1 WHERE uid = %s", (referrer,))
            conn.commit()
    finally: conn.close()

def update_user(uid, **kwargs):
    if not kwargs: return
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
            cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", list(kwargs.values()) + [uid])
            conn.commit()
    finally: conn.close()

def add_xp_to_user(uid, amount):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (amount, uid))
            conn.commit()
    finally: conn.close()

def add_referral_profit(uid, xp_amount, coin_amount):
    """Обновляет статистику профита реферера"""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET ref_profit_xp = ref_profit_xp + %s, ref_profit_coins = ref_profit_coins + %s WHERE uid = %s", (xp_amount, coin_amount, uid))
            conn.commit()
    finally: conn.close()

# =============================================================
# 🎒 ИНВЕНТАРЬ И ЭКИПИРОВКА
# =============================================================

def get_inventory_size(uid):
    conn = get_db_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM inventory WHERE uid=%s", (uid,))
            return cur.fetchone()[0]
    finally: conn.close()

def add_item(uid, item_id, qty=1):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
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
            conn.commit()
            return True
    finally: conn.close()

def get_inventory(uid):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM inventory WHERE quantity > 0 AND uid = %s", (uid,))
            return cur.fetchall()
    finally: conn.close()

def use_item(uid, item_id, qty=1):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE inventory SET quantity = quantity - %s WHERE uid = %s AND item_id = %s RETURNING quantity", (qty, uid, item_id))
            res = cur.fetchone()
            if res and res[0] <= 0:
                cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
            conn.commit()
            return True
    finally: conn.close()

def decrease_durability(uid, item_id, amount=1):
    """Снижает прочность. Реальная логика: если 0 - ломается 1 шт из стака."""
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
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
                conn.commit()
                return False 
            else:
                cur.execute("UPDATE inventory SET durability = %s WHERE uid=%s AND item_id=%s", (new_dur, uid, item_id))
                conn.commit()
                return True
    finally: conn.close()

def equip_item(uid, item_id, slot):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if old:
                cur.execute("""INSERT INTO inventory (uid, item_id, quantity) VALUES (%s, %s, 1) 
                               ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + 1""", (uid, old[0]))
            cur.execute("""INSERT INTO user_equipment (uid, slot, item_id) VALUES (%s, %s, %s)
                           ON CONFLICT (uid, slot) DO UPDATE SET item_id = %s""", (uid, slot, item_id, item_id))
            cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE uid=%s AND item_id=%s", (uid, item_id))
            cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s AND quantity <= 0", (uid, item_id))
            conn.commit()
            return True
    except: return False
    finally: conn.close()

def unequip_item(uid, slot):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if not old: return False
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cur.execute("""INSERT INTO inventory (uid, item_id, quantity) VALUES (%s, %s, 1) 
                           ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + 1""", (uid, old[0]))
            conn.commit()
            return True
    finally: conn.close()

def get_equipped_items(uid):
    conn = get_db_connection()
    if not conn: return {}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT slot, item_id FROM user_equipment WHERE uid=%s", (uid,))
            return {row['slot']: row['item_id'] for row in cur.fetchall()}
    finally: conn.close()

# =============================================================
# 🏆 АЧИВКИ, ЗНАНИЯ, АРХИВ
# =============================================================

def check_achievement_exists(uid, ach_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
            return cur.fetchone() is not None
    finally: conn.close()

def grant_achievement(uid, ach_id, bonus_xp):
    """Реальная запись достижения"""
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, ach_id))
            if cur.rowcount > 0:
                cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
                conn.commit()
                return True
            return False
    finally: conn.close()

def get_archived_protocols(uid):
    """Реальное чтение из unlocked_protocols"""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.text FROM content c
                JOIN unlocked_protocols up ON c.id = up.protocol_id
                WHERE up.uid = %s
            """, (uid,))
            return cur.fetchall()
    finally: conn.close()

def save_knowledge(uid, content_id):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
            cur.execute("INSERT INTO unlocked_protocols (uid, protocol_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
            conn.commit()
    finally: conn.close()

# Остальные функции (get_leaderboard, diary, admin) оставлены без изменений.

def get_leaderboard(limit=10):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT first_name, xp, level FROM users ORDER BY xp DESC LIMIT %s", (limit,))
            return cur.fetchall()
    finally: conn.close()

def add_diary_entry(uid, text):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO diary (uid, entry) VALUES (%s, %s)", (uid, text))
            conn.commit()
    finally: conn.close()

def get_diary_entries(uid, limit=5):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT entry, created_at FROM diary WHERE uid = %s ORDER BY created_at DESC LIMIT %s", (uid, limit))
            return cur.fetchall()
    finally: conn.close()

def get_referrals_stats(uid):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT username, first_name, level, ref_profit_xp, ref_profit_coins FROM users WHERE referrer = %s ORDER BY ref_profit_xp DESC LIMIT 20", (str(uid),))
            return cur.fetchall()
    finally: conn.close()

def admin_exec_query(query):
    conn = get_db_connection()
    if not conn: return "❌ No Connection"
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            if query.strip().upper().startswith("SELECT"):
                return str(cur.fetchall())[:3500]
            else:
                conn.commit()
                return f"✅ DONE. Rows: {cur.rowcount}"
    except Exception as e: return f"❌ ERROR: {e}"
    finally: conn.close()

def admin_add_content(c_type, text):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            if c_type == 'raid':
                cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, 'neutral', 0)", (text,))
            else:
                cur.execute("INSERT INTO content (type, path, text) VALUES (%s, 'general', %s)", (c_type, text))
            conn.commit()
    finally: conn.close()
