import telebot
from telebot import types
import flask
import os
import time
import random
import json
import threading
import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
# ИСПОЛЬЗУЕМ ТОЛЬКО SQL
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800     # 30 мин (Синхрон)
COOLDOWN_ACCEL = 900     # 15 мин (Ускоритель)
COOLDOWN_SIGNAL = 300    # 5 мин (Сигнал)
XP_GAIN = 25             # За Синхрон
XP_SIGNAL = 15           # За Сигнал
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ (СОХРАНЕНО КАК ТЫ ПРОСИЛ) ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# ПОДКЛЮЧЕНИЕ К SQL
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("/// SQL ENGINE: ONLINE")
except Exception as e:
    print(f"/// SQL ERROR: {e}")

# Хранилище контента (Так как гугл отключен, тексты нужно будет заливать в SQL или держать тут)
CONTENT_DB = {
    "money": [], 
    "mind": [], 
    "tech": [], 
    "general": ["/// ПРОТОКОЛ: Инициализация сознания.", "/// ПРОТОКОЛ: Очисти кеш реальности."], 
    "signals": ["/// СИГНАЛ: Действуй.", "/// СИГНАЛ: Наблюдай.", "/// СИГНАЛ: Тишина."]
}
USER_CACHE = {} 

# --- 3. ТЕКСТОВЫЕ МОДУЛИ (СОХРАНЕНО) ---
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

# --- 4. БАЗА ДАННЫХ (ЧИСТЫЙ SQL) ---

def init_db():
    """Инициализация таблиц и загрузка кэша"""
    conn = db_pool.getconn()
    try:
        cur = conn.cursor()
        # Создаем таблицу, если нет
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                signup_date TEXT,
                path TEXT DEFAULT 'general',
                xp INT DEFAULT 0,
                level INT DEFAULT 1,
                streak INT DEFAULT 1,
                last_active TEXT,
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
        
        # Загрузка пользователей в оперативную память
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
        print(f"/// SYSTEM READY. Loaded {len(USER_CACHE)} users.")
    except Exception as e:
        print(f"/// INIT ERROR: {e}")
    finally:
        db_pool.putconn(conn)

init_db()

# --- 5. ФУНКЦИИ ЯДРА ---

def sql_exec(query, params):
    """Асинхронное выполнение SQL-запросов"""
    def task():
        conn = db_pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
        except Exception as e: print(f"SQL ERROR: {e}")
        finally: db_pool.putconn(conn)
    threading.Thread(target=task).start()

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
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus = 0
        s_msg = None
        
        # Логика Стрика
        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5; s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН."
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else: u['streak'] = 1; bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        
        u['last_active'] = today
        total = amount + bonus 
        u['xp'] += total
        
        # Реферал 10%
        if u.get('referrer') and str(u['referrer']).isdigit():
            rid = int(u['referrer'])
            if rid in USER_CACHE:
                USER_CACHE[rid]['xp'] += max(1, int(total * 0.1))
                sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[rid]['xp'], rid))
            
        old_lvl = u['level']
        for lvl, threshold in sorted(LEVELS.items(), reverse=True):
            if u['xp'] >= threshold:
                u['level'] = lvl
                break
        
        # Сохранение в SQL
        sql_exec("""
            UPDATE users SET xp=%s, level=%s, streak=%s, last_active=%s, cryo=%s WHERE uid=%s
        """, (u['xp'], u['level'], u['streak'], u['last_active'], u['cryo'], uid))
        
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

