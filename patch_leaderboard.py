with open("keyboards.py", "r") as f:
    content = f.read()

old_lb_menu = """def leaderboard_menu(current_sort='xp'):
    m = types.InlineKeyboardMarkup(row_width=2)
    txt_xp = "🏆 ОПЫТ"
    txt_depth = "🕳 ГЛУБИНА"
    txt_bio = "🩸 КАПИТАЛ"
    txt_spent = "💎 СИНДИКАТ"
    if current_sort == 'xp': txt_xp = f"✅ {txt_xp}"
    elif current_sort == 'depth': txt_depth = f"✅ {txt_depth}"
    elif current_sort == 'biocoin': txt_bio = f"✅ {txt_bio}"
    elif current_sort == 'spent': txt_spent = f"✅ {txt_spent}"
    m.add(
        types.InlineKeyboardButton(txt_xp, callback_data="lb_xp"),
        types.InlineKeyboardButton(txt_depth, callback_data="lb_depth")
    )
    m.add(
        types.InlineKeyboardButton(txt_bio, callback_data="lb_biocoin"),
        types.InlineKeyboardButton(txt_spent, callback_data="lb_spent")
    )
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ В МЕНЮ", callback_data="back"))
    return m"""

new_lb_menu = """def leaderboard_menu(current_sort='xp', leaders=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    txt_xp = "🏆 ОПЫТ"
    txt_depth = "🕳 ГЛУБИНА"
    txt_bio = "🩸 КАПИТАЛ"
    txt_spent = "💎 СИНДИКАТ"
    if current_sort == 'xp': txt_xp = f"✅ {txt_xp}"
    elif current_sort == 'depth': txt_depth = f"✅ {txt_depth}"
    elif current_sort == 'biocoin': txt_bio = f"✅ {txt_bio}"
    elif current_sort == 'spent': txt_spent = f"✅ {txt_spent}"

    # Add profile inspect buttons for top 5
    if leaders:
        inspect_btns = []
        for i, l in enumerate(leaders[:5], 1):
            num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][i-1]
            inspect_btns.append(types.InlineKeyboardButton(num, callback_data=f"view_user_{l['uid']}"))
        if inspect_btns:
            # Group into rows of up to 5
            m.add(*inspect_btns)

    m.add(
        types.InlineKeyboardButton(txt_xp, callback_data="lb_xp"),
        types.InlineKeyboardButton(txt_depth, callback_data="lb_depth")
    )
    m.add(
        types.InlineKeyboardButton(txt_bio, callback_data="lb_biocoin"),
        types.InlineKeyboardButton(txt_spent, callback_data="lb_spent")
    )
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ В МЕНЮ", callback_data="back"))
    return m"""

content = content.replace(old_lb_menu, new_lb_menu)

with open("keyboards.py", "w") as f:
    f.write(content)
