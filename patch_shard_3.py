import re

filepath = 'modules/services/ai_worker.py'
with open(filepath, 'r') as f:
    content = f.read()

# Replace block from `try:\n            u = db.get_user(uid)` to the end of the `except Exception as e:`
# that handles DB error.
pattern = r"        try:\n            u = db\.get_user\(uid\).*?handle_failure\(\"👁‍🗨 Сбой записи артефакта в матрицу\.\"\)\n            return"
content = re.sub(pattern, "", content, flags=re.DOTALL)

# Remove the photo logic
pattern2 = r"        artifact_img_id = \"AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA\".*?bot\.send_photo\(chat_id, artifact_img_id, caption=final_caption\).*?flush=True\)\n            except Exception as e:\n                logging\.error.*?capture_exception\(e\)"
content = re.sub(pattern2, "", content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)

# 2. Patch utils.py check_and_update_eidos_shard
filepath_utils = 'modules/services/utils.py'
with open(filepath_utils, 'r') as f:
    content_utils = f.read()

old_func_end = """                if current_level > 0:
                    try:
                         bot.send_message(chat_id, f"💠 <b>СИНДИКАТ:</b> Твой Синхронизатор Абсолюта достиг уровня {new_level}!", parse_mode="HTML")
                    except:
                         pass"""

new_func_end = """                if current_level > 0:
                    try:
                        bot.send_message(chat_id, f"📦 <b>АРТЕФАКТ ЭВОЛЮЦИОНИРОВАЛ:</b> Уровень {new_level}\\n\\nСвязь с Нейро-ядром установлена...", parse_mode="HTML")
                        from modules.services.worker_queue import enqueue_task
                        from modules.services.ai_worker import generate_eidos_response_worker
                        enqueue_task(generate_eidos_response_worker, bot, chat_id, uid, "artifact_evolution")
                    except Exception as e:
                        print(f"Error triggering artifact evolution: {e}")"""

content_utils = content_utils.replace(old_func_end, new_func_end)

with open(filepath_utils, 'w') as f:
    f.write(content_utils)

print("Shard logic patched.")
