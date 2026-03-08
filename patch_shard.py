import re

# 1. Patch ai_worker.py (remove shard grant)
filepath = 'modules/services/ai_worker.py'
with open(filepath, 'r') as f:
    content = f.read()

# We need to remove the DB shard insert in generate_eidos_response_worker/generate_eidos_voice_worker
# Specifically looking for the block that inserts eidos_shard
block_to_remove = """        try:
            u = db.get_user(uid)
            first_name = u.get('first_name', 'Искатель') if u else 'Искатель'
            total_spent = u.get('total_spent', 0) if u else 0
            current_level = max(1, total_spent // 500)

            new_custom_data = json.dumps({
                "level": current_level,
                "lore": artifact_lore,
                "name": f"Синхронизатор Абсолюта: [{first_name}]"
            })

            with db.db_cursor() as cur:
                if cur:
                    cur.execute("DELETE FROM user_equipment WHERE uid = %s AND item_id = 'eidos_shard'", (uid,))
                    cur.execute("INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data) VALUES (%s, 'eidos_shard', 'eidos_shard', 100, %s) ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, custom_data = EXCLUDED.custom_data", (uid, new_custom_data))

        except Exception as e:
            logging.error(f"/// AI WORKER DB ERROR: {e}", exc_info=True)
            sentry_sdk.capture_exception(e)
            handle_failure("👁‍🗨 Сбой записи артефакта в матрицу.")
            return

        artifact_img_id = "AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA"

        final_caption = (
            f"📦 МАТЕРИАЛИЗОВАН АРТЕФАКТ: Синхронизатор Абсолюта: [{first_name}] (Уровень {current_level})\\n"
            f"Слот: Ментальное Ядро\\n"
            f"Память осколка: {artifact_lore}"
        )"""

# Instead of blindly replacing the exact block which might have tiny formatting differences,
# let's just use regex to remove everything from `try:\n            u = db.get_user(uid)` to `bot.send_photo`

import re
# The script is getting complex, let's do a precise string replacement on the parts.
content = re.sub(r'        try:\n\s+u = db\.get_user\(uid\).*?bot\.send_photo\(chat_id, artifact_img_id\)', '', content, flags=re.DOTALL)
content = re.sub(r'        if len\(final_caption\) > 1024:.*?bot\.send_photo\(chat_id, artifact_img_id, caption=final_caption\)', '', content, flags=re.DOTALL)
# actually let's just do it manually via python replace because regex on python code can be brittle.
