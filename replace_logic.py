import sys

new_func = """def generate_raid_report(uid, s, success=False):
    # Time
    duration = int(time.time() - s['start_time'])
    mins = duration // 60
    secs = duration % 60

    kills = s.get('kills', 0)
    riddles = s.get('riddles_solved', 0)
    depth = s.get('depth', 0)
    profit_xp = s.get('buffer_xp', 0)
    profit_coins = s.get('buffer_coins', 0)

    # Items
    buffer_items_str = s.get('buffer_items', '')
    items_list_str = ""
    if buffer_items_str:
        items = buffer_items_str.split(',')
        item_counts = {}
        for i in items:
            if i:
                name = ITEMS_INFO.get(i, {}).get('name', i)
                item_counts[name] = item_counts.get(name, 0) + 1

        items_list_str = ", ".join([f"{k} x{v}" for k,v in item_counts.items()])
    else:
        items_list_str = "Нет"

    if success:
        return (
            f"✅ <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"ПОЛУЧЕНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Предметы: {items_list_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 СТАТИСТИКА:\n"
            f"• Глубина: {depth}\n"
            f"• Убийств: {kills}\n"
            f"• Загадок: {riddles}\n"
            f"⏱ Время: {mins}м {secs}с"
        )
    else:
        return (
            f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\n"
            f"УТЕРЯНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Расходники: {items_list_str}\n"
            f"⏱ Время: {mins}м {secs}с"
        )
"""

with open('logic.py', 'r') as f:
    lines = f.readlines()

# Hardcoded indices based on previous check (77 to 116)
# But let's re-verify dynamically to be safe
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'def generate_raid_report(uid, s):' in line:
        start_idx = i
    if 'def format_combat_screen' in line and start_idx != -1:
        end_idx = i
        break

# The lines between start_idx and end_idx are the function body + some whitespace maybe
# Actually end_idx is the next function. So we replace lines[start_idx:end_idx] with new_func
# But we need to check if there are blank lines or comments we want to preserve?
# The gap is lines 77 to 116.
# Let's inspect line 116. It's usually the start of next function or comment header.
# "def format_combat_screen" starts at 121 in original read?
# Let's trust the search.

if start_idx != -1 and end_idx != -1:
    # We need to verify what is being replaced.
    print(f"Replacing lines {start_idx} to {end_idx}")

    # Check lines just before end_idx to see if they are whitespace we want to keep
    # Logic: replace everything from start_idx up to end_idx with new_func + newline

    new_lines = lines[:start_idx] + [new_func + "\n\n"] + lines[end_idx:]

    with open('logic.py', 'w') as f:
        f.writelines(new_lines)
    print("Success")
else:
    print("Could not find function bounds")
