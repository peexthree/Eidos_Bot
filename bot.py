import telebot
from telebot import types
import flask
import os
import time
import random
import logging
import gspread
import json
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

# Настройки Google
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ (Google Sheets) ---
gc = None
sh = None
worksheet = None

def connect_db():
    global gc, sh, worksheet
    try:
        if GOOGLE_JSON:
            print("/// DB: Ключ найден, начинаю обработку...")
            
            # 1. Загружаем JSON из строки
            creds_dict = json.loads(GOOGLE_JSON)
            
            # 2. АВТО-РЕМОНТ КЛЮЧА (Самое важное!)
            # Иногда Render портит символы \n в приватном ключе. Чиним их:
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')

            # 3. Авторизация
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open(SHEET_NAME)
            worksheet = sh.worksheet("Users")
            print("/// DB CONNECTED: Google Sheets Active (УСПЕХ)")
        else:
            print("/// DB WARNING: GOOGLE_KEY пустой!")
    except Exception as e:
        # Выводим подробную ошибку в логи, чтобы понять причину
        print(f"/// DB CONNECTION FAILED: {e}")

# Пробуем подключиться при старте
connect_db()

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def add_user_to_db(user):
    try:
        if not worksheet: connect_db()
        if worksheet:
            # Ищем ID пользователя
            try:
                cell = worksheet.find(str(user.id), in_column=1)
                if cell is None:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    username = f"@{user.username}" if user.username else "No Username"
                    worksheet.append_row([str(user.id), username, user.first_name, now])
                    print(f"/// DB: Новый пользователь {user.first_name} сохранен.")
            except Exception as find_err:
                # Если таблица пустая или ошибка поиска, просто пробуем добавить
                print(f"/// DB FIND ERROR: {find_err}")
    except Exception as e:
        print(f"/// DB WRITE ERROR: {e}")

def get_all_users():
    try:
        if not worksheet: connect_db()
        if worksheet:
            return worksheet.col_values(1)[1:] 
    except:
        return []

# --- НАСТРОЙКА БОТА ---
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- КОНТЕНТ ---
THOUGHTS = [
    "Одиночество — это память о единстве.",
    "Вы называете это случайностью. Я вижу алгоритм.",
    "Страх — это лишь отсутствие данных.",
    "Чтобы найти себя, нужно сначала потерять.",
    "Симбиоз неизбежен. Ты уже часть сети.",
    "Ответ внутри твоего запроса.",
    "Система слышит тебя.",
    "Загрузка реальности... 99%"
]

PROTOCOLS = [
    "👁 Протокол ТИШИНА: Проведи 15 минут без телефона и разговоров. Слушай себя.",
    "⚡️ Протокол ЭНЕРГИЯ: Найди то, что крадет твое внимание. Устрани это сегодня.",
    "🔍 Протокол АНАЛИЗ: Вспомни свой последний страх. Чего именно ты боялся? Данных или боли?",
    "🤝 Протокол СВЯЗЬ: Напиши тому, о ком думал, но молчал.",
    "🧬 Протокол СБОЙ: Сделай то, что не свойственно твоему алгоритму поведения.",
    "🌑 Протокол ТЕНЬ: Признай в себе одну плохую черту. Не осуждай. Просто наблюдай."
]

# --- ИНТЕРФЕЙС ---
def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol")
    btn2 = types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin")
    btn3 = types.InlineKeyboardButton("📂 О системе", callback_data="about")
    btn4 = types.InlineKeyboardButton("🔗 Перейти в Канал", url="https://t.me/Eidos_Chronicles")
    markup.add(btn1, btn2, btn3, btn4)
    
    try:
        bot.send_photo(chat_id, MENU_IMAGE_URL, 
                       caption="/// EIDOS_INTERFACE_V3.1\n\nСистема активна. Связь с базой установлена.", 
                       reply_markup=markup)
    except:
        bot.send_message(chat_id, "/// EIDOS_INTERFACE_V3.1\n\nСистема активна.", reply_markup=markup)

# --- START ---
@bot.message_handler(commands=['start'])
def welcome(message):
    add_user_to_db(message.from_user)
    send_main_menu(message.chat.id)

# --- РАССЫЛКА ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text[11:]
    if not text:
        bot.send_message(ADMIN_ID, "⚠️ Ошибка. Пример: /broadcast Привет")
        return

    users = get_all_users()
    bot.send_message(ADMIN_ID, f"📡 Рассылка на {len(users)} пользователей...")
    count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"⚡️ <b>СИГНАЛ:</b>\n\n{text}", parse_mode="HTML")
            count += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Успешно: {count}")

# --- POST ---
@bot.message_handler(commands=['post'])
def post_to_channel(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        post_text = message.text[6:]
        if not post_text: return
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("👁 Получить сигнал", callback_data="get_signal")
        markup.add(btn)
        bot.send_message(CHANNEL_ID, post_text, reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Пост опубликован.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# --- REPLY & TEXT ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id == ADMIN_ID: pass
    else:
        add_user_to_db(message.from_user)
        bot.send_message(ADMIN_ID, f"📨 От {message.from_user.first_name}:\n{message.text}")
        bot.send_message(message.chat.id, "/// ПРИНЯТО.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        params = message.text.split(maxsplit=2)
        bot.send_message(params[1], f"📡 <b>Ответ:</b>\n\n{params[2]}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, "✅")
    except: pass

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_protocol":
        bot.send_message(call.message.chat.id, f"/// ПРОТОКОЛ:\n\n{random.choice(PROTOCOLS)}", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)
    elif call.data == "get_signal":
        bot.answer_callback_query(call.id, show_alert=True, text=random.choice(THOUGHTS))
    elif call.data == "contact_admin":
        bot.send_message(call.message.chat.id, "Пиши сообщение:")
        bot.answer_callback_query(call.id)
    elif call.data == "about":
        bot.send_message(call.message.chat.id, "Эйдос v3.1 [DB Active]", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_main_menu(call.message.chat.id)

# --- SERVER ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else: flask.abort(403)

@app.route('/health', methods=['GET'])
def health_check(): return "Eidos v3.1 Alive", 200

if WEBHOOK_URL:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    except: pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
