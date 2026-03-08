import os
import re

filepath = 'bot.py'
with open(filepath, 'r') as f:
    content = f.read()

# 1. Init Sentry
sentry_init = """
# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    except Exception as e:
        print(f"/// SENTRY INIT ERROR: {e}")
"""

if 'import sentry_sdk' not in content:
    content = content.replace('import psycopg2', 'import psycopg2\n' + sentry_init)

# 2. Pydantic Durability Clamping
durability_fix = """                item["uid"] = uid
                item['durability'] = max(0, item.get('durability', 0))"""
content = content.replace('                item["uid"] = uid', durability_fix)

# 3. Payload Expansion
profile_data_match = re.search(r'profile_data = \{\n.*?"avatar_url": avatar_url\n\s*\}', content, re.DOTALL)
if profile_data_match:
    original_profile_data = profile_data_match.group(0)
    new_profile_data = original_profile_data.replace(
        '"avatar_url": avatar_url\n            }',
        '"avatar_url": avatar_url,\n                "hp": user.get(\'hp\', 100),\n                "max_hp": user.get(\'max_hp\', 100),\n                "class": faction_name,\n                "anomalies": user.get(\'anomalies\', []),\n                "dossier": user.get(\'dossier\', ""),\n                "artifact_lore": user.get(\'artifact_lore\', "")\n            }'
    )
    content = content.replace(original_profile_data, new_profile_data)

# 4. JSON Payload Mapping
json_return = 'return flask.jsonify({"items": inventory_data, "equipped": equipped_data, "profile": profile_data}), 200'
new_json_return = 'return flask.jsonify({\n            "items": inventory_data,\n            "equipped": equipped_data,\n            "profile": profile_data,\n            "inventory": inventory_data,\n            "hp": profile_data.get("hp", 100),\n            "max_hp": profile_data.get("max_hp", 100),\n            "xp": profile_data.get("xp", 0),\n            "max_xp": profile_data.get("max_xp", 1000),\n            "level": profile_data.get("level", 1),\n            "biocoin": profile_data.get("biocoin", 0),\n            "class": profile_data.get("class", ""),\n            "atk": profile_data.get("atk", 0),\n            "def": profile_data.get("def", 0),\n            "anomalies": profile_data.get("anomalies", []),\n            "dossier": profile_data.get("dossier", ""),\n            "artifact_lore": profile_data.get("artifact_lore", "")\n        }), 200'

content = content.replace(json_return, new_json_return)

with open(filepath, 'w') as f:
    f.write(content)

print("Bot patched.")
