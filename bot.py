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

# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    except Exception as e:
        print(f"/// SENTRY INIT ERROR: {e}")


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


@app.route('/css/<path:path>', methods=['GET'])
def send_css(path):
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/css')
    return flask.send_from_directory(static_dir, path)


@app.route('/IMG/<path:path>', methods=['GET'])
def send_img(path):
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/IMG')
    return flask.send_from_directory(static_dir, path)

@app.route('/js/<path:path>', methods=['GET'])
def send_js(path):
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/js')
    return flask.send_from_directory(static_dir, path)

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
            from modules.services.user import get_user_stats

            # Using basic stats logic
            path_str = str(user.get('path', 'general')).lower()
            faction_name = config.SCHOOLS.get(path_str, "НЕОФИТ")

            stats, _ = get_user_stats(uid)
            if not stats:
                stats = {'atk': 0, 'def': 0, 'luck': 0}

            # Approximate max_xp for level
            max_xp = level * 1000

            profile_data = {
                "name": get_user_display_name(user),
                "username": user.get('username', ''),
                "level": level,
                "faction": faction_name,
                "biocoin": user.get('biocoin', 0),
                "xp": user.get('xp', 0),
                "max_xp": max_xp,
                "atk": stats.get('atk', 0),
                "def": stats.get('def', 0),
                "luck": stats.get('luck', 0),
                "signal": user.get('signal', 100),
                "avatar_url": avatar_url,
                "hp": user.get('hp', 100),
                "max_hp": user.get('max_hp', 100),
                "class": faction_name,
                "anomalies": user.get('anomalies', []),
                "dossier": user.get('dossier', ""),
                "artifact_lore": user.get('artifact_lore', "")
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
            for slot, data in raw_equipped.items():
                if isinstance(data, dict):
                    item_id = data.get("item_id")
                    durability = data.get("durability")
                else:
                    item_id = data
                    durability = None

                if item_id:
                    info = config.ITEMS_INFO.get(item_id, {})
                    ui_slot = slot.replace('helmet', 'head').replace('armor', 'body')
                    equipped_data[ui_slot] = {
                        "item_id": item_id,
                        "name": info.get('name', item_id),
                        "type": ui_slot,
                        "desc": info.get('desc', ''),
                        "rarity": info.get('rarity', 'common'),
                        "image_url": get_image_url(item_id, info),
                        "durability": durability
                    }

        # 2. Load Inventory
        items = db.get_inventory(uid)
        from modules.schemas import InventoryItem

        for item in items:
            # Validate through Pydantic
            try:
                item["uid"] = uid
                item['durability'] = max(0, item.get('durability', 0))
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

        return flask.jsonify({
            "items": inventory_data,
            "equipped": equipped_data,
            "profile": profile_data,
            "inventory": inventory_data,
            "hp": profile_data.get("hp", 100),
            "max_hp": profile_data.get("max_hp", 100),
            "xp": profile_data.get("xp", 0),
            "max_xp": profile_data.get("max_xp", 1000),
            "level": profile_data.get("level", 1),
            "biocoin": profile_data.get("biocoin", 0),
            "class": profile_data.get("class", ""),
            "atk": profile_data.get("atk", 0),
            "def": profile_data.get("def", 0),
            "anomalies": profile_data.get("anomalies", []),
            "dossier": profile_data.get("dossier", ""),
            "artifact_lore": profile_data.get("artifact_lore", "")
        }), 200
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

        slot = item_info.get('slot')
        if not slot:
            slot = item_info.get('type')

        if slot in ['helmet']:
            slot = 'head'
        elif slot in ['armor']:
            slot = 'body'

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




from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# -- SCHEDULER JOBS --
def aps_stats_flusher():
    with _stats_lock:
        if not _stats_cache:
            return
        cache_copy = dict(_stats_cache)
        _stats_cache.clear()

    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                for uid, stats in cache_copy.items():
                    for stat_type, amount in stats.items():
                        cur.execute(f"UPDATE players SET {stat_type} = {stat_type} + %s WHERE uid = %s", (amount, uid))
            conn.commit()
    except Exception as e:
        print(f"/// STATS FLUSHER ERR: {e}")
        with _stats_lock:
            for uid, stats in cache_copy.items():
                if uid not in _stats_cache:
                    _stats_cache[uid] = {}
                for stat_type, amount in stats.items():
                    _stats_cache[uid][stat_type] = _stats_cache[uid].get(stat_type, 0) + amount

def aps_notification_loop():
    if getattr(db, '_formatted_db_url', None) is None:
        db.init_pool()

    users = []
    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                now = int(time.time())
                cur.execute("""
                    SELECT uid FROM players
                    WHERE last_protocol_time > 0
                    AND (last_protocol_time + 1800) < %s
                    AND notified = FALSE
                    AND is_active = TRUE
                    LIMIT 200
                """, (now,))
                users = cur.fetchall()
    except Exception as db_err:
        print(f"/// NOTIFICATION LOOP DB ERROR: {db_err}")
        return

    for row in users:
        uid = row[0]
        try:
            bot.send_message(uid, "🔄 <b>СИНХРОНИЗАЦИЯ ГОТОВА</b>\nНовые знания ждут тебя.", parse_mode="HTML")
            try:
                with db.db_session() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute("UPDATE players SET notified = TRUE WHERE uid = %s", (uid,))
                        conn2.commit()
            except Exception as update_err:
                print(f"/// DB UPDATE ERROR {uid}: {update_err}")
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
        time.sleep(0.05)

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(aps_stats_flusher, IntervalTrigger(seconds=30), id='stats_flusher', replace_existing=True)
scheduler.add_job(db._flush_xp_cache, IntervalTrigger(seconds=60), id='xp_flusher', replace_existing=True)
scheduler.add_job(aps_notification_loop, IntervalTrigger(seconds=60), id='notification_loop', replace_existing=True)
scheduler.start()
print("/// APSCHEDULER STARTED WITH JOBS: stats_flusher(30s), xp_flusher(60s), notification_loop(60s)")

start_worker(bot)

threading.Thread(target=system_startup, daemon=True).start()

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
