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
from datetime import datetime, timedelta

# --- 1. КОНФИГУРАЦИЯ ---
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
CHANNEL_ID = "@Eidos_Chronicles"
ADMIN_ID = 5178416366
MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"

SHEET_NAME = os.environ.get('SHEET_NAME', 'Eidos_Users')
GOOGLE_JSON = os.environ.get('GOOGLE_KEY')

# --- БАЛАНС СИСТЕМЫ ---
COOLDOWN_SECONDS = 3600  # 1 час между протоколами (чтобы не фармили)
PATH_CHANGE_COST = 50    # Цена смены пути

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# --- 3. СИСТЕМНАЯ ПАМЯТЬ ---
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}}
USER_CACHE = {} 

# --- 4. БАЗА ЗНАНИЙ (ТЕКСТЫ) ---
GUIDE_TEXT = (
    "**/// РУКОВОДСТВО ПО ЭКСПЛУАТАЦИИ**\n\n"
    "**1. ЗАЧЕМ ТЕБЕ ЭЙДОС?**\n"
    "Твой мозг работает на устаревшем софте (страхи, лень, шаблоны). Эйдос — это обновление прошивки.\n"
    "Мы даем **Протоколы** — алгоритмы, которые меняют твою эффективность.\n\n"
    "**2. МЕХАНИКА ВЫЖИВАНИЯ:**\n"
    "⚡️ **Энергия (XP):** Валюта влияния. Дается за Протоколы (+10) и Стрик.\n"
    "🔥 **Стрик (Серия):** Заходи раз в 24 часа. Пропустил день — серия сгорела. Дисциплина — основа власти.\n"
    "⏳ **Таймер:** Система не дает знания просто так. Между протоколами — пауза 1 час.\n\n"
    "**3. КЛАССЫ (ПУТИ):**\n\n"
    "🔴 **ХИЩНИК [Материя]**\n"
    "• *Для кого:* Предприниматели, сейлзы.\n"
    "• *Фокус:* Деньги, переговоры, доминирование.\n"
    "• *Цель:* Построение Империи.\n\n"
    "🔵 **МИСТИК [Разум]**\n"
    "• *Для кого:* Лидеры, психологи, серые кардиналы.\n"
    "• *Фокус:* Влияние, НЛП, чтение людей.\n"
    "• *Цель:* Власть над умами.\n\n"
    "🟣 **ТЕХНОЖРЕЦ [AI]**\n"
    "• *Для кого:* Системные архитекторы, криэйторы.\n"
    "• *Фокус:* Автоматизация, ИИ, удаление рутины.\n"
    "• *Цель:* Цифровое бессмертие.\n\n"
    "⚠️ **Смена Пути стоит 50 XP.** Выбирай мудро."
)

LEVEL_UP_MSG = {
    2: "🔓 **ДОСТУП РАСШИРЕН (LVL 2)**\nТебе открыты Инструменты Влияния. Теперь ты видишь не только *что* делать, но и *как*.",
    3: "🔓 **СИСТЕМНЫЙ ДОСТУП (LVL 3)**\nТы стал Оператором. Доступны стратегии масштабирования и управления хаосом.",
    4: "👑 **ВЫСШИЙ ДОСТУП (LVL 4)**\nТы — Архитектор. Метафизика власти и создание наследия. Добро пожаловать в элиту."
}

# --- 5. БАЗА ДАННЫХ ---
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
                print(f"/// CONTENT: {len(records)} loaded.")
            except: pass

            try:
                ws_users = sh.worksheet("Users")
                all_v = ws_users.get_all_values()
                for i, row in enumerate(all_v[1:], start=2):
                    if row and row[0] and str(row[0]).isdigit():
                        uid = int(row[0])
                        USER_CACHE[uid] = {
                            "path": row[4] if len(row) > 4 and row[4] else "general",
                            "xp": int(row[5]) if len(row) > 5 and str(row[5]).isdigit() else 0,
                            "level": int(row[6]) if len(row) > 6 and str(row[6]).isdigit() else 1,
                            "streak": int(row[7]) if len(row) > 7 and str(row[7]).isdigit() else 0,
                            "last_active": row[8] if len(row) > 8 else "2000-01-01",
                            "prestige": int(row[9]) if len(row) > 9 and str(row[9]).isdigit() else 0,
                            "last_protocol_time": 0,
                            "row_id": i
                        }
                print(f"/// USERS: {len(USER_CACHE)} cached.")
            except: pass
    except: pass

