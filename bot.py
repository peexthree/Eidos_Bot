import telebot
from telebot import types
import flask
import os
import time
import random
import logging
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

# --- БАЛАНС И ЦЕНЫ ---
COOLDOWN_BASE = 3600    # 1 час
COOLDOWN_ACCEL = 900    # 15 минут (под ускорителем)
PATH_CHANGE_COST = 50
PRICES = {"cryo": 100, "accel": 250, "decoder": 400}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {} 

# --- 3. ТЕКСТЫ ---
REMINDERS = [
    "⚡️ Энергия восстановлена. Следующий протокол готов к загрузке.",
    "👁 Эйдос потерял визуальный контакт. Вернись в систему.",
    "⏳ Таймер истек. Твоя порция реальности ждет.",
    "🔓 Доступ к новому файлу открыт.",
    "🐺 Хищник не спит так долго. Пора на охоту."
]

GUIDE_TEXT = (
    "**/// РУКОВОДСТВО v10.0**\n\n"
    "**АРТЕФАКТЫ:**\n"
    "❄️ **Крио-капсула**: Авто-спасение Стрика при пропуске дня.\n"
    "⚡️ **Ускоритель**: Снижает Кулдаун до 15 мин на 24 часа.\n"
    "🔑 **Дешифратор**: Разовый доступ к протоколу на 1 LVL выше твоего.\n\n"
    "⚠️ **ОГРАНИЧЕНИЯ:**\n"
    "Между протоколами — 1 час. Используй Ускоритель, чтобы сократить до 15 мин."
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
            
            # Контент
            try: 
                ws_content = sh.worksheet("Content")
                records = ws_content.get_all_records()
                CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
                for r in records:
                    path, text, lvl = str(r.get('Path', 'general')).lower(), r.get('Text', ''), int(r.get('Level', 1))
                    if text:
                        if path not in CONTENT_DB: path = "general"
                        if lvl not in CONTENT_DB[path]: CONTENT_DB[path][lvl] = []
                        CONTENT_DB[path][lvl].append(text)
            except: pass

            # Юзеры (Добавлены колонки K-N)
            try:
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
                            "cryo": int(row[10]) if len(row) > 10 and str(row[10]).isdigit() else 0,
                            "accel": int(row[11]) if len(row) > 11 and str(row[11]).isdigit() else 0,
                            "decoder": int(row[12]) if len(row) > 12 and str(row[12]).isdigit() else 0,
                            "accel_exp": float(row[13]) if len(row) > 13 and row[13] else 0,
                            "last_protocol_time": 0, "notified": True, "row_id": i
                        }
            except: pass
    except: pass

connect_db()

# --- 5. ФОНОВЫЙ ВОРКЕР (С учетом ускорителя) ---
def notification_worker():
    while True:
        try:
            time.sleep(60)
            now = time.time()
            for uid, u in list(USER_CACHE.items()):
                # Проверка кулдауна (базовый или ускоренный)
                current_cd = COOLDOWN_ACCEL if u.get('accel_exp', 0) > now else COOLDOWN_BASE
                if u['last_protocol_time'] > 0 and (now - u['last_protocol_time'] >= current_cd) and not u['notified']:
                    try:
                        bot.send_message(uid, random.choice(REMINDERS), 
                                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

# --- 6. ЛОГИКА ---
def save_progress(uid):
    def task():
        try:
            u = USER_CACHE.get(uid)
            if u and ws_users:
                # E(5) по N(14)
                data = [u['path'], str(u['xp']), str(u['level']), str(u['streak']), u['last_active'], str(u['prestige']),
                        str(u['cryo']), str(u['accel']), str(u['decoder']), str(u['accel_exp'])]
                ws_users.update(f"E{u['row_id']}:N{u['row_id']}", [data])
        except: pass
    threading.Thread(target=task).start()

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus = 0; streak_msg = None

        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5
            streak_msg = f"🔥 СЕРИЯ: {u['streak']} ДН. (+{bonus} XP)"
        elif u['last_active'] != today:
            # ПРОВЕРКА КРИО-КАПСУЛЫ (Novelty)
            if u.get('cryo', 0) > 0:
                u['cryo'] -= 1
                streak_msg = "❄️ КРИО-КАПСУЛА СПАСЛА СЕРИЮ!"
            else:
                if u['streak'] > 1: streak_msg = "❄️ СЕРИЯ ПРЕРВАНА."
                u['streak'] = 1; bonus = 5
        
        u['last_active'] = today
        u['xp'] += (amount + bonus)
        # Level-Up Logic
        old_lvl = u['level']
        if u['xp'] >= 1500: u['level'] = 4
        elif u['xp'] >= 500: u['level'] = 3
        elif u['xp'] >= 150: u['level'] = 2
        
        lvl_msg = LEVEL_UP_MSG.get(u['level']) if u['level'] > old_lvl else None
        save_progress(uid)
        return lvl_msg, streak_msg, (amount + bonus)
    return None, None, 0

# --- 7. МЕНЮ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 ПРОФИЛЬ / ИНВЕНТАРЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 МАГАЗИН АРТЕФАКТОВ", callback_data="shop"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ (-50 XP)", callback_data="change_path"),
        types.InlineKeyboardButton("📚 ГАЙД", callback_data="guide")
    )
    return markup

