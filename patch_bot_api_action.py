import re

file_path = 'bot.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """
@app.route('/api/action/synchron', methods=['POST'])
def action_synchron():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Unauthorized"}), 401

    # Just a placeholder for actual synchronization logic
    import time
    from database import db
    u = db.get_user(uid)
    if not u:
        return flask.jsonify({"error": "User not found"}), 404

    # Update cooldown
    db.update_user(uid, last_protocol_time=time.time())
    db.add_exp(uid, 50)

    return flask.jsonify({"success": True, "message": "Синхронизация успешна. XP +50", "cooldown": 300})

@app.route('/api/action/signal', methods=['POST'])
def action_signal():
    data = flask.request.json or {}
    uid = data.get('uid')
    if not uid:
        return flask.jsonify({"error": "Unauthorized"}), 401

    # Just a placeholder for actual signal logic
    import time
    from database import db
    u = db.get_user(uid)
    if not u:
        return flask.jsonify({"error": "User not found"}), 404

    # Update cooldown
    db.update_user(uid, last_signal_time=time.time())
    db.add_biocoins(uid, 100)

    return flask.jsonify({"success": True, "message": "Сигнал перехвачен. BIO +100", "cooldown": 600})
"""

# Replace the fake ones from patch_bot_api.py
pattern = r"@app\.route\('/api/action/synchron', methods=\['POST'\]\).*?def action_signal\(\):.*?return flask\.jsonify\(\{\"success\": success, \"message\": msg, \"obtained\": obtained, \"cooldown\": new_cd\}\)"

content = re.sub(pattern, replacement.strip(), content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("bot.py patched.")
