import telebot
import flask
import os
import time
import threading
import config
import database as db

# Import Bot Instance
from modules.bot_instance import bot, app, TOKEN, WEBHOOK_URL

# Import Handlers (Registers them)
import modules.handlers.start
import modules.handlers.admin
import modules.handlers.menu
import modules.handlers.items
import modules.handlers.gameplay

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
    with app.app_context():
        time.sleep(2)
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

threading.Thread(target=system_startup, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
