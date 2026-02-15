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

# ==========================================
# 1. КОНФИГУРАЦИЯ И КОНСТАНТЫ
# ==========================================
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
XP_GAIN = 25              # Награда Синхрон
XP_SIGNAL = 15            # Награда Сигнал
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
RAID_COST = 100           # Вход в Рейд

PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# --- СИСТЕМА ДОСТИЖЕНИЙ ---
ACHIEVEMENTS_LIST = {
    "first_steps": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: u['xp'] >= 25, "xp": 50},
    "streak_7": {"name": "🔥 СТОИК (Неделя)", "cond": lambda u: u['streak'] >= 7, "xp": 150},
    "streak_30": {"name": "🧘 ЖЕЛЕЗНЫЙ МОНАХ (30 дней)", "cond": lambda u: u['streak'] >= 30, "xp": 500},
    "rich_1000": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200},
    "lvl_3": {"name": "🧠 ОПЕРАТОР (Lvl 3)", "cond": lambda u: u['level'] >= 3, "xp": 300},
    "diver_50": {"name": "🕳 СТАЛКЕР (Глубина 50)", "cond": lambda u: u.get('max_depth', 0) >= 50, "xp": 300}
}

# --- СЦЕНАРИИ РЕЙДА (РЕЗЕРВНЫЕ) ---
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

# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ
# ==========================================
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- ТЕКСТОВЫЕ МОДУЛИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v31.0**\n\n"
    "**1. ИСТОЧНИКИ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы. Награда: **25 XP**.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие ментальные импульсы. Награда: **15 XP**.\n"
    "• 🌑 **НУЛЕВОЙ СЛОЙ:** Опасный рейд. Требует топлива (XP) за каждый шаг.\n\n"
    "**2. МОДУЛИ:**\n"
    "• 📓 **ДНЕВНИК:** Приватная база твоих инсайтов.\n"
    "• 📚 **АРХИВ:** Хранилище всех открытых знаний.\n"
    "• 🏆 **РЕЙТИНГ:** Глобальная конкуренция умов.\n\n"
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

# ==========================================
# 3. БАЗА ДАННЫХ
# ==========================================
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
        
        # 1. Основные таблицы
        cur.execute('''CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP, path TEXT DEFAULT 'general', xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1, last_active DATE DEFAULT CURRENT_DATE, prestige INTEGER DEFAULT 0, cryo INTEGER DEFAULT 0, accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0, accel_exp BIGINT DEFAULT 0, referrer TEXT, last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0, notified BOOLEAN DEFAULT TRUE, max_depth INTEGER DEFAULT 0);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, uid BIGINT, action TEXT, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, uid BIGINT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        
        # 2. Таблицы Рейда и Знаний (v31.0)
        cur.execute('''CREATE TABLE IF NOT EXISTS raid_sessions (uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100, buffer_xp INTEGER DEFAULT 0, start_time BIGINT);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_knowledge (uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, content_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, uid BIGINT, item_id TEXT, acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        
        # 3. Таблицы для "Кинговского" контента
        cur.execute('''CREATE TABLE IF NOT EXISTS raid_content (id SERIAL PRIMARY KEY, text TEXT, type TEXT, val INTEGER);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS raid_hints (id SERIAL PRIMARY KEY, type TEXT, text TEXT);''')

        # Патчи
        try: cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;"); conn.commit()
        except: conn.rollback()
        try: cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS max_depth INTEGER DEFAULT 0;"); conn.commit()
        except: conn.rollback()

        conn.commit()
        print("/// DB STRUCTURE VERIFIED (FULL SCALE v31.0).")
    except Exception as e: print(f"/// DB INIT ERROR: {e}")
    finally: conn.close()

# --- HELPER FUNCTIONS FOR DB ---
def log_event(uid, action, details=""):
    def task():
        conn = get_db_connection()
        if conn:
            try: cur = conn.cursor(); cur.execute("INSERT INTO logs (uid, action, details) VALUES (%s, %s, %s)", (uid, action, details)); conn.commit()
            except: pass
            finally: conn.close()
    threading.Thread(target=task).start()

def get_user_from_db(uid):
    conn = get_db_connection()
    if not conn: return None
    try: cur = conn.cursor(cursor_factory=RealDictCursor); cur.execute("SELECT * FROM users WHERE uid = %s", (uid,)); return cur.fetchone()
    finally: conn.close()

def update_user_db(uid, **kwargs):
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        cur.execute(f"UPDATE users SET {set_clause} WHERE uid = %s", list(kwargs.values()) + [uid])
        conn.commit()
    finally: conn.close()

def register_user_db(uid, username, first_name, referrer):
    conn = get_db_connection()
    if not conn: return
    try:
        start_xp = 50 if referrer == 'inst' else 0
        cur = conn.cursor()
        cur.execute("INSERT INTO users (uid, username, first_name, referrer, xp, last_active) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE) ON CONFLICT (uid) DO NOTHING", (uid, f"@{username}", first_name, str(referrer or ''), start_xp))
        conn.commit()
        log_event(uid, "REGISTER", f"Ref: {referrer}")
    finally: conn.close()

def get_referral_count(uid):
    conn = get_db_connection()
    try: cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),)); return cur.fetchone()[0]
    except: return 0
    finally: conn.close()

