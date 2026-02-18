import sys

with open('logic.py', 'r') as f:
    content = f.read()

# Exact string match block
search_block = """def generate_raid_report(uid, s):
    # Time
    duration = int(time.time() - s['start_time'])
    mins = duration // 60
    secs = duration % 60

    kills = s.get('kills', 0)
    riddles = s.get('riddles_solved', 0)
    profit_xp = s.get('buffer_xp', 0)
    profit_coins = s.get('buffer_coins', 0)

    # Items
    buffer_items_str = s.get('buffer_items', '')
    lost_items_list = ""
    if buffer_items_str:
        items = buffer_items_str.split(',')
        item_counts = {}
        for i in items:
            if i:
                name = ITEMS_INFO.get(i, {}).get('name', i)
                item_counts[name] = item_counts.get(name, 0) + 1

        lost_items_list = ", ".join([f"{k} x{v}" for k,v in item_counts.items()])
    else:
        lost_items_list = "Нет"

    return (
        f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\n"
        f"УТЕРЯНО:\n"
        f"• Данные (XP): {profit_xp}\n"
        f"• Энергоблоки (Coins): {profit_coins}\n"
        f"• Расходники: {lost_items_list}\n"
        f"⏱ Время: {mins}м {secs}с"
    )"""

replace_block = """def generate_raid_report(uid, s, success=False):
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
        )"""

if search_block in content:
    new_content = content.replace(search_block, replace_block)
    with open('logic.py', 'w') as f:
        f.write(new_content)
    print("Success")
else:
    print("Fail")
