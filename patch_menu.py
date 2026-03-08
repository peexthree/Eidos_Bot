import re

filepath = 'modules/handlers/menu.py'
with open(filepath, 'r') as f:
    content = f.read()

# Fix pvp_atk_direct_handler
old_pvp_handler = re.search(r'def pvp_atk_direct_handler\(call\):.*?_show_attack_screen\(call, safe_target, state_data\[\'slots\'\]\)', content, re.DOTALL).group(0)

new_pvp_handler = """def pvp_atk_direct_handler(call):
    target_uid = int(call.data.split("_")[3])
    from modules.handlers.pvp import pvp_search_handler

    target = db.get_user(target_uid)

    if not target:
        safe_answer_callback(bot, call.id, "❌ Объект исчез.")
        return

    target_slots = {}
    import json
    import config
    # Use deck_config from target user
    deck_config_str = target.get('deck_config')
    if deck_config_str:
        try:
            deck = json.loads(deck_config_str)
            for sid, iid in deck.items():
                if iid and iid in config.SOFTWARE_DB:
                    target_slots[str(sid)] = config.SOFTWARE_DB[iid]['icon']
        except Exception:
            pass

    safe_target = {
        'uid': target_uid,
        'name': target.get('username') or target.get('first_name') or "Unknown",
        'level': target.get('level', 1),
        'slots_preview': target_slots
    }

    state_data = {
        'target_uid': target_uid,
        'target_info': safe_target,
        'slots': {}
    }

    # Load current deck for attacker
    attacker = db.get_user(call.from_user.id)
    if attacker:
        attacker_deck_str = attacker.get('deck_config')
        if attacker_deck_str:
            try:
                attacker_deck = json.loads(attacker_deck_str)
                state_data['slots'] = {str(k): v for k, v in attacker_deck.items() if v}
            except Exception:
                pass

    db.set_state(call.from_user.id, 'pvp_attack_prep', json.dumps(state_data))

    from modules.handlers.pvp import _show_attack_screen
    _show_attack_screen(call, safe_target, state_data['slots'])"""

content = content.replace(old_pvp_handler, new_pvp_handler)

# Fix set_path_architect check
old_architect_check = 'if path == "architect":\n            safe_answer_callback(bot, call.id, "❌ Доступ закрыт. Требуется Ключ Архитектора. Вы — лишь наблюдатель, пока не найдете способ изменить сам код Системы.", show_alert=True)\n            return'
new_architect_check = 'if path == "architect":\n            safe_answer_callback(bot, call.id, "❌ Доступ закрыт. Требуется Ключ Архитектора.", show_alert=True)\n            return'
content = content.replace(old_architect_check, new_architect_check)

# Fix anomaly clear
old_anomaly_clear = """def remove_anomaly_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    import time
    if not u or not u.get('is_glitched') or u.get('anomaly_buff_expiry', 0) <= time.time():
        safe_answer_callback(bot, call.id, "❌ Аномалия уже рассеялась или отсутствует.", show_alert=True)
        return

    if int(u.get('biocoin', 0)) < 1000:
        safe_answer_callback(bot, call.id, "❌ Недостаточно BC (нужно 1000).", show_alert=True)
        return

    db.update_user(uid, biocoin=int(u.get('biocoin', 0)) - 1000, is_glitched=False, anomaly_buff_type=None, anomaly_buff_expiry=0)
    safe_answer_callback(bot, call.id, "Аномалия успешно удалена с вашего профиля.", show_alert=True)"""

new_anomaly_clear = """def remove_anomaly_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    import time
    if not u or not u.get('is_glitched') or u.get('anomaly_buff_expiry', 0) <= time.time():
        safe_answer_callback(bot, call.id, "❌ Аномалия уже рассеялась или отсутствует.", show_alert=True)
        return

    db.update_user(uid, is_glitched=False, anomaly_buff_type=None, anomaly_buff_expiry=0)
    safe_answer_callback(bot, call.id, "Аномалия успешно удалена с вашего профиля.", show_alert=True)"""

content = content.replace(old_anomaly_clear, new_anomaly_clear)

with open(filepath, 'w') as f:
    f.write(content)

print("Menu patched.")
