import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
import psycopg2 # ДОБАВЛЕНО: Для базы данных
from psycopg2 import pool # ДОБАВЛЕНО: Для пула соединений
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot" 
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL') # ДОБАВЛЕНО: URL базы

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800      # 30 мин (Синхрон)
COOLDOWN_ACCEL = 900      # 15 мин (Ускоритель)
COOLDOWN_SIGNAL = 300     # 5 мин (Сигнал)
XP_GAIN = 25              # За Синхрон
XP_SIGNAL = 15            # За Сигнал
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 0, 2: 100, 3: 350, 4: 850}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
# Добавили ключ 'signals'
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
USER_CACHE = {} 

# --- ПОДКЛЮЧЕНИЕ К SQL (ДОБАВЛЕНО) ---
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("/// SQL CONNECTION: OK")
except Exception as e:
    print(f"/// SQL ERROR: {e}")
    db_pool = None

# --- 3. ТЕКСТОВЫЕ МОДУЛИ (LORE) ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v20.2**\n\n"
    "**1. КАНАЛЫ ПОЛУЧЕНИЯ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы знаний. Награда: **25 XP** + Бонус Стрика.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие ментальные импульсы (Type: Signal). Награда: **15 XP**.\n\n"
    "**2. СИСТЕМА STREAK (СЕРИЯ):**\n"
    "Твоя дисциплина усиливает нейросеть. Каждый день непрерывного входа добавляет **+5 XP** к базовой награде за Синхрон.\n"
    "*Пример:* 5 дней подряд = +25 XP бонусом.\n\n"
    "**3. УРОВНИ ДОСТУПА:**\n"
    "• **LVL 1:** Базовый доступ.\n"
    "• **LVL 2 (100 XP):** Выбор Фракции.\n"
    "• **LVL 3 (350 XP):** Закрытые данные.\n"
    "• **LVL 4 (850 XP):** Режим Архитектора."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО-КАПСУЛА ({PRICES['cryo']} XP)**\nСтраховка. Спасает твой Стрик при пропуске дня.\n\n"
    f"⚡️ **НЕЙРО-УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nФорсаж. Сокращает ожидание СИНХРОНА с 30 до **15 минут** на 24 часа.\n*(Необходимо активировать в Профиле после покупки)*\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nВзлом. Разовый доступ к контенту уровня Lvl+1.\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

SYNDICATE_FULL = (
    "**🔗 СИНДИКАТ**\n\n"
    f"1. 🎁 **БОНУС:** +{REFERRAL_BONUS} XP за реферала.\n"
    "2. 📈 **РОЯЛТИ:** 10% от опыта твоей сети пожизненно."
)

LEVEL_UP_MSG = {
    2: "🔓 **LVL 2**: Доступ к инструментам Влияния открыт.",
    3: "🔓 **LVL 3**: Статус Оператора. Вижу структуру матрицы.",
    4: "👑 **LVL 4**: Ты — Архитектор. Твоя воля — закон."
}

