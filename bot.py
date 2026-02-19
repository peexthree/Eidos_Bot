import traceback
import telebot
from telebot import types
import config
from config import *
import database as db
import logic
import keyboards as kb
import time
import threading
import flask
import os
import sys
import random
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

# =============================================================
# ⚙️ НАСТРОЙКИ
# =============================================================

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN environment variable is not set.")
    # sys.exit(1)

WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
# ADMIN_ID loaded from config

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

user_states = {}

# =============================================================
# 🛠 УТИЛИТЫ UI
# =============================================================

def get_consumables(uid):
    inv = db.get_inventory(uid)
    cons = {}
    for i in inv:
        if i['item_id'] in ['battery', 'neural_stimulator', 'emp_grenade', 'stealth_spray', 'memory_wiper']:
            cons[i['item_id']] = i['quantity']
    return cons

def get_menu_text(u):
    return random.choice(WELCOME_VARIANTS)

def get_menu_image(u):
    p = u.get("path", "unknown")
    if p == "money": return MENU_IMAGE_URL_MONEY
    elif p == "mind": return MENU_IMAGE_URL_MIND
    elif p == "tech": return MENU_IMAGE_URL_TECH
    return MENU_IMAGE_URL

def menu_update(call, text, markup=None, image_url=None):
    try:
        if image_url:
            media = types.InputMediaPhoto(image_url, caption=text, parse_mode="HTML")
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            if call.message.content_type == "photo":
                 bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
            else:
                 bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"/// MENU UPDATE ERR: {e}")
        try:
            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        except: pass

def loading_effect(chat_id, message_id, final_text, final_kb):
    steps = ["▪️▫️▫️▫️▫️ 0%", "▪️▪️▫️▫️▫️ 25%", "▪️▪️▪️▫️▫️ 50%", "▪️▪️▪️▪️▫️ 75%", "▪️▪️▪️▪️▪️ 100%"]
    try:
        for s in steps:
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=f"<code>/// DOWNLOAD: {s}</code>", parse_mode="HTML")
            except:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"<code>/// DOWNLOAD: {s}</code>", parse_mode="HTML")
            time.sleep(0.3)
        try:
             bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=final_text, reply_markup=final_kb, parse_mode="HTML")
        except:
             bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=final_text, reply_markup=final_kb, parse_mode="HTML")
    except:
        try:
            bot.send_message(chat_id, final_text, reply_markup=final_kb, parse_mode="HTML")
        except: pass

# =============================================================
# 👋 СТАРТ
# =============================================================

@bot.message_handler(commands=['hack_random'])
def hack_command(m):
    uid = m.from_user.id
    try:
        msg = logic.perform_hack(uid)
        bot.send_message(uid, msg, parse_mode='HTML')
    except Exception as e:
        bot.send_message(uid, f"⚠️ ERROR: {e}")

@bot.message_handler(commands=['start'])
def start_handler(m):
    uid = m.from_user.id
    ref = m.text.split()[1] if len(m.text.split()) > 1 else None
    
    if not db.get_user(uid):
        username = m.from_user.username or "Anon"
        first_name = m.from_user.first_name or "User"
        db.add_user(uid, username, first_name, ref)
        if ref:
             db.add_xp_to_user(int(ref), REFERRAL_BONUS)
             try: bot.send_message(int(ref), f"👤 <b>НОВЫЙ АГЕНТ:</b> {first_name}\n+{REFERRAL_BONUS} XP")
             except: pass

        bot.send_message(uid, f"/// EIDOS v8.0 INITIALIZED\nID: {uid}\n\nДобро пожаловать в Систему, Искатель.", parse_mode="HTML")
        msg = ("🧬 <b>ВЫБОР ПУТИ (БЕСПЛАТНО)</b>\n\n"
               "Ты должен выбрать свою специализацию, чтобы выжить.\n\n"
               "🏦 <b>МАТЕРИЯ:</b> +20% Монет в Рейдах.\n"
               "🧠 <b>РАЗУМ:</b> +10 Защиты.\n"
               "🤖 <b>ТЕХНО:</b> +10 Удачи.")
        bot.send_message(uid, msg, reply_markup=kb.path_selection_keyboard(), parse_mode="HTML")
    else:
        u = db.get_user(uid)
        bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_command(m):
    uid = m.from_user.id
    if db.is_user_admin(uid):
        bot.send_message(uid, "⚡️ <b>GOD MODE: ACCESS GRANTED</b>", reply_markup=kb.admin_main_menu(), parse_mode="HTML")

