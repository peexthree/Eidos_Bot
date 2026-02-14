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
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# --- СИСТЕМА ДОСТИЖЕНИЙ (ACHIEVEMENTS) ---
ACHIEVEMENTS_LIST = {
    "first_steps": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: u['xp'] >= 25, "xp": 50},
    "streak_7": {"name": "🔥 СТОИК (Неделя)", "cond": lambda u: u['streak'] >= 7, "xp": 150},
    "streak_30": {"name": "🧘 ЖЕЛЕЗНЫЙ МОНАХ (30 дней)", "cond": lambda u: u['streak'] >= 30, "xp": 500},
    "rich_1000": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200},
    "lvl_3": {"name": "🧠 ОПЕРАТОР (Lvl 3)", "cond": lambda u: u['level'] >= 3, "xp": 300}
}

# --- A/B TESTING VARIANTS ---
WELCOME_VARIANTS = [
    "/// EIDOS OS: ЗАГРУЗКА СОЗНАНИЯ...\nДобро пожаловать в тренажер реальности.",
    "/// ВНИМАНИЕ: Обнаружен потенциал.\nЭйдос приветствует нового Архитектора.",
    "/// СИСТЕМА АКТИВНА.\nТвоя старая жизнь — это черновик. Начинаем чистовик."
]

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. ТЕКСТОВЫЕ МОДУЛИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v27.0**\n\n"
    "**1. ИСТОЧНИКИ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы. Награда: **25 XP**.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие ментальные импульсы. Награда: **15 XP**.\n\n"
    "**2. НОВЫЕ МОДУЛИ:**\n"
    "• 📓 **ДНЕВНИК:** Приватная база твоих инсайтов.\n"
    "• 🏆 **РЕЙТИНГ:** Глобальная конкуренция умов.\n"
    "• 🎖 **АЧИВКИ:** Награды за дисциплину.\n\n"
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

# --- 4. БАЗА ДАННЫХ (EXPANDED) ---
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
        
        # 1. Основные таблицы (Пользователи)
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
                last_signal_time BIGINT DEFAULT 0,
                notified BOOLEAN DEFAULT TRUE
            );
        ''')
        # 2. Контент
        cur.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id SERIAL PRIMARY KEY,
                type TEXT,
                path TEXT,
                text TEXT,
                level INTEGER DEFAULT 1
            );
        ''')
        
        # 3. НОВЫЕ ТАБЛИЦЫ (v27.0 - ПАМЯТЬ, АЧИВКИ, ДНЕВНИК)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                uid BIGINT,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                uid BIGINT,
                ach_id TEXT,
                date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(uid, ach_id)
            );
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                uid BIGINT,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Патч notified (на всякий случай)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;")
            conn.commit()
        except: conn.rollback()

        conn.commit()
        print("/// DB STRUCTURE VERIFIED (FULL SCALE).")
    except Exception as e:
        print(f"/// DB INIT ERROR: {e}")
    finally:
        if conn: conn.close()

# --- HELPER FUNCTIONS FOR DB ---
def log_event(uid, action, details=""):
    """Протокол ПАМЯТЬ УЗЛА: Пишет действие в БД асинхронно"""
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
        # Логируем регистрацию
        log_event(uid, "REGISTER", f"Ref: {referrer}")
    finally:
        conn.close()

def get_referral_count(uid):
    conn = get_db_connection()
    if not conn: return 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),))
        count = cur.fetchone()[0]
        return count
    except:
        return 0
    finally:
        conn.close()

