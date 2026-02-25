from modules.bot_instance import bot
import database as db
import config
from config import COOLDOWN_ACCEL, COOLDOWN_BASE, COOLDOWN_SIGNAL
import keyboards as kb
from modules.services.utils import menu_update, loading_effect, get_consumables, strip_html, get_menu_image, get_menu_text
from modules.services.content import get_content_logic, check_shadow_broker_trigger, start_decryption, claim_decrypted_cache, get_decryption_status
from modules.services.user import get_user_stats, check_level_up, check_achievements, check_daily_streak
from modules.services.raid import process_raid_step, get_raid_entry_cost, process_riddle_answer, process_anomaly_bet, generate_raid_report
from modules.services.combat import process_combat_action
import time
import random
import threading
import traceback
from telebot import types

# Helper for Shadow Broker (Middleware-ish)
def check_sb(call):
    uid = call.from_user.id
    check_daily_streak(uid)
    sb_triggered, sb_expiry = check_shadow_broker_trigger(uid)
    if sb_triggered:
        try: bot.answer_callback_query(call.id, "🕶 ГЛИТЧ: Теневой Брокер вышел на связь!", show_alert=True)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "get_protocol" or call.data == "get_signal")
def protocol_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    check_sb(call)

    # --- PHASE 1 RESTRICTION ---
    if u.get('onboarding_stage', 0) == 1:
        bot.answer_callback_query(call.id, "⛔️ ДОСТУП ЗАБЛОКИРОВАН. ЗАВЕРШИТЕ ИНИЦИАЛИЗАЦИЮ.", show_alert=True)
        return

    if call.data == "get_protocol":
        cd = COOLDOWN_ACCEL if u['accel_exp'] > time.time() else COOLDOWN_BASE
        if time.time() - u['last_protocol_time'] < cd:
            rem = int((cd - (time.time() - u['last_protocol_time'])) / 60)
            bot.answer_callback_query(call.id, f"⏳ Кулдаун: {rem} мин.", show_alert=True)
        else:
            # GLITCH CHECK (Module 2)
            if random.random() < 0.05:
                glitch_xp = random.randint(50, 150)
                db.update_user(uid, last_protocol_time=int(time.time()), xp=u['xp']+glitch_xp, notified=False)
                final_txt = f"🌀 <b>СБОЙ РЕАЛЬНОСТИ (GLITCH):</b>\n\nВы попытались синхронизироваться, но попали в поток чистого хаоса.\n\n⚡️ +{glitch_xp} XP"
                threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), config.MENU_IMAGES["get_protocol"])).start()
            else:
                bot.answer_callback_query(call.id)
                proto = get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
                txt = proto['text'] if proto else "/// ДАННЫЕ ПОВРЕЖДЕНЫ. ПОПРОБУЙ ПОЗЖЕ."

                # SCALING XP FORMULA (Module 1)
                # Base_XP * (u['level'] * 1.5) * (1 + (streak * 0.1))
                streak = u.get('streak', 0)
                level = u.get('level', 1)
                base_xp = config.XP_GAIN

                xp = int(base_xp * (level * 1.5) * (1 + (streak * 0.1)))

                db.update_user(uid, last_protocol_time=int(time.time()), xp=u['xp']+xp, notified=False)
                if proto: db.save_knowledge(uid, proto.get('id', 0))

                lvl, msg = check_level_up(uid)
                if lvl:
                    try: bot.send_message(uid, msg, parse_mode="HTML")
                    except: pass

                ach_text = ""
                new_achs = check_achievements(uid)
                if new_achs:
                    for a in new_achs:
                        ach_text += f"\n🏆 <b>ДОСТИЖЕНИЕ: {a['name']}</b> (+{a['xp']} XP)"

                final_txt = f"💠 <b>СИНХРОНИЗАЦИЯ:</b>\n\n{txt}\n\n⚡️ +{xp} XP{ach_text}"
                threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), config.MENU_IMAGES["get_protocol"])).start()

    elif call.data == "get_signal":
        cd = COOLDOWN_SIGNAL
        if time.time() - u['last_signal_time'] < cd:
             rem = int((cd - (time.time() - u['last_signal_time'])) / 60)
             bot.answer_callback_query(call.id, f"⏳ Кулдаун: {rem} мин.", show_alert=True)
        else:
             # GLITCH CHECK (Module 2)
             if random.random() < 0.05:
                 glitch_xp = 50
                 db.update_user(uid, last_signal_time=int(time.time()), xp=u['xp']+glitch_xp)
                 final_txt = f"🌀 <b>СБОЙ РЕАЛЬНОСТИ (GLITCH):</b>\n\nСигнал искажен временной аномалией.\n\n⚡️ +{glitch_xp} XP"
                 threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), config.MENU_IMAGES["get_signal"])).start()
             else:
                 bot.answer_callback_query(call.id)
                 sig = get_content_logic('signal')
                 txt = sig['text'] if sig else "/// НЕТ СВЯЗИ."

                 # SCALING XP
                 level = u.get('level', 1)
                 base_xp = config.XP_SIGNAL
                 xp = int(base_xp * (level * 1.5))

                 db.update_user(uid, last_signal_time=int(time.time()), xp=u['xp']+xp)

                 lvl, msg = check_level_up(uid)
                 if lvl:
                     try: bot.send_message(uid, msg, parse_mode='HTML')
                     except: pass

                 # Check achievements
                 ach_text = ""
                 new_achs = check_achievements(uid)
                 if new_achs:
                    for a in new_achs:
                        ach_text += f"\n🏆 <b>ДОСТИЖЕНИЕ: {a['name']}</b> (+{a['xp']} XP)"

                 final_txt = f"📡 <b>СИГНАЛ ПЕРЕХВАЧЕН:</b>\n\n{txt}\n\n⚡️ +{xp} XP{ach_text}"
                 threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), config.MENU_IMAGES["get_signal"])).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("raid_") or call.data == "zero_layer_menu" or call.data.startswith("r_check_") or call.data == "use_admin_key")
