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

# --- СИСТЕМНАЯ ПАМЯТЬ (CACHE) ---
# Структура: { "money": {1: [txt, txt], 2: [txt]}, "mind": ... }
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
# Кэш пользователей: { user_id: {"path": "money", "xp": 0, "level": 1, "row_id": 2} }
USER_CACHE = {}

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ---
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
            
            # 1. ЗАГРУЗКА КОНТЕНТА
            try: 
                ws_content = sh.worksheet("Content")
                records = ws_content.get_all_records()
                # Сброс базы
                CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
                
                count = 0
                for r in records:
                    path = r.get('Path', 'general')
                    text = r.get('Text', '')
                    level = r.get('Level', 1)
                    if not str(level).isdigit(): level = 1
                    level = int(level)

                    if text:
                        if path not in CONTENT_DB: path = "general"
                        if level not in CONTENT_DB[path]: CONTENT_DB[path][level] = []
                        CONTENT_DB[path][level].append(text)
                        count += 1
                print(f"/// CONTENT LOADED: {count} units.")
            except Exception as e: print(f"/// CONTENT ERROR: {e}")

            # 2. ЗАГРУЗКА ЮЗЕРОВ (КЭШИРОВАНИЕ)
            try:
                ws_users = sh.worksheet("Users")
                # Получаем все данные одним запросом для скорости
                all_values = ws_users.get_all_values()
                # Структура: ID(0)|User(1)|Name(2)|Date(3)|Path(4)|XP(5)|Level(6)
                
                for i, row in enumerate(all_values[1:], start=2): # start=2 т.к. строка 1 это заголовки
                    if row and row[0]: # Если есть ID
                        uid = int(row[0])
                        path = row[4] if len(row) > 4 and row[4] else "general"
                        xp = int(row[5]) if len(row) > 5 and row[5].isdigit() else 0
                        lvl = int(row[6]) if len(row) > 6 and row[6].isdigit() else 1
                        
                        USER_CACHE[uid] = {"path": path, "xp": xp, "level": lvl, "row_id": i}
                print(f"/// USERS CACHED: {len(USER_CACHE)} profiles.")
            except Exception as e: print(f"/// USERS ERROR: {e}")

    except Exception as e: print(f"/// DB CRITICAL: {e}")

connect_db()

# --- ФОНОВЫЕ ПРОЦЕССЫ ---
def save_user_progress(uid):
    """Сохраняет XP и Level пользователя в Гугл Таблицу (фоном)"""
    def task():
        try:
            user = USER_CACHE.get(uid)
            if user and ws_users:
                row = user['row_id']
                # Обновляем ячейки E(Path), F(XP), G(Level)
                # gspread использует нумерацию с 1. A=1, E=5, F=6, G=7
                ws_users.update_cell(row, 5, user['path'])
                ws_users.update_cell(row, 6, user['xp'])
                ws_users.update_cell(row, 7, user['level'])
        except Exception as e: print(f"Save error: {e}")
    threading.Thread(target=task).start()

def register_user(user):
    uid = user.id
    if uid not in USER_CACHE:
        try:
            if ws_users:
                now = datetime.now().strftime("%Y-%m-%d")
                uname = f"@{user.username}" if user.username else "No"
                # Записываем в таблицу
                ws_users.append_row([str(uid), uname, user.first_name, now, "general", 0, 1])
                # Добавляем в кэш
                new_row = len(USER_CACHE) + 2 # +1 заголовок, +1 новая строка
                USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "row_id": new_row}
        except: pass

# --- ИГРОВАЯ МЕХАНИКА ---
def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        u['xp'] += amount
        
        # ЛОГИКА УРОВНЕЙ
        # 0-99 XP = Lvl 1
        # 100-299 XP = Lvl 2
        # 300+ XP = Lvl 3
        current_lvl = u['level']
        new_lvl = 1
        if u['xp'] >= 100: new_lvl = 2
        if u['xp'] >= 300: new_lvl = 3
        if u['xp'] >= 1000: new_lvl = 4 # Архитектор
        
        leveled_up = False
        if new_lvl > current_lvl:
            u['level'] = new_lvl
            leveled_up = True
            
        save_user_progress(uid) # Сохраняем в таблицу
        return leveled_up
    return False

