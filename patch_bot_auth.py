import re

with open('bot.py', 'r') as f:
    content = f.read()

# Define a validation stub (or full HMAC logic if necessary, but stub matches requirements "a stub check for now, matching the standard approach")
def add_auth_check(func_name, code):
    check_code = f"""
    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        print("/// SECURITY WARN: No initData provided in {func_name}")
        # return flask.jsonify({{"error": "Unauthorized"}}), 401
    """

    # Let's actually enforce it gently, returning 401 if strict. The instruction says: "Return a 401 error if it's missing or invalid (a stub check for now...)"
    check_code_strict = f"""
    init_data = flask.request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return flask.jsonify({{"error": "Unauthorized - Missing InitData"}}), 401
    """

    # insert after def <func_name>():
    func_pattern = rf"def {func_name}\(\):"
    return re.sub(func_pattern, f"def {func_name}():\n{check_code_strict}", code, count=1)

content = add_auth_check("inventory_api", content)
content = add_auth_check("inventory_equip", content)
content = add_auth_check("inventory_unequip", content)
content = add_auth_check("inventory_use", content)
content = add_auth_check("inventory_dismantle", content)

with open('bot.py', 'w') as f:
    f.write(content)

print("Auth checks added to bot.py")
