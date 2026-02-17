# Fix logic.py
with open('logic.py', 'r') as f:
    lines = f.readlines()

new_lines_logic = []
skip = False
for line in lines:
    if 'msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}' in line:
        # This is the start of broken block. Skip next line too.
        new_lines_logic.append('        msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."\n')
        skip = True
    elif skip:
        # This is the second line "+25%..."
        skip = False
    else:
        new_lines_logic.append(line)

with open('logic.py', 'w') as f:
    f.writelines(new_lines_logic)

print("Fixed logic.py")

# Fix bot.py
with open('bot.py', 'r') as f:
    lines = f.readlines()

new_lines_bot = []
in_block = False
block_start = 'msg = (f"👤 <b>ПРОФИЛЬ:'
block_end = 'f"🕳 Рекорд глубины: <b>{max_depth}м</b>")'

correct_block_lines = [
    '            msg = (f"👤 <b>ПРОФИЛЬ: {u[\'first_name\']}</b>\n"\n',
    '                   f"🔰 Статус: <code>{TITLES.get(u[\'level\'])}</code>\n"\n',
    '                   f"📊 LVL {u[\'level\']} | {p_bar} ({perc}%)\n"\n',
    '                   f"💡 До апа: {xp_need} XP\n\n"\n',
    '                   f"⚔️ ATK: {stats[\'atk\']} | 🛡 DEF: {stats[\'def\']} | 🍀 LUCK: {stats[\'luck\']}\n"\n',
    '                   f"🏫 Школа: <code>{SCHOOLS.get(u[\'path\'], \'Общая\')}</code>\n"\n',
    '                   f"🔋 Энергия: {u[\'xp\']} | 🪙 BioCoins: {u[\'biocoin\']}\n\n"\n',
    '                   f"🏆 Ачивки: <b>{len(ach_list)}</b>\n"\n',
    '                   f"🔥 Стрик: <b>{streak} дн.</b> (Бонус: +{streak_bonus} XP)\n"\n',
    '                   f"🕳 Рекорд глубины: <b>{max_depth}м</b>")\n'
]

for line in lines:
    if 'msg = (f"👤 <b>ПРОФИЛЬ:' in line:
        in_block = True
        new_lines_bot.extend(correct_block_lines)

    if in_block:
        if 'f"🕳 Рекорд глубины:' in line: # End of block
             in_block = False
    else:
        new_lines_bot.append(line)

with open('bot.py', 'w') as f:
    f.writelines(new_lines_bot)

print("Fixed bot.py")
