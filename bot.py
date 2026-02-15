import telebot, flask, time, threading
from telebot import types
from config import *
import database as db
import keyboards as kb
import logic

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
user_states = {}

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if not db.get_user(uid):
        conn = db.get_db_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO users (uid, username, first_name) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (uid, m.from_user.username, m.from_user.first_name))
        conn.commit(); conn.close()
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// EIDOS-OS ЗАГРУЖЕНА", reply_markup=kb.main_menu(uid))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    
    if call.data.startswith("raid_step_"):
        alive, msg, riddle = logic.raid_step_logic(uid)
        if not alive:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 МЕНЮ", callback_data="back")), parse_mode="Markdown")
        elif riddle:
            user_states[uid] = riddle['correct']
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.riddle_keyboard(riddle['options']), parse_mode="Markdown")
        else:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard(), parse_mode="Markdown")

    elif call.data.startswith("r_pick_"):
        correct = user_states.get(uid, "")
        if call.data.replace("r_pick_", "") == correct[:15]:
            logic.process_xp_logic(uid, 150)
            bot.answer_callback_query(call.id, "✅ ВЕРНО!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"❌ ОШИБКА! Ответ: {correct}", show_alert=True)
        bot.edit_message_caption("/// ИДЕМ ДАЛЬШЕ...", call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    elif call.data == "back":
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА АКТИВНА", reply_markup=kb.main_menu(uid))



# --- НОВОЕ: ОБЯЗАТЕЛЬНЫЕ МАРШРУТЫ ДЛЯ RENDER ---


@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'OK', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'Error', 500
    return 'Eidos SQL Interface is Operational', 200

# ФОНОВЫЙ ЗАПУСК СИСТЕМ (ЧТОБЫ НЕ БЛОКИРОВАТЬ СТАРТ)
def system_startup():
    with app.app_context():
        # Даем серверу продышаться перед нагрузкой
        time.sleep(2)
        print("/// SYSTEM STARTUP INITIATED...")
        db.init_db()
        if WEBHOOK_URL:
            try:
                bot.remove_webhook()
                bot.set_webhook(url=WEBHOOK_URL)
                print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
            except Exception as e:
                print(f"/// WEBHOOK ERROR: {e}")
        # Запускаем воркер уведомлений
        notification_worker()

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)

