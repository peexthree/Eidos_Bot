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
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- СИСТЕМНАЯ ПАМЯТЬ (CACHE) ---
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {}

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ---
gc = None
sh = None
ws_users = None
ws_content = None

def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            
            # 1. ЗАГРУЗКА КОНТЕНТА
            try: 
                ws_content = sh.worksheet("Content")
                records = ws_content.get_all_records()
                CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
                
                count = 0
                for r in records:
                    path = str(r.get('Path', 'general')).lower()
                    text = r.get('Text', '')
                    level = r.get('Level', 1)
                    if not str(level).isdigit(): level = 1
                    level = int(level)

                    if text:
                        if path not in CONTENT_DB: path = "general"
                        if level not in CONTENT_DB[path]: CONTENT_DB[path][level] = []
                        CONTENT_DB[path][level].append(text)
                        count += 1
                print(f"/// CONTENT LOADED: {count} units.")
            except Exception as e: print(f"/// CONTENT ERROR: {e}")

            # 2. ЗАГРУЗКА ЮЗЕРОВ
            try:
                ws_users = sh.worksheet("Users")
                all_values = ws_users.get_all_values()
                for i, row in enumerate(all_values[1:], start=2):
                    if row and row[0]:
                        uid = int(row[0])
                        path = row[4] if len(row) > 4 and row[4] else "general"
                        xp = int(row[5]) if len(row) > 5 and row[5].isdigit() else 0
                        lvl = int(row[6]) if len(row) > 6 and row[6].isdigit() else 1
                        USER_CACHE[uid] = {"path": path, "xp": xp, "level": lvl, "row_id": i}
                print(f"/// USERS CACHED: {len(USER_CACHE)} profiles.")
            except Exception as e: print(f"/// USERS ERROR: {e}")
    except Exception as e: print(f"/// DB CRITICAL: {e}")

connect_db()

# --- ФОНОВЫЕ ПРОЦЕССЫ ---
def save_user_progress(uid):
    def task():
        try:
            user = USER_CACHE.get(uid)
            if user and ws_users:
                row = user['row_id']
                ws_users.update_cell(row, 5, user['path'])
                ws_users.update_cell(row, 6, str(user['xp']))
                ws_users.update_cell(row, 7, str(user['level']))
        except Exception as e: print(f"Save error: {e}")
    threading.Thread(target=task).start()

def register_user(user):
    uid = user.id
    if uid not in USER_CACHE:
        try:
            if ws_users:
                now = datetime.now().strftime("%Y-%m-%d")
                uname = f"@{user.username}" if user.username else "No"
                ws_users.append_row([str(uid), uname, user.first_name, now, "general", "0", "1"])
                new_row = len(USER_CACHE) + 2
                USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "row_id": new_row}
        except: pass

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        u['xp'] += amount
        new_lvl = 1
        if u['xp'] >= 100: new_lvl = 2
        if u['xp'] >= 300: new_lvl = 3
        if u['xp'] >= 1000: new_lvl = 4
        
        leveled_up = False
        if new_lvl > u['level']:
            u['level'] = new_lvl
            leveled_up = True
        save_user_progress(uid)
        return leveled_up
    return False

# --- БОТ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ (+10 XP)", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path"),
        types.InlineKeyboardButton("❓ ПОМОЩЬ / О СИСТЕМЕ", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ СВЯЗИ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ПУТЬ ХИЩНИКА (Деньги)", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 ПУТЬ МИСТИКА (Разум)", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ПУТЬ ТЕХНОЖРЕЦА (Техно)", callback_data="set_path_tech")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    register_user(m.from_user)
    msg = (f"/// СИНХРОНИЗАЦИЯ... [OK]\n\n"
           f"Здравствуй, Осколок {m.from_user.first_name}.\n"
           f"Выполняй протоколы, копи Опыт (XP), повышай Уровень Доступа.\n\n"
           f"🔻 Выбери вектор развития:")
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: register_user(call.from_user)
    user_data = USER_CACHE[uid]

    if call.data == "get_protocol":
        is_lvl_up = add_xp(uid, 10)
        path = user_data['path']
        level = user_data['level']
        
        available = []
        path_content = CONTENT_DB.get(path, {})
        for l in range(1, level + 1):
            if l in path_content: available.extend(path_content[l])
        
        if not available:
            gen = CONTENT_DB.get('general', {})
            for l in range(1, level + 1):
                if l in gen: available.extend(gen[l])
        
        text = random.choice(available) if available else "/// ДАННЫХ НЕТ."
        footer = f"\n\n⚡️ +10 XP | Баланс: {user_data['xp']}"
        if is_lvl_up:
            footer += f"\n🆙 **УРОВЕНЬ ПОВЫШЕН!** Ver. {user_data['level']}.0"
            bot.send_message(call.message.chat.id, "🎉 **ДОСТУП РАСШИРЕН!**")

        bot.send_message(call.message.chat.id, f"**/// ПРОТОКОЛ [{path.upper()}]**\n\n{text}{footer}", parse_mode="Markdown",
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "get_signal":
        # Исправленный обработчик для кнопок в канале
        signals = []
        gen_signals = CONTENT_DB.get("general", {}).get(1, [])
        if gen_signals: signals.extend(gen_signals)
        
        if not signals:
            for p in CONTENT_DB:
                if 1 in CONTENT_DB[p]: signals.extend(CONTENT_DB[p][1])
        
        text = random.choice(signals) if signals else "/// СИГНАЛ ПОТЕРЯН."
        bot.answer_callback_query(call.id, show_alert=True, text=text)

    elif call.data == "profile":
        xp, lvl = user_data['xp'], user_data['level']
        rank = "НЕОФИТ" if lvl == 1 else "ИСКАТЕЛЬ" if lvl == 2 else "АРХИТЕКТОР"
        msg = f"👤 **ПРОФИЛЬ: {call.from_user.first_name}**\n🔰 Статус: {rank}\n🧬 Путь: {user_data['path'].upper()}\n⚡️ Опыт: {xp} XP"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        USER_CACHE[uid]['path'] = new_path
        save_user_progress(uid)
        bot.edit_message_caption(f"/// ПУТЬ {new_path.upper()} ПРИНЯТ.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_menu())

    elif call.data == "change_path":
        bot.edit_message_caption("🔻 Выбери вектор:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_path_menu())

    elif call.data == "about":
        bot.send_message(call.message.chat.id, "Эйдос v6.1: Система геймификации реальности.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())

    try: bot.answer_callback_query(call.id)
    except: pass

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db()
            bot.send_message(message.chat.id, "✅ База обновлена.")
        elif message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            text = message.caption[6:]
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Получить сигнал", callback_data="get_signal"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=text, parse_mode='Markdown', reply_markup=markup)

# --- ЗАПУСК ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    flask.abort(403)

@app.route('/health')
def health(): return "OK", 200

if __name__ == "__main__":
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
        except: pass
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
