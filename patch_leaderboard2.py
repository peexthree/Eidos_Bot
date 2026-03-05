with open('modules/handlers/menu.py', 'r') as f:
    content = f.read()

# Fix newline issue in the script output
content = content.replace('txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\n"\n', 'txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\\n"\n')
content = content.replace('txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\n\n"', 'txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\\n"\n')

with open('modules/handlers/menu.py', 'w') as f:
    f.write(content)
