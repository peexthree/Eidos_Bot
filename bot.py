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

# --- ЭКОНОМИКА И БАЛАНС ---
COOLDOWN_BASE = 1800      # 30 мин (Синхрон)
COOLDOWN_ACCEL = 900      # 15 мин (Ускоритель)
COOLDOWN_SIGNAL = 300     # 5 мин (Сигнал)
XP_GAIN = 25              # Награда за Синхрон
XP_SIGNAL = 15            # Награда за Сигнал
PATH_CHANGE_COST = 100    # Цена смены пути
REFERRAL_BONUS = 250      # Бонус за друга
RAID_COST = 100           # Цена входа в Нулевой Слой

PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# Пороги уровней
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

# Ачивки
ACHIEVEMENTS_LIST = {
    "first_steps": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: u['xp'] >= 25, "xp": 50},
    "streak_7": {"name": "🔥 СТОИК (Неделя)", "cond": lambda u: u['streak'] >= 7, "xp": 150},
    "streak_30": {"name": "🧘 ЖЕЛЕЗНЫЙ МОНАХ", "cond": lambda u: u['streak'] >= 30, "xp": 500},
    "rich_1000": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200},
    "diver_50": {"name": "🕳 СТАЛКЕР (Глубина 50)", "cond": lambda u: u.get('max_depth', 0) >= 50, "xp": 300}
}

# Сценарии Нулевого Слоя (Генератор событий)
RAID_SCENARIOS = [
    {"text": "Ты нашел кластер битых данных. Среди мусора мерцает энергия.", "type": "loot", "val": 30, "dmg": 0},
    {"text": "Системный Страж заметил твое присутствие! Удар током.", "type": "trap", "val": 0, "dmg": 15},
    {"text": "Тишина. Только гул серверов. Ты продвигаешься глубже.", "type": "empty", "val": 5, "dmg": 2},
    {"text": "Кэш удаленного аккаунта. Это чья-то стертая память.", "type": "loot", "val": 60, "dmg": 0},
    {"text": "ГЛИТЧ РЕАЛЬНОСТИ! Текстуры плывут. Ты теряешь связь.", "type": "trap", "val": 0, "dmg": 25},
    {"text": "Ты нашел «Безопасный Узел». Сигнал стабилизирован.", "type": "heal", "val": 10, "dmg": -20} # Отрицательный урон = лечение
]

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. ТЕКСТЫ И СПРАВКИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 АРХИВ ЭЙДОСА v30.0**\n\n"
    "**1. БАЗОВЫЕ ПРОТОКОЛЫ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Получение знаний и сохранение их в Архив.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие импульсы опыта.\n\n"
    "**2. 🌑 НУЛЕВОЙ СЛОЙ (RAID):**\n"
    "Опасная зона изнанки системы. Трать XP, чтобы спуститься вглубь.\n"
    "• **Вход:** 100 XP.\n"
    "• **Цель:** Собрать как можно больше XP в буфер и **Эвакуироваться**.\n"
    "• **Риск:** Если СИГНАЛ упадет до 0%, ты потеряешь всё найденное.\n\n"
    "**3. АРХИВ:**\n"
    "Все открытые протоколы сохраняются в твоем Профиле -> Архив."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО ({PRICES['cryo']} XP)**\nСтраховка серии на 1 день.\n\n"
    f"⚡️ **УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nКулдаун 15 мин на 24 часа.\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nДоступ к знаниям +1 уровня.\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

