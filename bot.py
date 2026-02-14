import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
import psycopg2 # Библиотека для новой базы
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
DATABASE_URL = os.environ.get('DATABASE_URL') # Новая переменная для SQL

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800
COOLDOWN_ACCEL = 900
COOLDOWN_SIGNAL = 300 # 5 мин (Сигнал)
XP_GAIN = 25
XP_SIGNAL = 15
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 0, 2: 100, 3: 350, 4: 850}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
USER_CACHE = {} 

# --- 3. ТЕКСТОВЫЕ МОДУЛИ (ТВОИ ОРИГИНАЛЬНЫЕ) ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v19.0**\n\n"
    "**1. СУТЬ ПРОЕКТА:**\n"
    "Этот бот — агрегатор закрытых знаний. Мы выкупаем платные курсы, инсайды и приватные мануалы, дефрагментируем их и выдаем тебе в виде сжатых «Протоколов». Ты не тратишь годы — ты получаешь суть за секунды.\n\n"
    "**2. ЭКОНОМИКА ЭНЕРГИИ (XP/SYNC):**\n"
    "• **SYNC** — твоя валюта. Ты получаешь **25 XP** за каждую дешифровку.\n"
    "• **Дешифровка** доступна каждые **30 минут**. Это ритм, который держит твой мозг в тонусе.\n"
    "• **STREAK (Серия):** Заходи каждый день, чтобы растить множитель награды. Пропуск дня обнуляет серию.\n\n"
    "**3. УРОВНИ ДОСТУПА:**\n"
    "• **LVL 1 (Неофит):** Доступ к базовым истинам.\n"
    "• **LVL 2 (Искатель):** 100 XP. Открывает выбор Фракций.\n"
    "• **LVL 3 (Оператор):** 350 XP. Доступ к инсайдам с закрытых форумов.\n"
    "• **LVL 4 (Архитектор):** 850 XP. Элитный контент и управление реальностью.\n\n"
    "**4. ФРАКЦИИ (ПУТИ РАЗВИТИЯ):**\n"
    "• 🔴 **ХИЩНИК:** Психология продаж, переговоры, захват ресурсов.\n"
    "• 🔵 **МИСТИК:** НЛП, чтение людей, социальная инженерия.\n"
    "• 🟣 **ТЕХНОЖРЕЦ:** Нейросети, автоматизация, заработок на ИИ.\n\n"
    "/// *Используй меню, чтобы управлять своей эволюцией.*"
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК: АРТЕФАКТЫ**\n\n"
    "Здесь ты меняешь накопленный SYNC на преимущество перед системой.\n\n"
    f"❄️ **КРИО-КАПСУЛА ({PRICES['cryo']} XP)**\n"
    "**Зачем:** Жизнь непредсказуема. Если ты не сможешь зайти в бот (уехал, заболел), капсула сгорит вместо твоего Стрика. Твои бонусы сохранятся.\n"
    "_Лимит: Можно иметь до 5 штук в запасе._\n\n"
    f"⚡️ **НЕЙРО-УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\n"
    "**Зачем:** Включает режим «Форсаж» на 24 часа. Время ожидания сокращается с 30 до **15 минут**. Идеально для быстрого фарма уровней в выходные.\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\n"
    "**Зачем:** Хакерский взлом. Позволяет получить информацию, которая доступна только на уровень выше твоего. Узнай секреты Архитекторов, будучи Неофитом.\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**\n"
    "**Зачем:** Если ты понял, что путь Хищника не для тебя, ты можешь перепрошить нейроны и стать Техножрецом. Прогресс сохраняется."
)

