from modules.services.utils import safe_answer_callback
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
import re
from telebot import types

# Helper for Shadow Broker (Middleware-ish)
def handle_raid_action(call, uid, action_args=None, custom_success_callback=None, text_prefix=""):
    import traceback
    import threading
    from telebot import types

    if action_args is None: action_args = {}

    # NEW: Visual feedback in message body instead of blocking the only allowed callback answer
    try:
        # Prepend scanning status to current message
        current_text = call.message.caption or call.message.text or ""
        # Clean previous tags if any
        clean_text = re.sub(r'<code>\[ .*? \]</code>\n\n', '', current_text)
        loading_text = f"<code>[ СИСТЕМНОЕ СКАНЕРОВАНИЕ СЕКТОРА... ]</code>\n\n{clean_text}"

        if call.message.content_type == 'photo':
            bot.edit_message_caption(caption=loading_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
        else:
            bot.edit_message_text(text=loading_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=call.message.reply_markup, parse_mode="HTML")
    except:
        pass

    def _worker():
        try:
            res, txt, extra, new_u, etype, cost = process_raid_step(uid, **action_args)
        except Exception as e:
            print(f"RAID ACTION ERROR: {e}")
            traceback.print_exc()
            try: safe_answer_callback(bot, call.id, "⚠️ ОШИБКА. Попробуйте позже.", show_alert=True)
            except: pass
            return

        if not res:
            if txt == "no_key":
                 try: safe_answer_callback(bot, call.id, "⚠️ ОШИБКА ДОСТУПА: Ключ не найден.", show_alert=True)
                 except: pass
            elif etype == "death":
                 if extra and extra.get("death_reason"):
                      try: safe_answer_callback(bot, call.id, strip_html(extra["death_reason"]), show_alert=True)
                      except: pass
                 menu_update(call, txt, kb.back_button())
            else:
                 try: safe_answer_callback(bot, call.id, strip_html(txt), show_alert=True)
                 except: pass
            return

        # Success
        alert_handled = False
        if custom_success_callback:
            alert_handled = custom_success_callback(call, uid, extra)

        if not alert_handled:
            alert = extra.get("alert") if extra else None
            if alert:
                 try: safe_answer_callback(bot, call.id, strip_html(alert), show_alert=True)
                 except: pass
            else:
                 # Must answer anyway to stop the spinner
                 try: safe_answer_callback(bot, call.id)
                 except: pass
        else:
            # Spinner was likely answered in callback
            pass

        full_text = text_prefix + txt
        consumables = get_consumables(uid)
        riddle_opts = extra["options"] if etype == "riddle" and extra else []
        image_url = extra.get("image") if extra else None
        if not image_url: image_url = get_menu_image(new_u)
        has_spike = extra.get("has_data_spike", False) if extra else False

        markup = kb.riddle_keyboard(riddle_opts) if etype == "riddle" else kb.raid_action_keyboard(cost, etype, consumables=consumables, has_data_spike=has_spike)
        menu_update(call, full_text, markup, image_url=image_url)

    threading.Thread(target=_worker).start()

def check_sb(call):
    uid = int(call.from_user.id)
    check_daily_streak(uid)
    sb_triggered, sb_expiry = check_shadow_broker_trigger(uid)
    if sb_triggered:
        try: safe_answer_callback(bot, call.id, "🕶 ГЛИТЧ: Теневой Брокер вышел на связь!", show_alert=True)
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "get_protocol" or call.data == "get_signal")
def protocol_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    check_sb(call)

    # --- PHASE 1 RESTRICTION ---
    if u.get('onboarding_stage', 0) == 1:
        safe_answer_callback(bot, call.id, "⛔️ ДОСТУП ЗАБЛОКИРОВАН. ЗАВЕРШИТЕ ИНИЦИАЛИЗАЦИЮ.", show_alert=True)
        return

    if call.data == "get_protocol":
        accel_exp = u.get('accel_exp') or 0
        try: accel_exp = float(accel_exp)
        except: accel_exp = 0

        last_proto = u.get('last_protocol_time') or 0
        try: last_proto = float(last_proto)
        except: last_proto = 0

        # [MODULE 2] Shadow Metrics: Fast Sync (ADHD check)
        cd = COOLDOWN_ACCEL if accel_exp > time.time() else COOLDOWN_BASE
        if last_proto > 0 and time.time() - last_proto >= cd and time.time() - last_proto <= cd + 3:
            db.update_shadow_metric(uid, 'fast_sync_clicks', 1)

        if time.time() - last_proto < cd:
            rem = int((cd - (time.time() - last_proto)) / 60)
            safe_answer_callback(bot, call.id, f"⏳ Кулдаун: {rem} мин.", show_alert=True)
        else:
            safe_answer_callback(bot, call.id)
            from modules.services.glitch_system import check_micro_glitch
            from modules.services.utils import apply_zalgo_effect

            glitch = check_micro_glitch(uid, u.get('level', 1))

            proto = get_content_logic('protocol', u['path'], int(u.get('level', 1) or 1), u['decoder'] > 0)
            txt = proto['text'] if proto else "/// ДАННЫЕ ПОВРЕЖДЕНЫ."

            streak = u.get('streak', 0)
            level = u.get('level') or 1
            base_xp = config.XP_GAIN
            xp = int(base_xp * (level * 1.5) * (1 + (streak * 0.1)))

            final_img = config.MENU_IMAGES["get_protocol"]
            reward_text = ""

            if glitch:
                xp = int(xp * glitch.get('xp_modifier', 1.5))
                txt = apply_zalgo_effect(txt, 1)
                final_img = glitch.get('image', final_img)
                reward_text = f"\n\n🌀 <b>{glitch['message']}</b>"

                upd_args = {}
                if glitch.get('effect'):
                    upd_args['anomaly_buff_type'] = glitch['effect']
                    upd_args['anomaly_buff_expiry'] = int(time.time() + glitch.get('effect_duration', 3600))
                    upd_args['is_glitched'] = True

                if glitch.get('reward_item'):
                    db.add_item(uid, glitch['reward_item'], 1)
                    reward_text += f"\n📦 <b>Получен предмет:</b> {glitch['reward_item']}"

                if upd_args:
                    db.update_user(uid, **upd_args)

            db.update_user(uid, last_protocol_time=int(time.time()), xp=int(u.get('xp', 0) or 0)+xp, notified=False)
            if proto: db.save_knowledge(uid, proto.get('id', 0))

            lvl, msg = check_level_up(uid)
            if lvl:
                try: bot.send_message(uid, msg, parse_mode="HTML")
                except: pass

            new_achs = check_achievements(uid)
            if new_achs:
                for a in new_achs:
                    bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО: {a['name']}</b>\n(+{a['xp']} XP)", parse_mode="HTML")

            final_txt = f"💠 <b>СИНХРОНИЗАЦИЯ:</b>\n\n{txt}{reward_text}\n\n⚡️ +{xp} XP"
            threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()

    elif call.data == "get_signal":
        cd = COOLDOWN_SIGNAL
        last_sig = u.get('last_signal_time') or 0
        try: last_sig = float(last_sig)
        except: last_sig = 0

        if last_sig > 0 and time.time() - last_sig >= cd and time.time() - last_sig <= cd + 3:
            db.update_shadow_metric(uid, 'fast_sync_clicks', 1)

        if time.time() - last_sig < cd:
             rem = int((cd - (time.time() - last_sig)) / 60)
             safe_answer_callback(bot, call.id, f"⏳ Кулдаун: {rem} мин.", show_alert=True)
        else:
             safe_answer_callback(bot, call.id)
             from modules.services.glitch_system import check_micro_glitch
             from modules.services.utils import apply_zalgo_effect

             glitch = check_micro_glitch(uid, u.get('level', 1))

             sig = get_content_logic('signal')
             txt = sig['text'] if sig else "/// НЕТ СВЯЗИ."

             level = u.get('level') or 1
             base_xp = config.XP_SIGNAL
             xp = int(base_xp * (level * 1.5))

             final_img = config.MENU_IMAGES["get_signal"]
             reward_text = ""

             if glitch:
                 xp = int(xp * glitch.get('xp_modifier', 1.5))
                 txt = apply_zalgo_effect(txt, 1)
                 final_img = glitch.get('image', final_img)
                 reward_text = f"\n\n🌀 <b>{glitch['message']}</b>"

                 upd_args = {}
                 if glitch.get('effect'):
                     upd_args['anomaly_buff_type'] = glitch['effect']
                     upd_args['anomaly_buff_expiry'] = int(time.time() + glitch.get('effect_duration', 3600))
                     upd_args['is_glitched'] = True

                 if glitch.get('reward_item'):
                     db.add_item(uid, glitch['reward_item'], 1)
                     reward_text += f"\n📦 <b>Получен предмет:</b> {glitch['reward_item']}"

                 if upd_args:
                     db.update_user(uid, **upd_args)

             db.update_user(uid, last_signal_time=int(time.time()), xp=int(u.get('xp', 0) or 0)+xp)

             lvl, msg = check_level_up(uid)
             if lvl:
                 try: bot.send_message(uid, msg, parse_mode='HTML')
                 except: pass

             new_achs = check_achievements(uid)
             if new_achs:
                 for a in new_achs:
                     bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО: {a['name']}</b>\n(+{a['xp']} XP)", parse_mode="HTML")

             final_txt = f"📡 <b>СИГНАЛ:</b>\n\n{txt}{reward_text}\n\n⚡️ +{xp} XP"
             threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith("raid_") or call.data == "zero_layer_menu" or call.data.startswith("r_check_") or call.data == "use_admin_key")
