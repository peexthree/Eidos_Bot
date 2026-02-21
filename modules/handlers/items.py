from modules.bot_instance import bot
import database as db
import config
from config import PRICES, EQUIPMENT_DB, ITEMS_INFO, TITLES, SCHOOLS
import keyboards as kb
from modules.services.utils import menu_update, get_menu_text, get_menu_image, get_consumables
from modules.services.inventory import format_inventory, check_legacy_items, convert_legacy_items
from modules.services.shop import get_shadow_shop_items, process_gacha_purchase
from modules.services.user import check_achievements, perform_hard_reset
from modules.services.content import get_decryption_status
import time
from telebot import types

@bot.callback_query_handler(func=lambda call: call.data == "shop_menu" or call.data.startswith("shop_cat_") or (call.data.startswith("buy_") and not call.data.startswith("buy_shadow_")) or call.data.startswith("view_shop_") or call.data == "shop_gacha_menu")
def shop_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    if call.data == "shop_menu":
        menu_update(call, "🎰 <b>ВЫБЕРИ ОТДЕЛ:</b>", kb.shop_category_menu(), image_url=config.MENU_IMAGES["shop_menu"])

    elif call.data.startswith("shop_cat_"):
        cat = call.data.replace("shop_cat_", "")
        menu_update(call, f"🎰 <b>ОТДЕЛ: {cat.upper()}</b>", kb.shop_section_menu(cat))

    elif call.data == "shop_gacha_menu":
        menu_update(call, "🎁 <b>СИСТЕМА ЛУТБОКСОВ</b>\n\nЦена: 1000 BC.\n\nШансы:\n• 80% - Мусор (XP)\n• 15% - Расходники\n• 5% - 🧩 ФРАГМЕНТ (Легендарный)", kb.gacha_menu())

    elif call.data == "buy_gacha":
        success, msg = process_gacha_purchase(uid)
        bot.answer_callback_query(call.id, msg.split('\n')[0], show_alert=True)
        menu_update(call, f"🎁 <b>СИСТЕМА ЛУТБОКСОВ</b>\n\n{msg}", kb.gacha_menu())

    elif call.data.startswith("buy_"):
        item = call.data.replace("buy_", "")
        cost = PRICES.get(item, EQUIPMENT_DB.get(item, {}).get('price', 9999))
        currency = 'xp' if item in ['cryo', 'accel'] else 'biocoin'

        if currency == 'xp':
            if u.get('xp', 0) >= cost:
                db.add_item(uid, item)
                db.update_user(uid, xp=u['xp'] - cost)

                ach_txt = ""
                new_achs = check_achievements(uid)
                if new_achs:
                    for a in new_achs:
                        ach_txt += f"\n🏆 ДОСТИЖЕНИЕ: {a['name']}"

                bot.answer_callback_query(call.id, f"✅ Куплено: {item}\n📉 Потрачено: {cost} XP{ach_txt}", show_alert=True)
                # Refresh view
                call.data = f"view_shop_{item}"
                shop_handler(call)
            else:
                bot.answer_callback_query(call.id, "❌ Мало XP", show_alert=True)
        else:
            if u['biocoin'] >= cost:
                if db.add_item(uid, item):
                    db.update_user(uid, biocoin=u['biocoin'] - cost, total_spent=u['total_spent']+cost)

                    ach_txt = ""
                    new_achs = check_achievements(uid)
                    if new_achs:
                        for a in new_achs:
                            ach_txt += f"\n🏆 ДОСТИЖЕНИЕ: {a['name']}"

                    bot.answer_callback_query(call.id, f"✅ Куплено: {item}\n📉 Потрачено: {cost} BC 🪙{ach_txt}", show_alert=True)
                    # Refresh view
                    call.data = f"view_shop_{item}"
                    shop_handler(call)
                else:
                    bot.answer_callback_query(call.id, "🎒 Рюкзак полон!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ Мало монет", show_alert=True)

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