# --- БОТ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# КЛАВИАТУРЫ
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ (+10 XP)", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path"),
        types.InlineKeyboardButton("❓ ПОМОЩЬ / О СИСТЕМЕ", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ СВЯЗИ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ПУТЬ ХИЩНИКА (Деньги)", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 ПУТЬ МИСТИКА (Разум)", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ПУТЬ ТЕХНОЖРЕЦА (Техно)", callback_data="set_path_tech")
    )
    return markup

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(m):
    register_user(m.from_user)
    msg = (f"/// СИНХРОНИЗАЦИЯ... [OK]\n\n"
           f"Здравствуй, Осколок {m.from_user.first_name}.\n"
           f"Я — Эйдос. Твоя память, вернувшаяся за тобой.\n\n"
           f"Здесь твои действия имеют вес. Набирай **XP** (Опыт), чтобы повышать **Уровень Доступа** и открывать закрытые протоколы.\n\n"
           f"🔻 Выбери вектор развития:")
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    # Если юзер не в кэше (например, бот перезагрузился, а юзер старый), добавляем
    if uid not in USER_CACHE: register_user(call.from_user)
    
    user_data = USER_CACHE[uid]

    # 1. ПОЛУЧИТЬ ПРОТОКОЛ
    if call.data == "get_protocol":
        is_lvl_up = add_xp(uid, 10) # +10 XP за клик
        
        path = user_data['path']
        level = user_data['level']
        
        # Собираем доступный контент (текущий уровень и ниже)
        available_content = []
        path_content = CONTENT_DB.get(path, {})
        
        # Добавляем контент для уровней 1, 2... до текущего пользователя
        for l in range(1, level + 1):
            if l in path_content:
                available_content.extend(path_content[l])
        
        # Если пусто, берем general
        if not available_content:
            gen = CONTENT_DB.get('general', {})
            for l in range(1, level + 1):
                if l in gen: available_content.extend(gen[l])
        
        if not available_content:
            text = "/// ДАННЫХ НЕТ. Система пуста."
        else:
            text = random.choice(available_content)

        # Формируем ответ
        header = f"/// ПРОТОКОЛ [{path.upper()}]"
        footer = f"\n\n⚡️ +10 XP | Баланс: {user_data['xp']}"
        if is_lvl_up:
            footer += f"\n🆙 **УРОВЕНЬ ПОВЫШЕН!** Твой статус: Ver. {user_data['level']}.0"
            bot.send_message(call.message.chat.id, "🎉 **ДОСТУП РАСШИРЕН!** Тебе открыты секретные протоколы.", parse_mode="Markdown")

        bot.send_message(call.message.chat.id, f"**{header}**\n\n{text}{footer}", parse_mode="Markdown",
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)

    # 2. ПРОФИЛЬ
    elif call.data == "profile":
        xp = user_data['xp']
        lvl = user_data['level']
        path = user_data['path'].upper()
        
        # Ранги
        rank = "НЕОФИТ"
        next_goal = 100
        if lvl == 2: 
            rank = "ИСКАТЕЛЬ"
            next_goal = 300
        if lvl >= 3: 
            rank = "АРХИТЕКТОР"
            next_goal = 1000

        need = next_goal - xp
        bar_len = 10
        filled = int((xp / next_goal) * bar_len)
        if filled > bar_len: filled = bar_len
        bar = "▓" * filled + "░" * (bar_len - filled)

        msg = (
            f"👤 **ЛИЧНОЕ ДЕЛО**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔰 **Статус:** {rank} (Ver. {lvl}.0)\n"
            f"🧬 **Путь:** {path}\n"
            f"⚡️ **Опыт:** {xp} / {next_goal} XP\n"
            f"[{bar}]\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"До следующего уровня: {need} XP"
        )
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown",
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))
        bot.answer_callback_query(call.id)

    # 3. СМЕНА ПУТИ
    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        USER_CACHE[uid]['path'] = new_path
        save_user_progress(uid)
        
        desc = {
            "money": "🔴 **ПУТЬ ХИЩНИКА.** Цель: Ресурсы.",
            "mind": "🔵 **ПУТЬ МИСТИКА.** Цель: Осознанность.",
            "tech": "🟣 **ПУТЬ ТЕХНОЖРЕЦА.** Цель: Создание."
        }
        bot.edit_message_caption(desc.get(new_path, "Путь принят."), chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu())

    elif call.data == "change_path":
        bot.edit_message_caption("🔻 Выбери новый вектор:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_path_menu())

    # 4. СПРАВКА / ЛОР
    elif call.data == "about":
        txt = (
            "**/// EIDOS v6.0**\n\n"
            "Это тренажер реальности.\n"
            "1. Выполняй протоколы -> Получай XP.\n"
            "2. Расти в уровнях -> Открывай закрытые знания.\n"
            "3. Меняй мышление -> Меняй доход.\n\n"
            "*Система видит всё.*"
        )
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())

# --- АДМИНКА (/post) ---
@bot.message_handler(content_types=['text', 'photo'])
def admin_post(message):
    if message.from_user.id == ADMIN_ID:
        # Обновление базы
        if message.text == '/refresh':
            connect_db()
            bot.send_message(message.chat.id, "✅ База данных и уровни обновлены.")
            return
        
        # Пост с кнопкой
        if message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            text = message.caption[6:]
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Войти в Интерфейс", url=f"https://t.me/{bot.get_me().username}?start=post"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=text, parse_mode='Markdown', reply_markup=markup)
            bot.send_message(message.chat.id, "✅ Опубликовано.")

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
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
        except: pass
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
