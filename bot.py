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

# --- ЭКОНОМИКА V15.5 (ЭКСПАНСИЯ) ---
COOLDOWN_BASE = 1800     # 30 МИНУТ
COOLDOWN_ACCEL = 900     # 15 МИНУТ
XP_GAIN = 25             
PATH_CHANGE_COST = 100   
REFERRAL_BONUS = 250     
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {} 

# --- 3. ЛОР И ТЕКСТЫ ---
SCHOOLS = {
    "money": "🏦 ШКОЛА МАТЕРИИ (Влияние и Капитал)",
    "mind": "🧠 ШКОЛА РАЗУМА (Психофизика и НЛП)",
    "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ (ИИ и Автоматизация)"
}

GUIDE_TEXT = (
    "**/// МЕНТАЛЬНЫЙ РЕГЛАМЕНТ EIDOS-OS**\n\n"
    "**СУТЬ:** Твой мозг — это биокомпьютер с устаревшим софтом. Эйдос — это патч безопасности и драйвер эффективности.\n\n"
    "**1. СИНХРОНИЗАЦИЯ (SYNC):**\n"
    "Твой XP — это энергия влияния. Каждые **30 минут** открывается канал для дешифровки протокола. Чем выше дисциплина (STREAK), тем чище сигнал.\n\n"
    "**2. ВЕКТОРЫ:**\n"
    "🔴 **ХИЩНИК:** Взлом ресурсов. Ты берешь свое по праву интеллекта.\n"
    "🔵 **МИСТИК:** Взлом людей. Ты управляешь через эмпатию.\n"
    "🟣 **ТЕХНОЖРЕЦ:** Взлом рутины. ИИ работает вместо тебя.\n\n"
    "**3. ПРАВИЛА:**\n"
    "Покупай модификации за SYNC. Строй Синдикат. Твоя цель — Clearance Level 4."
)

LEVEL_UP_MSG = {
    2: "🔓 **CLEARANCE LVL 2**: Нейронные фильтры обновлены.",
    3: "🔓 **CLEARANCE LVL 3**: Статус Оператора. Вижу структуру матрицы.",
    4: "👑 **CLEARANCE LVL 4**: Архитектор. Твоя воля — закон."
}

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
            USER_CACHE.clear()
            for i, row in enumerate(all_v[1:], start=2):
                if row and row[0] and str(row[0]).isdigit():
                    uid = int(row[0])
                    def s_int(val, d=0): return int(str(val).strip()) if str(val).strip().isdigit() else d
                    USER_CACHE[uid] = {
                        "path": row[4] if len(row) > 4 and row[4] else "general",
                        "xp": s_int(row[5]), "level": s_int(row[6], 1), "streak": s_int(row[7]),
                        "last_active": row[8] if len(row) > 8 and row[8] else "2000-01-01",
                        "prestige": s_int(row[9]), "cryo": s_int(row[10]), "accel": s_int(row[11]),
                        "decoder": s_int(row[12]),
                        "accel_exp": float(row[13]) if len(row) > 13 and str(row[13]).replace('.','').isdigit() else 0,
                        "referrer": s_int(row[14], None) if len(row) > 14 else None,
                        "last_protocol_time": 0, "notified": True, "row_id": i
                    }
            print("/// EIDOS CORE: ONLINE")
    except Exception as e: print(f"/// CORE ERROR: {e}")

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
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-БУФЕР СПАС СЕРИЮ!"
            else: u['streak'] = 1; bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        u['last_active'] = today
        total = amount + bonus
        u['xp'] += total
        if u.get('referrer') and u['referrer'] in USER_CACHE:
            r = USER_CACHE[u['referrer']]; r['xp'] += max(1, int(total*0.1)); save_progress(u['referrer'])
        
        old_lvl = u['level']
        if u['xp'] >= 850: u['level'] = 4
        elif u['xp'] >= 350: u['level'] = 3
        elif u['xp'] >= 100: u['level'] = 2
        
        save_progress(uid)
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

