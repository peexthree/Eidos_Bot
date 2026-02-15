import telebot, flask, time, threading, random
from telebot import types
from psycopg2.extras import RealDictCursor
from config import *
import database as db
import keyboards as kb
import logic

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# =============================================================
# 1. ОБРАБОТКА КОМАНД (ВХОД В МАТРИЦУ)
# =============================================================

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    # Умная рефералка: проверяем, что юзер не пригласил сам себя
    ref_id = m.text.split()[1] if len(m.text.split()) > 1 else None
    if ref_id and str(ref_id) == str(uid): ref_id = None 
    
    user = db.get_user(uid)
    if not user:
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", 
                    (uid, m.from_user.username, m.from_user.first_name, ref_id)
                )
                if ref_id: # Бонус за вербовку
                    cur.execute("UPDATE users SET xp = xp + %s, ref_count = ref_count + 1 WHERE uid = %s", (REFERRAL_BONUS, ref_id))
            conn.commit()
        user = db.get_user(uid)
        bot.send_message(ADMIN_ID, f"🆕 НОВЫЙ УЗЕЛ: {m.from_user.first_name} (ID: {uid})")

    welcome_text = random.choice(WELCOME_VARIANTS)
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=welcome_text, reply_markup=kb.main_menu(user))

# =============================================================
# 2. ВСПОМОГАТЕЛЬНЫЙ ФУНКЦИОНАЛ (УВЕДОМЛЕНИЯ)
# =============================================================

def send_update_package(uid, gain, is_lvl_up, u_after):
    """Отправляет пак уведомлений: XP + Ачивки + Уровень"""
    # 1. Проверка ачивок
    new_achievements = logic.check_achievements(uid)
    for ach in new_achievements:
        bot.send_message(uid, f"🏆 **ДОСТИЖЕНИЕ ОТКРЫТО!**\n\n{ach}", parse_mode="Markdown")
    
    # 2. Уведомление о LVL UP
    if is_lvl_up:
        msg = LEVEL_UP_MSG.get(u_after['level'], f"👑 Твой статус повышен до: {TITLES[u_after['level']]}")
        bot.send_message(uid, msg, parse_mode="Markdown")

# =============================================================
# 3. ОБРАБОТКА CALLBACK (ЛОГИКА КНОПОК)
# =============================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    # --- СИНХРОН И СИГНАЛ ---
    if call.data == "get_protocol":
        ok, rem = logic.check_cooldown(uid, 'protocol')
        if not ok:
            bot.answer_callback_query(call.id, f"⏳ ДЕШИФРАЦИЯ ЗАБЛОКИРОВАНА: {rem//60}м", show_alert=True)
            return
        
        # Здесь логика получения контента из БД (content = db.get_random_content...)
        gain, is_up = logic.process_xp_logic(uid, XP_GAIN)
        db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
        
        bot.send_message(uid, f"🧬 **ПРОТОКОЛ ПРИНЯТ**\n\n(Текст из БД)\n\n🔋 Энергия: +{gain} XP", reply_markup=kb.back_button())
        send_update_package(uid, gain, is_up, db.get_user(uid))

    # --- МАГАЗИН И ПОКУПКИ ---
    elif call.data == "shop":
        bot.edit_message_caption(SHOP_FULL, call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(u))

    elif call.data == "buy_cryo":
        if u['xp'] >= PRICES['cryo']:
            db.update_user(uid, xp=u['xp']-PRICES['cryo'], cryo=u['cryo']+1, total_spent=u['total_spent']+PRICES['cryo'])
            bot.answer_callback_query(call.id, "❄️ КРИО-КАПСУЛА УСТАНОВЛЕНА", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
        else:
            bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО XP", show_alert=True)

    # --- НУЛЕВОЙ СЛОЙ (РЕЙД) ---
    elif call.data == "raid_go":
        if u['xp'] < RAID_COST:
            bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО XP ДЛЯ ВЗЛОМА", show_alert=True); return
        db.update_user(uid, xp=u['xp'] - RAID_COST)
        with db.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO raid_sessions (uid, start_time) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET depth=0, signal=100, buffer_xp=0", (uid, int(time.time())))
        bot.edit_message_caption("🌀 **ИНТЕГРАЦИЯ...**", call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    elif call.data.startswith("raid_step_"):
        alive, msg, riddle = logic.raid_step_logic(uid)
        if not alive:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.back_button())
        elif riddle:
            # Сохраняем ответ в базу, а не в словарь (для надежности)
            db.update_user(uid, username=f"ANS:{riddle['correct']}") # Хак: временно используем поле или отдельную таблицу
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.riddle_keyboard(riddle['options']))
        else:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    elif call.data == "back":
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ ОНЛАЙН", reply_markup=kb.main_menu(db.get_user(uid)))
    
    bot.answer_callback_query(call.id)

# =============================================================
# 4. СЛУЖБЫ И ЗАПУСК (RENDER)
# =============================================================

@app.route('/health')
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
    return 'OK', 200

def system_startup():
    print("/// SYSTEM STARTUP...")
    db.init_db()
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    
    # Воркер уведомлений
    while True:
        try:
            time.sleep(60)
            with db.get_db_connection() as conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("SELECT uid, last_protocol_time, accel_exp FROM users WHERE notified = FALSE")
                for row in cur.fetchall():
                    cd = COOLDOWN_ACCEL if row['accel_exp'] > time.time() else COOLDOWN_BASE
                    if time.time() - row['last_protocol_time'] >= cd:
                        bot.send_message(row['uid'], "⚡️ **ПРОТОКОЛ ВОССТАНОВЛЕН.**", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol")))
                        db.update_user(row['uid'], notified=True)
        except Exception as e: print(f"Worker Error: {e}")

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
