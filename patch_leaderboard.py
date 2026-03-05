import re

with open('modules/handlers/menu.py', 'r') as f:
    content = f.read()

# Replace top 3 header format
# From: header = f"{rank_icon} [{detail}] {vip_display} <i>({path_icon})</i> — <b>{val}</b>"
# To:   header = f"{rank_icon} {vip_display} ({detail}) <i>{path_icon}</i> — <b>{val}</b>"
content = re.sub(
    r'header = f"\{rank_icon\} \[\{detail\}\] \{vip_display\} <i>\(\{path_icon\}\)</i> — <b>\{val\}</b>"',
    r'header = f"{rank_icon} {vip_display} ({detail}) <i>{path_icon}</i> — <b>{val}</b>"',
    content
)

# Replace 4+ format
# From: txt += f"<code>{i:<2} {vip_display:<15} | {detail} | {val}</code>\n"
# To:   txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\n"
content = re.sub(
    r'txt \+= f"<code>\{i:<2\} \{vip_display:<15\} \| \{detail\} \| \{val\}</code>\\n"',
    r'txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\n"',
    content
)

with open('modules/handlers/menu.py', 'w') as f:
    f.write(content)

print("Patched.")