def raid_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    check_sb(call)

    # --- PHASE 1 RESTRICTION ---
    if u.get('onboarding_stage', 0) == 1:
        bot.answer_callback_query(call.id, "⛔️ ДОСТУП ЗАБЛОКИРОВАН. ЗАВЕРШИТЕ ИНИЦИАЛИЗАЦИЮ.", show_alert=True)
        return

    if call.data == "zero_layer_menu":
         cost = get_raid_entry_cost(uid)
         try: bot.answer_callback_query(call.id)
         except: pass
         menu_update(call, f"🚀 <b>---НУЛЕВОЙ СЛОЙ---</b>\nВаш текущий опыт: {u['xp']}\nСтоимость входа: {cost}", kb.raid_welcome_keyboard(cost), image_url=config.MENU_IMAGES["zero_layer_menu"])

    elif call.data == "raid_select_depth":
         cost = get_raid_entry_cost(uid)
         max_depth = u.get('max_depth', 0)
         menu_update(call, f"🚀 <b>ТОЧКА ВХОДА</b>\n\nВыберите глубину погружения.\nСтоимость: {cost} XP", kb.raid_depth_selection_menu(max_depth, cost))

    elif call.data.startswith("raid_start_"):
         val = call.data.replace("raid_start_", "")
         start_depth = 0

         if "range_" in val:
             parts = val.replace("range_", "").split("_")
             min_d = int(parts[0])
             max_d = int(parts[1])
             start_depth = random.randint(min_d, max_d)
         else:
             start_depth = int(val)

         try:
             res, txt, extra, new_u, etype, cost = process_raid_step(uid, start_depth=start_depth)
         except Exception as e:
             print(f"RAID START ERROR: {e}")
             bot.answer_callback_query(call.id, "⚠️ ОШИБКА РЕЙДА. Попробуйте позже.", show_alert=True)
             return

         if res:
             db.log_action(uid, 'raid_start', f"Depth: {start_depth}")
             entry_cost = get_raid_entry_cost(uid)
             bot.answer_callback_query(call.id, f"📉 ПОТРАЧЕНО: {entry_cost} XP", show_alert=True)
             consumables = get_consumables(uid)
         else:
             bot.answer_callback_query(call.id, txt, show_alert=True)
             return

         riddle_opts = extra['options'] if etype == 'riddle' and extra else []
         image_url = extra.get('image') if extra else None
         has_spike = extra.get('has_data_spike', False) if extra else False
         markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
         menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_enter":
         try:
             res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         except Exception as e:
             print(f"RAID ENTER ERROR: {e}")
             bot.answer_callback_query(call.id, "⚠️ ОШИБКА ВХОДА. Попробуйте позже.", show_alert=True)
             return

         if res:
             entry_cost = get_raid_entry_cost(uid)
             bot.answer_callback_query(call.id, f"📉 ПОТРАЧЕНО: {entry_cost} XP", show_alert=True)
             consumables = get_consumables(uid)
         else:
             bot.answer_callback_query(call.id, txt, show_alert=True)
             return

         riddle_opts = extra['options'] if etype == 'riddle' and extra else []
         image_url = extra.get('image') if extra else None
         has_spike = extra.get('has_data_spike', False) if extra else False
         markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
         menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_step":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         if not res:
             if etype == 'death' and extra and extra.get('death_reason'):
                  try: bot.answer_callback_query(call.id, extra['death_reason'], show_alert=True)
                  except: pass
             menu_update(call, txt, kb.back_button())
         else:
             if extra and extra.get('alert'):
                  try: bot.answer_callback_query(call.id, extra['alert'], show_alert=True)
                  except: bot.answer_callback_query(call.id)
             else:
                  try: bot.answer_callback_query(call.id)
                  except: pass

             consumables = get_consumables(uid)
             riddle_opts = extra['options'] if etype == 'riddle' and extra else []
             image_url = extra.get('image') if extra else None
             has_spike = extra.get('has_data_spike', False) if extra else False
             markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
             menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_open_chest":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid, answer='open_chest')
         if not res:
             if txt == "no_key":
                 bot.answer_callback_query(call.id, "⚠️ ОШИБКА ДОСТУПА: Ключ не найден.", show_alert=True)
             else:
                 bot.answer_callback_query(call.id, txt, show_alert=True)
         else:
             alert_txt = f"🔓 СИСТЕМА РАЗБЛОКИРОВАНА. Получено: {extra.get('alert', '')}" if extra else "🔓 СИСТЕМА РАЗБЛОКИРОВАНА"
             bot.answer_callback_query(call.id, alert_txt, show_alert=True)
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             has_spike = extra.get('has_data_spike', False) if extra else False
             markup = kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
             menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_hack_chest":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid, answer='hack_chest')
         if not res:
             bot.answer_callback_query(call.id, txt, show_alert=True)
             # Refresh menu to show failure state if needed, or just alert
             # If failure means "chest remains locked", we should refresh the keyboard probably?
             # But usually process_raid_step returns False only for errors or hard blocks.
             # If hack fails, process_raid_step should return True with "Hack Failed" text and next state?
             # Let's assume process_raid_step handles it. If False, it's an error.
         else:
             alert_txt = extra.get('alert', 'Взлом завершен') if extra else 'Взлом завершен'
             bot.answer_callback_query(call.id, alert_txt, show_alert=True)
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             has_spike = extra.get('has_data_spike', False) if extra else False
             markup = kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
             menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_use_battery":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid, answer='use_battery')
         if not res:
             bot.answer_callback_query(call.id, txt, show_alert=True)
         else:
             alert_txt = extra.get('alert', 'Батарея использована') if extra else 'Батарея использована'
             bot.answer_callback_query(call.id, alert_txt, show_alert=True)
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             markup = kb.raid_action_keyboard(cost, etype, consumables=consumables)
             menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "raid_use_stimulator":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid, answer='use_stimulator')
         if not res:
             bot.answer_callback_query(call.id, txt, show_alert=True)
         else:
             alert_txt = extra.get('alert', 'Стимулятор использован') if extra else 'Стимулятор использован'
             bot.answer_callback_query(call.id, alert_txt, show_alert=True)
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             markup = kb.raid_action_keyboard(cost, etype, consumables=consumables)
             menu_update(call, txt, markup, image_url=image_url)

    elif call.data == "use_admin_key":
         bot.answer_callback_query(call.id, "🟠 КЛЮЧ АРХИТЕКТОРА:\n\nЭтот артефакт пульсирует странной энергией.\nОн не имеет видимого применения в этой версии реальности.\n\n...пока что.", show_alert=True)

    elif call.data == "raid_extract":
         with db.db_session() as conn:
             with conn.cursor() as cur:
                 cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid=%s", (uid,))
                 res = cur.fetchone()
                 if res:
                     db.add_xp_to_user(uid, res[0])
                     db.update_user(uid, biocoin=u['biocoin'] + res[1])
                     db.log_action(uid, 'raid_extract', f"XP: {res[0]}, Coins: {res[1]}")

         lvl, msg = check_level_up(uid)
         if lvl:
             try: bot.send_message(uid, msg, parse_mode="HTML")
             except: pass

         # Process buffered items
         with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
              cur.execute("SELECT buffer_items FROM raid_sessions WHERE uid=%s", (uid,))
              res_items = cur.fetchone()
              if res_items and res_items['buffer_items']:
                  item_list = res_items['buffer_items'].split(',')
                  for itm in item_list:
                      if itm: db.add_item(uid, itm)

         with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
              cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
              s = cur.fetchone()

         report = generate_raid_report(uid, s, success=True)

         # --- STATS: RAID DONE & PERFECT ---
         db.increment_user_stat(uid, 'raids_done')
         if s['signal'] >= 100:
             db.increment_user_stat(uid, 'perfect_raids')

         db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
         menu_update(call, report, kb.back_button(), image_url=config.RAID_EVENT_IMAGES.get('evacuation'))

    elif call.data == "raid_claim_body":
         res, txt, extra, new_u, etype, cost = process_raid_step(uid, answer='claim_body')
         if res:
             alert = extra.get('alert') if extra else "Забрано"
             bot.answer_callback_query(call.id, alert, show_alert=True)
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             menu_update(call, txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)
         else:
             bot.answer_callback_query(call.id, txt, show_alert=True)

    elif call.data.startswith("r_check_"):
        ans = call.data.replace("r_check_", "")
        success, msg = process_riddle_answer(uid, ans)
        bot.answer_callback_query(call.id, "Принято.")

        res, txt, extra, new_u, etype, cost = process_raid_step(uid)
        full_txt = f"{msg}\n\n{txt}"
        consumables = get_consumables(uid)
        riddle_opts = extra['options'] if etype == 'riddle' and extra else []
        image_url = extra.get('image') if extra else None
        markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables)
        menu_update(call, full_txt, markup, image_url=image_url)

