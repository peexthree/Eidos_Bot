import re

# Fix logic.py
with open('logic.py', 'r') as f:
    content = f.read()

# The broken string in logic.py spans two lines
broken_logic = r'msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n\+25% Сигнала."'
# Wait, reading from file will contain actual newline.
# Regex dot matches newline? No.
# I will search for the exact string including newline.
broken_logic_str = 'msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."'

fixed_logic_str = 'msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."'

if broken_logic_str in content:
    content = content.replace(broken_logic_str, fixed_logic_str)
    print("Fixed logic.py")
else:
    print("logic.py pattern not found")

with open('logic.py', 'w') as f:
    f.write(content)

# Fix bot.py
with open('bot.py', 'r') as f:
    content = f.read()

# The broken block in bot.py has multiple newlines inside f-strings.
# I'll just replace the whole msg assignment block.
# I'll use a regex to match the broken block.
# It starts with 'msg = (f"👤 <b>ПРОФИЛЬ:' and ends with '")' before 'menu_update'
# But regex matching across lines is tricky.

# Let's verify what the file contains exactly.
# It contains:
# msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\n
# f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\n
# ...

# I will replace the whole msg = (...) block with a correct one.
# I'll define the correct block and search for the start of the broken one.

correct_block = '''            msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\n"
                   f"📊 LVL {u['level']} | {p_bar} ({perc}%)\n"
                   f"💡 До апа: {xp_need} XP\n\n"
                   f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\n"
                   f"🔋 Энергия: {u['xp']} | 🪙 BioCoins: {u['biocoin']}\n\n"
                   f"🏆 Ачивки: <b>{len(ach_list)}</b>\n"
                   f"🔥 Стрик: <b>{streak} дн.</b> (Бонус: +{streak_bonus} XP)\n"
                   f"🕳 Рекорд глубины: <b>{max_depth}м</b>")'''

# Locate start
start_marker = 'msg = (f"👤 <b>ПРОФИЛЬ: {u[\'first_name\']}</b>'
end_marker = 'menu_update(call, msg, kb.back_button())'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # We replace from start_idx to end_idx (exclusive of end_marker)
    # But wait, end_marker is after the block.
    # The block ends with '")' followed by newline and indentation.

    # Let's find the closing parenthesis of the msg tuple.
    # It ends with '")'
    # And then next line is menu_update.
    # So replacing from start_idx to end_idx (stripped of whitespace) should work if I construct correct block + newline + indentation.

    # Actually, simpler: just find the broken string parts and replace newlines with \n.
    # But there are many.

    # Let's delete the chunk and insert correct_block.
    # We keep everything before start_idx.
    # We keep everything starting from end_idx.

    # Check indentation of correct_block. It has 12 spaces.
    # start_marker in file has 12 spaces?
    # Yes, based on previous cat.

    new_content = content[:start_idx] + correct_block + "\n            " + content[end_idx:]
    # Adjusted indentation before menu_update?
    # The original file has indentation before menu_update.
    # content[end_idx:] starts with 'menu_update...'.
    # So we need newline and indentation before it?
    # The correct_block ends with ')'.
    # The original code had:
    # ... )
    # menu_update...
    # So yes, we need newline and indentation.

    content = new_content
    print("Fixed bot.py")
else:
    print("bot.py pattern not found")

with open('bot.py', 'w') as f:
    f.write(content)