def raid_handler(call):
    uid = int(call.from_user.id)
    import cache_db
    if cache_db.check_throttle(uid, 'raid_action'):
        try: safe_answer_callback(bot, call.id, "Обработка...", show_alert=False)
        except: pass
        return
    u = db.get_user(uid)
    check_sb(call)

    # --- PHASE 1 RESTRICTION ---
    if u.get('onboarding_stage', 0) == 1:
        safe_answer_callback(bot, call.id, "⛔️ ДОСТУП ЗАБЛОКИРОВАН. ЗАВЕРШИТЕ ИНИЦИАЛИЗАЦИЮ.", show_alert=True)
        return

    if call.data == "zero_layer_menu":
         import database as _db
         session = None
         with _db.db_cursor() as cur:
             if cur:
                 cur.execute("SELECT depth FROM raid_sessions WHERE uid=%s", (uid,))
                 session = cur.fetchone()

         if session:
             try: safe_answer_callback(bot, call.id)
             except: pass
             m = types.InlineKeyboardMarkup()
             m.add(types.InlineKeyboardButton("♻️ ПРОДОЛЖИТЬ ПОХОД", callback_data="raid_step"))
             m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
             menu_update(call, f"⚠️ <b>ВНИМАНИЕ</b>\n\nВы уже находитесь в рейде (Глубина: {session[0] if isinstance(session, tuple) else session.get('depth')}).\nВаш сигнал зафиксирован в Пустоши.", m, image_url=config.MENU_IMAGES["zero_layer_menu"])
         else:
             cost = get_raid_entry_cost(uid)
             try: safe_answer_callback(bot, call.id)
             except: pass
             menu_update(call, f"🚀 <b>---НУЛЕВОЙ СЛОЙ---</b>\nВаш текущий опыт: {int(u.get('xp', 0) or 0)}\nСтоимость входа: {cost}", kb.raid_welcome_keyboard(cost), image_url=config.MENU_IMAGES["zero_layer_menu"])

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

         def on_start_success(call, uid, extra):
             db.log_action(uid, 'raid_start', f"Depth: {start_depth}")
             entry_cost = get_raid_entry_cost(uid)
             safe_answer_callback(bot, call.id, f"📉 ПОТРАЧЕНО: {entry_cost} XP", show_alert=True)
             return True

         handle_raid_action(call, uid, {'start_depth': start_depth}, custom_success_callback=on_start_success)

    elif call.data == "raid_enter":
         def on_enter_success(call, uid, extra):
             entry_cost = get_raid_entry_cost(uid)
             safe_answer_callback(bot, call.id, f"📉 ПОТРАЧЕНО: {entry_cost} XP", show_alert=True)
             return True

         handle_raid_action(call, uid, custom_success_callback=on_enter_success)

    elif call.data == "raid_step":
         handle_raid_action(call, uid)

    elif call.data == "raid_open_chest":
         handle_raid_action(call, uid, {'answer': 'open_chest'})

    elif call.data == "raid_hack_chest":
         handle_raid_action(call, uid, {'answer': 'hack_chest'})

    elif call.data == "raid_use_battery":
         handle_raid_action(call, uid, {'answer': 'use_battery'})

    elif call.data == "raid_use_stimulator":
         handle_raid_action(call, uid, {'answer': 'use_stimulator'})

    elif call.data == "raid_use_architect_key":
         handle_raid_action(call, uid, {"answer": "use_architect_key"})

    elif call.data == "raid_extract":
         res = None
         with db.db_session() as conn:
             with conn.cursor() as cur:
                 cur.execute("SELECT buffer_xp, buffer_coins, signal FROM raid_sessions WHERE uid=%s", (uid,))
                 res = cur.fetchone()

         if res:
             from modules.services.utils import add_biocoin
             db.add_xp_to_user(uid, res[0])
             add_biocoin(uid, res[1])
             db.log_action(uid, 'raid_extract', f"XP: {res[0]}, Coins: {res[1]}")
             # [MODULE 2] Track escapes at full HP
             if res[2] and res[2] >= 80:
                 db.update_shadow_metric(uid, 'escapes_at_full_hp', 1)

         # [MODULE 2] Reset consecutive deaths on successful escape
         db.update_shadow_metric(uid, 'consecutive_deaths', -db.get_user_shadow_metrics(uid).get('consecutive_deaths', 0))

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
         handle_raid_action(call, uid, {'answer': 'claim_body'})

    elif call.data.startswith("r_check_"):
        ans = call.data.replace("r_check_", "")
        success, msg = process_riddle_answer(uid, ans)
        safe_answer_callback(bot, call.id, "Принято.")

        handle_raid_action(call, uid, text_prefix=f"{msg}\n\n")

