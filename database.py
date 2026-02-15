import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

def get_db_connection():
    try: return psycopg2.connect(DATABASE_URL, sslmode='require')
    except: return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    cur = conn.cursor()
    # Таблица пользователей
    cur.execute('''CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1, last_active DATE DEFAULT CURRENT_DATE, cryo INTEGER DEFAULT 0, accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0, accel_exp BIGINT DEFAULT 0, referrer TEXT, last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0, notified BOOLEAN DEFAULT TRUE, max_depth INTEGER DEFAULT 0, path TEXT DEFAULT 'general');''')
    # Контент и Рейд
    cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS raid_content (id SERIAL PRIMARY KEY, text TEXT, type TEXT, val INTEGER);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS raid_hints (id SERIAL PRIMARY KEY, type TEXT, text TEXT);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS raid_sessions (uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100, buffer_xp INTEGER DEFAULT 0, start_time BIGINT);''')
    # Доп таблицы
    cur.execute('''CREATE TABLE IF NOT EXISTS user_knowledge (uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, content_id));''')
    cur.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, uid BIGINT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
    cur.execute('''CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, uid BIGINT, action TEXT, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
    conn.commit(); conn.close()

def get_user(uid):
    conn = get_db_connection()
    if not conn: return None
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
    res = cur.fetchone(); conn.close(); return res

def update_user(uid, **kwargs):
    conn = get_db_connection(); cur = conn.cursor()
    set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
    cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", list(kwargs.values()) + [uid])
    conn.commit(); conn.close()
