import telebot
import flask
import os
import time
import threading
import config
import database as db

# Import Bot Instance
from modules.bot_instance import bot, app, TOKEN, WEBHOOK_URL

# --- QUARANTINE & ONBOARDING MIDDLEWARE ---
QUARANTINE_CACHE = {}

def check_quarantine(user):
    # SIMPLE CHECK: Skip DB for bots or system messages
    if not user or user.is_bot: return False

    uid = user.id

    # CACHE CHECK
    if uid in QUARANTINE_CACHE:
        is_q, expiry = QUARANTINE_CACHE[uid]
        if time.time() < expiry:
            return is_q

    u = db.get_user(uid)
    if not u:
        QUARANTINE_CACHE[uid] = (False, time.time() + 60)
        return False

    # 1. Check if already quarantined
    if u.get('is_quarantined'):
        if time.time() < u.get('quarantine_end_time', 0):
            QUARANTINE_CACHE[uid] = (True, time.time() + 60)
            return True
        else:
            # Quarantine expired
            db.update_user(uid, is_quarantined=False)
            QUARANTINE_CACHE[uid] = (False, time.time() + 60)
            return False

    # 2. Check Sleep Timer (Only for Levels < 2 and active onboarding)
    # Stage > 0 means started.
    if u.get('level', 1) < 2 and u.get('onboarding_stage', 0) > 0:
        start_time = u.get('onboarding_start_time', 0)
        if start_time > 0:
            elapsed = time.time() - start_time
            if elapsed > 86400: # 24 hours
                 db.quarantine_user(uid)
                 QUARANTINE_CACHE[uid] = (True, time.time() + 60)
                 return True

    QUARANTINE_CACHE[uid] = (False, time.time() + 60)
    return False

@bot.message_handler(func=lambda m: check_quarantine(m.from_user))
def quarantine_message_handler(m):
    u = db.get_user(m.from_user.id)
    rem_time = int((u['quarantine_end_time'] - time.time()) / 3600)
    if rem_time < 0: rem_time = 0
    msg = (
        "⛔️ <b>ДОСТУП ЗАБЛОКИРОВАН</b>\n\n"
        "Ты упустил окно возможностей. Система распознала в тебе спящий NPC.\n"
        "Возвращайся в свой сон.\n\n"
        f"⏳ Повторная попытка Сборки будет доступна через <b>{rem_time} часов</b>."
    )
    try:
        bot.send_message(m.chat.id, msg, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: check_quarantine(c.from_user))
def quarantine_callback_handler(c):
    try:
        bot.answer_callback_query(c.id, "⛔️ ТЫ СПИШЬ. ДОСТУП ЗАПРЕЩЕН.", show_alert=True)
    except: pass

# Import Handlers (Registers them)
import modules.handlers.start
import modules.handlers.admin
import modules.handlers.menu
import modules.handlers.items
import modules.handlers.gameplay
import modules.handlers.onboarding

# --- MIDDLEWARE FOR STATS TRACKING ---
@bot.middleware_handler(update_types=['message'])
def stats_message_middleware(bot_instance, message):
    try:
        uid = message.from_user.id
        db.increment_user_stat(uid, 'messages')
    except: pass

@bot.middleware_handler(update_types=['callback_query'])
def stats_callback_middleware(bot_instance, call):
    try:
        uid = call.from_user.id
        db.increment_user_stat(uid, 'clicks')
    except: pass

@app.route('/health', methods=['GET'])
def health_check():
    return 'ALIVE', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))])
            return 'ALIVE', 200
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
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
    except Exception as e:
        print(f"/// SYSTEM STARTUP FATAL ERROR: {e}")

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
