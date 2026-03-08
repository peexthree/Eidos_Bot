filepath = 'modules/services/raid.py'
with open(filepath, 'r') as f:
    content = f.read()

content = content.replace("new_dur = scanner_res['durability'] - 1", "new_dur = max(0, scanner_res['durability'] - 1)")

with open(filepath, 'w') as f:
    f.write(content)

print("Raid durability patched.")