connect_db()

# --- 6. ЯДРО ---
def safe_edit(call, text, markup):
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
                ws_users.update_cell(u['row_id'], 8, str(u['streak']))
                ws_users.update_cell(u['row_id'], 9, u['last_active'])
                ws_users.update_cell(u['row_id'], 10, str(u.get('prestige', 0)))
        except: pass
    threading.Thread(target=task).start()

def update_activity(uid):
    if uid in USER_CACHE:
        USER_CACHE[uid]['last_active'] = datetime.now().strftime("%Y-%m-%d")

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        bonus = 0; streak_msg = None
        if u['last_active'] == yesterday:
            u['streak'] += 1; bonus = u['streak'] * 5
            streak_msg = f"🔥 **СЕРИЯ: {u['streak']} ДН.** (+{bonus} XP)"
        elif u['last_active'] != today:
            if u['streak'] > 1: streak_msg = "❄️ **СЕРИЯ ПРЕРВАНА.**"
            u['streak'] = 1; bonus = 5
        
        u['last_active'] = today
        total_xp = amount + bonus
        u['xp'] += total_xp
        
        old_lvl = u['level']
        if u['xp'] >= 1500: u['level'] = 4
        elif u['xp'] >= 500: u['level'] = 3
        elif u['xp'] >= 150: u['level'] = 2
        
        lvl_msg = None
        if u['level'] > old_lvl:
            lvl_msg = LEVEL_UP_MSG.get(u['level'], "🎉 **УРОВЕНЬ ПОВЫШЕН!**")
            
        save_progress(uid)
        return lvl_msg, streak_msg, total_xp
    return None, None, 0

def do_prestige(uid):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        if u['level'] >= 4:
            u['xp'] = 0; u['level'] = 1
            u['prestige'] = u.get('prestige', 0) + 1
            save_progress(uid)
            return True
    return False

