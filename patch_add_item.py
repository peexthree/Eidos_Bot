import re

with open('database.py', 'r') as f:
    content = f.read()

# Replace add_item
new_add_item = """def add_item(uid, item_id, qty=1, cursor=None, specific_durability=None):
    from config import EQUIPMENT_DB, CURSED_CHEST_DROPS, ITEMS_INFO
    from psycopg2.extras import execute_values
    import cache_db

    success = False

    def _add_logic(cur):
        is_equipment = item_id in EQUIPMENT_DB
        item_info = ITEMS_INFO.get(item_id, {})
        max_stack = item_info.get("max_stack", 1) if not is_equipment else 1

        if is_equipment:
            cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
            res = cur.fetchone()
            count = (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0

            from config import INVENTORY_LIMIT
            if count + qty > int(INVENTORY_LIMIT or 20):
                return False

            if specific_durability:
                durability = specific_durability
            elif item_id in CURSED_CHEST_DROPS:
                durability = 50
            else:
                import random
                durability = random.randint(5, 10)

            values = [(uid, item_id, 1, durability, None) for _ in range(qty)]
            execute_values(cur, \"\"\"
                INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                VALUES %s
            \"\"\", values)
            return True
        else:
            cur.execute("SELECT id, quantity FROM inventory WHERE uid=%s AND item_id=%s ORDER BY id", (uid, item_id))
            stacks = cur.fetchall()

            remaining_qty = qty

            for stack in stacks:
                inv_id, current_qty = stack
                if isinstance(stack, dict):
                    inv_id = stack['id']
                    current_qty = stack['quantity']

                space_in_stack = max_stack - current_qty
                if space_in_stack > 0:
                    add_to_stack = min(remaining_qty, space_in_stack)
                    cur.execute("UPDATE inventory SET quantity = quantity + %s WHERE id = %s", (add_to_stack, inv_id))
                    remaining_qty -= add_to_stack
                if remaining_qty <= 0:
                    break

            if remaining_qty > 0:
                new_stacks_needed = (remaining_qty + max_stack - 1) // max_stack

                cur.execute("SELECT COUNT(*) FROM inventory WHERE uid = %s", (uid,))
                res = cur.fetchone()
                count = (res[0] if isinstance(res, tuple) else res.get("count") or res.get("count(*)")) if res else 0

                from config import INVENTORY_LIMIT
                if count + new_stacks_needed > int(INVENTORY_LIMIT or 20):
                    return False

                values = []
                while remaining_qty > 0:
                    stack_qty = min(remaining_qty, max_stack)
                    values.append((uid, item_id, stack_qty, 100, None))
                    remaining_qty -= stack_qty

                execute_values(cur, \"\"\"
                    INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                    VALUES %s
                \"\"\", values)
            return True

    if cursor:
        success = _add_logic(cursor)
    else:
        with db_cursor() as cur:
            if cur:
                success = _add_logic(cur)

    if success:
        cache_db.clear_cache(uid)

    return success"""

content = re.sub(r'def add_item\(uid, item_id, qty=1, cursor=None, specific_durability=None\):.*?return res', new_add_item, content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)
