with open("modules/services/utils.py", "r") as f:
    content = f.read()

pattern = """    if cursor:
        cursor.execute(sql, tuple(params))
    else:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))"""

replacement = """    if cursor:
        cursor.execute(sql, tuple(params))
        # Referrer logic
        if amount > 0:
            cursor.execute("SELECT referrer FROM players WHERE uid = %s", (uid,))
            res = cursor.fetchone()
            if res and res[0]:
                ref_id = res[0]
                profit = int(amount * 0.1)
                if profit > 0:
                    cursor.execute("UPDATE players SET biocoin = biocoin + %s, ref_profit_coins = ref_profit_coins + %s WHERE uid = %s", (profit, profit, ref_id))
                    cursor.execute("UPDATE players SET generated_ref_coins = generated_ref_coins + %s WHERE uid = %s", (profit, uid))
    else:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                # Referrer logic
                if amount > 0:
                    cur.execute("SELECT referrer FROM players WHERE uid = %s", (uid,))
                    res = cur.fetchone()
                    if res and res[0]:
                        ref_id = res[0]
                        profit = int(amount * 0.1)
                        if profit > 0:
                            cur.execute("UPDATE players SET biocoin = biocoin + %s, ref_profit_coins = ref_profit_coins + %s WHERE uid = %s", (profit, profit, ref_id))
                            cur.execute("UPDATE players SET generated_ref_coins = generated_ref_coins + %s WHERE uid = %s", (profit, uid))"""

content = content.replace(pattern, replacement)

with open("modules/services/utils.py", "w") as f:
    f.write(content)

print("Patched utils.py")
