import psycopg2
from psycopg2.extras import RealDictCursor
import os
from config import DATABASE_URL

# =============================================================
# 🔌 ПОДКЛЮЧЕНИЕ
# =============================================================

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"/// CRITICAL DB ERROR: {e}")
        return None

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
                username TEXT,
                first_name TEXT,
                path TEXT DEFAULT 'general',
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak INTEGER DEFAULT 1,
                last_active DATE DEFAULT CURRENT_DATE,
                cryo INTEGER DEFAULT 0,
                accel INTEGER DEFAULT 0,
                decoder INTEGER DEFAULT 0,
                accel_exp BIGINT DEFAULT 0,
                referrer TEXT,
                last_protocol_time BIGINT DEFAULT 0,
                last_signal_time BIGINT DEFAULT 0,
                notified BOOLEAN DEFAULT TRUE,
                max_depth INTEGER DEFAULT 0,
                ref_count INTEGER DEFAULT 0,
                know_count INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0
            );
        ''')
        
        # 2. ДОСТИЖЕНИЯ
        cur.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                uid BIGINT, 
                ach_id TEXT, 
                date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(uid, ach_id)
            );
        ''')
        
        # 3. ЗНАНИЯ (ИСТОРИЯ)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_knowledge (
                uid BIGINT, 
                content_id INTEGER, 
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(uid, content_id)
            );
        ''')
        
        # 4. ДНЕВНИК
        cur.execute('''
            CREATE TABLE IF NOT EXISTS diary (
                id SERIAL PRIMARY KEY, 
                uid BIGINT, 
                entry TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 5. КОНТЕНТ (СИНХРОНЫ)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id SERIAL PRIMARY KEY,
                type TEXT, -- protocol, signal
                path TEXT, -- money, mind, tech, general
                text TEXT,
                level INTEGER DEFAULT 1
            );
        ''')
        
        # 6. РЕЙДЫ (СЕССИИ)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS raid_sessions (
                uid BIGINT PRIMARY KEY,
                depth INTEGER DEFAULT 0,
                signal INTEGER DEFAULT 100,
                buffer_xp INTEGER DEFAULT 0,
                start_time BIGINT
            );
        ''')

        # 7. РЕЙДЫ (КОНТЕНТ СОБЫТИЙ)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS raid_content (
                id SERIAL PRIMARY KEY,
                text TEXT,
                type TEXT, -- trap, loot, heal, neutral
                val INTEGER DEFAULT 0
            );
        ''')
        
        # 8. РЕЙДЫ (ПОДСКАЗКИ КОМПАСА)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS raid_hints (
                id SERIAL PRIMARY KEY,
                text TEXT
            );
        ''')
        
        # --- МИГРАЦИИ И ПАТЧИ ---
        # Добавляем колонки, если база старая
        patch_cols = [
            ("users", "ref_count", "INTEGER DEFAULT 0"),
            ("users", "know_count", "INTEGER DEFAULT 0"), 
            ("users", "total_spent", "INTEGER DEFAULT 0"), 
            ("users", "max_depth", "INTEGER DEFAULT 0"),
            ("users", "referrer_id", "BIGINT") # Для надежности
        ]
        
        for table, col, col_type in patch_cols:
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};")
            except Exception as e:
                print(f"Warning: Migration failed for {col}: {e}")
                conn.rollback() 
            else:
                conn.commit()

        # --- ЗАЛИВКА БАЗОВОГО КОНТЕНТА (ЕСЛИ ПУСТО) ---
        # Это чтобы бот не выдавал None при первых тестах
        
        # Проверка контента
        cur.execute("SELECT COUNT(*) FROM content")
        if cur.fetchone()[0] == 0:
            print("/// DB: SEEDING BASIC CONTENT...")
            base_content = [
                ('protocol', 'general', '<b>СИСТЕМА:</b> Мир — это набор договоренностей. Тот, кто создает новые договоренности — управляет миром.', 1),
                ('signal', 'general', 'Не бойся выглядеть глупо. Бойся выглядеть одинаково.', 1),
                ('protocol', 'money', '<b>ДЕНЬГИ:</b> Деньги любят тишину, но ненавидят застой. Деньги должны течь.', 1)
            ]
            cur.executemany("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)", base_content)
        
        # Проверка рейд-контента
        cur.execute("SELECT COUNT(*) FROM raid_content")
        if cur.fetchone()[0] == 0:
             print("/// DB: SEEDING RAID CONTENT...")
             raid_ev = [
                 ('Ты наткнулся на старый сервер. В нем еще есть данные.', 'loot', 50),
                 ('Ловушка! Электромагнитный импульс.', 'trap', 20),
                 ('Тишина. Ты слышишь только гул проводов.', 'neutral', 0),
                 ('Источник питания. Сигнал восстановлен.', 'heal', 20)
             ]
             cur.executemany("INSERT INTO raid_content (text, type, val) VALUES (%s, %s, %s)", raid_ev)

        # Проверка подсказок
        cur.execute("SELECT COUNT(*) FROM raid_hints")
        if cur.fetchone()[0] == 0:
             print("/// DB: SEEDING HINTS...")
             hints = [('Чувствую вибрацию...',), ('Впереди чисто.',), ('Опасно...',)]
             cur.executemany("INSERT INTO raid_hints (text) VALUES (%s)", hints)
             
        conn.commit()
        
    conn.close()
    print("/// DATABASE ENGINE: SYNCHRONIZED.")

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
    finally:
        conn.close()

