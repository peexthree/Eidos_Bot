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

# STATES (Состояния пользователей)
user_states = {} # {uid: "state_name"}
active_riddles = {} # {uid: "correct_answer"}

# =============================================================
# 🟢 СИСТЕМНЫЕ ФУНКЦИИ
# =============================================================

def broadcast_progress(uid, is_up, new_achs):
    """Отправляет уведомления о левел-апе и ачивках"""
    try:
        for ach in new_achs:
            bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ:</b> {ach}", parse_mode="HTML")
        
        if is_up:
            u = db.get_user(uid)
            msg = LEVEL_UP_MSG.get(u['level'], f"👑 <b>НОВЫЙ СТАТУС:</b> {TITLES.get(u['level'])}")
            bot.send_message(uid, msg, parse_mode="HTML")
    except: pass

def menu_update(call, text, markup=None):
    """Безопасное обновление меню (Caption или Text)"""
    try:
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except:
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_photo(call.message.chat.id, MENU_IMAGE_URL, caption=text, reply_markup=markup, parse_mode="HTML")
            except: pass

# =============================================================
# 🚀 СТАРТ И РЕГИСТРАЦИЯ
# =============================================================

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    ref_id = args[1] if len(args) > 1 else None
    
    if ref_id and str(ref_id) == str(uid): ref_id = None
    
    if not db.get_user(uid):
        username = m.from_user.username or "Unknown"
        first_name = m.from_user.first_name or "User"
        db.create_user(uid, username, first_name, ref_id)
        if ref_id:
            try:
                db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
                bot.send_message(int(ref_id), f"🤝 <b>НОВЫЙ УЗЕЛ В СЕТИ!</b>\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
            except: pass

    u = db.get_user(uid)
    caption = f"<code>{random.choice(WELCOME_VARIANTS)}</code>"
    try:
        bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=caption, reply_markup=kb.main_menu(u), parse_mode="HTML")
    except:
        bot.send_message(m.chat.id, caption, reply_markup=kb.main_menu(u), parse_mode="HTML")

