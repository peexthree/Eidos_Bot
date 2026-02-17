import re

with open('logic.py', 'r') as f:
    content = f.read()

# Replace the compass line I just added
old_compass = r'res = "❇️ БЕЗОПАСНО \(Ресурсы\)" if event\[\'type\'\] in \[\'loot\', \'heal\'\] else \("⬜️ ПУСТО" if event\[\'type\'\] == \'neutral\' else "⚠️ УГРОЗА \(Ловушка\)"\)'
new_compass = 'res = "❇️ БЕЗОПАСНО (Ресурсы)" if event[\'type\'] in [\'loot\', \'heal\', \'locked_chest\'] else ("⬜️ ПУСТО" if event[\'type\'] == \'neutral\' else "⚠️ УГРОЗА (Ловушка)")'

content = re.sub(old_compass, new_compass, content)

with open('logic.py', 'w') as f:
    f.write(content)