@bot.callback_query_handler(func=lambda call: call.data.startswith("combat_"))
def combat_handler(call):
     uid = call.from_user.id
     check_sb(call)
     action = call.data.replace("combat_", "")

     try:
         res_type, msg, extra = process_combat_action(uid, action)
     except Exception as e:
         print(f"/// COMBAT HANDLER FATAL ERROR (UID={uid}): {e}")
         traceback.print_exc()
         try: bot.answer_callback_query(call.id, "⚠️ SYSTEM ERROR: Combat failed.", show_alert=True)
         except: pass
         return

     # Alert with combat log
     alert_msg = strip_html(msg)
     if len(alert_msg) > 190: alert_msg = alert_msg[:190] + "..."
     try: bot.answer_callback_query(call.id, alert_msg, show_alert=True)
     except: pass

     if res_type == 'error':
         res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         if res:
             consumables = get_consumables(uid)
             image_url = extra.get('image') if extra else None
             markup = kb.raid_action_keyboard(cost, etype, consumables=consumables)
             menu_update(call, txt, markup, image_url=image_url)
         else: menu_update(call, "Ошибка синхронизации.", kb.back_button())

     elif res_type == 'win':
         res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         full_txt = f"{msg}\n\n{txt}"
         consumables = get_consumables(uid)
         image_url = extra.get('image') if extra else None
         if not image_url: image_url = get_menu_image(new_u)
         menu_update(call, full_txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)

     elif res_type == 'escaped':
         res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         full_txt = f"{msg}\n\n{txt}"
         consumables = get_consumables(uid)
         image_url = extra.get('image') if extra else None
         if not image_url: image_url = get_menu_image(new_u)
         menu_update(call, full_txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)

     elif res_type == 'death':
         if extra and extra.get('broadcast'):
             try: bot.answer_callback_query(call.id, "💀 СИСТЕМНЫЙ НЕКРОЛОГ", show_alert=True)
             except: pass

             try:
                 active_threshold = int(time.time() - 86400)
                 with db.db_cursor() as cur:
                     cur.execute("""
                         SELECT uid FROM players
                         WHERE uid != %s
                         AND (last_raid_date >= CURRENT_DATE - 1 OR last_protocol_time >= %s)
                         ORDER BY last_raid_date DESC
                         LIMIT 50
                     """, (uid, active_threshold))

                     for row in cur.fetchall():
                         try:
                             bot.send_message(row[0], extra['broadcast'], parse_mode="HTML")
                             time.sleep(0.05)
                         except: pass
             except Exception as e:
                 print(f"Broadcast error: {e}")

         menu_update(call, msg, kb.back_button())

     elif res_type == 'combat':
         res, txt, extra, new_u, etype, cost = process_raid_step(uid)
         full_txt = f"{msg}\n\n{txt}"
         consumables = get_consumables(uid)
         image_url = extra.get('image') if extra else None
         markup = kb.raid_action_keyboard(cost, 'combat', consumables=consumables)
         menu_update(call, full_txt, markup, image_url=image_url)