SYNDICATE_FULL = (
    "**🔗 СИНДИКАТ: ТВОЯ ПАССИВНАЯ ИМПЕРИЯ**\n\n"
    "В одиночку ты — просто юнит. Вместе — сеть.\n"
    "Мы платим тебе за расширение нашей Системы.\n\n"
    "**ТВОИ ВЫГОДЫ:**\n"
    f"1. 🎁 **МГНОВЕННЫЙ БОНУС:** Получи **+{REFERRAL_BONUS} XP** сразу, как только твой реферал нажмет /start.\n"
    "2. 📈 **ВЕЧНЫЙ ПРОЦЕНТ:** Ты будешь получать **10%** от всего опыта, который зарабатывают твои люди. Если они качаются — ты растешь автоматически.\n\n"
    "**КАК ЭТО РАБОТАЕТ:**\n"
    "Отправь ссылку другу. Как только он активирует нейро-интерфейс, он навсегда закрепляется в твоем Синдикате."
)

LEVEL_UP_MSG = {
    2: "🔓 **LVL 2**: Доступ к инструментам Влияния открыт.",
    3: "🔓 **LVL 3**: Статус Оператора. Вижу структуру матрицы.",
    4: "👑 **LVL 4**: Ты — Архитектор. Твоя воля — закон."
}

