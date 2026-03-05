import sys

file_path = 'modules/handlers/items.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'elif call.data.startswith("craft_"):' in line:
        new_lines.append(line)
        new_lines.append('        item_id = call.data.replace("craft_", "")\n')
        new_lines.append('        success, res = crafting_service.craft_item(uid, item_id)\n')
        new_lines.append('\n')
        new_lines.append('        if success:\n')
        new_lines.append('            bot.answer_callback_query(call.id, "✅ Процесс запущен", show_alert=False)\n')
        new_lines.append('            \n')
        new_lines.append('            # Animation\n')
        new_lines.append('            menu_update(call, "🛰 <b>Инициализация чертежа...</b>", kb.back_button())\n')
        new_lines.append('            time.sleep(1)\n')
        new_lines.append('            menu_update(call, "🧬 <b>Синтез материи...</b>", kb.back_button())\n')
        new_lines.append('            time.sleep(1)\n')
        new_lines.append('            \n')
        new_lines.append('            new_item_id = res\n')
        new_lines.append('            new_info = ITEMS_INFO.get(new_item_id) or EQUIPMENT_DB.get(new_item_id, {})\n')
        new_lines.append('            name = new_info.get("name", new_item_id)\n')
        new_lines.append('            desc = new_info.get("desc", "")\n')
        new_lines.append('            image = ITEM_IMAGES.get(new_item_id)\n')
        new_lines.append('            \n')
        new_lines.append('            msg = f"✨ <b>СИНТЕЗ ЗАВЕРШЕН</b> ✨\\n\\n🎁 <b>ПОЛУЧЕНО:</b> {name}\\n\\n{desc}"\n')
        new_lines.append('            menu_update(call, msg, kb.back_button(), image_url=image)\n')
        new_lines.append('        else:\n')
        new_lines.append('            bot.answer_callback_query(call.id, strip_html(res), show_alert=True)\n')
        skip = True
    elif skip and 'elif call.data.startswith("use_item_"):' in line:
        skip = False
        new_lines.append('\n')
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
