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

SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- СИСТЕМНАЯ ПАМЯТЬ ---
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {}

# --- ПОДКЛЮЧЕНИЕ ---
gc = None
sh = None
ws_users = None
ws_content = None

def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            
            # 1. ЗАГРУЗКА КОНТЕНТА (LVL 1-4)
            try: 
                ws_content = sh.worksheet("Content")
                records = ws_content.get_all_records()
                CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
                for r in records:
                    path = str(r.get('Path', 'general')).lower()
                    text = r.get('Text', '')
                    level = int(r.get('Level', 1)) if str(r.get('Level')).isdigit() else 1
                    if text:
                        if path not in CONTENT_DB: path = "general"
                        if level not in CONTENT_DB[path]: CONTENT_DB[path][level] = []
                        CONTENT_DB[path][level].append(text)
                print(f"/// CONTENT LOADED: {len(records)} units.")
            except Exception as e: print(f"/// CONTENT ERROR: {e}")

            # 2. ЗАГРУЗКА ЮЗЕРОВ
            try:
                ws_users = sh.worksheet("Users")
                all_v = ws_users.get_all_values()
                for i, row in enumerate(all_v[1:], start=2):
                    if row and row[0]:
                        uid = int(row[0])
                        USER_CACHE[uid] = {
                            "path": row[4] if len(row) > 4 and row[4] else "general",
                            "xp": int(row[5]) if len(row) > 5 and row[5].isdigit() else 0,
                            "level": int(row[6]) if len(row) > 6 and row[6].isdigit() else 1,
                            "row_id": i
                        }
                print(f"/// USERS CACHED: {len(USER_CACHE)}")
            except Exception as e: print(f"/// USERS ERROR: {e}")
    except Exception as e: print(f"/// DB CRITICAL: {e}")

connect_db()

# --- ФУНКЦИИ ЗАЩИТЫ И ПРОГРЕССА ---
def safe_edit(call, text, markup):
    """Исправляет ошибку 400: корректно редактирует и фото, и текст"""
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def save_progress(uid):
    def task():
        try:
            u = USER_CACHE.get(uid)
            if u and ws_users:
                ws_users.update_cell(u['row_id'], 5, u['path'])
                ws_users.update_cell(u['row_id'], 6, str(u['xp']))
                ws_users.update_cell(u['row_id'], 7, str(u['level']))
        except: pass
    threading.Thread(target=task).start()

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        u['xp'] += amount
        new_lvl = 1
        if u['xp'] >= 100: new_lvl = 2
        elif u['xp'] >= 300: new_lvl = 3
        elif u['xp'] >= 1000: new_lvl = 4
        
        up = new_lvl > u['level']
        u['level'] = new_lvl
        save_progress(uid)
        return up
    return False

# --- МЕНЮ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ (+10 XP)", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path"),
        types.InlineKeyboardButton("❓ О СИСТЕМЕ", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ХИЩНИК (Деньги)", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 МИСТИК (Разум)", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ТЕХНОЖРЕЦ (Техно)", callback_data="set_path_tech")
    )
    return markup

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid not in USER_CACHE:
        now = datetime.now().strftime("%Y-%m-%d")
        uname = f"@{m.from_user.username}" if m.from_user.username else "No"
        if ws_users:
            ws_users.append_row([str(uid), uname, m.from_user.first_name, now, "general", "0", "1"])
            USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "row_id": len(USER_CACHE)+2}
    
    msg = f"/// СИНХРОНИЗАЦИЯ...\n\nЗдравствуй, Осколок {m.from_user.first_name}. Выбери вектор развития:"
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]

    if call.data == "get_protocol":
        up = add_xp(uid, 10)
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, u['level'] + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            g_cont = CONTENT_DB.get('general', {})
            for l in range(1, u['level'] + 1):
                if l in g_cont: pool.extend(g_cont[l])
        
        txt = random.choice(pool) if pool else "/// ДАННЫХ НЕТ."
        res = f"**/// ПРОТОКОЛ [{u['path'].upper()}]**\n\n{txt}\n\n⚡️ +10 XP | XP: {u['xp']}"
        if up: bot.send_message(call.message.chat.id, "🎉 **УРОВЕНЬ ПОВЫШЕН!** Доступ к новым данным открыт.")
        bot.send_message(call.message.chat.id, res, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "get_signal":
        pool = []
        for p in CONTENT_DB:
            if 1 in CONTENT_DB[p]: pool.extend(CONTENT_DB[p][1])
        txt = random.choice(pool) if pool else "/// СИГНАЛ ПОТЕРЯН."
        bot.answer_callback_query(call.id, show_alert=True, text=txt)

    elif call.data == "profile":
        rank = "НЕОФИТ" if u['level'] == 1 else "ИСКАТЕЛЬ" if u['level'] == 2 else "АРХИТЕКТОР"
        msg = f"👤 **ПРОФИЛЬ**\n🔰 Статус: {rank}\n🧬 Путь: {u['path'].upper()}\n⚡️ Опыт: {u['xp']} XP"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif "set_path_" in call.data:
        u['path'] = call.data.split("_")[-1]
        save_progress(uid)
        safe_edit(call, f"/// ПУТЬ {u['path'].upper()} ПРИНЯТ.", get_main_menu())

    elif call.data == "change_path":
        safe_edit(call, "🔻 Выбери вектор развития:", get_path_menu())

    elif call.data == "about":
        safe_edit(call, "**EIDOS v6.2**\nТренажер реальности. Расти, чтобы взломать систему.", get_main_menu())

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())
    
    try: bot.answer_callback_query(call.id)
    except: pass

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db()
            bot.send_message(message.chat.id, "✅ Синхронизация завершена.")
        elif message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Получить сигнал", callback_data="get_signal"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=message.caption[6:], reply_markup=markup)

# --- ЗАПУСК ---
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
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