# =============================================================
# 🎮 ОБРАБОТЧИК КНОПОК (ГЛАВНЫЙ ЦИКЛ)
# =============================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        uid = call.from_user.id
        u = db.get_user(uid)
        if not u: return

        # --- 1. ЭНЕРГИЯ И ЗНАНИЯ ---
        if call.data == "get_protocol":
            ok, rem = logic.check_cooldown(uid, 'protocol')
            if not ok:
                bot.answer_callback_query(call.id, f"⏳ ПЕРЕГРЕВ: {rem//60} мин", show_alert=True)
                return
            
            content = logic.get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_GAIN)
                db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
                # Сохраняем в историю для архива
                db.save_knowledge(uid, content.get('id', 0)) 
                menu_update(call, f"🧬 <b>ПРОТОКОЛ ЗАГРУЖЕН</b>\n\n{content['text']}\n\n⚡️ +{gain} XP", kb.back_button())
                broadcast_progress(uid, is_up, achs)

        elif call.data == "get_signal":
            ok, rem = logic.check_cooldown(uid, 'signal')
            if not ok:
                bot.answer_callback_query(call.id, f"⏳ ЖДИ: {rem} сек", show_alert=True)
                return
            content = logic.get_content_logic('signal')
            if content:
                gain, is_up, achs = logic.process_xp_logic(uid, XP_SIGNAL)
                db.update_user(uid, last_signal_time=int(time.time()))
                menu_update(call, f"📡 <b>СИГНАЛ ПОЛУЧЕН</b>\n\n{content['text']}\n\n⚡️ +{gain} XP", kb.back_button())
                broadcast_progress(uid, is_up, achs)

        # --- 2. РЕЙД (ЭКСПЕДИЦИЯ) ---
        elif call.data == "zero_layer_menu":
             m = types.InlineKeyboardMarkup()
             if u['xp'] >= RAID_COST: 
                 m.add(types.InlineKeyboardButton(f"🚀 НАЧАТЬ (-{RAID_COST} XP)", callback_data="raid_start"))
             m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
             menu_update(call, f"<b>🌑 НУЛЕВОЙ СЛОЙ</b>\n\nВход: <b>{RAID_COST} XP</b>\nТвой заряд: {u['xp']} XP", m)

        elif call.data == "raid_start":
             # Фикс кнопки начать: Инициализация + Первый шаг
             if u['xp'] < RAID_COST: return
             alive, msg, riddle, u_new, ev_type = logic.raid_step_logic(uid)
             if alive:
                 if riddle:
                     active_riddles[uid] = riddle['correct']
                     menu_update(call, msg, kb.riddle_keyboard(riddle['options']))
                 else:
                     has_key = db.get_item_count(uid, 'master_key') > 0
                     menu_update(call, msg, kb.raid_action_keyboard(RAID_STEP_COST, ev_type, has_key))

        elif call.data == "raid_step" or call.data == "raid_open_chest":
             ans = 'open_chest' if call.data == "raid_open_chest" else None
             alive, msg, riddle, u_new, ev_type = logic.raid_step_logic(uid, answer=ans)
             if not alive:
                 menu_update(call, msg, kb.back_button())
             else:
                 if riddle:
                     active_riddles[uid] = riddle['correct']
                     menu_update(call, msg, kb.riddle_keyboard(riddle['options']))
                 else:
                     has_key = db.get_item_count(uid, 'master_key') > 0
                     menu_update(call, msg, kb.raid_action_keyboard(RAID_STEP_COST, ev_type, has_key))

        elif call.data.startswith("r_check_"):
             ans = call.data.replace("r_check_", "")
             correct = active_riddles.get(uid, "")
             if ans in correct:
                 bot.answer_callback_query(call.id, "✅ ВЕРНО! +15 XP")
                 db.add_xp_to_user(uid, 15)
             else:
                 bot.answer_callback_query(call.id, "❌ ОШИБКА! Удар током.", show_alert=True)
                 conn = db.get_db_connection()
                 with conn.cursor() as cur: cur.execute("UPDATE raid_sessions SET signal = signal - 20 WHERE uid = %s", (uid,)); conn.commit()
                 conn.close()
             handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data == "raid_extract":
             conn = db.get_db_connection()
             with conn.cursor(cursor_factory=RealDictCursor) as cur:
                 cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
                 res = cur.fetchone()
                 xp_gain = res['buffer_xp'] if res else 0
                 coin_gain = res['buffer_coins'] if res else 0
                 cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
                 conn.commit()
             conn.close()
             gain, is_up, achs = logic.process_xp_logic(uid, xp_gain, source='raid')
             db.update_user(uid, biocoin=u['biocoin'] + coin_gain)
             menu_update(call, f"🚁 <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n\n⚡️ +{gain} XP\n🪙 +{coin_gain} BC", kb.back_button())
             broadcast_progress(uid, is_up, achs)

        # --- 3. МАГАЗИН И ИНВЕНТАРЬ ---
        elif call.data == "shop":
            menu_update(call, SHOP_FULL + f"\n\n💰 Баланс: <b>{u['biocoin']} BC</b>", kb.shop_menu(u))
        
        elif call.data.startswith("buy_"):
            item = call.data.replace("buy_", "")
            price = PRICES.get(item, EQUIPMENT_DB.get(item, {}).get('price', 99999))
            currency = 'xp' if item in ['cryo', 'accel', 'decoder'] else 'biocoin'
            
            can_buy = False
            if currency == 'xp' and u['xp'] >= price: can_buy = True
            elif currency == 'biocoin' and u['biocoin'] >= price: can_buy = True
            
            if can_buy:
                if item not in ['cryo', 'accel', 'decoder'] and not db.add_item(uid, item):
                    bot.answer_callback_query(call.id, "🎒 НЕТ МЕСТА!", show_alert=True)
                    return
                if currency == 'xp': db.update_user(uid, xp=u['xp']-price)
                else: db.update_user(uid, biocoin=u['biocoin']-price)
                
                # Эффекты
                if item == 'cryo': db.update_user(uid, cryo=u['cryo']+1)
                elif item == 'accel': db.update_user(uid, accel_exp=int(time.time())+86400)
                elif item == 'decoder': db.update_user(uid, decoder=1)
                
                bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item}")
                handle_query(type('obj', (object,), {'data': 'shop', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
            else: bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО СРЕДСТВ", show_alert=True)

        elif call.data == "inventory":
            items = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            stats, _ = logic.get_user_stats(uid)
            txt = f"🎒 <b>ИНВЕНТАРЬ ({len(items)}/{INVENTORY_LIMIT})</b>\n\n"
            txt += f"⚔️ АТАКA: {stats['atk']}\n🛡 ЗАЩИТА: {stats['def']}\n🍀 УДАЧА: {stats['luck']}\n\n"
            txt += "<i>Выбери предмет, чтобы надеть или снять его.</i>"
            menu_update(call, txt, kb.inventory_menu(items, equipped))

        elif call.data.startswith("equip_"):
            db.equip_item(uid, call.data.replace("equip_", ""), EQUIPMENT_DB.get(call.data.replace("equip_", ""), {}).get('slot'))
            handle_query(type('obj', (object,), {'data': 'inventory', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data.startswith("unequip_"):
            if db.unequip_item(uid, call.data.replace("unequip_", "")):
                handle_query(type('obj', (object,), {'data': 'inventory', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
            else: bot.answer_callback_query(call.id, "🎒 НЕТ МЕСТА!", show_alert=True)

        # --- 4. ДНЕВНИК И АРХИВ ---
        elif call.data == "diary_menu":
            menu_update(call, "📓 <b>ЦЕНТРАЛЬНЫЙ АРХИВ</b>\n\nТвои мысли и купленные знания.", kb.diary_menu())

        elif call.data == "diary_new":
            user_states[uid] = "diary_wait"
            bot.send_message(uid, "📝 <b>ВВОД ИНСАЙТА:</b>\nПришли свою мысль следующим сообщением.", parse_mode="HTML")

        elif call.data.startswith("diary_read_"):
            page = int(call.data.replace("diary_read_", ""))
            entries = db.get_diary_entries(uid, limit=100)
            if not entries:
                menu_update(call, "<i>Твой дневник пока пуст...</i>", kb.back_button())
                return
            entry = entries[page]
            date_str = entry['created_at'].strftime('%d.%m.%y %H:%M')
            txt = f"📖 <b>ЗАПИСЬ #{page+1}</b>\n📅 {date_str}\n\n{entry['entry']}"
            menu_update(call, txt, kb.diary_read_nav(page, len(entries)))

        elif call.data == "diary_archive":
            if u['xp'] >= ARCHIVE_COST:
                db.update_user(uid, xp=u['xp']-ARCHIVE_COST)
                prots = db.get_archived_protocols(uid)
                txt = "💾 <b>АРХИВ ПРОТОКОЛОВ</b>\n\n"
                if not prots: txt += "<i>Архив пуст. Изучай новые протоколы через Синхронизацию.</i>"
                else:
                    for p in prots: txt += f"🔹 {p['text'][:150]}...\n\n"
                menu_update(call, txt, kb.back_button())
            else: bot.answer_callback_query(call.id, f"❌ Нужно {ARCHIVE_COST} XP", show_alert=True)

        # --- 5. СОЦИУМ ---
        elif call.data == "profile":
            stats, _ = logic.get_user_stats(uid)
            perc, xp_need = logic.get_level_progress_stats(u)
            p_bar = kb.get_progress_bar(perc, 100)
            msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\n"
                   f"📊 LVL {u['level']} | {p_bar} ({perc}%)\n"
                   f"💡 До апа: {xp_need} XP\n\n"
                   f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\n"
                   f"🔋 Энергия: {u['xp']} | 🪙 BioCoins: {u['biocoin']}")
            menu_update(call, msg, kb.back_button())

        elif call.data == "leaderboard":
            top = db.get_leaderboard()
            txt = "🏆 <b>ТОП-10 АРХИТЕКТОРОВ</b>\n\n"
            for i, r in enumerate(top, 1):
                txt += f"{i}. {r['first_name']} — <code>{r['xp']} XP</code> (Lvl {r['level']})\n"
            menu_update(call, txt, kb.back_button())

        elif call.data == "referral":
            refs = db.get_referrals_stats(uid)
            txt = f"{SYNDICATE_FULL}\n\n📊 <b>ОТЧЕТ:</b>\n"
            if not refs: txt += "<i>У тебя пока нет агентов.</i>"
            else:
                for r in refs:
                    txt += f"• {r['first_name']} (Lvl {r['level']}) | +{r['ref_profit_xp']} XP | +{r['ref_profit_coins']} BC\n"
            txt += f"\n🔗 Ссылка:\n<code>https://t.me/{BOT_USERNAME}?start={uid}</code>"
            menu_update(call, txt, kb.back_button())

        elif call.data == "guide":
            menu_update(call, GUIDE_FULL, kb.back_button())

        # --- 6. ADMIN PANEL ---
        elif call.data == "admin_panel" and str(uid) == str(ADMIN_ID):
            menu_update(call, "⚡️ <b>GOD MODE CONSOLE</b>", kb.admin_keyboard())

        elif call.data == "admin_sql":
            user_states[uid] = "admin_sql"
            bot.send_message(uid, "⌨️ <b>SQL INPUT:</b>")
        
        elif call.data == "admin_broadcast":
            user_states[uid] = "admin_broadcast"
            bot.send_message(uid, "📢 <b>TEXT FOR ALL:</b>")

        elif call.data == "admin_dm":
            user_states[uid] = "admin_dm_id"
            bot.send_message(uid, "✉️ <b>USER ID:</b>")

        elif call.data == "admin_give_res":
            user_states[uid] = "admin_give_res"
            bot.send_message(uid, "💰 <b>ID XP COINS:</b>")

        elif call.data == "admin_give_item_menu":
            menu_update(call, "🎁 <b>SELECT ITEM:</b>", kb.admin_item_select())

        elif call.data.startswith("adm_give_"):
            item = call.data.replace("adm_give_", "")
            user_states[uid] = f"admin_give_item_id:{item}"
            bot.send_message(uid, f"⌨️ <b>ID FOR {item}:</b>")

        elif call.data == "back":
            menu_update(call, f"<code>{random.choice(WELCOME_VARIANTS)}</code>", kb.main_menu(u))

        bot.answer_callback_query(call.id)
    except Exception as e: print(f"/// ERR: {e}")

# =============================================================
# ✉️ ОБРАБОТЧИК ТЕКСТА (INPUT)
# =============================================================

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def text_input_handler(m):
    uid = m.from_user.id
    state = user_states[uid]
    
    if state == "diary_wait":
        db.add_diary_entry(uid, m.text[:1000])
        logic.process_xp_logic(uid, 5)
        bot.send_message(uid, "✅ <b>ИНСАЙТ СОХРАНЕН.</b>\n+5 XP", parse_mode="HTML", reply_markup=kb.main_menu(db.get_user(uid)))
        del user_states[uid]

    elif str(uid) == str(ADMIN_ID):
        if state == "admin_sql":
            res = db.admin_exec_query(m.text)
            bot.send_message(uid, f"📊 <b>SQL RESULT:</b>\n<code>{res}</code>", parse_mode="HTML")
        elif state == "admin_broadcast":
            users = db.admin_exec_query("SELECT uid FROM users")
            # users придет как строка из-за admin_exec_query, поэтому лучше сделать через db напрямую
            conn = db.get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT uid FROM users")
                all_u = cur.fetchall()
            conn.close()
            count = 0
            for usr in all_u:
                try: bot.send_message(usr[0], f"📢 <b>ОПОВЕЩЕНИЕ:</b>\n\n{m.text}", parse_mode="HTML"); count += 1
                except: pass
            bot.send_message(uid, f"✅ Разослано: {count}")
        elif state == "admin_dm_id":
            user_states[uid] = f"admin_dm_msg:{m.text}"
            bot.send_message(uid, "✉️ <b>MESSAGE TEXT:</b>")
            return
        elif state.startswith("admin_dm_msg:"):
            target = state.split(":")[1]
            try: bot.send_message(target, f"📩 <b>СООБЩЕНИЕ ОТ АДМИНИСТРАЦИИ:</b>\n\n{m.text}", parse_mode="HTML"); bot.send_message(uid, "✅ OK")
            except: bot.send_message(uid, "❌ FAIL")
        elif state == "admin_give_res":
            try:
                tid, xp, bc = m.text.split()
                db.add_xp_to_user(int(tid), int(xp))
                db.update_user(int(tid), biocoin=db.get_user(int(tid))['biocoin'] + int(bc))
                bot.send_message(uid, "✅ OK")
            except: bot.send_message(uid, "❌ ERR (ID XP BC)")
        elif state.startswith("admin_give_item_id:"):
            item = state.split(":")[1]
            if db.add_item(int(m.text), item): bot.send_message(uid, "✅ OK")
            else: bot.send_message(uid, "❌ FAIL")

        if uid in user_states: del user_states[uid]


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
