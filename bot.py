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

# --- ПАМЯТЬ ---
CONTENT_DB = {"money": [], "mind": [], "tech": [], "general": []}
# Кэш пользователей для скорости: { user_id: {"path": "money", "xp": 0, "level": 1, "row": 2} }
USER_CACHE = {}

# --- ПОДКЛЮЧЕНИЕ ---
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
            
            # 1. Загружаем Контент
            try: 
                ws_content = sh.worksheet("Content")
                records = ws_content.get_all_records()
                CONTENT_DB = {"money": [], "mind": [], "tech": [], "general": []}
                for r in records:
                    path = r.get('Path', 'general')
                    text = r.get('Text', '')
                    # Тут можно добавить проверку Level контента в будущем
                    if text:
                        target = CONTENT_DB.get(path, CONTENT_DB['general'])
                        target.append(text)
            except: pass

            # 2. Загружаем Юзеров в кэш (чтобы не дергать API каждый раз)
            try:
                ws_users = sh.worksheet("Users")
                users_data = ws_users.get_all_values() # Получаем всё как список списков
                # Предполагаем структуру: ID | @username | Name | Date | Path | XP | Level
                # Пропускаем заголовок
                for i, row in enumerate(users_data[1:], start=2):
                    if row:
                        uid = int(row[0])
                        path = row[4] if len(row) > 4 else "general"
                        xp = int(row[5]) if len(row) > 5 and row[5].isdigit() else 0
                        level = int(row[6]) if len(row) > 6 and row[6].isdigit() else 1
                        USER_CACHE[uid] = {"path": path, "xp": xp, "level": level, "row": i}
                print(f"/// SYNC: {len(USER_CACHE)} users loaded.")
            except Exception as e: print(f"/// USERS LOAD ERROR: {e}")

    except Exception as e: print(f"/// DB ERROR: {e}")

connect_db()

# Фоновое сохранение (чтобы не тормозить бота)
def save_user_progress(uid):
    def task():
        try:
            user = USER_CACHE.get(uid)
            if user and ws_users:
                # Обновляем ячейки Path(E), XP(F), Level(G)
                row = user['row']
                ws_users.update_cell(row, 5, user['path'])
                ws_users.update_cell(row, 6, user['xp'])
                ws_users.update_cell(row, 7, user['level'])
        except Exception as e: print(f"Save error: {e}")
    threading.Thread(target=task).start()

def register_user(user):
    uid = user.id
    if uid not in USER_CACHE:
        try:
            if ws_users:
                now = datetime.now().strftime("%Y-%m-%d")
                uname = f"@{user.username}" if user.username else "No"
                # Добавляем в конец таблицы
                ws_users.append_row([str(uid), uname, user.first_name, now, "general", 0, 1])
                # Узнаем номер строки (грубо, но быстро)
                row_idx = len(USER_CACHE) + 2 
                USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "row": row_idx}
        except: pass

# --- ГЕЙМИФИКАЦИЯ ---
def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        u['xp'] += amount
        
        # Логика уровней: Lv2 = 100xp, Lv3 = 300xp, Lv4 = 600xp
        new_level = 1
        if u['xp'] >= 100: new_level = 2
        if u['xp'] >= 300: new_level = 3
        if u['xp'] >= 600: new_level = 4
        
        # Если уровень вырос
        if new_level > u['level']:
            u['level'] = new_level
            return True # Level Up!
        
        save_user_progress(uid)
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
        types.InlineKeyboardButton("📂 ЛОР СИСТЕМЫ", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ХИЩНИК (Деньги)", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 МИСТИК (Разум)", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ТЕХНОЖРЕЦ (ИИ)", callback_data="set_path_tech")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    register_user(m.from_user)
    msg = f"/// СИНХРОНИЗАЦИЯ...\n\nДобро пожаловать в Эйдос, {m.from_user.first_name}.\nЗдесь твои действия имеют значение.\nВыполняй протоколы, копи Опыт, повышай Уровень Доступа.\n\n🔻 Выбери свой Путь:"
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    user_data = USER_CACHE.get(uid, {"path": "general", "xp": 0, "level": 1})
    
    # 1. ПОЛУЧИТЬ ПРОТОКОЛ (ГЕЙМИФИКАЦИЯ)
    if call.data == "get_protocol":
        # Начисляем XP
        is_levelup = add_xp(uid, 10)
        
        path = user_data['path']
        content = CONTENT_DB.get(path, [])
        if not content: content = CONTENT_DB.get("general", ["Данные не найдены."])
        text = random.choice(content)
        
        header = f"/// ПРОТОКОЛ [{path.upper()}]"
        footer = f"\n\n⚡️ +10 XP | Твой баланс: {user_data['xp']}"
        
        if is_levelup:
            footer += f"\n🆙 **УРОВЕНЬ ПОВЫШЕН!** Теперь ты: Ver. {user_data['level']}.0"
        
        bot.send_message(call.message.chat.id, f"**{header}**\n\n{text}{footer}", parse_mode="Markdown",
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)

    # 2. ПРОФИЛЬ ЮЗЕРА
    elif call.data == "profile":
        lv = user_data['level']
        xp = user_data['xp']
        pt = user_data['path'].upper()
        
        # Статусы
        rank = "НЕОФИТ"
        if lv == 2: rank = "ИСКАТЕЛЬ"
        if lv == 3: rank = "ОПЕРАТОР"
        if lv >= 4: rank = "АРХИТЕКТОР"
        
        msg = (
            f"👤 **ЛИЧНОЕ ДЕЛО: {call.from_user.first_name}**\n\n"
            f"🔰 **Статус:** {rank} (Ver. {lv}.0)\n"
            f"🧬 **Вектор:** {pt}\n"
            f"⚡️ **Опыт:** {xp} XP\n\n"
            f"--- \n"
            f"До следующего уровня: {100 - xp if xp < 100 else 'MAX'}"
        )
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown",
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    # 3. СМЕНА ПУТИ
    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        if uid in USER_CACHE: 
            USER_CACHE[uid]['path'] = new_path
            save_user_progress(uid) # Сохраняем выбор в базу
        
        bot.edit_message_caption(f"/// ПУТЬ {new_path.upper()} ЗАГРУЖЕН.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_menu())

    elif call.data == "change_path":
        bot.edit_message_caption("Выбери новый вектор:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_path_menu())

    elif call.data == "about":
        bot.send_message(call.message.chat.id, "Эйдос — это тренажер реальности.\nКаждое действие здесь меняет твой код там, снаружи.", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())

    try: bot.answer_callback_query(call.id)
    except: pass

# --- POST ---
@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db()
            bot.send_message(message.chat.id, "✅ База обновлена.")
            return
        # Постинг (как в прошлой версии)
        if message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            text = message.caption[6:]
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Войти в Интерфейс", url=f"https://t.me/{bot.get_me().username}?start=post"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=text, parse_mode='Markdown', reply_markup=markup)
            bot.send_message(message.chat.id, "✅ Опубликовано.")

# --- WEBHOOK ---
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
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
