import re

with open("modules/handlers/gameplay.py", "r") as f:
    text = f.read()

old_block = """    if call.data == "zero_layer_menu":
         cost = get_raid_entry_cost(uid)
         try: bot.answer_callback_query(call.id)
         except: pass
         menu_update(call, f"🚀 <b>---НУЛЕВОЙ СЛОЙ---</b>\\nВаш текущий опыт: {int(u.get('xp', 0) or 0)}\\nСтоимость входа: {cost}", kb.raid_welcome_keyboard(cost), image_url=config.MENU_IMAGES["zero_layer_menu"])"""

new_block = """    if call.data == "zero_layer_menu":
         import database as _db
         session = None
         with _db.db_cursor() as cur:
             if cur:
                 cur.execute("SELECT depth FROM raid_sessions WHERE uid=%s", (uid,))
                 session = cur.fetchone()

         if session:
             try: bot.answer_callback_query(call.id)
             except: pass
             m = types.InlineKeyboardMarkup()
             m.add(types.InlineKeyboardButton("♻️ ПРОДОЛЖИТЬ ПОХОД", callback_data="raid_step"))
             m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
             menu_update(call, f"⚠️ <b>ВНИМАНИЕ</b>\\n\\nВы уже находитесь в рейде (Глубина: {session[0] if isinstance(session, tuple) else session.get('depth')}).\\nВаш сигнал зафиксирован в Пустоши.", m, image_url=config.MENU_IMAGES["zero_layer_menu"])
         else:
             cost = get_raid_entry_cost(uid)
             try: bot.answer_callback_query(call.id)
             except: pass
             menu_update(call, f"🚀 <b>---НУЛЕВОЙ СЛОЙ---</b>\\nВаш текущий опыт: {int(u.get('xp', 0) or 0)}\\nСтоимость входа: {cost}", kb.raid_welcome_keyboard(cost), image_url=config.MENU_IMAGES["zero_layer_menu"])"""

text = text.replace(old_block, new_block)

with open("modules/handlers/gameplay.py", "w") as f:
    f.write(text)