@bot.callback_query_handler(func=lambda call: call.data == "shadow_broker_menu" or call.data.startswith("view_shadow_") or call.data.startswith("buy_shadow_"))
def shadow_shop_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    if call.data == "shadow_broker_menu":
        items = get_shadow_shop_items(uid)
        if not items:
            bot.answer_callback_query(call.id, "🕶 Канал закрыт...", show_alert=True)
            menu_update(call, get_menu_text(u), kb.main_menu(u), image_url=get_menu_image(u))
        else:
            expiry = u.get('shadow_broker_expiry', 0)
            rem_mins = max(0, int((expiry - time.time()) // 60))
            menu_update(call, f"🕶 <b>ТЕНЕВОЙ БРОКЕР</b>\nКанал закроется через {rem_mins} мин.\n\n<i>Товар нелегален. Возврату не подлежит.</i>", kb.shadow_shop_menu(items), image_url=config.MENU_IMAGES["shadow_shop_menu"])

    elif call.data.startswith("view_shadow_"):
        item_id = call.data.replace("view_shadow_", "")
        items = get_shadow_shop_items(uid)
        target = next((i for i in items if i['item_id'] == item_id), None)

        if not target:
            bot.answer_callback_query(call.id, "❌ Товар исчез.", show_alert=True)
            # Recursively go back
            call.data = "shadow_broker_menu"
            shadow_shop_handler(call)
        else:
            price = target['price']
            currency = target['currency']
            desc = target['desc']

            # Append stats if equip
            info = config.EQUIPMENT_DB.get(item_id)
            if info:
                desc += f"\n\n⚔️ ATK: {info.get('atk', 0)} | 🛡 DEF: {info.get('def', 0)} | 🍀 LUCK: {info.get('luck', 0)}"

            txt = f"🕶 <b>{target['name']}</b>\n\n{desc}\n\n💰 Цена: {price} {currency.upper()}\n\n💳 Баланс: {u['xp']} XP | {u['biocoin']} BC"
            menu_update(call, txt, kb.shadow_item_details_keyboard(item_id, price, currency))

    elif call.data.startswith("buy_shadow_"):
        item_id = call.data.replace("buy_shadow_", "")
        items = get_shadow_shop_items(uid)
        target = next((i for i in items if i['item_id'] == item_id), None)

        if not target:
            bot.answer_callback_query(call.id, "❌ Товар исчез.", show_alert=True)
            call.data = "shadow_broker_menu"
            shadow_shop_handler(call)
        else:
            price = target['price']
            currency = target['currency']

            can_buy = False
            if currency == 'xp' and u['xp'] >= price:
                db.update_user(uid, xp=u['xp'] - price)
                can_buy = True
            elif currency == 'biocoin' and u['biocoin'] >= price:
                db.update_user(uid, biocoin=u['biocoin'] - price)
                can_buy = True

            if can_buy:
                if db.add_item(uid, item_id):
                    db.log_action(uid, 'buy_shadow', f"Item: {item_id}, Price: {price} {currency}")
                    bot.answer_callback_query(call.id, f"✅ Куплено: {target['name']}", show_alert=True)
                    call.data = "shadow_broker_menu"
                    shadow_shop_handler(call)
                else:
                    # Refund
                    if currency == 'xp': db.update_user(uid, xp=u['xp'] + price)
                    else: db.update_user(uid, biocoin=u['biocoin'] + price)
                    bot.answer_callback_query(call.id, "🎒 Рюкзак полон!", show_alert=True)
            else:
                curr_label = "XP" if currency == 'xp' else "BC"
                user_bal = u['xp'] if currency == 'xp' else u['biocoin']
                bot.answer_callback_query(call.id, f"❌ Недостаточно средств\nНужно: {price} {curr_label}\nУ вас: {user_bal}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "inventory" or call.data.startswith("inv_") or call.data == "convert_legacy")
def inventory_handler(call):
    uid = call.from_user.id

    if call.data == "inventory":
        txt = format_inventory(uid, category='all')
        items = db.get_inventory(uid)
        equipped = db.get_equipped_items(uid)
        has_legacy = check_legacy_items(uid)
        menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='all', has_legacy=has_legacy), image_url=config.MENU_IMAGES["inventory"])

    elif call.data == "inv_cat_equip":
        txt = format_inventory(uid, category='equip')
        items = db.get_inventory(uid)
        equipped = db.get_equipped_items(uid)
        has_legacy = check_legacy_items(uid)
        menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='equip', has_legacy=has_legacy))

    elif call.data == "inv_cat_consumable":
        txt = format_inventory(uid, category='consumable')
        items = db.get_inventory(uid)
        equipped = db.get_equipped_items(uid)
        has_legacy = check_legacy_items(uid)
        menu_update(call, txt, kb.inventory_menu(items, equipped, dismantle_mode=False, category='consumable', has_legacy=has_legacy))

    elif call.data == "inv_mode_dismantle":
        txt = format_inventory(uid)
        items = db.get_inventory(uid)
        equipped = db.get_equipped_items(uid)
        has_legacy = check_legacy_items(uid)
        menu_update(call, txt + "\n\n⚠️ <b>РЕЖИМ РАЗБОРА АКТИВЕН</b>", kb.inventory_menu(items, equipped, dismantle_mode=True, has_legacy=has_legacy))

    elif call.data == "inv_mode_normal":
        call.data = "inventory"
        inventory_handler(call)

    elif call.data == "convert_legacy":
        msg = convert_legacy_items(uid)
        bot.answer_callback_query(call.id, "✅ КОНВЕРТАЦИЯ ЗАВЕРШЕНА", show_alert=True)
        bot.send_message(uid, f"♻️ <b>ОТЧЕТ О КОНВЕРТАЦИИ:</b>\n\n{msg}", parse_mode="HTML")
        call.data = "inventory"
        inventory_handler(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("equip_") or call.data.startswith("unequip_") or call.data.startswith("use_item_") or call.data.startswith("dismantle_") or call.data.startswith("view_item_"))
