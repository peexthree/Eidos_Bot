import telebot, flask, time, threading
from telebot import types
from psycopg2.extras import RealDictCursor
from config import *
import database as db
import keyboards as kb
import logic

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
user_states = {} # Хранение правильных ответов для текущих сессий

# --- ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if not db.get_user(uid):
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (uid, username, first_name) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                    (uid, m.from_user.username, m.from_user.first_name))
        conn.commit()
        cur.close()
        conn.close()
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ EIDOS: ОНЛАЙН", reply_markup=kb.main_menu(uid))

# --- ОБРАБОТКА КНОПОК (CALLBACK) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return
    bot.answer_callback_query(call.id)

    # 1. Рейд: Движение
    if call.data.startswith("raid_step_"):
        alive, msg, riddle = logic.raid_step_logic(uid)
        if not alive:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, 
                                     reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔄 В МЕНЮ", callback_data="back")), 
                                     parse_mode="Markdown")
        elif riddle:
            user_states[uid] = riddle['correct']
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, 
                                     reply_markup=kb.riddle_keyboard(riddle['options']), 
                                     parse_mode="Markdown")
        else:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, 
                                     reply_markup=kb.raid_keyboard(), 
                                     parse_mode="Markdown")

    # 2. Рейд: Ответ на загадку
    elif call.data.startswith("r_p_"):
        correct = user_states.get(uid, "")
        picked = call.data.replace("r_p_", "")
        if picked == correct[:15]:
            logic.process_xp_logic(uid, 150)
            res_text = f"✅ **ВЕРНО!** +150 XP"
        else:
            res_text = f"❌ **ОШИБКА!** Ответ: {correct}"
        
        bot.answer_callback_query(call.id, res_text, show_alert=True)
        bot.edit_message_caption("/// ШИФР ОБРАБОТАН. ИДЕМ ДАЛЬШЕ...", call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    # 3. Синхрон и Сигнал
    elif call.data == "get_protocol":
        content = logic.get_content_logic('protocol', u['path'], u['level'])
        if content:
            logic.process_xp_logic(uid, XP_GAIN)
            bot.send_message(uid, f"🧬 **ПРОТОКОЛ**\n\n{content['text']}\n\n⚡️ +{XP_GAIN} XP", 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back")))

    elif call.data == "get_signal":
        content = logic.get_content_logic('signal')
        if content:
            logic.process_xp_logic(uid, XP_SIGNAL)
            bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{content['text']}\n\n⚡️ +{XP_SIGNAL} XP", 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back")))

    # 4. Профиль, Рынок и Меню Рейда
    elif call.data == "profile":
        msg = f"👤 **ПРОФИЛЬ**\n━━━━━━━━━━━━━━\n🔰 Статус: {TITLES.get(u['level'], 'НЕОФИТ')}\n🔋 Энергия: {u['xp']} XP\n⚓️ Рекорд: {u['max_depth']} м."
        bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(uid))

    elif call.data == "shop":
        bot.edit_message_caption("🎰 **ЧЕРНЫЙ РЫНОК**", call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu())

    elif call.data == "zero_layer_menu":
        bot.edit_message_caption(f"🌑 **НУЛЕВОЙ СЛОЙ**\n🎫 Вход: {RAID_COST} XP", call.message.chat.id, call.message.message_id, 
                                 reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🌪 ПОГРУЖЕНИЕ", callback_data="raid_go"), 
                                 types.InlineKeyboardButton("🔙", callback_data="back")), parse_mode="Markdown")

    elif call.data == "raid_go":
        if u['xp'] < RAID_COST:
            bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
            return
        db.update_user(uid, xp=u['xp']-RAID_COST)
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO raid_sessions (uid, start_time) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET depth=0, signal=100, buffer_xp=0", (uid, int(time.time())))
        conn.commit()
        cur.close(); conn.close()
        bot.edit_message_caption("🌀 **ПОГРУЖЕНИЕ...**", call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    elif call.data == "back":
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА ONLINE", reply_markup=kb.main_menu(uid))

# --- СИСТЕМА УВЕДОМЛЕНИЙ ---

def notification_worker():
    while True:
        try:
            time.sleep(60)
            conn = db.get_db_connection()
            if not conn: continue
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM users WHERE notified = FALSE")
            users = cur.fetchall()
            now = time.time()
            for u in users:
                cd = COOLDOWN_ACCEL if u['accel_exp'] > now else COOLDOWN_BASE
                if u['last_protocol_time'] > 0 and (now - u['last_protocol_time'] >= cd):
                    try:
                        bot.send_message(u['uid'], "⚡️ **ПРОТОКОЛ ВОССТАНОВЛЕН.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🧬 ДЕШИФРОВАТЬ", callback_data="get_protocol")))
                        db.update_user(u['uid'], notified=True)
                    except: pass
            cur.close(); conn.close()
        except Exception as e: print(f"/// WORKER ERROR: {e}")

# --- ТВОЯ КОНСТРУКЦИЯ ЗАПУСКА ---

@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
        return 'OK', 200
    return 'Eidos System: Operational', 200

def system_startup():
    """Инициализация базы и вебхука"""
    time.sleep(2)
    print("/// SYSTEM STARTUP INITIATED...")
    db.init_db()
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
    # Запускаем воркер уведомлений
    notification_worker()

# Запуск в отдельном потоке, чтобы не блокировать Flask
threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)