def save_note(uid, text):
    """Сохраняет запись в Нейро-Дневник"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO notes (uid, text) VALUES (%s, %s)", (uid, text))
        conn.commit()
    finally: conn.close()

def get_leaderboard_text():
    """Генерирует текст Глобального Рейтинга"""
    conn = get_db_connection()
    if not conn: return "/// ОШИБКА СВЯЗИ С РЕЙТИНГОМ"
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, xp, level FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        text = "🏆 **ГЛОБАЛЬНЫЙ РЕЙТИНГ АРХИТЕКТОРОВ**\n━━━━━━━━━━━━━━\n"
        for i, row in enumerate(rows, 1):
            icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            uname = row[0] if row[0] else "Неизвестный"
            text += f"{icon} **{i}. {uname}** — {row[1]} XP (Lvl {row[2]})\n"
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
    """Проверка и выдача ачивок"""
    u = get_user_from_db(uid)
    if not u: return
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Какие уже есть?
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
    if level >= 6: return "`[||||||||||] MAX`"
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
        
        # A/B TESTING: Выбор и логирование варианта приветствия
        welcome_msg = random.choice(WELCOME_VARIANTS)
        log_event(uid, "REGISTER", f"Variant: {WELCOME_VARIANTS.index(welcome_msg)}")
    else:
        welcome_msg = "/// EIDOS-OS: СИСТЕМА ПЕРЕЗАГРУЖЕНА."
        log_event(uid, "RESTART")
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

# --- ОБРАБОТЧИК ТЕКСТА (ДЛЯ ДНЕВНИКА И АДМИНКИ) ---
user_action_state = {} 

@bot.message_handler(content_types=['text'])
def text_input_handler(m):
    uid = m.from_user.id
    state = user_action_state.get(uid)
    
    # 1. Обработка Дневника
    if state and state.get('type') == 'diary_wait':
        save_note(uid, m.text)
        log_event(uid, "DIARY_ENTRY")
        bot.send_message(uid, "💾 **ЗАПИСЬ СОХРАНЕНА В НЕЙРО-ДНЕВНИК.**", reply_markup=get_main_menu(uid))
        user_action_state.pop(uid)
        return

    # 2. Обработка Админки (только для ADMIN_ID)
    if uid == ADMIN_ID and state:
        if state['step'] == 'wait_signal_text':
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO content (type, path, text, level) VALUES ('signal', 'general', %s, 1)", (m.text,))
            conn.commit()
            conn.close()
            bot.send_message(ADMIN_ID, "✅ **СИГНАЛ ЗАГРУЖЕН В БАЗУ.**")
            user_action_state.pop(ADMIN_ID)
            
        elif state['step'] == 'wait_proto_text':
            try:
                path, level, text = m.text.split('|', 2)
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO content (type, path, text, level) VALUES ('protocol', %s, %s, %s)", (path.strip(), text.strip(), int(level)))
                conn.commit()
                conn.close()
                bot.send_message(ADMIN_ID, f"✅ **ПРОТОКОЛ ({path}) ЗАГРУЖЕН.**")
            except:
                bot.send_message(ADMIN_ID, "❌ Ошибка формата. Надо: `path|level|text`")
            user_action_state.pop(ADMIN_ID)

        elif state['step'] == 'wait_user_id':
            uid_target = int(m.text) if m.text.isdigit() else 0
            u = get_user_from_db(uid_target)
            if u:
                msg = (f"👤 **DOSSIER ID:** `{u['uid']}`\n"
                       f"Name: {u['username']}\n"
                       f"XP: {u['xp']} | LVL: {u['level']}\n"
                       f"Path: {u['path']} | Streak: {u['streak']}\n"
                       f"Inv: Cryo={u['cryo']}, Accel={u['accel']}, Dec={u['decoder']}")
                bot.send_message(ADMIN_ID, msg)
            else:
                bot.send_message(ADMIN_ID, "❌ Пользователь не найден в БД.")
            user_action_state.pop(ADMIN_ID)

# --- АДМИН HANDLER ДЛЯ КОМАНД ---
@bot.message_handler(content_types=['text', 'photo'])
def admin_cmd_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': 
            init_db() 
            bot.send_message(message.chat.id, "✅ Структура БД проверена.")
        
        elif message.text and message.text.startswith('/telegraph '):
            parts = message.text.split(maxsplit=2)
            if len(parts) >= 2:
                url, text = parts[1], parts[2] if len(parts) > 2 else "/// АРХИВ ДЕШИФРОВАН"
                clean_url = url.split("google.com/search?q=")[-1] if "google.com" in url else url
                markup = types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("📂 ОТКРЫТЬ ДОСЬЕ", url=clean_url),
                    types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=signal")
                )
                bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ВОЙТИ В ТЕРМИНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=channel"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/ban '): 
            try:
                target_id = int(message.text.split()[1])
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE uid = %s", (target_id,))
                conn.commit()
                conn.close()
                bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} СТЕРТ ИЗ РЕАЛЬНОСТИ.")
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
        bot.answer_callback_query(call.id, "⚠️ Нажми /start для инициализации", show_alert=True); return
    
    now_ts = time.time()
    # 1. ЛОГИРОВАНИЕ ДЕЙСТВИЯ
    log_event(uid, "CLICK", call.data)

    try:
        if call.data == "admin_panel" and uid == ADMIN_ID: 
            safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ АРХИТЕКТОРА**", get_admin_menu())
        
        elif call.data == "adm_add_signal" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_signal_text'}
            bot.send_message(uid, "✍️ **Введи текст нового СИГНАЛА:**")
            
        elif call.data == "adm_add_proto" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_proto_text'}
            bot.send_message(uid, "✍️ **Введи ПРОТОКОЛ:**\n`money|1|Текст протокола`")

        elif call.data == "adm_view_user" and uid == ADMIN_ID:
            user_action_state[uid] = {'step': 'wait_user_id'}
            bot.send_message(uid, "🔎 **Введи Telegram ID:**")

        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET xp = xp + 100")
            count = cur.rowcount
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, f"🎁 Выдано по 100 XP {count} узлам")

        elif call.data == "admin_stats" and uid == ADMIN_ID:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE referrer = 'inst'")
            inst = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM logs")
            logs_count = cur.fetchone()[0]
            conn.close()
            bot.answer_callback_query(call.id, f"📊 Узлы: {total} | Логи: {logs_count}\n📸 Instagram: {inst}", show_alert=True)

        elif call.data == "get_protocol":
            is_accel_active = u['accel_exp'] > now_ts
            cd = COOLDOWN_ACCEL if is_accel_active else COOLDOWN_BASE
            
            if now_ts - u['last_protocol_time'] < cd:
                rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
            
            update_user_db(uid, last_protocol_time=int(now_ts), notified=False)
            
            up, s_msg, total = process_xp_logic(uid, XP_GAIN, is_sync=True)
            u = get_user_from_db(uid) 
            
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: update_user_db(uid, decoder=u['decoder'] - 1)
            
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
            
            def dec_task():
                status_msg = bot.send_message(uid, "📡 **ИНИЦИАЛИЗАЦИЯ...**")
                time.sleep(1)
                bot.edit_message_text(f"🔓 **ДЕШИФРОВКА...**\n`[||||||||..] 84%`", uid, status_msg.message_id, parse_mode="Markdown")
                time.sleep(0.8)
                
                txt = get_content('protocol', u['path'], target_lvl) or "/// НЕТ ДАННЫХ В ЭТОМ СЕКТОРЕ. Жди обновлений базы."
                school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
                res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
                
                bot.edit_message_text(res, uid, status_msg.message_id, parse_mode="Markdown", 
                                     reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
            threading.Thread(target=dec_task).start()

        elif call.data == "get_signal":
            if now_ts - u['last_signal_time'] < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u['last_signal_time'])) / 60)
                bot.answer_callback_query(call.id, f"📡 СИГНАЛ НЕ ГОТОВ. Жди {rem} мин.", show_alert=True); return
            
            update_user_db(uid, last_signal_time=int(now_ts))
            up, s_msg, total = process_xp_logic(uid, XP_SIGNAL)
            
            txt = get_content('signal', 'general', 1) or "/// ЭФИР ПУСТ. Архитектор еще не загрузил данные."
            
            bot.send_message(uid, f"📶 **ПОЛУЧЕН СИГНАЛ**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

        elif call.data == "profile":
            u = get_user_from_db(uid) 
            title = TITLES.get(u['level'], "НЕОФИТ")
            progress = get_progress_bar(u['xp'], u['level'])
            accel_status = "✅ АКТИВЕН" if u['accel_exp'] > now_ts else "❌ НЕ АКТИВЕН"
            
            # Считаем рефералов и ачивки
            ref_count = get_referral_count(uid)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM achievements WHERE uid = %s", (uid,))
            ach_count = cur.fetchone()[0]
            conn.close()
            
            msg = (f"👤 **НЕЙРО-ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n"
                   f"🔰 **СТАТУС:** {title}\n"
                   f"⚔️ **ФРАКЦИЯ:** {SCHOOLS.get(u['path'], 'ОБЩИЙ ПОТОК')}\n"
                   f"🔋 **SYNC:** {u['xp']} XP\n{progress}\n"
                   f"🔥 **STREAK:** {u['streak']} дн. (Бонус: +{u['streak']*5} XP)\n"
                   f"👥 **СЕТЬ:** {ref_count} узлов | 🏆 **АЧИВКИ:** {ach_count}\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🎒 **ИНВЕНТАРЬ:**\n❄️ Крио: {u['cryo']}\n⚡️ Ускоритель: {accel_status}\n🔑 Дешифратор: {u['decoder']}")
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            if u['accel'] > 0 and u['accel_exp'] < now_ts:
                markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ВЕКТОР", callback_data="change_path_confirm"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

        # 3. ЛОГИКА РЕЙТИНГА
        elif call.data == "leaderboard":
            text = get_leaderboard_text()
            safe_edit(call, text, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))

        # 4. ЛОГИКА ДНЕВНИКА
        elif call.data == "diary_mode":
            user_action_state[uid] = {'type': 'diary_wait'}
            msg = "📓 **РЕЖИМ НЕЙРО-ДНЕВНИКА**\n\nНапиши любой инсайт, мысль или отчет за день. Я сохраню это в вечной памяти.\n\n*Ожидаю ввод...*"
            safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back_to_menu")))

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
                update_user_db(uid, xp=u['xp'] - PRICES[item])
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE users SET {item} = {item} + 1 WHERE uid = %s", (uid,))
                conn.commit()
                conn.close()
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item.upper()}"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
                log_event(uid, "BUY", item)
            else: bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО SYNC", show_alert=True)

        elif call.data == "referral":
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ТВОЯ ПЕРСОНАЛЬНАЯ ССЫЛКА:**\n`{link}`", get_main_menu(uid))

        elif call.data == "change_path_confirm":
            safe_edit(call, f"⚠️ **СМЕНА ФРАКЦИИ**\nЦена: **{PATH_CHANGE_COST} SYNC**.", get_path_menu(cost_info=True))

        elif "set_path_" in call.data:
            new_path = call.data.split("_")[-1]
            if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
                if u['path'] != 'general' and u['path'] != new_path: 
                    update_user_db(uid, xp=u['xp'] - PATH_CHANGE_COST)
                update_user_db(uid, path=new_path)
                bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
                log_event(uid, "PATH_CHANGE", new_path)
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "use_accel":
            if u['accel'] > 0:
                update_user_db(uid, accel=u['accel'] - 1, accel_exp=int(now_ts + 86400))
                bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН. КУЛДАУН: 15 МИН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕТ УСКОРИТЕЛЯ", show_alert=True)

        elif call.data == "guide": 
            safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except Exception as e: print(f"/// CALLBACK ERROR: {e}")

# --- 9. ЗАПУСК И МАРШРУТЫ (SAFE BOOT PROTOCOL) ---
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'OK', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'Error', 500
    return 'Eidos SQL Interface is Operational', 200

# ФОНОВЫЙ ЗАПУСК СИСТЕМ (ЧТОБЫ НЕ БЛОКИРОВАТЬ СТАРТ)
def system_startup():
    with app.app_context():
        # Даем серверу продышаться перед нагрузкой
        time.sleep(2)
        print("/// SYSTEM STARTUP INITIATED...")
        init_db()
        if WEBHOOK_URL:
            try:
                bot.remove_webhook()
                bot.set_webhook(url=WEBHOOK_URL)
                print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
            except Exception as e:
                print(f"/// WEBHOOK ERROR: {e}")
        # Запускаем воркер уведомлений
        notification_worker()

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
