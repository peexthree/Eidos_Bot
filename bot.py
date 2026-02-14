import telebot
from telebot import types
import flask
import os
import time
import random
import gspread
import json
import threading
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

# --- ЭКОНОМИКА ---
COOLDOWN_BASE = 1800     # 30 мин (Синхрон)
COOLDOWN_ACCEL = 900     # 15 мин (Ускоритель)
COOLDOWN_SIGNAL = 300    # 5 мин (Сигнал)
XP_GAIN = 25             # Синхрон
XP_SIGNAL = 15           # Сигнал
PATH_CHANGE_COST = 100
REFERRAL_BONUS = 250
PRICES = {"cryo": 200, "accel": 500, "decoder": 800}

# --- ПОРОГИ УРОВНЕЙ ---
LEVELS = {1: 100, 2: 500, 3: 1500, 4: 3000}
TITLES = {1: "НЕОФИТ", 2: "ИСКАТЕЛЬ", 3: "ОПЕРАТОР", 4: "АРХИТЕКТОР"}

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
# Добавили хранилище для сигналов
CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
USER_CACHE = {} 

# --- 3. ТЕКСТОВЫЕ МОДУЛИ ---
SCHOOLS = {"money": "🏦 ШКОЛА МАТЕРИИ", "mind": "🧠 ШКОЛА РАЗУМА", "tech": "🤖 ШКОЛА СИНГУЛЯРНОСТИ"}

GUIDE_FULL = (
    "**📚 ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ EIDOS v20.1**\n\n"
    "**1. ИСТОЧНИКИ ДАННЫХ:**\n"
    "• 👁 **СИНХРОН (30 мин):** Глубокие протоколы. Награда: **25 XP**.\n"
    "• 📶 **СИГНАЛ (5 мин):** Короткие ментальные импульсы. Награда: **15 XP**.\n\n"
    "**2. СИСТЕМА STREAK (СЕРИЯ):**\n"
    "Каждый день непрерывного входа увеличивает награду за Синхрон на **+5 XP**.\n"
    "Пропуск дня сжигает серию (если нет Крио-капсулы).\n\n"
    "**3. УРОВНИ ДОСТУПА:**\n"
    "• **LVL 1 (100 XP):** База.\n"
    "• **LVL 2 (500 XP):** Фракции.\n"
    "• **LVL 3 (1500 XP):** Инсайды.\n"
    "• **LVL 4 (3000 XP):** Архитектор."
)

SHOP_FULL = (
    "**🎰 ЧЕРНЫЙ РЫНОК**\n\n"
    f"❄️ **КРИО ({PRICES['cryo']} XP)**\nСтраховка серии при пропуске дня.\n\n"
    f"⚡️ **УСКОРИТЕЛЬ ({PRICES['accel']} XP)**\nСнижает ожидание Синхрона до 15 мин на 24 часа.\n*(Требует активации в Профиле после покупки)*\n\n"
    f"🔑 **ДЕШИФРАТОР ({PRICES['decoder']} XP)**\nВзлом уровня доступа.Даёт знания уровнем выше\n\n"
    f"⚙️ **СМЕНА ФРАКЦИИ ({PATH_CHANGE_COST} XP)**"
)

SYNDICATE_FULL = (
    "**🔗 СИНДИКАТ**\n\n"
    f"1. 🎁 **БОНУС:** +{REFERRAL_BONUS} XP за реферала.Приведи друга и раскачайся\n"
    "2. 📈 **РОЯЛТИ:** 10% от опыта твоей сети пожизненно."
)

LEVEL_UP_MSG = {
    2: "🔓 **LVL 2**: Доступ к секретам 2 уровня открыт.",
    3: "🔓 **LVL 3**: Статус Оператора.Знания синхрона будут богаче",
    4: "👑 **LVL 4**: Ты — Архитектор.Уровень знаний будет высоким"
}

