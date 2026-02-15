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
RAID_COST = 100           # Цена входа в Нулевой Слой
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# --- СИСТЕМА ДОСТИЖЕНИЙ ---
ACHIEVEMENTS_LIST = {
    "first_steps": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: u['xp'] >= 25, "xp": 50},
    "streak_7": {"name": "🔥 СТОИК (Неделя)", "cond": lambda u: u['streak'] >= 7, "xp": 150},
    "streak_30": {"name": "🧘 ЖЕЛЕЗНЫЙ МОНАХ", "cond": lambda u: u['streak'] >= 30, "xp": 500},
    "rich_1000": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200},
    "lvl_3": {"name": "🧠 ОПЕРАТОР (Lvl 3)", "cond": lambda u: u['level'] >= 3, "xp": 300},
    "diver_50": {"name": "🕳 СТАЛКЕР (Глубина 50)", "cond": lambda u: u.get('max_depth', 0) >= 50, "xp": 300}
}

# --- СЦЕНАРИИ РЕЙДА (НУЛЕВОЙ СЛОЙ) ---
RAID_SCENARIOS = [
    {"text": "Ты нашел кластер битых данных. Среди мусора мерцает энергия.", "type": "loot", "val": 30, "dmg": 0},
    {"text": "Системный Страж заметил твое присутствие! Удар током.", "type": "trap", "val": 0, "dmg": 15},
    {"text": "Тишина. Только гул серверов. Ты продвигаешься глубже.", "type": "empty", "val": 5, "dmg": 2},
    {"text": "Кэш удаленного аккаунта. Это чья-то стертая память.", "type": "loot", "val": 60, "dmg": 0},
    {"text": "ГЛИТЧ РЕАЛЬНОСТИ! Текстуры плывут. Ты теряешь связь.", "type": "trap", "val": 0, "dmg": 25},
    {"text": "Ты нашел «Безопасный Узел». Сигнал стабилизирован.", "type": "heal", "val": 10, "dmg": -20}
]

WELCOME_VARIANTS = [
    "/// EIDOS OS: ЗАГРУЗКА СОЗНАНИЯ...\nДобро пожаловать в тренажер реальности.",
    "/// ВНИМАНИЕ: Обнаружен потенциал.\nЭйдос приветствует нового Архитектора.",
    "/// СИСТЕМА АКТИВНА.\nТвоя старая жизнь — это черновик. Начинаем чистовик."
]

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. ТЕКСТЫ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v30.0**\n\n"
    "**1. ИСТОЧНИКИ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы. +25 XP.\n"
    "• 📶 **СИГНАЛ (5 мин):** Импульсы. +15 XP.\n"
    "• 🌑 **НУЛЕВОЙ СЛОЙ:** Опасный рейд за XP.\n\n"
    "**2. МОДУЛИ:**\n"
    "• 📓 **ДНЕВНИК:** База инсайтов.\n"
    "• 📚 **АРХИВ:** Сохраняет все открытые протоколы.\n"
    "• 🏆 **РЕЙТИНГ:** Глобальная конкуренция."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО ({PRICES['cryo']} XP)**\nСтраховка серии при пропуске дня.\n\n"
    f"⚡️ **УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nСнижает ожидание Синхрона до 15 мин на 24 часа.\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nВзлом уровня доступа.\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

SYNDICATE_FULL = (
    "**🔗 СИНДИКАТ**\n\n"
    f"1. 🎁 **БОНУС:** +{REFERRAL_BONUS} XP за реферала.\n"
    "2. 📈 **РОЯЛТИ:** 10% от опыта твоей сети."
)

LEVEL_UP_MSG = {
    2: "🔓 **LVL 2**: Доступ к секретам 2 уровня открыт.",
    3: "🔓 **LVL 3**: Статус Оператора.",
    4: "👑 **LVL 4**: Ты — Архитектор."
}