# --- 4. БАЗА ДАННЫХ ---
def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        # 1. Сначала старый добрый Google (чтобы ничего не сломать)
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            ws_content = sh.worksheet("Content")
            records = ws_content.get_all_records()
            # Обнуляем базу перед загрузкой
            CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
            
            for r in records:
                # Читаем поля
                r_type = str(r.get('Type', '')).lower().strip()
                path = str(r.get('Path', 'general')).lower().strip()
                text = r.get('Text', '')
                try: lvl = int(r.get('Level', 1))
                except: lvl = 1
                
                if text:
                    if r_type == 'signal':
                        CONTENT_DB["signals"].append(text)
                    else:
                        if path not in CONTENT_DB: path = "general"
                        if lvl not in CONTENT_DB[path]: CONTENT_DB[path][lvl] = []
                        CONTENT_DB[path][lvl].append(text)
            
            ws_users = sh.worksheet("Users")
            all_v = ws_users.get_all_values()
            USER_CACHE.clear()
            for i, row in enumerate(all_v[1:], start=2):
                if row and row[0] and str(row[0]).isdigit():
                    uid = int(row[0])
                    def s_int(val, d=0): return int(str(val).strip()) if str(val).strip().isdigit() else d
                    # Добавляем last_signal_time
                    USER_CACHE[uid] = {
                        "path": row[4] if len(row) > 4 and row[4] else "general",
                        "xp": s_int(row[5]), "level": s_int(row[6], 1), "streak": s_int(row[7]),
                        "last_active": row[8] if len(row) > 8 and row[8] else "2000-01-01",
                        "prestige": s_int(row[9]), "cryo": s_int(row[10]), "accel": s_int(row[11]),
                        "decoder": s_int(row[12]),
                        "accel_exp": float(row[13]) if len(row) > 13 and str(row[13]).replace('.','').isdigit() else 0,
                        "referrer": row[14] if len(row) > 14 else None,
                        "last_protocol_time": 0, "last_signal_time": 0, "notified": True, "row_id": i
                    }
            print("/// GOOGLE DB CONNECTED")

        # 2. Инициализация SQL (Создаем таблицу, если нет)
        if db_pool:
            conn = db_pool.getconn()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uid BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    signup_date TEXT,
                    path TEXT,
                    xp INT,
                    level INT,
                    streak INT,
                    last_active TEXT,
                    prestige INT,
                    cryo INT,
                    accel INT,
                    decoder INT,
                    accel_exp FLOAT,
                    referrer TEXT,
                    last_protocol_time FLOAT DEFAULT 0,
                    last_signal_time FLOAT DEFAULT 0
                );
            """)
            conn.commit()
            db_pool.putconn(conn)
            print("/// SQL TABLE CHECKED")

    except Exception as e: print(f"/// DB ERROR: {e}")

connect_db()

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

def sql_update_user(uid):
    """Сохраняет юзера в SQL (дублирование)"""
    if not db_pool: return
    def task():
        u = USER_CACHE.get(uid)
        if not u: return
        try:
            conn = db_pool.getconn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (uid, path, xp, level, streak, last_active, prestige, cryo, accel, decoder, accel_exp, referrer, last_protocol_time, last_signal_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uid) DO UPDATE SET
                path=EXCLUDED.path, xp=EXCLUDED.xp, level=EXCLUDED.level, streak=EXCLUDED.streak,
                last_active=EXCLUDED.last_active, prestige=EXCLUDED.prestige, cryo=EXCLUDED.cryo,
                accel=EXCLUDED.accel, decoder=EXCLUDED.decoder, accel_exp=EXCLUDED.accel_exp,
                last_protocol_time=EXCLUDED.last_protocol_time, last_signal_time=EXCLUDED.last_signal_time;
            """, (uid, u['path'], u['xp'], u['level'], u['streak'], u['last_active'], u['prestige'],
                  u['cryo'], u['accel'], u['decoder'], u['accel_exp'], u.get('referrer'), 
                  u.get('last_protocol_time', 0), u.get('last_signal_time', 0)))
            conn.commit()
            db_pool.putconn(conn)
        except Exception as e: print(f"SQL UPDATE ERROR: {e}")
    threading.Thread(target=task).start()

def save_progress(uid):
    def task():
        try:
            u = USER_CACHE.get(uid)
            # 1. Сохраняем в Гугл (как было)
            if u and ws_users:
                data = [u['path'], str(u['xp']), str(u['level']), str(u['streak']), u['last_active'], str(u['prestige']),
                        str(u['cryo']), str(u['accel']), str(u['decoder']), str(u['accel_exp']), str(u.get('referrer', ''))]
                ws_users.update(f"E{u['row_id']}:O{u['row_id']}", [data])
            
            # 2. Сохраняем в SQL (дублируем)
            sql_update_user(uid)
        except: pass
    threading.Thread(target=task).start()

