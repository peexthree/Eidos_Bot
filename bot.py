import telebot, flask, time, threading, random, os
from telebot import types
from psycopg2.extras import RealDictCursor
from config import *
import database as db
import keyboards as kb
import logic

# Инициализация
bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

# STATES
waiting_for_diary = {} 
waiting_for_admin_sql = {}
active_riddles = {} # {uid: "correct_answer_string"}

# =============================================================
# 📡 СИСТЕМНЫЕ УВЕДОМЛЕНИЯ
# =============================================================

def broadcast_progress(uid, is_up, new_achs):
    """Отправляет уведомления о левел-апе и ачивках"""
    try:
        for ach in new_achs:
            bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ ПОЛУЧЕНО</b>\n\n<code>{ach}</code>", parse_mode="HTML")
        
        if is_up:
            u = db.get_user(uid)
            msg = LEVEL_UP_MSG.get(u['level'], f"👑 <b>НОВЫЙ СТАТУС:</b> {TITLES.get(u['level'])}")
            bot.send_message(uid, msg, parse_mode="HTML")
    except Exception as e:
        print(f"/// BROADCAST ERROR: {e}")

# =============================================================
# 🚀 ТОЧКА ВХОДА
# =============================================================

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    ref_id = args[1] if len(args) > 1 else None
    if ref_id and str(ref_id) == str(uid): ref_id = None
    
    if not db.get_user(uid):
        username = m.from_user.username if m.from_user.username else "Unknown"
        first_name = m.from_user.first_name if m.from_user.first_name else "User"
        db.create_user(uid, username, first_name, ref_id)
        if ref_id: 
            db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
            try:
                bot.send_message(int(ref_id), f"🤝 <b>НОВЫЙ УЗЕЛ В СЕТИ.</b>\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
            except: pass

    welcome = random.choice(WELCOME_VARIANTS)
    caption_text = f"<code>{welcome}</code>"
    
    try:
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=caption_text, reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")
    except Exception as e:
        bot.send_message(m.chat.id, caption_text, reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")

# =============================================================
# 🎮 ОБРАБОТЧИК ИНТЕРФЕЙСА (CALLBACKS)
# =============================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        uid = call.from_user.id
        u = db.get_user(uid)
        if not u: return

        # ХЕЛПЕР ОБНОВЛЕНИЯ МЕНЮ
        def menu_update(text, markup=None):
            try:
                bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption=text, reply_markup=markup, parse_mode="HTML")
                except: pass

        # --- 💠 СИНХРОН ---
        if call.data == "get_protocol":
            ok, rem = logic.check_cooldown(uid, 'protocol')
            if not ok:
                bot.answer_callback_query(call.id, f"⏳ Остынь: {rem//60}м", show_alert=True)
                return
            
            content = logic.get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_GAIN)
                db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
                msg = f"🧬 <b>ПРОТОКОЛ</b>\n\n{content['text']}\n\n⚡️ +{gain} XP"
                menu_update(msg, kb.back_button())
                broadcast_progress(uid, is_up, achs)
            else:
                bot.answer_callback_query(call.id, "Пусто.", show_alert=True)

        elif call.data == "get_signal":
            ok, rem = logic.check_cooldown(uid, 'signal')
            if not ok:
                bot.answer_callback_query(call.id, f"⏳ {rem} сек", show_alert=True)
                return
            content = logic.get_content_logic('signal')
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_SIGNAL)
                db.update_user(uid, last_signal_time=int(time.time()))
                msg = f"📶 <b>СИГНАЛ</b>\n\n{content['text']}\n\n⚡️ +{gain} XP"
                menu_update(msg, kb.back_button())
                broadcast_progress(uid, is_up, achs)

        # --- 🌑 РЕЙД V2 ---
        elif call.data == "zero_layer_menu":
             msg = (f"<b>🌑 НУЛЕВОЙ СЛОЙ</b>\n\n"
                    f"Цена входа: <b>{RAID_COST} XP</b>\n"
                    f"Цена шага: <b>{RAID_STEP_COST} XP</b>\n"
                    f"Твой баланс: {u['xp']} XP\n\n"
                    f"<i>Здесь ты тратишь реальность, чтобы найти истину.</i>")
             
             m = types.InlineKeyboardMarkup()
             if u['xp'] >= RAID_COST:
                 m.add(types.InlineKeyboardButton("🚀 ВОЙТИ", callback_data="raid_start"))
             m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
             menu_update(msg, m)

        elif call.data == "raid_start":
             if u['xp'] < RAID_COST: return
             db.update_user(uid, xp=u['xp'] - RAID_COST)
             
             conn = db.get_db_connection()
             with conn.cursor() as cur:
                 cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
                 cur.execute("INSERT INTO raid_sessions (uid, start_time) VALUES (%s, %s)", (uid, int(time.time())))
                 conn.commit()
             conn.close()
             
             handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data == "raid_step":
             alive, msg, riddle, u_new = logic.raid_step_logic(uid)
             if not alive:
                 menu_update(msg, kb.back_button())
             else:
                 if riddle:
                     active_riddles[uid] = riddle['correct']
                     menu_update(msg, kb.riddle_keyboard(riddle['options']))
                 else:
                     menu_update(msg, kb.raid_action_keyboard())

        elif call.data.startswith("r_check_"):
             ans = call.data.replace("r_check_", "")
             correct = active_riddles.get(uid, "")
             
             if ans in correct: 
                 bot.answer_callback_query(call.id, "✅ ВЕРНО! +10 XP", show_alert=True)
                 db.add_xp_to_user(uid, 10)
                 handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
             else:
                 bot.answer_callback_query(call.id, "❌ ОШИБКА! УДАР ТОКОМ.", show_alert=True)
                 conn = db.get_db_connection()
                 with conn.cursor() as cur:
                     cur.execute("UPDATE raid_sessions SET signal = signal - 25 WHERE uid = %s", (uid,))
                     conn.commit()
                 conn.close()
                 handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data == "raid_extract":
             conn = db.get_db_connection()
             with conn.cursor(cursor_factory=RealDictCursor) as cur:
                 cur.execute("SELECT buffer_xp FROM raid_sessions WHERE uid = %s", (uid,))
                 res = cur.fetchone()
                 loot = res['buffer_xp'] if res else 0
                 cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
                 conn.commit()
             conn.close()
             
             gain, is_up, achs = logic.process_xp_logic(uid, loot, source='raid')
             msg = f"🚁 <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n\nВынесено: +{loot} XP\nБаланс: {u['xp']+loot}"
             menu_update(msg, kb.back_button())
             broadcast_progress(uid, is_up, achs)

        # --- 🔗 СИНДИКАТ ---
        elif call.data == "referral":
             refs = db.get_referrals_stats(uid)
             count = len(refs)
             earnings = sum([r['generated'] for r in refs])
             
             txt = (f"<b>🔗 СИНДИКАТ</b>\n\n"
                    f"Твоя сеть: {count} узлов\n"
                    f"Пассивный доход: {earnings} XP\n\n"
                    f"📜 <b>СПИСОК:</b>\n")
             
             if not refs: txt += "<i>Пусто. Распространяй вирус.</i>"
             else:
                 for r in refs[:10]:
                     txt += f"• {r['first_name']} (Lvl {r['level']}) — дал {r['generated']} XP\n"
             
             txt += f"\n🔗 Твоя ссылка:\n<code>https://t.me/{BOT_USERNAME}?start={uid}</code>"
             menu_update(txt, kb.back_button())

        # --- ⚡️ ADMIN PANEL ---
        elif call.data == "admin_panel" and str(uid) == str(ADMIN_ID):
             menu_update("⚡️ <b>GOD MODE CONSOLE</b>", kb.admin_keyboard())

        elif call.data == "admin_sql":
             waiting_for_admin_sql[uid] = True
             bot.send_message(uid, "⌨️ <b>Введи SQL запрос:</b>\nНапример: <code>SELECT * FROM users LIMIT 5</code>", parse_mode="HTML")

        elif call.data == "admin_users_count":
             res = db.admin_exec_query("SELECT COUNT(*) FROM users")
             bot.answer_callback_query(call.id, f"Users: {res}", show_alert=True)

        # --- СТАНДАРТНЫЕ ---
        elif call.data == "shop":
            menu_update(SHOP_FULL, kb.shop_menu(u))
        
        elif call.data == "profile":
            percent, xp_needed = logic.get_level_progress_stats(u)
            p_bar = kb.get_progress_bar(percent, 100)
            
            with db.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT ach_id FROM achievements WHERE uid = %s", (uid,))
                    achs = [row[0] for row in cur.fetchall()]
            
            ach_names = ", ".join([ACHIEVEMENTS_LIST[a]['name'] for a in achs if a in ACHIEVEMENTS_LIST]) or "Нет"
            accel_info = f"✅ ({int((u['accel_exp']-time.time())//60)}м)" if u['accel_exp'] > time.time() else "❌"

            msg = (f"👤 <b>ТЕРМИНАЛ: {u['first_name']}</b>\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\n"
                   f"📊 Прогресс: <code>{percent}%</code> | {p_bar}\n"
                   f"💡 До след. уровня: <code>{xp_needed} XP</code>\n\n"
                   f"🔋 Энергия: <code>{u['xp']} XP</code> | 🔥 Серия: <code>{u['streak']} дн.</code>\n"
                   f"⚓️ Глубина: <code>{u['max_depth']} м.</code>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🎒 <b>ИНВЕНТАРЬ:</b>\n"
                   f"❄️ Крио: <code>{u['cryo']} шт.</code> | ⚡️ Ускоритель: {accel_info}\n"
                   f"🔑 Дешифратор: <code>{'Есть' if u['decoder'] > 0 else 'Нет'}</code>\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\n"
                   f"━━━━━━━━━━━━━━\n"
                   f"🏆 <b>ДОСТИЖЕНИЯ:</b>\n<i>{ach_names}</i>")
            
            menu_update(msg, kb.main_menu(u))

        elif call.data == "leaderboard":
            top = db.get_leaderboard()
            txt = "🏆 <b>ТОП-10 АРХИТЕКТОРОВ:</b>\n\n"
            for i, r in enumerate(top, 1): 
                txt += f"{i}. {r['first_name']} — <code>{r['xp']} XP</code> (Lvl {r['level']})\n"
            menu_update(txt, kb.back_button())

        elif call.data == "guide": 
            menu_update(GUIDE_FULL, kb.back_button())

        elif call.data == "diary_mode":
            entries = db.get_diary_entries(uid)
            txt = "📓 <b>ДНЕВНИК ИНСАЙТОВ</b>\n\n"
            if not entries: txt += "<i>Пусто. Запиши свою первую мысль.</i>"
            else:
                for e in entries: 
                    d = e['created_at'].strftime('%d.%m') if hasattr(e['created_at'], 'strftime') else "Unknown"
                    txt += f"• [{d}] {e['entry'][:50]}...\n"
            
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("➕ ЗАПИСАТЬ", callback_data="diary_add"))
            m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
            menu_update(txt, m)
            
        elif call.data == "diary_add":
            waiting_for_diary[uid] = True
            bot.send_message(uid, "📝 Отправь инсайт следующим сообщением (до 500 символов).")

        elif call.data == "back":
            menu_update("/// ТЕРМИНАЛ ОНЛАЙН", kb.main_menu(u))
            
        elif call.data == "buy_cryo":
            if u['xp'] >= PRICES['cryo']:
                db.update_user(uid, xp=u['xp']-PRICES['cryo'], cryo=u['cryo']+1, total_spent=u['total_spent']+PRICES['cryo'])
                bot.answer_callback_query(call.id, "❄️ КРИО-КАПСУЛА ПРИОБРЕТЕНА", show_alert=True)
                menu_update(SHOP_FULL, kb.shop_menu(db.get_user(uid)))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
            
        elif call.data == "buy_accel":
             if u['accel_exp'] > time.time(): 
                 bot.answer_callback_query(call.id, "⚡️ УЖЕ АКТИВЕН", show_alert=True)
             elif u['xp'] >= PRICES['accel']:
                 db.update_user(uid, xp=u['xp']-PRICES['accel'], accel_exp=int(time.time())+86400, total_spent=u['total_spent']+PRICES['accel'])
                 bot.answer_callback_query(call.id, "⚡️ РАЗГОН ВКЛЮЧЕН (24ч)", show_alert=True)
                 menu_update(SHOP_FULL, kb.shop_menu(db.get_user(uid)))
             else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
             
        elif call.data == "buy_decoder":
            if u['decoder'] > 0:
                 bot.answer_callback_query(call.id, "🔑 У ТЕБЯ УЖЕ ЕСТЬ ДЕШИФРАТОР", show_alert=True)
            elif u['xp'] >= PRICES['decoder']:
                db.update_user(uid, xp=u['xp']-PRICES['decoder'], decoder=1, total_spent=u['total_spent']+PRICES['decoder'])
                bot.answer_callback_query(call.id, "🔑 ДОСТУП ПОВЫШЕН", show_alert=True)
                menu_update(SHOP_FULL, kb.shop_menu(db.get_user(uid)))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
            
        elif call.data == "change_path":
             if u['xp'] >= PATH_CHANGE_COST:
                 menu_update("🧬 <b>ВЫБЕРИ ВЕКТОР:</b>", kb.path_selection_keyboard())
             else: bot.answer_callback_query(call.id, f"Нужно {PATH_CHANGE_COST} XP", show_alert=True)

        elif call.data.startswith("set_path_"):
             new_p = call.data.replace("set_path_", "")
             db.update_user(uid, path=new_p, xp=u['xp']-PATH_CHANGE_COST)
             menu_update("/// ВЕКТОР УСТАНОВЛЕН", kb.main_menu(db.get_user(uid)))

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"ERROR: {e}")

