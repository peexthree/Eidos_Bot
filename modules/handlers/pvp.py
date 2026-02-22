from modules.bot_instance import bot
import database as db
import config
import keyboards as kb
from modules.services.utils import menu_update, get_menu_text, get_menu_image
from modules.services import pvp
from telebot import types
import time

@bot.callback_query_handler(func=lambda call: call.data == "pvp_menu" or call.data == "pvp_search" or call.data == "pvp_reset" or call.data.startswith("pvp_attack_"))
def pvp_action_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    if call.data == "pvp_menu":
        menu_update(call, "🌐 <b>СЕТЕВАЯ ВОЙНА</b>\n\nПодключаюсь к даркнету...", kb.pvp_menu(), image_url=config.MENU_IMAGES["pvp_menu"])

    elif call.data == "pvp_search":
        _handle_search(call, uid, u, config.PVP_FIND_COST)

    elif call.data == "pvp_reset":
        _handle_search(call, uid, u, config.PVP_RESET_COST)

    elif call.data.startswith("pvp_attack_"):
        parts = call.data.split('_')
        method = parts[2]
        target_uid = int(parts[3])

        res = pvp.perform_hack(uid, target_uid, method=method)

        if not res['success'] and res.get('msg'):
            bot.answer_callback_query(call.id, f"❌ {res['msg']}", show_alert=True)
            return

        txt = ""
        if res['success']:
            txt = (f"✅ <b>ВЗЛОМ УСПЕШЕН!</b>\n\n"
                   f"💸 Украдено: <b>{res['stolen']} BC</b>\n"
                   f"👤 Жертва: {res['target_name']}")
        else:
            txt = f"❌ <b>ВЗЛОМ ПРОВАЛЕН!</b>\n\n"
            if res['blocked']:
                txt += "🛡 Сработал ФАЙРВОЛ жертвы!\n"
            elif res['ice_trap']:
                txt += f"🪤 Сработала ICE-ЛОВУШКА!\nВы потеряли {res['lost_xp']} XP."
            else:
                txt += "Система защиты отразила атаку."

        bot.answer_callback_query(call.id, "📡 Данные получены.", show_alert=False)
        menu_update(call, txt, kb.pvp_menu())

        send_pvp_notification(target_uid, uid, res)

def _handle_search(call, uid, u, cost):
    if u['xp'] < cost:
        bot.answer_callback_query(call.id, f"❌ Не хватает XP ({cost})", show_alert=True)
        return

    db.update_user(uid, xp=u['xp'] - cost)

    target = pvp.find_target(uid)

    if not target:
        db.update_user(uid, xp=u['xp'])
        bot.answer_callback_query(call.id, "🔍 Цели не обнаружены.", show_alert=True)
        return

    msg = (
        f"⚠️ <b>НАЙДЕНА УЯЗВИМОСТЬ</b>\n\n"
        f"👤 Цель: <b>{target['name']}</b> (Lvl {target['level']})\n"
        f"💰 Возможная добыча: <b>{target['est_loot_min']} - {target['est_loot_max']} BC</b>\n"
        f"🛡 Уровень угрозы: <b>{target['threat']}</b>\n\n"
        f"Выберите метод взлома:"
    )
    menu_update(call, msg, kb.pvp_target_menu(target['uid']))

