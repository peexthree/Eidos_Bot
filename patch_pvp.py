import re

with open("modules/services/pvp.py", "r") as f:
    content = f.read()

# Find blocked_by_fw block
pattern = """    if blocked_by_fw:
        return {
            'success': False,"""

replacement = """    if blocked_by_fw:
        import time
        with db.db_cursor() as cur:
            if cur:
                cur.execute(\"\"\"
                    INSERT INTO pvp_logs (attacker_uid, target_uid, stolen_coins, success, timestamp, is_revenged, is_anonymous)
                    VALUES (%s, %s, 0, False, %s, False, False)
                \"\"\", (attacker_uid, target_uid, int(time.time())))
        return {
            'success': False,"""

new_content = content.replace(pattern, replacement)

with open("modules/services/pvp.py", "w") as f:
    f.write(new_content)

print("Patched pvp.py")
