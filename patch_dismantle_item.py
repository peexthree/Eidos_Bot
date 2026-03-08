import re

with open('database.py', 'r') as f:
    content = f.read()

# Replace dismantle_item
new_dismantle_item = """def dismantle_item(uid, inv_id):
    from config import ITEMS_INFO
    import cache_db
    success = False

    with db_cursor() as cur:
        if not cur: return False

        cur.execute("SELECT item_id, quantity FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
        res = cur.fetchone()
        if not res: return False

        item_id = res[0]
        qty = res[1]

        if qty > 1:
             cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id=%s", (inv_id,))
             success = True
        else:
             cur.execute("DELETE FROM inventory WHERE id=%s", (inv_id,))
             success = cur.rowcount > 0

        if success:
            item_info = ITEMS_INFO.get(item_id, {})
            rarity = item_info.get("rarity", "common").lower()

            coins_to_add = 0
            if rarity == "common":
                coins_to_add = 50
            elif rarity == "rare":
                coins_to_add = 150
            elif rarity == "epic":
                coins_to_add = 500
            elif rarity == "legendary":
                coins_to_add = 1500

            if coins_to_add > 0:
                cur.execute("UPDATE players SET biocoin = biocoin + %s WHERE uid = %s", (coins_to_add, uid))

    if success:
        cache_db.clear_cache(uid)

    return success"""

content = re.sub(r'def dismantle_item\(uid, inv_id\):.*?return cur\.rowcount > 0', new_dismantle_item, content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)
