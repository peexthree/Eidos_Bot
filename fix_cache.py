with open('cache_db.py', 'r') as f:
    c = f.read()

# Remove duplicate DB Call block that was accidentally inserted
to_remove = """    # DB call outside lock to prevent deadlock
    try:
        val = db_func()
    except Exception as e:
        print(f"/// CACHE DB_FUNC ERROR for {key}: {e}")
        return None

    with _lock:
        _cache[key] = (val, now + ttl)
    return val"""

c = c.replace(to_remove, "", 1)

with open('cache_db.py', 'w') as f:
    f.write(c)