@bot.callback_query_handler(func=lambda call: call.data.startswith("combat_"))
def combat_handler(call):
     uid = int(call.from_user.id)
     import cache_db
     if cache_db.check_throttle(uid, 'raid_action'):
         try: safe_answer_callback(bot, call.id, "Обработка...", show_alert=False)
         except: pass
         return
     check_sb(call)
     action = call.data.replace("combat_", "")

     try:
         res_type, msg, extra = process_combat_action(uid, action)
     except Exception as e:
         print(f"/// COMBAT HANDLER FATAL ERROR (UID={uid}): {e}")
         traceback.print_exc()
         try: safe_answer_callback(bot, call.id, "⚠️ SYSTEM ERROR: Combat failed.", show_alert=True)
         except: pass
         return

     # Alert with combat log
     alert_msg = strip_html(msg)
     if len(alert_msg) > 190: alert_msg = alert_msg[:190] + "..."
     try: safe_answer_callback(bot, call.id, alert_msg, show_alert=True)
     except: pass

     if res_type == 'error':
         handle_raid_action(call, uid)

     elif res_type == 'win' or res_type == 'escaped':
         handle_raid_action(call, uid, text_prefix=f"{msg}\n\n")

     elif res_type == 'death':
         if extra and extra.get('broadcast'):
             try: safe_answer_callback(bot, call.id, "💀 СИСТЕМНЫЙ НЕКРОЛОГ", show_alert=True)
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
         handle_raid_action(call, uid, text_prefix=f"{msg}\n\n")

