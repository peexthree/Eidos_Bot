import telebot
import flask
import os
import sys
import time
import threading
import traceback

sys.stdout.reconfigure(line_buffering=True)
import config
import database as db

# Import Bot Instance
from modules.bot_instance import bot, app, TOKEN, WEBHOOK_URL

# --- QUARANTINE & ONBOARDING MIDDLEWARE ---
QUARANTINE_CACHE = {}

# Initialization Flag
DB_READY = threading.Event()

def check_quarantine(user):
    # SIMPLE CHECK: Skip DB for bots or system messages
    if not user or user.is_bot: return False

    uid = user.id

    # CACHE CHECK
    if uid in QUARANTINE_CACHE:
        is_q, expiry = QUARANTINE_CACHE[uid]
        if time.time() < expiry:
            return is_q

    print("/// DB CALL START (check_quarantine)")
    try:
        # statement_timeout is set to 2s in DB connection pool
        u = db.get_user(uid)
    except Exception as e:
        print("/// TIMEOUT/ERROR: check_quarantine DB CALL FAILED")
        import traceback; traceback.print_exc()
        QUARANTINE_CACHE[uid] = (False, time.time() + 5) # Short cache on error
        return False
    print("/// DB CALL END (check_quarantine)")
    if not u:
        QUARANTINE_CACHE[uid] = (False, time.time() + 60)
        return False

    # 1. Check if already quarantined
    if u.get('is_quarantined'):
        quarantine_end_time = u.get('quarantine_end_time', 0)
        try:
            quarantine_end_time = float(quarantine_end_time)
        except (ValueError, TypeError):
            quarantine_end_time = 0

        if time.time() < quarantine_end_time:
            QUARANTINE_CACHE[uid] = (True, time.time() + 60)
            return True
        else:
            # Quarantine expired
            db.update_user(uid, is_quarantined=False)
            QUARANTINE_CACHE[uid] = (False, time.time() + 60)
            return False

    # 2. Check Sleep Timer (Only for Levels < 2 and active onboarding)
    # Stage > 0 means started.
    level = u.get('level', 1)
    onboarding_stage = u.get('onboarding_stage', 0)
    try:
        level = int(level)
        onboarding_stage = int(onboarding_stage)
    except (ValueError, TypeError):
        level = 1
        onboarding_stage = 0

    if level < 2 and onboarding_stage > 0:
        start_time = u.get('onboarding_start_time', 0)
        try:
            start_time = float(start_time)
        except (ValueError, TypeError):
            start_time = 0

        if start_time > 0:
            elapsed = time.time() - start_time
            if elapsed > 86400: # 24 hours
                 db.quarantine_user(uid)
                 QUARANTINE_CACHE[uid] = (True, time.time() + 60)
                 return True

    QUARANTINE_CACHE[uid] = (False, time.time() + 60)
    return False


# Import Handlers (Registers them)
# Handlers Order Preserved
import modules.handlers.start
import modules.handlers.admin
import modules.handlers.menu
import modules.handlers.items
import modules.handlers.gameplay
import modules.handlers.onboarding
import modules.handlers.pvp
import modules.handlers.glitch_handler
import modules.handlers.eidos_room

# --- MIDDLEWARE FOR STATS TRACKING & GLITCHES ---
@bot.middleware_handler(update_types=['message'])
def stats_message_middleware(bot_instance, message):
    # RUN IN THREAD TO PREVENT BLOCKING
    def run_middleware():
        try:
            uid = message.from_user.id
            # db.increment_user_stat(uid, 'messages')
            import database as db
            db.increment_user_stat(uid, 'messages')
        except: pass

    import threading
    threading.Thread(target=run_middleware, daemon=True).start()
@bot.middleware_handler(update_types=['callback_query'])
def stats_callback_middleware(bot_instance, call):
    # RUN IN THREAD TO PREVENT BLOCKING
    def run_middleware():
        try:
            uid = call.from_user.id
            import database as db
            db.increment_user_stat(uid, 'clicks')
        except: pass

    import threading
    threading.Thread(target=run_middleware, daemon=True).start()
def process_update_safe(update):
    try:
        bot.process_new_updates([update])
    except Exception as e:
        print(f"/// UNHANDLED EXCEPTION IN UPDATE THREAD: {e}")
        import traceback; traceback.print_exc()

