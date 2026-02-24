from modules.bot_instance import bot
import database as db
import config
import keyboards as kb
from modules.services.utils import menu_update, split_long_message
import time
import csv
import base64
import os
import zipfile
from datetime import datetime

@bot.message_handler(commands=['admin'])
def admin_command(m):
    uid = m.from_user.id
    if db.is_user_admin(uid):
        bot.send_message(uid, "⚡️ <b>GOD MODE: ACCESS GRANTED</b>", reply_markup=kb.admin_main_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel" or call.data.startswith("admin_"))
def admin_callbacks(call):
    uid = call.from_user.id

    if call.data == "admin_panel":
         if db.is_user_admin(uid):
             menu_update(call, "⚡️ <b>GOD MODE: MAIN TERMINAL</b>", kb.admin_main_menu(), image_url=config.MENU_IMAGES["admin_panel"])
         else:
             bot.answer_callback_query(call.id, "❌ ACCESS DENIED")
         return

    # --- ADMIN SUB-MENUS ---
    if call.data.startswith("admin_menu_"):
         if not db.is_user_admin(uid): return
         sub = call.data.replace("admin_menu_", "")
         if sub == "users": menu_update(call, "👥 <b>USER MANAGEMENT</b>", kb.admin_users_menu())
         elif sub == "content": menu_update(call, "📝 <b>CONTENT MANAGEMENT</b>", kb.admin_content_menu())
         elif sub == "broadcast": menu_update(call, "📢 <b>BROADCAST SYSTEMS</b>", kb.admin_broadcast_menu())
         elif sub == "system": menu_update(call, "⚙️ <b>SYSTEM TOOLS</b>", kb.admin_system_menu())

    elif call.data == "admin_guide":
         if not db.is_user_admin(uid): return
         menu_update(call, config.ADMIN_GUIDE_TEXT, kb.back_button())

    elif call.data == "admin_user_list":
         if not db.is_user_admin(uid): return
         report = db.admin_get_users_dossier()

         if len(report) > 1000:
             chunks = split_long_message(report)
             for chunk in chunks:
                 try:
                     bot.send_message(uid, chunk, parse_mode="HTML")
                 except Exception as e:
                     bot.send_message(uid, f"❌ ERROR SENDING PART: {e}")

             menu_update(call, "✅ <b>Список пользователей отправлен в чат.</b>", kb.back_button())
         else:
             menu_update(call, report, kb.back_button())

    # --- ADMIN ACTIONS (STATE SETTERS) ---
    elif call.data in ["admin_grant_admin", "admin_revoke_admin", "admin_give_res",
                       "admin_broadcast", "admin_post_channel", "admin_add_riddle",
                       "admin_add_content", "admin_add_signal", "admin_sql", "admin_dm_user",
                       "admin_reset_user", "admin_delete_user"]:
         if not db.is_user_admin(uid): return

         state_map = {
             "admin_grant_admin": "wait_grant_admin",
             "admin_revoke_admin": "wait_revoke_admin",
             "admin_give_res": "wait_give_res_id",
             "admin_broadcast": "wait_broadcast_text",
             "admin_post_channel": "wait_channel_post",
             "admin_add_riddle": "wait_add_riddle",
             "admin_add_content": "wait_add_protocol",
             "admin_add_signal": "wait_add_signal",
             "admin_sql": "wait_sql",
             "admin_dm_user": "wait_dm_user_id",
             "admin_reset_user": "wait_reset_user_id",
             "admin_delete_user": "wait_delete_user_id"
         }
         db.set_state(uid, state_map[call.data])
         msg_map = {
             "admin_grant_admin": "🆔 <b>ENTER USER ID TO PROMOTE:</b>",
             "admin_revoke_admin": "🆔 <b>ENTER USER ID TO DEMOTE:</b>",
             "admin_give_res": "🆔 <b>ENTER USER ID:</b>",
             "admin_broadcast": "📢 <b>ENTER MESSAGE TEXT (HTML Supported):</b>",
             "admin_post_channel": "📡 <b>ENTER POST TEXT (HTML Supported):</b>\nBot must be admin in channel.",
             "admin_add_riddle": "🎭 <b>ENTER RIDDLE:</b>\nFormat: Question (Ответ: Answer)",
             "admin_add_content": "💠 <b>ENTER PROTOCOL TEXT:</b>",
             "admin_add_signal": "📡 <b>ENTER SIGNAL TEXT:</b>",
             "admin_sql": "📜 <b>ENTER SQL QUERY:</b>\n⚠️ BE CAREFUL!",
             "admin_dm_user": "🆔 <b>ENTER USER ID TO DM:</b>",
             "admin_reset_user": "♻️ <b>ENTER USER ID TO RESET (XP=0, LVL=1):</b>",
             "admin_delete_user": "🗑 <b>ENTER USER ID TO PERMANENTLY DELETE:</b>\n⚠️ This action cannot be undone."
         }
         menu_update(call, msg_map[call.data], kb.back_button())

    elif call.data == "admin_give_item_menu":
         if not db.is_user_admin(uid): return
         menu_update(call, "🎁 <b>SELECT ITEM:</b>", kb.admin_item_select())

    elif call.data == "admin_summon_broker":
         if not db.is_user_admin(uid): return
         db.update_user(uid, shadow_broker_expiry=int(time.time() + 900))
         bot.answer_callback_query(call.id, "✅ БРОКЕР ПРИЗВАН (15 мин)", show_alert=True)
         # Refresh main menu if possible, but admin is deep in menu.
         # Just alert is enough.

    elif call.data == "admin_fix_inventory":
         if not db.is_user_admin(uid): return
         items = db.get_inventory(uid)
         menu_update(call, "🗑 <b>ЧИСТКА ИНВЕНТАРЯ</b>\nНажми, чтобы удалить навсегда.", kb.admin_inventory_keyboard(items))

    elif call.data.startswith("admin_del_"):
         if not db.is_user_admin(uid): return
         item_id = call.data.replace("admin_del_", "")
         db.admin_force_delete_item(uid, item_id)
         bot.answer_callback_query(call.id, f"✅ {item_id} УДАЛЕН")

         # Refresh list
         items = db.get_inventory(uid)
         menu_update(call, "🗑 <b>ЧИСТКА ИНВЕНТАРЯ</b>\nНажми, чтобы удалить навсегда.", kb.admin_inventory_keyboard(items))

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_give_"))
def admin_give_item(call):
     uid = call.from_user.id
     if not db.is_user_admin(uid): return
     item = call.data.replace("adm_give_", "")
     db.set_state(uid, f"wait_give_item_id|{item}")
     menu_update(call, f"🆔 <b>GIVING {item.upper()}\nENTER USER ID:</b>", kb.back_button())

# We need a separate handler for admin text input
# But 'bot.py' had a generic text_handler.
# We should probably put all text handling in one place or split it by state?
# Telebot doesn't easily route based on state unless we use middleware or filters.
# I'll create a specific handler for admin states.

def is_admin_state(message):
    uid = message.from_user.id
    state = db.get_state(uid)
    return state and (state.startswith("wait_") or state.startswith("admin_")) and db.is_user_admin(uid)

@bot.message_handler(func=is_admin_state, content_types=['text'])
def admin_text_handler(m):
    uid = m.from_user.id
    state = db.get_state(uid)

    if state == "wait_grant_admin":
        try:
            tid = int(m.text)
            db.set_user_admin(tid, True)
            bot.send_message(uid, f"✅ ADMIN GRANTED TO {tid}")
        except: bot.send_message(uid, "❌ INVALID ID")
        db.delete_state(uid)

    elif state == "wait_revoke_admin":
        try:
            tid = int(m.text)
            if str(tid) == str(config.ADMIN_ID):
                 bot.send_message(uid, "❌ CANNOT REVOKE OWNER")
            else:
                 db.set_user_admin(tid, False)
                 bot.send_message(uid, f"✅ ADMIN REVOKED FROM {tid}")
        except: bot.send_message(uid, "❌ INVALID ID")
        db.delete_state(uid)

    elif state == "wait_reset_user_id":
        try:
            tid = int(m.text)
            u = db.get_user(tid)
            if u:
                db.update_user(tid, xp=0, level=1)
                bot.send_message(uid, f"✅ USER {tid} RESET TO LVL 1 / 0 XP")
                try: bot.send_message(tid, "♻️ <b>АДМИНИСТРАТОР СБРОСИЛ ВАШ ПРОГРЕСС.</b>", parse_mode="HTML")
                except: pass
            else:
                bot.send_message(uid, "❌ USER NOT FOUND")
        except: bot.send_message(uid, "❌ INVALID ID / ERROR")
        db.delete_state(uid)

    elif state == "wait_delete_user_id":
        try:
            tid = int(m.text)
            u = db.get_user(tid)
            if u:
                if db.delete_user_fully(tid):
                    bot.send_message(uid, f"✅ USER {tid} PERMANENTLY DELETED")
                else:
                    bot.send_message(uid, "❌ ERROR DELETING USER")
            else:
                bot.send_message(uid, "❌ USER NOT FOUND")
        except: bot.send_message(uid, "❌ INVALID ID / ERROR")
        db.delete_state(uid)

    elif state == "wait_give_res_id":
        try:
            tid = int(m.text)
            db.set_state(uid, f"wait_give_res_val|{tid}")
            bot.send_message(uid, "💰 <b>ENTER AMOUNT:</b>\nExamples: '1000' (Coins), '500 xp' (XP)")
        except:
            bot.send_message(uid, "❌ INVALID ID")
            db.delete_state(uid)

    elif state.startswith("wait_give_res_val|"):
        tid = int(state.split("|")[1])
        try:
            val = m.text.lower().strip()
            if 'xp' in val:
                amount = int(val.replace('xp', '').strip())
                db.add_xp_to_user(tid, amount)
                bot.send_message(uid, f"✅ GAVE {amount} XP TO {tid}")
                try: bot.send_message(tid, f"👤 <b>Создатель перечислил Вам в награду {amount} XP</b>", parse_mode="HTML")
                except: pass
            else:
                amount = int(val)
                u = db.get_user(tid)
                if u:
                    db.update_user(tid, biocoin=u['biocoin'] + amount)
                    bot.send_message(uid, f"✅ GAVE {amount} BC TO {tid}")
                    try: bot.send_message(tid, f"👤 <b>Создатель перечислил Вам в награду {amount} BioCoins</b>", parse_mode="HTML")
                    except: pass
                else: bot.send_message(uid, "❌ USER NOT FOUND")
        except: bot.send_message(uid, "❌ ERROR")
        db.delete_state(uid)

    elif state.startswith("wait_give_item_id|"):
        item = state.split("|")[1]
        try:
            tid = int(m.text)
            if db.add_item(tid, item):
                bot.send_message(uid, f"✅ SENT {item} TO {tid}")
                item_name = config.ITEMS_INFO.get(item, {}).get('name', item)
                try: bot.send_message(tid, f"👤 <b>Создатель отправил Вам предмет: {item_name}</b>", parse_mode="HTML")
                except: pass
            else:
                bot.send_message(uid, "❌ INVENTORY FULL OR ERROR")
        except: bot.send_message(uid, "❌ INVALID ID")
        db.delete_state(uid)

    elif state == "wait_dm_user_id":
        try:
            tid = int(m.text)
            db.set_state(uid, f"wait_dm_text|{tid}")
            bot.send_message(uid, "✉️ <b>ENTER MESSAGE TEXT (HTML Supported):</b>")
        except:
            bot.send_message(uid, "❌ INVALID ID")
            db.delete_state(uid)

    elif state.startswith("wait_dm_text|"):
        tid = int(state.split("|")[1])
        try:
            bot.send_message(tid, f"✉️ <b>ЛИЧНОЕ СООБЩЕНИЕ ОТ АДМИНИСТРАТОРА:</b>\n\n{m.text}", parse_mode="HTML")
            bot.send_message(uid, f"✅ SENT TO {tid}")
        except Exception as e:
            bot.send_message(uid, f"❌ ERROR: {e}")
        db.delete_state(uid)

    elif state == "wait_broadcast_text":
        count = 0
        try:
            with db.db_cursor() as cur:
                cur.execute("SELECT uid FROM players")
                users = cur.fetchall()
                for row in users:
                    try:
                        bot.send_message(row[0], m.text, parse_mode="HTML")
                        count += 1
                        time.sleep(0.05)
                    except: pass
            bot.send_message(uid, f"✅ SENT TO {count} USERS")
        except Exception as e: bot.send_message(uid, f"❌ ERROR: {e}")
        db.delete_state(uid)

    elif state == "wait_channel_post":
        try:
            bot.send_message(config.CHANNEL_ID, m.text, parse_mode="HTML")
            bot.send_message(uid, f"✅ POSTED TO {config.CHANNEL_ID}")
        except Exception as e:
            bot.send_message(uid, f"❌ ERROR: {e}\nCheck if bot is admin in channel.")
        db.delete_state(uid)

    elif state == "wait_add_riddle":
        if db.admin_add_riddle_to_db(m.text):
            bot.send_message(uid, "✅ RIDDLE ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        db.delete_state(uid)

    elif state == "wait_add_protocol":
        if db.admin_add_signal_to_db(m.text, c_type='protocol'):
             bot.send_message(uid, "✅ PROTOCOL ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        db.delete_state(uid)

    elif state == "wait_add_signal":
        if db.admin_add_signal_to_db(m.text, c_type='signal'):
             bot.send_message(uid, "✅ SIGNAL ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        db.delete_state(uid)

    elif state == "wait_sql":
        res = db.admin_exec_query(m.text)
        try:
            bot.send_message(uid, f"<code>{str(res)[:4000]}</code>", parse_mode="HTML")
        except:
            bot.send_message(uid, "RESULT TOO LONG / ERROR")
        db.delete_state(uid)


# Команда для выгрузки базы
@bot.message_handler(commands=['backup_content'])
def send_content_backup(message):
    uid = message.from_user.id
    # Проверка, что это админ
    if not db.is_user_admin(uid):
        return

    bot.send_message(uid, "⏳ Начинаю сборку контента из базы...")

    filename = f"content_export_{datetime.now().strftime('%d_%m')}.csv"

    try:
        # 1. Подключаемся к базе
        with db.db_cursor() as cursor:
            if not cursor:
                bot.send_message(uid, "❌ Ошибка подключения к базе данных.")
                return

            cursor.execute("SELECT id, type, path, level, text FROM content ORDER BY id")
            rows = cursor.fetchall()

        if not rows:
             bot.send_message(uid, "⚠️ База данных пуста.")
             return

        # 2. Создаем CSV и сразу расшифровываем текст
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'type', 'path', 'level', 'text'])

            for row in rows:
                # Handle both tuple and RealDictCursor logic if necessary
                if isinstance(row, dict):
                     r_id = row['id']
                     r_type = row['type']
                     r_path = row['path']
                     r_level = row['level']
                     r_text = row['text']
                else:
                     r_id, r_type, r_path, r_level, r_text = row

                try:
                    # Расшифровываем Base64 прямо тут
                    decoded_text = base64.b64decode(r_text).decode('utf-8')
                except:
                    decoded_text = r_text # Если не вышло, оставляем как есть

                writer.writerow([r_id, r_type, r_path, r_level, decoded_text])

        # 3. Отправляем файл
        with open(filename, 'rb') as doc:
            bot.send_document(uid, doc, caption=f"✅ База выгружена! Всего строк: {len(rows)}")

    except Exception as e:
        bot.send_message(uid, f"❌ Ошибка при выгрузке: {e}")

    finally:
        # Удаляем временный файл
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

@bot.message_handler(commands=['backup_full'])
def send_full_backup(message):
    uid = message.from_user.id
    if not db.is_user_admin(uid):
        return

    bot.send_message(uid, "⏳ Начинаю полную выгрузку базы данных...")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"full_backup_{timestamp}.zip"
    temp_files = []

    try:
        tables = db.get_all_tables()
        if not tables:
            bot.send_message(uid, "⚠️ Не удалось получить список таблиц.")
            return

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_obj:
            for table in tables:
                csv_filename = f"{table}.csv"
                temp_files.append(csv_filename)
                try:
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        with db.db_cursor() as cur:
                            cur.execute(f"SELECT * FROM {table}")
                            if cur.description:
                                headers = [desc[0] for desc in cur.description]
                                writer.writerow(headers)
                                # Fetch in chunks if needed, but fetchall is simpler for now
                                writer.writerows(cur.fetchall())
                            else:
                                writer.writerow(['(Empty Table Structure)'])

                    zip_obj.write(csv_filename)
                except Exception as e:
                    bot.send_message(uid, f"⚠️ Ошибка при экспорте таблицы {table}: {e}")

        if os.path.exists(zip_filename):
            with open(zip_filename, 'rb') as doc:
                bot.send_document(uid, doc, caption=f"✅ Полный бэкап базы ({len(tables)} таблиц).")
            temp_files.append(zip_filename)
        else:
             bot.send_message(uid, "❌ Ошибка создания архива.")

    except Exception as e:
        bot.send_message(uid, f"❌ Критическая ошибка бэкапа: {e}")
    finally:
        for f in temp_files:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass
