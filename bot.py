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

# --- ЭКОНОМИКА И ГЕЙМИФИКАЦИЯ ---
COOLDOWN_BASE = 1800
COOLDOWN_ACCEL = 900
COOLDOWN_SIGNAL = 300
XP_GAIN = 25
XP_SIGNAL = 15
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000, 5: 5000, 6: 10000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР", 5: "ДЕМИУРГ", 6: "ЭЙДОС"}

ACHIEVEMENTS_LIST = {
    "first_blood": {"name": "🩸 ПЕРВАЯ КРОВЬ", "cond": lambda u: True, "xp": 10}, # Дается при первом действии
    "streak_7": {"name": "🔥 СТОИК (7 дней)", "cond": lambda u: u['streak'] >= 7, "xp": 100},
    "lvl_3": {"name": "🧠 ОПЕРАТОР (Lvl 3)", "cond": lambda u: u['level'] >= 3, "xp": 300},
    "rich": {"name": "💎 МАГНАТ (1000 XP)", "cond": lambda u: u['xp'] >= 1000, "xp": 200}
}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. ТЕКСТОВЫЕ МОДУЛИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 АРХИВ ЭЙДОСА v26.0**\n\n"
    "**1. МЕХАНИКА:**\n"
    "• 👁 **СИНХРОН:** Основной источник знаний (+25 XP).\n"
    "• 📓 **ДНЕВНИК:** Твоя приватная база инсайтов.\n"
    "• 🏆 **РЕЙТИНГ:** Глобальная конкуренция умов.\n\n"
    "**2. ЭКОНОМИКА:**\n"
    "XP — это валюта. Покупай артефакты, меняй судьбу."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО ({PRICES['cryo']} XP)**\nЗаморозка стрика на 1 день.\n\n"
    f"⚡️ **УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nСнижение кулдауна до 15 мин (24ч).\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nДоступ к знаниям +1 уровня.\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

# A/B TESTING VARIANTS
WELCOME_VARIANTS = [
    "/// EIDOS OS: ЗАГРУЗКА СОЗНАНИЯ...\nДобро пожаловать в тренажер реальности.",
    "/// ВНИМАНИЕ: Обнаружен потенциал.\nЭйдос приветствует нового Архитектора.",
    "/// СИСТЕМА АКТИВНА.\nТвоя старая жизнь — это черновик. Начинаем чистовик."
]

# --- 4. БАЗА ДАННЫХ ---
def get_db_connection():
    try: return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e: print(f"/// DB ERROR: {e}"); return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    try:
        cur = conn.cursor()
        
        # Основные таблицы
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, username TEXT, first_name TEXT, date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                path TEXT DEFAULT 'general', xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, streak INTEGER DEFAULT 1,
                last_active DATE DEFAULT CURRENT_DATE, prestige INTEGER DEFAULT 0, cryo INTEGER DEFAULT 0,
                accel INTEGER DEFAULT 0, decoder INTEGER DEFAULT 0, accel_exp BIGINT DEFAULT 0, referrer TEXT,
                last_protocol_time BIGINT DEFAULT 0, last_signal_time BIGINT DEFAULT 0, notified BOOLEAN DEFAULT TRUE
            );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS content (id SERIAL PRIMARY KEY, type TEXT, path TEXT, text TEXT, level INTEGER DEFAULT 1);''')
        
        # НОВЫЕ ТАБЛИЦЫ (v26.0)
        cur.execute('''CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, uid BIGINT, action TEXT, details TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS achievements (uid BIGINT, ach_id TEXT, date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(uid, ach_id));''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, uid BIGINT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

        # Патч notified (на всякий случай)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT TRUE;")
            conn.commit()
        except: conn.rollback()

        conn.commit()
        print("/// DB v26.0 STRUCTURE VERIFIED.")
    except Exception as e: print(f"/// DB INIT ERROR: {e}")
    finally: conn.close()

# --- HELPER FUNCTIONS ---
def log_event(uid, action, details=""):
    """Пишет действие в таблицу logs"""
    threading.Thread(target=lambda: _async_log(uid, action, details)).start()

def _async_log(uid, action, details):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO logs (uid, action, details) VALUES (%s, %s, %s)", (uid, action, details))
            conn.commit()
        except: pass
        finally: conn.close()

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

def check_achievements(uid):
    """Проверяет и выдает ачивки"""
    u = get_user_from_db(uid)
    if not u: return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем уже полученные
    cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
    existing = set(row[0] for row in cur.fetchall())
    
    new_achieved = []
    
    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if ach_id not in existing and data['cond'](u):
            try:
                cur.execute("INSERT INTO achievements (uid, ach_id) VALUES (%s, %s)", (uid, ach_id))
                # Награда за ачивку
                update_user_db(uid, xp=u['xp'] + data['xp'])
                new_achieved.append(f"{data['name']} (+{data['xp']} XP)")
            except: pass
    
    conn.commit()
    conn.close()
    
    if new_achieved:
        msg = "🏆 **НОВЫЕ ДОСТИЖЕНИЯ:**\n" + "\n".join(new_achieved)
        try: bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

