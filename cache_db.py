import threading
import time
import traceback
import os
import ujson as json
import redis
from datetime import date, datetime

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = None

if REDIS_URL:
    try:
        # Стандартизация URL: добавляем схему, если её нет
        safe_url = REDIS_URL
        if not (safe_url.startswith('redis://') or safe_url.startswith('rediss://') or safe_url.startswith('unix://')):
            # Фолбэк на защищенное соединение для Render
            safe_url = f"rediss://{REDIS_URL}"

        # Декодирование ответов в str вместо bytes для удобства
        redis_client = redis.Redis.from_url(safe_url, decode_responses=True, ssl_cert_reqs=None)
        redis_client.ping()
        print(f"/// REDIS CONNECTED SUCCESSFULLY")
    except Exception as e:
        print(f"/// REDIS CONNECTION ERROR: {e}")
        redis_client = None

_cache = {}
_lock = threading.Lock()

def json_serial(obj):
    """Сериализатор для объектов, которые JSON не понимает по умолчанию (даты)"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj) # Фолбэк для всего остального

def get_cached_state(key, db_func, ttl=2.0):
    now = time.time()

    # REDIS PATH
    if redis_client:
        try:
            cached_val = redis_client.get(key)
            if cached_val is not None:
                return json.loads(cached_val)

            val = db_func()
            if val is not None:
                # ТВЕРДОЕ: Используем default=json_serial, чтобы не было ошибок datetime
                redis_client.setex(key, int(ttl), json.dumps(val, default=json_serial))
            return val
        except Exception as e:
            print(f"/// REDIS CACHE ERROR for {key}: {e}")
            pass

    # LOCAL MEMORY PATH
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
    key = f"throttle_{uid}_{action}"
    if redis_client:
        try:
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