# --- 4. БАЗА ДАННЫХ ---
def get_db_connection():
    try: return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e: print(f"/// DB ERROR: {e}"); return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        
        # 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, 
                date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                path TEXT DEFAULT 'general', xp INTEGER DEFAULT 0, 
                level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1,
                last_active DATE DEFAULT CURRENT_DATE, 
                cryo INTEGER DEFAULT 0, accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0,
                accel_exp BIGINT DEFAULT 0, referrer TEXT,
                last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0,
                notified BOOLEAN DEFAULT TRUE,
                max_depth INTEGER DEFAULT 0
            );
        ''')

        # 2. КОНТЕНТ
        cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
        
        # 3. ВСПОМОГАТЕЛЬНЫЕ ТАБЛИЦЫ (v26-v30)
        cur.execute('''CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, uid BIGINT, action TEXT, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, uid BIGINT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        
        # 4. НОВЫЕ ТАБЛИЦЫ v30.0 (RAID & ARCHIVE)
        cur.execute('''CREATE TABLE IF NOT EXISTS raid_sessions (uid BIGINT PRIMARY KEY, depth INTEGER DEFAULT 0, signal INTEGER DEFAULT 100, buffer_xp INTEGER DEFAULT 0, start_time BIGINT);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_knowledge (uid BIGINT, content_id INTEGER, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, content_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, uid BIGINT, item_id TEXT, acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

        # Патчи колонок (для совместимости)
        try: cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS max_depth INTEGER DEFAULT 0;")
        except: conn.rollback()
        
        try: cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;")
        except: conn.rollback()

        conn.commit()
        print("/// EIDOS SYSTEM v30.0: DATABASE OPTIMIZED.")
    except Exception as e: print(f"/// DB INIT ERROR: {e}")
    finally: conn.close()

# --- HELPER FUNCTIONS ---
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

def save_knowledge(uid, content_id):
    """Сохраняет протокол в Нейро-Архив пользователя"""
    if not content_id: return
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO user_knowledge (uid, content_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, content_id))
        conn.commit()
    except: pass
    finally: conn.close()

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
            except: pass
    conn.commit(); conn.close()
    if new_ach:
        try: bot.send_message(uid, "🏆 **ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО:**\n" + "\n".join(new_ach))
        except: pass

def get_leaderboard():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Рейтинг теперь показывает и Глубину
        cur.execute("SELECT username, xp, level, max_depth FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        text = "🏆 **ГЛОБАЛЬНЫЙ РЕЙТИНГ**\n━━━━━━━━━━━━━━\n"
        for i, row in enumerate(rows, 1):
            icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
            uname = row[0] if row[0] else "Неизвестный"
            depth = f" | ⚓️ {row[3]}м" if row[3] > 0 else ""
            text += f"{icon} **{i}. {uname}** — {row[1]} XP{depth}\n"
        return text
    finally: conn.close()

# --- 5. ЛОГИКА XP ---
def process_xp_logic(uid, amount):
    u = get_user_from_db(uid)
    if not u: return False, None, 0
    today = datetime.now().date()
    # Фикс даты
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
    """Возвращает (id, text)"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if c_type == 'signal': 
            cur.execute("SELECT id, text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
        else: 
            cur.execute("SELECT id, text FROM content WHERE type='protocol' AND (path=%s OR path='general') AND level<=%s ORDER BY RANDOM() LIMIT 1", (path, level))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally: conn.close()

# --- 6. ЯДРО: НУЛЕВОЙ СЛОЙ (RAID ENGINE) ---
def raid_start_session(uid):
    u = get_user_from_db(uid)
    if u['xp'] < RAID_COST: return False, "❌ Недостаточно энергии (нужно 100 XP)."
    
    # Списываем XP
    update_user_db(uid, xp=u['xp'] - RAID_COST)
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Создаем сессию
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
    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
    s = cur.fetchone()
    if not s: conn.close(); return None, "Сессия не найдена."
    
    # Генерация события
    event = random.choice(RAID_SCENARIOS)
    
    # Расчеты
    new_depth = s['depth'] + 1
    dmg = event['dmg'] + random.randint(0, 5) # Случайный разброс урона
    new_signal = min(100, s['signal'] - dmg) # Не больше 100
    if direction == "left": new_signal -= 2 # Боковые ходы затратнее
    if direction == "right": new_signal -= 2
    
    new_buffer = s['buffer_xp'] + event['val']
    
    msg = ""
    is_alive = True
    
    if new_signal <= 0:
        # СМЕРТЬ
        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        msg = f"💀 **СИГНАЛ ПОТЕРЯН.**\nТы зашел слишком далеко. Аварийный выброс.\nПотеряно: {s['buffer_xp']} XP."
        is_alive = False
    else:
        # УСПЕХ
        cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, buffer_xp=%s WHERE uid=%s", (new_depth, new_signal, new_buffer, uid))
        
        # Обновляем рекорд если нужно
        u = get_user_from_db(uid)
        if new_depth > u.get('max_depth', 0):
            update_user_db(uid, max_depth=new_depth)
            
        status_icon = "🟢" if new_signal > 60 else "🟡" if new_signal > 30 else "🔴"
        msg = (f"⚓️ **ГЛУБИНА: {new_depth}**\n\n"
               f"{event['text']}\n\n"
               f"🎒 **Буфер:** {new_buffer} XP\n"
               f"📡 **Сигнал:** {status_icon} {new_signal}%")
        
    conn.commit()
    conn.close()
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
    
    # Начисляем на реальный счет
    process_xp_logic(uid, amount)
    log_event(uid, "RAID_EXTRACT", f"Amount: {amount}")
    return amount

# --- 7. ИНТЕРФЕЙС ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: 
        try: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except: pass

def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    markup.add(types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu")) # НОВАЯ КНОПКА
    markup.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"), types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"))
    markup.add(types.InlineKeyboardButton("🔗 СЕТЬ", callback_data="referral"), types.InlineKeyboardButton("📚 БАЗА", callback_data="guide"))
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
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

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None
    
    u = get_user_from_db(uid)
    if not u:
        variant = random.choice(WELCOME_VARIANTS)
        register_user_db(uid, m.from_user.username, m.from_user.first_name, ref_arg)
        # Бонус рефереру
        if ref_arg and ref_arg.isdigit():
            r_u = get_user_from_db(int(ref_arg))
            if r_u: update_user_db(int(ref_arg), xp=r_u['xp'] + REFERRAL_BONUS)
        log_event(uid, "REGISTER", f"Var: {variant}")
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=variant, reply_markup=get_main_menu(uid))
    else:
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS: СИСТЕМА В СЕТИ.", reply_markup=get_main_menu(uid))

# STATE MACHINE
user_state = {} 

@bot.message_handler(content_types=['text'])
def text_handler(m):
    uid = m.from_user.id
    state = user_state.get(uid)
    
    if state == 'diary_wait':
        save_note(uid, m.text)
        bot.send_message(uid, "💾 **ЗАПИСАНО.**", reply_markup=get_main_menu(uid))
        user_state.pop(uid)
        
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
        
        target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
        if u['decoder'] > 0: update_user_db(uid, decoder=u['decoder']-1)
        
        content_id, txt = get_content('protocol', u['path'], target_lvl)
        if not txt: txt = "/// ДАННЫЕ НЕ НАЙДЕНЫ. ОЖИДАНИЕ ОБНОВЛЕНИЯ."
        else: save_knowledge(uid, content_id) # СОХРАНЯЕМ В АРХИВ
        
        msg = f"🧬 **{SCHOOLS.get(u['path'], 'ОБЩИЙ')}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
        if up: bot.send_message(uid, f"🎉 **{LEVEL_UP_MSG.get(u['level'], 'LEVEL UP!')}**")
        safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

    elif call.data == "get_signal":
        if now - u['last_signal_time'] < COOLDOWN_SIGNAL:
            bot.answer_callback_query(call.id, "⏳ Жди...", show_alert=True); return
        update_user_db(uid, last_signal_time=int(now))
        process_xp_logic(uid, XP_SIGNAL)
        cid, txt = get_content('signal', 'general', 1)
        if not txt: txt = "/// ЭФИР ПУСТ."
        bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{txt}\n\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

    # --- ЛОГИКА НУЛЕВОГО СЛОЯ ---
    elif call.data == "zero_layer_menu":
        msg = (f"🌑 **НУЛЕВОЙ СЛОЙ**\n"
               f"Зона высокого риска. Изнанка системы.\n\n"
               f"🎫 **ВХОД:** {RAID_COST} XP\n"
               f"⚓️ **ТВОЙ РЕКОРД:** {u.get('max_depth', 0)} м.\n\n"
               f"Правила:\n1. Трать Сигнал на шаги.\n2. Собирай XP в Буфер.\n3. Жми «Эвакуация», чтобы спасти награду.\n4. Сигнал 0% = Смерть (потеря всего).")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"🌪 НАЧАТЬ ПОГРУЖЕНИЕ (-{RAID_COST} XP)", callback_data="raid_start_confirm"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)
        
    elif call.data == "raid_start_confirm":
        success, msg = raid_start_session(uid)
        if success:
            safe_edit(call, msg, get_raid_keyboard())
        else:
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
    elif call.data.startswith("raid_step_"):
        direction = call.data.split("_")[2] # left, forward, right
        is_alive, msg = raid_process_step(uid, direction)
        if is_alive:
            safe_edit(call, msg, get_raid_keyboard())
        else:
            # Game Over
            safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back_to_menu")))
            
    elif call.data == "raid_extract_confirm":
        amount = raid_extract(uid)
        msg = f"📦 **УСПЕШНАЯ ЭВАКУАЦИЯ.**\n\nСохранено: {amount} XP.\nСигнал восстановлен."
        safe_edit(call, msg, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back_to_menu")))

    # --- ПРОФИЛЬ И АРХИВ ---
    elif call.data == "profile":
        conn=get_db_connection(); cur=conn.cursor(); cur.execute("SELECT COUNT(*) FROM users WHERE referrer=%s", (str(uid),)); refs=cur.fetchone()[0]; 
        cur.execute("SELECT COUNT(*) FROM achievements WHERE uid=%s", (uid,)); achs=cur.fetchone()[0]; 
        # Считаем открытые знания
        cur.execute("SELECT COUNT(*) FROM user_knowledge WHERE uid=%s", (uid,)); k_count=cur.fetchone()[0]; conn.close()

        bar = "||" * int((u['xp']%500)/50) + ".." * (10 - int((u['xp']%500)/50))
        msg = (f"👤 **{u['username']}** | {TITLES.get(u['level'], '...')}\n"
               f"━━━━━━━━━━━━━━\n"
               f"🔋 **XP:** {u['xp']} `[{bar}]`\n"
               f"⚔️ **Фракция:** {u['path']}\n"
               f"🔥 **Стрик:** {u['streak']} дн.\n"
               f"📚 **Архив:** {k_count} прот. | ⚓️ **Глубина:** {u.get('max_depth', 0)}м\n"
               f"━━━━━━━━━━━━━━\n"
               f"🎒 **Склад:** ❄️{u['cryo']} ⚡️{u['accel']} 🔑{u['decoder']}")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📚 ЧИТАТЬ АРХИВ", callback_data="open_archive"))
        markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path_confirm"))
        if u['accel'] > 0 and u['accel_exp'] < now: markup.add(types.InlineKeyboardButton("🚀 БУСТ", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)

    elif call.data == "open_archive":
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("""
            SELECT c.text FROM user_knowledge k 
            JOIN content c ON k.content_id = c.id 
            WHERE k.uid = %s ORDER BY k.unlocked_at DESC LIMIT 5
        """, (uid,))
        rows = cur.fetchall(); conn.close()
        
        if not rows:
            bot.answer_callback_query(call.id, "Архив пуст. Делай Синхрон.", show_alert=True)
            return

        text = "**📚 ПОСЛЕДНИЕ ОТКРЫТИЯ:**\n\n"
        for i, r in enumerate(rows, 1):
            preview = r[0].split('\n')[0][:50] + "..."
            text += f"{i}. {preview}\n"
        
        safe_edit(call, text, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="profile")))

    # --- ОСТАЛЬНОЕ ---
    elif call.data == "leaderboard":
        safe_edit(call, get_leaderboard(), types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "diary_mode":
        user_state[uid] = 'diary_wait'
        safe_edit(call, "📓 **ДНЕВНИК**\nПиши. Я запомню.", types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data == "shop":
        safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("❄️ КРИО (200 XP)", callback_data="buy_cryo"),
            types.InlineKeyboardButton("⚡️ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
            types.InlineKeyboardButton("🔑 ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"),
            types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            update_user_db(uid, xp=u['xp']-PRICES[item])
            conn=get_db_connection(); cur=conn.cursor(); cur.execute(f"UPDATE users SET {item}={item}+1 WHERE uid=%s", (uid,)); conn.commit(); conn.close()
            bot.answer_callback_query(call.id, "✅"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP")
    elif call.data == "change_path_confirm":
        safe_edit(call, "⚠️ Выбери путь (-100 XP):", types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("🔴 МАТЕРИЯ", callback_data="set_path_money"),
            types.InlineKeyboardButton("🔵 РАЗУМ", callback_data="set_path_mind"),
            types.InlineKeyboardButton("🟣 СИНГУЛЯРНОСТЬ", callback_data="set_path_tech"),
            types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))
    elif "set_path_" in call.data:
        path = call.data.split("_")[2]
        cost = 0 if u['path'] == 'general' else 100
        if u['xp'] >= cost:
            if cost > 0: update_user_db(uid, xp=u['xp']-cost)
            update_user_db(uid, path=path)
            bot.send_message(uid, f"/// ПУТЬ: {path.upper()}", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP")
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS: ONLINE", reply_markup=get_main_menu(uid))

    # ADMIN
    elif call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ ADMIN", get_admin_menu())
    elif call.data == "adm_add_signal" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_signal'}; bot.send_message(uid, "✍️ Текст:")
    elif call.data == "adm_add_proto" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_proto'}; bot.send_message(uid, "✍️ `path|level|text`:")
    elif call.data == "admin_stats" and uid == ADMIN_ID:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM logs"); logs = cur.fetchone()[0]
        conn.close()
        bot.answer_callback_query(call.id, f"U: {total} | L: {logs}", show_alert=True)

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
                        bot.send_message(u['uid'], "⚡️ **ГОТОВНОСТЬ 100%.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 СИНХРОН", callback_data="get_protocol")))
                        update_user_db(u['uid'], notified=True)
                    except: pass
            conn.close()
        except: pass

# --- ЗАПУСК ---
@app.route('/health', methods=['GET'])
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    try: bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))]); return 'OK', 200
    except: return 'Error', 500

def system_startup():
    with app.app_context():
        time.sleep(2); init_db()
        if WEBHOOK_URL:
            try: bot.remove_webhook(); bot.set_webhook(url=WEBHOOK_URL)
            except: pass
        notification_worker()

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
