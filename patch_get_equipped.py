import re

with open('database.py', 'r') as f:
    content = f.read()

# Replace get_equipped_items_full
new_get_equipped_items_full = """def get_equipped_items_full(uid, cursor=None):
    slots = ['head', 'weapon', 'body', 'software', 'artifact']
    result = {slot: None for slot in slots}

    if cursor:
        cursor.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        for row in cursor.fetchall():
            if row["slot"] in slots:
                result[row["slot"]] = {"item_id": row["item_id"], "durability": row["durability"]}
        return result

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return result
        cur.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        for row in cur.fetchall():
            if row["slot"] in slots:
                result[row["slot"]] = {"item_id": row["item_id"], "durability": row["durability"]}
        return result"""

content = re.sub(r'def get_equipped_items_full\(uid, cursor=None\):.*?for row in cur\.fetchall\(\)\}', new_get_equipped_items_full, content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)
