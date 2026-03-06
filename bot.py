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

_stats_cache = {}
_stats_lock = threading.Lock()

def stats_worker():
    print("/// STATS WORKER STARTED")
    while True:
        try:
            task = STATS_QUEUE.get()
            if task is None: break
            uid, stat_type = task
            with _stats_lock:
                if uid not in _stats_cache:
                    _stats_cache[uid] = {}
                _stats_cache[uid][stat_type] = _stats_cache[uid].get(stat_type, 0) + 1
        except Exception as e:
            print(f"/// STATS WORKER ERR: {e}")
        finally:
            STATS_QUEUE.task_done()



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
@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.method == 'POST':
        try:
            json_string = flask.request.get_data().decode('utf-8')
            if not json_string:
                return 'Empty Data', 200

            update = telebot.types.Update.de_json(json_string)
            if update:
                # Отдаем апдейт напрямую телеботу. Никаких threading.Thread(target=process_update_safe)
                bot.process_new_updates([update])
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
    uid_str = flask.request.args.get('uid')
    if not uid_str:
        return flask.jsonify({"error": "Missing uid"}), 400

    try:
        uid = int(uid_str)
    except ValueError:
        return flask.jsonify({"error": "Invalid uid type"}), 400

    try:
        inventory_data = []
        equipped_data = {}

        # Profile Data Fetching
        from modules.schemas import User # Pydantic import
        user_dict = db.get_user(uid)

        profile_data = {}
        if user_dict:
            # Strictly validate user structure again just for safety (or rely on DB return)
            try:
                user = User(**user_dict).model_dump()
            except Exception as e:
                print(f"/// API INVENTORY PYDANTIC USER ERROR: {e}")
                user = user_dict

            level = user.get('level', 1)
            avatar_file_id = config.USER_AVATARS.get(level, config.USER_AVATARS.get(1))
            avatar_url = None
            if avatar_file_id:
                try:
                    avatar_url = bot.get_file_url(avatar_file_id)
                except Exception as e:
                    print(f"/// API INVENTORY ERROR GETTING AVATAR: {e}")

            from modules.services.utils import get_user_display_name

            # Using basic stats logic
            path_str = str(user.get('path', 'general')).lower()
            faction_name = config.SCHOOLS.get(path_str, "НЕОФИТ")

            profile_data = {
                "name": get_user_display_name(user),
                "username": user.get('username', ''),
                "level": level,
                "faction": faction_name,
                "biocoin": user.get('biocoin', 0),
                "xp": user.get('xp', 0),
                "avatar_url": avatar_url
            }

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
                    pass
            return None

        # 1. Load Equipment
        raw_equipped = db.get_user_equipment(uid) if hasattr(db, 'get_user_equipment') else {}
        if raw_equipped:
            for slot, item_id in raw_equipped.items():
                if item_id:
                    info = config.ITEMS_INFO.get(item_id, {})
                    ui_slot = slot.replace('helmet', 'head').replace('armor', 'body')
                    equipped_data[ui_slot] = {
                        "item_id": item_id,
                        "name": info.get('name', item_id),
                        "type": ui_slot,
                        "desc": info.get('desc', ''),
                        "rarity": info.get('rarity', 'common'),
                        "image_url": get_image_url(item_id, info)
                    }

        # 2. Load Inventory
        items = db.get_inventory(uid)
        from modules.schemas import InventoryItem

        for item in items:
            # Validate through Pydantic
            try:
                valid_item = InventoryItem(**item)
            except Exception as valid_err:
                print(f"/// API INV PYDANTIC ITEM ERR (UID {uid}): {valid_err}")
                continue # Skip corrupted item records

            item_id = valid_item.item_id

            if item_id in getattr(config, 'PVP_ITEMS', []):
                continue

            qty = valid_item.quantity
            item_info = config.ITEMS_INFO.get(item_id, {})

            raw_type = item_info.get('type', 'misc')
            category = raw_type

            if raw_type in ['weapon'] or item_info.get('slot') == 'weapon':
                category = 'weapon'
            elif raw_type in ['head', 'helmet', 'body', 'armor'] or item_info.get('slot') in ['head', 'helmet', 'body', 'armor']:
                category = 'equip'
            elif raw_type in ['software'] or item_info.get('slot') == 'software':
                category = 'software'
            elif raw_type in ['artifact'] or item_info.get('slot') == 'artifact':
                category = 'artifact'
            elif raw_type in ['consumable', 'misc']:
                category = 'consumable'
            else:
                if item_id in getattr(config, 'EQUIPMENT_DB', {}):
                    slot = item_info.get('slot')
                    if slot in ['head', 'helmet', 'body', 'armor']:
                        category = 'equip'
                    else:
                        category = slot
                else:
                    category = 'consumable'

            inventory_data.append({
                "id": valid_item.id,
                "item_id": item_id,
                "name": item_info.get('name', item_id),
                "quantity": qty,
                "type": category,
                "desc": item_info.get('desc', ''),
                "rarity": item_info.get('rarity', 'common'),
                "usable": item_info.get('usable', False),
                "image_url": get_image_url(item_id, item_info)
            })

        return flask.jsonify({"items": inventory_data, "equipped": equipped_data, "profile": profile_data}), 200
    except Exception as e:
        print(f"/// API INVENTORY ERROR: {e}")
        import traceback
        traceback.print_exc()
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
