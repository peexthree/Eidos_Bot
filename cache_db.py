import threading
import time
import traceback

_cache = {}
_lock = threading.Lock()

def get_cached_state(key, db_func, ttl=2.0):
    """
    Generic caching function.
    'key' should be a unique string including the UID and the data type.
    """
    now = time.time()
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
    with _lock:
        # Clear all possible keys for this UID
        keys_to_del = [k for k in _cache.keys() if str(uid) in k]
        for k in keys_to_del:
            _cache.pop(k, None)

def check_throttle(uid, action, timeout=1.5):
    """
    Returns True if action is throttled (blocked), False otherwise.
    Sets timeout for the next allowed action.
    """
    key = f"throttle_{uid}_{action}"
    now = time.time()

    with _lock:
        if key in _cache:
            expiry = _cache[key][1]
            if now < expiry:
                return True

        _cache[key] = (True, now + timeout)
        return False
