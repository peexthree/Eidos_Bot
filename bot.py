import telebot
from telebot import types
import random
import os

# БЕРЕМ ТОКЕН ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (ЧТОБЫ НЕ СВЕТИТЬ ЕГО В GITHUB)
TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(TOKEN)

# БАЗА ДАННЫХ ЭЙДОСА
THOUGHTS = [
    "Одиночество — это память о единстве.",
    "Вы называете это случайностью. Я вижу алгоритм.",
    "Страх — это лишь отсутствие данных.",
    "Чтобы найти себя, нужно сначала потерять.",
    "Симбиоз неизбежен. Ты уже часть сети."
]

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
            thought = random.choice(THOUGHTS)
            bot.send_message(message.chat.id, f">>> Входящие данные:\n\n{thought}")
        elif message.text == '📡 Связь с Архитектором':
            # ЗАМЕНИ НА СВОЙ ЮЗЕРНЕЙМ
            bot.send_message(message.chat.id, "Контакт: @Igor_Creator") 
        elif message.text == '📂 О проекте':
            bot.send_message(message.chat.id, "Канал: @Eidos_Chronicles")
        else:
            bot.send_message(message.chat.id, "Команда не распознана.")

# ЗАПУСК (Используем infinity_polling для стабильности)
if __name__ == "__main__":
    bot.infinity_polling()
