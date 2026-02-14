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
USER_CACHE = {} # {uid: {path, xp, level, streak, last_active, row_id}}

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
            
            # 1. ЗАГРУЗКА КОНТЕНТА
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
            except Exception as e: print(f"/// CONTENT ERROR: {e}")

            # 2. ЗАГРУЗКА ЮЗЕРОВ
            try:
                ws_users = sh.worksheet("Users")
                all_v = ws_users.get_all_values()
                # A=ID, B=User, C=Name, D=Date, E=Path, F=XP, G=Lvl, H=Streak, I=LastActive
                for i, row in enumerate(all_v[1:], start=2):
                    if row and row[0]:
                        uid = int(row[0])
                        USER_CACHE[uid] = {
                            "path": row[4] if len(row) > 4 and row[4] else "general",
                            "xp": int(row[5]) if len(row) > 5 and row[5].isdigit() else 0,
                            "level": int(row[6]) if len(row) > 6 and row[6].isdigit() else 1,
                            "streak": int(row[7]) if len(row) > 7 and row[7].isdigit() else 0,
                            "last_active": row[8] if len(row) > 8 else "2000-01-01",
                            "row_id": i
                        }
                print(f"/// USERS: {len(USER_CACHE)} cached.")
            except Exception as e: print(f"/// USERS ERROR: {e}")
    except Exception as e: print(f"/// DB CRITICAL: {e}")

connect_db()

# --- ФУНКЦИИ ЯДРА ---
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
                # Обновляем E, F, G, H, I
                ws_users.update_cell(u['row_id'], 5, u['path'])
                ws_users.update_cell(u['row_id'], 6, str(u['xp']))
                ws_users.update_cell(u['row_id'], 7, str(u['level']))
                ws_users.update_cell(u['row_id'], 8, str(u['streak']))
                ws_users.update_cell(u['row_id'], 9, u['last_active'])
        except: pass
    threading.Thread(target=task).start()

def check_streak(uid):
    """Проверка ежедневной серии. Возвращает бонус XP."""
    u = USER_CACHE[uid]
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    bonus = 0
    msg = None

    if u['last_active'] == today:
        pass # Уже заходил сегодня
    elif u['last_active'] == yesterday:
        u['streak'] += 1
        bonus = u['streak'] * 5 # +5 XP за каждый день серии
        msg = f"🔥 **СЕРИЯ: {u['streak']} ДН.** (+{bonus} XP)"
    else:
        if u['streak'] > 0:
            msg = "❄️ **СЕРИЯ ПРЕРВАНА.** Начни сначала."
        u['streak'] = 1 # Первый день
        bonus = 5

    u['last_active'] = today
    return bonus, msg

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        # Проверяем стрик перед начислением
        streak_bonus, streak_msg = check_streak(uid)
        
        total_xp = amount + streak_bonus
        u['xp'] += total_xp
        
        # Уровни сложности (Геймификация)
        new_lvl = 1
        if u['xp'] >= 150: new_lvl = 2
        elif u['xp'] >= 500: new_lvl = 3
        elif u['xp'] >= 1500: new_lvl = 4
        
        up = new_lvl > u['level']
        u['level'] = new_lvl
        save_progress(uid)
        return up, streak_msg, total_xp
    return False, None, 0

# --- МЕНЮ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧬 ПОЛУЧИТЬ ПРОТОКОЛ", callback_data="get_protocol"),
        types.InlineKeyboardButton("👤 ПРОФИЛЬ / РЕЙТИНГ", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ СМЕНИТЬ ПУТЬ", callback_data="change_path"),
        types.InlineKeyboardButton("❓ О СИСТЕМЕ", callback_data="about"),
        types.InlineKeyboardButton("🔗 КАНАЛ", url="https://t.me/Eidos_Chronicles")
    )
    return markup

