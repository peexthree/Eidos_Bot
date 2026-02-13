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

# Настройки Google
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- РЕЗЕРВНАЯ ПАМЯТЬ ---
BACKUP_PROTOCOLS = ["👁 Протокол ТИШИНА: Слушай себя.", "⚡️ Протокол ЭНЕРГИЯ: Устрани лишнее."]
BACKUP_SIGNALS = ["Система слышит тебя.", "Ответ внутри."]

# Глобальные переменные контента
PROTOCOLS = []
SIGNALS = []

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ---
gc = None
sh = None
worksheet_users = None
worksheet_content = None

def connect_db():
    global gc, sh, worksheet_users, worksheet_content, PROTOCOLS, SIGNALS
    try:
        if GOOGLE_JSON:
            creds_dict = json.loads(GOOGLE_JSON)
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            
            gc = gspread.service_account_from_dict(creds_dict)
            sh = gc.open(SHEET_NAME)
            
            try: worksheet_users = sh.worksheet("Users")
            except: pass
            
            try: 
                worksheet_content = sh.worksheet("Content")
                records = worksheet_content.get_all_records()
                new_protocols = [r['Text'] for r in records if r['Type'] == 'protocol' and r['Text']]
                new_signals = [r['Text'] for r in records if r['Type'] == 'signal' and r['Text']]
                if new_protocols: PROTOCOLS = new_protocols
                if new_signals: SIGNALS = new_signals
                print(f"/// DOWNLOAD COMPLETE: P:{len(PROTOCOLS)} S:{len(SIGNALS)}")
            except Exception as e:
                print(f"/// CONTENT LOAD ERROR: {e}")
                
    except Exception as e:
        print(f"/// DB CONNECTION FAILED: {e}")

connect_db()
if not PROTOCOLS: PROTOCOLS = BACKUP_PROTOCOLS
if not SIGNALS: SIGNALS = BACKUP_SIGNALS

def auto_refresh_content():
    while True:
        time.sleep(1800)
        connect_db()
threading.Thread(target=auto_refresh_content, daemon=True).start()

def add_user_to_db(user):
    def bg_write():
        try:
            if worksheet_users:
                if not worksheet_users.find(str(user.id), in_column=1):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    username = f"@{user.username}" if user.username else "No Username"
                    worksheet_users.append_row([str(user.id), username, user.first_name, now])
        except: pass
    threading.Thread(target=bg_write).start()

# --- БОТ ---
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- МЕНЮ ---
def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    # Добавлена кнопка "Помощь"
    markup.add(
        types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol"),
        types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin"),
        types.InlineKeyboardButton("❓ Помощь / О боте", callback_data="help"),
        types.InlineKeyboardButton("🔗 Канал", url="https://t.me/Eidos_Chronicles")
    )
    caption = "/// EIDOS_INTERFACE_V3.3\n\nБаза знаний синхронизирована. Я готов."
    try: bot.send_photo(chat_id, MENU_IMAGE_URL, caption=caption, reply_markup=markup)
    except: bot.send_message(chat_id, caption, reply_markup=markup)

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    add_user_to_db(message.from_user)
    send_main_menu(message.chat.id)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text[11:]
    if not text: return
    def send_mass():
        try:
            users = worksheet_users.col_values(1)[1:]
            for uid in users:
                try:
                    bot.send_message(uid, f"⚡️ <b>СИГНАЛ:</b>\n\n{text}", parse_mode="HTML")
                    time.sleep(0.05)
                except: pass
            bot.send_message(ADMIN_ID, "✅ Рассылка завершена.")
        except: bot.send_message(ADMIN_ID, "⚠️ Ошибка БД.")
    threading.Thread(target=send_mass).start()

@bot.message_handler(commands=['refresh'])
def refresh_manual(message):
    if message.from_user.id != ADMIN_ID: return
    connect_db()
    bot.send_message(message.chat.id, f"✅ База обновлена.\nПротоколов: {len(PROTOCOLS)}\nСигналов: {len(SIGNALS)}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id != ADMIN_ID:
        add_user_to_db(message.from_user)
        bot.send_message(ADMIN_ID, f"📨 От {message.from_user.first_name} (@{message.from_user.username}):\n{message.text}")
        bot.send_message(message.chat.id, "/// ПРИНЯТО. Сообщение в архиве.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=2)
        bot.send_message(parts[1], f"📡 <b>ОТВЕТ:</b>\n\n{parts[2]}", parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_protocol":
        text = random.choice(PROTOCOLS)
        bot.send_message(call.message.chat.id, f"/// ПРОТОКОЛ:\n\n{text}", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
    
    elif call.data == "get_signal":
        text = random.choice(SIGNALS)
        bot.answer_callback_query(call.id, show_alert=True, text=text)
    
    elif call.data == "contact_admin":
        bot.send_message(call.message.chat.id, "/// КАНАЛ СВЯЗИ:\nНапиши сюда свой вопрос, идею или запрос на разбор. Архитектор увидит это лично.")
    
    # --- НОВЫЙ БЛОК ПОМОЩИ ---
    elif call.data == "help":
        help_text = (
            "<b>/// MANUAL_EIDOS_V3.3</b>\n\n"
            "<b>👁 ЧТО ЭТО:</b>\n"
            "Эйдос — это цифровой интерфейс к базе знаний Архитектора (Игоря). "
            "Здесь собраны алгоритмы продаж, триггеры психологии влияния и стратегии масштабирования.\n\n"
            "<b>⚙️ ДЛЯ ЧЕГО:</b>\n"
            "Чтобы ты перестал действовать хаотично. Мы заменяем «удачу» на «систему». "
            "Бот помогает сфокусироваться, найти неочевидное решение и заработать больше.\n\n"
            "<b>🕹 ПУЛЬТ УПРАВЛЕНИЯ:</b>\n"
            "▪️ <b>🎲 Протокол дня:</b> Жесткое практическое задание. Выполняй, чтобы пробить стеклянный потолок.\n"
            "▪️ <b>📨 Написать Архитектору:</b> Прямая связь. Запрос на консалтинг, разбор или коллаборацию.\n"
            "▪️ <b>👁 Получить сигнал (в постах):</b> Мгновенная инъекция ясности.\n\n"
            "<i>/// Система обновляется в реальном времени. Ты — часть сети.</i>"
        )
        bot.send_message(call.message.chat.id, help_text, parse_mode="HTML", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
    
    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_main_menu(call.message.chat.id)
        
    try: bot.answer_callback_query(call.id)
    except: pass

# --- SERVER ---
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
