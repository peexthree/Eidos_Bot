import re

with open('cache_db.py', 'r') as f:
    content = f.read()

new_imports = """
import threading
import time
import traceback
import os
import ujson as json
import redis

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = None

if REDIS_URL:
    try:
        if 'rediss://' in REDIS_URL or '--tls' in REDIS_URL or 'VzBEbItaYFFXU7R6Xrv8x6xPJuFSJLDT' in REDIS_URL: # Specific check for Render TLS Redis
            # Standardizing URL for redis-py
            safe_url = REDIS_URL
            if 'rediss://' not in safe_url and 'redis://' not in safe_url:
               safe_url = f"rediss://red-d6llkmftskes73dhkd10:VzBEbItaYFFXU7R6Xrv8x6xPJuFSJLDT@frankfurt-keyvalue.render.com:6379"

            redis_client = redis.Redis.from_url(safe_url, decode_responses=True, ssl_cert_reqs="none")
        else:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print(f"/// REDIS CONNECTED SUCCESSFULLY")
    except Exception as e:
        print(f"/// REDIS CONNECTION ERROR: {e}")
        redis_client = None
"""

content = re.sub(r'import threading\nimport time\nimport traceback', new_imports.strip(), content, count=1)

new_get_cached = """
def get_cached_state(key, db_func, ttl=2.0):
    \"\"\"
    Generic caching function.
    'key' should be a unique string including the UID and the data type.
    \"\"\"
    now = time.time()

    # REDIS PATH
    if redis_client:
        try:
            cached_val = redis_client.get(key)
            if cached_val is not None:
                return json.loads(cached_val)

            val = db_func()
            if val is not None:
                redis_client.setex(key, int(ttl), json.dumps(val))
            return val
        except Exception as e:
            print(f"/// REDIS CACHE ERROR for {key}: {e}")
            # Fallback to local memory if Redis fails during operation
            pass

    # LOCAL MEMORY PATH
    with _lock:
        if key in _cache:
            val, expiry = _cache[key]
            if now < expiry:
                return val

    # DB call outside lock to prevent deadlock
    try:
        val = db_func()
    except Exception as e:
        print(f"/// CACHE DB_FUNC ERROR for {key}: {e}")
        return None

    with _lock:
        _cache[key] = (val, now + ttl)
    return val
"""
content = re.sub(r'def get_cached_state.*?return val', new_get_cached.strip(), content, flags=re.DOTALL)


new_clear = """
def clear_cache(uid):
    uid_str = str(uid)

    if redis_client:
        try:
            # Redis pattern matching deletion
            # WARNING: KEYS is slow, but usually okay for small cache.
            # In production, consider SCAN or targeted deletion.
            keys = redis_client.keys(f"*{uid_str}*")
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
             print(f"/// REDIS CLEAR ERROR: {e}")

    with _lock:
        # Clear all possible keys for this UID
        keys_to_del = [k for k in _cache.keys() if uid_str in k]
        for k in keys_to_del:
            _cache.pop(k, None)
"""
content = re.sub(r'def clear_cache.*?_cache\.pop\(k, None\)', new_clear.strip(), content, flags=re.DOTALL)


new_throttle = """
def check_throttle(uid, action, timeout=1.5):
    \"\"\"
    Returns True if action is throttled (blocked), False otherwise.
    Sets timeout for the next allowed action.
    \"\"\"
    key = f"throttle_{uid}_{action}"

    if redis_client:
        try:
            # SET NX (Not eXists) EX (Expire) is an atomic check-and-set
            # If it returns True, the key was set (not throttled). If False, key exists (throttled).
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
"""
content = re.sub(r'def check_throttle.*?return False', new_throttle.strip(), content, flags=re.DOTALL)


with open('cache_db.py', 'w') as f:
    f.write(content)