# --- 4. БАЗА ДАННЫХ (ГИБРИДНАЯ СИСТЕМА) ---
def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        # 1. Подключение к Google Sheets (для чтения Контента)
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            ws_content = sh.worksheet("Content")
            records = ws_content.get_all_records()
            CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
            for r in records:
                path, text, lvl = str(r.get('Path', 'general')).lower(), r.get('Text', ''), int(r.get('Level', 1))
                r_type = str(r.get('Type', '')).lower()
                if text:
                    if r_type == 'signal': 
                        CONTENT_DB["signals"].append(text)
                    else:
                        if path not in CONTENT_DB: path = "general"
                        if lvl not in CONTENT_DB[path]: CONTENT_DB[path][lvl] = []
                        CONTENT_DB[path][lvl].append(text)
            
            # 2. Подключение к PostgreSQL (Для пользователей)
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            # Создаем таблицу, если её нет
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, signup_date TEXT,
                    path TEXT DEFAULT 'general', xp INT DEFAULT 0, level INT DEFAULT 1,
                    streak INT DEFAULT 1, last_active TEXT, prestige INT DEFAULT 0,
                    cryo INT DEFAULT 0, accel INT DEFAULT 0, decoder INT DEFAULT 0,
                    accel_exp FLOAT DEFAULT 0, referrer TEXT,
                    last_protocol_time FLOAT DEFAULT 0, last_signal_time FLOAT DEFAULT 0
                );
            """)
            conn.commit()
            
            # Загружаем кэш из SQL
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            USER_CACHE.clear()
            for r in rows:
                USER_CACHE[r[0]] = {
                    "path": r[4], "xp": r[5], "level": r[6], "streak": r[7], "last_active": r[8],
                    "prestige": r[9], "cryo": r[10], "accel": r[11], "decoder": r[12],
                    "accel_exp": r[13], "referrer": r[14], "last_protocol_time": r[15],
                    "last_signal_time": r[16], "notified": True
                }
            cur.close()
            conn.close()
            print("/// DB CONNECTED (SQL + SHEETS)")
            
    except Exception as e: print(f"/// DB ERROR: {e}")

connect_db()

# --- 5. ФУНКЦИИ ЯДРА (ОБНОВЛЕНЫ ПОД SQL) ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def sql_update(uid):
    """Фоновое сохранение юзера в SQL"""
    def task():
        u = USER_CACHE.get(uid)
        if not u: return
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                UPDATE users SET path=%s, xp=%s, level=%s, streak=%s, last_active=%s, prestige=%s, 
                cryo=%s, accel=%s, decoder=%s, accel_exp=%s, last_protocol_time=%s, last_signal_time=%s
                WHERE uid=%s
            """, (u['path'], u['xp'], u['level'], u['streak'], u['last_active'], u['prestige'],
                  u['cryo'], u['accel'], u['decoder'], u['accel_exp'], u['last_protocol_time'], u['last_signal_time'], uid))
            conn.commit()
            conn.close()
        except Exception as e: print(f"SQL UPDATE ERR: {e}")
    threading.Thread(target=task).start()

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today, yesterday = datetime.now().strftime("%Y-%m-%d"), (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus, s_msg = 0, None
        
        # Стрик
        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5; s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН."
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else: u['streak'] = 1; bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        
        u['last_active'] = today
        total = amount + bonus
        u['xp'] += total
        
        # Реферал 10%
        if u.get('referrer') and str(u['referrer']).isdigit() and int(u['referrer']) in USER_CACHE:
            rid = int(u['referrer'])
            USER_CACHE[rid]['xp'] += max(1, int(total*0.1)); sql_update(rid)
        
        old_lvl = u['level']
        for lvl, threshold in sorted(LEVELS.items(), reverse=True):
            if u['xp'] >= threshold:
                u['level'] = lvl
                break
        
        sql_update(uid)
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
        txt = random.choice(pool) if pool else "/// НЕТ ДАННЫХ"
        school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
        res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC {use_dec_text}"
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
                cd = COOLDOWN_ACCEL if u.get('accel_exp', 0) > now else COOLDOWN_BASE
                if u.get('last_protocol_time', 0) > 0 and (now - u['last_protocol_time'] >= cd) and not u.get('notified', True):
                    try:
                        bot.send_message(uid, "⚡️ **СИСТЕМА ГОТОВА.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
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
    # КНОПКА СИГНАЛ ДОБАВЛЕНА
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
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
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
    ref_arg = None
    if len(m.text.split()) > 1:
        ref_arg = m.text.split()[1] 

    if uid not in USER_CACHE:
        start_xp = 50 if ref_arg == 'inst' else 0
        USER_CACHE[uid] = {
            "path": "general", "xp": start_xp, "level": 1, "streak": 1, 
            "last_active": datetime.now().strftime("%Y-%m-%d"),
            "prestige": 0, "cryo": 0, "accel": 0, "decoder": 0, "accel_exp": 0, 
            "referrer": ref_arg, "last_protocol_time": 0, "last_signal_time": 0, 
            "notified": True, "row_id": 0
        }
        # СОХРАНЯЕМ СРАЗУ В SQL
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (uid, username, first_name, signup_date, path, xp, referrer, last_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING
            """, (uid, m.from_user.username, m.from_user.first_name, datetime.now(), 'general', start_xp, ref_arg, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
        except: pass
        
        if ref_arg and ref_arg.isdigit() and int(ref_arg) in USER_CACHE:
            USER_CACHE[int(ref_arg)]['xp'] += REFERRAL_BONUS; sql_update(int(ref_arg))
            try: bot.send_message(int(ref_arg), f"🎁 **УЗЕЛ ВЕРБОВАН.** (+{REFERRAL_BONUS} XP)")
            except: pass
            
    welcome = "/// EIDOS-OS: СИНХРОНИЗИРОВАН."
    if ref_arg == 'inst': welcome = "🧬 **INSTAGRAM-БОНУС:** +50 XP."
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome, reply_markup=get_main_menu(uid))

# --- СКРИПТ МИГРАЦИИ (ВСТРОЕННАЯ КОМАНДА) ---
@bot.message_handler(commands=['migration_start'])
def migration_handler(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(m.chat.id, "⏳ НАЧИНАЮ ПЕРЕНОС ДАННЫХ ИЗ ГУГЛ ТАБЛИЦЫ В POSTGRES...")
        try:
            # 1. Читаем Гугл
            creds = json.loads(GOOGLE_JSON)
            gc = gspread.service_account_from_dict(creds)
            rows = gc.open(SHEET_NAME).worksheet("Users").get_all_values()[1:] # Пропускаем заголовок
            
            # 2. Пишем в SQL
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            count = 0
            for r in rows:
                try:
                    # Маппинг полей (UID, Username, Name, Date, Path, XP, Lvl, Streak, LastAct, Prest, Cryo, Accel, Dec, AccExp, Ref)
                    uid = int(r[0])
                    cur.execute("""
                        INSERT INTO users (uid, username, first_name, signup_date, path, xp, level, streak, last_active, prestige, cryo, accel, decoder, accel_exp, referrer)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uid) DO NOTHING
                    """, (uid, r[1], r[2], r[3], r[4], int(r[5]), int(r[6]), int(r[7]), r[8], int(r[9]), int(r[10]), int(r[11]), int(r[12]), float(r[13]), r[14]))
                    count += 1
                except: pass
            conn.commit()
            conn.close()
            connect_db() # Перезагружаем кэш бота
            bot.send_message(m.chat.id, f"✅ УСПЕШНО. Перенесено {count} пользователей. Теперь бот работает на базе PostgreSQL.")
        except Exception as e:
            bot.send_message(m.chat.id, f"❌ ОШИБКА: {e}")

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': 
            connect_db(); bot.send_message(message.chat.id, "✅ БД ОБНОВЛЕНА.")
        elif message.text and message.text.startswith('/telegraph '):
            parts = message.text.split(maxsplit=2)
            if len(parts) >= 2:
                url = parts[1]
                if "google.com" in url: url = url.split("q=")[1].split("&")[0] # Чистим ссылку
                text = parts[2] if len(parts) > 2 else "/// НОВЫЕ ДАННЫЕ В СЕТИ"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📂 ОТКРЫТЬ ДОСЬЕ", url=url))
                markup.add(types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=signal"))
                bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
                bot.send_message(message.chat.id, "✅ TELEGRAPH ПОСТ ОТПРАВЛЕН.")
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ПОЛУЧИТЬ СИНХРОН", url=f"https://t.me/{BOT_USERNAME}?start=channel_post"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ ТЕКСТ ОТПРАВЛЕН.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE:
        bot.answer_callback_query(call.id, "⚠️ ОШИБКА ДОСТУПА. Нажми /start", show_alert=True)
        return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ **АДМИН-ПАНЕЛЬ**\n\nКоманды:\n`/migration_start` - перенос БД", get_admin_menu())
    elif call.data == "admin_refresh" and uid == ADMIN_ID: connect_db(); bot.answer_callback_query(call.id, "✅ OK")
    elif call.data == "admin_stats" and uid == ADMIN_ID: bot.answer_callback_query(call.id, f"📊 Узлов: {len(USER_CACHE)}", show_alert=True)

    elif call.data == "get_protocol":
        # Логика ускорителя
        is_accel = u.get('accel_exp', 0) > now_ts
        cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
        
        if now_ts - u.get('last_protocol_time', 0) < cd:
            rem = int((cd - (now_ts - u.get('last_protocol_time', 0))) / 60)
            bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
        
        if call.message.chat.id < 0: bot.answer_callback_query(call.id, "🧬 ОТПРАВЛЕНО В ЛС")
        
        u['last_protocol_time'], u['notified'] = now_ts, False
        up, s_msg, total = add_xp(uid, XP_GAIN)
        use_dec = "(+🔑)" if u['decoder'] > 0 else ""
        target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
        if u['decoder'] > 0: u['decoder'] -= 1
        if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 УРОВЕНЬ ПОВЫШЕН!"))
        threading.Thread(target=decrypt_and_send, args=(uid, uid, target_lvl, use_dec)).start()

    # --- ЛОГИКА СИГНАЛА ---
    elif call.data == "get_signal":
        if now_ts - u.get('last_signal_time', 0) < COOLDOWN_SIGNAL:
            rem = int((COOLDOWN_SIGNAL - (now_ts - u.get('last_signal_time', 0))) / 60)
            bot.answer_callback_query(call.id, f"📡 СИГНАЛ СЛАБЫЙ. Жди {rem} мин.", show_alert=True); return
        
        u['last_signal_time'] = now_ts
        up, s_msg, total = add_xp(uid, XP_SIGNAL)
        sql_update(uid) # Сохраняем таймер
        
        txt = random.choice(CONTENT_DB["signals"]) if CONTENT_DB["signals"] else "/// ЭФИР ПУСТ. СКОРО БУДЕТ."
        bot.send_message(uid, f"📶 **ВХОДЯЩИЙ СИГНАЛ**\n\n{txt}\n\n⚡️ +{XP_SIGNAL} XP")

    elif call.data == "profile":
        stars = "★" * u['prestige']
        title = TITLES.get(u['level'], "НЕОФИТ")
        path_name = u['path'].upper() if u['path'] != 'general' else "БАЗОВЫЙ"
        progress = get_progress_bar(u['xp'], u['level'])
        ref_count = sum(1 for user in USER_CACHE.values() if user.get('referrer') == str(uid))
        
        accel_status = "АКТИВЕН" if u.get('accel_exp', 0) > now_ts else "НЕТ"

        msg = (
            f"👤 **НЕЙРО-ПРОФИЛЬ** {stars}\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔰 **СТАТУС:** {title} [{path_name}]\n"
            f"🔋 **SYNC:** {u['xp']} XP\n"
            f"{progress}\n\n"
            f"🔗 **ВЕРБОВАНО УЗЛОВ:** {ref_count}\n"
            f"🔥 **ЧИСТОТА СИГНАЛА:** {u['streak']} дн.\n"
            f"━━━━━━━━━━━━━━\n"
            f"🎒 **ИНВЕНТАРЬ:**\n❄️ Крио: {u['cryo']}\n⚡️ Ускоритель: {accel_status}\n🔑 Дешифратор: {u['decoder']}"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        if u['accel'] > 0 and u.get('accel_exp', 0) < now_ts: markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ РАЗГОН", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton(f"⚙️ СМЕНИТЬ ВЕКТОР (-{PATH_CHANGE_COST} XP)", callback_data="change_path_confirm"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)

    elif call.data == "shop":
        safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton(f"❄️ КУПИТЬ", callback_data="buy_cryo"),
            types.InlineKeyboardButton(f"⚡️ КУПИТЬ", callback_data="buy_accel"),
            types.InlineKeyboardButton(f"🔑 КУПИТЬ", callback_data="buy_decoder"),
            types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
        ))

    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            u['xp'] -= PRICES[item]; u[item] += 1; sql_update(uid)
            bot.answer_callback_query(call.id, f"✅ КУПЛЕНО")
            safe_edit(call, SHOP_FULL, get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

    elif call.data == "referral":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        safe_edit(call, f"{SYNDICATE_FULL}\n`{link}`", get_main_menu(uid))

    elif call.data == "change_path_confirm":
        safe_edit(call, f"⚠️ Смена Вектора: -{PATH_CHANGE_COST} XP.", get_path_menu(cost_info=True))

    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
            if u['path'] != 'general' and u['path'] != new_path: u['xp'] -= PATH_CHANGE_COST
            u['path'] = new_path; sql_update(uid)
            bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} АКТИВИРОВАН.", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

    elif call.data == "use_accel":
        if u['accel'] > 0:
            u['accel'] -= 1; u['accel_exp'] = now_ts + 86400; sql_update(uid)
            bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН.", reply_markup=get_main_menu(uid))

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))

    elif call.data == "guide": safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))
    try: bot.answer_callback_query(call.id)
    except: pass

# --- 10. ЗАПУСК ---
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    return 'Alive', 200

@app.route('/health')
def health_check(): return 'OK', 200

if __name__ == "__main__":
    if WEBHOOK_URL: 
        bot.remove_webhook(); time.sleep(1); bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=notification_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
