import re

with open('modules/handlers/onboarding.py', 'r') as f:
    content = f.read()

content = content.replace("db.add_item(uid, 'master_key', 2)", "db.add_item(uid, 'master_key', 2)\n        db.add_item(uid, 'rusty_knife', 1)")

old_msg_end = "Цикл запущен. Нажми «Профиль», чтобы увидеть свое новое отражение.\"\n        )"
new_msg_end = "Я положил тебе в инвентарь Ржавый Тесак. Одень его. А теперь выбери свою специализацию.\"\n        )"

content = content.replace(old_msg_end, new_msg_end)

content = content.replace("reply_markup=kb.main_menu(u)", "reply_markup=kb.path_selection_keyboard()")

with open('modules/handlers/onboarding.py', 'w') as f:
    f.write(content)