@bot.callback_query_handler(func=lambda call: call.data.startswith("anomaly_bet_"))
def anomaly_handler(call):
    uid = int(call.from_user.id)
    import cache_db
    if cache_db.check_throttle(uid, 'raid_action'):
        try: safe_answer_callback(bot, call.id, "Обработка...", show_alert=False)
        except: pass
        return
    check_sb(call)
    bet_type = call.data.replace("anomaly_bet_", "")
    res, msg, extra = process_anomaly_bet(uid, bet_type)

    if not res: # Death
        if extra and extra.get('death_reason'):
             menu_update(call, msg, kb.back_button())
        else:
             safe_answer_callback(bot, call.id, strip_html(msg), show_alert=True)
    else:
        alert = extra.get('alert') if extra else ""
        try: safe_answer_callback(bot, call.id, strip_html(alert), show_alert=True)
        except: pass

        # Show result and continue raid
        handle_raid_action(call, uid, text_prefix=f"{msg}\n\n")

@bot.callback_query_handler(func=lambda call: call.data.startswith("decrypt_"))
def decrypt_handler(call):
    uid = int(call.from_user.id)
    check_sb(call)

    if call.data == "decrypt_menu":
        status, txt = get_decryption_status(uid)
        menu_update(call, f"🔐 <b>ДЕШИФРАТОР</b>\n\n{txt}", kb.decrypt_menu(status))

    elif call.data == "decrypt_start":
        res, msg = start_decryption(uid)
        safe_answer_callback(bot, call.id, strip_html(msg), show_alert=True)
        call.data = "decrypt_menu"
        decrypt_handler(call)

    elif call.data == "decrypt_claim":
        res, msg = claim_decrypted_cache(uid)
        if res:
            menu_update(call, msg, kb.back_button())
        else:
            safe_answer_callback(bot, call.id, strip_html(msg), show_alert=True)
