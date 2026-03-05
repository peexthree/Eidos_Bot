with open("modules/services/combat.py", "r") as f:
    text = f.read()

# Add signal display next to HP
# Look for msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"
# and change to: msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n💠 <b>ТВОЙ СИГНАЛ:</b> {current_signal}%\n"

text = text.replace(
    "msg += f\"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\\n\"",
    "msg += f\"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\\n💠 <b>ТВОЙ СИГНАЛ:</b> {current_signal}%\\n\""
)

with open("modules/services/combat.py", "w") as f:
    f.write(text)
