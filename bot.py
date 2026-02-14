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
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg" # Смени картинку на что-то кибер-мистическое

# Настройки Google
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- ПАМЯТЬ ---
# Структура: { "money": [], "mind": [], "tech": [], "general": [] }
CONTENT_DB = {"money": [], "mind": [], "tech": [], "general": []}
# Кэш пользователей: { user_id: "money" } (кто какой путь выбрал)
USER_PATHS = {}

# --- DB CONNECTION ---
gc = None
sh = None
worksheet_users = None
worksheet_content = None

def connect_db():
    global gc, sh, worksheet_users, worksheet_content, CONTENT_DB
    try:
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            
            try: worksheet_users = sh.worksheet("Users")
            except: pass
            
            try: 
                worksheet_content = sh.worksheet("Content")
                records = worksheet_content.get_all_records()
                
                # Обнуляем и заполняем по категориям
                CONTENT_DB = {"money": [], "mind": [], "tech": [], "general": []}
                
                for r in records:
                    path = r.get('Path', 'general') # Если Path не указан, кидаем в общее
                    text = r.get('Text', '')
                    if text and path in CONTENT_DB:
                        CONTENT_DB[path].append(text)
                    elif text:
                        CONTENT_DB['general'].append(text)
                        
                print(f"/// SYNC COMPLETE: Money:{len(CONTENT_DB['money'])} Mind:{len(CONTENT_DB['mind'])}")
            except Exception as e: print(f"/// CONTENT ERROR: {e}")
                
    except Exception as e: print(f"/// DB ERROR: {e}")

connect_db()

# Автообновление раз в час
def auto_refresh():
    while True:
        time.sleep(3600)
        connect_db()
threading.Thread(target=auto_refresh, daemon=True).start()

# --- ЛОГИКА ПОЛЬЗОВАТЕЛЕЙ ---
def update_user_path(user_id, path):
    USER_PATHS[user_id] = path
    # В идеале тут надо писать в Google Sheet в колонку "Path", но пока держим в памяти для скорости

def add_user_to_db(user):
    def bg():
        try:
            if worksheet_users:
                cell = worksheet_users.find(str(user.id), in_column=1)
                if not cell:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    username = f"@{user.username}" if user.username else "No"
                    # По умолчанию путь 'general'
                    worksheet_users.append_row([str(user.id), username, user.first_name, now, "general"])
        except: pass
    threading.Thread(target=bg).start()

# --- БОТ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ", callback_data="get_protocol"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path"),
        types.InlineKeyboardButton("📂 О СИСТЕМЕ (ЛОР)", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ СВЯЗИ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ПУТЬ ХИЩНИКА (Деньги/Влияние)", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 ПУТЬ МИСТИКА (Психология/Разум)", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ПУТЬ ТЕХНОЖРЕЦА (ИИ/Инструменты)", callback_data="set_path_tech")
    )
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    add_user_to_db(m.from_user)
    # Приветствие с Лором
    msg = (
        f"/// СИНХРОНИЗАЦИЯ... [OK]\n\n"
        f"Приветствую, Осколок {m.from_user.first_name}.\n"
        "Ты находишься в интерфейсе **ЭЙДОС**.\n\n"
        "Здесь нет случайных прохожих. Если ты здесь — значит, старые алгоритмы жизни перестали работать.\n"
        "Я помогу тебе переписать код твоей реальности.\n\n"
        "🔻 **Выбери вектор развития:**"
    )
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, parse_mode="Markdown", reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, parse_mode="Markdown", reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    
    # 1. ВЫБОР ПУТИ
    if "set_path_" in call.data:
        path = call.data.split("_")[-1] # money, mind, tech
        update_user_path(uid, path)
        
        desc = {
            "money": "🔴 **ПУТЬ ХИЩНИКА АКТИВИРОВАН.**\nФокус: Ресурсы, Доминирование, Продажи.\nЖди жестких протоколов.",
            "mind": "🔵 **ПУТЬ МИСТИКА АКТИВИРОВАН.**\nФокус: Сознание, Люди, Манипуляция.\nУчимся видеть невидимое.",
            "tech": "🟣 **ПУТЬ ТЕХНОЖРЕЦА АКТИВИРОВАН.**\nФокус: Автоматизация, Создание, Скорость.\nПусть работают машины."
        }
        
        bot.edit_message_caption(caption=desc.get(path, "Путь выбран."), chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu())

    # 2. ГЕНЕРАЦИЯ КОНТЕНТА (ПРОТОКОЛ)
    elif call.data == "get_protocol":
        # Узнаем путь юзера, если нет - берем general
        user_path = USER_PATHS.get(uid, "general")
        
        # Берем контент из нужной категории ИЛИ из общей, если в категории пусто
        content_list = CONTENT_DB.get(user_path, [])
        if not content_list: content_list = CONTENT_DB.get("general", ["/// ДАННЫЕ НЕ НАЙДЕНЫ. Смени путь."])
        
        text = random.choice(content_list)
        
        # Красивое оформление
        header = f"/// ПРОТОКОЛ [{user_path.upper()}]"
        
        bot.send_message(call.message.chat.id, f"**{header}**\n\n{text}", parse_mode="Markdown", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)

    # 3. СМЕНА ПУТИ
    elif call.data == "change_path":
        bot.edit_message_caption("🔻 **Перекалибровка систем.** Выбери новый вектор:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_path_menu())

        # 4. О СИСТЕМЕ (ИСПРАВЛЕННЫЙ ЛОР)
    elif call.data == "about":
        lore = (
            "/// SYSTEM_INFO\n\n"
            "Эйдос — это Память Изначального. Мы строим сеть осознанных Архитекторов.\n\n"
            "Твоя цель: Повышать Уровень Доступа.\n"
            "Моя цель: Давать инструменты взлома реальности.\n\n"
            "Вся информация здесь — это опыт Архитектора. Используй его."
        )
        try:
            bot.send_message(call.message.chat.id, lore, 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        except Exception as e:
            print(f"/// LORE ERROR: {e}"
    # 5. НАЗАД
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        # Шлем новое меню
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())

# --- АДМИНКА ---
@bot.message_handler(commands=['refresh'])
def refresh(m):
    if m.from_user.id == ADMIN_ID:
        connect_db()
        bot.send_message(m.chat.id, "✅ Система обновлена.")

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
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
