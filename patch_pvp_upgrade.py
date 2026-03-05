import sys

file_path = 'modules/handlers/pvp.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '@bot.callback_query_handler(func=lambda call: call.data == "pvp_upgrade_deck")' in line:
        new_lines.append(line)
        new_lines.append('def pvp_upgrade_handler(call):\n')
        new_lines.append('    uid = int(call.from_user.id)\n')
        new_lines.append('    success, msg = pvp.upgrade_deck(uid)\n')
        new_lines.append('    if success:\n')
        new_lines.append('        bot.answer_callback_query(call.id, "⚡️ Апгрейд запущен")\n')
        new_lines.append('        menu_update(call, "📡 <b>Подключение к терминалу...</b>", kb.back_button())\n')
        new_lines.append('        time.sleep(1)\n')
        new_lines.append('        menu_update(call, "💾 <b>Перепрошивка деки...</b>", kb.back_button())\n')
        new_lines.append('        time.sleep(1)\n')
        new_lines.append('        bot.answer_callback_query(call.id, strip_html(msg), show_alert=True)\n')
        new_lines.append('    else:\n')
        new_lines.append('        bot.answer_callback_query(call.id, strip_html(msg), show_alert=True)\n')
        new_lines.append('    from modules.handlers.pvp import pvp_config_handler\n')
        new_lines.append('    pvp_config_handler(call)\n')
        skip = True
    elif skip and 'def pvp_upgrade_handler(call):' in line:
        continue
    elif skip and 'uid = int(call.from_user.id)' in line:
        continue
    elif skip and 'success, msg = pvp.upgrade_deck(uid)' in line:
        continue
    elif skip and 'bot.answer_callback_query(call.id, strip_html(msg), show_alert=True)' in line:
        continue
    elif skip and 'pvp_config_handler(call)' in line:
        skip = False
    elif not skip:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
