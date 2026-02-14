import telebot
from telebot import types
import flask
import os
import time
import random
import psycopg2
from psycopg2.extras import RealDictCursor
import threading
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
DATABASE_URL = os.environ.get('DATABASE_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800      # 30 мин (Синхрон)
COOLDOWN_ACCEL = 900      # 15 мин (Ускоритель)
COOLDOWN_SIGNAL = 300     # 5 мин (Сигнал)
XP_GAIN = 25              # Синхрон
XP_SIGNAL = 15            # Сигнал
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. ТЕКСТОВЫЕ МОДУЛИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v20.1**\n\n"
    "**1. ИСТОЧНИКИ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы. Награда: **25 XP**.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие ментальные импульсы. Награда: **15 XP**.\n\n"
    "**2. СИСТЕМА STREAK (СЕРИЯ):**\n"
    "Каждый день непрерывного входа увеличивает награду за Синхрон на **+5 XP**.\n"
    "Пропуск дня сжигает серию (если нет Крио-капсулы).\n\n"
    "**3. УРОВНИ ДОСТУПА:**\n"
    "• **LVL 1 (100 XP):** База.\n"
    "• **LVL 2 (500 XP):** Фракции.\n"
    "• **LVL 3 (1500 XP):** Инсайды.\n"
    "• **LVL 4 (3000 XP):** Архитектор."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО ({PRICES['cryo']} XP)**\nСтраховка серии при пропуске дня.\n\n"
    f"⚡️ **УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nСнижает ожидание Синхрона до 15 мин на 24 часа.\n*(Требует активации в Профиле после покупки)*\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nВзлом уровня доступа.Даёт знания уровнем выше\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

SYNDICATE_FULL = (
    "**🔗 СИНДИКАТ**\n\n"
    f"1. 🎁 **БОНУС:** +{REFERRAL_BONUS} XP за реферала.Приведи друга и раскачайся\n"
    "2. 📈 **РОЯЛТИ:** 10% от опыта твоей сети пожизненно."
)

LEVEL_UP_MSG = {
    2: "🔓 **LVL 2**: Доступ к секретам 2 уровня открыт.",
    3: "🔓 **LVL 3**: Статус Оператора.Знания синхрона будут богаче",
    4: "👑 **LVL 4**: Ты — Архитектор.Уровень знаний будет высоким"
}

# --- 4. БАЗА ДАННЫХ ---
def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"/// DB CONNECTION ERROR: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        # Основная таблица пользователей
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                path TEXT DEFAULT 'general',
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                streak INTEGER DEFAULT 1,
                last_active DATE DEFAULT CURRENT_DATE,
                prestige INTEGER DEFAULT 0,
                cryo INTEGER DEFAULT 0,
                accel INTEGER DEFAULT 0,
                decoder INTEGER DEFAULT 0,
                accel_exp BIGINT DEFAULT 0,
                referrer TEXT,
                last_protocol_time BIGINT DEFAULT 0,
                last_signal_time BIGINT DEFAULT 0
            );
        ''')
        # Таблица контента
        cur.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id SERIAL PRIMARY KEY,
                type TEXT,
                path TEXT,
                text TEXT,
                level INTEGER DEFAULT 1
            );
        ''')
        # ПАТЧ: Автоматическое добавление колонки notified, если её нет
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;")
            conn.commit()
            print("/// DB PATCH: COLUMN 'notified' VERIFIED/ADDED.")
        except Exception as patch_e:
            print(f"/// DB PATCH WARNING: {patch_e}")
            conn.rollback()

        conn.commit()
        print("/// DB STRUCTURE VERIFIED.")
    except Exception as e:
        print(f"/// DB INIT ERROR: {e}")
    finally:
        if conn: conn.close()

# --- HELPER FUNCTIONS ---
def get_user_from_db(uid):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
        user = cur.fetchone()
        return user
    finally:
        conn.close()

def update_user_db(uid, **kwargs):
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [uid]
        cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", values)
        conn.commit()
    finally:
        conn.close()