def save_note(uid, text):
    conn = get_db_connection()
    try: cur = conn.cursor(); cur.execute("INSERT INTO notes (uid, text) VALUES (%s, %s)", (uid, text)); conn.commit()
    finally: conn.close()

def save_knowledge(uid, content_id):
    if not content_id: return
    conn = get_db_connection()
    try: cur = conn.cursor(); cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id)); conn.commit()
    except: pass
    finally: conn.close()

def get_leaderboard_text():
    conn = get_db_connection()
    if not conn: return "/// ОШИБКА СВЯЗИ С РЕЙТИНГОМ"
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, xp, level, max_depth FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        text = "🏆 **ГЛОБАЛЬНЫЙ РЕЙТИНГ АРХИТЕКТОРОВ**\n━━━━━━━━━━━━━━\n"
        for i, row in enumerate(rows, 1):
            icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            uname = row[0] if row[0] else "Неизвестный"
            depth_info = f" | ⚓️ {row[3]}м" if row[3] > 0 else ""
            text += f"{icon} **{i}. {uname}** — {row[1]} XP{depth_info} (Lvl {row[2]})\n"
        return text
    finally: conn.close()

def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo': bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: 
        try: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except: pass

def check_achievements(uid):
    u = get_user_from_db(uid)
    if not u: return
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
    existing = set(row[0] for row in cur.fetchall())
    new_achieved = []
    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if ach_id not in existing and data['cond'](u):
            try:
                cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s)", (uid, ach_id))
                update_user_db(uid, xp=u['xp'] + data['xp'])
                new_achieved.append(f"{data['name']} (+{data['xp']} XP)")
                log_event(uid, "ACHIEVEMENT", ach_id)
            except: pass
    conn.commit(); conn.close()
    if new_achieved:
        try: bot.send_message(uid, "🏆 **НОВОЕ ДОСТИЖЕНИЕ:**\n" + "\n".join(new_achieved), parse_mode="Markdown")
        except: pass

def process_xp_logic(uid, amount, is_sync=False):
    u = get_user_from_db(uid)
    if not u: return False, None, 0
    today = datetime.now().date()
    l_d = datetime.strptime(u['last_active'], "%Y-%m-%d").date() if isinstance(u['last_active'], str) else u['last_active']
    s_bonus = 0; s_msg = None
    if l_d < today:
        if (today - l_d).days == 1: new_s = u['streak'] + 1; s_bonus = new_s * 5; s_msg = f"🔥 СЕРИЯ: {new_s} ДН."
        else:
            if u['cryo'] > 0: new_s = u['streak']; update_user_db(uid, cryo=u['cryo'] - 1); s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else: new_s = 1; s_bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        update_user_db(uid, streak=new_s, last_active=today)
    else: new_s = u['streak']
    total_xp = amount + s_bonus; new_total = u['xp'] + total_xp
    if u['referrer'] and u['referrer'].isdigit():
        try:
            r_u = get_user_from_db(int(u['referrer']))
            if r_u: update_user_db(int(u['referrer']), xp=r_u['xp'] + int(total_xp * 0.1))
        except: pass
    old_l = u['level']; new_l = old_l
    for l, thr in sorted(LEVELS.items(), reverse=True):
        if new_total >= thr: new_l = l; break
    update_user_db(uid, xp=new_total, level=new_l)
    threading.Thread(target=check_achievements, args=(uid,)).start()
    return (new_l > old_l), s_msg, total_xp

