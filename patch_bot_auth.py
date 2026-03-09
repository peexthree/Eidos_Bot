import re

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_auth(match):
    return """    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401"""

# Match equip
content = re.sub(
    r"    init_data = flask\.request\.headers\.get\('X-Telegram-Init-Data'\)\n    if not init_data:\n        return flask\.jsonify\(\{\"error\": \"Unauthorized - Missing InitData\"\}\), 401\n\n    data = flask\.request\.json\n    uid, item_id = data\.get\('uid'\), data\.get\('item_id'\)",
    """    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id = data.get('item_id')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401""",
    content
)

# Match unequip
content = re.sub(
    r"    init_data = flask\.request\.headers\.get\('X-Telegram-Init-Data'\)\n    if not init_data:\n        return flask\.jsonify\(\{\"error\": \"Unauthorized - Missing InitData\"\}\), 401\n\n    data = flask\.request\.json\n    uid, slot = data\.get\('uid'\), data\.get\('slot'\)",
    """    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')
    slot = data.get('slot')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401""",
    content
)

# Match use
content = re.sub(
    r"    init_data = flask\.request\.headers\.get\('X-Telegram-Init-Data'\)\n    if not init_data:\n        return flask\.jsonify\(\{\"error\": \"Unauthorized - Missing InitData\"\}\), 401\n\n    data = flask\.request\.json\n    uid, item_id = data\.get\('uid'\), data\.get\('item_id'\)",
    """    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id = data.get('item_id')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401""",
    content
)

# Match dismantle
content = re.sub(
    r"    init_data = flask\.request\.headers\.get\('X-Telegram-Init-Data'\)\n    if not init_data:\n        return flask\.jsonify\(\{\"error\": \"Unauthorized - Missing InitData\"\}\), 401\n\n    try:\n        data = flask\.request\.json\n        uid = data\.get\('uid'\)",
    """    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401

    try:""",
    content
)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)