# --- 4. БАЗА ДАННЫХ ---
def get_db_connection():
    try: return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e: print(f"/// DB ERROR: {e}"); return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        
        # 1. ОСНОВНЫЕ ТАБЛИЦЫ
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
                date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP, path TEXT DEFAULT 'general',
                xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1,
                last_active DATE DEFAULT CURRENT_DATE, prestige INTEGER DEFAULT 0,
                cryo INTEGER DEFAULT 0, accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0,
                accel_exp BIGINT DEFAULT 0, referrer TEXT,
                last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0,
                notified BOOLEAN DEFAULT TRUE, max_depth INTEGER DEFAULT 0
            );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
        
        # 2. ВСПОМОГАТЕЛЬНЫЕ
        cur.execute('''CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, uid BIGINT, action TEXT, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, uid BIGINT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        
        # 3. НУЛЕВОЙ СЛОЙ И АРХИВ (ЭТО НОВЫЕ ТАБЛИЦЫ, ОНИ СОЗДАДУТСЯ САМИ)
        cur.execute('''CREATE TABLE IF NOT EXISTS raid_sessions (uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100, buffer_xp INTEGER DEFAULT 0, start_time BIGINT);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_knowledge (uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, content_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, uid BIGINT, item_id TEXT, acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

        # Патчи колонок (для старых баз, чтобы ничего не упало)
        try: 
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS max_depth INTEGER DEFAULT 0;")
            conn.commit()
        except: conn.rollback()
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;")
            conn.commit()
        except: conn.rollback()

        conn.commit()
        print("/// DB v30.0 STRUCTURE VERIFIED.")
    except Exception as e: print(f"/// DB INIT ERROR: {e}")
    finally: conn.close()

# --- DB HELPERS ---
def log_event(uid, action, details=""):
    def task():
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO logs (uid, action, details) VALUES (%s, %s, %s)", (uid, action, details))
                conn.commit()
            except: pass
            finally: conn.close()
    threading.Thread(target=task).start()

def get_user_from_db(uid):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
        return cur.fetchone()
    finally: conn.close()

def update_user_db(uid, **kwargs):
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [uid]
        cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", values)
        conn.commit()
    finally: conn.close()

def register_user_db(uid, username, first_name, referrer):
    conn = get_db_connection()
    if not conn: return
    try:
        start_xp = 50 if referrer == 'inst' else 0
        cur = conn.cursor()
        cur.execute("INSERT INTO users (uid, username, first_name, referrer, xp, last_active) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE) ON CONFLICT (uid) DO NOTHING", 
                    (uid, f"@{username}", first_name, str(referrer or ''), start_xp))
        conn.commit()
        log_event(uid, "REGISTER", f"Ref: {referrer}")
    finally: conn.close()

def get_referral_count(uid):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),))
        row = cur.fetchone()
        return row[0] if row else 0
    except: return 0
    finally: conn.close()

def save_note(uid, text):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO notes (uid, text) VALUES (%s, %s)", (uid, text))
        conn.commit()
    finally: conn.close()

def save_knowledge(uid, content_id):
    """Сохраняет ID протокола в архив юзера"""
    if not content_id: return
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
        conn.commit()
    except: pass
    finally: conn.close()

def get_leaderboard_text():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Теперь выводим и Глубину (max_depth)
        cur.execute("SELECT username, xp, level, max_depth FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        text = "🏆 **ГЛОБАЛЬНЫЙ РЕЙТИНГ**\n━━━━━━━━━━━━━━\n"
        for i, row in enumerate(rows, 1):
            icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            uname = row[0] if row[0] else "..."
            depth = f" | ⚓️ {row[3]}м" if row[3] > 0 else ""
            text += f"{icon} **{i}. {uname}** — {row[1]} XP{depth}\n"
        return text
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

def check_achievements(uid):
    u = get_user_from_db(uid)
    if not u: return
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
    existing = set(row[0] for row in cur.fetchall())
    new_ach = []
    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if ach_id not in existing and data['cond'](u):
            try:
                cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s)", (uid, ach_id))
                update_user_db(uid, xp=u['xp'] + data['xp'])
                new_ach.append(f"{data['name']} (+{data['xp']} XP)")
                log_event(uid, "ACHIEVEMENT", ach_id)
            except: pass
    conn.commit(); conn.close()
    if new_ach:
        try: bot.send_message(uid, "🏆 **ДОСТИЖЕНИЕ:**\n" + "\n".join(new_ach))
        except: pass