def async_register_user(uid, username, first_name, ref_arg):
    try:
        start_xp = "50" if ref_arg == 'inst' else "0"
        
        # 1. Гугл
        if ws_users:
            ws_users.append_row([str(uid), f"@{username}", first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                 "general", start_xp, "1", "1", datetime.now().strftime("%Y-%m-%d"), 
                                 "0", "0", "0", "0", "0", str(ref_arg or '')])
        
        # 2. SQL
        if db_pool:
            conn = db_pool.getconn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (uid, username, first_name, signup_date, path, xp, referrer, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING
            """, (uid, username, first_name, datetime.now(), 'general', int(start_xp), ref_arg, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            db_pool.putconn(conn)
            
    except: pass

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today, yesterday = datetime.now().strftime("%Y-%m-%d"), (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus, s_msg = 0, None
        
        streak_bonus = u['streak'] * 5
        
        if u['last_active'] == yesterday:
            u['streak'] += 1; s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН."
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else: u['streak'] = 1; streak_bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        
        u['last_active'] = today
        total = amount + streak_bonus 
        u['xp'] += total
        
        if u.get('referrer') and str(u['referrer']).isdigit() and int(u['referrer']) in USER_CACHE:
            r = USER_CACHE[int(u['referrer'])]
            r['xp'] += max(1, int(total * 0.1)); save_progress(int(u['referrer']))
            
        old_lvl = u['level']
        for lvl, threshold in sorted(LEVELS.items(), reverse=True):
            if u['xp'] >= threshold:
                u['level'] = lvl
                break
        save_progress(uid)
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

def decrypt_and_send(chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    try:
        status_msg = bot.send_message(chat_id, "📡 **ИНИЦИАЛИЗАЦИЯ...**")
        time.sleep(1)
        bot.edit_message_text(f"🔓 **ДЕШИФРОВКА...**\n`[||||||||..] 84%`", chat_id, status_msg.message_id, parse_mode="Markdown")
        time.sleep(0.8)
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, target_lvl + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            for l in range(1, target_lvl + 1):
                if l in CONTENT_DB.get('general', {}): pool.extend(CONTENT_DB['general'][l])
        txt = random.choice(pool) if pool else "/// НЕТ ДАННЫХ ДЛЯ ВАШЕГО УРОВНЯ."
        school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
        res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} XP (+{u['streak']*5} Bonus) {use_dec_text}"
        bot.edit_message_text(res, chat_id, status_msg.message_id, parse_mode="Markdown", 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except: pass

# --- 6. ПУШИ ---
def notification_worker():
    while True:
        try:
            time.sleep(60)
            now = time.time()
            for uid, u in list(USER_CACHE.items()):
                is_accel = u.get('accel_exp', 0) > now
                cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
                
                if u.get('last_protocol_time', 0) > 0 and (now - u['last_protocol_time'] >= cd) and not u.get('notified', True):
                    try:
                        bot.send_message(uid, "⚡️ **СИСТЕМА ГОТОВА.**\nПротокол восстановлен.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

def get_progress_bar(current_xp, level):
    next_level_xp = LEVELS.get(level + 1, 10000)
    prev_level_xp = LEVELS.get(level, 0)
    if level >= 4: return "`[||||||||||] MAX`"
    needed = next_level_xp - prev_level_xp
    current = current_xp - prev_level_xp
    percent = min(100, max(0, int((current / needed) * 100)))
    blocks = int(percent / 10)
    bar = "||" * blocks + ".." * (10 - blocks)
    return f"`[{bar}] {percent}%`"

# --- 7. ИНТЕРФЕЙС ---
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # ИЗМЕНЕНИЕ: Добавлена кнопка СИГНАЛ рядом с СИНХРОНОМ
    markup.add(
        types.InlineKeyboardButton("👁 ДЕШИФРОВАТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")
    )
    markup.add(
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"),
        types.InlineKeyboardButton("📚 РУКОВОДСТВО", callback_data="guide")
    )
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel"))
    return markup

def get_admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 ОБНОВИТЬ БД", callback_data="admin_refresh"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"),
        types.InlineKeyboardButton("🎁 НАЧИСЛИТЬ ВСЕМ БОНУС", callback_data="admin_bonus"),
        types.InlineKeyboardButton("💀 УДАЛИТЬ ПО ID", callback_data="admin_ban"),
        types.InlineKeyboardButton("🔙 В МЕНЮ", callback_data="back_to_menu")
    )
    return markup

def get_path_menu(cost_info=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_text = f" (-{PATH_CHANGE_COST} XP)" if cost_info else ""
    markup.add(
        types.InlineKeyboardButton(f"🔴 ХИЩНИК [Материя]{btn_text}", callback_data="set_path_money"),
        types.InlineKeyboardButton(f"🔵 МИСТИК [Разум]{btn_text}", callback_data="set_path_mind"),
        types.InlineKeyboardButton(f"🟣 ТЕХНОЖРЕЦ [AI]{btn_text}", callback_data="set_path_tech"),
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
    )
    return markup

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None

    # Мгновенная регистрация в кэш
    if uid not in USER_CACHE:
        start_xp = 50 if ref_arg == 'inst' else 0
        USER_CACHE[uid] = {
            "path": "general", "xp": start_xp, "level": 1, "streak": 1, "last_active": datetime.now().strftime("%Y-%m-%d"),
            "prestige": 0, "cryo": 0, "accel": 0, "decoder": 0, "accel_exp": 0, "referrer": ref_arg,
            "last_protocol_time": 0, "last_signal_time": 0, "notified": True, "row_id": len(USER_CACHE) + 2
        }
        threading.Thread(target=async_register_user, args=(uid, m.from_user.username, m.from_user.first_name, ref_arg)).start()
        
        if ref_arg and ref_arg.isdigit() and int(ref_arg) in USER_CACHE:
            USER_CACHE[int(ref_arg)]['xp'] += REFERRAL_BONUS; save_progress(int(ref_arg))
            try: bot.send_message(int(ref_arg), f"🎁 **НОВЫЙ УЗЕЛ.** +{REFERRAL_BONUS} XP.")
            except: pass

    welcome_msg = "/// EIDOS-OS: СИНХРОНИЗИРОВАН."
    if ref_arg == 'inst': welcome_msg = "🧬 **СИГНАЛ ИЗ INSTAGRAM.**\nБонус +50 XP начислен."
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

# --- МИГРАЦИЯ (СЕКРЕТНАЯ КОМАНДА) ---
@bot.message_handler(commands=['migration_start'])
def migration_cmd(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(m.chat.id, "⏳ НАЧИНАЮ МИГРАЦИЮ В SQL...")
        try:
            if ws_users and db_pool:
                rows = ws_users.get_all_values()[1:] # Пропускаем хедер
                conn = db_pool.getconn()
                cur = conn.cursor()
                count = 0
                for r in rows:
                    try:
                        uid = int(r[0])
                        # Вставляем данные, игнорируем если уже есть
                        cur.execute("""
                            INSERT INTO users (uid, username, first_name, signup_date, path, xp, level, streak, last_active, prestige, cryo, accel, decoder, accel_exp, referrer)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (uid) DO NOTHING
                        """, (uid, r[1], r[2], r[3], r[4], int(r[5]), int(r[6]), int(r[7]), r[8], int(r[9]), int(r[10]), int(r[11]), int(r[12]), float(r[13]), r[14]))
                        count += 1
                    except: pass
                conn.commit()
                db_pool.putconn(conn)
                bot.send_message(m.chat.id, f"✅ УСПЕШНО! Обработано строк: {count}")
            else:
                bot.send_message(m.chat.id, "❌ Ошибка подключения к базе или таблице.")
        except Exception as e:
            bot.send_message(m.chat.id, f"❌ CRITICAL ERROR: {e}")

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': connect_db(); bot.send_message(message.chat.id, "✅ БД ОБНОВЛЕНА.")
        elif message.text and message.text.startswith('/telegraph '):
            parts = message.text.split(maxsplit=2)
            if len(parts) >= 2:
                url, text = parts[1], parts[2] if len(parts) > 2 else "/// АРХИВ ДЕШИФРОВАН"
                clean_url = url.split("google.com/search?q=")[-1] if "google.com" in url else url
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📂 ОТКРЫТЬ ДОСЬЕ", url=clean_url))
                markup.add(types.InlineKeyboardButton("👁 СИНХРОН", url=f"https://t.me/{BOT_USERNAME}"))
                markup.add(types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=signal"))
                
                bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ВОЙТИ В ТЕРМИНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=channel"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
        elif message.text and message.text.startswith('/ban '): 
            try:
                target_id = int(message.text.split()[1])
                if target_id in USER_CACHE:
                    del USER_CACHE[target_id]
                    bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} ОТКЛЮЧЕН.")
            except: bot.send_message(message.chat.id, "❌ Ошибка ID.")
        elif message.text and message.text.startswith('/give_xp '):
            try:
                _, t_id, amount = message.text.split()
                t_id, amount = int(t_id), int(amount)
                if t_id in USER_CACHE:
                    USER_CACHE[t_id]['xp'] += amount; save_progress(t_id)
                    bot.send_message(t_id, f"⚡️ **ВМЕШАТЕЛЬСТВО АРХИТЕКТОРА:** Начислено {amount} XP.")
                    bot.send_message(message.chat.id, "✅ Начислено.")
            except: bot.send_message(message.chat.id, "❌ Формат: /give_xp ID СУММА")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE:
        bot.answer_callback_query(call.id, "⚠️ Нажми /start", show_alert=True); return
    u = USER_CACHE[uid]
    now_ts = time.time()

    try:
        if call.data == "admin_panel" and uid == ADMIN_ID: 
            safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ АРХИТЕКТОРА**\n\nКоманды чата:\n`/ban ID` — Удалить юзера\n`/give_xp ID СУММА` — Начислить опыт\n`/telegraph ССЫЛКА ТЕКСТ` — Пост статьи\n`/migration_start` — Перенос в SQL", get_admin_menu())
        
        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            count = 0
            for u_id in USER_CACHE:
                USER_CACHE[u_id]['xp'] += 100; save_progress(u_id); count += 1
            bot.answer_callback_query(call.id, f"🎁 Выдано по 100 XP {count} узлам")

        elif call.data == "admin_refresh" and uid == ADMIN_ID: connect_db(); bot.answer_callback_query(call.id, "✅ OK")
        elif call.data == "admin_stats" and uid == ADMIN_ID:
            inst_users = sum(1 for user in USER_CACHE.values() if user.get('referrer') == 'inst')
            bot.answer_callback_query(call.id, f"📊 Всего: {len(USER_CACHE)}\n📸 Instagram: {inst_users}", show_alert=True)

        elif call.data == "get_protocol":
            # --- ФИКС УСКОРИТЕЛЯ ---
            is_accel = u.get('accel_exp', 0) > now_ts
            cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
            
            if now_ts - u.get('last_protocol_time', 0) < cd:
                rem = int((cd - (now_ts - u.get('last_protocol_time', 0))) / 60)
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
            
            u['last_protocol_time'] = now_ts
            up, s_msg, total = add_xp(uid, XP_GAIN)
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: u['decoder'] -= 1
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
            threading.Thread(target=decrypt_and_send, args=(uid, uid, target_lvl, "")).start()

        # --- НОВАЯ КНОПКА: СИГНАЛ ---
        elif call.data == "get_signal":
            if now_ts - u.get('last_signal_time', 0) < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u.get('last_signal_time', 0))) / 60)
                msg_t = f"{rem} мин" if rem > 0 else "< 1 мин"
                bot.answer_callback_query(call.id, f"📡 ЖДИ: {msg_t}", show_alert=True); return
            
            u['last_signal_time'] = now_ts
            up, s_msg, total = add_xp(uid, XP_SIGNAL)
            
            # Берем сигнал из массива CONTENT_DB["signals"]
            # Если база пуста - заглушка
            txt = random.choice(CONTENT_DB["signals"]) if CONTENT_DB["signals"] else "/// ЭФИР ПУСТ. ПОПРОБУЙ ПОЗЖЕ."
            
            bot.send_message(uid, f"📶 **ПОЛУЧЕН СИГНАЛ**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP (+{u['streak']*5} Streak Bonus)", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

        elif call.data == "profile":
            title = TITLES.get(u['level'], "НЕОФИТ")
            progress = get_progress_bar(u['xp'], u['level'])
            ref_count = sum(1 for user in USER_CACHE.values() if str(user.get('referrer')) == str(uid))
            desc_map = {
                "money": "Искусство Влияния и Продаж",
                "mind": "Психология и Ментальные Ловушки",
                "tech": "ИИ-Инструменты и Автоматизация",
                "general": "Базовая Калибровка Сознания"
            }
            path_desc = desc_map.get(u['path'], "Не определен")
            
            # ОТОБРАЖЕНИЕ СТАТУСА УСКОРИТЕЛЯ
            accel_status = "✅ АКТИВЕН" if u.get('accel_exp', 0) > now_ts else "❌ НЕ АКТИВЕН"

            msg = (f"👤 **НЕЙРО-ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n"
                   f"🔰 **СТАТУС:** {title}\n"
                   f"⚔️ **ФРАКЦИЯ:** {SCHOOLS.get(u['path'], 'ОБЩИЙ ПОТОК')}\n"
                   f"📖 *{path_desc}*\n\n"
                   f"🔋 **SYNC:** {u['xp']} XP\n{progress}\n"
                   f"🔥 **STREAK:** {u['streak']} дн. (Бонус: +{u['streak']*5} XP)\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🎒 **ИНВЕНТАРЬ:**\n❄️ Крио: {u['cryo']}\n⚡️ Ускоритель: {accel_status}\n🔑 Дешифратор: {u['decoder']}")
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            # Кнопка активации (появляется только если есть предмет и он не активен)
            if u['accel'] > 0 and u.get('accel_exp', 0) < now_ts:
                markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ВЕКТОР", callback_data="change_path_confirm"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

        elif call.data == "back_to_menu":
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))

        elif call.data == "shop":
            safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("❄️ КУПИТЬ КРИО (200 XP)", callback_data="buy_cryo"),
                types.InlineKeyboardButton("⚡️ КУПИТЬ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
                types.InlineKeyboardButton("🔑 КУПИТЬ ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"),
                types.InlineKeyboardButton("⚙️ СМЕНИТЬ ФРАКЦИЮ (100 XP)", callback_data="change_path_confirm"),
                types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))

        elif call.data.startswith("buy_"):
            item = call.data.split("_")[1]
            if u['xp'] >= PRICES[item]:
                u['xp'] -= PRICES[item]; u[item] += 1; save_progress(uid)
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item.upper()}"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО SYNC", show_alert=True)

        elif call.data == "referral":
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ТВОЯ ПЕРСОНАЛЬНАЯ ССЫЛКА:**\n`{link}`", get_main_menu(uid))

        elif call.data == "change_path_confirm":
            safe_edit(call, f"⚠️ **СМЕНА ФРАКЦИИ**\nЦена: **{PATH_CHANGE_COST} SYNC**.", get_path_menu(cost_info=True))

        elif "set_path_" in call.data:
            new_path = call.data.split("_")[-1]
            if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
                if u['path'] != 'general' and u['path'] != new_path: u['xp'] -= PATH_CHANGE_COST
                u['path'] = new_path; save_progress(uid)
                bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "use_accel":
            if u['accel'] > 0:
                u['accel'] -= 1; u['accel_exp'] = now_ts + 86400; save_progress(uid)
                bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН. КУЛДАУН: 15 МИН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕТ УСКОРИТЕЛЯ", show_alert=True)

        elif call.data == "guide": 
            safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except Exception as e: print(f"/// CALLBACK ERROR: {e}")

# --- 9. ЗАПУСК ---
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'OK', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'Error', 500
    return 'Eidos Interface is Operational', 200

@app.route('/health')
def health_check(): return 'OK', 200

if __name__ == "__main__":
    if WEBHOOK_URL: 
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
    threading.Thread(target=notification_worker, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