@bot.callback_query_handler(func=lambda call: call.data == "pvp_vendetta" or call.data.startswith("pvp_revenge_"))
def pvp_vendetta_handler(call):
    uid = call.from_user.id

    if call.data == "pvp_vendetta":
        history = pvp.get_revenge_list(uid)
        menu_update(call, "🩸 <b>ВЕНДЕТТА</b>\n\nСписок тех, кто атаковал вас за последние 24 часа.", kb.pvp_vendetta_menu(history))

    elif call.data.startswith("pvp_revenge_confirm_"):
        log_id = int(call.data.replace("pvp_revenge_confirm_", ""))
        log = db.get_revenge_target(log_id)
        if not log or log['is_revenged']:
             bot.answer_callback_query(call.id, "❌ Уже отомщено или устарело.", show_alert=True)
             return

        attacker_id = log['attacker_uid']
        a_user = db.get_user(attacker_id)
        name = a_user['username'] if a_user else "Unknown"

        menu_update(call, f"🩸 <b>МЕСТЬ: {name}</b>\n\nЦена: 50 XP.\nЦель: Вернуть {log['stolen_coins']} + 10%.\nЕсли победишь - вернешь честь.", kb.pvp_revenge_confirm(log_id, name))

    elif call.data.startswith("pvp_revenge_exec_"):
        log_id = int(call.data.replace("pvp_revenge_exec_", ""))
        log = db.get_revenge_target(log_id)
        if not log or log['is_revenged']:
             bot.answer_callback_query(call.id, "❌ Неактуально.", show_alert=True)
             return

        target_uid = log['attacker_uid']
        amount_to_steal = int(log['stolen_coins'] * 1.10)

        res = pvp.perform_hack(uid, target_uid, method='revenge', revenge_amount=amount_to_steal)

        if not res['success'] and res.get('msg'):
            bot.answer_callback_query(call.id, f"❌ {res['msg']}", show_alert=True)
            return

        if res['success']:
            db.mark_log_revenged(log_id)
            txt = f"🩸 <b>МЕСТЬ СВЕРШИЛАСЬ!</b>\n\nТы забрал {res['stolen']} BC."
        else:
            txt = "❌ <b>МЕСТЬ ПРОВАЛЕНА...</b>"
            if res['ice_trap']: txt += f"\n🪤 Ловушка: -{res['lost_xp']} XP"

        menu_update(call, txt, kb.pvp_menu())
        send_pvp_notification(target_uid, uid, res, is_revenge=True)

@bot.callback_query_handler(func=lambda call: call.data == "pvp_defense_shop")
def pvp_shop_handler(call):
    menu_update(call, "🛡 <b>СИСТЕМЫ ЗАЩИТЫ</b>\n\nПокупай софт, чтобы сохранить монеты.", kb.pvp_defense_shop())

def send_pvp_notification(target_uid, attacker_uid, res, is_revenge=False):
    """
    Sends a notification to the victim.
    """
    try:
        attacker_name = "НЕИЗВЕСТНЫЙ"
        if not res['anonymous']:
             au = db.get_user(attacker_uid)
             if au: attacker_name = f"@{au['username']}" if au['username'] else au['first_name']

        if res['success']:
            msg = (
                f"🚨 <b>КРИТИЧЕСКАЯ УГРОЗА!</b>\n\n"
                f"Ваша система взломана агентом <b>{attacker_name}</b>.\n"
                f"💸 Украдено: <b>{res['stolen']} BC</b>."
            )

            markup = None
            if not res['anonymous'] and not is_revenge and res['log_id']:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🩸 ОТОМСТИТЬ (-50 XP)", callback_data=f"pvp_revenge_confirm_{res['log_id']}"))

            bot.send_message(target_uid, msg, parse_mode="HTML", reply_markup=markup)

        else:
            if res['ice_trap']:
                msg = (
                    f"🪤 <b>ICE-ЛОВУШКА АКТИВИРОВАНА!</b>\n\n"
                    f"Хакер <b>{attacker_name}</b> попался.\n"
                    f"⚡️ Получено: <b>{res['lost_xp']} XP</b>."
                )
                bot.send_message(target_uid, msg, parse_mode="HTML")
            elif res['blocked']:
                 msg = (
                    f"🛡 <b>ФАЙРВОЛ ОТРАЗИЛ АТАКУ!</b>\n\n"
                    f"Хакер <b>{attacker_name}</b> заблокирован.\n"
                    f"Модуль защиты сгорел."
                )
                 bot.send_message(target_uid, msg, parse_mode="HTML")

    except Exception as e:
        print(f"PVP Notification Error: {e}")
