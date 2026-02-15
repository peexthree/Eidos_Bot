import telebot, flask, time, threading, random
from telebot import types
from psycopg2.extras import RealDictCursor
from config import *
import database as db
import keyboards as kb
import logic

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
waiting_for_diary = {} # Состояние для записи в дневник

def broadcast_progress(uid, is_up, new_achs):
    for ach in new_achs:
        bot.send_message(uid, f"🏆 **ДОСТИЖЕНИЕ ПОЛУЧЕНО**\n\n`{ach}`", parse_mode="Markdown")
    if is_up:
        u = db.get_user(uid)
        msg = LEVEL_UP_MSG.get(u['level'], f"👑 **НОВЫЙ СТАТУС:** {TITLES.get(u['level'])}")
        bot.send_message(uid, msg, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    ref_id = m.text.split()[1] if len(m.text.split()) > 1 else None
    if ref_id and str(ref_id) == str(uid): ref_id = None
    if not db.get_user(uid):
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (uid, m.from_user.username, m.from_user.first_name, ref_id))
                if ref_id: db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
            conn.commit()
    welcome = random.choice(WELCOME_VARIANTS)
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=f"`{welcome}`", reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    # --- 💠 СИНХРОН И 📡 СИГНАЛ ---
    if call.data == "get_protocol":
        ok, rem = logic.check_cooldown(uid, 'protocol')
        if not ok:
            bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem//60}м", show_alert=True); return
        content = logic.get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
        if content:
            gain, is_up, achs = logic.process_xp_logic(uid, XP_GAIN)
            db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
            bot.send_message(uid, f"🧬 **ПРОТОКОЛ**\n\n{content['text']}\n\n⚡️ +{gain} XP", reply_markup=kb.back_button(), parse_mode="Markdown")
            broadcast_progress(uid, is_up, achs)

    elif call.data == "get_signal":
        ok, rem = logic.check_cooldown(uid, 'signal')
        if not ok:
            bot.answer_callback_query(call.id, f"📡 ЖДИ: {rem}с.", show_alert=True); return
        content = logic.get_content_logic('signal')
        if content:
            gain, is_up, achs = logic.process_xp_logic(uid, XP_SIGNAL)
            db.update_user(uid, last_signal_time=int(time.time()))
            bot.send_message(uid, f"📶 **СИГНАЛ**\n\n{content['text']}\n\n⚡️ +{gain} XP", reply_markup=kb.back_button(), parse_mode="Markdown")
            broadcast_progress(uid, is_up, achs)

    # --- 🎰 РЫНОК И ПОКУПКИ ---
    elif call.data == "shop":
        bot.edit_message_caption(SHOP_FULL, call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(u), parse_mode="Markdown")

    elif call.data == "buy_cryo":
        if u['xp'] >= PRICES['cryo']:
            db.update_user(uid, xp=u['xp']-PRICES['cryo'], cryo=u['cryo']+1, total_spent=u['total_spent']+PRICES['cryo'])
            bot.answer_callback_query(call.id, "❄️ КРИО-КАПСУЛА ПРИОБРЕТЕНА", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

    elif call.data == "buy_accel":
        if u['accel_exp'] > time.time(): bot.answer_callback_query(call.id, "⚡️ УЖЕ АКТИВЕН", show_alert=True)
        elif u['xp'] >= PRICES['accel']:
            db.update_user(uid, xp=u['xp']-PRICES['accel'], accel_exp=int(time.time())+86400, total_spent=u['total_spent']+PRICES['accel'])
            bot.answer_callback_query(call.id, "⚡️ РАЗГОН ВКЛЮЧЕН (24ч)", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
        else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

    elif call.data == "change_path":
        if u['xp'] >= PATH_CHANGE_COST:
            bot.edit_message_caption("🧬 **ВЫБЕРИ ВЕКТОР:**", call.message.chat.id, call.message.message_id, reply_markup=kb.path_selection_keyboard())
        else: bot.answer_callback_query(call.id, f"Нужно {PATH_CHANGE_COST} XP", show_alert=True)

    elif call.data.startswith("set_path_"):
        new_p = call.data.replace("set_path_", "")
        db.update_user(uid, path=new_p, xp=u['xp']-PATH_CHANGE_COST)
        bot.edit_message_caption("/// ВЕКТОР УСТАНОВЛЕН", call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(db.get_user(uid)))

    # --- 👤 ПРОФИЛЬ (УЛУЧШЕННЫЙ) ---
    elif call.data == "profile":
        u = db.get_user(uid)
        percent, xp_needed = logic.get_level_progress_stats(u)
        p_bar = kb.get_progress_bar(percent, 100)
        
        with db.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
                achs = [row[0] for row in cur.fetchall()]
        ach_names = ", ".join([ACHIEVEMENTS_LIST[a]['name'] for a in achs if a in ACHIEVEMENTS_LIST]) or "Нет"
        
        accel_info = f"✅ ({int((u['accel_exp']-time.time())//60)}м)" if u['accel_exp'] > time.time() else "❌"

        msg = (f"👤 **ТЕРМИНАЛ: {u['first_name']}**\n"
               f"🔰 Статус: `{TITLES.get(u['level'])}`\n"
               f"📊 Прогресс: `{percent}%` | {p_bar}\n"
               f"💡 До след. уровня: `{xp_needed} XP`\n\n"
               f"🔋 Энергия: `{u['xp']} XP` | 🔥 Серия: `{u['streak']} дн.`\n"
               f"⚓️ Глубина: `{u['max_depth']} м.`\n"
               f"━━━━━━━━━━━━━━\n"
               f"🎒 **ИНВЕНТАРЬ:**\n"
               f"❄️ Крио: `{u['cryo']} шт.` | ⚡️ Ускоритель: {accel_info}\n"
               f"🔑 Дешифратор: `{'Есть' if u['decoder'] > 0 else 'Нет'}`\n"
               f"🏫 Школа: `{SCHOOLS.get(u['path'], 'Общая')}`\n"
               f"━━━━━━━━━━━━━━\n"
               f"🏆 **ДОСТИЖЕНИЯ:**\n_{ach_names}_")
        bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(u), parse_mode="Markdown")

    # --- 🏆 ТОП-10 И ДРУГОЕ ---
    elif call.data == "leaderboard":
        top = db.get_leaderboard()
        txt = "🏆 **ТОП-10 АРХИТЕКТОРОВ:**\n\n"
        for i, r in enumerate(top, 1): txt += f"{i}. {r['first_name']} — `{r['xp']} XP` (Lvl {r['level']})\n"
        bot.send_message(uid, txt, parse_mode="Markdown", reply_markup=kb.back_button())

    elif call.data == "guide": bot.send_message(uid, GUIDE_FULL, parse_mode="Markdown")
    elif call.data == "referral": bot.send_message(uid, f"{SYNDICATE_FULL}\n\n🔗 Ссылка: `https://t.me/{BOT_USERNAME}?start={uid}`", parse_mode="Markdown")
    
    # --- 📓 ДНЕВНИК ---
    elif call.data == "diary_mode":
        entries = db.get_diary_entries(uid)
        txt = "📓 **ДНЕВНИК ИНСАЙТОВ**\n\n"
        if not entries: txt += "_Пусто. Запиши свою первую мысль._"
        else:
            for e in entries: txt += f"• [{e['created_at'].strftime('%d.%m')}] {e['entry'][:50]}...\n"
        m = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("➕ ЗАПИСАТЬ", callback_data="diary_add"), types.InlineKeyboardButton("🔙", callback_data="back"))
        bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="Markdown")

    elif call.data == "diary_add":
        waiting_for_diary[uid] = True
        bot.send_message(uid, "📝 Отправь инсайт следующим сообщением (до 500 символов).")

    elif call.data == "back": bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption="/// ТЕРМИНАЛ ОНЛАЙН", reply_markup=kb.main_menu(u))
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: waiting_for_diary.get(m.from_user.id))
def save_diary(m):
    uid = m.from_user.id
    waiting_for_diary[uid] = False
    db.add_diary_entry(uid, m.text[:500])
    gain, is_up, achs = logic.process_xp_logic(uid, 5) # +5 XP за рефлексию
    bot.send_message(uid, "✅ Инсайт сохранен в Дневник. +5 XP", reply_markup=kb.main_menu(db.get_user(uid)))
    broadcast_progress(uid, is_up, achs)

# ... (оставь health, webhook и system_startup как в твоем файле) ...
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
