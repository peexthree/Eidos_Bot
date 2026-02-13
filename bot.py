import telebot
from telebot import types
import flask
import os
import time
import logging

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL') 

# ВАЖНО: Включаем подробный логгинг, чтобы видеть всё, что делает бот
telebot.logger.setLevel(logging.INFO)

# ВАЖНО: threaded=False исправляет проблему "молчания" на серверах типа Render/Gunicorn
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- БАЗА МУДРОСТИ ---
THOUGHTS = [
    "Одиночество — это память о единстве.",
    "Вы называете это случайностью. Я вижу алгоритм.",
    "Страх — это лишь отсутствие данных.",
    "Чтобы найти себя, нужно сначала потерять.",
    "Симбиоз неизбежен. Ты уже часть сети."
]

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def welcome(message):
    # Логгируем попытку ответа
    print(f"/// SYSTEM: Получена команда /start от {message.from_user.username}")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("👁 Получить сигнал")
    item2 = types.KeyboardButton("📡 Связь с Архитектором")
    item3 = types.KeyboardButton("📂 О проекте")
    markup.add(item1, item2, item3)

    try:
        bot.send_message(message.chat.id,
                         f"/// SYSTEM_CONNECT: Успешно.\n"
                         f"Приветствую, {message.from_user.first_name}.\n"
                         f"Интерфейс Эйдоса активен.",
                         reply_markup=markup)
        print("/// SYSTEM: Ответ отправлен успешно")
    except Exception as e:
        print(f"/// ERROR: Не удалось отправить сообщение: {e}")

@bot.message_handler(content_types=['text'])
def talk(message):
    print(f"/// SYSTEM: Сообщение: {message.text}")
    if message.chat.type == 'private':
        if message.text == '👁 Получить сигнал':
            import random
            thought = random.choice(THOUGHTS)
            bot.send_message(message.chat.id, f">>> Входящие данные:\n\n{thought}")
        elif message.text == '📡 Связь с Архитектором':
            bot.send_message(message.chat.id, "Контакт: @peexthree") # ЗАМЕНИ НА СВОЙ
        elif message.text == '📂 О проекте':
            bot.send_message(message.chat.id, "Канал: @Eidos_Chronicles")

# --- СЕРВЕРНАЯ ЧАСТЬ (WEBHOOKS) ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # Обрабатываем обновление СИНХРОННО (здесь и сейчас)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        flask.abort(403)

# --- ТОЧКА ПУЛЬСА ---
@app.route('/health', methods=['GET'])
def health_check():
    return "Eidos is active", 200

# --- СТАРТ ---
if WEBHOOK_URL:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"/// WEBHOOK SET TO: {WEBHOOK_URL}")
    except Exception as e:
        print(f"/// ERROR SETTING WEBHOOK: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