def register_user_db(uid, username, first_name, referrer):
    conn = get_db_connection()
    if not conn: return
    try:
        start_xp = 50 if referrer == 'inst' else 0
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (uid, username, first_name, referrer, xp, last_active)
            VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (uid) DO NOTHING
        ''', (uid, f"@{username}", first_name, str(referrer or ''), start_xp))
        conn.commit()
    finally:
        conn.close()

def get_referral_count(uid):
    conn = get_db_connection()
    if not conn: return 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),))
        return cur.fetchone()[0]
    except: return 0
    finally: conn.close()

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

def process_xp_logic(uid, amount, is_sync=False):
    u = get_user_from_db(uid)
    if not u: return False, None, 0
    
    today = datetime.now().date()
    if isinstance(u['last_active'], str):
        last_active_date = datetime.strptime(u['last_active'], "%Y-%m-%d").date()
    else:
        last_active_date = u['last_active']
    
    streak_bonus = 0
    s_msg = None
    
    if last_active_date < today:
        if (today - last_active_date).days == 1:
            new_streak = u['streak'] + 1
            streak_bonus = new_streak * 5
            s_msg = f"🔥 СЕРИЯ: {new_streak} ДН."
        else:
            if u['cryo'] > 0:
                new_streak = u['streak']
                update_user_db(uid, cryo=u['cryo'] - 1)
                s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else:
                new_streak = 1
                streak_bonus = 5
                s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        update_user_db(uid, streak=new_streak, last_active=today)
    else:
        new_streak = u['streak']

    total_xp = amount + streak_bonus
    new_total_xp = u['xp'] + total_xp
    
    if u['referrer'] and u['referrer'].isdigit():
        ref_id = int(u['referrer'])
        ref_user = get_user_from_db(ref_id)
        if ref_user:
            bonus = max(1, int(total_xp * 0.1))
            update_user_db(ref_id, xp=ref_user['xp'] + bonus)

    old_lvl = u['level']
    new_lvl = old_lvl
    for lvl, threshold in sorted(LEVELS.items(), reverse=True):
        if new_total_xp >= threshold:
            new_lvl = lvl
            break
            
    update_user_db(uid, xp=new_total_xp, level=new_lvl)
    return (new_lvl > old_lvl), s_msg, total_xp

def get_content(c_type, path, level):
    conn = get_db_connection()
    if not conn: return "/// ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ ЗНАНИЙ"
    try:
        cur = conn.cursor()
        if c_type == 'signal':
             cur.execute("SELECT text FROM content WHERE type = 'signal' ORDER BY RANDOM() LIMIT 1")
        else:
            cur.execute("""
                SELECT text FROM content 
                WHERE type = 'protocol' AND (path = %s OR path = 'general') AND level <= %s 
                ORDER BY RANDOM() LIMIT 1
            """, (path, level))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

# --- 6. ПУШИ ---
def notification_worker():
    while True:
        try:
            time.sleep(60)
            conn = get_db_connection()
            if not conn: continue
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE notified = FALSE")
            users = cur.fetchall()
            now = time.time()
            for u in users:
                cd = COOLDOWN_ACCEL if u['accel_exp'] > now else COOLDOWN_BASE
                if u['last_protocol_time'] > 0 and (now - u['last_protocol_time'] >= cd):
                    try:
                        bot.send_message(u['uid'], "⚡️ **СИСТЕМА ГОТОВА.**\nПротокол восстановлен.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        update_user_db(u['uid'], notified=True)
                    except: pass
            conn.close()
        except Exception as e:
            print(f"WORKER ERROR: {e}")

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
        types.InlineKeyboardButton("➕ ДОБАВИТЬ СИГНАЛ", callback_data="adm_add_signal"),
        types.InlineKeyboardButton("➕ ДОБАВИТЬ ПРОТОКОЛ", callback_data="adm_add_proto"),
        types.InlineKeyboardButton("👁 ПРОСМОТР ЮЗЕРА (ID)", callback_data="adm_view_user"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"),
        types.InlineKeyboardButton("🎁 НАЧИСЛИТЬ ВСЕМ БОНУС", callback_data="admin_bonus"),
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
    u = get_user_from_db(uid)
    if not u:
        register_user_db(uid, m.from_user.username, m.from_user.first_name, ref_arg)
        if ref_arg and ref_arg.isdigit():
            ref_id = int(ref_arg)
            ref_u = get_user_from_db(ref_id)
            if ref_u:
                update_user_db(ref_id, xp=ref_u['xp'] + REFERRAL_BONUS)
                try: bot.send_message(ref_id, f"🎁 **НОВЫЙ УЗЕЛ.** +{REFERRAL_BONUS} XP.")
                except: pass
    welcome_msg = "/// EIDOS-OS: СИНХРОНИЗИРОВАН."
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

user_action_state = {} 

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and user_action_state.get(ADMIN_ID))
def admin_steps(m):
    state = user_action_state[ADMIN_ID]
    if state['step'] == 'wait_signal_text':
        conn = get_db_connection()
        cur = conn.cursor(); cur.execute("INSERT INTO content (type, path, text, level) VALUES ('signal', 'general', %s, 1)", (m.text,)); conn.commit(); conn.close()
        bot.send_message(ADMIN_ID, "✅ **СИГНАЛ ЗАГРУЖЕН.**"); user_action_state.pop(ADMIN_ID)
    elif state['step'] == 'wait_proto_text':
        try:
            path, level, text = m.text.split('|', 2)
            conn = get_db_connection(); cur = conn.cursor(); cur.execute("INSERT INTO content (type, path, text, level) VALUES ('protocol', %s, %s, %s)", (path.strip(), text.strip(), int(level))); conn.commit(); conn.close()
            bot.send_message(ADMIN_ID, f"✅ **ПРОТОКОЛ ЗАГРУЖЕН.**")
        except: bot.send_message(ADMIN_ID, "❌ Формат: `path|level|text`")
        user_action_state.pop(ADMIN_ID)
    elif state['step'] == 'wait_user_id':
        uid_target = int(m.text) if m.text.isdigit() else 0
        u = get_user_from_db(uid_target)
        if u: bot.send_message(ADMIN_ID, f"👤 **ID:** `{u['uid']}`\nName: {u['username']}\nXP: {u['xp']} | LVL: {u['level']}\nPath: {u['path']}")
        else: bot.send_message(ADMIN_ID, "❌ Не найден.")
        user_action_state.pop(ADMIN_ID)

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': init_db(); bot.send_message(message.chat.id, "✅ БД Проверена.")
        elif message.text and message.text.startswith('/ban '): 
            try:
                target_id = int(message.text.split()[1])
                conn = get_db_connection(); cur = conn.cursor(); cur.execute("DELETE FROM users WHERE uid = %s", (target_id,)); conn.commit(); conn.close()
                bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} УДАЛЕН.")
            except: bot.send_message(message.chat.id, "❌ Ошибка ID.")
        elif message.text and message.text.startswith('/give_xp '):
            try:
                _, t_id, amount = message.text.split()
                t_id, amount = int(t_id), int(amount)
                u = get_user_from_db(t_id)
                if u: update_user_db(t_id, xp=u['xp'] + amount); bot.send_message(t_id, f"⚡️ +{amount} XP."); bot.send_message(message.chat.id, "✅")
            except: bot.send_message(message.chat.id, "❌ /give_xp ID СУММА")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    u = get_user_from_db(uid)
    if not u: bot.answer_callback_query(call.id, "⚠️ Нажми /start"); return
    now_ts = time.time()
    try:
        if call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ**", get_admin_menu())
        elif call.data == "adm_add_signal" and uid == ADMIN_ID: user_action_state[uid] = {'step': 'wait_signal_text'}; bot.send_message(uid, "✍️ Текст сигнала:")
        elif call.data == "adm_add_proto" and uid == ADMIN_ID: user_action_state[uid] = {'step': 'wait_proto_text'}; bot.send_message(uid, "✍️ `path|level|text`:")
        elif call.data == "adm_view_user" and uid == ADMIN_ID: user_action_state[uid] = {'step': 'wait_user_id'}; bot.send_message(uid, "🔎 Введи ID:")
        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            conn = get_db_connection(); cur = conn.cursor(); cur.execute("UPDATE users SET xp = xp + 100"); count = cur.rowcount; conn.commit(); conn.close()
            bot.answer_callback_query(call.id, f"🎁 Выдано {count} узлам")
        elif call.data == "admin_stats" and uid == ADMIN_ID:
            conn = get_db_connection(); cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]; conn.close()
            bot.answer_callback_query(call.id, f"📊 Узлов: {total}", show_alert=True)
        elif call.data == "get_protocol":
            cd = COOLDOWN_ACCEL if u['accel_exp'] > now_ts else COOLDOWN_BASE
            if now_ts - u['last_protocol_time'] < cd:
                rem = int((cd - (now_ts - u['last_protocol_time'])) / 60); bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
            update_user_db(uid, last_protocol_time=int(now_ts), notified=False)
            up, s_msg, total = process_xp_logic(uid, XP_GAIN, is_sync=True)
            u = get_user_from_db(uid)
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: update_user_db(uid, decoder=u['decoder'] - 1)
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 LEVEL UP!"))
            def dec_task():
                status_msg = bot.send_message(uid, "📡 **ИНИЦИАЛИЗАЦИЯ...**"); time.sleep(1)
                bot.edit_message_text(f"🔓 **ДЕШИФРОВКА... 84%**", uid, status_msg.message_id)
                time.sleep(0.8); txt = get_content('protocol', u['path'], target_lvl) or "/// НЕТ ДАННЫХ."
                res = f"🧬 **{SCHOOLS.get(u['path'], 'ОБЩИЙ КАНАЛ')}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
                bot.edit_message_text(res, uid, status_msg.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
            threading.Thread(target=dec_task).start()
        elif call.data == "get_signal":
            if now_ts - u['last_signal_time'] < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u['last_signal_time'])) / 60); bot.answer_callback_query(call.id, f"📡 Жди {rem} мин.", show_alert=True); return
            update_user_db(uid, last_signal_time=int(now_ts))
            process_xp_logic(uid, XP_SIGNAL); txt = get_content('signal', 'general', 1) or "/// ЭФИР ПУСТ."
            bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
        elif call.data == "profile":
            u = get_user_from_db(uid)
            ref_count = get_referral_count(uid)
            msg = (f"👤 **НЕЙРО-ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n🔰 **СТАТУС:** {TITLES.get(u['level'], 'НЕОФИТ')}\n⚔️ **ФРАКЦИЯ:** {SCHOOLS.get(u['path'], 'ОБЩИЙ')}\n🔋 **SYNC:** {u['xp']} XP\n{get_progress_bar(u['xp'], u['level'])}\n🔥 **STREAK:** {u['streak']} дн.\n👥 **СЕТЬ:** {ref_count} узлов\n━━━━━━━━━━━━━━\n🎒 **ИНВЕНТАРЬ:**\n❄️ Крио: {u['cryo']}\n⚡️ Ускоритель: {'✅' if u['accel_exp'] > now_ts else '❌'}\n🔑 Дешифратор: {u['decoder']}")
            markup = types.InlineKeyboardMarkup(row_width=1)
            if u['accel'] > 0 and u['accel_exp'] < now_ts: markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ВЕКТОР", callback_data="change_path_confirm"), types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)
        elif call.data == "back_to_menu":
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))
        elif call.data == "shop": safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("❄️ КРИО (200 XP)", callback_data="buy_cryo"), types.InlineKeyboardButton("⚡️ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"), types.InlineKeyboardButton("🔑 ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"), types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))
        elif call.data.startswith("buy_"):
            item = call.data.split("_")[1]
            if u['xp'] >= PRICES[item]:
                update_user_db(uid, xp=u['xp'] - PRICES[item]); conn = get_db_connection(); cur = conn.cursor(); cur.execute(f"UPDATE users SET {item} = {item} + 1 WHERE uid = %s", (uid,)); conn.commit(); conn.close()
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
        elif call.data == "referral": safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ССЫЛКА:**\n`https://t.me/{BOT_USERNAME}?start={uid}`", get_main_menu(uid))
        elif call.data == "change_path_confirm": safe_edit(call, f"⚠️ **СМЕНА ФРАКЦИИ** (100 XP)", get_path_menu(cost_info=True))
        elif "set_path_" in call.data:
            new_path = call.data.split("_")[-1]
            if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
                if u['path'] != 'general' and u['path'] != new_path: update_user_db(uid, xp=u['xp'] - PATH_CHANGE_COST)
                update_user_db(uid, path=new_path); bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
        elif call.data == "use_accel":
            if u['accel'] > 0: update_user_db(uid, accel=u['accel'] - 1, accel_exp=int(now_ts + 86400)); bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕТ УСКОРИТЕЛЯ", show_alert=True)
        elif call.data == "guide": safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except Exception as e: print(f"/// CALLBACK ERROR: {e}")

# --- 9. ЗАПУСК И МАРШРУТЫ ---
@app.route('/health', methods=['GET'])
def health_check(): return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try: bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))]); return 'OK', 200
        except Exception as e: print(f"/// WEBHOOK ERROR: {e}"); return 'Error', 500
    return 'Eidos SQL Operating', 200

def system_startup():
    with app.app_context():
        time.sleep(2); print("/// STARTUP..."); init_db()
        if WEBHOOK_URL:
            try: bot.remove_webhook(); bot.set_webhook(url=WEBHOOK_URL); print("/// WEBHOOK OK")
            except Exception as e: print(f"/// WH ERROR: {e}")
        notification_worker()

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
