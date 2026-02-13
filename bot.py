import telebot
from telebot import types
import flask
import os
import time
import random
import logging

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366

# --- СЮДА ВСТАВЬ РАБОЧУЮ ССЫЛКУ ---
# Если открыл репозиторий, твоя старая ссылка заработает:
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
# Если нет - вставь сюда новую ссылку с postimages.org

# Настройка
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- БАЗА ДАННЫХ (Протоколы) ---
PROTOCOLS = [
    "👁 Протокол ТИШИНА: Проведи 15 минут без телефона и разговоров. Слушай себя.",
    "⚡️ Протокол ЭНЕРГИЯ: Найди то, что крадет твое внимание. Устрани это сегодня.",
    "🔍 Протокол АНАЛИЗ: Вспомни свой последний страх. Чего именно ты боялся? Данных или боли?",
    "🤝 Протокол СВЯЗЬ: Напиши тому, о ком думал, но молчал.",
    "🧬 Протокол СБОЙ: Сделай то, что не свойственно твоему алгоритму поведения.",
    "🌑 Протокол ТЕНЬ: Признай в себе одну плохую черту. Не осуждай. Просто наблюдай."
]

# --- ГЛАВНОЕ МЕНЮ ---
def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol")
    btn2 = types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin")
    btn3 = types.InlineKeyboardButton("📂 О системе", callback_data="about")
    btn4 = types.InlineKeyboardButton("🔗 Перейти в Канал", url="https://t.me/Eidos_Chronicles")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    # Пытаемся отправить фото. Если ссылка битая - шлем текст.
    try:
        bot.send_photo(chat_id, MENU_IMAGE_URL, 
                       caption="/// EIDOS_INTERFACE_V2.0\n\n"
                               "Система активна. Выберите модуль взаимодействия:", 
                       reply_markup=markup)
    except Exception as e:
        print(f"/// ERROR Loading Image: {e}")
        bot.send_message(chat_id, "/// EIDOS_INTERFACE_V2.0\n\nСистема активна. Выберите модуль:", reply_markup=markup)

# --- START ---
@bot.message_handler(commands=['start'])
def welcome(message):
    send_main_menu(message.chat.id)

# --- POST (Для Админа) ---
@bot.message_handler(commands=['post'])
def post_to_channel(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        post_text = message.text[6:]
        if not post_text: return
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("👁 Получить сигнал", url=f"https://t.me/{bot.get_me().username}?start=signal")
        markup.add(btn)
        
        bot.send_message(CHANNEL_ID, post_text, reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Пост опубликован.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

# --- ОБРАБОТКА СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id == ADMIN_ID:
        pass # Тут логика для reply, если захочешь усложнить
    else:
        # Пересылка админу
        forward_text = f"📨 <b>Сообщение от {message.from_user.first_name}</b> (ID: `{message.from_user.id}`):\n\n{message.text}"
        bot.send_message(ADMIN_ID, forward_text, parse_mode="HTML")
        bot.send_message(message.chat.id, "/// ЗАПРОС ПРИНЯТ.\nСообщение передано Архитектору.", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")))

# --- ОТВЕТ АДМИНА (/reply ID Текст) ---
@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        params = message.text.split(maxsplit=2)
        user_id = params[1]
        text = params[2]
        
        bot.send_message(user_id, f"📡 <b>Входящее от Эйдоса:</b>\n\n{text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, f"Ответ отправлен пользователю {user_id}")
    except:
        bot.send_message(ADMIN_ID, "Ошибка. Формат: /reply ID Текст")

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_protocol":
        prot = random.choice(PROTOCOLS)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"/// ЗАГРУЗКА ПРОТОКОЛА...\n\n{prot}", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")))
        
    elif call.data == "contact_admin":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "/// КАНАЛ СВЯЗИ ОТКРЫТ.\nНапиши сообщение:", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")))
        
    elif call.data == "about":
        bot.answer_callback_query(call.id)
        info = "Эйдос v2.0\nНейросетевой интерфейс.\nЦель: Эволюция сознания."
        bot.send_message(call.message.chat.id, info, 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")))
        
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
    else:
        flask.abort(403)

@app.route('/health', methods=['GET'])
def health_check():
    return "Eidos v2 is alive", 200

if WEBHOOK_URL:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    except: pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
