import telebot
from telebot import types
import flask
import os
import time
import random
import psycopg2
from psycopg2 import pool
import threading
import gspread # Нужно для миграции
import json
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
# ЭТИ ДВЕ ПЕРЕМЕННЫЕ ДОЛЖНЫ БЫТЬ В ENVIRONMENT VARIABLES НА RENDER
DATABASE_URL = os.environ.get('DATABASE_URL') 
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800
COOLDOWN_ACCEL = 900
COOLDOWN_SIGNAL = 300
XP_GAIN = 25
XP_SIGNAL = 15
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}
LEVELS = {1: 0, 2: 100, 3: 350, 4: 850}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# ПОДКЛЮЧЕНИЕ К SQL
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("/// SQL CONNECTION: OK")
except Exception as e:
    print(f"/// SQL ERROR: {e}")

CONTENT_DB = {"money": [], "mind": [], "tech": [], "general": [], "signals": []}
USER_CACHE = {} 

# --- 3. ТЕКСТЫ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}
GUIDE_FULL = "**📚 ДОКУМЕНТАЦИЯ**\n\n1. **СИНХРОН (30 мин):** 25 XP + бонус Стрика.\n2. **СИГНАЛ (5 мин):** 15 XP.\n3. **СТРИК:** +5 XP за каждый день.\n4. **УРОВНИ:** Открывают контент."
SHOP_FULL = "**🎰 ЧЕРНЫЙ РЫНОК**\n\n❄️ **КРИО** (200 XP)\n⚡️ **УСКОРИТЕЛЬ** (500 XP)\n🔑 **ДЕШИФРАТОР** (800 XP)\n⚙️ **СМЕНА ФРАКЦИИ** (100 XP)"
SYNDICATE_FULL = f"**🔗 СИНДИКАТ**\n\n🎁 +{REFERRAL_BONUS} XP за друга + 10% роялти."
LEVEL_UP_MSG = {2: "🔓 **LVL 2**: Доступ открыт.", 3: "🔓 **LVL 3**: Статус Оператора.", 4: "👑 **LVL 4**: Архитектор."}

# --- 4. РАБОТА С БД И МИГРАЦИЯ ---