# --- 7. МЕНЮ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 ПРОФИЛЬ / РЕЙТИНГ", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ (-50 XP)", callback_data="change_path"),
        types.InlineKeyboardButton("📚 ГАЙД / КЛАССЫ", callback_data="guide")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ХИЩНИК [Материя]", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 МИСТИК [Разум]", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ТЕХНОЖРЕЦ [AI]", callback_data="set_path_tech")
    )
    return markup

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid not in USER_CACHE:
        now = datetime.now().strftime("%Y-%m-%d")
        uname = f"@{m.from_user.username}" if m.from_user.username else "No"
        if ws_users:
            ws_users.append_row([str(uid), uname, m.from_user.first_name, now, "general", "0", "1", "1", now, "0"])
            USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "streak": 1, "last_active": now, "prestige": 0, "last_protocol_time": 0, "row_id": len(USER_CACHE)+2}
    else:
        update_activity(uid); save_progress(uid)

    header = "░▒▓█ 𝗘𝗜𝗗𝗢𝗦_𝗢𝗦 𝘃𝟴.𝟯 █▓▒░"
    msg = f"{header}\n\nОсколок {m.from_user.first_name}, синхронизация завершена.\n\n⚠️ **ЭНЕРГИЯ:** Каждое действие имеет цену. Учись управлять ресурсом.\n\n🔻 Выбери вектор:"
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]
    
    if call.data != "get_protocol": 
        update_activity(uid)
        save_progress(uid)

    if call.data == "get_protocol":
        now_ts = time.time()
        last_ts = u.get('last_protocol_time', 0)
        
        # Кулдаун (анти-фарм)
        if now_ts - last_ts < COOLDOWN_SECONDS:
            remain = int((COOLDOWN_SECONDS - (now_ts - last_ts)) / 60)
            bot.answer_callback_query(call.id, f"⚠️ ПЕРЕГРЕВ. Система остывает. Жди {remain} мин.", show_alert=True)
            return

        lvl_msg, streak_msg, earned = add_xp(uid, 10)
        u['last_protocol_time'] = now_ts
        
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, u['level'] + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            g_cont = CONTENT_DB.get('general', {})
            for l in range(1, u['level'] + 1):
                if l in g_cont: pool.extend(g_cont[l])
        
        txt = random.choice(pool) if pool else "/// ПУСТОТА."
        res = f"**// ПРОТОКОЛ [{u['path'].upper()}]**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{earned} XP"
        if streak_msg: res += f" | {streak_msg}"
        
        if lvl_msg: bot.send_message(call.message.chat.id, lvl_msg, parse_mode="Markdown")
        bot.send_message(call.message.chat.id, res, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "profile":
        rank = ["НЕОФИТ", "ИСКАТЕЛЬ", "ОПЕРАТОР", "АРХИТЕКТОР"][min(u['level']-1, 3)]
        next_g = [150, 500, 1500, 5000][min(u['level']-1, 3)]
        perc = min(1.0, u['xp'] / next_g)
        bar = "▰" * int(perc * 10) + "▱" * (10 - int(perc * 10))
        stars = "★" * u.get('prestige', 0)
        
        msg = f"👤 **ПРОФИЛЬ** {stars}\n━━━━━━━━━━━━━━\n🔰 Ранг: {rank}\n🔥 Серия: {u['streak']} дн.\n⚡️ XP: {u['xp']} / {next_g}\n[{bar}] {int(perc*100)}%\n\n"
        markup = types.InlineKeyboardMarkup()
        if u['level'] >= 4:
            msg += "\n🌀 **ДОСТУПНО ВОЗНЕСЕНИЕ**\n"
            markup.add(types.InlineKeyboardButton("🌀 ВОЗНЕСТИСЬ", callback_data="do_prestige"))
        
        sorted_top = sorted(USER_CACHE.items(), key=lambda x: x[1]['xp'] + (x[1].get('prestige',0)*10000), reverse=True)[:3]
        top_str = "\n".join([f"{['🥇','🥈','🥉'][i]} ID {str(k)[-4:]}: {v['xp']} XP" + ("★" * v.get('prestige',0)) for i, (k, v) in enumerate(sorted_top)])
        msg += f"🏆 **ТОП-3:**\n{top_str}"
        markup.add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu"))
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "do_prestige":
        if do_prestige(uid):
            bot.send_message(call.message.chat.id, "🌀 **ВОЗНЕСЕНИЕ ЗАВЕРШЕНО.**", reply_markup=get_main_menu())
        else: bot.answer_callback_query(call.id, "❌ Рано.")

    elif "set_path_" in call.data:
        new_path = call.data.split("_")[-1]
        if u['xp'] >= PATH_CHANGE_COST:
            u['xp'] -= PATH_CHANGE_COST
            u['path'] = new_path
            save_progress(uid)
            safe_edit(call, f"/// ВЕКТОР {new_path.upper()} АКТИВИРОВАН.\n💸 Списано: {PATH_CHANGE_COST} XP", get_main_menu())
        else:
            bot.answer_callback_query(call.id, f"❌ НУЖНО {PATH_CHANGE_COST} XP.", show_alert=True)

    elif call.data == "change_path":
        safe_edit(call, f"🔻 Смена вектора (Цена: {PATH_CHANGE_COST} XP):", get_path_menu())

    elif call.data == "guide":
        safe_edit(call, GUIDE_TEXT, get_main_menu())

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        try: bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ИНТЕРФЕЙС АКТИВЕН", reply_markup=get_main_menu())
        except: bot.send_message(call.message.chat.id, "/// ИНТЕРФЕЙС АКТИВЕН", reply_markup=get_main_menu())

    elif call.data == "get_signal":
        pool = []
        for p in CONTENT_DB:
            if 1 in CONTENT_DB[p]: pool.extend(CONTENT_DB[p][1])
        txt = random.choice(pool) if pool else "..."; bot.answer_callback_query(call.id, show_alert=True, text=txt)
    
    try: bot.answer_callback_query(call.id)
    except: pass

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db(); bot.send_message(message.chat.id, "✅ OK")
        elif message.content_type == 'photo' and message.caption and message.caption.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 Сигнал", callback_data="get_signal"))
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=message.caption[6:], reply_markup=markup)

# --- 8. ЗАПУСК ---
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
        bot.remove_webhook(); time.sleep(1); bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
