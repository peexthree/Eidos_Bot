import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# БАЛАНС
COOLDOWN_BASE = 3600
COOLDOWN_ACCEL = 900
PATH_CHANGE_COST = 50
REFERRAL_BONUS = 100
REFERRAL_PERCENT = 0.1
PRICES = {"cryo": 100, "accel": 250, "decoder": 400}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {} 

# --- 3. ШКОЛЫ МЫШЛЕНИЯ ---
SCHOOLS = {
    "money": "🏦 ШКОЛА МАТЕРИИ (Влияние & Капитал)",
    "mind": "🧠 ШКОЛА РАЗУМА (Психофизика & НЛП)",
    "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ (ИИ & Автоматизация)"
}

REMINDERS = [
    "⚡️ Канал связи восстановлен. Следующий протокол готов к дешифровке.",
    "👁 Эйдос обнаружил новый паттерн реальности. Требуется твое внимание.",
    "📡 Входящий сигнал... Данные синхронизированы. Ждем подключения.",
    "🔓 Допуск к файлам высшего порядка подтвержден.",
    "🌑 Твой нейроинтерфейс остыл. Пора обновить прошивку."
]

GUIDE_TEXT = (
    "**/// ИНСТРУКЦИЯ ПО ЭКСПЛУАТАЦИИ EIDOS_OS**\n\n"
    "**1. СУТЬ СИСТЕМЫ:**\n"
    "Эйдос — это не игра. Это инструмент обновления твоих ментальных карт. Знания, которые ты получаешь, требуют внедрения, а не просто чтения.\n\n"
    "**2. НЕЙРОННЫЙ СИНХРОН (SYNC):**\n"
    "XP — это уровень твоей синхронизации с системой. Чем выше SYNC, тем сложнее и опаснее данные тебе открываются.\n\n"
    "**3. ШКОЛЫ ДОСТУПА:**\n"
    "🔴 **МАТЕРИЯ:** Взлом финансовых систем и человеческих убеждений.\n"
    "🔵 **РАЗУМ:** Управление собственным биороботом и чтение чужих кодов.\n"
    "🟣 **СИНГУЛЯРНОСТЬ:** Симбиоз с ИИ для удаления рутины из жизни.\n\n"
    "⚠️ Серия заходов (STREAK) определяет чистоту твоего сигнала."
)

# --- 4. БАЗА ДАННЫХ ---
def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            
            ws_content = sh.worksheet("Content")
            records = ws_content.get_all_records()
            CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
            for r in records:
                path, text, lvl = str(r.get('Path', 'general')).lower(), r.get('Text', ''), int(r.get('Level', 1))
                if text:
                    if path not in CONTENT_DB: path = "general"
                    if lvl not in CONTENT_DB[path]: CONTENT_DB[path][lvl] = []
                    CONTENT_DB[path][lvl].append(text)

            ws_users = sh.worksheet("Users")
            all_v = ws_users.get_all_values()
            for i, row in enumerate(all_v[1:], start=2):
                if row and row[0] and str(row[0]).isdigit():
                    uid = int(row[0])
                    USER_CACHE[uid] = {
                        "path": row[4] if len(row) > 4 else "general",
                        "xp": int(row[5]) if len(row) > 5 and str(row[5]).isdigit() else 0,
                        "level": int(row[6]) if len(row) > 6 else 1,
                        "streak": int(row[7]) if len(row) > 7 else 0,
                        "last_active": row[8] if len(row) > 8 else "2000-01-01",
                        "prestige": int(row[9]) if len(row) > 9 else 0,
                        "cryo": int(row[10]) if len(row) > 10 else 0,
                        "accel": int(row[11]) if len(row) > 11 else 0,
                        "decoder": int(row[12]) if len(row) > 12 else 0,
                        "accel_exp": float(row[13]) if len(row) > 13 and row[13] else 0,
                        "referrer": int(row[14]) if len(row) > 14 and str(row[14]).isdigit() else None,
                        "last_protocol_time": 0, "notified": True, "row_id": i
                    }
    except: pass

connect_db()

# --- 5. ФУНКЦИИ ЯДРА ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def save_progress(uid):
    def task():
        try:
            u = USER_CACHE.get(uid)
            if u and ws_users:
                data = [u['path'], str(u['xp']), str(u['level']), str(u['streak']), u['last_active'], str(u['prestige']),
                        str(u['cryo']), str(u['accel']), str(u['decoder']), str(u['accel_exp']), str(u.get('referrer', ''))]
                ws_users.update(f"E{u['row_id']}:O{u['row_id']}", [data])
        except: pass
    threading.Thread(target=task).start()

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus = 0; s_msg = None
        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5
            s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН. (+{bonus} XP)"
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ СЕРИИ!"
            else: u['streak'] = 1; bonus = 5; s_msg = "❄️ СЕРИЯ ПРЕРВАНА."
        
        u['last_active'] = today
        total = amount + bonus
        u['xp'] += total
        if u.get('referrer') and u['referrer'] in USER_CACHE:
            ref = USER_CACHE[u['referrer']]; ref['xp'] += max(1, int(total * 0.1)); save_progress(u['referrer'])
        
        old_lvl = u['level']
        if u['xp'] >= 1500: u['level'] = 4
        elif u['xp'] >= 500: u['level'] = 3
        elif u['xp'] >= 150: u['level'] = 2
        
        save_progress(uid)
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