def process_xp_logic(uid, amount, is_sync=False):
    u = get_user_from_db(uid)
    if not u: return False, None, 0
    today = datetime.now().date()
    last_date = u['last_active']
    if isinstance(last_date, str): last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
    
    streak_bonus = 0
    s_msg = None
    
    if last_date < today:
        if (today - last_date).days == 1:
            new_streak = u['streak'] + 1
            streak_bonus = new_streak * 5
            s_msg = f"🔥 СЕРИЯ: {new_streak} ДН."
        else:
            if u['cryo'] > 0:
                new_streak = u['streak']; update_user_db(uid, cryo=u['cryo'] - 1); s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else:
                new_streak = 1; streak_bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        update_user_db(uid, streak=new_streak, last_active=today)
    else: new_streak = u['streak']

    total = amount + streak_bonus
    new_xp = u['xp'] + total
    
    if u['referrer'] and u['referrer'].isdigit():
        try:
            r_u = get_user_from_db(int(u['referrer']))
            if r_u: update_user_db(int(u['referrer']), xp=r_u['xp'] + int(total*0.1))
        except: pass

    new_lvl = u['level']
    for lvl, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr: new_lvl = lvl; break
    update_user_db(uid, xp=new_xp, level=new_lvl)
    threading.Thread(target=check_achievements, args=(uid,)).start()
    return (new_lvl > u['level']), s_msg, total