def get_leaderboard():
    conn = get_db_connection()
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

def save_note(uid, text):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO notes (uid, text) VALUES (%s, %s)", (uid, text))
        conn.commit()
    finally: conn.close()

# --- 5. ЛОГИКА XP ---
def process_xp_logic(uid, amount):
    u = get_user_from_db(uid)
    if not u: return False, None, 0
    
    today = datetime.now().date()
    last_date = u['last_active'] if isinstance(u['last_active'], (datetime, float, int)) else datetime.strptime(str(u['last_active']), "%Y-%m-%d").date()
    
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
    
    # Рефералка
    if u['referrer'] and u['referrer'].isdigit():
        try:
            ref_id = int(u['referrer'])
            r_u = get_user_from_db(ref_id)
            if r_u: update_user_db(ref_id, xp=r_u['xp'] + int(total*0.1))
        except: pass

    # Уровни
    new_lvl = u['level']
    for lvl, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr:
            new_lvl = lvl
            break
            
    update_user_db(uid, xp=new_xp, level=new_lvl)
    
    # Проверка ачивок после начисления XP
    threading.Thread(target=check_achievements, args=(uid,)).start()
    
    return (new_lvl > u['level']), s_msg, total

def get_content(c_type, path, level):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if c_type == 'signal': cur.execute("SELECT text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
        else: cur.execute("SELECT text FROM content WHERE type='protocol' AND (path=%s OR path='general') AND level<=%s ORDER BY RANDOM() LIMIT 1", (path, level))
        row = cur.fetchone()
        return row[0] if row else None
    finally: conn.close()

# --- 6. ИНТЕРФЕЙС ---
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    markup.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"), types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"))
    markup.add(types.InlineKeyboardButton("🔗 СЕТЬ", callback_data="referral"), types.InlineKeyboardButton("📚 БАЗА", callback_data="guide"))
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return markup

def get_admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ СИГНАЛ", callback_data="adm_add_signal"),
        types.InlineKeyboardButton("➕ ПРОТОКОЛ", callback_data="adm_add_proto"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
    )
    return markup

# --- 7. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None
    
    u = get_user_from_db(uid)
    if not u:
        conn = get_db_connection()
        cur = conn.cursor()
        # A/B TESTING: Выбираем вариант приветствия и пишем в базу
        variant = random.choice(WELCOME_VARIANTS)
        try:
            cur.execute("INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", 
                        (uid, f"@{m.from_user.username}", m.from_user.first_name, str(ref_arg or '')))
            conn.commit()
            log_event(uid, "REGISTER", f"Ref: {ref_arg} | Variant: {WELCOME_VARIANTS.index(variant)}")
            
            # Бонус рефереру
            if ref_arg and ref_arg.isdigit():
                r_u = get_user_from_db(int(ref_arg))
                if r_u: update_user_db(int(ref_arg), xp=r_u['xp'] + REFERRAL_BONUS)
        finally: conn.close()
        
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=variant, reply_markup=get_main_menu(uid))
    else:
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА ПЕРЕЗАГРУЖЕНА.", reply_markup=get_main_menu(uid))

# STATE MACHINE ДЛЯ ДНЕВНИКА И АДМИНКИ
user_state = {} 