# --- 4. БАЗА ДАННЫХ ---
def connect_db():
    global gc, sh, ws_users, ws_content, CONTENT_DB, USER_CACHE
    try:
        if GOOGLE_JSON:
            creds = json.loads(GOOGLE_JSON)
            if 'private_key' in creds: creds['private_key'] = creds['private_key'].replace('\\n', '\n')
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open(SHEET_NAME)
            ws_content = sh.worksheet("Content")
            records = ws_content.get_all_records()
            CONTENT_DB = {"money": {}, "mind": {}, "tech": {}, "general": {}, "signals": []}
            for r in records:
                # Читаем по колонкам: Type, Path, Text, Level
                r_type = str(r.get('Type', '')).lower().strip()
                path = str(r.get('Path', 'general')).lower().strip()
                text = r.get('Text', '')
                try: lvl = int(r.get('Level', 1))
                except: lvl = 1
                
                if text:
                    if r_type == 'signal': # Логика Сигнала
                        CONTENT_DB["signals"].append(text)
                    else: # Логика Синхрона
                        if path not in CONTENT_DB: path = "general"
                        if lvl not in CONTENT_DB[path]: CONTENT_DB[path][lvl] = []
                        CONTENT_DB[path][lvl].append(text)
            
            ws_users = sh.worksheet("Users")
            all_v = ws_users.get_all_values()
            USER_CACHE.clear()
            for i, row in enumerate(all_v[1:], start=2):
                if row and row[0] and str(row[0]).isdigit():
                    uid = int(row[0])
                    def s_int(val, d=0): return int(str(val).strip()) if str(val).strip().isdigit() else d
                    USER_CACHE[uid] = {
                        "path": row[4] if len(row) > 4 and row[4] else "general",
                        "xp": s_int(row[5]), "level": s_int(row[6], 1), "streak": s_int(row[7]),
                        "last_active": row[8] if len(row) > 8 and row[8] else "2000-01-01",
                        "prestige": s_int(row[9]), "cryo": s_int(row[10]), "accel": s_int(row[11]),
                        "decoder": s_int(row[12]),
                        "accel_exp": float(row[13]) if len(row) > 13 and str(row[13]).replace('.','').isdigit() else 0,
                        "referrer": row[14] if len(row) > 14 else None,
                        "last_protocol_time": 0,
                        "last_signal_time": 0, # Новое поле для КД сигнала
                        "notified": True, "row_id": i
                    }
            print("/// DB CONNECTED")
    except Exception as e: print(f"/// DB ERROR: {e}")

connect_db()

# --- 5. ФУНКЦИИ ЯДРА ---
def safe_edit(call, text, markup):
    try:
        if call.message.content_type == 'photo':
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except: 
        try: bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except: pass

def save_progress(uid):
    def task():
        try:
            u = USER_CACHE.get(uid)
            if u and ws_users:
                data = [u['path'], str(u['xp']), str(u['level']), str(u['streak']), u['last_active'], str(u['prestige']),
                        str(u['cryo']), str(u['accel']), str(u['decoder']), str(u['accel_exp']), str(u.get('referrer', ''))]
                ws_users.update(f"E{u['row_id']}:O{u['row_id']}", [data])
        except: pass
    threading.Thread(target=task).start()

def async_register_user(uid, username, first_name, ref_arg):
    try:
        if ws_users:
            start_xp = "50" if ref_arg == 'inst' else "0"
            ws_users.append_row([str(uid), f"@{username}", first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                 "general", start_xp, "1", "1", datetime.now().strftime("%Y-%m-%d"), 
                                 "0", "0", "0", "0", "0", str(ref_arg or '')])
    except: pass