# --- MESSAGE HANDLERS ---

@bot.message_handler(func=lambda m: waiting_for_diary.get(m.from_user.id))
def save_diary(m):
    uid = m.from_user.id
    waiting_for_diary[uid] = False
    db.add_diary_entry(uid, m.text[:500])
    gain, is_up, achs = logic.process_xp_logic(uid, 5) 
    bot.send_message(uid, "✅ Инсайт сохранен в Дневник. +5 XP", reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")
    broadcast_progress(uid, is_up, achs)

@bot.message_handler(func=lambda m: waiting_for_admin_sql.get(m.from_user.id))
def admin_sql_handler(m):
    uid = m.from_user.id
    waiting_for_admin_sql[uid] = False
    res = db.admin_exec_query(m.text)
    bot.send_message(uid, f"📊 <b>RESULT:</b>\n<code>{res}</code>", parse_mode="HTML")

# --- WEBHOOK ---

@app.route('/health')
def health(): return 'OK', 200

@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        try:
            json_string = flask.request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'ERROR', 500
    return 'OK', 200

def system_startup():
    print("/// EIDOS CORE STARTING...")
    db.init_db()
    
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
    
    while True:
        try:
            time.sleep(60)
            conn = db.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT uid, last_protocol_time, accel_exp FROM users WHERE notified = FALSE")
                    rows = cur.fetchall()
                conn.close()
                for row in rows:
                    cd = COOLDOWN_ACCEL if row['accel_exp'] > time.time() else COOLDOWN_BASE
                    if time.time() - row['last_protocol_time'] >= cd:
                        try:
                            kb_start = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("👁 НАЧАТЬ", callback_data="get_protocol"))
                            bot.send_message(row['uid'], "⚡️ <b>СИСТЕМА ГОТОВА К СИНХРОНИЗАЦИИ.</b>", reply_markup=kb_start, parse_mode="HTML")
                            db.update_user(row['uid'], notified=True)
                        except: pass
        except: pass

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