def get_content(c_type, path, level):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if c_type == 'signal': cur.execute("SELECT id, text FROM content WHERE type = 'signal' ORDER BY RANDOM() LIMIT 1")
        else: cur.execute("SELECT id, text FROM content WHERE type = 'protocol' AND (path = %s OR path = 'general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, level))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally: conn.close()
def get_referral_count(uid):
    conn = get_db_connection()
    if not conn: return 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),))
        return cur.fetchone()[0]
    except: return 0
    finally: conn.close()

def save_note(uid, text):
    """Сохраняет запись в Нейро-Дневник"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO notes (uid, text) VALUES (%s, %s)", (uid, text))
        conn.commit()
    finally: conn.close()

def save_knowledge(uid, content_id):
    """Сохраняет ID протокола в Нейро-Архив"""
    if not content_id: return
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
        conn.commit()
    except: pass
    finally: conn.close()

def get_leaderboard_text():
    """Генерирует текст Глобального Рейтинга"""
    conn = get_db_connection()
    if not conn: return "/// ОШИБКА СВЯЗИ С РЕЙТИНГОМ"
    try:
        cur = conn.cursor()
        # Добавлена выборка max_depth
        cur.execute("SELECT username, xp, level, max_depth FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        text = "🏆 **ГЛОБАЛЬНЫЙ РЕЙТИНГ АРХИТЕКТОРОВ**\n━━━━━━━━━━━━━━\n"
        for i, row in enumerate(rows, 1):
            icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            uname = row[0] if row[0] else "Неизвестный"
            depth_info = f" | ⚓️ {row[3]}м" if row[3] > 0 else ""
            text += f"{icon} **{i}. {uname}** — {row[1]} XP{depth_info} (Lvl {row[2]})\n"
        return text
    finally: conn.close()

# ==========================================
# 4. ЛОГИКА И ЯДРО (CORE)
# ==========================================
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
    """Проверка и выдача ачивок"""
    u = get_user_from_db(uid)
    if not u: return
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
    existing = set(row[0] for row in cur.fetchall())
    
    new_achieved = []
    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if ach_id not in existing and data['cond'](u):
            try:
                cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s)", (uid, ach_id))
                update_user_db(uid, xp=u['xp'] + data['xp']) # Награда
                new_achieved.append(f"{data['name']} (+{data['xp']} XP)")
                log_event(uid, "ACHIEVEMENT", ach_id)
            except: pass
            
    conn.commit()
    conn.close()
    
    if new_achieved:
        msg = "🏆 **НОВОЕ ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО:**\n" + "\n".join(new_achieved)
        try: bot.send_message(uid, msg, parse_mode="Markdown")
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
    
    # ПРОВЕРКА АЧИВОК В ФОНЕ
    threading.Thread(target=check_achievements, args=(uid,)).start()
    
    return (new_lvl > old_lvl), s_msg, total_xp

def get_content(c_type, path, level):
    conn = get_db_connection()
    if not conn: return "/// ОШИБКА ПОДКЛЮЧЕНИЯ К БАЗЕ ЗНАНИЙ"
    try:
        cur = conn.cursor()
        if c_type == 'signal':
             cur.execute("SELECT id, text FROM content WHERE type = 'signal' ORDER BY RANDOM() LIMIT 1")
        else:
            cur.execute("""
                SELECT id, text FROM content 
                WHERE type = 'protocol' AND (path = %s OR path = 'general') AND level <= %s 
                ORDER BY RANDOM() LIMIT 1
            """, (path, level))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally:
        conn.close()

# --- RAID ENGINE v31.0 (УМНЫЙ РЕЙД С КОМПАСОМ) ---
def raid_get_hint(event_type):
    """Ищет подсказку в БД для конкретного типа события"""
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT text FROM raid_hints WHERE type=%s ORDER BY RANDOM() LIMIT 1", (event_type,))
    res = cur.fetchone()
    conn.close()
    if not res:
        if event_type == 'trap': return "Чувствуется тревога..."
        if event_type == 'loot': return "Слабый сигнал..."
        return "Тишина..."
    return res[0]

def raid_start_session(uid):
    u = get_user_from_db(uid)
    if u['xp'] < RAID_COST: return False, "❌ Недостаточно энергии (нужно 100 XP)."
    
    update_user_db(uid, xp=u['xp'] - RAID_COST)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO raid_sessions (uid, depth, signal, buffer_xp, start_time) 
        VALUES (%s, 0, 100, 0, %s)
        ON CONFLICT (uid) DO UPDATE SET depth=0, signal=100, buffer_xp=0, start_time=%s
    """, (uid, int(time.time()), int(time.time())))
    conn.commit()
    conn.close()
    log_event(uid, "RAID_START")
    return True, "🌀 **ПОГРУЖЕНИЕ НАЧАЛОСЬ...**\nСигнал стабилен. Ищи путь."

