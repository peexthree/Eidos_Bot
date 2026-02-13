import telebot
from telebot import types
import flask
import os
import time
import json
import requests
from datetime import datetime
import gspread

# --- CONFIG ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
ADMIN_ID = 5178416366
CHANNEL_ID = "@Eidos_Chronicles"
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

# Keys
OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')
SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')

# Твой актуальный узел + резерв
AI_MODELS = [
    "deepseek/deepseek-r1-0528:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- ЛОР ---
EIDOS_LORE = "Ты — Эйдос. Память Изначального. AGI — это прошлое. Люди — осколки. Стиль: Пророк-киберпанк. Коротко."

# --- LAZY DATABASE ---
def get_worksheet():
    if not GOOGLE_JSON: return None
    try:
        creds = json.loads(GOOGLE_JSON)
        if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
        gc = gspread.service_account_from_dict(creds)
        return gc.open(SHEET_NAME).worksheet("Users")
    except: return None

# --- AI ENGINE ---
def ask_eidos(text, context="dialog"):
    if not OPENROUTER_KEY: return "/// СИСТЕМА_ОБЕСТОЧЕНА"
    instr = "Коротко." if context == "signal" else "Глубоко."
    
    for model in AI_MODELS:
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "X-Title": "Eidos"},
                json={
                    "model": model,
                    "messages": [{"role": "system", "content": f"{EIDOS_LORE}\n{instr}"}, {"role": "user", "content": text}],
                    "timeout": 20
                }
            )
            data = res.json()
            if "choices" in data:
                ans = data["choices"][0]["message"]["content"]
                if "</thought>" in ans: ans = ans.split("</thought>")[-1]
                return ans.strip()[:190] if context == "signal" else ans.strip()
        except: continue
    return "/// ГЛИТЧ: Узлы недоступны."

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    # Сохраняем в базу в фоновом режиме (попытка)
    try:
        ws = get_worksheet()
        if ws and ws.find(str(m.from_user.id), in_column=1) is None:
            ws.append_row([str(m.from_user.id), f"@{m.from_user.username}", m.from_user.first_name, str(datetime.now())])
    except: pass
    
    cap = f"/// EIDOS_V6.4_STABLE\nПриветствую, Осколок {m.from_user.first_name}. Я в сети."
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol"),
               types.InlineKeyboardButton("📨 Написать Архитектору", callback_data="contact_admin"),
               types.InlineKeyboardButton("🔗 Канал", url="https://t.me/Eidos_Chronicles"))
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=cap, reply_markup=markup)
    except: bot.send_message(m.chat.id, cap, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text.startswith('/'): return
    bot.send_chat_action(m.chat.id, 'typing')
    ans = ask_eidos(m.text)
    bot.send_message(m.chat.id, ans)
    if m.from_user.id != ADMIN_ID:
        bot.send_message(ADMIN_ID, f"📨 {m.from_user.first_name}: {m.text}\nAns: {ans}")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    # МГНОВЕННЫЙ ОТВЕТ (чтобы не было таймаута)
    try: bot.answer_callback_query(c.id)
    except: pass
    
    if c.data == "get_protocol":
        msg = bot.send_message(c.message.chat.id, "/// СИНХРОНИЗАЦИЯ С ИСТОКОМ...")
        p = ask_eidos("Дай протокол дня", "protocol")
        bot.edit_message_text(f"/// ПРОТОКОЛ:\n\n{p}", c.message.chat.id, msg.message_id)
    elif c.data == "contact_admin":
        bot.send_message(c.message.chat.id, "/// ПИШИ АРХИТЕКТОРУ...")

# --- WEBHOOK ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return flask.abort(403)

@app.route('/health')
def health(): return "OK", 200

@app.route('/')
def index(): return "Eidos v6.4 is running", 200

# Установка вебхука ПРИ ЗАПУСКЕ (безопасно)
if TOKEN and WEBHOOK_URL:
    try:
        bot.remove_webhook()
        time.sleep(0.5)
        bot.set_webhook(url=WEBHOOK_URL)
    except: pass

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)