def get_shop_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"❄️ КРИО-КАПСУЛА ({PRICES['cryo']} XP)", callback_data="buy_cryo"),
        types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="buy_accel"),
        types.InlineKeyboardButton(f"🔑 ДЕШИФРАТОР ({PRICES['decoder']} XP)", callback_data="buy_decoder"),
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
    )
    return markup

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid not in USER_CACHE:
        now = datetime.now().strftime("%Y-%m-%d")
        if ws_users:
            ws_users.append_row([str(uid), f"@{m.from_user.username}", m.from_user.first_name, now, "general", "0", "1", "1", now, "0", "0", "0", "0", "0"])
            connect_db()
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS OS v10.0 ACTIVE\nИнвентарь и Магазин разблокированы.", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]
    now_ts = time.time()

    if call.data == "shop":
        safe_edit(call, "🎰 **ЧЕРНЫЙ РЫНОК**\nУправляй вероятностью через XP.", get_shop_menu())

    elif call.data.startswith("buy_"):
        item = call.data.split("_")[1]
        if u['xp'] >= PRICES[item]:
            u['xp'] -= PRICES[item]
            u[item] += 1
            save_progress(uid)
            bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item.upper()}")
            safe_edit(call, f"🎰 **ЧЕРНЫЙ РЫНОК**\n\nПредмет получен. Баланс: {u['xp']} XP.", get_shop_menu())
        else:
            bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО XP", show_alert=True)

    elif call.data == "get_protocol":
        # Проверка кулдауна
        cd = COOLDOWN_ACCEL if u['accel_exp'] > now_ts else COOLDOWN_BASE
        if now_ts - u['last_protocol_time'] < cd:
            rem = int((cd - (now_ts - u['last_protocol_time'])) / 60)
            bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ. Жди {rem} мин.", show_alert=True)
            return

        # Проверка Дешифратора
        target_lvl = u['level']
        use_dec = ""
        if u['decoder'] > 0:
            u['decoder'] -= 1; target_lvl += 1
            use_dec = "\n🔑 **ДЕШИФРАТОР АКТИВИРОВАН: ДОСТУП LVL+1**"

        lvl_msg, s_msg, earned = add_xp(uid, 10)
        u['last_protocol_time'], u['notified'] = now_ts, False
        
        # Поиск контента
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, target_lvl + 1):
            if l in p_cont: pool.extend(p_cont[l])
        
        txt = random.choice(pool) if pool else "/// ПУСТОТА."
        res = f"**// ПРОТОКОЛ [{u['path'].upper()}]**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{earned} XP{use_dec}"
        if s_msg: res += f" | {s_msg}"
        
        if lvl_msg: bot.send_message(call.message.chat.id, lvl_msg, parse_mode="Markdown")
        bot.send_message(call.message.chat.id, res, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 МЕНЮ", callback_data="back_to_menu")))

    elif call.data == "profile":
        stars = "★" * u['prestige']
        accel_info = "✅ АКТИВЕН" if u['accel_exp'] > now_ts else "❌ НЕАКТИВЕН"
        msg = (f"👤 **ПРОФИЛЬ** {stars}\n"
               f"💰 Баланс: {u['xp']} XP\n"
               f"🔥 Серия: {u['streak']} дн.\n\n"
               f"🎒 **ИНВЕНТАРЬ:**\n"
               f"❄️ Крио: {u['cryo']} шт.\n"
               f"⚡️ Ускоритель: {u['accel']} шт. ({accel_info})\n"
               f"🔑 Дешифратор: {u['decoder']} шт.")
        
        markup = types.InlineKeyboardMarkup()
        if u['accel'] > 0 and u['accel_exp'] < now_ts:
            markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "use_accel":
        if u['accel'] > 0:
            u['accel'] -= 1; u['accel_exp'] = now_ts + 86400
            save_progress(uid); bot.answer_callback_query(call.id, "🚀 УСКОРИТЕЛЬ НА 24Ч АКТИВИРОВАН!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА УСКОРЕНА", reply_markup=get_main_menu())

    elif call.data == "guide": safe_edit(call, GUIDE_TEXT, get_main_menu())
    
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ИНТЕРФЕЙС АКТИВЕН", reply_markup=get_main_menu())

    try: bot.answer_callback_query(call.id)
    except: pass

# --- ЗАПУСК ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    flask.abort(403)

if __name__ == "__main__":
    if WEBHOOK_URL:
        bot.remove_webhook(); time.sleep(1); bot.set_webhook(url=WEBHOOK_URL)
    threading.Thread(target=notification_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
