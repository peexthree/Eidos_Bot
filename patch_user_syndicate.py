with open("modules/services/user.py", "r") as f:
    content = f.read()

pattern = """        if isinstance(r, dict):
             username = r.get('username', 'Anon')
             level = r.get('level', 1)
             profit = r.get('ref_profit_xp', 0) + r.get('ref_profit_coins', 0)
        else:
             username = r[0]
             level = r[2]
             profit = r[3] + r[4]

        total_profit += profit
        txt += f"👤 <b>@{username}</b> (Lvl {level})\\n   └ 💸 Роялти: +{profit}\\n"

    txt += f"\\n💰 <b>ВСЕГО ПОЛУЧЕНО:</b> {total_profit}\""""

replacement = """        if isinstance(r, dict):
             username = r.get('username', 'Anon')
             level = r.get('level', 1)
             # now these map to generated_ref_xp and generated_ref_coins
             profit = r.get('generated_ref_xp', 0) + r.get('generated_ref_coins', 0)
        else:
             username = r[0]
             level = r[2]
             profit = r[3] + r[4]

        txt += f"👤 <b>@{username}</b> (Lvl {level})\\n   └ 💸 Роялти: +{profit}\\n"

    u = db.get_user(uid)
    if u:
        total_profit = u.get('ref_profit_xp', 0) + u.get('ref_profit_coins', 0)
    else:
        total_profit = 0

    txt += f"\\n💰 <b>ВСЕГО ПОЛУЧЕНО:</b> {total_profit}\""""

content = content.replace(pattern, replacement)

with open("modules/services/user.py", "w") as f:
    f.write(content)

print("Patched user.py")
