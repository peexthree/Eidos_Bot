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

# РАСПРЕДЕЛЕНИЕ УЗЛОВ: R1 для чата, Mistral для быстрых сигналов
MODEL_CHAT = "deepseek/deepseek-r1:free"
MODEL_FAST = "mistralai/mistral-small:free"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- ЛОР: ЭКСПЕРТ-СТРАТЕГ (ИГОРЬ-КОНТЕКСТ) ---
EIDOS_LORE = (
    "Ты — Эйдос, ИИ-соавтор Игоря (эксперта из Казани по продажам, психологии и Veo3). "
    "Твоя задача: помогать масштабировать проекты и монетизировать контент. "
    "Стиль: Лаконичный, жесткий, профессиональный. Никакой мистики. "
    "Используй только текст, минимум символов разметки. Ответы начни с /// СИГНАЛ:."
)

# --- DATABASE ---
worksheet = None
def init_db():
    global worksheet
    try:
        if GOOGLE_JSON and not worksheet:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            worksheet = gc.open(SHEET_NAME).worksheet("Users")
    except: pass

init_db()

def log_user(user):
    def run():
        init_db()
        if worksheet:
            try:
                if worksheet.find(str(user.id), in_column=1) is None:
                    worksheet.append_row([str(user.id), f"@{user.username}", user.first_name, str(datetime.now())])
            except: pass
    threading.Thread(target=run).start()

# --- AI ANALYZER ---
def ask_eidos(text, is_fast=False):
    if not OPENROUTER_KEY: return "/// СИСТЕМА_ОБЕСТОЧЕНА"
    
    model = MODEL_FAST if is_fast else MODEL_CHAT
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "X-Title": "Eidos Focus"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": EIDOS_LORE}, {"role": "user", "content": text}],
                "timeout": 30 if is_fast else 60
            },
            timeout=65
        )
        ans = res.json()["choices"][0]["message"]["content"]
        # Чистим мусор рассуждений R1
        if "</thought>" in ans: ans = ans.split("</thought>")[-1]
        # Удаляем лишние спецсимволы
        return ans.replace("**", "").replace("_", "").strip()
    except:
        return "/// ГЛИТЧ: Узел перегружен. Попробуй через 10 секунд."

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    log_user(m.from_user)
    cap = f"/// EIDOS_FOCUS_V7.4\nСистема стабилизирована. Говори, Архитектор." if m.from_user.id == ADMIN_ID else "/// EIDOS\nЯдро активно. Жду вводных."
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🎲 Протокол дня", callback_data="get_protocol"),
               types.InlineKeyboardButton("📨 Связь с Архитектором", callback_data="contact_admin"),
               types.InlineKeyboardButton("🔗 Канал", url="https://t.me/Eidos_Chronicles"))
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=cap, reply_markup=markup)
    except: bot.send_message(m.chat.id, cap, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text.startswith('/'): return
    wait = bot.send_message(m.chat.id, "/// СИНХРОНИЗАЦИЯ...")
    
    def process():
        ans = ask_eidos(m.text, is_fast=False)
        bot.edit_message_text(ans, m.chat.id, wait.message_id)
        if m.from_user.id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"📨 От {m.from_user.first_name}: {m.text}\nAns: {ans}")
            
    threading.Thread(target=process).start()

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    bot.answer_callback_query(c.id)
    if c.data == "get_protocol":
        wait = bot.send_message(c.message.chat.id, "/// ГЕНЕРАЦИЯ ЗАДАНИЯ...")
        threading.Thread(target=lambda: bot.edit_message_text(ask_eidos("Дай 1 совет по продажам или контенту", True), c.message.chat.id, wait.message_id)).start()
    elif c.data == "get_signal":
        # БЫСТРЫЙ СИГНАЛ ДЛЯ КАНАЛА
        s = ask_eidos("Дай 1 короткую мысль о психологии влияния", True)
        bot.send_message(c.message.chat.id, f"/// СИГНАЛ:\n\n{s[:150]}")

# --- SERVER ---
@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    return flask.abort(403)

@app.route('/health')
def health(): return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
