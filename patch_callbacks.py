import os

filepath = 'modules/services/utils.py'
with open(filepath, 'r') as f:
    content = f.read()

safe_callback_func = """
from telebot.apihelper import ApiTelegramException
import logging

def safe_answer_callback(bot, call_id, text=None, show_alert=False):
    try:
        if text:
            bot.answer_callback_query(call_id, text, show_alert=show_alert)
        else:
            bot.answer_callback_query(call_id)
    except ApiTelegramException as e:
        if "query is too old" in str(e):
            pass # Ignore, the user clicked too long ago or network lagged
        else:
            logging.error(f"Callback answer error: {e}")
    except Exception as e:
        logging.error(f"Unexpected callback error: {e}")
"""

if 'def safe_answer_callback' not in content:
    content = content + "\n" + safe_callback_func

with open(filepath, 'w') as f:
    f.write(content)

# Patch handlers
handlers_dir = 'modules/handlers'
for filename in os.listdir(handlers_dir):
    if filename.endswith('.py'):
        file_path = os.path.join(handlers_dir, filename)
        with open(file_path, 'r') as f:
            file_content = f.read()

        if 'bot.answer_callback_query' in file_content:
            if 'from modules.services.utils import safe_answer_callback' not in file_content:
                # Insert import near the top
                file_content = 'from modules.services.utils import safe_answer_callback\n' + file_content

            file_content = file_content.replace('bot.answer_callback_query(call.id', 'safe_answer_callback(bot, call.id')

            with open(file_path, 'w') as f:
                f.write(file_content)

print("Callbacks patched.")