@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            DB_READY.wait(timeout=10)
            print("/// WEBHOOK RECEIVED")
            # 1. Get raw data
            json_string = flask.request.get_data().decode('utf-8')
            print(f"/// WEBHOOK JSON: {json_string}")
            if not json_string:
                return 'Empty Data', 200

            # 2. Parse JSON safely
            try:
                update = telebot.types.Update.de_json(json_string)
                # Check if de_json returned None (unlikely for valid JSON string but possible)
                if update is None:
                    return 'Invalid JSON', 200
            except TypeError:
                # Catches "TypeError: 'NoneType' object is not subscriptable" when input is "null"
                # Log as warning but return 200 to stop retries
                print(f"/// WEBHOOK WARNING: Received 'null' or invalid payload.")
                return 'Invalid Payload', 200
            except Exception as e:
                print(f"/// WEBHOOK PARSE ERROR: {e}")
                return 'Parse Error', 200

            # 3. Process Update
            print("/// WEBHOOK: STARTING THREAD TO PROCESS UPDATE")
            print("/// WEBHOOK: --- THREAD CREATION TRIGGERED ---")
            threading.Thread(target=process_update_safe, args=(update,)).start()
            print("/// WEBHOOK: --- THREAD CREATION SUCCESS ---")
            print("/// WEBHOOK: THREAD STARTED")
            return 'ALIVE', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
            traceback.print_exc()
            return 'Error', 500

@app.route("/", methods=["GET"])
def index():
    return "Eidos SQL Interface is Operational", 200

def system_startup():
    try:
        with app.app_context():
            # time.sleep(2)  # Removed for faster startup on Render
            print("/// SYSTEM STARTUP INITIATED...")
            db.init_db()
            print("/// DB INIT COMPLETE")

            # FIX: Broken Riddle
            try:
                db.admin_exec_query("UPDATE raid_content SET text = 'Я даю тебе то, что ты боишься потерять... (Ответ: Жизнь)' WHERE text LIKE '%я даю тебе то%' AND text NOT LIKE '%(Ответ:%'")
                print("/// RIDDLE FIX APPLIED")
            except Exception as e:
                print(f"/// RIDDLE FIX ERR: {e}")

            # Sync Admin from Config
            try:
                db.set_user_admin(config.ADMIN_ID, True)
                print(f"/// ADMIN SYNC: {config.ADMIN_ID} rights granted.")
            except Exception as e:
                print(f"/// ADMIN SYNC ERROR: {e}")

            if WEBHOOK_URL:
                try:
                    bot.remove_webhook()
                    bot.set_webhook(url=WEBHOOK_URL + "/webhook")
                    print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
                except Exception as e:
                    print(f"/// WEBHOOK ERROR: {e}")
                    traceback.print_exc()
            else:
                print("/// WARNING: WEBHOOK_URL not set. Bot will not receive updates via Webhook.")

            # Signal DB is ready
            DB_READY.set()
            print("/// DB_READY SIGNAL SET")

    except Exception as e:
        print(f"/// SYSTEM STARTUP FATAL ERROR: {e}")

def notification_loop():
    # Wait for DB to be initialized
    if not DB_READY.wait(timeout=300): # Wait up to 5 mins
        print("/// NOTIFICATION LOOP TIMEOUT: DB NOT READY")
        return

    while True:
        try:
            with db.db_session() as conn:
                with conn.cursor() as cur:
                    now = int(time.time())
                    # Check Protocol Cooldowns
                    cur.execute("""
                        SELECT uid FROM players
                        WHERE last_protocol_time > 0
                        AND (last_protocol_time + 1800) < %s
                        AND notified = FALSE
                        AND is_active = TRUE
                        LIMIT 50
                    """, (now,))
                    users = cur.fetchall()

                    for row in users:
                        uid = row[0]
                        try:
                            bot.send_message(uid, "🔄 <b>СИНХРОНИЗАЦИЯ ГОТОВА</b>\nНовые знания ждут тебя.", parse_mode="HTML")
                            # Update immediately to prevent duplicate sends if loop crashes or slow
                            with db.db_session() as conn2:
                                with conn2.cursor() as cur2:
                                    cur2.execute("UPDATE players SET notified = TRUE WHERE uid = %s", (uid,))
                            time.sleep(0.2)
                        except Exception as e:
                            print(f"Notify Error {uid}: {e}")
                            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                                with db.db_session() as conn3:
                                    with conn3.cursor() as cur3:
                                        cur3.execute("UPDATE players SET is_active = FALSE WHERE uid = %s", (uid,))
        except Exception as e:
            print(f"/// NOTIFICATION LOOP ERROR: {e}")

        time.sleep(60)

threading.Thread(target=system_startup, daemon=True).start()
threading.Thread(target=notification_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)

import modules.handlers.eidos_room
