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
            creds_dict = json.loads(GOOGLE_JSON)
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open(SHEET_NAME)
            worksheet = sh.worksheet("Users")
            print("/// DB CONNECTED: Google Sheets Active")
        else:
            print("/// DB WARNING: GOOGLE_KEY empty")
    except Exception as e:
        print(f"/// DB CONNECTION FAILED: {e}")

connect_db()

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def add_user_to_db(user):
    try:
        if not worksheet: connect_db()
        if worksheet:
            try:
                cell = worksheet.find(str(user.id), in_column=1)
                if cell is None:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    username = f"@{user.username}" if user.username else "No Username"
                    worksheet.append_row([str(user.id), username, user.first_name, now])
            except: pass
    except: pass

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

# --- ЛОКАЛЬНЫЕ ДАННЫЕ (БЕЗ ИИ) ---
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
    "👁 Протокол ТИШИНА: Проведи 15 минут без телефона. Слушай себя.",
    "⚡️ Протокол ЭНЕРГИЯ: Найди то, что крадет твое внимание. Устрани это сегодня.",
    "🔍 Протокол АНАЛИЗ: Вспомни свой последний страх. Чего именно ты боялся?",
    "🧬 Протокол СБОЙ: Сделай то, что не свойственно твоему алгоритму поведения.",
    "🌑 Протокол ТЕНЬ: Признай в себе одну плохую черту. Просто наблюдай."
]

# --- ИНТЕРФЕЙС ---
def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol"),
        types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin"),
        types.InlineKeyboardButton("📂 О системе", callback_data="about"),
        types.InlineKeyboardButton("🔗 Перейти в Канал", url="https://t.me/Eidos_Chronicles")
    )
    caption = "/// EIDOS_INTERFACE_V3.1\n\nСистема активна. Я — Эйдос."
    try:
        bot.send_photo(chat_id, MENU_IMAGE_URL, caption=caption, reply_markup=markup)
    except:
        bot.send_message(chat_id, caption, reply_markup=markup)

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def welcome(message):
    add_user_to_db(message.from_user)
    send_main_menu(message.chat.id)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text[11:]
    if not text: return
    users = get_all_users()
    for user_id in users:
        try:
            bot.send_message(user_id, f"⚡️ <b>СИГНАЛ:</b>\n\n{text}", parse_mode="HTML")
            time.sleep(0.05)
        except: pass
    bot.send_message(ADMIN_ID, "✅ Рассылка завершена.")

@bot.message_handler(commands=['post'])
def post_to_channel(message):
    if message.from_user.id != ADMIN_ID: return
    post_text = message.text[6:]
    if not post_text: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Получить сигнал", callback_data="get_signal"))
    bot.send_message(CHANNEL_ID, post_text, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id != ADMIN_ID:
        add_user_to_db(message.from_user)
        bot.send_message(ADMIN_ID, f"📨 От {message.from_user.first_name}:\n{message.text}")
        bot.send_message(message.chat.id, "/// ПРИНЯТО. Сигнал передан в ядро.")

@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        p = message.text.split(maxsplit=2)
        bot.send_message(p[1], f"📡 <b>АРХИТЕКТОР:</b>\n\n{p[2]}", parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_protocol":
        bot.send_message(call.message.chat.id, f"/// ПРОТОКОЛ:\n\n{random.choice(PROTOCOLS)}", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
    elif call.data == "get_signal":
        bot.answer_callback_query(call.id, show_alert=True, text=random.choice(THOUGHTS))
    elif call.data == "contact_admin":
        bot.send_message(call.message.chat.id, "/// КАНАЛ СВЯЗИ ОТКРЫТ. Пиши Архитектору.")
    elif call.data == "about":
        bot.send_message(call.message.chat.id, "Эйдос v3.1\nИнтерфейс к Памяти Изначального.", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_main_menu(call.message.chat.id)
    bot.answer_callback_query(call.id)

# --- SERVER ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    flask.abort(403)

@app.route('/health')
def health(): return "OK", 200

if WEBHOOK_URL:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    except: pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