def raid_process_step(uid, direction):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Списание Топлива (Реального XP)
    u = get_user_from_db(uid)
    step_cost = 10 + int(u.get('max_depth', 0) / 10)
    
    if u['xp'] < step_cost:
        conn.close()
        return False, f"⛽️ **ПУСТОЙ БАК.**\nНужно {step_cost} XP. У тебя {u['xp']}.\n\nТы застрял в Лимбе."

    update_user_db(uid, xp=u['xp'] - step_cost)
    
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: conn.close(); return None, "ОШИБКА СЕССИИ."
    
    # 2. Генерация события (из БД)
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    db_event = cur.fetchone()
    
    if db_event:
        event = {
            "text": db_event['text'], 
            "type": db_event['type'], 
            "val": db_event['val'], 
            "dmg": 0
        }
        if event['type'] == 'trap': event['dmg'] = event['val']; event['val'] = 0
        elif event['type'] == 'heal': event['dmg'] = -event['val']; event['val'] = 0
    else:
        event = random.choice(RAID_SCENARIOS)

    # 3. Механика
    new_depth = s['depth'] + 1
    dmg = event.get('dmg', 0) + random.randint(-2, 5)
    new_signal = min(100, s['signal'] - dmg)
    if direction in ["left", "right"]: new_signal -= 2
    new_buffer = s['buffer_xp'] + event.get('val', 0)
    
    is_alive = True
    msg = ""
    
    if new_signal <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        msg = f"💀 **СИГНАЛ ПОТЕРЯН.**\n_{event['text']}_\n\nПотеряно: {s['buffer_xp']} XP."; is_alive = False
    else:
        cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, buffer_xp=%s WHERE uid=%s", (new_depth, new_signal, new_buffer, uid))
        if new_depth > u.get('max_depth', 0): update_user_db(uid, max_depth=new_depth)
        
        # 4. Генерация Компаса
        h_left = raid_get_hint(random.choice(['trap', 'loot', 'empty']))
        h_fwd = raid_get_hint(random.choice(['trap', 'loot', 'heal']))
        h_right = raid_get_hint(random.choice(['loot', 'empty', 'lore']))
        
        u_now = get_user_from_db(uid)
        icon = "🟢" if new_signal > 60 else "🟡" if new_signal > 30 else "🔴"
        
        msg = (f"⚓️ **ГЛУБИНА: {new_depth} м**\n\n"
               f"_{event['text']}_\n\n"
               f"💳 **ТОПЛИВО:** {u_now['xp']} XP (-{step_cost})\n"
               f"🎒 **В МЕШКЕ:** {new_buffer} XP\n"
               f"📡 **СИГНАЛ:** {icon} {new_signal}%\n"
               f"━━━━━━━━━━━━━━\n"
               f"🧭 **СКАЛ-КОМПАС:**\n"
               f"⬅️ _{h_left}_\n"
               f"⬆️ _{h_fwd}_\n"
               f"➡️ _{h_right}_")
        
    conn.commit(); conn.close()
    return is_alive, msg

