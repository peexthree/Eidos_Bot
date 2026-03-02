import database as db
import config
from contextlib import contextmanager

print("/// RUNNING MIGRATION SCRIPT")

db.init_db()
print("/// DB SCHEMA INIT COMPLETE")

try:
    with db.db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE raid_content SET text = 'Я даю тебе то, что ты боишься потерять... (Ответ: Жизнь)' WHERE text LIKE '%я даю тебе то%' AND text NOT LIKE '%(Ответ:%'")
            print("/// RIDDLE FIX APPLIED")
except Exception as e:
    print(f"/// RIDDLE FIX ERR: {e}")

try:
    with db.db_session() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO players (uid) VALUES (%s) ON CONFLICT DO NOTHING", (config.ADMIN_ID,))
            cur.execute("UPDATE players SET is_admin = TRUE WHERE uid = %s", (config.ADMIN_ID,))
            print(f"/// ADMIN SYNC: {config.ADMIN_ID} rights granted.")
except Exception as e:
    print(f"/// ADMIN SYNC ERROR: {e}")

print("/// MIGRATION SCRIPT COMPLETE")