# --- 6. ЭФФЕКТ ДЕШИФРОВКИ (VISUAL VALUE) ---
def decrypt_and_send(chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    status_msg = bot.send_message(chat_id, "📡 **УСТАНОВКА СОЕДИНЕНИЯ...**", parse_mode="Markdown")
    time.sleep(1)
    bot.edit_message_text(f"📥 **ЗАГРУЗКА ДАННЫХ [{u['path'].upper()}]...**\n`[||||......] 38%`", chat_id, status_msg.message_id, parse_mode="Markdown")
    time.sleep(1.2)
    bot.edit_message_text(f"🔓 **ДЕШИФРОВКА УРОВНЯ {target_lvl}...**\n`[||||||||..] 84%`", chat_id, status_msg.message_id, parse_mode="Markdown")
    time.sleep(0.8)

    pool = []
    p_cont = CONTENT_DB.get(u['path'], {})
    for l in range(1, target_lvl + 1):
        if l in p_cont: pool.extend(p_cont[l])
    if not pool:
        for l in range(1, target_lvl + 1):
            if l in CONTENT_DB.get('general', {}): pool.extend(CONTENT_DB['general'][l])
    
    txt = random.choice(pool) if pool else "/// ДАННЫЕ УТЕРЯНЫ."
    school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
    
    res = (f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n"
           f"{txt}\n\n━━━━━━━━━━━━━━\n"
           f"⚡️ +10 SYNC {use_dec_text}")
    
    bot.edit_message_text(res, chat_id, status_msg.message_id, parse_mode="Markdown", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

# --- 7. МЕНЮ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👁 ПОЛУЧИТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop"),
        types.InlineKeyboardButton("🔗 СЕТЬ ОСКОЛКОВ", callback_data="referral"),
        types.InlineKeyboardButton("📚 РУКОВОДСТВО", callback_data="guide")
    )
    return markup

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid not in USER_CACHE:
        now = datetime.now().strftime("%Y-%m-%d")
        if ws_users:
            ws_users.append_row([str(uid), f"@{m.from_user.username}", m.from_user.first_name, now, "general", "0", "1", "1", now, "0", "0", "0", "0", "0", ""])
            connect_db()
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS_OS: СИСТЕМА АКТИВИРОВАНА.\n\nТвоя реальность — это код. Мы здесь, чтобы помочь тебе его переписать.", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "get_protocol":
        cd = COOLDOWN_ACCEL if u['accel_exp'] > now_ts else COOLDOWN_BASE
        if now_ts - u['last_protocol_time'] < cd:
            rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
            bot.answer_callback_query(call.id, f"⚠️ ПЕРЕГРЕВ. Жди {rem} мин.", show_alert=True); return

        target_lvl = u['level']
        use_dec = ""
        if u['decoder'] > 0: u['decoder'] -= 1; target_lvl += 1; use_dec = "(+🔑 Дешифратор)"

        u['last_protocol_time'], u['notified'] = now_ts, False
        add_xp(uid, 10)
        
        # Запуск анимации дешифровки в отдельном потоке
        threading.Thread(target=decrypt_and_send, args=(call.message.chat.id, uid, target_lvl, use_dec)).start()

    elif call.data == "profile":
        stars = "★" * u['prestige']
        msg = (f"👤 **НЕЙРО-ПРОФИЛЬ** {stars}\n"
               f"💰 SYNC: {u['xp']} XP\n"
               f"🔥 СЕРИЯ: {u['streak']} дн.\n"
               f"🎒 ИНВ: ❄️{u['cryo']} ⚡️{u['accel']} 🔑{u['decoder']}")
        markup = types.InlineKeyboardMarkup()
        if u['accel'] > 0 and u['accel_exp'] < now_ts: markup.add(types.InlineKeyboardButton("🚀 УСКОРИТЬ СИНХРОН", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ АКТИВЕН", reply_markup=get_main_menu())

    elif call.data == "guide": safe_edit(call, GUIDE_TEXT, get_main_menu())
    
    try: bot.answer_callback_query(call.id)
    except: pass

# --- ЗАПУСК ---
if __name__ == "__main__":
    if WEBHOOK_URL: bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
