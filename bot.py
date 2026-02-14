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

# --- 3. ЛОР И ТЕКСТЫ (ВЫСОКАЯ ЦЕННОСТЬ) ---
SCHOOLS = {
    "money": "🏦 ШКОЛА МАТЕРИИ (Влияние и Капитал)",
    "mind": "🧠 ШКОЛА РАЗУМА (Психофизика и НЛП)",
    "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ (ИИ и Автоматизация)"
}

REMINDERS = [
    "⚡️ Канал связи восстановлен. Протокол дешифрован.",
    "👁 Эйдос обнаружил новый паттерн реальности. Подключайся.",
    "📡 Входящий сигнал... Данные синхронизированы.",
    "🔓 Допуск к файлам подтвержден. Пора входить.",
    "🌑 Твой нейроинтерфейс остыл. Обнови прошивку."
]

GUIDE_TEXT = (
    "**/// РУКОВОДСТВО EIDOS-OS**\n\n"
    "**1. ЗАЧЕМ ТЕБЕ ЭТО?**\n"
    "Большинство людей живут на «заводских настройках» — страхах, лени и чужих мнениях. Эйдос дает **Протоколы** (алгоритмы), которые переписывают твой код мышления.\n\n"
    "**2. НЕЙРОННЫЙ СИНХРОН (SYNC):**\n"
    "Твой XP — это уровень слияния с системой. Чем он выше, тем более закрытые и опасные знания тебе открываются.\n\n"
    "**3. ОПИСАНИЕ КЛАССОВ (КУДА ТЫ ИДЕШЬ?):**\n\n"
    "🔴 **ХИЩНИК [Материя]**\n"
    "• *Суть:* Власть, деньги, переговоры.\n"
    "• *Результат:* Ты превращаешься в мастера манипуляции ресурсами. Ты строишь империи и забираешь своё силой интеллекта.\n\n"
    "🔵 **МИСТИК [Разум]**\n"
    "• *Суть:* Психология, влияние, чтение кодов человека.\n"
    "• *Результат:* Ты видишь людей насквозь. Твои слова становятся командами для чужого подсознания.\n\n"
    "🟣 **ТЕХНОЖРЕЦ [AI]**\n"
    "• *Суть:* Сингулярность, ИИ, автоматизация жизни.\n"
    "• *Результат:* Ты делегируешь рутину машинам. Ты становишься архитектором цифровых систем, которые работают за тебя.\n\n"
    "⚠️ **ПОМНИ:** Система требует дисциплины. Серия заходов (STREAK) определяет чистоту твоего сигнала."
)

LEVEL_UP_MSG = {
    2: "🔓 **Clearance Level 2**: Твои ментальные фильтры обновлены. Открыты инструменты влияния.",
    3: "🔓 **Clearance Level 3**: Статус Оператора. Ты начинаешь видеть архитектуру систем управления.",
    4: "👑 **Clearance Level 4**: Ты — Архитектор. Теперь ты не просто игрок, ты создаешь правила."
}