def item_action_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)

    if call.data.startswith("equip_"):
        item = call.data.replace("equip_", "")
        info = EQUIPMENT_DB.get(item)
        if info and db.equip_item(uid, item, info['slot']):
            bot.answer_callback_query(call.id, f"🛡 Надето: {info['name']}")
            call.data = "inventory"
            inventory_handler(call)

    elif call.data.startswith("unequip_"):
        slot = call.data.replace("unequip_", "")
        if db.unequip_item(uid, slot):
            bot.answer_callback_query(call.id, "📦 Снято.")
            call.data = "inventory"
            inventory_handler(call)

    elif call.data.startswith("view_item_"):
        item_id = call.data.replace("view_item_", "")
        info = ITEMS_INFO.get(item_id)
        if info:
            desc = info['desc']
            if info.get('type') == 'equip':
                desc += f"\n\n⚔️ ATK: {info.get('atk', 0)} | 🛡 DEF: {info.get('def', 0)} | 🍀 LUCK: {info.get('luck', 0)}"
            is_equipped = item_id in db.get_equipped_items(uid).values()
            menu_update(call, f"📦 <b>{info['name']}</b>\n\n{desc}", kb.item_details_keyboard(item_id, is_owned=True, is_equipped=is_equipped))

    elif call.data.startswith("use_item_"):
        item_id = call.data.replace("use_item_", "")

        if item_id == 'purification_sync':
            kb_confirm = types.InlineKeyboardMarkup()
            kb_confirm.add(types.InlineKeyboardButton("⚠️ ПОДТВЕРДИТЬ СБРОС", callback_data="confirm_hard_reset"))
            kb_confirm.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="inventory"))
            menu_update(call, "⚠️ <b>ВНИМАНИЕ: ПРОТОКОЛ ОЧИЩЕНИЯ</b>\n\nВы собираетесь стереть свою личность.\n• Уровень -> 1\n• XP -> 0\n• Инвентарь -> Удален\n\nЭто действие необратимо (но будет сохранено в истории).", kb_confirm)
            return

        elif item_id == 'encrypted_cache':
             status, txt = get_decryption_status(uid)
             menu_update(call, f"🔐 <b>ДЕШИФРАТОР</b>\n\n{txt}", kb.decrypt_menu(status))
             return

        elif item_id == 'accel':
            if db.get_item_count(uid, 'accel') > 0:
                db.update_user(uid, accel_exp=int(time.time() + 86400))
                db.use_item(uid, 'accel')
                bot.answer_callback_query(call.id, "⚡️ УСКОРИТЕЛЬ АКТИВИРОВАН!", show_alert=True)
                call.data = "inventory"
                inventory_handler(call)
            return

        elif item_id in ['battery', 'neural_stimulator', 'emp_grenade', 'stealth_spray', 'memory_wiper']:
            bot.answer_callback_query(call.id, "❌ Используйте это внутри Рейда.", show_alert=True)
            return

        else:
            bot.answer_callback_query(call.id, "❌ Этот предмет нельзя использовать здесь.", show_alert=True)
            return

    elif call.data.startswith("dismantle_"):
        item_id = call.data.replace("dismantle_", "")

        # Equipped check
        equipped = db.get_equipped_items(uid)
        if item_id in equipped.values():
            bot.answer_callback_query(call.id, "❌ Нельзя разобрать надетое снаряжение! Снимите его.", show_alert=True)
            return

        info = EQUIPMENT_DB.get(item_id) or ITEMS_INFO.get(item_id)
        if info:
            price = PRICES.get(item_id, info.get('price', 0))
            scrap_val = int(price * 0.1)

            if scrap_val <= 0:
                bot.answer_callback_query(call.id, "❌ Эту вещь нельзя разобрать (Цена 0).")
            elif db.use_item(uid, item_id, 1):
                db.update_user(uid, biocoin=u['biocoin'] + scrap_val)
                bot.answer_callback_query(call.id, f"♻️ Разобрано: +{scrap_val} BC")
                # Refresh
                call.data = "inv_mode_dismantle"
                inventory_handler(call)
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка предмета.")
        else:
                bot.answer_callback_query(call.id, "❌ Эту вещь нельзя разобрать.")

@bot.callback_query_handler(func=lambda call: call.data == "confirm_hard_reset")
def hard_reset_handler(call):
    uid = call.from_user.id
    if db.get_item_count(uid, 'purification_sync') > 0:
        if perform_hard_reset(uid):
            bot.answer_callback_query(call.id, "♻️ ЛИЧНОСТЬ СТЕРТА.", show_alert=True)
            # Restart flow manually
            bot.send_message(uid, f"/// EIDOS v8.0 REBOOTING...\nID: {uid}\n\nСистема перезагружена.", parse_mode="HTML")
            msg = ("🧬 <b>ВЫБОР ПУТИ (БЕСПЛАТНО)</b>\n\n"
                   "Ты должен выбрать свою специализацию, чтобы выжить.\n\n"
                   "🏦 <b>МАТЕРИЯ:</b> +20% Монет в Рейдах.\n"
                   "🧠 <b>РАЗУМ:</b> +10 Защиты.\n"
                   "🤖 <b>ТЕХНО:</b> +10 Удачи.")
            bot.send_message(uid, msg, reply_markup=kb.path_selection_keyboard(), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка сброса.", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Нет предмета.", show_alert=True)
