with open('modules/handlers/menu.py', 'r') as f:
    content = f.read()

checks = {
    "Nickname wrapping 1": 'display_name = f"<code>@{username}</code>"',
    "Nickname wrapping 2": 'display_name = f"<code>{html.escape(l[\'first_name\'] or \'Unknown\')}</code>"',
    "menu_update in init": 'menu_update(call, txt, m)',
    "players table in search": 'SELECT uid, username, first_name, level, xp, biocoin, total_spent, path FROM players WHERE username ILIKE'
}

import html
all_pass = True
for name, snippet in checks.items():
    if snippet in content:
        print(f"✅ {name} found.")
    else:
        print(f"❌ {name} NOT found.")
        all_pass = False

if not all_pass:
    exit(1)
