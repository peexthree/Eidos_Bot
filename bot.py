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
waiting_for_diary = {} 

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
            # Берем текст из конфига (он уже в HTML)
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
    # Парсинг рефералки
    args = m.text.split()
    ref_id = args[1] if len(args) > 1 else None
    if ref_id and str(ref_id) == str(uid): ref_id = None
    
    # Регистрация
    if not db.get_user(uid):
        username = m.from_user.username if m.from_user.username else "Unknown"
        first_name = m.from_user.first_name if m.from_user.first_name else "User"
        db.create_user(uid, username, first_name, ref_id)
        if ref_id: 
            # Начисляем бонус рефереру
            db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
            try:
                bot.send_message(int(ref_id), f"🤝 <b>НОВЫЙ УЗЕЛ В СЕТИ.</b>\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
            except: pass

    welcome = random.choice(WELCOME_VARIANTS)
    # Используем HTML для форматирования
    caption_text = f"<code>{welcome}</code>"
    
    try:
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=caption_text, reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")
    except Exception as e:
        # Фоллбэк, если картинка не грузится
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

        # --- 💠 СИНХРОН И 📡 СИГНАЛ ---
        if call.data == "get_protocol":
            ok, rem = logic.check_cooldown(uid, 'protocol')
            if not ok:
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem//60}м", show_alert=True)
                return
            
            content = logic.get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_GAIN)
                db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
                
                # HTML FORMAT
                msg = f"🧬 <b>ПРОТОКОЛ</b>\n\n{content['text']}\n\n⚡️ +{gain} XP"
                bot.send_message(uid, msg, reply_markup=kb.back_button(), parse_mode="HTML")
                broadcast_progress(uid, is_up, achs)
            else:
                bot.answer_callback_query(call.id, "⚠️ Нет данных для твоего уровня.", show_alert=True)

        elif call.data == "get_signal":
            ok, rem = logic.check_cooldown(uid, 'signal')
            if not ok:
                bot.answer_callback_query(call.id, f"📡 ЖДИ: {rem}с.", show_alert=True)
                return
            
            content = logic.get_content_logic('signal')
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_SIGNAL)
                db.update_user(uid, last_signal_time=int(time.time()))
                
                msg = f"📶 <b>СИГНАЛ</b>\n\n{content['text']}\n\n⚡️ +{gain} XP"
                bot.send_message(uid, msg, reply_markup=kb.back_button(), parse_mode="HTML")
                broadcast_progress(uid, is_up, achs)

        # --- 🎰 РЫНОК И ПОКУПКИ ---
        elif call.data == "shop":
            bot.edit_message_caption(SHOP_FULL, call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(u), parse_mode="HTML")

        elif call.data == "buy_cryo":
            if u['xp'] >= PRICES['cryo']:
                db.update_user(uid, xp=u['xp']-PRICES['cryo'], cryo=u['cryo']+1, total_spent=u['total_spent']+PRICES['cryo'])
                bot.answer_callback_query(call.id, "❄️ КРИО-КАПСУЛА ПРИОБРЕТЕНА", show_alert=True)
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "buy_accel":
            if u['accel_exp'] > time.time(): 
                bot.answer_callback_query(call.id, "⚡️ УЖЕ АКТИВЕН", show_alert=True)
            elif u['xp'] >= PRICES['accel']:
                db.update_user(uid, xp=u['xp']-PRICES['accel'], accel_exp=int(time.time())+86400, total_spent=u['total_spent']+PRICES['accel'])
                bot.answer_callback_query(call.id, "⚡️ РАЗГОН ВКЛЮЧЕН (24ч)", show_alert=True)
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)
        
        elif call.data == "buy_decoder":
            if u['decoder'] > 0:
                 bot.answer_callback_query(call.id, "🔑 У ТЕБЯ УЖЕ ЕСТЬ ДЕШИФРАТОР", show_alert=True)
            elif u['xp'] >= PRICES['decoder']:
                db.update_user(uid, xp=u['xp']-PRICES['decoder'], decoder=1, total_spent=u['total_spent']+PRICES['decoder'])
                bot.answer_callback_query(call.id, "🔑 ДОСТУП ПОВЫШЕН", show_alert=True)
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb.shop_menu(db.get_user(uid)))
            else: bot.answer_callback_query(call.id, "❌ МАЛО XP", show_alert=True)

        elif call.data == "change_path":
            if u['xp'] >= PATH_CHANGE_COST:
                bot.edit_message_caption("🧬 <b>ВЫБЕРИ ВЕКТОР:</b>", call.message.chat.id, call.message.message_id, reply_markup=kb.path_selection_keyboard(), parse_mode="HTML")
            else: bot.answer_callback_query(call.id, f"Нужно {PATH_CHANGE_COST} XP", show_alert=True)

        elif call.data.startswith("set_path_"):
            new_p = call.data.replace("set_path_", "")
            db.update_user(uid, path=new_p, xp=u['xp']-PATH_CHANGE_COST)
            bot.edit_message_caption("/// ВЕКТОР УСТАНОВЛЕН", call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")

        # --- 🌑 НУЛЕВОЙ СЛОЙ (РЕЙДЫ) ---
        elif call.data == "zero_layer_menu":
             msg = (f"<b>🌑 НУЛЕВОЙ СЛОЙ</b>\n\n"
                    f"Зона высокого риска. Здесь нет законов физики.\n"
                    f"Стоимость входа: <b>{RAID_COST} XP</b>\n\n"
                    f"Твой баланс: {u['xp']} XP")
             
             # Клавиатура входа
             m = types.InlineKeyboardMarkup()
             if u['xp'] >= RAID_COST:
                 m.add(types.InlineKeyboardButton(f"🚀 ВОЙТИ (-{RAID_COST})", callback_data="raid_start"))
             else:
                 m.add(types.InlineKeyboardButton("🔒 НЕДОСТАТОЧНО ЭНЕРГИИ", callback_data="shop"))
             m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
             
             bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")

        elif call.data == "raid_start":
             if u['xp'] < RAID_COST: return
             # Списываем XP и создаем сессию
             db.update_user(uid, xp=u['xp'] - RAID_COST)
             
             conn = db.get_db_connection()
             with conn.cursor() as cur:
                 cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,)) # Очистка старой
                 cur.execute("INSERT INTO raid_sessions (uid, start_time) VALUES (%s, %s)", (uid, int(time.time())))
                 conn.commit()
             conn.close()
             
             # Первый шаг
             handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data == "raid_step" or call.data.startswith("r_ans_"):
             # Проверка ответа на загадку (если был)
             # В этой версии упростим: любой ответ ведет дальше, но правильный дает бонус?
             # Пока просто логика шага
             
             alive, msg, riddle = logic.raid_step_logic(uid)
             
             if not alive:
                 # Гейм овер
                 bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.back_button(), parse_mode="HTML")
             else:
                 # Продолжаем
                 markup = kb.riddle_keyboard(riddle['options'], riddle['correct']) if riddle else kb.raid_keyboard()
                 bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

        elif call.data == "raid_extract":
             conn = db.get_db_connection()
             with conn.cursor(cursor_factory=RealDictCursor) as cur:
                 cur.execute("SELECT buffer_xp FROM raid_sessions WHERE uid = %s", (uid,))
                 res = cur.fetchone()
                 if res:
                     loot = res['buffer_xp']
                     cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
                     conn.commit()
                     
                     gain, is_up, achs = logic.process_xp_logic(uid, loot, source='raid')
                     bot.edit_message_caption(f"🚁 <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n\nВынесено: +{loot} XP", call.message.chat.id, call.message.message_id, reply_markup=kb.back_button(), parse_mode="HTML")
                     broadcast_progress(uid, is_up, achs)
                 else:
                     bot.answer_callback_query(call.id, "Ошибка шлюза", show_alert=True)
             conn.close()


        # --- 👤 ПРОФИЛЬ ---
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
            
            bot.edit_message_caption(msg, call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(u), parse_mode="HTML")

        # --- 🏆 ТОП-10 И ДРУГОЕ ---
        elif call.data == "leaderboard":
            top = db.get_leaderboard()
            txt = "🏆 <b>ТОП-10 АРХИТЕКТОРОВ:</b>\n\n"
            for i, r in enumerate(top, 1): 
                txt += f"{i}. {r['first_name']} — <code>{r['xp']} XP</code> (Lvl {r['level']})\n"
            bot.send_message(uid, txt, parse_mode="HTML", reply_markup=kb.back_button())

        elif call.data == "guide": 
            bot.send_message(uid, GUIDE_FULL, parse_mode="HTML")
        
        elif call.data == "referral": 
            bot.send_message(uid, f"{SYNDICATE_FULL}\n\n🔗 Ссылка: <code>https://t.me/{BOT_USERNAME}?start={uid}</code>", parse_mode="HTML")
        
        # --- 📓 ДНЕВНИК ---
        elif call.data == "diary_mode":
            entries = db.get_diary_entries(uid)
            txt = "📓 <b>ДНЕВНИК ИНСАЙТОВ</b>\n\n"
            if not entries: 
                txt += "<i>Пусто. Запиши свою первую мысль.</i>"
            else:
                for e in entries: 
                    # Форматирование даты
                    d = e['created_at'].strftime('%d.%m') if hasattr(e['created_at'], 'strftime') else "Unknown"
                    txt += f"• [{d}] {e['entry'][:50]}...\n"
            
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("➕ ЗАПИСАТЬ", callback_data="diary_add"))
            m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
            
            bot.edit_message_caption(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")

        elif call.data == "diary_add":
            waiting_for_diary[uid] = True
            bot.send_message(uid, "📝 Отправь инсайт следующим сообщением (до 500 символов).")

        elif call.data == "back": 
            # Якорь на картинку
            caption = "/// ТЕРМИНАЛ ОНЛАЙН"
            try:
                bot.edit_message_caption(caption, call.message.chat.id, call.message.message_id, reply_markup=kb.main_menu(u), parse_mode="HTML")
            except:
                # Если старое сообщение было без картинки (текст), то шлем новое фото
                bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption=caption, reply_markup=kb.main_menu(u), parse_mode="HTML")

        # --- ADMIN PANEL ---
        elif call.data == "admin_panel" and uid == ADMIN_ID:
             bot.send_message(uid, "⚡️ ADMIN TERMINAL ACTIVE", reply_markup=kb.admin_keyboard())
        
        # Финализация коллбека, чтобы не крутился спиннер
        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"/// HANDLER ERROR: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ GLITCH DETECTED", show_alert=True)
        except: pass

# =============================================================
# 📨 ОБРАБОТЧИК СООБЩЕНИЙ (ДНЕВНИК И ПР.)
# =============================================================

@bot.message_handler(func=lambda m: waiting_for_diary.get(m.from_user.id))
def save_diary(m):
    uid = m.from_user.id
    waiting_for_diary[uid] = False
    db.add_diary_entry(uid, m.text[:500])
    gain, is_up, achs = logic.process_xp_logic(uid, 5) # +5 XP за рефлексию
    bot.send_message(uid, "✅ Инсайт сохранен в Дневник. +5 XP", reply_markup=kb.main_menu(db.get_user(uid)), parse_mode="HTML")
    broadcast_progress(uid, is_up, achs)

# =============================================================
# 🔌 WEBHOOK & SERVER
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
    
    # Настройка вебхука
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=WEBHOOK_URL)
            print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
    
    # Воркер уведомлений
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
                        except Exception as e:
                            print(f"/// NOTIFY ERROR for {row['uid']}: {e}")
        except Exception as e:
            print(f"/// WORKER ERROR: {e}")

# Запуск в отдельном потоке, чтобы Flask не блокировал воркера
threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
