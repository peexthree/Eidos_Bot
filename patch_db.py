with open('database.py', 'r') as f:
    content = f.read()

content = content.replace(
"""            # Insert QTY times
            for _ in range(qty):
                cur.execute(\"\"\"
                    INSERT INTO inventory (uid, item_id, quantity, durability)
                    VALUES (%s, %s, 1, %s)
                \"\"\", (uid, item_id, durability))""",
"""            # Insert QTY times
            for _ in range(qty):
                cur.execute(\"\"\"
                    INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                    VALUES (%s, %s, 1, %s, NULL)
                \"\"\", (uid, item_id, durability))"""
)

content = content.replace(
"""                cur.execute(\"\"\"
                    INSERT INTO inventory (uid, item_id, quantity, durability)
                    VALUES (%s, %s, %s, 100)
                \"\"\", (uid, item_id, qty))""",
"""                cur.execute(\"\"\"
                    INSERT INTO inventory (uid, item_id, quantity, durability, custom_data)
                    VALUES (%s, %s, %s, 100, NULL)
                \"\"\", (uid, item_id, qty))"""
)

content = content.replace(
"""    query = "SELECT id, uid, item_id, quantity, durability FROM inventory WHERE quantity > 0 AND uid = %s ORDER BY item_id ASC\"""",
"""    query = "SELECT id, uid, item_id, quantity, durability, custom_data FROM inventory WHERE quantity > 0 AND uid = %s ORDER BY item_id ASC\""""
)

content = content.replace(
"""            # 1. Get item from inventory
            cur.execute("SELECT item_id, durability, quantity FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
            res = cur.fetchone()
            if not res: return False
            item_id, durability, qty = res

            # 2. Check if slot is occupied
            cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()""",
"""            # 1. Get item from inventory
            cur.execute("SELECT item_id, durability, quantity, custom_data FROM inventory WHERE id=%s AND uid=%s", (inv_id, uid))
            res = cur.fetchone()
            if not res: return False
            item_id, durability, qty, custom_data = res

            # 2. Check if slot is occupied
            cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()"""
)

content = content.replace(
"""            if old:
                # Unequip old item -> Move to Inventory
                old_item_id, old_dur = old
                if old_dur is None: old_dur = 10
                cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, %s)", (uid, old_item_id, old_dur))

            # 3. Equip new item
            # upsert into user_equipment
            cur.execute(\"\"\"
                INSERT INTO user_equipment (uid, slot, item_id, durability) VALUES (%s, %s, %s, %s)
                ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, durability = EXCLUDED.durability
            \"\"\", (uid, slot, item_id, durability))""",
"""            if old:
                # Unequip old item -> Move to Inventory
                old_item_id, old_dur, old_custom = old
                if old_dur is None: old_dur = 10
                cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, %s, %s)", (uid, old_item_id, old_dur, old_custom))

            # 3. Equip new item
            # upsert into user_equipment
            cur.execute(\"\"\"
                INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, durability = EXCLUDED.durability, custom_data = EXCLUDED.custom_data
            \"\"\", (uid, slot, item_id, durability, custom_data))"""
)

content = content.replace(
"""            cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if not old: return False

            item_id, durability = old
            if durability is None: durability = 10

            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))

            # Move to inventory using add_item to handle stacking and limits properly
            # We pass specific_durability to preserve the item's condition
            if not add_item(uid, item_id, 1, cursor=cur, specific_durability=durability):
                # If inventory is full, rollback the unequip
                raise Exception("Inventory Full")""",
"""            cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            old = cur.fetchone()
            if not old: return False

            item_id, durability, custom_data = old
            if durability is None: durability = 10

            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))

            # Move to inventory directly to preserve custom_data
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, %s, %s)", (uid, item_id, durability, custom_data))"""
)

content = content.replace(
"""        cursor.execute("SELECT slot, item_id, durability FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cursor.fetchall()}

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT slot, item_id, durability FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cur.fetchall()}""",
"""        cursor.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cursor.fetchall()}

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return {}
        cur.execute("SELECT slot, item_id, durability, custom_data FROM user_equipment WHERE uid=%s", (uid,))
        return {row['slot']: row['item_id'] for row in cur.fetchall()}"""
)

content = content.replace(
"""    if cursor:
        cursor.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cursor.fetchone()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT item_id, durability FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cur.fetchone()""",
"""    if cursor:
        cursor.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cursor.fetchone()

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return None
        cur.execute("SELECT item_id, durability, custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
        return cur.fetchone()"""
)

content = content.replace(
"""        if new_dur == 0:
            # Move to inventory (Broken)
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, 0)", (uid, item_id))
            return item_id # Signal that it broke""",
"""        if new_dur == 0:
            # Move to inventory (Broken)
            cur.execute("SELECT custom_data FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cd_res = cur.fetchone()
            custom_data = cd_res[0] if cd_res else None
            cur.execute("DELETE FROM user_equipment WHERE uid=%s AND slot=%s", (uid, slot))
            cur.execute("INSERT INTO inventory (uid, item_id, quantity, durability, custom_data) VALUES (%s, %s, 1, 0, %s)", (uid, item_id, custom_data))
            return item_id # Signal that it broke"""
)

content = content.replace(
"""        query = f"SELECT uid, first_name, username, COALESCE(xp, 0) as xp, COALESCE(level, 1) as level, COALESCE(max_depth, 0) as max_depth, COALESCE(biocoin, 0) as biocoin, path FROM players ORDER BY {order_clause} LIMIT %s\"""",
"""        # Join with user_equipment to fetch eidos_shard custom_data
        query = f\"\"\"
            SELECT p.uid, p.first_name, p.username, COALESCE(p.xp, 0) as xp, COALESCE(p.level, 1) as level,
                   COALESCE(p.max_depth, 0) as max_depth, COALESCE(p.biocoin, 0) as biocoin, p.path,
                   ue.custom_data as eidos_custom_data
            FROM players p
            LEFT JOIN user_equipment ue ON p.uid = ue.uid AND ue.slot = 'eidos_shard'
            ORDER BY p.{order_clause.replace('DESC', 'DESC').replace('ASC', 'ASC').replace('uid', 'p.uid').replace('xp', 'p.xp').replace('level', 'p.level').replace('max_depth', 'p.max_depth').replace('biocoin', 'p.biocoin')} LIMIT %s
        \"\"\""""
)

with open('database.py', 'w') as f:
    f.write(content)
