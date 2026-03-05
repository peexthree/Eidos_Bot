with open('modules/handlers/menu.py', 'r') as f:
    lines = f.readlines()

new_handlers = """
@bot.callback_query_handler(func=lambda call: call.data == "find_user_dossier_init")
def find_user_dossier_init_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно BioCoin (нужно 100 BC)", show_alert=True)
        return

    txt = "⚠️ <b>Внимание!</b> Доступ к защищенному досье «Паспорт Осколка» стоит <b>100 BC</b>.\\nПродолжить?"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("✅ Да, взломать (100 BC)", callback_data="find_user_dossier_confirm"))
    m.add(types.InlineKeyboardButton("❌ Отмена", callback_data="leaderboard"))

    bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=m)


@bot.callback_query_handler(func=lambda call: call.data == "find_user_dossier_confirm")
def find_user_dossier_confirm_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно BioCoin", show_alert=True)
        return

    db.set_state(uid, "await_dossier_search")

    txt = "⚠️ <b>СИСТЕМА:</b> Введите <b>@username</b> пользователя для взлома его досье.\\n<i>(Вы можете скопировать ник из списка Зала Славы)</i>"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("❌ Отмена", callback_data="leaderboard"))

    bot.edit_message_text(txt, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=m)
"""

with open('modules/handlers/menu.py', 'a') as f:
    f.write(new_handlers)

print("Appended.")