# =============================================================
# 🎮 ОБРАБОТЧИК КНОПОК
# =============================================================
# ==========================================
# СЕКРЕТНЫЙ ИНСТРУМЕНТ АРХИТЕКТОРА: FILE_ID
# ==========================================
@bot.message_handler(content_types=['photo'])
def grab_file_id(message):
    # Берем самую качественную версию картинки (она всегда последняя в списке)
    file_id = message.photo[-1].file_id
    
    # Формируем ответ, делаем ID моноширинным, чтобы он копировался по клику
    text = (
        "✅ **Медиа-файл загружен в кэш Telegram.**\n\n"
        "Твой `file_id`:\n"
        f"`{file_id}`\n\n"
        "_(Нажми на код, чтобы скопировать)_"
    )
    
    bot.reply_to(message, text, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u:
        bot.answer_callback_query(call.id, "❌ Ошибка авторизации. Жми /start")
        return

    try:
        # --- 1. ЭНЕРГИЯ И СИНХРОН ---
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
                    threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button())).start()
                else:
                    bot.answer_callback_query(call.id)
                    proto = logic.get_content_logic('protocol', u['path'], u['level'], u['decoder'] > 0)
                    txt = proto['text'] if proto else "/// ДАННЫЕ ПОВРЕЖДЕНЫ. ПОПРОБУЙ ПОЗЖЕ."
                    xp = config.XP_GAIN
                    db.update_user(uid, last_protocol_time=int(time.time()), xp=u['xp']+xp, notified=False)
                    if proto: db.save_knowledge(uid, proto.get('id', 0))

                    lvl, msg = logic.check_level_up(uid)
                    if lvl:
                        try: bot.send_message(uid, msg, parse_mode="HTML")
                        except: pass

                    final_txt = f"💠 <b>СИНХРОНИЗАЦИЯ:</b>\n\n{txt}\n\n⚡️ +{xp} XP"
                    threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button())).start()

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
                     threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button())).start()
                 else:
                     bot.answer_callback_query(call.id)
                     sig = logic.get_content_logic('signal')
                     txt = sig['text'] if sig else "/// НЕТ СВЯЗИ."
                     xp = config.XP_SIGNAL
                     db.update_user(uid, last_signal_time=int(time.time()), xp=u['xp']+xp)

                     lvl, msg = logic.check_level_up(uid)
                     if lvl:
                         try: bot.send_message(uid, msg, parse_mode='HTML')
                         except: pass

                     final_txt = f"📡 <b>СИГНАЛ ПЕРЕХВАЧЕН:</b>\n\n{txt}\n\n⚡️ +{xp} XP"
                     threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button())).start()

        elif call.data == "admin_panel":
             if db.is_user_admin(uid):
                 menu_update(call, "⚡️ <b>GOD MODE: MAIN TERMINAL</b>", kb.admin_main_menu())
             else:
                 bot.answer_callback_query(call.id, "❌ ACCESS DENIED")

        # --- ADMIN SUB-MENUS ---
        elif call.data.startswith("admin_menu_"):
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
             menu_update(call, report, kb.back_button())

        # --- ADMIN ACTIONS (STATE SETTERS) ---
        elif call.data in ["admin_grant_admin", "admin_revoke_admin", "admin_give_res",
                           "admin_broadcast", "admin_post_channel", "admin_add_riddle",
                           "admin_add_content", "admin_add_signal", "admin_sql", "admin_dm_user",
                           "admin_reset_user"]:
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
                 "admin_reset_user": "wait_reset_user_id"
             }
             user_states[uid] = state_map[call.data]
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
                 "admin_reset_user": "♻️ <b>ENTER USER ID TO RESET (XP=0, LVL=1):</b>"
             }
             menu_update(call, msg_map[call.data], kb.back_button())

        elif call.data == "admin_give_item_menu":
             if not db.is_user_admin(uid): return
             menu_update(call, "🎁 <b>SELECT ITEM:</b>", kb.admin_item_select())

        elif call.data.startswith("adm_give_"):
             if not db.is_user_admin(uid): return
             item = call.data.replace("adm_give_", "")
             user_states[uid] = f"wait_give_item_id|{item}"
             menu_update(call, f"🆔 <b>GIVING {item.upper()}\nENTER USER ID:</b>", kb.back_button())

        # --- 2. ПРОФИЛЬ И ФРАКЦИЯ ---
        elif call.data == "profile":
            stats, _ = logic.get_user_stats(uid)
            perc, xp_need = logic.get_level_progress_stats(u)
            p_bar = kb.get_progress_bar(perc, 100)
            ach_list = db.get_user_achievements(uid)
            has_accel = db.get_item_count(uid, 'accel') > 0

            p_stats = logic.get_profile_stats(uid)
            accel_status = ""
            if u.get('accel_exp', 0) > time.time():
                 rem_hours = int((u['accel_exp'] - time.time()) / 3600)
                 accel_status = f"\n⚡️ Ускоритель: <b>АКТИВЕН ({rem_hours}ч)</b>"

            msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'], 'Unknown')}</code>\n"
                   f"📊 LVL {u['level']} | {p_bar} ({perc}%)\n"
                   f"📉 ДО СЛЕДУЮЩЕГО УРОВНЯ: {xp_need} XP\n\n"
                   f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\n"
                   f"🔋 ТЕКУЩИЙ ОПЫТ: {u['xp']} | 🪙 BioCoins: {u['biocoin']}\n"
                   f"{accel_status}\n"
                   f"🔥 СТРИК: <b>{p_stats['streak']} дн. (+{p_stats['streak_bonus']}% к опыту)</b>\n"
                   f"🕳 Рекорд глубины: <b>{p_stats['max_depth']}м</b>\n"
                   f"🏆 Ачивки: <b>{len(ach_list)}</b>")

            menu_update(call, msg, kb.profile_menu(u, has_accel))

        elif call.data.startswith("set_path_"):
            path = call.data.replace("set_path_", "")
            info = SCHOOLS_INFO.get(path)
            txt = (f"🧬 <b>ВЫБОР: {info['name']}</b>\n\n"
                   f"✅ Бонус: {info['bonus']}\n"
                   f"⚠️ Штраф: {info['penalty']}\n\n"
                   f"📜 <i>{info['ideology']}</i>\n\n"
                   f"💳 Баланс: {u['xp']} XP | {u['biocoin']} BC\n\n"
                   "Подтвердить выбор?")
            menu_update(call, txt, kb.faction_confirm_menu(path))

        elif call.data.startswith("confirm_path_"):
            path = call.data.replace("confirm_path_", "")
            db.update_user(uid, path=path)
            bot.answer_callback_query(call.id, f"✅ ВЫБРАН ПУТЬ: {path.upper()}")
            u = db.get_user(uid)
            bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")

        elif call.data == "achievements_list":
             # Redirect to page 0
             call.data = "achievements_list_0"
             handle_query(call)

        elif call.data.startswith("achievements_list_"):
             page = int(call.data.replace("achievements_list_", ""))
             limit = 5
             offset = page * limit

             alist = db.get_user_achievements(uid)
             total = len(alist)
             total_pages = (total // limit) + (1 if total % limit > 0 else 0)
             if total_pages == 0: total_pages = 1

             # Slice
             current_items = alist[offset : offset + limit]

             txt = f"🏆 <b>ТВОИ ДОСТИЖЕНИЯ ({page+1}/{total_pages}):</b>\n\n"
             if not current_items: txt += "Пока пусто."
             else:
                 for a in current_items:
                     info = config.ACHIEVEMENTS_LIST.get(a)
                     if info: txt += f"✅ <b>{info['name']}</b>\n{info['desc']}\n\n"
                     else: txt += f"✅ <b>НЕИЗВЕСТНОЕ ДОСТИЖЕНИЕ ({a})</b>\nДанные утеряны.\n\n"

             menu_update(call, txt, kb.achievements_nav(page, total_pages))

        elif call.data == "use_accelerator":
            if db.get_item_count(uid, 'accel') > 0:
                db.update_user(uid, accel_exp=int(time.time() + 86400))
                db.use_item(uid, 'accel')
                bot.answer_callback_query(call.id, "⚡️ УСКОРИТЕЛЬ АКТИВИРОВАН НА 24 ЧАСА!", show_alert=True)
                handle_query(type('obj', (object,), {'data': 'profile', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
            else:
                bot.answer_callback_query(call.id, "❌ Нет предмета.")

        # --- 3. ИНВЕНТАРЬ ---
        elif call.data == "inventory":
            txt = logic.format_inventory(uid, category='all')
            items = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='all'))

        elif call.data == "inv_cat_equip":
            txt = logic.format_inventory(uid, category='equip')
            items = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='equip'))

        elif call.data == "inv_cat_consumable":
            txt = logic.format_inventory(uid, category='consumable')
            items = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='consumable'))
        
        elif call.data == "inv_mode_dismantle":
            txt = logic.format_inventory(uid)
            items = db.get_inventory(uid)
            equipped = db.get_equipped_items(uid)
            menu_update(call, txt + "\n\n⚠️ <b>РЕЖИМ РАЗБОРА АКТИВЕН</b>", kb.inventory_menu(items, equipped, dismantle_mode=True))

        elif call.data == "inv_mode_normal":
            handle_query(type('obj', (object,), {'data': 'inventory', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data.startswith("equip_"):
            item = call.data.replace("equip_", "")
            info = EQUIPMENT_DB.get(item)
            if info and db.equip_item(uid, item, info['slot']):
                bot.answer_callback_query(call.id, f"🛡 Надето: {info['name']}")
                handle_query(type('obj', (object,), {'data': 'inventory', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data.startswith("unequip_"):
            slot = call.data.replace("unequip_", "")
            if db.unequip_item(uid, slot):
                bot.answer_callback_query(call.id, "📦 Снято.")
                handle_query(type('obj', (object,), {'data': 'inventory', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))

        elif call.data.startswith("dismantle_"):
            item_id = call.data.replace("dismantle_", "")
            info = EQUIPMENT_DB.get(item_id)
            if info:
                price = info.get('price', 0)
                scrap_val = int(price * 0.1)
                if db.use_item(uid, item_id, 1):
                    db.update_user(uid, biocoin=u['biocoin'] + scrap_val)
                    bot.answer_callback_query(call.id, f"♻️ Разобрано: +{scrap_val} BC")
                    # Refresh
                    txt = logic.format_inventory(uid)
                    items = db.get_inventory(uid)
                    equipped = db.get_equipped_items(uid)
                    menu_update(call, txt + "\n\n⚠️ <b>РЕЖИМ РАЗБОРА АКТИВЕН</b>", kb.inventory_menu(items, equipped, dismantle_mode=True))
            else:
                 bot.answer_callback_query(call.id, "❌ Эту вещь нельзя разобрать.")

        # --- 4. МАГАЗИН ---
        elif call.data == "shop_menu":
            menu_update(call, "🎰 <b>ВЫБЕРИ ОТДЕЛ:</b>", kb.shop_category_menu())

        elif call.data.startswith("shop_cat_"):
            cat = call.data.replace("shop_cat_", "")
            menu_update(call, f"🎰 <b>ОТДЕЛ: {cat.upper()}</b>", kb.shop_section_menu(cat))

        elif call.data.startswith("buy_"):
            item = call.data.replace("buy_", "")
            cost = PRICES.get(item, EQUIPMENT_DB.get(item, {}).get('price', 9999))
            currency = 'xp' if item in ['cryo', 'accel'] else 'biocoin'

            if currency == 'xp':
                if u.get('xp', 0) >= cost:
                    db.add_item(uid, item)
                    db.update_user(uid, xp=u['xp'] - cost)
                    bot.answer_callback_query(call.id, f"✅ Куплено: {item}", show_alert=True)
                    handle_query(type('obj', (object,), {'data': f'view_shop_{item}', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
                else:
                    bot.answer_callback_query(call.id, "❌ Мало XP", show_alert=True)
            else:
                if u['biocoin'] >= cost:
                    if db.add_item(uid, item):
                        db.update_user(uid, biocoin=u['biocoin'] - cost, total_spent=u['total_spent']+cost)
                        bot.answer_callback_query(call.id, f"✅ Куплено: {item}", show_alert=True)
                        handle_query(type('obj', (object,), {'data': f'view_shop_{item}', 'message': call.message, 'from_user': call.from_user, 'id': call.id}))
                    else:
                        bot.answer_callback_query(call.id, "🎒 Рюкзак полон!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, "❌ Мало монет", show_alert=True)

        # --- 5. РЕЙД ---
        elif call.data == "zero_layer_menu":
             cost = logic.get_raid_entry_cost(uid)
             menu_update(call, f"🚀 <b>---НУЛЕВОЙ СЛОЙ---</b>\nВаш текущий опыт: {u['xp']}\nСтоимость входа: {cost}", kb.raid_welcome_keyboard(cost))

        elif call.data == "raid_enter":
             res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
             if not res:
                 bot.answer_callback_query(call.id, txt, show_alert=True)
             else:
                 consumables = get_consumables(uid)
                 riddle_opts = extra['options'] if etype == 'riddle' and extra else []
                 image_url = extra.get('image') if extra else None
                 markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables)
                 menu_update(call, txt, markup, image_url=image_url)

        elif call.data == "raid_step":
             res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
             if not res:
                 menu_update(call, txt, kb.back_button())
             else:
                 consumables = get_consumables(uid)
                 riddle_opts = extra['options'] if etype == 'riddle' and extra else []
                 image_url = extra.get('image') if extra else None
                 markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables)
                 menu_update(call, txt, markup, image_url=image_url)

        elif call.data == "raid_open_chest":
             res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid, answer='open_chest')
             if not res:
                 if txt == "no_key":
                     bot.answer_callback_query(call.id, "⚠️ ОШИБКА ДОСТУПА: Ключ не найден.", show_alert=True)
                 else:
                     bot.answer_callback_query(call.id, txt, show_alert=True)
             else:
                 # Success
                 alert_txt = f"🔓 СИСТЕМА РАЗБЛОКИРОВАНА. Получено: {extra.get('alert', '')}" if extra else "🔓 СИСТЕМА РАЗБЛОКИРОВАНА"
                 bot.answer_callback_query(call.id, alert_txt, show_alert=True)
                 consumables = get_consumables(uid)
                 image_url = extra.get('image') if extra else None
                 markup = kb.raid_action_keyboard(cost, etype, consumables=consumables)
                 menu_update(call, txt, markup, image_url=image_url)

        elif call.data == "raid_use_battery":
             res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid, answer='use_battery')
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
             res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid, answer='use_stimulator')
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

             lvl, msg = logic.check_level_up(uid)
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

             report = logic.generate_raid_report(uid, s, success=True)
             db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
             menu_update(call, report, kb.back_button())

        # --- COMBAT HANDLERS ---
        elif call.data in ["combat_attack", "combat_run", "combat_use_emp", "combat_use_stealth", "combat_use_wiper"]:
             action = call.data.replace("combat_", "")
             res_type, msg = logic.process_combat_action(uid, action)

             if res_type == 'error':
                 bot.answer_callback_query(call.id, msg, show_alert=True)
                 res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
                 if res:
                     consumables = get_consumables(uid)
                     image_url = extra.get('image') if extra else None
                     menu_update(call, txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)
                 else: menu_update(call, "Ошибка синхронизации.", kb.back_button())

             elif res_type == 'win':
                 bot.answer_callback_query(call.id, "VICTORY!")
                 # Continue after win
                 res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
                 full_txt = f"{msg}\n\n{txt}"
                 consumables = get_consumables(uid)
                 image_url = extra.get('image') if extra else None
                 # FIX: If no new image (e.g. non-combat step), reset to faction image to remove monster pic
                 if not image_url: image_url = get_menu_image(new_u)
                 menu_update(call, full_txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)

             elif res_type == 'escaped':
                 res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
                 full_txt = f"{msg}\n\n{txt}"
                 consumables = get_consumables(uid)
                 image_url = extra.get('image') if extra else None
                 # FIX: If no new image, reset to faction image
                 if not image_url: image_url = get_menu_image(new_u)
                 menu_update(call, full_txt, kb.raid_action_keyboard(cost, etype, consumables=consumables), image_url=image_url)

             elif res_type == 'death':
                 menu_update(call, msg, kb.back_button())

             elif res_type == 'combat':
                 res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
                 full_txt = f"{msg}\n\n{txt}"
                 consumables = get_consumables(uid)
                 image_url = extra.get('image') if extra else None
                 menu_update(call, full_txt, kb.raid_action_keyboard(cost, 'combat', consumables=consumables), image_url=image_url)

        # --- RIDDLES ---
        elif call.data.startswith("r_check_"):
            ans = call.data.replace("r_check_", "")
            success, msg = logic.process_riddle_answer(uid, ans)
            bot.answer_callback_query(call.id, "Принято.")

            res, txt, extra, new_u, etype, cost = logic.process_raid_step(uid)
            full_txt = f"{msg}\n\n{txt}"
            consumables = get_consumables(uid)
            riddle_opts = extra['options'] if etype == 'riddle' and extra else []
            image_url = extra.get('image') if extra else None
            markup = kb.riddle_keyboard(riddle_opts) if etype == 'riddle' else kb.raid_action_keyboard(cost, etype, consumables=consumables)
            menu_update(call, full_txt, markup, image_url=image_url)

        # --- 6. MISC ---
        elif call.data == "leaderboard":
            leaders = db.get_leaderboard()
            txt = "🏆 <b>ТОП-10 ИСКАТЕЛЕЙ</b>\n\n"
            for i, l in enumerate(leaders, 1):
                icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "▫️"
                txt += f"{icon} {l['first_name']} — {l['max_depth']}м | {l['xp']} XP\n"
            menu_update(call, txt, kb.back_button())

        elif call.data == "referral":
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            txt = SYNDICATE_FULL + f"\n\n<code>{link}</code>\n\n"
            txt += logic.get_syndicate_stats(uid)
            menu_update(call, txt, kb.back_button())

        elif call.data == "diary_menu":
            menu_update(call, "📓 <b>ЛИЧНЫЙ ДНЕВНИК</b>\nЗдесь ты можешь записывать свои мысли.", kb.diary_menu())

        elif call.data == "diary_new":
            user_states[uid] = "waiting_for_diary_entry"
            menu_update(call, "✍️ <b>НОВАЯ ЗАПИСЬ</b>\n\nНапиши свои мысли в чат. Я сохраню их в архиве.", kb.back_button())

        elif call.data.startswith("diary_read_"):
            page = int(call.data.replace("diary_read_", ""))
            limit = 5
            offset = page * limit

            entries = db.get_diary_entries(uid, limit, offset)
            total = db.get_diary_count(uid)
            total_pages = (total // limit) + (1 if total % limit > 0 else 0)

            if not entries:
                txt = "📓 <b>ДНЕВНИК ПУСТ</b>"
                menu_update(call, txt, kb.diary_menu())
            else:
                txt = f"📓 <b>СТРАНИЦА {page+1}/{total_pages}</b>\n\n"
                for e in entries:
                    dt = e['created_at'].strftime('%d.%m %H:%M')
                    txt += f"📅 <b>{dt}</b>\n{e['entry']}\n\n"

                menu_update(call, txt, kb.diary_read_nav(page, total_pages))

        elif call.data == "archive_list":
             if u['xp'] >= config.ARCHIVE_COST:
                 db.update_user(uid, xp=u['xp']-config.ARCHIVE_COST)
                 call.data = "archive_list_0"
                 handle_query(call)
             else:
                 bot.answer_callback_query(call.id, f"❌ Нужно {config.ARCHIVE_COST} XP", show_alert=True)

        elif call.data.startswith("archive_list_"):
             page = int(call.data.replace("archive_list_", ""))
             limit = 5
             offset = page * limit

             protocols = db.get_archived_protocols_paginated(uid, limit, offset)
             total = db.get_archived_protocols_count(uid)
             total_pages = (total // limit) + (1 if total % limit > 0 else 0)
             if total_pages == 0: total_pages = 1

             txt = f"💾 <b>АРХИВ ДАННЫХ ({page+1}/{total_pages}):</b>\n\n"
             if not protocols: txt += "Пусто."
             else:
                 for p in protocols:
                     icon = "🧬" if p['type'] == 'protocol' else "📡"
                     txt += f"{icon} <b>ЗАПИСЬ</b> (Lvl {p['level']})\n{p['text']}\n\n"

             menu_update(call, txt, kb.archive_nav(page, total_pages))

        elif call.data == "guide":
            menu_update(call, logic.GAME_GUIDE_TEXTS.get('intro', "Error"), kb.guide_menu('intro'))

        elif call.data.startswith("guide_page_"):
            page = call.data.replace("guide_page_", "")
            text = logic.GAME_GUIDE_TEXTS.get(page, "Error")
            menu_update(call, text, kb.guide_menu(page))

        elif call.data == "change_path_menu":
            menu_update(call, f"🧬 <b>СМЕНА ФРАКЦИИ</b>\nЦена: {PATH_CHANGE_COST} XP.\nТекущая: {SCHOOLS.get(u['path'], 'Нет')}", kb.change_path_keyboard(PATH_CHANGE_COST))

        elif call.data.startswith("view_item_"):
            item_id = call.data.replace("view_item_", "")
            info = ITEMS_INFO.get(item_id)
            if info:
                desc = info['desc']
                if info.get('type') == 'equip':
                    desc += f"\n\n⚔️ ATK: {info.get('atk', 0)} | 🛡 DEF: {info.get('def', 0)} | 🍀 LUCK: {info.get('luck', 0)}"
                is_equipped = item_id in db.get_equipped_items(uid).values()
                menu_update(call, f"📦 <b>{info['name']}</b>\n\n{desc}", kb.item_details_keyboard(item_id, is_owned=True, is_equipped=is_equipped))

        elif call.data.startswith("view_shop_"):
            item_id = call.data.replace("view_shop_", "")
            price = PRICES.get(item_id, EQUIPMENT_DB.get(item_id, {}).get('price', 9999))
            currency = 'xp' if item_id in ['cryo', 'accel'] else 'biocoin'
            info = ITEMS_INFO.get(item_id)
            if not info:
                 if item_id == 'cryo': info = {'name': '❄️ КРИО-КАПСУЛА', 'desc': 'Позволяет сохранять стрик даже если пропустил день.', 'type': 'misc'}
                 elif item_id == 'accel': info = {'name': '⚡️ УСКОРИТЕЛЬ', 'desc': 'Снижает кулдаун Синхронизации до 15 минут на 24 часа.', 'type': 'misc'}
                 else: info = {'name': item_id, 'desc': '???', 'type': 'misc'}
            desc = info['desc']
            if info.get('type') == 'equip':
                desc += f"\n\n⚔️ ATK: {info.get('atk', 0)} | 🛡 DEF: {info.get('def', 0)} | 🍀 LUCK: {info.get('luck', 0)}"
            txt = f"🎰 <b>{info['name']}</b>\n\n{desc}\n\n💰 Цена: {price} {currency.upper()}\n\n💳 Баланс: {u['xp']} XP | {u['biocoin']} BC"
            menu_update(call, txt, kb.shop_item_details_keyboard(item_id, price, currency))
        elif call.data == "back":
            menu_update(call, get_menu_text(u), kb.main_menu(u), image_url=get_menu_image(u))

        try: bot.answer_callback_query(call.id)
        except telebot.apihelper.ApiTelegramException as e:
            if "query is too old" in e.description or "query ID is invalid" in e.description:
                print(f"/// SYSTEM: Skipped dead query {call.id}")
            else:
                print(f"/// SYSTEM ERROR: {e}")
    except Exception as e:
        print(f"/// ERR: {e}"); traceback.print_exc()
        try: bot.answer_callback_query(call.id, "⚠️ ERROR")
        except: pass

@bot.message_handler(content_types=['text'])
def text_handler(m):
    uid = m.from_user.id
    state = user_states.get(uid)

    if not state: return

    # --- DIARY ---
    if state == "waiting_for_diary_entry":
        db.add_diary_entry(uid, m.text)
        del user_states[uid]
        bot.send_message(uid, "✅ <b>ЗАПИСЬ СОХРАНЕНА.</b>", parse_mode="HTML")
        bot.send_message(uid, "📓 ДНЕВНИК", reply_markup=kb.diary_menu())
        return

    # --- ADMIN ---
    if not db.is_user_admin(uid): return

    if state == "wait_grant_admin":
        try:
            tid = int(m.text)
            db.set_user_admin(tid, True)
            bot.send_message(uid, f"✅ ADMIN GRANTED TO {tid}")
        except: bot.send_message(uid, "❌ INVALID ID")
        del user_states[uid]

    elif state == "wait_revoke_admin":
        try:
            tid = int(m.text)
            if str(tid) == str(config.ADMIN_ID):
                 bot.send_message(uid, "❌ CANNOT REVOKE OWNER")
            else:
                 db.set_user_admin(tid, False)
                 bot.send_message(uid, f"✅ ADMIN REVOKED FROM {tid}")
        except: bot.send_message(uid, "❌ INVALID ID")
        del user_states[uid]

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
        del user_states[uid]

    elif state == "wait_give_res_id":
        try:
            tid = int(m.text)
            user_states[uid] = f"wait_give_res_val|{tid}"
            bot.send_message(uid, "💰 <b>ENTER AMOUNT:</b>\nExamples: '1000' (Coins), '500 xp' (XP)")
        except:
            bot.send_message(uid, "❌ INVALID ID")
            del user_states[uid]

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
        del user_states[uid]

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
        del user_states[uid]

    elif state == "wait_dm_user_id":
        try:
            tid = int(m.text)
            user_states[uid] = f"wait_dm_text|{tid}"
            bot.send_message(uid, "✉️ <b>ENTER MESSAGE TEXT (HTML Supported):</b>")
        except:
            bot.send_message(uid, "❌ INVALID ID")
            del user_states[uid]

    elif state.startswith("wait_dm_text|"):
        tid = int(state.split("|")[1])
        try:
            bot.send_message(tid, f"✉️ <b>ЛИЧНОЕ СООБЩЕНИЕ ОТ АДМИНИСТРАТОРА:</b>\n\n{m.text}", parse_mode="HTML")
            bot.send_message(uid, f"✅ SENT TO {tid}")
        except Exception as e:
            bot.send_message(uid, f"❌ ERROR: {e}")
        del user_states[uid]

    elif state == "wait_broadcast_text":
        count = 0
        try:
            with db.db_cursor() as cur:
                cur.execute("SELECT uid FROM users")
                users = cur.fetchall()
                for row in users:
                    try:
                        bot.send_message(row[0], m.text, parse_mode="HTML")
                        count += 1
                        time.sleep(0.05)
                    except: pass
            bot.send_message(uid, f"✅ SENT TO {count} USERS")
        except Exception as e: bot.send_message(uid, f"❌ ERROR: {e}")
        del user_states[uid]

    elif state == "wait_channel_post":
        try:
            bot.send_message(config.CHANNEL_ID, m.text, parse_mode="HTML")
            bot.send_message(uid, f"✅ POSTED TO {config.CHANNEL_ID}")
        except Exception as e:
            bot.send_message(uid, f"❌ ERROR: {e}\nCheck if bot is admin in channel.")
        del user_states[uid]

    elif state == "wait_add_riddle":
        if db.admin_add_riddle_to_db(m.text):
            bot.send_message(uid, "✅ RIDDLE ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        del user_states[uid]

    elif state == "wait_add_protocol":
        if db.admin_add_signal_to_db(m.text, c_type='protocol'):
             bot.send_message(uid, "✅ PROTOCOL ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        del user_states[uid]

    elif state == "wait_add_signal":
        if db.admin_add_signal_to_db(m.text, c_type='signal'):
             bot.send_message(uid, "✅ SIGNAL ADDED")
        else: bot.send_message(uid, "❌ ERROR")
        del user_states[uid]

    elif state == "wait_sql":
        res = db.admin_exec_query(m.text)
        try:
            bot.send_message(uid, f"<code>{str(res)[:4000]}</code>", parse_mode="HTML")
        except:
            bot.send_message(uid, "RESULT TOO LONG / ERROR")
        del user_states[uid]

@app.route('/health', methods=['GET'])
def health_check():
    return 'ALIVE', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'ALIVE', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            return 'Error', 500

@app.route("/", methods=["GET"])
def index():
    return "Eidos SQL Interface is Operational", 200

def system_startup():
    with app.app_context():
        time.sleep(2)
        print("/// SYSTEM STARTUP INITIATED...")
        db.init_db()

        # Sync Admin from Config
        try:
            db.set_user_admin(config.ADMIN_ID, True)
            print(f"/// ADMIN SYNC: {config.ADMIN_ID} rights granted.")
        except Exception as e:
            print(f"/// ADMIN SYNC ERROR: {e}")

        if WEBHOOK_URL:
            try:
                bot.remove_webhook()
                bot.set_webhook(url=WEBHOOK_URL + "/webhook")
                print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
            except Exception as e:
                print(f"/// WEBHOOK ERROR: {e}")

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
