with open("modules/services/ai_worker.py", "r") as f:
    text = f.read()

import re

insert_sql = """
    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO user_dossiers (uid, dossier_text) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET dossier_text = EXCLUDED.dossier_text, generated_at = CURRENT_TIMESTAMP", (target_uid, ai_text))
                conn.commit()
    except Exception as e:
        print(f"/// AI WORKER DB INSERT ERROR: {e}")
"""

text = text.replace('bot.send_message(chat_id, "❌ Не удалось пробить защиту объекта. Системный сбой.", parse_mode="HTML")\n        return', 'bot.send_message(chat_id, "❌ Не удалось пробить защиту объекта. Системный сбой.", parse_mode="HTML")\n        return\n' + insert_sql)

with open("modules/services/ai_worker.py", "w") as f:
    f.write(text)
print("done")