def init_db():
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        # Создаем таблицу, если её нет
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                signup_date TIMESTAMP,
                path TEXT DEFAULT 'general',
                xp INT DEFAULT 0,
                level INT DEFAULT 1,
                streak INT DEFAULT 1,
                last_active DATE,
                prestige INT DEFAULT 0,
                cryo INT DEFAULT 0,
                accel INT DEFAULT 0,
                decoder INT DEFAULT 0,
                accel_exp FLOAT DEFAULT 0,
                referrer TEXT,
                last_protocol_time FLOAT DEFAULT 0,
                last_signal_time FLOAT DEFAULT 0
            );
        """)
        conn.commit()
        
        # ЗАГРУЗКА КЭША
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        USER_CACHE.clear()
        for r in rows:
            uid = r[0]
            USER_CACHE[uid] = {
                "username": r[1], "first_name": r[2], "signup_date": str(r[3]),
                "path": r[4], "xp": r[5], "level": r[6], "streak": r[7], 
                "last_active": str(r[8]), "prestige": r[9], "cryo": r[10], 
                "accel": r[11], "decoder": r[12], "accel_exp": r[13], 
                "referrer": r[14], "last_protocol_time": r[15], "last_signal_time": r[16],
                "notified": True
            }
        
        # ЗАГРУЗКА КОНТЕНТА ИЗ ГУГЛА (ВРЕМЕННО, ЧТОБЫ ТЕКСТЫ НЕ ПРОПАЛИ)
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            ws_c = sh.worksheet("Content")
            records = ws_c.get_all_records()
            for r in records:
                path, text, lvl = str(r.get('Path', 'general')).lower(), r.get('Text', ''), int(r.get('Level', 1) or 1)
                r_type = str(r.get('Type', '')).lower().strip()
                if text:
                    if r_type == 'signal': CONTENT_DB["signals"].append(text)
                    else:
                        if path not in CONTENT_DB: path = "general"
                        CONTENT_DB[path].append(text)
                        
        print(f"/// SYSTEM ONLINE. Users: {len(USER_CACHE)}")
    except Exception as e: print(f"/// INIT ERROR: {e}")
    finally: db_pool.putconn(conn)

init_db()

def sql_exec(query, params):
    threading.Thread(target=lambda: _sql_exec_thread(query, params)).start()

def _sql_exec_thread(query, params):
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
    except Exception as e: print(f"SQL ERROR: {e}")
    finally: db_pool.putconn(conn)

# --- 5. ФУНКЦИИ ЯДРА ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: 
        try: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except: pass

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today = datetime.now().strftime("%Y-%m-%d")
        bonus = 0
        
        # Стрик
        if str(u['last_active']) != today:
            try:
                last = datetime.strptime(str(u['last_active']), "%Y-%m-%d")
                curr = datetime.strptime(today, "%Y-%m-%d")
                if (curr - last).days == 1: u['streak'] += 1; bonus = u['streak'] * 5
                else:
                    if u['cryo'] > 0: u['cryo'] -= 1
                    else: u['streak'] = 1; bonus = 5
            except: u['streak'] = 1
        
        u['last_active'] = today
        total = amount + bonus
        u['xp'] += total
        
        # Реферал
        if u.get('referrer') and str(u['referrer']).isdigit():
            rid = int(u['referrer'])
            if rid in USER_CACHE:
                USER_CACHE[rid]['xp'] += max(1, int(total * 0.1))
                sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[rid]['xp'], rid))

        old_lvl = u['level']
        for lvl, th in sorted(LEVELS.items(), reverse=True):
            if u['xp'] >= th: u['level'] = lvl; break
        
        # Сохранение в SQL
        sql_exec("""
            UPDATE users SET xp=%s, level=%s, streak=%s, last_active=%s, cryo=%s WHERE uid=%s
        """, (u['xp'], u['level'], u['streak'], u['last_active'], u['cryo'], uid))
        
        return (u['level'] > old_lvl), total
    return False, 0

def decrypt_and_send(chat_id, uid):
    u = USER_CACHE[uid]
    try:
        time.sleep(1)
        # Выбираем контент по пути юзера или общий
        pool = CONTENT_DB.get(u['path'], []) + CONTENT_DB.get('general', [])
        txt = random.choice(pool) if pool else "/// ЗАГРУЗКА..."
        bot.send_message(chat_id, f"🧬 **ДАННЫЕ:**\n\n{txt}\n\n━━━━━━━━━━━━━━", parse_mode="Markdown")
        bot.send_message(chat_id, "/// ТЕРМИНАЛ ГОТОВ.", reply_markup=get_main_menu(uid))
    except: pass

# --- 6. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None

    # МГНОВЕННАЯ РЕГИСТРАЦИЯ В ПАМЯТИ И SQL
    if uid not in USER_CACHE:
        start_xp = 50 if ref_arg == 'inst' else 0
        USER_CACHE[uid] = {
            "path": "general", "xp": start_xp, "level": 1, "streak": 1, 
            "last_active": datetime.now().strftime("%Y-%m-%d"),
            "prestige": 0, "cryo": 0, "accel": 0, "decoder": 0, "accel_exp": 0, 
            "referrer": ref_arg, "last_protocol_time": 0, "last_signal_time": 0, "notified": True
        }
        
        sql_exec("""
            INSERT INTO users (uid, username, first_name, signup_date, path, xp, referrer, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING
        """, (uid, m.from_user.username, m.from_user.first_name, datetime.now(), 'general', start_xp, ref_arg, datetime.now().date()))
        
        if ref_arg and str(ref_arg).isdigit() and int(ref_arg) in USER_CACHE:
            rid = int(ref_arg)
            USER_CACHE[rid]['xp'] += REFERRAL_BONUS
            sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[rid]['xp'], rid))
            try: bot.send_message(rid, f"🎁 **НОВЫЙ УЗЕЛ.** +{REFERRAL_BONUS} XP.")
            except: pass

    welcome = "/// EIDOS: ONLINE."
    if ref_arg == 'inst': welcome = "🧬 **INSTAGRAM-БОНУС:** +50 XP."
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome, reply_markup=get_main_menu(uid))

@bot.message_handler(commands=['migration_start'])
def migration_handler(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(m.chat.id, "⏳ НАЧИНАЮ МИГРАЦИЮ ИЗ GOOGLE SHEETS В POSTGRES...")
        try:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            rows = gc.open(SHEET_NAME).worksheet("Users").get_all_values()[1:]
            
            conn = db_pool.getconn()
            cur = conn.cursor()
            count = 0
            for r in rows:
                try:
                    # Маппинг данных из старой таблицы
                    # r[0]=uid, r[4]=path, r[5]=xp, r[6]=lvl, r[7]=streak, r[8]=last_active ...
                    uid = int(r[0])
                    if uid in USER_CACHE: continue # Уже есть в новой базе
                    
                    cur.execute("""
                        INSERT INTO users (uid, username, first_name, signup_date, path, xp, level, streak, last_active, prestige, cryo, accel, decoder, accel_exp, referrer)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uid) DO NOTHING
                    """, (uid, r[1], r[2], r[3], r[4], int(r[5]), int(r[6]), int(r[7]), r[8], int(r[9]), int(r[10]), int(r[11]), int(r[12]), float(r[13]), r[14]))
                    count += 1
                except: pass
            
            conn.commit()
            db_pool.putconn(conn)
            # Обновляем кэш
            init_db()
            bot.send_message(m.chat.id, f"✅ МИГРАЦИЯ УСПЕШНА. ПЕРЕНЕСЕНО: {count} ПОЛЬЗОВАТЕЛЕЙ.")
        except Exception as e:
            bot.send_message(m.chat.id, f"❌ ОШИБКА: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "get_protocol":
        is_accel = u.get('accel_exp', 0) > now_ts
        cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
        if now_ts - u.get('last_protocol_time', 0) < cd:
            rem = int((cd - (now_ts - u.get('last_protocol_time', 0))) / 60)
            bot.answer_callback_query(call.id, f"⏳ ЖДИ: {rem} мин.", show_alert=True); return
        
        u['last_protocol_time'] = now_ts
        sql_exec("UPDATE users SET last_protocol_time=%s WHERE uid=%s", (now_ts, uid))
        up, total = add_xp(uid, XP_GAIN)
        if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 LEVEL UP!"))
        threading.Thread(target=decrypt_and_send, args=(uid, uid)).start()

    elif call.data == "get_signal":
        if now_ts - u.get('last_signal_time', 0) < COOLDOWN_SIGNAL:
            rem = int((COOLDOWN_SIGNAL - (now_ts - u.get('last_signal_time', 0))) / 60)
            msg_t = f"{rem} мин" if rem > 0 else "< 1 мин"
            bot.answer_callback_query(call.id, f"📡 ЖДИ: {msg_t}", show_alert=True); return
        
        u['last_signal_time'] = now_ts
        sql_exec("UPDATE users SET last_signal_time=%s WHERE uid=%s", (now_ts, uid))
        up, total = add_xp(uid, XP_SIGNAL)
        
        txt = random.choice(CONTENT_DB["signals"]) if CONTENT_DB["signals"] else "/// ЭФИР ПУСТ."
        bot.send_message(uid, f"📶 **СИГНАЛ ПОЛУЧЕН:**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP")

    elif call.data == "profile":
        accel_s = "✅ АКТИВЕН" if u.get('accel_exp', 0) > now_ts else "❌ НЕТ"
        msg = f"👤 **ПРОФИЛЬ**\n🔋 XP: {u['xp']} | LVL: {u['level']}\n🔥 Стрик: {u['streak']} дн.\n🎒 Крио: {u['cryo']} | Ускоритель: {accel_s}"
        m = types.InlineKeyboardMarkup()
        if u['accel'] > 0 and u.get('accel_exp', 0) < now_ts: m.add(types.InlineKeyboardButton("🚀 ВКЛЮЧИТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
        m.add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))
        safe_edit(call, msg, m)

    elif call.data == "use_accel":
        if u['accel'] > 0:
            u['accel'] -= 1; u['accel_exp'] = now_ts + 86400
            sql_exec("UPDATE users SET accel=%s, accel_exp=%s WHERE uid=%s", (u['accel'], u['accel_exp'], uid))
            bot.answer_callback_query(call.id, "✅ ВКЛЮЧЕНО (24ч)")
            callback.data = "profile"; callback(call) # Обновляем вид
        else: bot.answer_callback_query(call.id, "❌ ПУСТО")

    elif call.data == "shop":
        safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("❄️ КУПИТЬ КРИО (200 XP)", callback_data="buy_cryo"),
            types.InlineKeyboardButton("⚡️ КУПИТЬ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
            types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            u['xp'] -= PRICES[item]; u[item] += 1
            sql_exec(f"UPDATE users SET xp=%s, {item}=%s WHERE uid=%s", (u['xp'], u[item], uid))
            bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item}"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP")

    elif call.data == "back_to_menu":
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// SYSTEM READY.", reply_markup=get_main_menu(uid))
    
    elif call.data == "guide": safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "referral": safe_edit(call, f"{SYNDICATE_FULL}\n`https://t.me/{BOT_USERNAME}?start={uid}`", get_main_menu(uid))
    
    elif call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ ADMIN\n/migration_start - перенос базы", get_admin_menu())
    elif call.data == "admin_stats" and uid == ADMIN_ID: bot.answer_callback_query(call.id, f"Users: {len(USER_CACHE)}", show_alert=True)

def get_main_menu(uid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    m.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    m.add(types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"), types.InlineKeyboardButton("📚 ГАЙД", callback_data="guide"))
    if uid == ADMIN_ID: m.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return m

def get_admin_menu():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📊 STATS", callback_data="admin_stats"), types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))

# --- 9. ЗАПУСК ---
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try: bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        except: pass
        return 'OK', 200
    return 'Alive', 200

@app.route('/health')
def health(): return 'OK', 200

def notification_worker():
    while True:
        try:
            time.sleep(60)
            now = time.time()
            for uid, u in list(USER_CACHE.items()):
                # Уведомление о СИНХРОНЕ
                cd = COOLDOWN_ACCEL if u.get('accel_exp', 0) > now else COOLDOWN_BASE
                if u.get('last_protocol_time', 0) > 0 and (now - u['last_protocol_time'] >= cd) and not u.get('notified', True):
                    try:
                        bot.send_message(uid, "⚡️ **ГОТОВО:** Протокол восстановлен.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

if __name__ == "__main__":
    bot.remove_webhook(); time.sleep(1); bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=notification_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
