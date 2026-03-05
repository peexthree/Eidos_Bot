import re

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # We replace: bot.answer_callback_query(call.id, f"🌀 {glitch['message']}", show_alert=True)
    # with:
    # bot.answer_callback_query(call.id, "🌀 СИСТЕМНАЯ АНОМАЛИЯ", show_alert=True)
    # bot.send_message(uid, f"🌀 <b>СИСТЕМНАЯ АНОМАЛИЯ</b>\\n\\n{glitch['message']}", parse_mode="HTML")

    old_str = 'bot.answer_callback_query(call.id, f"🌀 {glitch[\'message\']}", show_alert=True)'
    new_str = 'bot.answer_callback_query(call.id, "🌀 СИСТЕМНАЯ АНОМАЛИЯ", show_alert=True)\n            bot.send_message(uid, f"🌀 <b>СИСТЕМНАЯ АНОМАЛИЯ</b>\\n\\n{glitch[\'message\']}", parse_mode="HTML")'

    content = content.replace(old_str, new_str)

    with open(filepath, 'w') as f:
        f.write(content)

patch_file("modules/handlers/menu.py")
patch_file("modules/handlers/items.py")

# In gameplay.py, the glitch message is already added to reward_text.
# reward_text = f"\n\n🌀 <b>{glitch['message']}</b>"
# It is sent as part of the loading effect text. This is probably fine since it's fully readable there.
