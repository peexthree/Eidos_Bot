from modules.services.worker_queue import start_worker, enqueue_task
import logging_setup
import cache_db
import telebot
import flask
import os
import sys
import time
import threading
import concurrent.futures

import traceback
import psycopg2
import requests
import io

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
from modules.services.user import get_user_stats, flush_stats
from modules.services.utils import get_user_display_name
from modules.services.inventory import equip_item, unequip_item
from modules.services.shop import get_shadow_shop_items
from modules.services.auth import require_telegram_auth

# Import Bot Instance
from modules.bot_instance import bot, app, TOKEN, WEBHOOK_URL

# Import Handlers
import modules.handlers.start
import modules.handlers.admin
import modules.handlers.eidos_room
import modules.handlers.glitch_handler
import modules.handlers.gameplay
import modules.handlers.menu
import modules.handlers.items
import modules.handlers.pvp
import modules.handlers.onboarding


# Глобальный пул потоков для Webhook
executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

def process_update_safe(update):
    try:
        bot.process_new_updates([update])
    except Exception as e:
        print(f"/// THREAD POOL ERROR: {e}")
        traceback.print_exc()

# --- API ROUTES ---

@app.route('/health', methods=['GET'])
def health_check():
    return flask.jsonify({"status": "ok", "time": time.time()}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        executor.submit(process_update_safe, update)
        return '', 200
    else:
        flask.abort(403)


# ==========================================
# VITE REACT FRONTEND ROUTES (frontend_v2/dist)
# ==========================================

# Serve static assets from frontend_v2/dist
@app.route('/assets/<path:path>', methods=['GET'])
def send_vite_assets(path):
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend_v2/dist/assets')
    return flask.send_from_directory(dist_dir, path)

@app.route('/IMG/<path:path>', methods=['GET'])
def send_vite_img(path):
    # Try serving from frontend_v2/dist/IMG first, fallback to static/IMG
    dist_img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend_v2/dist/IMG')
    static_img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/IMG')
    if os.path.exists(os.path.join(dist_img_dir, path)):
        return flask.send_from_directory(dist_img_dir, path)
    return flask.send_from_directory(static_img_dir, path)

@app.route('/video/<path:path>', methods=['GET'])
def send_vite_video(path):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/video')
    return flask.send_from_directory(static_dir, path)

@app.route('/inventory', methods=['GET'])
@app.route('/hub', methods=['GET'])
@app.route('/shop', methods=['GET'])
def inventory_webapp():
    # Serve the Vite React build index.html
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend_v2/dist')
    return flask.send_from_directory(dist_dir, 'index.html')


@app.route("/", methods=["GET"])
def index():
    return "Eidos Terminal Interface Operational", 200

# === PROXY ДЛЯ КАРТИНОК TELEGRAM ===

_image_cache = {}
@app.route('/api/image/<file_id>', methods=['GET'])
def get_telegram_image(file_id):
    """Безопасный шлюз для передачи изображений из Telegram в WebApp без утечки токена"""
    if file_id in _image_cache:
        return flask.send_file(io.BytesIO(_image_cache[file_id]), mimetype='image/jpeg')
    try:
        file_info = bot.get_file(file_id)
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response = requests.get(download_url)
        if response.status_code == 200:
            _image_cache[file_id] = response.content
            return flask.send_file(io.BytesIO(response.content), mimetype='image/jpeg')
        else:
            return flask.jsonify({"error": "Failed to download"}), 404
    except Exception as e:
        print(f"/// IMAGE PROXY ERROR: {e}")
        # Если файла нет, возвращаем SVG-заглушку из статики
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/IMG')
        return flask.send_from_directory(static_dir, 'eidos_sys-warning.svg')


@app.route('/api/hub_data', methods=['GET'])
@require_telegram_auth
def hub_data_api():
    uid_str = flask.request.args.get('uid')
    if not uid_str:
        return flask.jsonify({"error": "Missing uid"}), 400
    try:
        uid = int(uid_str)
    except:
        return flask.jsonify({"error": "Invalid uid"}), 400

    u = db.get_user(uid)
    if not u:
        return flask.jsonify({"error": "User not found"}), 404

    lvl = u.get("level", 1)
    # Get items to check for keys like 'architect_eye' (Ключ Архитектора)
    # Actually, we can check raw_equipped or full inventory.
    # Let's just do a basic implementation based on level first, as asked:
    # "Бэкенд должен отдавать список доступных локаций и их статус (заблокировано, карантин, доступно) в зависимости от уровня пользователя"

    hub_images = {}
    for key, file_id in getattr(config, 'MENU_IMAGES', {}).items():
        hub_images[key] = f"/api/image/{file_id}"

    status = {
        "zero_layer_menu": "available",
        "shop_menu": "available" if lvl >= 2 else "locked",
        "diary_menu": "available",
        "shadow_shop_menu": "available" if lvl >= 5 else "locked",
        "leaderboard": "available",
        "referral": "available",
        "guide": "available",
        "admin_panel": "locked" # Only admin, but let's say locked for now
    }

    if str(uid) in getattr(config, 'ADMIN_IDS', []):
        status["admin_panel"] = "available"

    return flask.jsonify({"images": hub_images, "status": status})


@app.route('/api/action/synchron', methods=['POST'])
@require_telegram_auth
def action_synchron():
    data = flask.request.json or {}
    uid = data.get('uid')

    # Just a placeholder for actual synchronization logic
    u = db.get_user(uid)
    if not u:
        return flask.jsonify({"error": "User not found"}), 404

    # Update cooldown
    db.update_user(uid, last_protocol_time=time.time())
    db.add_exp(uid, 50)

    return flask.jsonify({"success": True, "message": "Синхронизация успешна. XP +50", "cooldown": 300})

@app.route('/api/action/signal', methods=['POST'])
@require_telegram_auth
def action_signal():
    data = flask.request.json or {}
    uid = data.get('uid')

    # Just a placeholder for actual signal logic
    u = db.get_user(uid)
    if not u:
        return flask.jsonify({"error": "User not found"}), 404

    # Update cooldown
    db.update_user(uid, last_signal_time=time.time())
    db.add_biocoins(uid, 100)

    return flask.jsonify({"success": True, "message": "Сигнал перехвачен. BIO +100", "cooldown": 600})

_inventory_cache = {}

_inventory_cache = {}
@app.route('/api/inventory', methods=['GET'])
@require_telegram_auth
def inventory_api():

    uid_str = flask.request.args.get('uid')
    if not uid_str:
        return flask.jsonify({"error": "Missing uid"}), 400
    try:
        uid = int(uid_str)
    except:
        return flask.jsonify({"error": "Invalid uid"}), 400

    now = time.time()
    cached = _inventory_cache.get(uid)
    if cached and now - cached['time'] < 3:
        return flask.jsonify(cached['data'])

    user = db.get_user(uid)
    if not user:
        return flask.jsonify({"error": "User not found"}), 404

    # --- Profile Data ---

    stats, _ = get_user_stats(uid)
    if not stats: stats = {'atk': 0, 'def': 0, 'luck': 0}

    level = user.get('level', 1)
    avatar_file_id = config.USER_AVATARS.get(level, config.USER_AVATARS.get(1))
    avatar_url = None
    if avatar_file_id:
        # ТВЕРДОЕ: Используем наш защищенный прокси вместо прямой ссылки Telegram
        avatar_url = f"/api/image/{avatar_file_id}"

    profile = {
        "name": get_user_display_name(user),
        "level": level,
        "faction": config.SCHOOLS.get(user.get('path', 'none'), 'NEUTRAL'),
        "biocoins": user.get('biocoin', 0), # Гарантируем biocoins
        "xp": user.get('xp', 0),
        "next_xp": level * 1000,
        "atk": stats.get('atk', 0),
        "def": stats.get('def', 0),
        "luck": stats.get('luck', 0),
        "signal": user.get('signal', 100),
        "avatar_url": avatar_url
    }

    # --- Items (Inventory) ---
    items = []
    raw_items = db.get_inventory(uid)
    for i in raw_items:
        info = config.ITEMS_INFO.get(i['item_id'], {})
        img_file_id = info.get('file_id') # Извлекаем file_id из конфига
        items.append({
            "id": i['id'], # Уникальный ID записи в БД
            "item_id": i['item_id'],
            "name": info.get('name', i['item_id']),
            "quantity": i.get('quantity', 1),
            "type": info.get('type', 'misc'),
            "description": info.get('desc', 'Описание отсутствует.'),
            "rarity": info.get('rarity', 'common'),
            "stats": info.get('stats', {}),
            # Передаем ссылку на прокси, если file_id есть, иначе None
            "image_url": f"/api/image/{img_file_id}" if img_file_id else None
        })

    # --- Equipped (Enriching Data for WebApp) ---
    raw_equipped = db.get_user_equipment(uid)
    equipped = {}
    for slot, item_data in raw_equipped.items():
        iid = item_data['item_id'] if isinstance(item_data, dict) else item_data
        if iid:
            info = config.ITEMS_INFO.get(iid, {})
            img_file_id = info.get('file_id')
            equipped[slot] = {
                "item_id": iid,
                "name": info.get('name', iid),
                "description": info.get('desc', "Данные отсутствуют."),
                "rarity": info.get('rarity', 'common'),
                "type": info.get('type', slot),
                "durability": item_data.get('durability', 100) if isinstance(item_data, dict) else 100,
                "stats": info.get('stats', {}),
                "image_url": f"/api/image/{img_file_id}" if img_file_id else None
            }
        else:
            equipped[slot] = None

    response_data = {
        "profile": profile,
        "items": items,
        "equipped": equipped
    }

    _inventory_cache[uid] = {'time': time.time(), 'data': response_data}

    return flask.jsonify(response_data)
@app.route('/api/action/equip', methods=['POST'])
@app.route('/api/inventory/equip', methods=['POST'])
@require_telegram_auth
def inventory_equip():
    global _inventory_cache
    if flask.request.json and "uid" in flask.request.json:
        _inventory_cache.pop(flask.request.json.get("uid"), None)
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id = data.get('item_id')

    success = equip_item(uid, item_id)
    return flask.jsonify({"success": success})

@app.route('/api/action/unequip', methods=['POST'])
@app.route('/api/inventory/unequip', methods=['POST'])
@require_telegram_auth
def inventory_unequip():
    global _inventory_cache
    if flask.request.json and "uid" in flask.request.json:
        _inventory_cache.pop(flask.request.json.get("uid"), None)
    data = flask.request.json or {}
    uid = data.get('uid')
    slot = data.get('slot')

    success = unequip_item(uid, slot)
    return flask.jsonify({"success": success})

@app.route('/api/inventory/use', methods=['POST'])
@require_telegram_auth
def inventory_use():
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id = data.get('item_id')

    success = db.use_item(uid, item_id, 1)
    return flask.jsonify({"success": success})

@app.route('/api/inventory/dismantle', methods=['POST'])
@require_telegram_auth
def inventory_dismantle():
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id_str = data.get('item_id')

    try:

        if not uid or not item_id_str:
            return flask.jsonify({"error": "Missing parameters"}), 400

        inv_id = None
        with db.db_cursor() as cur:
            if cur:
                cur.execute(
                    "SELECT id FROM inventory WHERE uid=%s AND item_id=%s AND quantity > 0 LIMIT 1",
                    (uid, item_id_str)
                )
                row = cur.fetchone()
                if row:
                    inv_id = row[0]

        if not inv_id:
            return flask.jsonify({"error": "Item not found in inventory"}), 404

        success = db.dismantle_item(uid, inv_id)

        if success:
            return flask.jsonify({"status": "ok"})
        else:
            return flask.jsonify({"error": "Failed to dismantle"}), 400

    except Exception as e:
        traceback.print_exc()
        return flask.jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/shop', methods=['GET'])
def shop_api():
    uid = int(flask.request.args.get('uid', 0))
    items = get_shadow_shop_items()
    for it in items:
        it['owned'] = db.get_item_count(uid, it['id']) > 0 if uid else False
    return flask.jsonify({"items": items})


@app.route('/api/shop/buy', methods=['POST'])
@require_telegram_auth
def api_shop_buy():
    data = flask.request.json
    uid = data.get('uid')
    item_id = data.get('item_id')

    if not item_id or item_id not in config.ITEMS_INFO:
        return flask.jsonify({"error": "Item not found"}), 400

    price = config.ITEMS_INFO[item_id].get('price')
    if not price:
        shadow_items = get_shadow_shop_items()
        shadow_item = next((i for i in shadow_items if i['id'] == item_id), None)
        if shadow_item:
            price = shadow_item.get('price')
        if not price:
            return flask.jsonify({"error": "Item not for sale"}), 400

    stats = get_user_stats(uid)
    if stats.get('coins', 0) < price:
        return flask.jsonify({"error": "Insufficient BC"}), 400

    db.update_user(uid, bc=stats.get('coins', 0) - price)
    db.add_items(uid, [{'id': item_id, 'qty': 1}])
    flush_stats(uid)
    return flask.jsonify({"success": True})

@app.route('/api/action/craft', methods=['POST'])
@require_telegram_auth
def api_action_craft():
    data = flask.request.json
    uid = data.get('uid')
    item_ids = data.get('item_ids', [])

    if not item_ids or len(item_ids) < 3:
        return flask.jsonify({"error": "Not enough items to craft"}), 400

    return flask.jsonify({"error": "Crafting algorithm requires server sync."}), 501

    return flask.jsonify({"success": False, "reason": "Insufficient biocoins"}), 400


@app.route('/api/twa/sync', methods=['POST'])
@require_telegram_auth
def twa_sync():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Missing uid"}), 400

    try:
        # Clear redis cache for this specific user so next text interaction loads fresh data
        cache_db.clear_cache(uid)

        # Flush the background stats (which could be pending processing)
        flush_stats()

        return flask.jsonify({"success": True, "message": "Context synchronized"})
    except Exception as e:
        traceback.print_exc()
        return flask.jsonify({"error": "Sync Failed"}), 500

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard_api():
    top = db.get_leaderboard(limit=10)
    return flask.jsonify({"top": top})

@app.route('/api/dossier', methods=['GET'])
@require_telegram_auth
def dossier_api():
    uid = int(flask.request.args.get('uid', 0))
    with db.db_cursor() as cur:
        cur.execute("SELECT dossier_text FROM user_dossiers WHERE uid = %s", (uid,))
        res = cur.fetchone()
        if res:
            return flask.jsonify({"status": "ready", "text": res[0]})

    enqueue_task("generate_user_dossier_worker", uid=uid, chat_id=uid, target_user_data=db.get_user(uid))
    return flask.jsonify({"status": "processing", "text": "ГЕНЕРАЦИЯ ДОСЬЕ ЗАПУЩЕНА..."})

# --- STARTUP & SCHEDULER ---
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', seconds=30)
def stats_flusher():
    try: flush_stats()
    except: pass

@scheduler.scheduled_job('interval', seconds=60)
def xp_flusher():
    if hasattr(db, '_flush_xp_cache'):
        try: db._flush_xp_cache()
        except: pass

def system_startup():
    print("/// SYSTEM STARTUP INITIATED...")
    if hasattr(db, 'fix_indexes'): db.fix_indexes()
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            bot.set_webhook(url=WEBHOOK_URL + "/webhook")
            print(f"/// WEBHOOK SET: {WEBHOOK_URL}")
        except Exception as e:
            print(f"/// WEBHOOK ERROR: {e}")
    if not scheduler.running:
        scheduler.start()

# Fallback handlers for bot
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def fallback_message(m):
    print(f"/// FALLBACK: Unhandled message from {m.from_user.id}")

@bot.callback_query_handler(func=lambda call: True)
def fallback_callback(call):
    print(f"/// FALLBACK: Unhandled callback from {call.from_user.id}: {call.data}")

if __name__ == "__main__":
    start_worker(bot)
    # Запуск системы в отдельном потоке
    threading.Thread(target=system_startup, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
