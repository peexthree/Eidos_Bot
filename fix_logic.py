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
            f"✅ <b>ЭВАКУАЦИЯ УСПЕШНА</b>\\n"
            f"━━━━━━━━━━━━━━\\n"
            f"ПОЛУЧЕНО:\\n"
            f"• Данные (XP): {profit_xp}\\n"
            f"• Энергоблоки (Coins): {profit_coins}\\n"
            f"• Предметы: {items_list_str}\\n"
            f"━━━━━━━━━━━━━━\\n"
            f"📊 СТАТИСТИКА:\\n"
            f"• Глубина: {depth}\\n"
            f"• Убийств: {kills}\\n"
            f"• Загадок: {riddles}\\n"
            f"⏱ Время: {mins}м {secs}с"
        )
    else:
        return (
            f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\\n"
            f"УТЕРЯНО:\\n"
            f"• Данные (XP): {profit_xp}\\n"
            f"• Энергоблоки (Coins): {profit_coins}\\n"
            f"• Расходники: {items_list_str}\\n"
            f"⏱ Время: {mins}м {secs}с"
        )"""

with open('logic.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if 'def generate_raid_report' in line:
        start_idx = i
        break

end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if 'def format_combat_screen' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + [new_func + "\n\n"] + lines[end_idx:]
    with open('logic.py', 'w') as f:
        f.writelines(new_lines)
    print("Success")
else:
    print(f"Fail: {start_idx} {end_idx}")