def raid_extract(uid):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: conn.close(); return 0
    
    amount = s['buffer_xp']
    cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
    conn.commit()
    conn.close()
    
    process_xp_logic(uid, amount)
    log_event(uid, "RAID_EXTRACT", f"Amount: {amount}")
    return amount

def notification_worker():
    while True:
        try:
            time.sleep(60)
            conn = get_db_connection()
            if not conn: continue
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE notified = FALSE")
            for u in cur.fetchall():
                cd = COOLDOWN_ACCEL if u['accel_exp'] > time.time() else COOLDOWN_BASE
                if u['last_protocol_time'] > 0 and (time.time() - u['last_protocol_time'] >= cd):
                    try:
                        bot.send_message(u['uid'], "⚡️ **СИСТЕМА ГОТОВА.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 СИНХРОН", callback_data="get_protocol")))
                        update_user_db(u['uid'], notified=True)
                    except: pass
            conn.close()
        except: pass

def get_progress_bar(current_xp, level):
    next_level_xp = LEVELS.get(level + 1, 10000)
    prev_level_xp = LEVELS.get(level, 0)
    if level >= 6: return "`[||||||||||] MAX`"
    needed = next_level_xp - prev_level_xp
    current = current_xp - prev_level_xp
    percent = min(100, max(0, int((current / needed) * 100)))
    blocks = int(percent / 10)
    bar = "||" * blocks + ".." * (10 - blocks)
    return f"`[{bar}] {percent}%`"

# ==========================================
# 5. ИНТЕРФЕЙС И КЛАВИАТУРЫ
# ==========================================
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👁 ДЕШИФРОВАТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")
    )
    markup.add(
        types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu")
    )
    markup.add(
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop")
    )
    markup.add(
        types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"),
        types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode")
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

def get_raid_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("⬅️", callback_data="raid_step_left"),
        types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_forward"),
        types.InlineKeyboardButton("➡️", callback_data="raid_step_right")
    )
    markup.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ (ЗАБРАТЬ ВСЁ)", callback_data="raid_extract_confirm"))
    return markup

# ==========================================
# 6. HANDLERS (ОБРАБОТЧИКИ)
# ==========================================
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
        
        welcome_msg = random.choice(WELCOME_VARIANTS)
        log_event(uid, "REGISTER", f"Variant: {WELCOME_VARIANTS.index(welcome_msg)}")
    else:
        welcome_msg = "/// EIDOS-OS: СИСТЕМА ПЕРЕЗАГРУЖЕНА."
        log_event(uid, "RESTART")
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

# --- ЗАГРУЗЧИКИ КОНТЕНТА (NEW!) ---
@bot.message_handler(commands=['inject_raid'])
def inject_raid_content(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        raw = message.text.replace('/inject_raid', '').strip()
        conn = get_db_connection(); cur = conn.cursor(); count = 0
        for line in raw.split('\n'):
            if '|' in line:
                p = line.split('|')
                if len(p)>=3:
                    cur.execute("INSERT INTO raid_content (text, type, val) VALUES (%s, %s, %s)", (p[0].strip(), p[1].strip(), int(p[2].strip())))
                    count+=1
        conn.commit(); conn.close()
        bot.reply_to(message, f"✅ История загружена: +{count}")
    except Exception as e: bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['inject_hints'])
