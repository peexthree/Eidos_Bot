import re

with open('logic.py', 'r') as f:
    content = f.read()

# 1. Replace Trap flavor
old_trap = r"flavor = random.choice\(RAID_FLAVOR_TEXT\['trap'\]\)"
new_trap = "flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['trap'])"
content = re.sub(old_trap, new_trap, content)

# 2. Replace Loot flavor
old_loot = r"flavor = random.choice\(RAID_FLAVOR_TEXT\['loot'\]\)"
new_loot = "flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['loot'])"
content = re.sub(old_loot, new_loot, content)

# 3. Replace Heal (msg_event assignment)
old_heal = r'msg_event = "❤️ <b>АПТЕЧКА:</b> \+25% Сигнала."'
new_heal = 'desc = event["text"] if len(event.get("text","")) > 15 else "Найден источник энергии."\n        msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."'
content = re.sub(old_heal, new_heal, content)

# 4. Replace Empty flavor
old_empty = r"flavor = random.choice\(RAID_FLAVOR_TEXT\['empty'\]\)"
new_empty = "flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['empty'])"
content = re.sub(old_empty, new_empty, content)

# 5. Riddles
old_riddle = r'options = random.sample\(\["Ошибка", "Сбой", "Пустота", "Шум"\], 2\) \+ \[correct\]'
new_riddle = '''# Smart distractors
        if " и " in correct or " and " in correct.lower():
             d1 = random.choice(RIDDLE_DISTRACTORS)
             d2 = random.choice(RIDDLE_DISTRACTORS)
             d3 = random.choice(RIDDLE_DISTRACTORS)
             d4 = random.choice(RIDDLE_DISTRACTORS)
             opts = [f"{d1} и {d2}", f"{d3} и {d4}"]
             options = opts + [correct]
        else:
             options = random.sample(RIDDLE_DISTRACTORS, 2) + [correct]'''
content = re.sub(old_riddle, new_riddle, content)

# 6. Compass
old_compass = r'res = "БЕЗОПАСНО" if event\[\'type\'\] in \[\'loot\', \'heal\', \'neutral\'\] else "⚠️ УГРОЗА"'
new_compass = 'res = "❇️ БЕЗОПАСНО (Ресурсы)" if event[\'type\'] in [\'loot\', \'heal\'] else ("⬜️ ПУСТО" if event[\'type\'] == \'neutral\' else "⚠️ УГРОЗА (Ловушка)")'
content = re.sub(old_compass, new_compass, content)

with open('logic.py', 'w') as f:
    f.write(content)
