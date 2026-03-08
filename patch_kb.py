filepath = 'keyboards.py'
with open(filepath, 'r') as f:
    content = f.read()

content = content.replace('types.InlineKeyboardButton("🧬 УНИЧТОЖИТЬ АНОМАЛИЮ (1000 BC)", callback_data="remove_anomaly")', 'types.InlineKeyboardButton("🧬 Уничтожить аномалию", callback_data="remove_anomaly")')

with open(filepath, 'w') as f:
    f.write(content)
print("KB patched")
