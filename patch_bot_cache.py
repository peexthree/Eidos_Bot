import re

with open('bot.py', 'r') as f:
    content = f.read()

# Make sure we add cache variable at the top
if "_inventory_cache =" not in content:
    content = content.replace("@app.route('/api/inventory', methods=['GET'])", "_inventory_cache = {}\n@app.route('/api/inventory', methods=['GET'])")


old_api = """def inventory_api():

    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return flask.jsonify({"error": "Unauthorized - Missing InitData"}), 401

    uid_str = flask.request.args.get('uid')
    if not uid_str:
        return flask.jsonify({"error": "Missing uid"}), 400
    try:
        uid = int(uid_str)
    except:
        return flask.jsonify({"error": "Invalid uid"}), 400

    user = db.get_user(uid)
    if not user:
        return flask.jsonify({"error": "User not found"}), 404

    # --- Profile Data ---
    from modules.services.utils import get_user_display_name
    from modules.services.user import get_user_stats

    stats, _ = get_user_stats(uid)"""

new_api = """def inventory_api():

    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return flask.jsonify({"error": "Unauthorized - Missing InitData"}), 401

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
    from modules.services.utils import get_user_display_name
    from modules.services.user import get_user_stats

    stats, _ = get_user_stats(uid)"""


old_return = """    return flask.jsonify({
        "profile": profile,
        "items": items,
        "equipped": enriched_equipped
    })"""

new_return = """    response_data = {
        "profile": profile,
        "items": items,
        "equipped": enriched_equipped
    }

    _inventory_cache[uid] = {'time': time.time(), 'data': response_data}

    return flask.jsonify(response_data)"""

content = content.replace(old_api, new_api)
content = content.replace(old_return, new_return)

with open('bot.py', 'w') as f:
    f.write(content)

print("Inventory API caching implemented.")
