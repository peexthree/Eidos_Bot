import re

with open('modules/services/ai_worker.py', 'r') as f:
    content = f.read()

# Replace the glitch image picking with the target user's actual avatar logic
# Also fix the import statement
old_glitch_logic = """                # Pick glitch image
                glitch_keys = list(GLITCH_IMAGES.keys())
                picked_glitch = random.choice(glitch_keys)
                img_id = GLITCH_IMAGES[picked_glitch]

                from telebot import types
                m = types.InlineKeyboardMarkup()
                m.add(types.InlineKeyboardButton("🔙 Вернуться к рейтингу", callback_data="leaderboard"))

                try:
                    bot.send_photo(chat_id, img_id, caption="<b>ДОСЬЕ ЗАГРУЖЕНО</b>", parse_mode="HTML")
                    bot.send_message(chat_id, ai_text, parse_mode="HTML", reply_markup=m)
                except Exception as e:
                    bot.send_message(chat_id, f"<b>ДОСЬЕ ЗАГРУЖЕНО</b>\\n\\n{ai_text}", parse_mode="HTML", reply_markup=m)"""

new_avatar_logic = """                # Pick target user's actual avatar
                from modules.services.utils import get_menu_image
                img_url = get_menu_image(target_user_data)

                from telebot import types
                m = types.InlineKeyboardMarkup()
                m.add(types.InlineKeyboardButton("🔙 Вернуться к рейтингу", callback_data="leaderboard"))

                try:
                    bot.send_photo(chat_id, img_url, caption="<b>ДОСЬЕ ЗАГРУЖЕНО</b>", parse_mode="HTML")
                    bot.send_message(chat_id, ai_text, parse_mode="HTML", reply_markup=m)
                except Exception as e:
                    bot.send_message(chat_id, f"<b>ДОСЬЕ ЗАГРУЖЕНО</b>\\n\\n{ai_text}", parse_mode="HTML", reply_markup=m)"""

content = content.replace(old_glitch_logic, new_avatar_logic)

with open('modules/services/ai_worker.py', 'w') as f:
    f.write(content)

print("AI worker logic patched to use target avatar.")
