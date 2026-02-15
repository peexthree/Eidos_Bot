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
# 🛠 СИСТЕМНЫЕ ФУНКЦИИ (УВЕДОМЛЕНИЯ И АПДЕЙТЫ)
# =============================================================

def broadcast_progress(uid, is_up):
    """Проверяет ачивки и уведомляет о новом уровне"""
    # 1. Авто-проверка всех 25 достижений
    new_ach = logic.check_achievements(uid)
    for ach in new_ach:
        bot.send_message(uid, f"🏆 **ДОСТИЖЕНИЕ ПОЛУЧЕНО**\n\n`{ach}`", parse_mode="Markdown")
    
    # 2. Уведомление о повышении уровня
    if is_up:
        u = db.get_user(uid)
        msg = LEVEL_UP_MSG.get(u['level'], f"👑 **НОВЫЙ СТАТУС:** {TITLES[u['level']]}")
        bot.send_message(uid, msg, parse_mode="Markdown")

# =============================================================
# 📡 ОБРАБОТКА ВХОДНЫХ ТОЧЕК (COMMANDS)
# =============================================================

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    ref_id = m.text.split()[1] if len(m.text.split()) > 1 else None
    
    # Защита от самореферальства
    if ref_id and str(ref_id) == str(uid): ref_id = None
    
    user = db.get_user(uid)
    if not user:
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", 
                    (uid, m.from_user.username, m.from_user.first_name, ref_id)
                )
                if ref_id:
                    db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
            conn.commit()
        user = db.get_user(uid)
        print(f"/// NEW NODE INITIALIZED: {uid}")

    welcome = random.choice(WELCOME_VARIANTS)
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=f"`{welcome}`", reply_markup=kb.main_menu(user), parse_mode="Markdown")

# =============================================================
# 🕹 ЦЕНТРАЛЬНЫЙ ОБРАБОТЧИК (CALLBACKS)
# =============================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return
    
    # 1. СИНХРОНИЗАЦИЯ (ОСНОВНОЙ КОНТЕНТ)
    if call.data == "get_protocol":
        ok, rem = logic.check_cooldown(uid, 'protocol')
        if not ok:
            bot.answer_callback_query(call.id, f"⏳ ТЕРМИНАЛ ПЕРЕГРЕТ. ЖДИ: {rem//60}м", show_alert=True)
            return
        
        gain, is_up = logic.process_xp_logic(uid, XP_GAIN)
        db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
        
        # Здесь бот берет контент из БД (предполагаем наличие функции в logic или db)
        bot.send_message(uid, f"🧬 **ПРОТОКОЛ ДЕШИФРОВАН**\n\n`Вставьте здесь текст синхрона из БД` \n\n⚡️ Энергия: +{gain} XP", 
                         reply_markup=kb.back_button(), parse_mode="Markdown")
        broadcast_progress(uid, is_up)

    # 2. НУЛЕВОЙ СЛОЙ (РЕЙД)
    elif call.data == "zero_layer_menu":
        bot.edit_message_caption(f"🌑 **НУЛЕВОЙ СЛОЙ**\n\n`STATUS: ОПАСНО`\n🎫 Вход: {RAID_COST} XP\n⚓️ Рекорд: {u['max_depth']} м.", 
                                 call.message.chat.id, call.message.message_id, 
                                 reply_markup=types.InlineKeyboardMarkup().add(
                                     types.InlineKeyboardButton("🌪 ПОГРУЖЕНИЕ", callback_data="raid_go"),
                                     types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back")
                                 ), parse_mode="Markdown")

    elif call.data == "raid_go":
        if u['xp'] < RAID_COST:
            bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО XP", show_alert=True); return
        db.update_user(uid, xp=u['xp'] - RAID_COST)
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO raid_sessions (uid, start_time) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET depth=0, signal=100, buffer_xp=0", (uid, int(time.time())))
            conn.commit()
        bot.edit_message_caption("🌀 **ИНТЕГРАЦИЯ...**", call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard())

    elif call.data.startswith("raid_step_"):
        alive, msg, riddle = logic.raid_step_logic(uid)
        if not alive:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.back_button(), parse_mode="Markdown")
        elif riddle:
            # ПРАВИЛЬНОЕ РЕШЕНИЕ: Ответ на загадку пишем в спец. поле сессии рейда
            with db.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Мы создадим колонку riddle_ans в raid_sessions (см. database.py)
                    cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp, start_time = start_time WHERE uid = %s", (uid,)) 
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.riddle_keyboard(riddle['options']), parse_mode="Markdown")
        else:
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.raid_keyboard(), parse_mode="Markdown")

    # 3. РЫНОК И ПРОФИЛЬ
    elif call.data == "shop":
        bot.edit_message_caption(SHOP_FULL, call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(u), parse_mode="Markdown")

    elif call.data == "profile":
        u = db.get_user(uid) # Обновляем данные
        msg = (f"👤 **ТЕРМИНАЛ: {u['first_name']}**\n"
               f"🔰 Статус: `{TITLES.get(u['level'])}`\n"
               f"🔋 Энергия: `{u['xp']} XP`\n"
               f"🔥 Серия: `{u['streak']} дн.`\n"
               f"⚓️ Глубина: `{u['max_depth']} м.`")
        bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(u), parse_mode="Markdown")

    elif call.data == "back":
        bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ ОНЛАЙН", reply_markup=kb.main_menu(u))
    
    bot.answer_callback_query(call.id)

# =============================================================
# ⚙️ ИНФРАСТРУКТУРА (SERVER & WORKER)
# =============================================================

@app.route('/health')
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
    return 'OK', 200

def system_startup():
    print("/// EIDOS CORE STARTING...")
    db.init_db()
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    
    # Воркер уведомлений (теперь с использованием db-функций)
    while True:
        try:
            time.sleep(60)
            with db.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT uid, last_protocol_time, accel_exp FROM users WHERE notified = FALSE")
                    for row in cur.fetchall():
                        cd = COOLDOWN_ACCEL if row['accel_exp'] > time.time() else COOLDOWN_BASE
                        if time.time() - row['last_protocol_time'] >= cd:
                            bot.send_message(row['uid'], "⚡️ **СИСТЕМА ГОТОВА К СИНХРОНИЗАЦИИ.**", 
                                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 НАЧАТЬ", callback_data="get_protocol")))
                            db.update_user(row['uid'], notified=True)
        except Exception as e: print(f"/// WORKER ERROR: {e}")

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
