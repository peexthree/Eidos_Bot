import re

with open("database.py", "r") as f:
    content = f.read()

# 1. Add schema columns
schema_pattern = """        'ref_profit_xp': ('BIGINT', '0'),
        'ref_profit_coins': ('BIGINT', '0'),"""
schema_repl = """        'ref_profit_xp': ('BIGINT', '0'),
        'ref_profit_coins': ('BIGINT', '0'),
        'generated_ref_xp': ('BIGINT', '0'),
        'generated_ref_coins': ('BIGINT', '0'),"""
content = content.replace(schema_pattern, schema_repl)

# 2. Update add_xp_to_user
xp_pattern = """                if profit > 0:
                    cur.execute("UPDATE players SET xp = xp + %s, ref_profit_xp = ref_profit_xp + %s WHERE uid = %s", (profit, profit, ref_id))"""
xp_repl = """                if profit > 0:
                    cur.execute("UPDATE players SET xp = xp + %s, ref_profit_xp = ref_profit_xp + %s WHERE uid = %s", (profit, profit, ref_id))
                    cur.execute("UPDATE players SET generated_ref_xp = generated_ref_xp + %s WHERE uid = %s", (profit, uid))"""
content = content.replace(xp_pattern, xp_repl)

# 3. Update get_referrals_stats
ref_stats_pattern = """cur.execute("SELECT username, first_name, level, ref_profit_xp, ref_profit_coins FROM players WHERE referrer = %s ORDER BY ref_profit_xp DESC LIMIT 20", (str(uid),))"""
ref_stats_repl = """cur.execute("SELECT username, first_name, level, generated_ref_xp, generated_ref_coins FROM players WHERE referrer = %s ORDER BY generated_ref_xp DESC LIMIT 20", (str(uid),))"""
content = content.replace(ref_stats_pattern, ref_stats_repl)

with open("database.py", "w") as f:
    f.write(content)

print("Patched database.py for royalty tracking.")
