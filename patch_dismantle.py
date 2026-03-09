import re

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace dismantle route
content = re.sub(
    r"""def inventory_dismantle\(\):
    init_data = flask\.request\.headers\.get\('X-Telegram-Init-Data'\)
    data = flask\.request\.json or \{\}
    uid = data\.get\('uid'\)

    if not init_data and not uid:
        return flask\.jsonify\(\{"error": "Unauthorized - Missing InitData and UID"\}\), 401

    try:
        item_id_str = data\.get\('item_id'\) """,
    """def inventory_dismantle():
    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    data = flask.request.json or {}
    uid = data.get('uid')
    item_id_str = data.get('item_id')

    if not init_data and not uid:
        return flask.jsonify({"error": "Unauthorized - Missing InitData and UID"}), 401

    try:""",
    content
)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)
