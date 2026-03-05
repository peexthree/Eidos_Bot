with open("modules/handlers/menu.py", "r") as f:
    text = f.read()

old_str = "menu_update(call, txt, kb.leaderboard_menu(current_sort=sort_by), image_url=config.MENU_IMAGES[\"leaderboard\"])"
new_str = "menu_update(call, txt, kb.leaderboard_menu(current_sort=sort_by, leaders=leaders), image_url=config.MENU_IMAGES[\"leaderboard\"])"

text = text.replace(old_str, new_str)

# Add view_user_ handler
view_handler = """
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_user_"))
def view_user_handler(call):
    uid_str = call.data.replace("view_user_", "")
    try:
        target_uid = int(uid_str)
    except ValueError:
        bot.answer_callback_query(call.id, "Ошибка ID", show_alert=True)
        return

    stats, tu = get_user_stats(target_uid)
    if not tu:
        bot.answer_callback_query(call.id, "Пользователь не найден.", show_alert=True)
        return

    from modules.services.user import get_profile_stats
    profile_txt = get_profile_stats(target_uid)

    # Prepend info about who this is
    final_txt = f"👁 <b>НАБЛЮДЕНИЕ ЗА ОБЪЕКТОМ:</b> {tu['username'] or tu['first_name']}\\n\\n{profile_txt}"

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ К РЕЙТИНГУ", callback_data="leaderboard"))

    avatar = get_menu_image(tu)
    menu_update(call, final_txt, m, image_url=avatar)
"""

text += view_handler

with open("modules/handlers/menu.py", "w") as f:
    f.write(text)