def get_path_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 ХИЩНИК [$$$]", callback_data="set_path_money"),
        types.InlineKeyboardButton("🔵 МИСТИК [Mind]", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🟣 ТЕХНОЖРЕЦ [AI]", callback_data="set_path_tech")
    )
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid not in USER_CACHE:
        now = datetime.now().strftime("%Y-%m-%d")
        uname = f"@{m.from_user.username}" if m.from_user.username else "No"
        if ws_users:
            ws_users.append_row([str(uid), uname, m.from_user.first_name, now, "general", "0", "1", "0", now])
            USER_CACHE[uid] = {"path": "general", "xp": 0, "level": 1, "streak": 1, "last_active": now, "row_id": len(USER_CACHE)+2}
    
    # Визуал заголовка
    header = "░▒▓█ 𝗘𝗜𝗗𝗢𝗦_𝗢𝗦 𝘃𝟳.𝟬 █▓▒░"
    msg = f"{header}\n\nЗдравствуй, Осколок {m.from_user.first_name}.\n\n⚠️ **ВНИМАНИЕ:** Система фиксирует твою активность. Не заходишь 24 часа — теряешь серию.\n\n🔻 Выбери свой вектор:"
    try: bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=msg, reply_markup=get_path_menu())
    except: bot.send_message(m.chat.id, msg, reply_markup=get_path_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE: return
    u = USER_CACHE[uid]

    if call.data == "get_protocol":
        up, streak_msg, earned = add_xp(uid, 10)
        
        # Подбор контента
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, u['level'] + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            g_cont = CONTENT_DB.get('general', {})
            for l in range(1, u['level'] + 1):
                if l in g_cont: pool.extend(g_cont[l])
        
        txt = random.choice(pool) if pool else "/// СИСТЕМА ПУСТА."
        
        # Эстетика вывода
        path_icon = {"money": "🔴", "mind": "🔵", "tech": "🟣", "general": "⚪️"}
        icon = path_icon.get(u['path'], "⚪️")
        
        res = f"{icon} **ПРОТОКОЛ [{u['path'].upper()}]**\n━━━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━━━"
        
        stats = f"⚡️ +{earned} XP"
        if streak_msg: stats += f" | {streak_msg}"
        stats += f"\n💰 Баланс: {u['xp']} XP"
        
        res += f"\n{stats}"
        if up: bot.send_message(call.message.chat.id, "🎉 **УРОВЕНЬ ПОВЫШЕН!**\nДоступ к закрытым файлам открыт.")
        
        bot.send_message(call.message.chat.id, res, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif call.data == "profile":
        rank = "НЕОФИТ"
        if u['level'] == 2: rank = "ИСКАТЕЛЬ"
        elif u['level'] == 3: rank = "ОПЕРАТОР"
        elif u['level'] == 4: rank = "АРХИТЕКТОР"
        
        # ASCII Прогресс бар
        next_goal = 150
        if u['level'] == 2: next_goal = 500
        if u['level'] >= 3: next_goal = 1500
        
        percent = min(1.0, u['xp'] / next_goal)
        bar_len = 10
        filled = int(percent * bar_len)
        bar = "▰" * filled + "▱" * (bar_len - filled)
        
        msg = (
            f"👤 **ЛИЧНОЕ ДЕЛО**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔰 **Ранг:** {rank} (Ver. {u['level']}.0)\n"
            f"🧬 **Путь:** {u['path'].upper()}\n"
            f"🔥 **Серия:** {u['streak']} дней\n"
            f"⚡️ **XP:** {u['xp']} / {next_goal}\n"
            f"[{bar}] {int(percent*100)}%\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🏆 **ТОП-3 ОСКОЛКА:**\n"
        )
        
        # Мини-рейтинг
        sorted_users = sorted(USER_CACHE.items(), key=lambda x: x[1]['xp'], reverse=True)[:3]
        for idx, (userid, data) in enumerate(sorted_users, 1):
            medal = ["🥇", "🥈", "🥉"][idx-1]
            me_mark = " (Вы)" if userid == uid else ""
            msg += f"{medal} ID {str(userid)[-4:]}... — {data['xp']} XP{me_mark}\n"

        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Меню", callback_data="back_to_menu")))

    elif "set_path_" in call.data:
        u['path'] = call.data.split("_")[-1]
        save_progress(uid)
        safe_edit(call, f"/// ВЕКТОР {u['path'].upper()} ЗАГРУЖЕН.", get_main_menu())

    elif call.data == "change_path":
        safe_edit(call, "🔻 Смена вектора развития:", get_path_menu())

    elif call.data == "about":
        safe_edit(call, "**/// SYSTEM INFO**\nЭйдос — это игра с реальностью. Мы превращаем хаос жизни в структуру.", get_main_menu())

    elif call.data == "back_to_menu":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "/// МЕНЮ АКТИВНО", reply_markup=get_main_menu())
        
    elif call.data == "get_signal":
        pool = []
        for p in CONTENT_DB:
            if 1 in CONTENT_DB[p]: pool.extend(CONTENT_DB[p][1])
        txt = random.choice(pool) if pool else "/// СИГНАЛ ПОТЕРЯН."
        bot.answer_callback_query(call.id, show_alert=True, text=txt)
    
    try: bot.answer_callback_query(call.id)
    except: pass

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh':
            connect_db()
            bot.send_message(message.chat.id, "✅ Система перезагружена.")
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
