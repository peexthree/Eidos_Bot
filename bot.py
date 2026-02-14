import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- ЭКОНОМИКА (ТВОИ ПОРОГИ) ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("/// SQL ENGINE: ONLINE")
except Exception as e:
    print(f"/// SQL ERROR: {e}")

# --- 3. МОДУЛЬ ПРОВЕРКИ БАЗЫ (ДЛЯ ТЕБЯ) ---

@bot.message_handler(commands=['db_check'])
def db_check_cmd(m):
    if m.from_user.id != ADMIN_ID: return
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        u_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM content")
        c_count = cur.fetchone()[0]
        bot.send_message(m.chat.id, f"📊 **СТАТУС SQL БАЗЫ:**\n\n👤 Пользователей: {u_count}\n📑 Строк контента: {c_count}")
    except Exception as e: bot.send_message(m.chat.id, f"❌ Ошибка: {e}")
    finally: db_pool.putconn(conn)

# --- 4. ТОТАЛЬНАЯ МИГРАЦИЯ (ОБНОВЛЕННАЯ) ---

@bot.message_handler(commands=['full_migrate'])
def full_migrate_cmd(m):
    if m.from_user.id != ADMIN_ID: return
    bot.send_message(m.chat.id, "⏳ Начинаю тотальный перенос данных...")
    try:
        creds = json.loads(GOOGLE_JSON)
        if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open(SHEET_NAME)
        
        conn = db_pool.getconn()
        cur = conn.cursor()

        # МИГРАЦИЯ КОНТЕНТА
        cur.execute("DROP TABLE IF EXISTS content CASCADE;")
        cur.execute("CREATE TABLE content (id SERIAL, type TEXT, path TEXT, text TEXT, level INT);")
        ws_content = sh.worksheet("Content")
        c_records = ws_content.get_all_records()
        for r in c_records:
            cur.execute("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)",
                       (str(r.get('Type','')), str(r.get('Path','general')), str(r.get('Text','')), int(r.get('Level',1))))
        
        # МИГРАЦИЯ ЮЗЕРОВ
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, signup_date TEXT,
                path TEXT DEFAULT 'general', xp INT DEFAULT 0, level INT DEFAULT 1,
                streak INT DEFAULT 1, last_active TEXT, prestige INT DEFAULT 0,
                cryo INT DEFAULT 0, accel INT DEFAULT 0, decoder INT DEFAULT 0,
                accel_exp FLOAT DEFAULT 0, referrer TEXT, last_protocol_time FLOAT DEFAULT 0,
                last_signal_time FLOAT DEFAULT 0
            );
        """)
        ws_users = sh.worksheet("Users")
        u_rows = ws_users.get_all_values()[1:]
        for r in u_rows:
            if not r[0].isdigit(): continue
            cur.execute("""
                INSERT INTO users (uid, username, first_name, signup_date, path, xp, level, streak, last_active, prestige, cryo, accel, decoder, accel_exp, referrer)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uid) DO UPDATE SET xp=EXCLUDED.xp, level=EXCLUDED.level;
            """, (int(r[0]), r[1], r[2], r[3], r[4], int(r[5]), int(r[6]), int(r[7]), r[8], int(r[9]), int(r[10]), int(r[11]), int(r[12]), float(r[13]), r[14]))

        conn.commit()
        db_pool.putconn(conn)
        bot.send_message(m.chat.id, f"✅ МИГРАЦИЯ ЗАВЕРШЕНА.\nЮзеров: {len(u_rows)}\nКонтента: {len(c_records)}")
    except Exception as e: bot.send_message(m.chat.id, f"❌ ОШИБКА: {e}")

# --- 5. ЛОГИКА ВЫБОРА КОНТЕНТА ---
def get_content_sql(u_path, u_level, c_type='protocol'):
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        if c_type == 'signal':
            cur.execute("SELECT text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
        else:
            cur.execute("SELECT text FROM content WHERE type!='signal' AND path=%s AND level<=%s ORDER BY RANDOM() LIMIT 1", (u_path, u_level))
        res = cur.fetchone()
        return res[0] if res else "/// НЕТ ДАННЫХ В SQL."
    finally: db_pool.putconn(conn)

# --- 6. HEALTH CHECK И WEBHOOK ---
@app.route('/health')
def health_check(): return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    return 'Eidos Operational', 200

# --- 7. ЗАПУСК ---
if __name__ == "__main__":
    bot.remove_webhook(); time.sleep(1)
    if WEBHOOK_URL: bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
