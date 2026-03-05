with open('modules/handlers/menu.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "txt += f\"{rank_icon} <b>{vip_display}</b> — {detail} ({val})" in line:
        lines[i] = "            txt += f\"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\\n\"\n"
    elif line == "\"\n" and "txt +=" in lines[i-1]:
        lines[i] = ""

with open('modules/handlers/menu.py', 'w') as f:
    f.writelines(lines)
