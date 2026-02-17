import re

# Logic.py fix
with open('logic.py', 'r') as f:
    lines = f.readlines()

new_lines_logic = []
skip = False
for line in lines:
    if 'msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}' in line:
        # This is the start of broken block. Skip next line too.
        # We write correct line with \n inside string
        new_lines_logic.append('        msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\\n+25% Сигнала."\n')
        skip = True
    elif skip:
        # This is the second line "+25%..."
        skip = False
    else:
        new_lines_logic.append(line)

with open('logic.py', 'w') as f:
    f.writelines(new_lines_logic)
print("Fixed logic.py")

# Bot.py fix
with open('bot.py', 'r') as f:
    lines = f.readlines()

new_lines_bot = []
found_first = False
in_broken_block = False

# Correct block definition
correct_block_lines = [
    '            msg = (f"👤 <b>ПРОФИЛЬ: {u[\'first_name\']}</b>\\n"\n',
    '                   f"🔰 Статус: <code>{TITLES.get(u[\'level\'])}</code>\\n"\n',
    '                   f"📊 LVL {u[\'level\']} | {p_bar} ({perc}%)\\n"\n',
    '                   f"💡 До апа: {xp_need} XP\\n\\n"\n',
    '                   f"⚔️ ATK: {stats[\'atk\']} | 🛡 DEF: {stats[\'def\']} | 🍀 LUCK: {stats[\'luck\']}\\n"\n',
    '                   f"🏫 Школа: <code>{SCHOOLS.get(u[\'path\'], \'Общая\')}</code>\\n"\n',
    '                   f"🔋 Энергия: {u[\'xp\']} | 🪙 BioCoins: {u[\'biocoin\']}\\n\\n"\n',
    '                   f"🏆 Ачивки: <b>{len(ach_list)}</b>\\n"\n',
    '                   f"🔥 Стрик: <b>{streak} дн.</b> (Бонус: +{streak_bonus} XP)\\n"\n',
    '                   f"🕳 Рекорд глубины: <b>{max_depth}м</b>")\n',
    '            menu_update(call, msg, kb.back_button())\n'
]
# Note: I included menu_update call in correct block to ensure we consume the old one properly if it was part of broken block logic.
# But existing logic for removal matches until end marker.

for line in lines:
    if 'msg = (f"👤 <b>ПРОФИЛЬ:' in line:
        if not found_first:
            # First occurrence: Replace with correct block
            new_lines_bot.extend(correct_block_lines)
            found_first = True
            in_broken_block = True # Skip original lines until end of block
        else:
            # Duplicate occurrence: Skip it
            in_broken_block = True

    elif in_broken_block:
        if 'menu_update(call, msg, kb.back_button())' in line:
            # End of block
            in_broken_block = False
            # We already added menu_update in correct_block_lines?
            # Yes. So we skip this line.
    else:
        new_lines_bot.append(line)

with open('bot.py', 'w') as f:
    f.writelines(new_lines_bot)
print("Fixed bot.py")