@bot.message_handler(content_types=['text'])
def text_handler(m):
    uid = m.from_user.id
    state = user_state.get(uid)
    
    if state == 'diary_wait':
        save_note(uid, m.text)
        log_event(uid, "NOTE_SAVED")
        bot.send_message(uid, "💾 **МЫСЛЬ ЗАПИСАНА В НЕЙРОСЕТЬ.**", reply_markup=get_main_menu(uid))
        user_state.pop(uid)
        
    elif uid == ADMIN_ID and state:
        if state['step'] == 'wait_signal':
            conn = get_db_connection(); cur = conn.cursor(); cur.execute("INSERT INTO content (type, path, text) VALUES ('signal', 'general', %s)", (m.text,)); conn.commit(); conn.close()
            bot.send_message(uid, "✅"); user_state.pop(uid)
        elif state['step'] == 'wait_proto':
            try:
                p, l, t = m.text.split('|', 2)
                conn = get_db_connection(); cur = conn.cursor(); cur.execute("INSERT INTO content (type, path, level, text) VALUES ('protocol', %s, %s, %s)", (p.strip(), int(l), t.strip())); conn.commit(); conn.close()
                bot.send_message(uid, "✅"); user_state.pop(uid)
            except: bot.send_message(uid, "❌ Format error")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    u = get_user_from_db(uid)
    if not u: bot.answer_callback_query(call.id, "Нажми /start"); return
    
    now = time.time()
    log_event(uid, "CLICK", call.data) # LOGGING EVERY CLICK

    try:
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
            
            if up: bot.send_message(uid, f"🎉 **{LEVEL_UP_MSG.get(u['level'], 'LEVEL UP!')}**")
            
            txt = get_content('protocol', u['path'], target_lvl) or "/// БАЗА ОБНОВЛЯЕТСЯ..."
            msg = f"🧬 **{SCHOOLS.get(u['path'], 'ОБЩИЙ')}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC"
            
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

        elif call.data == "get_signal":
            if now - u['last_signal_time'] < COOLDOWN_SIGNAL:
                bot.answer_callback_query(call.id, "⏳ Жди...", show_alert=True); return
            
            update_user_db(uid, last_signal_time=int(now))
            process_xp_logic(uid, XP_SIGNAL)
            txt = get_content('signal', 'general', 1) or "/// ТИШИНА В ЭФИРЕ."
            bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{txt}\n\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

        elif call.data == "leaderboard":
            safe_edit(call, get_leaderboard(), types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu")))

        elif call.data == "diary_mode":
            user_state[uid] = 'diary_wait'
            safe_edit(call, "📓 **НЕЙРО-ДНЕВНИК**\n\nНапиши любой инсайт, мысль или план. Я сохраню это в вечной памяти.\n\n*Ожидаю ввод...*", types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back_to_menu")))

        elif call.data == "profile":
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE referrer = %s", (str(uid),))
            refs = cur.fetchone()[0]
            conn.close()
            
            # Получаем ачивки
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM achievements WHERE uid = %s", (uid,))
            ach_count = cur.fetchone()[0]; conn.close()

            bar = "||" * int((u['xp']%500)/50) + ".." * (10 - int((u['xp']%500)/50)) # Простой бар
            msg = (f"👤 **{u['username']}** | {TITLES.get(u['level'], 'NOBODY')}\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🔋 **XP:** {u['xp']} `[{bar}]`\n"
                   f"⚔️ **Фракция:** {u['path']}\n"
                   f"🔥 **Стрик:** {u['streak']} дн.\n"
                   f"👥 **Сеть:** {refs} | 🏆 **Ачивки:** {ach_count}\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🎒 **Склад:** ❄️{u['cryo']} ⚡️{u['accel']} 🔑{u['decoder']}")
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path_confirm"))
            if u['accel'] > 0 and u['accel_exp'] < now: markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ БУСТ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("🔙", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

        elif call.data == "shop":
            safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("❄️ КРИО (200 XP)", callback_data="buy_cryo"),
                types.InlineKeyboardButton("⚡️ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
                types.InlineKeyboardButton("🔑 ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"),
                types.InlineKeyboardButton("🔙", callback_data="back_to_menu")
            ))

        elif call.data.startswith("buy_"):
            item = call.data.split("_")[1]
            if u['xp'] >= PRICES[item]:
                update_user_db(uid, xp=u['xp']-PRICES[item])
                conn=get_db_connection(); cur=conn.cursor(); cur.execute(f"UPDATE users SET {item}={item}+1 WHERE uid=%s", (uid,)); conn.commit(); conn.close()
                bot.answer_callback_query(call.id, "✅ КУПЛЕНО"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
                log_event(uid, "BUY", item)
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP")

        elif call.data == "change_path_confirm":
            safe_edit(call, "⚠️ Выбери путь (-100 XP):", types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("🔴 МАТЕРИЯ (Деньги/Бизнес)", callback_data="set_path_money"),
                types.InlineKeyboardButton("🔵 РАЗУМ (Психология/Мозг)", callback_data="set_path_mind"),
                types.InlineKeyboardButton("🟣 СИНГУЛЯРНОСТЬ (AI/Tech)", callback_data="set_path_tech"),
                types.InlineKeyboardButton("🔙", callback_data="back_to_menu")
            ))

        elif "set_path_" in call.data:
            path = call.data.split("_")[2]
            cost = 0 if u['path'] == 'general' else 100
            if u['xp'] >= cost:
                if cost > 0: update_user_db(uid, xp=u['xp']-cost)
                update_user_db(uid, path=path)
                bot.send_message(uid, f"/// ПУТЬ ПРИНЯТ: {path.upper()}", reply_markup=get_main_menu(uid))
                log_event(uid, "CHANGE_PATH", path)
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP")

        elif call.data == "back_to_menu":
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS: ONLINE", reply_markup=get_main_menu(uid))

        # ADMIN
        elif call.data == "admin_panel" and uid == ADMIN_ID: safe_edit(call, "⚙️ ADMIN CORE", get_admin_menu())
        elif call.data == "adm_add_signal" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_signal'}; bot.send_message(uid, "✍️ Текст:")
        elif call.data == "adm_add_proto" and uid == ADMIN_ID: user_state[uid] = {'step': 'wait_proto'}; bot.send_message(uid, "✍️ `path|level|text`:")
        elif call.data == "admin_stats" and uid == ADMIN_ID:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM logs"); logs = cur.fetchone()[0]
            conn.close()
            bot.answer_callback_query(call.id, f"Users: {total} | Logs: {logs}", show_alert=True)

    except Exception as e: print(f"/// CB ERROR: {e}")

# --- 8. ЗАПУСК ---
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