def decrypt_and_send(chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    try:
        status_msg = bot.send_message(chat_id, "📡 **ИНИЦИАЛИЗАЦИЯ...**")
        time.sleep(1)
        bot.edit_message_text(f"🔓 **ДЕШИФРОВКА...**\n`[||||||||..] 84%`", chat_id, status_msg.message_id, parse_mode="Markdown")
        time.sleep(0.8)
        
        # Выбор контента (из локального словаря, т.к. гугл отключен)
        pool = CONTENT_DB.get(u['path'], []) + CONTENT_DB.get('general', [])
        txt = random.choice(pool) if pool else "/// НЕТ ДАННЫХ."
        
        school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
        res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} XP {use_dec_text}"
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
                # Проверка кулдауна с учетом ускорителя
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

    # Регистрация (КЭШ + SQL)
    if uid not in USER_CACHE:
        start_xp = 50 if ref_arg == 'inst' else 0
        USER_CACHE[uid] = {
            "path": "general", "xp": start_xp, "level": 1, "streak": 1, 
            "last_active": datetime.now().strftime("%Y-%m-%d"),
            "prestige": 0, "cryo": 0, "accel": 0, "decoder": 0, "accel_exp": 0, 
            "referrer": ref_arg, "last_protocol_time": 0, "last_signal_time": 0, "notified": True
        }
        # Пишем в SQL
        sql_exec("""
            INSERT INTO users (uid, username, first_name, signup_date, path, xp, referrer, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING
        """, (uid, m.from_user.username, m.from_user.first_name, datetime.now(), 'general', int(start_xp), ref_arg, datetime.now().strftime("%Y-%m-%d")))
        
        # Награда рефереру
        if ref_arg and ref_arg.isdigit() and int(ref_arg) in USER_CACHE:
            rid = int(ref_arg)
            USER_CACHE[rid]['xp'] += REFERRAL_BONUS
            sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[rid]['xp'], rid))
            try: bot.send_message(rid, f"🎁 **НОВЫЙ УЗЕЛ.** +{REFERRAL_BONUS} XP.")
            except: pass

    welcome_msg = "/// EIDOS-OS: СИНХРОНИЗИРОВАН."
    if ref_arg == 'inst': welcome_msg = "🧬 **СИГНАЛ ИЗ INSTAGRAM.**\nБонус +50 XP начислен."
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': 
            # Здесь только SQL, гугл отключен
            bot.send_message(message.chat.id, "✅ SQL БД В НОРМЕ.")
        
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
                    # Из SQL тоже можно удалить, но пока оставим только из кэша
                    bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} ОТКЛЮЧЕН.")
            except: bot.send_message(message.chat.id, "❌ Ошибка ID.")
        
        elif message.text and message.text.startswith('/give_xp '):
            try:
                _, t_id, amount = message.text.split()
                t_id, amount = int(t_id), int(amount)
                if t_id in USER_CACHE:
                    USER_CACHE[t_id]['xp'] += amount
                    sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[t_id]['xp'], t_id))
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
            safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ АРХИТЕКТОРА**\n\n`/ban ID`\n`/give_xp ID СУММА`\n`/telegraph ССЫЛКА ТЕКСТ`", get_admin_menu())
        
        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            count = 0
            for u_id in USER_CACHE:
                USER_CACHE[u_id]['xp'] += 100
                sql_exec("UPDATE users SET xp=%s WHERE uid=%s", (USER_CACHE[u_id]['xp'], u_id))
                count += 1
            bot.answer_callback_query(call.id, f"🎁 Выдано по 100 XP {count} узлам")

        elif call.data == "admin_refresh" and uid == ADMIN_ID: bot.answer_callback_query(call.id, "✅ OK")
        elif call.data == "admin_stats" and uid == ADMIN_ID:
            inst_users = sum(1 for user in USER_CACHE.values() if user.get('referrer') == 'inst')
            bot.answer_callback_query(call.id, f"📊 Узлы: {len(USER_CACHE)}\n📸 Instagram: {inst_users}", show_alert=True)

        elif call.data == "get_protocol":
            # --- ФИКС УСКОРИТЕЛЯ ---
            is_accel = u.get('accel_exp', 0) > now_ts
            cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
            
            if now_ts - u.get('last_protocol_time', 0) < cd:
                rem = int((cd - (now_ts - u.get('last_protocol_time', 0))) / 60)
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
            
            u['last_protocol_time'] = now_ts
            sql_exec("UPDATE users SET last_protocol_time=%s WHERE uid=%s", (now_ts, uid))
            
            up, s_msg, total = add_xp(uid, XP_GAIN)
            use_dec = "(+🔑)" if u['decoder'] > 0 else ""
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: u['decoder'] -= 1
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
            threading.Thread(target=decrypt_and_send, args=(uid, uid, target_lvl, use_dec)).start()

        # --- КНОПКА СИГНАЛ ---
        elif call.data == "get_signal":
            if now_ts - u.get('last_signal_time', 0) < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u.get('last_signal_time', 0))) / 60)
                msg_t = f"{rem} мин" if rem > 0 else "< 1 мин"
                bot.answer_callback_query(call.id, f"📡 ЖДИ: {msg_t}", show_alert=True); return
            
            u['last_signal_time'] = now_ts
            sql_exec("UPDATE users SET last_signal_time=%s WHERE uid=%s", (now_ts, uid))
            
            up, s_msg, total = add_xp(uid, XP_SIGNAL)
            
            txt = random.choice(CONTENT_DB["signals"]) if CONTENT_DB["signals"] else "/// СИГНАЛ НЕ НАЙДЕН."
            bot.send_message(uid, f"📶 **ПОЛУЧЕН СИГНАЛ**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP (+{u['streak']*5} Streak Bonus)", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

        elif call.data == "profile":
            title = TITLES.get(u['level'], "НЕОФИТ")
            progress = get_progress_bar(u['xp'], u['level'])
            ref_count = sum(1 for user in USER_CACHE.values() if str(user.get('referrer')) == str(uid))
            path_desc = "Не определен"
            if u['path'] == 'money': path_desc = "Искусство Влияния и Продаж"
            elif u['path'] == 'mind': path_desc = "Психология и Ментальные Ловушки"
            elif u['path'] == 'tech': path_desc = "ИИ-Инструменты и Автоматизация"
            elif u['path'] == 'general': path_desc = "Базовая Калибровка Сознания"
            
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
            if u['accel'] > 0 and u.get('accel_exp', 0) < now_ts:
                markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ВЕКТОР", callback_data="change_path_confirm"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

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
                u['xp'] -= PRICES[item]; u[item] += 1
                sql_exec(f"UPDATE users SET xp=%s, {item}=%s WHERE uid=%s", (u['xp'], u[item], uid))
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item.upper()}")
                safe_edit(call, SHOP_FULL, get_main_menu(uid))
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
                u['path'] = new_path
                sql_exec(f"UPDATE users SET xp=%s, path=%s WHERE uid=%s", (u['xp'], u['path'], uid))
                bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "use_accel":
            if u['accel'] > 0:
                u['accel'] -= 1; u['accel_exp'] = now_ts + 86400
                sql_exec("UPDATE users SET accel=%s, accel_exp=%s WHERE uid=%s", (u['accel'], u['accel_exp'], uid))
                bot.answer_callback_query(call.id, "✅ ВКЛЮЧЕНО (24ч)")
                callback.data = "profile"; callback(call)
            else: bot.answer_callback_query(call.id, "❌ НЕТ УСКОРИТЕЛЯ", show_alert=True)

        elif call.data == "guide": safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
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
