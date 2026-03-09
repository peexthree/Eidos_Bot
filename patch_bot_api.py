import re

file_path = 'bot.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find a place to insert the new routes. For example, before _inventory_cache

target = "_inventory_cache = {}"

new_routes = """
@app.route('/api/hub_data', methods=['GET'])
def hub_data_api():
    import config
    hub_images = {}
    for key, file_id in getattr(config, 'MENU_IMAGES', {}).items():
        hub_images[key] = f"/api/image/{file_id}"
    return flask.jsonify(hub_images)

@app.route('/api/action/synchron', methods=['POST'])
def action_synchron():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Unauthorized"}), 401

    # Fake implementation, should call backend logic for synchron
    from modules.services.economy import attempt_protocol_extraction
    success, msg, obtained, new_cd = attempt_protocol_extraction(uid)
    return flask.jsonify({"success": success, "message": msg, "obtained": obtained, "cooldown": new_cd})

@app.route('/api/action/signal', methods=['POST'])
def action_signal():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Unauthorized"}), 401

    # Fake implementation, should call backend logic for signal
    from modules.services.economy import attempt_signal_extraction
    success, msg, obtained, new_cd = attempt_signal_extraction(uid)
    return flask.jsonify({"success": success, "message": msg, "obtained": obtained, "cooldown": new_cd})

_inventory_cache = {}
"""

content = content.replace(target, new_routes, 1)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("bot.py patched.")
