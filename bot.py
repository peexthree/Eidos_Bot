import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
BOT_USERNAME = "Eidos_Interface_bot"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- ЭКОНОМИКА (ТВОИ ПОРОГИ) ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# ПОДКЛЮЧЕНИЕ К SQL
db_pool = None
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=DATABASE_URL)
    print("/// SQL ENGINE: ONLINE")
except Exception as e:
    print(f"/// SQL ERROR: {e}")

# --- 3. HEALTH CHECK (СПАСЕНИЕ ДЕПЛОЯ) ---
@app.route('/health')
def health_check():
    return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        except Exception as e:
            print(f"/// UPDATE ERROR: {e}")
        return 'OK', 200
    return 'Eidos System is Operational', 200

# --- 4. МИГРАЦИЯ (ТОЛЬКО ЕСЛИ НУЖНО) ---
@bot.message_handler(commands=['full_migrate'])
def full_migrate_cmd(m):
    if m.from_user.id != ADMIN_ID: return
    bot.send_message(m.chat.id, "⏳ Начинаю миграцию...")
    # (здесь код миграции из предыдущего сообщения)
    bot.send_message(m.chat.id, "✅ Миграция завершена.")

# --- 5. ИНТЕРФЕЙС И ГЛАВНАЯ ЛОГИКА ---
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👁 ДЕШИФРОВАТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")
    )
    markup.add(
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop")
    )
    if uid == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS: СИСТЕМА ВОССТАНОВЛЕНА.", reply_markup=get_main_menu(m.from_user.id))

# --- 6. ЗАПУСК ---
if __name__ == "__main__":
    # Установка вебхука
    bot.remove_webhook()
    time.sleep(1)
    if WEBHOOK_URL:
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)