def add_xp(uid, amount):
    if uid in USER_CACHE:
        u = USER_CACHE[uid]
        today, yesterday = datetime.now().strftime("%Y-%m-%d"), (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        bonus, s_msg = 0, None
        
        # СТРИК работает только раз в сутки (привяжем его к обновлению активности)
        streak_bonus = 0
        if u['last_active'] == yesterday:
            u['streak'] += 1; streak_bonus = u['streak'] * 5; s_msg = f"🔥 СЕРИЯ: {u['streak']} ДН."
        elif u['last_active'] != today:
            if u.get('cryo', 0) > 0: u['cryo'] -= 1; s_msg = "❄️ КРИО-СПАСЕНИЕ!"
            else: u['streak'] = 1; streak_bonus = 5; s_msg = "❄️ СЕРИЯ СБРОШЕНА."
        
        u['last_active'] = today
        # Бонус за стрик даем только если это Синхрон (не сигнал), но для простоты добавим ко всему, если день сменился
        total = amount + streak_bonus 
        u['xp'] += total
        
        if u.get('referrer') and str(u['referrer']).isdigit() and int(u['referrer']) in USER_CACHE:
            r = USER_CACHE[int(u['referrer'])]
            r['xp'] += max(1, int(total * 0.1)); save_progress(int(u['referrer']))
            
        old_lvl = u['level']
        for lvl, threshold in sorted(LEVELS.items(), reverse=True):
            if u['xp'] >= threshold:
                u['level'] = lvl
                break
        save_progress(uid)
        return (u['level'] > old_lvl), s_msg, total
    return False, None, 0

def decrypt_and_send(chat_id, uid, target_lvl, use_dec_text):
    u = USER_CACHE[uid]
    try:
        status_msg = bot.send_message(chat_id, "📡 **ИНИЦИАЛИЗАЦИЯ...**")
        time.sleep(1)
        bot.edit_message_text(f"🔓 **ДЕШИФРОВКА...**\n`[||||||||..] 84%`", chat_id, status_msg.message_id, parse_mode="Markdown")
        time.sleep(0.8)
        pool = []
        p_cont = CONTENT_DB.get(u['path'], {})
        for l in range(1, target_lvl + 1):
            if l in p_cont: pool.extend(p_cont[l])
        if not pool:
            for l in range(1, target_lvl + 1):
                if l in CONTENT_DB.get('general', {}): pool.extend(CONTENT_DB['general'][l])
        txt = random.choice(pool) if pool else "/// НЕТ ДАННЫХ."
        school = SCHOOLS.get(u['path'], "🌐 ОБЩИЙ КАНАЛ")
        res = f"🧬 **{school}**\n━━━━━━━━━━━━━━\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_GAIN} SYNC {use_dec_text}"
        bot.edit_message_text(res, chat_id, status_msg.message_id, parse_mode="Markdown", 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except: pass

# --- 6. ПУШИ ---
def notification_worker():
    while True:
        try:
            time.sleep(60)
            now = time.time()
            for uid, u in list(USER_CACHE.items()):
                cd = COOLDOWN_ACCEL if u.get('accel_exp', 0) > now else COOLDOWN_BASE
                if u.get('last_protocol_time', 0) > 0 and (now - u['last_protocol_time'] >= cd) and not u.get('notified', True):
                    try:
                        bot.send_message(uid, "⚡️ **СИСТЕМА ГОТОВА.**\nПротокол восстановлен.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        u['notified'] = True
                    except: pass
        except: pass

def get_progress_bar(current_xp, level):
    next_level_xp = LEVELS.get(level + 1, 10000)
    prev_level_xp = LEVELS.get(level, 0)
    if level >= 4: return "`[||||||||||] MAX`"
    needed = next_level_xp - prev_level_xp
    current = current_xp - prev_level_xp
    percent = min(100, max(0, int((current / needed) * 100)))
    blocks = int(percent / 10)
    bar = "||" * blocks + ".." * (10 - blocks)
    return f"`[{bar}] {percent}%`"

# --- 7. ИНТЕРФЕЙС ---
def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # КНОПКИ СИНХРОН И СИГНАЛ В ОДИН РЯД
    markup.add(
        types.InlineKeyboardButton("👁 ДЕШИФРОВАТЬ СИНХРОН", callback_data="get_protocol"),
        types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", callback_data="get_signal")
    )
    markup.add(
        types.InlineKeyboardButton("👤 НЕЙРО-ПРОФИЛЬ", callback_data="profile"),
        types.InlineKeyboardButton("🎰 ЧЕРНЫЙ РЫНОК", callback_data="shop")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"),
        types.InlineKeyboardButton("📚 РУКОВОДСТВО", callback_data="guide")
    )
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel"))
    return markup

def get_admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 ОБНОВИТЬ БД", callback_data="admin_refresh"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"),
        types.InlineKeyboardButton("🎁 НАЧИСЛИТЬ ВСЕМ БОНУС", callback_data="admin_bonus"),
        types.InlineKeyboardButton("💀 УДАЛИТЬ ПО ID", callback_data="admin_ban"),
        types.InlineKeyboardButton("🔙 В МЕНЮ", callback_data="back_to_menu")
    )
    return markup

def get_path_menu(cost_info=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_text = f" (-{PATH_CHANGE_COST} XP)" if cost_info else ""
    markup.add(
        types.InlineKeyboardButton(f"🔴 ХИЩНИК [Материя]{btn_text}", callback_data="set_path_money"),
        types.InlineKeyboardButton(f"🔵 МИСТИК [Разум]{btn_text}", callback_data="set_path_mind"),
        types.InlineKeyboardButton(f"🟣 ТЕХНОЖРЕЦ [AI]{btn_text}", callback_data="set_path_tech"),
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")
    )
    return markup

# --- 8. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    uid = m.from_user.id
    ref_arg = m.text.split()[1] if len(m.text.split()) > 1 else None

    # --- ЛОГИКА ДЛЯ СИГНАЛА ИЗ КАНАЛА ---
    # Если юзер перешел по ?start=signal, мы просто регистрируем его (если новый)
    # А само действие "получить сигнал" он нажмет в меню или мы можем принудительно вызвать, но лучше просто открыть меню.

    if uid not in USER_CACHE:
        start_xp = 50 if ref_arg == 'inst' else 0
        USER_CACHE[uid] = {
            "path": "general", "xp": start_xp, "level": 1, "streak": 1, "last_active": datetime.now().strftime("%Y-%m-%d"),
            "prestige": 0, "cryo": 0, "accel": 0, "decoder": 0, "accel_exp": 0, "referrer": ref_arg,
            "last_protocol_time": 0, "last_signal_time": 0, "notified": True, "row_id": len(USER_CACHE) + 2
        }
        threading.Thread(target=async_register_user, args=(uid, m.from_user.username, m.from_user.first_name, ref_arg)).start()
        
        if ref_arg and ref_arg.isdigit() and int(ref_arg) in USER_CACHE:
            USER_CACHE[int(ref_arg)]['xp'] += REFERRAL_BONUS; save_progress(int(ref_arg))
            try: bot.send_message(int(ref_arg), f"🎁 **НОВЫЙ УЗЕЛ.** +{REFERRAL_BONUS} XP.")
            except: pass

    welcome_msg = "/// EIDOS-OS: СИНХРОНИЗИРОВАН."
    if ref_arg == 'inst': welcome_msg = "🧬 **СИГНАЛ ИЗ INSTAGRAM.**\nБонус +50 XP начислен."
    
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_msg, reply_markup=get_main_menu(uid))

@bot.message_handler(content_types=['text', 'photo'])
def admin_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == '/refresh': connect_db(); bot.send_message(message.chat.id, "✅ БД ОБНОВЛЕНА.")
        
        # ОБНОВЛЕННЫЙ TELEGRAPH С КНОПКОЙ СИГНАЛА
        elif message.text and message.text.startswith('/telegraph '):
            parts = message.text.split(maxsplit=2)
            if len(parts) >= 2:
                url, text = parts[1], parts[2] if len(parts) > 2 else "/// АРХИВ ДЕШИФРОВАН"
                clean_url = url.split("google.com/search?q=")[-1] if "google.com" in url else url
                markup = types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("📂 ОТКРЫТЬ ДОСЬЕ", url=clean_url),
                    types.InlineKeyboardButton("📶 ПОЛУЧИТЬ СИГНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=signal")
                )
                bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/post '):
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 ВОЙТИ В ТЕРМИНАЛ", url=f"https://t.me/{BOT_USERNAME}?start=channel"))
            bot.send_message(CHANNEL_ID, message.text[6:], reply_markup=markup, parse_mode="Markdown")
        
        elif message.text and message.text.startswith('/ban '): 
            try:
                target_id = int(message.text.split()[1])
                if target_id in USER_CACHE: del USER_CACHE[target_id]; bot.send_message(message.chat.id, f"🚫 УЗЕЛ {target_id} ОТКЛЮЧЕН.")
            except: bot.send_message(message.chat.id, "❌ Ошибка ID.")
        
        elif message.text and message.text.startswith('/give_xp '):
            try:
                _, t_id, amount = message.text.split()
                t_id, amount = int(t_id), int(amount)
                if t_id in USER_CACHE:
                    USER_CACHE[t_id]['xp'] += amount; save_progress(t_id)
                    bot.send_message(t_id, f"⚡️ **ВМЕШАТЕЛЬСТВО АРХИТЕКТОРА:** Начислено {amount} XP.")
                    bot.send_message(message.chat.id, "✅ Начислено.")
            except: bot.send_message(message.chat.id, "❌ Формат: /give_xp ID СУММА")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = call.from_user.id
    if uid not in USER_CACHE:
        bot.answer_callback_query(call.id, "⚠️ Нажми /start", show_alert=True); return
    u = USER_CACHE[uid]
    now_ts = time.time()

    try:
        if call.data == "admin_panel" and uid == ADMIN_ID: 
            safe_edit(call, "⚙️ **ЦЕНТР УПРАВЛЕНИЯ АРХИТЕКТОРА**\n\n`/ban ID`\n`/give_xp ID СУММА`\n`/telegraph ССЫЛКА ТЕКСТ`", get_admin_menu())
        
        elif call.data == "admin_bonus" and uid == ADMIN_ID:
            count = 0
            for u_id in USER_CACHE: USER_CACHE[u_id]['xp'] += 100; save_progress(u_id); count += 1
            bot.answer_callback_query(call.id, f"🎁 Выдано по 100 XP {count} узлам")

        elif call.data == "admin_refresh" and uid == ADMIN_ID: connect_db(); bot.answer_callback_query(call.id, "✅ OK")
        elif call.data == "admin_stats" and uid == ADMIN_ID:
            inst_users = sum(1 for user in USER_CACHE.values() if user.get('referrer') == 'inst')
            bot.answer_callback_query(call.id, f"📊 Узлы: {len(USER_CACHE)}\n📸 Instagram: {inst_users}", show_alert=True)

        elif call.data == "get_protocol":
            # --- ЛОГИКА УСКОРИТЕЛЯ ---
            is_accel_active = u.get('accel_exp', 0) > now_ts
            cd = COOLDOWN_ACCEL if is_accel_active else COOLDOWN_BASE
            
            if now_ts - u.get('last_protocol_time', 0) < cd:
                rem = int((cd - (now_ts - u.get('last_protocol_time', 0))) / 60)
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem} мин.", show_alert=True); return
            u['last_protocol_time'] = now_ts
            up, s_msg, total = add_xp(uid, XP_GAIN)
            target_lvl = u['level'] + 1 if u['decoder'] > 0 else u['level']
            if u['decoder'] > 0: u['decoder'] -= 1
            if up: bot.send_message(uid, LEVEL_UP_MSG.get(u['level'], "🎉 ВЫШЕ УРОВЕНЬ!"))
            threading.Thread(target=decrypt_and_send, args=(uid, uid, target_lvl, "")).start()

        # --- ЛОГИКА СИГНАЛА ---
        elif call.data == "get_signal":
            if now_ts - u.get('last_signal_time', 0) < COOLDOWN_SIGNAL:
                rem = int((COOLDOWN_SIGNAL - (now_ts - u.get('last_signal_time', 0))) / 60)
                bot.answer_callback_query(call.id, f"📡 СИГНАЛ НЕ ГОТОВ. Жди {rem} мин.", show_alert=True); return
            
            u['last_signal_time'] = now_ts
            up, s_msg, total = add_xp(uid, XP_SIGNAL)
            
            # Выбор случайного сигнала
            txt = random.choice(CONTENT_DB["signals"]) if CONTENT_DB["signals"] else "/// ЭФИР ПУСТ. ЖДИ ОБНОВЛЕНИЯ БАЗЫ."
            
            bot.send_message(uid, f"📶 **ПОЛУЧЕН СИГНАЛ**\n\n{txt}\n\n━━━━━━━━━━━━━━\n⚡️ +{XP_SIGNAL} XP", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))

        elif call.data == "profile":
            title = TITLES.get(u['level'], "НЕОФИТ")
            progress = get_progress_bar(u['xp'], u['level'])
            ref_count = sum(1 for user in USER_CACHE.values() if str(user.get('referrer')) == str(uid))
            
            # Отображение статуса ускорителя в профиле
            accel_status = "✅ АКТИВЕН" if u.get('accel_exp', 0) > now_ts else "❌ НЕ АКТИВЕН"
            
            msg = (f"👤 **НЕЙРО-ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n"
                   f"🔰 **СТАТУС:** {title}\n"
                   f"⚔️ **ФРАКЦИЯ:** {SCHOOLS.get(u['path'], 'ОБЩИЙ ПОТОК')}\n"
                   f"🔋 **SYNC:** {u['xp']} XP\n{progress}\n"
                   f"🔥 **STREAK:** {u['streak']} дн. (Бонус: +{u['streak']*5} XP)\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🎒 **ИНВЕНТАРЬ:**\n❄️ Крио: {u['cryo']}\n⚡️ Ускоритель: {accel_status}\n🔑 Дешифратор: {u['decoder']}")
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            # Кнопка активации ускорителя (если он есть, но не активен)
            if u['accel'] > 0 and u.get('accel_exp', 0) < now_ts:
                markup.add(types.InlineKeyboardButton("🚀 АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accel"))
            markup.add(types.InlineKeyboardButton("⚙️ СМЕНИТЬ ВЕКТОР", callback_data="change_path_confirm"))
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu"))
            safe_edit(call, msg, markup)

        elif call.data == "back_to_menu":
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА.", reply_markup=get_main_menu(uid))

        elif call.data == "shop":
            safe_edit(call, SHOP_FULL, types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton("❄️ КУПИТЬ КРИО (200 XP)", callback_data="buy_cryo"),
                types.InlineKeyboardButton("⚡️ КУПИТЬ УСКОРИТЕЛЬ (500 XP)", callback_data="buy_accel"),
                types.InlineKeyboardButton("🔑 КУПИТЬ ДЕШИФРАТОР (800 XP)", callback_data="buy_decoder"),
                types.InlineKeyboardButton("⚙️ СМЕНИТЬ ФРАКЦИЮ (100 XP)", callback_data="change_path_confirm"),
                types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back_to_menu")))

        elif call.data.startswith("buy_"):
            item = call.data.split("_")[1]
            if u['xp'] >= PRICES[item]:
                u['xp'] -= PRICES[item]; u[item] += 1; save_progress(uid)
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item.upper()}"); safe_edit(call, SHOP_FULL, get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО SYNC", show_alert=True)

        elif call.data == "referral":
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            safe_edit(call, f"{SYNDICATE_FULL}\n\n👇 **ТВОЯ ПЕРСОНАЛЬНАЯ ССЫЛКА:**\n`{link}`", get_main_menu(uid))

        elif call.data == "change_path_confirm":
            safe_edit(call, f"⚠️ **СМЕНА ФРАКЦИИ**\nЦена: **{PATH_CHANGE_COST} SYNC**.", get_path_menu(cost_info=True))

        elif "set_path_" in call.data:
            new_path = call.data.split("_")[-1]
            if u['xp'] >= PATH_CHANGE_COST or u['path'] == 'general':
                if u['path'] != 'general' and u['path'] != new_path: u['xp'] -= PATH_CHANGE_COST
                u['path'] = new_path; save_progress(uid)
                bot.send_photo(uid, MENU_IMAGE_URL, caption=f"/// ПУТЬ {new_path.upper()} ИНТЕГРИРОВАН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "use_accel":
            if u['accel'] > 0:
                u['accel'] -= 1; u['accel_exp'] = now_ts + 86400; save_progress(uid)
                bot.send_photo(uid, MENU_IMAGE_URL, caption="/// РАЗГОН АКТИВИРОВАН. КУЛДАУН: 15 МИН.", reply_markup=get_main_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ НЕТ УСКОРИТЕЛЯ", show_alert=True)

        elif call.data == "guide": 
            safe_edit(call, GUIDE_FULL, types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 В ТЕРМИНАЛ", callback_data="back_to_menu")))
    except Exception as e: print(f"/// CALLBACK ERROR: {e}")

# --- 9. ЗАПУСК ---
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'OK', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'Error', 500
    return 'Eidos Interface is Operational', 200

@app.route('/health')
def health_check(): return 'OK', 200

if __name__ == "__main__":
    if WEBHOOK_URL: 
        bot.remove_webhook(); time.sleep(1); bot.set_webhook(url=WEBHOOK_URL)
        print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
    threading.Thread(target=notification_worker, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
