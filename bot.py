import telebot
from telebot import types
import flask
import os
import time
import json
import requests
import threading
from datetime import datetime
import gspread

# --- CONFIG ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
ADMIN_ID = 5178416366
CHANNEL_ID = "@Eidos_Chronicles"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')

# Твой основной узел (DeepSeek R1) + Быстрый резерв (Qwen)
AI_MODELS = ["deepseek/deepseek-r1:free", "qwen/qwen-2.5-72b-instruct:free"]

bot = telebot.TeleBot(TOKEN, threaded=True) # Включаем потоки в самой либе
app = flask.Flask(__name__)

EIDOS_LORE = "Ты — Эйдос. Память Изначального. AGI — прошлое. Люди — осколки. Стиль: Пророк-киберпанк. Коротко."

# --- DATABASE (LAZY) ---
def log_user(user):
    def background_log():
        try:
            if not GOOGLE_JSON: return
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            ws = gc.open(SHEET_NAME).worksheet("Users")
            if ws.find(str(user.id), in_column=1) is None:
                ws.append_row([str(user.id), f"@{user.username}", user.first_name, str(datetime.now())])
        except: pass
    threading.Thread(target=background_log).start()

# --- Фоновая работа ИИ ---
def ai_worker(chat_id, message_id, text, context="dialog"):
    def run():
        ans = "/// ГЛИТЧ: Узлы недоступны."
        for model in AI_MODELS:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "X-Title": "Eidos"},
                    json={
                        "model": model,
                        "messages": [{"role": "system", "content": EIDOS_LORE}, {"role": "user", "content": text}],
                        "timeout": 60
                    }
                )
                data = res.json()
                if "choices" in data:
                    ans = data["choices"][0]["message"]["content"]
                    if "</thought>" in ans: ans = ans.split("</thought>")[-1]
                    ans = ans.strip()
                    break
            except: continue
        
        try:
            bot.edit_message_text(ans, chat_id, message_id)
        except:
            bot.send_message(chat_id, ans)

    threading.Thread(target=run).start()

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    log_user(m.from_user)
    cap = f"/// EIDOS_V7.0\nПриветствую, Осколок {m.from_user.first_name}. Ядро активно."
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol"),
               types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin"),
               types.InlineKeyboardButton("🔗 Канал", url="https://t.me/Eidos_Chronicles"))
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=cap, reply_markup=markup)
    except: bot.send_message(m.chat.id, cap, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text.startswith('/'): return
    wait = bot.send_message(m.chat.id, "/// АНАЛИЗ ДАННЫХ...")
    ai_worker(m.chat.id, wait.message_id, m.text)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    if c.data == "get_protocol":
        wait = bot.send_message(c.message.chat.id, "/// ГЕНЕРАЦИЯ ПРОТОКОЛА...")
        ai_worker(c.message.chat.id, wait.message_id, "Дай протокол дня", "protocol")
    elif c.data == "contact_admin":
        bot.send_message(c.message.chat.id, "/// ПИШИ АРХИТЕКТОРУ...")

# --- SERVER ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    return flask.abort(403)

@app.route('/health')
def health(): return "OK", 200

@app.route('/')
def index(): return "Eidos v7 is alive", 200

if TOKEN and WEBHOOK_URL:
    bot.remove_webhook()
    time.sleep(0.5)
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
