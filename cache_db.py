import threading
import time
import traceback
import os
import json
import redis
from datetime import date, datetime

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = None

def json_serial(obj):
    """Сериализатор для объектов, которые JSON не понимает по умолчанию (даты)"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

if REDIS_URL:
    try:
        url = REDIS_URL.strip()
        
        # Базовые параметры подключения
        params = {
            "decode_responses": True,
            "socket_timeout": 5,
            "retry_on_timeout": True
        }

        # ТВЕРДОЕ: Определяем необходимость SSL параметров по схеме URL
        if url.startswith('rediss://'):
            # Для Render Redis (TLS) требуется отключение проверки сертификата
            params["ssl_cert_reqs"] = None
        elif not url.startswith('redis://') and not url.startswith('unix://'):
            # Если схемы нет, предполагаем rediss (стандарт Render) и добавляем параметры
            url = f"rediss://{url}"
            params["ssl_cert_reqs"] = None
        
        # Если схема redis:// — параметры SSL НЕ добавляются, что предотвращает ошибку
        redis_client = redis.Redis.from_url(url, **params)
        redis_client.ping()
        print(f"/// REDIS CONNECTED SUCCESSFULLY")
    except Exception as e:
        print(f"/// REDIS CONNECTION ERROR: {e}")
        redis_client = None

_cache = {}
_lock = threading.Lock()

def get_cached_state(key, db_func, ttl=2.0):
    """
    Универсальная функция кэширования.
    Если Redis доступен — использует его, иначе падает на локальную память.
    """
    now = time.time()

    # ПУТЬ REDIS
    if redis_client:
        try:
            cached_val = redis_client.get(key)
            if cached_val is not None:
                return json.loads(cached_val)

            val = db_func()
            if val is not None:
                # ТВЕРДОЕ: Используем default=json_serial для поддержки datetime
                redis_client.setex(key, int(ttl), json.dumps(val, default=json_serial))
            return val
        except Exception as e:
            print(f"/// REDIS CACHE ERROR for {key}: {e}")
            pass

    # ПУТЬ ЛОКАЛЬНОЙ ПАМЯТИ (Fallback)
    with _lock:
        if key in _cache:
            val, expiry = _cache[key]
            if now < expiry:
                return val

    try:
        val = db_func()
    except Exception as e:
        print(f"/// CACHE DB_FUNC ERROR for {key}: {e}")
        return None

    with _lock:
        _cache[key] = (val, now + ttl)
    return val

def get_cached_user(uid, ttl=5.0):
    import database as db
    return get_cached_state(f"u_{uid}", lambda: db.get_user(uid), ttl=ttl)

def get_cached_user_state(uid, ttl=2.0):
    import database as db
    return get_cached_state(f"state_{uid}", lambda: db.get_state(uid), ttl=ttl)

def get_cached_admin_status(uid, ttl=10.0):
    import database as db
    return get_cached_state(f"admin_{uid}", lambda: db.is_user_admin(uid), ttl=ttl)

def clear_cache(uid):
    uid_str = str(uid)
    if redis_client:
        try:
            # Массовое удаление ключей пользователя в Redis
            keys = redis_client.keys(f"*{uid_str}*")
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
             print(f"/// REDIS CLEAR ERROR: {e}")

    with _lock:
        keys_to_del = [k for k in _cache.keys() if uid_str in k]
        for k in keys_to_del:
            _cache.pop(k, None)

def check_throttle(uid, action, timeout=1.5):
    """
    Проверка лимитов (троттлинг).
    Возвращает True, если действие заблокировано, False — если разрешено.
    """
    key = f"throttle_{uid}_{action}"
    if redis_client:
        try:
            # Атомарная установка ключа с временем жизни (EX)
            is_new = redis_client.set(key, "1", nx=True, ex=int(max(1, timeout)))
            return not is_new
        except Exception as e:
            print(f"/// REDIS THROTTLE ERROR: {e}")
            pass

    now = time.time()
    with _lock:
        if key in _cache:
            expiry = _cache[key][1]
            if now < expiry:
                return True
        _cache[key] = (True, now + timeout)
        return False