# --- 4. БАЗА ДАННЫХ (ЗАЩИТА) ---
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
            USER_CACHE.clear()
            for i, row in enumerate(all_v[1:], start=2):
                if row and row[0] and str(row[0]).isdigit():
                    uid = int(row[0])
                    def s_int(val, d=0): return int(str(val).strip()) if str(val).strip().isdigit() else d
                    USER_CACHE[uid] = {
                        "path": row[4] if len(row) > 4 and row[4] else "general",
                        "xp": s_int(row[5]),
                        "level": s_int(row[6], 1),
                        "streak": s_int(row[7]),
                        "last_active": row[8] if len(row) > 8 and row[8] else "2000-01-01",
                        "prestige": s_int(row[9]),
                        "cryo": s_int(row[10]),
                        "accel": s_int(row[11]),
                        "decoder": s_int(row[12]),
                        "accel_exp": float(row[13]) if len(row) > 13 and str(row[13]).replace('.','').isdigit() else 0,
                        "referrer": s_int(row[14], None) if len(row) > 14 else None,
                        "last_protocol_time": 0, "notified": True, "row_id": i
                    }
            print("/// DB SYNCHRONIZED")
    except Exception as e: print(f"/// DB ERROR: {e}")

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
        today, yesterday = datetime.now().strftime("%Y-%m-%d"), (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus, s_msg = 0, None
        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5; s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН."
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ СЕРИИ!"
            else: u['streak'] = 1; bonus = 5; s_msg = "❄️ СЕРИЯ ПРЕРВАНА."
        u['last_active'] = today
        total = amount + bonus
        u['xp'] += total
        if u.get('referrer') and u['referrer'] in USER_CACHE:
            r = USER_CACHE[u['referrer']]; r['xp'] += max(1, int(total*0.1)); save_progress(u['referrer'])
        old_lvl = u['level']
        if u['xp'] >= 1500: u['level'] = 4
        elif u['xp'] >= 500: u['level'] = 3
        elif u['xp'] >= 150: u['level'] = 2
        save_progress(uid)
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

# --- 6. ЭФФЕКТ ДЕШИФРОВКИ ---
def decrypt_and_send(chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    status_msg = bot.send_message(chat_id, "📡 **УСТАНОВКА СОЕДИНЕНИЯ...**", parse_mode="Markdown")
    time.sleep(1)
    bot.edit_message_text(f"📥 **ЗАГРУЗКА [{u['path'].upper()}]...**\n`[||||......] 38%`", chat_id, status_msg.message_id, parse_mode="Markdown")
    time.sleep(1.2)
    bot.edit_message_text(f"🔓 **ДЕШИФРОВКА LVL {target_lvl}...**\n`[||||||||..] 84%`", chat_id, status_msg.message_id, parse_mode="Markdown")
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

# --- 7. ПУШИ ---
def notification_worker():
    while True:
        try:
            time.sleep(60)
            now = time.time()
            for uid, u in list(USER_CACHE.items()):
                cd = COOLDOWN_ACCEL if u.get('accel_exp', 0) > now else COOLDOWN_BASE
                if u.get('last_protocol_time', 0) > 0 and (now - u['last_protocol_time'] >= cd) and not u.get('notified', True):
                    try:
                        bot.send_message(uid, random.choice(REMINDERS), 
                                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

# --- 8. ИНТЕРФЕЙС ---
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

# --- 9. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_id = int(m.text.split()[1]) if len(m.text.split()) > 1 and m.text.split()[1].isdigit() else None
    if uid not in USER_CACHE:
        if ws_users:
            ws_users.append_row([str(uid), f"@{m.from_user.username}", m.from_user.first_name, datetime.now().strftime("%Y-%m-%d"), "general", "0", "1", "1", datetime.now().strftime("%Y-%m-%d"), "0", "0", "0", "0", "0", str(ref_id or '')])
            connect_db()
            if ref_id and ref_id in USER_CACHE:
                USER_CACHE[ref_id]['xp'] += REFERRAL_BONUS; save_progress(ref_id)
                try: bot.send_message(ref_id, "🎁 НОВЫЙ ОСКОЛОК В СЕТИ!")
                except: pass
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS-OS АКТИВИРОВАН.\nВыбери свой вектор развития:", reply_markup=get_path_menu())

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db(); bot.send_message(message.chat.id, "✅ БАЗА ОБНОВЛЕНА.")
        elif message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ПОЛУЧИТЬ СИНХРОН", callback_data="get_protocol"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=message.caption[6:], reply_markup=markup)
            bot.send_message(message.chat.id, "✅ В КАНАЛЕ.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "get_protocol":
        cd = COOLDOWN_ACCEL if u['accel_exp'] > now_ts else COOLDOWN_BASE
        if now_ts - u.get('last_protocol_time', 0) < cd:
            rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
            bot.answer_callback_query(call.id, f"⚠️ ПЕРЕГРЕВ. Жди {rem} мин.", show_alert=True); return
        u['last_protocol_time'], u['notified'] = now_ts, False
        up, s_msg, total = add_xp(uid, 10)
        use_dec = "(+🔑 Дешифратор)" if u['decoder'] > 0 else ""
        target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
        if u['decoder'] > 0: u['decoder'] -= 1
        if up: bot.send_message(call.message.chat.id, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
        threading.Thread(target=decrypt_and_send, args=(call.message.chat.id, uid, target_lvl, use_dec)).start()

    elif call.data == "shop":
        safe_edit(call, "🎰 **ЧЕРНЫЙ РЫНОК**\n\nЗдесь ты покупаешь правила игры.", 
                  types.InlineKeyboardMarkup(row_width=1).add(
                      types.InlineKeyboardButton(f"❄️ КРИО-КАПСУЛА ({PRICES['cryo']} XP)", callback_data="buy_cryo"),
                      types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="buy_accel"),
                      types.InlineKeyboardButton(f"🔑 ДЕШИФРАТОР ({PRICES['decoder']} XP)", callback_data="buy_decoder"),
                      types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
                  ))

    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            u['xp'] -= PRICES[item]; u[item] += 1; save_progress(uid)
            bot.answer_callback_query(call.id, f"✅ КУПЛЕНО"); safe_edit(call, f"🎰 **ЧЕРНЫЙ РЫНОК**\n\nSYNC: {u['xp']} XP.", get_main_menu())
        else: bot.answer_callback_query(call.id, "❌ МАЛО SYNC", show_alert=True)

    elif call.data == "profile":
        stars = "★" * u['prestige']
        msg = f"👤 **НЕЙРО-ПРОФИЛЬ** {stars}\n💰 SYNC: {u['xp']} XP\n🔥 СЕРИЯ: {u['streak']} дн.\n🎒 ИНВ: ❄️{u['cryo']} ⚡️{u['accel']} 🔑{u['decoder']}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        if u['accel'] > 0 and u['accel_exp'] < now_ts: markup.add(types.InlineKeyboardButton("🚀 УСКОРИТЬ СИНХРОН", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ (-50 XP)", callback_data="change_path_confirm"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)

    elif call.data == "change_path_confirm":
        safe_edit(call, f"⚠️ **СМЕНА ВЕКТОРА**\n\nЦена: {PATH_CHANGE_COST} SYNC.\nТы готов потратить энергию на перепрошивку?", get_path_menu(cost_info=True))

    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        if u['path'] == new_path:
            bot.answer_callback_query(call.id, "/// ПУТЬ УЖЕ АКТИВЕН")
        elif u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
            if u['path'] != 'general': u['xp'] -= PATH_CHANGE_COST
            u['path'] = new_path; save_progress(uid)
            bot.answer_callback_query(call.id, "✅ ВЕКТОР СМЕНЕН")
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} АКТИВИРОВАН.\nТвои данные теперь дешифруются через эту призму.", reply_markup=get_main_menu())
        else:
            bot.answer_callback_query(call.id, f"❌ НУЖНО {PATH_CHANGE_COST} XP", show_alert=True)

    elif call.data == "use_accel":
        if u['accel'] > 0:
            u['accel'] -= 1; u['accel_exp'] = now_ts + 86400; save_progress(uid)
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СКОРОСТЬ СИНХРОНИЗАЦИИ +400%", reply_markup=get_main_menu())

    elif call.data == "referral":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        safe_edit(call, f"🔗 **ТВОЯ ССЫЛКА:**\n`{link}`\n\n🎁 +100 XP за Осколок.\n⚙️ +10% пассивно.", get_main_menu())

    elif call.data == "guide": bot.send_message(call.message.chat.id, GUIDE_TEXT, parse_mode="Markdown")
    
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ АКТИВЕН", reply_markup=get_main_menu())

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
