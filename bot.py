from modules.services.worker_queue import start_worker
import logging_setup
import cache_db
import telebot
import flask
import os
import sys
import time
import threading
import traceback
import psycopg2

sys.stdout.reconfigure(line_buffering=True)
import config
import database as db

# Import Bot Instance
from modules.bot_instance import bot, app, TOKEN, WEBHOOK_URL

# --- QUARANTINE & ONBOARDING MIDDLEWARE ---
QUARANTINE_CACHE = {}

# Initialization Flag
# DB_READY removed in favor of direct DB pool check

# def check_quarantine(user):
#     return False


# Import Handlers (Registers them)
# Handlers Order Preserved
import modules.handlers.start
import modules.handlers.admin
import modules.handlers.eidos_room
import modules.handlers.glitch_handler
import modules.handlers.menu
import modules.handlers.items
import modules.handlers.gameplay
import modules.handlers.onboarding
import modules.handlers.pvp


import queue
STATS_QUEUE = queue.Queue()

def stats_worker():
    print("/// STATS WORKER STARTED")
    while True:
        try:
            task = STATS_QUEUE.get()
            if task is None: break
            uid, stat_type = task
            db.increment_user_stat(uid, stat_type)
        except Exception as e:
            print(f"/// STATS WORKER ERR: {e}")
        finally:
            STATS_QUEUE.task_done()

threading.Thread(target=stats_worker, daemon=True).start()

# --- MIDDLEWARE FOR STATS TRACKING & GLITCHES ---
@bot.middleware_handler(update_types=['message'])
def stats_message_middleware(bot_instance, message):
    try:
        uid = int(message.from_user.id)
        STATS_QUEUE.put((uid, 'messages'))
    except: pass
@bot.middleware_handler(update_types=['callback_query'])
def stats_callback_middleware(bot_instance, call):
    try:
        uid = int(call.from_user.id)
        STATS_QUEUE.put((uid, 'clicks'))
    except: pass
def process_update_safe(update):
    try:
        uid = getattr(update.message or update.callback_query, "from_user", None)
        uid = int(uid.id) if uid else 0
        print(f"/// DEBUG: Starting process_new_updates for update {update.update_id} (User: {uid})")
        bot.process_new_updates([update])
        print(f"/// DEBUG: Finished process_new_updates for update {update.update_id}")
    except Exception as e:
        print(f"/// UNHANDLED EXCEPTION IN UPDATE THREAD: {e}")
        import traceback; traceback.print_exc()

@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    print("/// WEBHOOK ENDPOINT HIT")
    if flask.request.method == 'POST':
        try:
            # 1. Get raw data
            json_string = flask.request.get_data().decode('utf-8')
            print(f"/// WEBHOOK RECEIVED PAYLOAD: {json_string}")
            if not json_string:
                print("/// WEBHOOK ERROR: Received empty payload")
                return 'Empty Data', 200

            # 2. Parse JSON safely
            try:
                update = telebot.types.Update.de_json(json_string)
                if update is None:
                    print("/// WEBHOOK ERROR: telebot.types.Update.de_json returned None")
                    return 'Invalid JSON', 200
            except TypeError:
                print(f"/// WEBHOOK WARNING: Received 'null' or invalid payload.")
                return 'Invalid Payload', 200
            except Exception as e:
                print(f"/// WEBHOOK PARSE ERROR: {e}")
                return 'Parse Error', 200

            # 3. Process Update
            print(f"/// WEBHOOK: STARTING THREAD TO PROCESS UPDATE {update.update_id}")
            threading.Thread(target=process_update_safe, args=(update,)).start()
            return 'ALIVE', 200
        except Exception as e:
            print(f"/// WEBHOOK CRITICAL ERROR: {e}")
            traceback.print_exc()
            return 'Error', 500

@app.route("/", methods=["GET"])
def index():
    return "Eidos SQL Interface is Operational", 200

@app.route('/inventory', methods=['GET'])
def inventory_webapp():
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return flask.send_from_directory(static_dir, 'inventory.html')

