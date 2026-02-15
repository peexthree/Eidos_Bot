import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"/// CRITICAL DB ERROR: {e}")
        return None

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Таблица пользователей
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
            # Таблица достижений
            cur.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(uid, ach_id)
                );
            ''')
            # Таблица открытых знаний
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_knowledge (
                    uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(uid, content_id)
                );
            ''')
            # ТАБЛИЦА ДНЕВНИКА
            cur.execute('''
                CREATE TABLE IF NOT EXISTS diary (
                    id SERIAL PRIMARY KEY, uid BIGINT, entry TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Индексы и патчинг
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_xp ON users(xp DESC);")
            patch_cols = [("ref_count", "INTEGER DEFAULT 0"), ("know_count", "INTEGER DEFAULT 0"), ("total_spent", "INTEGER DEFAULT 0"), ("max_depth", "INTEGER DEFAULT 0")]
            for col, col_type in patch_cols:
                cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type};")
            conn.commit()
    print("/// DATABASE ENGINE: SYNCHRONIZED.")

def get_user(uid):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
            return cur.fetchone()

def update_user(uid, **kwargs):
    if not kwargs: return
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
            cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", list(kwargs.values()) + [uid])
            conn.commit()

def add_xp_to_user(uid, amount):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (amount, uid))
            conn.commit()

def save_knowledge(uid, content_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
                if cur.rowcount > 0:
                    cur.execute("UPDATE users SET know_count = know_count + 1 WHERE uid = %s", (uid,))
                conn.commit()
            except: conn.rollback()

def check_achievement_exists(uid, ach_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM achievements WHERE uid = %s AND ach_id = %s", (uid, ach_id))
            return cur.fetchone() is not None

def grant_achievement(uid, ach_id, bonus_xp):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, ach_id))
                if cur.rowcount > 0:
                    cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (bonus_xp, uid))
                conn.commit()
                return True
            except: conn.rollback(); return False

def get_leaderboard(limit=10):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT first_name, xp, level FROM users ORDER BY xp DESC LIMIT %s", (limit,))
            return cur.fetchall()

def add_diary_entry(uid, text):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO diary (uid, entry) VALUES (%s, %s)", (uid, text))
            conn.commit()

def get_diary_entries(uid):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT entry, created_at FROM diary WHERE uid = %s ORDER BY created_at DESC LIMIT 5", (uid,))
            return cur.fetchall()
