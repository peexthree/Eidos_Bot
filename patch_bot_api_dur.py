import re

with open('bot.py', 'r', encoding='utf-8') as f:
    code = f.read()

def replace_equipped(match):
    return """                    equipped_data[ui_slot] = {
                        "item_id": item_id,
                        "name": info.get('name', item_id),
                        "type": ui_slot,
                        "desc": info.get('desc', ''),
                        "rarity": info.get('rarity', 'common'),
                        "image_url": get_image_url(item_id, info),
                        "durability": durability
                    }"""

code = re.sub(r'                    equipped_data\[ui_slot\] = \{\n.*?"image_url": get_image_url\(item_id, info\)\n                    \}', replace_equipped, code, flags=re.DOTALL)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(code)