def get_content(c_type, path, level):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if c_type == 'signal': cur.execute("SELECT id, text FROM content WHERE type = 'signal' ORDER BY RANDOM() LIMIT 1")
        else: cur.execute("SELECT id, text FROM content WHERE type = 'protocol' AND (path = %s OR path = 'general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, level))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally: conn.close()

# --- 6. ЯДРО: НУЛЕВОЙ СЛОЙ (RAID ENGINE) - ВОТ ЭТИ 200 СТРОК ---
def raid_start_session(uid):
    u = get_user_from_db(uid)
    if u['xp'] < RAID_COST: return False, "❌ Недостаточно энергии (нужно 100 XP)."
    
    update_user_db(uid, xp=u['xp'] - RAID_COST)
    
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO raid_sessions (uid, depth, signal, buffer_xp, start_time) 
        VALUES (%s, 0, 100, 0, %s)
        ON CONFLICT (uid) DO UPDATE SET depth=0, signal=100, buffer_xp=0, start_time=%s
    """, (uid, int(time.time()), int(time.time())))
    conn.commit(); conn.close()
    return True, "🌀 **ПОГРУЖЕНИЕ НАЧАЛОСЬ...**\nСигнал стабилен. Ищи путь."

def raid_process_step(uid, direction):
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: conn.close(); return None, "Сессия не найдена."
    
    event = random.choice(RAID_SCENARIOS)
    new_depth = s['depth'] + 1
    dmg = event['dmg'] + random.randint(0, 5)
    new_signal = min(100, s['signal'] - dmg)
    if direction in ["left", "right"]: new_signal -= 2
    new_buffer = s['buffer_xp'] + event['val']
    
    is_alive = True
    msg = ""
    
    if new_signal <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        msg = f"💀 **СИГНАЛ ПОТЕРЯН.**\nТы зашел слишком далеко.\nПотеряно: {s['buffer_xp']} XP."; is_alive = False
    else:
        cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, buffer_xp=%s WHERE uid=%s", (new_depth, new_signal, new_buffer, uid))
        u = get_user_from_db(uid)
        if new_depth > u.get('max_depth', 0): update_user_db(uid, max_depth=new_depth)
        icon = "🟢" if new_signal > 60 else "🟡" if new_signal > 30 else "🔴"
        msg = f"⚓️ **ГЛУБИНА: {new_depth}**\n\n{event['text']}\n\n🎒 **Буфер:** {new_buffer} XP\n📡 **Сигнал:** {icon} {new_signal}%"
    conn.commit(); conn.close()
    return is_alive, msg

def raid_extract(uid):
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: conn.close(); return 0
    amount = s['buffer_xp']
    cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
    conn.commit(); conn.close()
    process_xp_logic(uid, amount)
    return amount

# --- 7. ИНТЕРФЕЙС ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo': bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: 
        try: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except: pass

def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    markup.add(types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu")) # <--- КНОПКА ДОБАВЛЕНА
    markup.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"), types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"))
    markup.add(types.InlineKeyboardButton("🔗 СЕТЬ", callback_data="referral"), types.InlineKeyboardButton("📚 БАЗА", callback_data="guide"))
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return markup

def get_raid_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("⬅️", callback_data="raid_step_left"), types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_forward"), types.InlineKeyboardButton("➡️", callback_data="raid_step_right"))
    markup.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract_confirm"))
    return markup

def get_progress_bar(current_xp, level):
    next_level_xp = LEVELS.get(level + 1, 10000); prev_level_xp = LEVELS.get(level, 0)
    if level >= 6: return "`[||||||||||] MAX`"
    percent = min(100, max(0, int(((current_xp - prev_level_xp) / (next_level_xp - prev_level_xp)) * 100)))
    blocks = int(percent / 10); bar = "||" * blocks + ".." * (10 - blocks)
    return f"`[{bar}] {percent}%`"

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None
    u = get_user_from_db(uid)
    if not u:
        variant = random.choice(WELCOME_VARIANTS)
        register_user_db(uid, m.from_user.username, m.from_user.first_name, ref_arg)
        if ref_arg and ref_arg.isdigit():
            r_u = get_user_from_db(int(ref_arg))
            if r_u: update_user_db(int(ref_arg), xp=r_u['xp'] + REFERRAL_BONUS)
        log_event(uid, "REGISTER", f"Var: {variant}")
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=variant, reply_markup=get_main_menu(uid))
    else: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS: СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))

user_state = {} 

@bot.message_handler(content_types=['text'])
def text_handler(m):
    uid = m.from_user.id
    state = user_state.get(uid)
    if state and state.get('type') == 'diary_wait':
        save_note(uid, m.text); bot.send_message(uid, "💾 **ЗАПИСАНО.**", reply_markup=get_main_menu(uid)); user_state.pop(uid)
    elif uid == ADMIN_ID and state:
        if state['step'] == 'wait_signal':
            conn=get_db_connection(); cur=conn.cursor(); cur.execute("INSERT INTO content (type, path, text) VALUES ('signal', 'general', %s)", (m.text,)); conn.commit(); conn.close()
            bot.send_message(uid, "✅"); user_state.pop(uid)
        elif state['step'] == 'wait_proto':
            try:
                p, l, t = m.text.split('|', 2)
                conn=get_db_connection(); cur=conn.cursor(); cur.execute("INSERT INTO content (type, path, level, text) VALUES ('protocol', %s, %s, %s)", (p.strip(), int(l), t.strip())); conn.commit(); conn.close()
                bot.send_message(uid, "✅"); user_state.pop(uid)
            except: bot.send_message(uid, "❌ Format error")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    u = get_user_from_db(uid)
    if not u: return
    now = time.time()
    log_event(uid, "CLICK", call.data)

    if call.data == "get_protocol":
        cd = COOLDOWN_ACCEL if u['accel_exp'] > now else COOLDOWN_BASE
        if now - u['last_protocol_time'] < cd:
            rem = int((cd - (now - u['last_protocol_time']))/60)
            bot.answer_callback_query(call.id, f"⏳ {rem} мин", show_alert=True); return
        update_user_db(uid, last_protocol_time=int(now), notified=False)
        up, s_msg, tot = process_xp_logic(uid, XP_GAIN)
        u = get_user_from_db(uid)
        if u['decoder'] > 0: update_user_db(uid, decoder=u['decoder']-1)
        target = u['level'] + 1 if u['decoder'] > 0 else u['level']
        cid, txt = get_content('protocol', u['path'], target)
        if not txt: txt = "/// НЕТ ДАННЫХ."
        else: save_knowledge(uid, cid) # СОХРАНЯЕМ В АРХИВ
        msg = f"🧬 **{SCHOOLS.get(u['path'], 'ОБЩИЙ')}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
        if up: bot.send_message(uid, f"🎉 **{LEVEL_UP_MSG.get(u['level'], 'LEVEL UP!')}**")
        safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

    elif call.data == "get_signal":
        if now - u['last_signal_time'] < COOLDOWN_SIGNAL:
            bot.answer_callback_query(call.id, "⏳ Жди...", show_alert=True); return
        update_user_db(uid, last_signal_time=int(now))
        process_xp_logic(uid, XP_SIGNAL)
        cid, txt = get_content('signal', 'general', 1)
        if not txt: txt = "/// ПУСТО."
        bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{txt}\n\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

    # --- НУЛЕВОЙ СЛОЙ (НОВЫЙ ФУНКЦИОНАЛ) ---
    elif call.data == "zero_layer_menu":
        msg = (f"🌑 **НУЛЕВОЙ СЛОЙ**\nЗона высокого риска.\n\n🎫 **ВХОД:** {RAID_COST} XP\n⚓️ **РЕКОРД:** {u.get('max_depth', 0)} м.\n\nПравила:\n1. Трать Сигнал на шаги.\n2. Собирай XP в Буфер.\n3. Жми «Эвакуация» вовремя.")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"🌪 НАЧАТЬ (-{RAID_COST} XP)", callback_data="raid_start_confirm"))
        markup.add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)
    elif call.data == "raid_start_confirm":
        success, msg = raid_start_session(uid)
        if success: safe_edit(call, msg, get_raid_keyboard())
        else: bot.answer_callback_query(call.id, msg, show_alert=True)
    elif call.data.startswith("raid_step_"):
        direction = call.data.split("_")[2]
        is_alive, msg = raid_process_step(uid, direction)
        if is_alive: safe_edit(call, msg, get_raid_keyboard())
        else: safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back_to_menu")))
    elif call.data == "raid_extract_confirm":
        amount = raid_extract(uid)
        msg = f"📦 **ЭВАКУАЦИЯ.**\nСохранено: {amount} XP."
        safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back_to_menu")))

    # --- ПРОФИЛЬ (С АРХИВОМ И ГЛУБИНОЙ) ---
    elif call.data == "profile":
        ref_count = get_referral_count(uid)
        conn=get_db_connection(); cur=conn.cursor()
        cur.execute("SELECT COUNT(*) FROM achievements WHERE uid=%s", (uid,)); achs=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_knowledge WHERE uid=%s", (uid,)); k_count=cur.fetchone()[0]; conn.close()
        
        msg = (f"👤 **{u['username']}** | {TITLES.get(u['level'], '...')}\n"
               f"🔋 **XP:** {u['xp']} {get_progress_bar(u['xp'], u['level'])}\n"
               f"📚 **Архив:** {k_count} | ⚓️ **Глубина:** {u.get('max_depth', 0)}м\n"
               f"👥 **Сеть:** {ref_count} | 🏆 **Ачивки:** {achs}")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📚 ЧИТАТЬ АРХИВ", callback_data="open_archive"))
        markup.add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)

    elif call.data == "open_archive":
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT c.text FROM user_knowledge k JOIN content c ON k.content_id = c.id WHERE k.uid = %s ORDER BY k.unlocked_at DESC LIMIT 5", (uid,))
        rows = cur.fetchall(); conn.close()
        text = "**📚 ПОСЛЕДНИЕ ОТКРЫТИЯ:**\n\n" + ("\n".join([f"{i}. {r[0][:50]}..." for i, r in enumerate(rows, 1)]) if rows else "Пусто.")
        safe_edit(call, text, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="profile")))

    # --- ОСТАЛЬНОЕ ---
    elif call.data == "shop":
        safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("❄️ КУПИТЬ КРИО (200 XP)", callback_data="buy_cryo"), types.InlineKeyboardButton("⚡️ КУПИТЬ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"), types.InlineKeyboardButton("🔑 КУПИТЬ ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"), types.InlineKeyboardButton("⚙️ СМЕНИТЬ ФРАКЦИЮ (100 XP)", callback_data="change_path_confirm"), types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            update_user_db(uid, xp=u['xp']-PRICES[item])
            conn=get_db_connection(); cur=conn.cursor(); cur.execute(f"UPDATE users SET {item}={item}+1 WHERE uid=%s", (uid,)); conn.commit(); conn.close()
            bot.answer_callback_query(call.id, "✅"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP")
    elif call.data == "change_path_confirm":
        safe_edit(call, "⚠️ Путь (-100 XP):", types.InlineKeyboardMarkup(row_width=1).add(types.InlineKeyboardButton("🔴 МАТЕРИЯ", callback_data="set_path_money"), types.InlineKeyboardButton("🔵 РАЗУМ", callback_data="set_path_mind"), types.InlineKeyboardButton("🟣 СИНГУЛЯРНОСТЬ", callback_data="set_path_tech"), types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif "set_path_" in call.data:
        path = call.data.split("_")[2]
        cost = 0 if u['path'] == 'general' else 100
        if u['xp'] >= cost:
            if cost > 0: update_user_db(uid, xp=u['xp']-cost)
            update_user_db(uid, path=path)
            bot.send_message(uid, f"/// ПУТЬ: {path.upper()}", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP")
    elif call.data == "leaderboard":
        safe_edit(call, get_leaderboard_text(), types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "diary_mode":
        user_state[uid] = {'type': 'diary_wait'}
        safe_edit(call, "📓 **ДНЕВНИК**\nПиши инсайт:", types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "referral":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ТВОЯ ССЫЛКА:**\n`{link}`", get_main_menu(uid))
    elif call.data == "guide":
        safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS: ONLINE", reply_markup=get_main_menu(uid))

    # ADMIN
    elif call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ ADMIN", get_admin_menu())
    elif call.data == "adm_add_signal" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_signal'}; bot.send_message(uid, "✍️ Signal:")
    elif call.data == "adm_add_proto" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_proto'}; bot.send_message(uid, "✍️ `path|level|text`:")
    elif call.data == "admin_stats" and uid == ADMIN_ID:
        conn=get_db_connection(); cur=conn.cursor(); cur.execute("SELECT COUNT(*) FROM users"); u=cur.fetchone()[0]; conn.close()
        bot.answer_callback_query(call.id, f"Users: {u}", show_alert=True)

# --- 9. БЕЗОПАСНЫЙ ЗАПУСК ДЛЯ RENDER ---
@app.route('/health', methods=['GET'])
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    try: bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))]); return 'OK', 200
    except: return 'Error', 500

def notification_worker():
    while True:
        try:
            time.sleep(60); conn = get_db_connection()
            if not conn: continue
            cur = conn.cursor(cursor_factory=RealDictCursor); cur.execute("SELECT * FROM users WHERE notified = FALSE")
            for u in cur.fetchall():
                cd = COOLDOWN_ACCEL if u['accel_exp'] > time.time() else COOLDOWN_BASE
                if u['last_protocol_time'] > 0 and (time.time() - u['last_protocol_time'] >= cd):
                    try: bot.send_message(u['uid'], "⚡️ **ГОТОВНОСТЬ 100%.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 СИНХРОН", callback_data="get_protocol"))); update_user_db(u['uid'], notified=True)
                    except: pass
            conn.close()
        except: pass

def system_startup():
    with app.app_context():
        # Сначала инициализируем БД
        try:
            init_db()
            if WEBHOOK_URL:
                bot.remove_webhook()
                time.sleep(1)
                bot.set_webhook(url=WEBHOOK_URL)
        except Exception as e: print(f"Error: {e}")
        # Потом запускаем воркер
        notification_worker()

if __name__ == "__main__":
    # Запускаем фоновый процесс (БД + Уведомления)
    threading.Thread(target=system_startup, daemon=True).start()
    
    # Сразу открываем порт для Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