def create_user(uid, username, first_name, referrer=None):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (uid, username, first_name, referrer)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (uid) DO NOTHING
            """, (uid, username, first_name, referrer))
            conn.commit()
    finally:
        conn.close()

def update_user(uid, **kwargs):
    if not kwargs: return
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Безопасное построение запроса (ключи жестко заданы кодом, значения экранируются)
            set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
            values = list(kwargs.values()) + [uid]
            cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", values)
            conn.commit()
    finally:
        conn.close()

def add_xp_to_user(uid, amount):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (amount, uid))
            conn.commit()
    finally:
        conn.close()

# =============================================================
# 🏆 ДОСТИЖЕНИЯ И ЗНАНИЯ
# =============================================================

def check_achievement_exists(uid, ach_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
            return cur.fetchone() is not None
    finally:
        conn.close()

def grant_achievement(uid, ach_id, bonus_xp):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, ach_id))
            if cur.rowcount > 0:
                cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
                conn.commit()
                return True
            conn.commit()
            return False
    except Exception as e:
        print(f"Error granting ach: {e}")
        return False
    finally:
        conn.close()

def save_knowledge(uid, content_id):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
            if cur.rowcount > 0:
                cur.execute("UPDATE users SET know_count = know_count + 1 WHERE uid = %s", (uid,))
            conn.commit()
    finally:
        conn.close()

# =============================================================
# 📊 СТАТИСТИКА И ДНЕВНИК
# =============================================================

def get_leaderboard(limit=10):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT first_name, xp, level, path FROM users ORDER BY xp DESC LIMIT %s", (limit,))
            return cur.fetchall()
    finally:
        conn.close()

def add_diary_entry(uid, text):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO diary (uid, entry) VALUES (%s, %s)", (uid, text))
            conn.commit()
    finally:
        conn.close()

def get_diary_entries(uid, limit=5):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT entry, created_at FROM diary WHERE uid = %s ORDER BY created_at DESC LIMIT %s", (uid, limit))
            return cur.fetchall()
    finally:
        conn.close()

# =============================================================
# 🔗 СИНДИКАТ (РЕФЕРАЛЫ)
# =============================================================

def get_referrals_stats(uid):
    """Возвращает список рефералов и сколько они принесли (эмуляция 10% от их XP)"""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Мы считаем "Заработок" как 10% от текущего XP реферала (упрощенная модель)
            # Или просто показываем их статус
            cur.execute("""
                SELECT username, first_name, level, xp, 
                       TRUNC(xp * 0.1) as generated 
                FROM users WHERE referrer = %s ORDER BY xp DESC
            """, (str(uid),))
            return cur.fetchall()
    finally:
        conn.close()

# =============================================================
# ⚡️ АДМИН-ПАНЕЛЬ (GOD MODE)
# =============================================================

def admin_exec_query(query):
    """Выполняет любой SQL запрос (SELECT/UPDATE/DELETE)"""
    conn = get_db_connection()
    if not conn: return "❌ No Connection"
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            if query.strip().upper().startswith("SELECT"):
                res = cur.fetchall()
                return str(res)[:3500] # Обрезаем, чтобы влезло в сообщение
            else:
                conn.commit()
                return f"✅ DONE. Rows affected: {cur.rowcount}"
    except Exception as e:
        return f"❌ ERROR: {e}"
    finally:
        conn.close()
