with open("modules/services/combat.py", "r") as f:
    text = f.read()

old_chance = "chance = 0.5 + (stats['luck'] / 200.0) + bonus_dodge"
new_chance = "chance = min(0.95, 0.10 + (stats['luck'] * 0.05) + bonus_dodge)"

text = text.replace(old_chance, new_chance)

with open("modules/services/combat.py", "w") as f:
    f.write(text)