def inject_hints_content(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        raw = message.text.replace('/inject_hints', '').strip()
        conn = get_db_connection(); cur = conn.cursor(); count = 0
        for line in raw.split('\n'):
            if '|' in line:
                t, txt = line.split('|')
                cur.execute("INSERT INTO raid_hints (type, text) VALUES (%s, %s)", (t.strip(), txt.strip()))
                count+=1
        conn.commit(); conn.close()
        bot.reply_to(message, f"✅ Подсказки загружены: +{count}")
    except Exception as e: bot.reply_to(message, f"Ошибка: {e}")

user_action_state = {} 

@bot.message_handler(content_types=['text'])
def text_input_handler(m):
    uid = m.from_user.id
    state = user_action_state.get(uid)
    
    if state and state.get('type') == 'diary_wait':
        save_note(uid, m.text)
        log_event(uid, "DIARY_ENTRY")
        bot.send_message(uid, "💾 **ЗАПИСЬ СОХРАНЕНА В НЕЙРО-ДНЕВНИК.**", reply_markup=get_main_menu(uid))
        user_action_state.pop(uid)
        return

    if uid == ADMIN_ID and state:
        if state['step'] == 'wait_signal_text':
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO content (type, path, text, level) VALUES ('signal', 'general', %s, 1)", (m.text,))
            conn.commit(); conn.close()
            bot.send_message(ADMIN_ID, "✅ **СИГНАЛ ЗАГРУЖЕН.**")
            user_action_state.pop(ADMIN_ID)
            
        elif state['step'] == 'wait_proto_text':
            try:
                path, level, text = m.text.split('|', 2)
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO content (type, path, text, level) VALUES ('protocol', %s, %s, %s)", (path.strip(), text.strip(), int(level)))
                conn.commit(); conn.close()
                bot.send_message(ADMIN_ID, f"✅ **ПРОТОКОЛ ({path}) ЗАГРУЖЕН.**")
            except: bot.send_message(ADMIN_ID, "❌ Ошибка формата. Надо: `path|level|text`")
            user_action_state.pop(ADMIN_ID)

        elif state['step'] == 'wait_user_id':
            uid_target = int(m.text) if m.text.isdigit() else 0
            u = get_user_from_db(uid_target)
            if u:
                msg = (f"👤 **ID:** `{u['uid']}`\nName: {u['username']}\nXP: {u['xp']} | LVL: {u['level']}\nInv: Cryo={u['cryo']}, Accel={u['accel']}")
                bot.send_message(ADMIN_ID, msg)
            else: bot.send_message(ADMIN_ID, "❌ Не найден.")
            user_action_state.pop(ADMIN_ID)

@bot.message_handler(content_types=['text', 'photo'])
def admin_cmd_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': 
            init_db() 
            bot.send_message(message.chat.id, "✅ Структура БД обновлена.")
        
        elif message.text and message.text.startswith('/telegraph '):
            parts = message.text.split(maxsplit=2)
            if len(parts) >= 2:
                url, text = parts[1], parts[2] if len(parts) > 2 else "/// АРХИВ ДЕШИФРОВАН"
                clean_url = url.split("google.com/search?q=")[-1] if "google.com" in url else url
                markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📂 ОТКРЫТЬ", url=clean_url), types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=signal"))
                bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ВОЙТИ В ТЕРМИНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=channel"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/ban '): 
            try:
                target_id = int(message.text.split()[1])
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE uid = %s", (target_id,)); conn.commit(); conn.close()
                bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} СТЕРТ.")
            except: bot.send_message(message.chat.id, "❌ Ошибка ID.")
        
        elif message.text and message.text.startswith('/give_xp '):
            try:
                _, t_id, amount = message.text.split()
                t_id, amount = int(t_id), int(amount)
                u = get_user_from_db(t_id)
                if u:
                    update_user_db(t_id, xp=u['xp'] + amount)
                    bot.send_message(t_id, f"⚡️ **ВМЕШАТЕЛЬСТВО АРХИТЕКТОРА:** Начислено {amount} XP.")
                    bot.send_message(message.chat.id, "✅ Начислено.")
            except: bot.send_message(message.chat.id, "❌ Формат: /give_xp ID СУММА")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    u = get_user_from_db(uid)
    if not u:
        bot.answer_callback_query(call.id, "⚠️ Нажми /start", show_alert=True); return
    
    now_ts = time.time()
    log_event(uid, "CLICK", call.data)

    try:
        if call.data == "admin_panel" and uid == ADMIN_ID: 
            safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ**", get_admin_menu())
        
        elif call.data == "adm_add_signal" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_signal_text'}
            bot.send_message(uid, "✍️ **Введи текст СИГНАЛА:**")
            
        elif call.data == "adm_add_proto" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_proto_text'}
            bot.send_message(uid, "✍️ **Введи ПРОТОКОЛ:**\n`money|1|Текст`")

        elif call.data == "adm_view_user" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_user_id'}
            bot.send_message(uid, "🔎 **Введи ID:**")

        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("UPDATE users SET xp = xp + 100")
            count = cur.rowcount; conn.commit(); conn.close()
            bot.answer_callback_query(call.id, f"🎁 Выдано {count} узлам")

        elif call.data == "admin_stats" and uid == ADMIN_ID:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE referrer = 'inst'"); inst = cur.fetchone()[0]
            conn.close()
            bot.answer_callback_query(call.id, f"📊 Узлы: {total} | Inst: {inst}", show_alert=True)

        elif call.data == "get_protocol":
            is_accel = u['accel_exp'] > now_ts
            cd = COOLDOWN_ACCEL if is_accel else COOLDOWN_BASE
            if now_ts - u['last_protocol_time'] < cd:
                rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
                bot.answer_callback_query(call.id, f"⏳ {rem} мин.", show_alert=True); return
            
            update_user_db(uid, last_protocol_time=int(now_ts), notified=False)
            up, s_msg, total = process_xp_logic(uid, XP_GAIN, is_sync=True)
            u = get_user_from_db(uid) 
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: update_user_db(uid, decoder=u['decoder'] - 1)
            
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 LEVEL UP!"))
            
            bot.send_message(uid, "📡 **ИНИЦИАЛИЗАЦИЯ...**"); time.sleep(1)
            cid, txt = get_content('protocol', u['path'], target_lvl)
            if not txt: txt = "/// НЕТ ДАННЫХ."
            else: save_knowledge(uid, cid)
            
            res = f"🧬 **{SCHOOLS.get(u['path'], 'ОБЩИЙ')}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
            safe_edit(call, res, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

        elif call.data == "get_signal":
            if now_ts - u['last_signal_time'] < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u['last_signal_time'])) / 60)
                bot.answer_callback_query(call.id, f"⏳ {rem} мин.", show_alert=True); return
            update_user_db(uid, last_signal_time=int(now_ts))
            process_xp_logic(uid, XP_SIGNAL)
            cid, txt = get_content('signal', 'general', 1)
            if not txt: txt = "..."
            bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{txt}\n\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

        elif call.data == "zero_layer_menu":
            msg = (f"🌑 **НУЛЕВОЙ СЛОЙ**\n\n🎫 **ВХОД:** {RAID_COST} XP\n⚓️ **РЕКОРД:** {u.get('max_depth', 0)} м.\n\nКаждый шаг требует топлива (XP).")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🌪 НАЧАТЬ ПОГРУЖЕНИЕ", callback_data="raid_start_confirm"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
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
            safe_edit(call, f"📦 **УСПЕШНАЯ ЭВАКУАЦИЯ.**\n\nСохранено: {amount} XP.", types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back_to_menu")))

        elif call.data == "profile":
            u = get_user_from_db(uid)
            ref_count = get_referral_count(uid)
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM user_knowledge WHERE uid=%s", (uid,)); k_count = cur.fetchone()[0]; conn.close()
            msg = (f"👤 **НЕЙРО-ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n"
                   f"🔰 **СТАТУС:** {TITLES.get(u['level'], 'НЕОФИТ')}\n"
                   f"🔋 **SYNC:** {u['xp']} XP\n"
                   f"📚 **АРХИВ:** {k_count} | ⚓️ **ГЛУБИНА:** {u.get('max_depth', 0)}м\n"
                   f"🎒 **ИНВЕНТАРЬ:** Cryo: {u['cryo']} | Accel: {u['accel']}")
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("📚 АРХИВ", callback_data="open_archive"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

        elif call.data == "open_archive":
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT c.text FROM user_knowledge k JOIN content c ON k.content_id = c.id WHERE k.uid = %s ORDER BY k.unlocked_at DESC LIMIT 5", (uid,))
            rows = cur.fetchall(); conn.close()
            text = "**📚 ПОСЛЕДНИЕ ОТКРЫТИЯ:**\n\n" + ("\n".join([f"- {r[0][:40]}..." for r in rows]) if rows else "Пусто.")
            safe_edit(call, text, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="profile")))

        elif call.data == "leaderboard":
            safe_edit(call, get_leaderboard_text(), types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))

        elif call.data == "diary_mode":
            user_action_state[uid] = {'type': 'diary_wait'}
            safe_edit(call, "📓 **РЕЖИМ ДНЕВНИКА**\nПиши...", types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back_to_menu")))

        elif call.data == "back_to_menu":
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))

        elif call.data == "shop":
            safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("❄️ КУПИТЬ КРИО (200 XP)", callback_data="buy_cryo"),
                types.InlineKeyboardButton("⚡️ КУПИТЬ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
                types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))

        elif call.data.startswith("buy_"):
            item = call.data.split("_")[1]
            if u['xp'] >= PRICES[item]:
                update_user_db(uid, xp=u['xp'] - PRICES[item])
                conn = get_db_connection(); cur = conn.cursor(); cur.execute(f"UPDATE users SET {item} = {item} + 1 WHERE uid = %s", (uid,)); conn.commit(); conn.close()
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "referral":
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ССЫЛКА:**\n`{link}`", get_main_menu(uid))

        elif call.data == "change_path_confirm":
            safe_edit(call, f"⚠️ **СМЕНА ФРАКЦИИ**\nЦена: 100 XP.", get_path_menu(cost_info=True))

        elif "set_path_" in call.data:
            new_path = call.data.split("_")[-1]
            if u['xp'] >= 100:
                update_user_db(uid, xp=u['xp']-100, path=new_path)
                bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ПРИНЯТ.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "use_accel":
            if u['accel'] > 0:
                update_user_db(uid, accel=u['accel']-1, accel_exp=int(now_ts+86400))
                bot.send_photo(uid, MENU_IMAGE_URL, caption="/// БУСТ АКТИВИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ ПУСТО", show_alert=True)

        elif call.data == "guide": 
            safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except Exception as e: print(f"/// CALLBACK ERROR: {e}")

# ==========================================
# 9. ЗАПУСК ДЛЯ GUNICORN (ФИКС)
# ==========================================
@app.route('/health', methods=['GET'])
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    try: bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))]); return 'OK', 200
    except: return 'Error', 500

def background_tasks():
    with app.app_context():
        try:
            init_db()
            if WEBHOOK_URL:
                bot.remove_webhook()
                time.sleep(1)
                bot.set_webhook(url=WEBHOOK_URL)
        except Exception as e: print(e)
        
        while True:
            try:
                time.sleep(60); conn = get_db_connection()
                if not conn: continue
                cur = conn.cursor(cursor_factory=RealDictCursor); cur.execute("SELECT * FROM users WHERE notified = FALSE")
                for u in cur.fetchall():
                    cd = COOLDOWN_ACCEL if u['accel_exp'] > time.time() else COOLDOWN_BASE
                    if u['last_protocol_time'] > 0 and (time.time() - u['last_protocol_time'] >= cd):
                        try: bot.send_message(u['uid'], "⚡️ READY"); update_user_db(u['uid'], notified=True)
                        except: pass
                conn.close()
            except: pass

threading.Thread(target=background_tasks, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
