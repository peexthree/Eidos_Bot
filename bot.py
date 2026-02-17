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

@bot.message_handler(commands=['start'])
def start_command(m):
    uid = m.from_user.id
    ref_id = m.text.split()[1] if len(m.text.split()) > 1 else None
    
    u = db.get_user(uid)
    if not u:
        db.get_db_connection().cursor().execute("INSERT INTO users (uid, username, first_name, referrer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                                                (uid, m.from_user.username, m.from_user.first_name, ref_id))
        db.get_db_connection().commit()
        if ref_id and str(ref_id) != str(uid):
            db.update_user(int(ref_id), ref_count=db.get_user(int(ref_id))['ref_count']+1)
            db.add_xp_to_user(int(ref_id), REFERRAL_BONUS)
            try: bot.send_message(int(ref_id), f"🤝 <b>НОВЫЙ АГЕНТ:</b> {m.from_user.first_name}\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
            except: pass

    # [FIXED] Принудительное создание инвентаря
    if db.get_inventory_size(uid) == 0:
        db.add_item(uid, 'rusty_knife')

    u = db.get_user(uid)
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption=random.choice(WELCOME_VARIANTS), reply_markup=kb.main_menu(u), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    try:
        # --- 1. ЭНЕРГИЯ ---
        if call.data == "get_protocol":
            cd = COOLDOWN_ACCEL if u['accel_exp'] > time.time() else COOLDOWN_BASE
            if time.time() - u['last_protocol_time'] < cd:
                rem = int(cd - (time.time() - u['last_protocol_time']))
                bot.answer_callback_query(call.id, f"⏳ Жди {rem} сек.", show_alert=True)
                return

            cat = random.choice(list(SYNC_CATEGORIES.keys()))
            txt = random.choice(SYNC_CATEGORIES[cat])

            # [FIXED] Начисление
            amt, is_up, unlocks = logic.process_xp_logic(uid, 50 + (u['level']*5))
            db.update_user(uid, last_protocol_time=int(time.time()), notified=False)
            db.save_knowledge(uid, db.get_archived_protocols(uid).__len__() + 1) # Просто счетчик для примера

            msg = f"📡 <b>СИНХРОНИЗАЦИЯ:</b>\n\n[{cat.upper()}] ... {txt}\n\n⚡️ +{amt} XP"
            if is_up: msg += f"\n🆙 <b>LEVEL UP!</b> {u['level']} -> {u['level']+1}"
            if unlocks: msg += "\n🏅 " + ", ".join(unlocks)
            
            menu_update(call, msg, kb.back_button())

        elif call.data == "get_signal":
            cd = COOLDOWN_SIGNAL if u['level'] < 8 else 150
            if time.time() - u['last_signal_time'] < cd:
                bot.answer_callback_query(call.id, "⏳ Сигнал не найден.", show_alert=True)
                return

            amt, is_up, unlocks = logic.process_xp_logic(uid, 25)
            db.update_user(uid, last_signal_time=int(time.time()))
            bot.answer_callback_query(call.id, f"⚡️ +{amt} XP", show_alert=False)
            handle_query(type('obj', (object,), {'data': 'back', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        # --- 2. РЕЙД (С ЛОГИКОЙ) ---
        elif call.data == "zero_layer_menu":
             # [FIXED] Гарантированный старт
             alive, msg, riddle, u_new, ev_type = logic.raid_step_logic(uid)
             if not alive:
                 menu_update(call, msg, kb.back_button())
             else:
                 # Если загадка
                 markup = kb.riddle_keyboard(riddle['options']) if riddle else kb.raid_action_keyboard(10, ev_type, db.get_item_count(uid, 'master_key') > 0)
                 if riddle: active_riddles[uid] = riddle['correct']
                 menu_update(call, msg, markup)

        elif call.data == "raid_step" or call.data == "raid_open_chest":
             ans = 'open_chest' if call.data == "raid_open_chest" else None
             alive, msg, riddle, u_new, ev_type = logic.raid_step_logic(uid, answer=ans)

             if not alive:
                 # Смерть или выход
                 menu_update(call, msg, kb.back_button())
             else:
                 markup = kb.riddle_keyboard(riddle['options']) if riddle else kb.raid_action_keyboard(10, ev_type, db.get_item_count(uid, 'master_key') > 0)
                 if riddle: active_riddles[uid] = riddle['correct']
                 menu_update(call, msg, markup)

        elif call.data.startswith("r_check_"):
            if uid not in active_riddles:
                menu_update(call, "⚠️ Ошибка реальности.", kb.back_button())
                return

            ans = call.data.replace("r_check_", "")
            correct = active_riddles[uid]
            del active_riddles[uid]

            if ans == correct[:20]: # Сравнение с обрезкой
                db.add_xp_to_user(uid, 100)
                bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP")
                handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
            else:
                # Наказание
                conn = db.get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE raid_sessions SET signal = GREATEST(0, signal - 25) WHERE uid = %s RETURNING signal", (uid,))
                sig = cur.fetchone()[0]
                conn.commit(); conn.close()
                bot.answer_callback_query(call.id, "❌ ОШИБКА! -25% СИГНАЛА", show_alert=True)
                handle_query(type('obj', (object,), {'data': 'raid_step', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data == "raid_extract":
            conn = db.get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
            res = cur.fetchone()
            if res:
                # [FIXED] Исправлен баг с начислением
                logic.process_xp_logic(uid, res['buffer_xp'], source='raid')
                db.update_user(uid, biocoin=u['biocoin'] + res['buffer_coins'])
                cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
                conn.commit()
                menu_update(call, f"🚁 <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n\n⚡️ +{res['buffer_xp']} XP\n🪙 +{res['buffer_coins']} BC", kb.back_button())
            else:
                menu_update(call, "⚠️ Ошибка данных.", kb.back_button())
            conn.close()

        # --- 3. ИНВЕНТАРЬ И МАГАЗИН ---
        elif call.data == "inventory":
            inv = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            menu_update(call, f"🎒 <b>РЮКЗАК ({len(inv)}/{INVENTORY_LIMIT})</b>\n\nНажми на предмет, чтобы использовать или надеть.", kb.inventory_menu(inv, equipped))

        elif call.data == "shop":
            # [FIXED] Динамическое описание товаров
            shop_text = SHOP_FULL + "\n"
            shop_text += "\n<b>🛒 ДОСТУПНЫЕ ТОВАРЫ:</b>\n"
            for k, v in EQUIPMENT_DB.items():
                shop_text += f"▪️ <b>{v['name']}</b> ({v['price']} BC)\n   <i>{v['desc']}</i>\n"

            shop_text += f"\n💰 Твой баланс: <b>{u['biocoin']} BC</b>"
            menu_update(call, shop_text, kb.shop_menu(u))

        elif call.data.startswith("buy_"):
            item = call.data.replace("buy_", "")
            price = EQUIPMENT_DB.get(item, {}).get('price', PRICES.get(item, 999999))
            
            if u['biocoin'] >= price:
                if db.add_item(uid, item):
                    db.update_user(uid, biocoin=u['biocoin'] - price, total_spent=u['total_spent'] + price)
                    bot.answer_callback_query(call.id, f"✅ КУПЛЕНО: {item}", show_alert=True)
                    handle_query(type('obj', (object,), {'data': 'shop', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
                else:
                    bot.answer_callback_query(call.id, "🎒 РЮКЗАК ПОЛОН!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ НЕДОСТАТОЧНО СРЕДСТВ", show_alert=True)

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