@bot.callback_query_handler(func=lambda call: call.data.startswith("anomaly_bet_"))
def anomaly_handler(call):
    uid = call.from_user.id
    check_sb(call)
    bet_type = call.data.replace("anomaly_bet_", "")
    res, msg, extra = process_anomaly_bet(uid, bet_type)

    if not res: # Death
        if extra and extra.get('death_reason'):
             menu_update(call, msg, kb.back_button())
        else:
             bot.answer_callback_query(call.id, msg, show_alert=True)
    else:
        alert = extra.get('alert') if extra else ""
        try: bot.answer_callback_query(call.id, alert, show_alert=True)
        except: pass

        # Show result and continue raid
        res_raid, txt, extra_raid, new_u, etype, cost = process_raid_step(uid)
        full_txt = f"{msg}\n\n{txt}"
        consumables = get_consumables(uid)
        image_url = extra_raid.get('image') if extra_raid else None
        markup = kb.raid_action_keyboard(cost, etype, consumables=consumables)
        menu_update(call, full_txt, markup, image_url=image_url)

@bot.callback_query_handler(func=lambda call: call.data.startswith("decrypt_"))
def decrypt_handler(call):
    uid = call.from_user.id
    check_sb(call)

    if call.data == "decrypt_menu":
        status, txt = get_decryption_status(uid)
        menu_update(call, f"🔐 <b>ДЕШИФРАТОР</b>\n\n{txt}", kb.decrypt_menu(status))

    elif call.data == "decrypt_start":
        res, msg = start_decryption(uid)
        bot.answer_callback_query(call.id, msg, show_alert=True)
        call.data = "decrypt_menu"
        decrypt_handler(call)

    elif call.data == "decrypt_claim":
        res, msg = claim_decrypted_cache(uid)
        if res:
            menu_update(call, msg, kb.back_button())
        else:
            bot.answer_callback_query(call.id, msg, show_alert=True)
