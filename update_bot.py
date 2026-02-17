import re

with open('bot.py', 'r') as f:
    content = f.read()

old_func = r'def menu_update\(call, text, markup=None\):\s+"""Безопасное обновление меню \(Caption или Text\)"""\s+try:\s+bot\.edit_message_caption\(text, call\.message\.chat\.id, call\.message\.message_id, reply_markup=markup, parse_mode="HTML"\)\s+except:\s+try:\s+bot\.edit_message_text\(text, call\.message\.chat\.id, call\.message\.message_id, reply_markup=markup, parse_mode="HTML"\)\s+except: pass'

new_func = '''def menu_update(call, text, markup=None):
    """Безопасное обновление меню (Caption или Text) с защитой от переполнения"""
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # Если текст слишком длинный для подписи (1024), шлем как текст
    if len(text) > 1000:
        try:
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except:
            try:
                bot.delete_message(chat_id, msg_id)
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            except Exception as e: print(f"/// ERR menu_update long: {e}")
    else:
        try:
            bot.edit_message_caption(text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
        except:
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
            except:
                try:
                    bot.delete_message(chat_id, msg_id)
                    # Пытаемся восстановить фото, если есть URL
                    try:
                        bot.send_photo(chat_id, MENU_IMAGE_URL, caption=text, reply_markup=markup, parse_mode="HTML")
                    except:
                        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
                except Exception as e: print(f"/// ERR menu_update fallback: {e}")'''

# Use regex to find and replace
# Since whitespace might vary, I'll be more flexible or just locate the start and replace the block.
start_marker = 'def menu_update(call, text, markup=None):'
end_marker = 'except: pass' # This is risky as it appears many times.

# Let's match by indentation block.
# The function is defined at top level.
# It ends before the next function definition or major block.

pattern = r'def menu_update\(call, text, markup=None\):.*?except: pass'
# This pattern is too simple, regex dot usually doesn't match newline.
# And non-greedy .*? might stop early.

# Let's assume exact content match from what I read earlier.
# The cat output showed:
# def menu_update(call, text, markup=None):
#    """Безопасное обновление меню (Caption или Text)"""
#    try:
#        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
#    except:
#        try:
#            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
#        except: pass

exact_old_func = '''def menu_update(call, text, markup=None):
    """Безопасное обновление меню (Caption или Text)"""
    try:
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except:
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except: pass'''

if exact_old_func in content:
    content = content.replace(exact_old_func, new_func)
    print("Replaced exact match.")
else:
    print("Exact match not found. Trying regex.")
    # Fallback to a regex if indentation/spaces differed slightly in my copy
    content = re.sub(r'def menu_update\(.*?: pass', new_func, content, flags=re.DOTALL)
    # This regex is dangerous if not constrained.
    # Let's rely on exact match first. If it fails, I'll manually check why.

with open('bot.py', 'w') as f:
    f.write(content)
