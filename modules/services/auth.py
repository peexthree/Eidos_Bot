import hmac
import hashlib
import json
import time
import os
import sys
from functools import wraps

def verify_init_data(init_data: str, token: str) -> dict | None:
    """
    Верифицирует данные инициализации Telegram WebApp.
    """
    if not token:
        return None

    try:
        from urllib.parse import parse_qsl
        params = dict(parse_qsl(init_data))
        if 'hash' not in params:
            return None

        received_hash = params.pop('hash')

        # Проверка срока действия (24 часа)
        auth_date = int(params.get('auth_date', 0))
        if time.time() - auth_date > 86400:
            return None

        # Сортировка ключей и создание строки проверки
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        # Вычисление секретного ключа
        secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()

        # Вычисление HMAC
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if hmac.compare_digest(received_hash, expected_hash):
            user_json = params.get('user')
            if user_json:
                return json.loads(user_json)
            return {}
        return None
    except Exception as e:
        print(f"/// AUTH ERROR: {e}")
        return None

def require_telegram_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.environ.get("DEBUG_MODE") == "true":
            return f(*args, **kwargs)

        import flask
        from modules.bot_instance import TOKEN

        init_data = flask.request.headers.get('X-Telegram-Init-Data')
        if not init_data:
            return flask.jsonify({"error": "Unauthorized - Missing InitData"}), 401

        user_data = verify_init_data(init_data, TOKEN)
        if user_data is None:
            return flask.jsonify({"error": "Unauthorized - Invalid InitData"}), 401

        # Извлекаем UID для сверки
        req_uid = flask.request.args.get('uid')
        if not req_uid and flask.request.is_json:
            req_data = flask.request.json or {}
            req_uid = req_data.get('uid')

        # Если в запросе есть UID, проверяем его соответствие с UID из Telegram
        # Это предотвращает IDOR (Insecure Direct Object Reference)
        tg_uid = user_data.get('id')
        if req_uid and tg_uid:
            if str(req_uid) != str(tg_uid):
                return flask.jsonify({"error": "Forbidden - UID Mismatch"}), 403

        return f(*args, **kwargs)
    return decorated_function
