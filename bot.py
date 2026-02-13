import telebot
from telebot import types
import flask
import os
import time

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
# Твой URL на Render (мы добавим его в переменные окружения позже)
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL') 

bot = telebot.TeleBot(TOKEN)
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("👁 Получить сигнал")
    item2 = types.KeyboardButton("📡 Связь с Архитектором")
    item3 = types.KeyboardButton("📂 О проекте")
    markup.add(item1, item2, item3)

    bot.send_message(message.chat.id,
                     f"/// SYSTEM_CONNECT: Успешно.\n"
                     f"Приветствую, {message.from_user.first_name}.\n"
                     f"Интерфейс Эйдоса активен.",
                     reply_markup=markup)

@bot.message_handler(content_types=['text'])
def talk(message):
    if message.chat.type == 'private':
        if message.text == '👁 Получить сигнал':
            import random
            thought = random.choice(THOUGHTS)
            bot.send_message(message.chat.id, f">>> Входящие данные:\n\n{thought}")
        elif message.text == '📡 Связь с Архитектором':
            bot.send_message(message.chat.id, "Контакт: @Igor_Creator") # ЗАМЕНИ НА СВОЙ
        elif message.text == '📂 О проекте':
            bot.send_message(message.chat.id, "Канал: @Eidos_Chronicles")

# --- СЕРВЕРНАЯ ЧАСТЬ (WEBHOOKS) ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
# --- ТОЧКА ПУЛЬСА ДЛЯ МОНИТОРИНГА ---
@app.route('/health', methods=['GET'])
def health_check():
    # Эйдос сообщает, что системы в норме
    return "Eidos is active. Systems normal.", 200
# Эта команда сработает один раз при запуске сервера
# Она сообщает Телеграму: "Шли данные вот сюда"
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    # Ставим вебхук на адрес твоего приложения
    bot.set_webhook(url=WEBHOOK_URL)
    # Запускаем Flask (Render сам даст порт через переменную PORT)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
