import re

with open('bot.py', 'r', encoding='utf-8') as f:
    code = f.read()

def replace_profile(match):
    return """            profile_data = {
                "name": get_user_display_name(user),
                "username": user.get('username', ''),
                "level": level,
                "faction": faction_name,
                "biocoin": user.get('biocoin', 0),
                "xp": user.get('xp', 0),
                "max_xp": max_xp,
                "atk": stats.get('atk', 0),
                "def": stats.get('def', 0),
                "luck": stats.get('luck', 0),
                "signal": user.get('signal', 100),
                "avatar_url": avatar_url
            }"""

code = re.sub(r'            profile_data = \{\n.*?"avatar_url": avatar_url\n            \}', replace_profile, code, flags=re.DOTALL)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(code)