def decrypt_and_send(target_chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    try:
        status_msg = bot.send_message(target_chat_id, "📡 **ИНИЦИАЛИЗАЦИЯ НЕЙРО-КАНАЛА...**")
        time.sleep(1)
        bot.edit_message_text(f"🔓 **ДЕШИФРОВКА ПРОТОКОЛА...**\n`[||||||||..] 84%`", target_chat_id, status_msg.message_id, parse_mode="Markdown")
        time.sleep(0.8)
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, target_lvl + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            for l in range(1, target_lvl + 1):
                if l in CONTENT_DB.get('general', {}): pool.extend(CONTENT_DB['general'][l])
        txt = random.choice(pool) if pool else "/// ОШИБКА: ДАННЫЕ НЕ НАЙДЕНЫ."
        school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
        res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC {use_dec_text}"
        bot.edit_message_text(res, target_chat_id, status_msg.message_id, parse_mode="Markdown", 
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
                        bot.send_message(uid, "⚡️ **СИСТЕМА ОСТЫЛА.**\nНовый протокол готов к загрузке.", 
                                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

# --- 7. ИНТЕРФЕЙС ---
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👁 ДЕШИФРОВАТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop"),
        types.InlineKeyboardButton("🔗 СИНДИКАТ ОСКОЛКОВ", callback_data="referral"),
        types.InlineKeyboardButton("📚 РУКОВОДСТВО", callback_data="guide")
    )
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel"))
    return markup

def get_admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 ОБНОВИТЬ ЯДРО (БД)", callback_data="admin_refresh"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА УЗЛОВ", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 ИНСТРУКЦИЯ ПОСТОВ", callback_data="admin_post_info"),
        types.InlineKeyboardButton("🔙 НАЗАД В МЕНЮ", callback_data="back_to_menu")
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
    ref_id = int(m.text.split()[1]) if len(m.text.split()) > 1 and m.text.split()[1].isdigit() else None
    if uid not in USER_CACHE:
        if ws_users:
            ws_users.append_row([str(uid), f"@{m.from_user.username}", m.from_user.first_name, datetime.now().strftime("%Y-%m-%d"), "general", "0", "1", "1", datetime.now().strftime("%Y-%m-%d"), "0", "0", "0", "0", "0", str(ref_id or '')])
            connect_db()
            if ref_id and ref_id in USER_CACHE:
                USER_CACHE[ref_id]['xp'] += REFERRAL_BONUS; save_progress(ref_id)
                try: bot.send_message(ref_id, f"🎁 **НОВЫЙ УЗЕЛ ПОДКЛЮЧЕН.**\nТвой Синдикат вырос. +{REFERRAL_BONUS} XP.")
                except: pass
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS-OS: НЕЙРОИНТЕРФЕЙС СИНХРОНИЗИРОВАН.\nВыбери вектор развития своего биоробота:", reply_markup=get_path_menu())

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': connect_db(); bot.send_message(message.chat.id, "✅ БД ОБНОВЛЕНА.")
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ПОЛУЧИТЬ СИНХРОН", callback_data="get_protocol"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ ТЕКСТ ОТПРАВЛЕН В КАНАЛ.")
        elif message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ПОЛУЧИТЬ СИНХРОН", callback_data="get_protocol"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=message.caption[6:], reply_markup=markup, parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ ПОСТ С ФОТО ЗАВЕРШЕН.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE:
        bot.answer_callback_query(call.id, "⚠️ ОШИБКА ДОСТУПА. Нажми /start в боте", show_alert=True)
        return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "admin_panel" and uid == ADMIN_ID:
        safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ АРХИТЕКТОРА**", get_admin_menu())
    elif call.data == "admin_refresh" and uid == ADMIN_ID:
        connect_db(); bot.answer_callback_query(call.id, "✅ ЯДРО СИНХРОНИЗИРОВАНО", show_alert=True)
    elif call.data == "admin_stats" and uid == ADMIN_ID:
        bot.answer_callback_query(call.id, f"📊 Узлов в системе: {len(USER_CACHE)}", show_alert=True)
    elif call.data == "admin_post_info" and uid == ADMIN_ID:
        safe_edit(call, "**📢 ИНСТРУКЦИЯ ПОСТОВ:**\n\n1. Текст: напиши `/post Текст`.\n2. Фото: прикрепи фото и подпиши `/post Текст`.\nБот добавит кнопку автоматически.", get_admin_menu())

    elif call.data == "get_protocol":
        cd = COOLDOWN_ACCEL if u['accel_exp'] > now_ts else COOLDOWN_BASE
        if now_ts - u.get('last_protocol_time', 0) < cd:
            rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
            bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ. Жди {rem} мин.", show_alert=True); return
        
        # --- ФИКС ЗАСОРЕНИЯ КАНАЛА ---
        if call.message.chat.id < 0: # Если нажато в канале
            bot.answer_callback_query(call.id, "🧬 ДАННЫЕ ОТПРАВЛЕНЫ В ЛИЧНЫЙ ТЕРМИНАЛ")
        
        u['last_protocol_time'], u['notified'] = now_ts, False
        up, s_msg, total = add_xp(uid, XP_GAIN)
        use_dec = "(+🔑 Дешифратор)" if u['decoder'] > 0 else ""
        target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
        if u['decoder'] > 0: u['decoder'] -= 1
        if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
        
        # ОТПРАВЛЯЕМ СТРОГО В ЛС (uid), а не в call.message.chat.id
        threading.Thread(target=decrypt_and_send, args=(uid, uid, target_lvl, use_dec)).start()

    elif call.data == "shop":
        shop_text = (
            "🎰 **ЧЕРНЫЙ РЫНОК: МОДИФИКАЦИИ**\n\n"
            f"❄️ **КРИО-КАПСУЛА** ({PRICES['cryo']} XP)\n"
            "**Био-страховка.** Автоматически спасет твою Серию (Streak), если ты не выходил в сеть более 24 часов.\n\n"
            f"⚡️ **НЕЙРО-УСКОРИТЕЛЬ** ({PRICES['accel']} XP)\n"
            "**Оверклокинг.** На 24 часа сокращает ожидание с 30 до 15 минут.\n\n"
            f"🔑 **ДЕШИФРАТОР** ({PRICES['decoder']} XP)\n"
            "**Взлом доступа.** Разово дает протокол уровня Lvl+1."
        )
        safe_edit(call, shop_text, types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} XP)", callback_data="buy_cryo"),
            types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="buy_accel"),
            types.InlineKeyboardButton(f"🔑 ДЕШИФРАТОР ({PRICES['decoder']} XP)", callback_data="buy_decoder"),
            types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
        ))

    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            u['xp'] -= PRICES[item]; u[item] += 1; save_progress(uid)
            bot.answer_callback_query(call.id, f"✅ МОДИФИКАЦИЯ УСТАНОВЛЕНА")
            safe_edit(call, "🎰 **ЧЕРНЫЙ РЫНОК АКТИВЕН**", get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО SYNC", show_alert=True)

    elif call.data == "referral":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        ref_text = (
            "🔗 **СИНДИКАТ ОСКОЛКОВ: ТВОЯ ИМПЕРИЯ**\n\n"
            f"Ссылка для вербовки новых узлов:\n`{link}`\n\n"
            f"🎁 **БОНУС:** +{REFERRAL_BONUS} XP за узел.\n"
            "⚙️ **ПРОЦЕНТ:** 10% от всей добычи твоих людей — пожизненно."
        )
        safe_edit(call, ref_text, get_main_menu(uid))

    elif call.data == "profile":
        stars = "★" * u['prestige']
        msg = f"👤 **НЕЙРО-ПРОФИЛЬ** {stars}\n💰 SYNC: {u['xp']}\n🔥 СИГНАЛ: {u['streak']} дн.\n🎒 ИНВ: ❄️{u['cryo']} ⚡️{u['accel']} 🔑{u['decoder']}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        if u['accel'] > 0 and u['accel_exp'] < now_ts: markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ РАЗГОН ⚡️", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton(f"⚙️ СМЕНИТЬ ВЕКТОР (-{PATH_CHANGE_COST} XP)", callback_data="change_path_confirm"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        safe_edit(call, msg, markup)

    elif call.data == "change_path_confirm":
        safe_edit(call, f"⚠️ Смена Школы требует **{PATH_CHANGE_COST} SYNC**. Продолжить перепрошивку?", get_path_menu(cost_info=True))

    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
            if u['path'] != 'general' and u['path'] != new_path: u['xp'] -= PATH_CHANGE_COST
            u['path'] = new_path; save_progress(uid)
            bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
        else: bot.answer_callback_query(call.id, "❌ МАЛО ЭНЕРГИИ", show_alert=True)

    elif call.data == "use_accel":
        if u['accel'] > 0:
            u['accel'] -= 1; u['accel_exp'] = now_ts + 86400; save_progress(uid)
            bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН. СКОРОСТЬ СИНХРОНИЗАЦИИ +200%.", reply_markup=get_main_menu(uid))

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// EIDOS-OS: БИОЛОГИЧЕСКАЯ ОБОЛОЧКА СИНХРОНИЗИРОВАНА.\nОжидаю нейронную директиву...", reply_markup=get_main_menu(uid))

    elif call.data == "guide": bot.send_message(uid, GUIDE_TEXT, parse_mode="Markdown")
    try: bot.answer_callback_query(call.id)
    except: pass

# --- 9. ЗАПУСК ---
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
