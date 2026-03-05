with open('modules/handlers/menu.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "vip_display = get_user_display_name(l['uid'], name[:10]" in line:
        lines[i] = """            username = l.get('username')
            if username:
                display_name = f"@{username}"
            else:
                display_name = html.escape(name[:10])
            vip_display = get_user_display_name(l['uid'], display_name, custom_data=custom_data).replace('<b>', '').replace('</b>', '')
"""

with open('modules/handlers/menu.py', 'w') as f:
    f.writelines(lines)