@app.route('/api/inventory', methods=['GET'])
def inventory_api():
    uid = flask.request.args.get('uid')
    if not uid:
        return flask.jsonify({"error": "Missing uid"}), 400
    try:
        uid = int(uid)
        inventory_data = []
        equipped_data = {}

        def get_image_url(item_id, info):
            if info.get('url'):
                return info.get('url')
            file_id = info.get('file_id')

            if not file_id:
                if hasattr(config, 'ITEM_IMAGES') and item_id in config.ITEM_IMAGES:
                    file_id = config.ITEM_IMAGES[item_id]

            if file_id:
                try:
                    return bot.get_file_url(file_id)
                except Exception as e:
                    print(f"/// API INVENTORY ERROR GETTING FILE_ID: {e}")
            return None

        # 1. Загружаем экипировку (исправляем маппинг типов)
        raw_equipped = db.get_user_equipment(uid) if hasattr(db, 'get_user_equipment') else {}
        if raw_equipped:
            for slot, item_id in raw_equipped.items():
                if item_id:
                    info = config.ITEMS_INFO.get(item_id, {})
                    # Важно: приводим slot к единому стандарту фронтенда
                    ui_slot = slot.replace('helmet', 'head').replace('armor', 'body')
                    equipped_data[ui_slot] = {
                        "item_id": item_id,
                        "name": info.get('name', item_id),
                        "type": ui_slot,
                        "desc": info.get('desc', ''),
                        "rarity": info.get('rarity', 'common'),
                        "image_url": get_image_url(item_id, info)
                    }

        # 2. Загружаем инвентарь
        items = db.get_inventory(uid)
        for item in items:
            item_id = item.get('item_id')

            # Filter out PVP items from general inventory to match telegram logic
            if item_id in config.PVP_ITEMS:
                continue

            qty = item.get('quantity', 0)
            item_info = config.ITEMS_INFO.get(item_id, {})

            # Определяем категорию для фильтров фронтенда
            raw_type = item_info.get('type', 'misc')
            category = raw_type
            if raw_type in ['weapon'] or item_info.get('slot') == 'weapon': category = 'weapon'
            elif raw_type in ['head', 'helmet', 'body', 'armor'] or item_info.get('slot') in ['head', 'helmet', 'body', 'armor']: category = 'armor'
            elif raw_type in ['software'] or item_info.get('slot') == 'software': category = 'software'
            elif raw_type in ['artifact'] or item_info.get('slot') == 'artifact': category = 'artifact'
            elif raw_type in ['consumable', 'misc']: category = 'consumable'
            else:
                if item_id in config.EQUIPMENT_DB:
                    slot = item_info.get('slot')
                    if slot in ['head', 'helmet', 'body', 'armor']: category = 'armor'
                    else: category = slot
                else: category = 'consumable'

            inventory_data.append({
                "id": item.get("id"),
                "item_id": item_id,
                "name": item_info.get('name', item_id),
                "quantity": qty,
                "type": category,
                "desc": item_info.get('desc', ''),
                "rarity": item_info.get('rarity', 'common'),
                "usable": item_info.get('usable', False),
                "image_url": get_image_url(item_id, item_info)
            })

        return flask.jsonify({"items": inventory_data, "equipped": equipped_data}), 200
    except Exception as e:
        print(f"/// API INVENTORY ERROR: {e}")
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/inventory/equip', methods=['POST'])
def inventory_equip_api():
    data = flask.request.json
    uid = data.get('uid')
    item_id = data.get('item_id')
    inv_id = data.get('inv_id')

    if not uid or not item_id or not inv_id:
        return flask.jsonify({"error": "Missing params"}), 400

    try:
        uid = int(uid)
        item_info = config.ITEMS_INFO.get(item_id)
        if not item_info:
            return flask.jsonify({"error": "Item not found in database"}), 400

        slot = item_info.get('type')
        if slot not in ['weapon', 'head', 'body', 'software', 'artifact']:
            return flask.jsonify({"error": "Item cannot be equipped"}), 400



        db.equip_item(uid, inv_id, slot)

        # Clear cache so menus update
        import cache_db
        cache_db.clear_cache(uid)

        return flask.jsonify({"success": True}), 200
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

@app.route('/api/inventory/unequip', methods=['POST'])
def inventory_unequip_api():
    data = flask.request.json
    uid = data.get('uid')
    slot = data.get('slot')

    if not uid or not slot:
        return flask.jsonify({"error": "Missing params"}), 400

    try:
        uid = int(uid)

        db.unequip_item(uid, slot)

        import cache_db
        cache_db.clear_cache(uid)

        return flask.jsonify({"success": True}), 200
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500


def system_startup():
    try:
        with app.app_context():
            print("/// SYSTEM STARTUP INITIATED...")
            db.fix_indexes()

            if WEBHOOK_URL:
                try:
                    bot.remove_webhook()
                    res = bot.set_webhook(url=WEBHOOK_URL + "/webhook")
                    print(f"/// WEBHOOK SET: {WEBHOOK_URL} (Result: {res})")
                except Exception as e:
                    print(f"/// WEBHOOK SET ERROR: {e}")
                    traceback.print_exc()
            else:
                print("/// WARNING: WEBHOOK_URL not set. Bot will not receive updates via Webhook.")

    except Exception as e:
        print(f"/// SYSTEM STARTUP FATAL ERROR: {e}")

def notification_loop():
    if getattr(db, '_formatted_db_url', None) is None:
        db.init_pool()

    while True:
        users = []
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
        except Exception as db_err:
            print(f"/// NOTIFICATION LOOP DB ERROR: {db_err}")
            if isinstance(db_err, (psycopg2.OperationalError, psycopg2.InterfaceError)):
                print("/// CRITICAL DB ERROR in Notification Loop. Waiting 10s...")
                time.sleep(10)

        for row in users:
            uid = row[0]
            try:
                # Network Call Outside the DB Transaction
                bot.send_message(uid, "🔄 <b>СИНХРОНИЗАЦИЯ ГОТОВА</b>\nНовые знания ждут тебя.", parse_mode="HTML")
                try:
                    with db.db_session() as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute("UPDATE players SET notified = TRUE WHERE uid = %s", (uid,))
                            conn2.commit()
                except Exception as update_err:
                    print(f"/// DB UPDATE ERROR {uid}: {update_err}")

                time.sleep(0.2)
            except Exception as e:
                print(f"Notify Error {uid}: {e}")
                if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                    try:
                        with db.db_session() as conn3:
                            with conn3.cursor() as cur3:
                                cur3.execute("UPDATE players SET is_active = FALSE WHERE uid = %s", (uid,))
                                conn3.commit()
                    except Exception as block_err:
                        print(f"/// DB BLOCK ERROR {uid}: {block_err}")

        time.sleep(60)


start_worker(bot)
threading.Thread(target=system_startup, daemon=True).start()
threading.Thread(target=notification_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)


# --- FALLBACK HANDLERS ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def fallback_message(m):
    uid = int(m.from_user.id)
    text = m.text or "Media/Non-text"
    print(f"/// FALLBACK: Unhandled message from {uid}: {text}")
    # Don't send anything to user in production to avoid spam, just log it.

@bot.callback_query_handler(func=lambda call: True)
def fallback_callback(call):
    uid = int(call.from_user.id)
    print(f"/// FALLBACK: Unhandled callback from {uid}: {call.data}")
