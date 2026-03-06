import re

with open("bot.py", "r") as f:
    content = f.read()

# 1. Fix stats_worker
old_stats_worker = """def stats_worker():
    print("/// STATS WORKER STARTED")
    while True:
        try:
            task = STATS_QUEUE.get()
            if task is None: break
            uid, stat_type = task
            db.increment_user_stat(uid, stat_type)
        except Exception as e:
            print(f"/// STATS WORKER ERR: {e}")
        finally:
            STATS_QUEUE.task_done()

threading.Thread(target=stats_worker, daemon=True).start()"""

new_stats_worker = """_stats_cache = {}
_stats_lock = threading.Lock()

def stats_worker():
    print("/// STATS WORKER STARTED")
    while True:
        try:
            task = STATS_QUEUE.get()
            if task is None: break
            uid, stat_type = task
            with _stats_lock:
                if uid not in _stats_cache:
                    _stats_cache[uid] = {}
                _stats_cache[uid][stat_type] = _stats_cache[uid].get(stat_type, 0) + 1
        except Exception as e:
            print(f"/// STATS WORKER ERR: {e}")
        finally:
            STATS_QUEUE.task_done()

def stats_flusher():
    while True:
        time.sleep(30)
        with _stats_lock:
            if not _stats_cache:
                continue
            cache_copy = dict(_stats_cache)
            _stats_cache.clear()

        try:
            with db.db_session() as conn:
                with conn.cursor() as cur:
                    for uid, stats in cache_copy.items():
                        for stat_type, amount in stats.items():
                            cur.execute(f"UPDATE players SET {stat_type} = {stat_type} + %s WHERE uid = %s", (amount, uid))
                conn.commit()
        except Exception as e:
            print(f"/// STATS FLUSHER ERR: {e}")
            with _stats_lock:
                for uid, stats in cache_copy.items():
                    if uid not in _stats_cache:
                        _stats_cache[uid] = {}
                    for stat_type, amount in stats.items():
                        _stats_cache[uid][stat_type] = _stats_cache[uid].get(stat_type, 0) + amount

threading.Thread(target=stats_worker, daemon=True).start()
threading.Thread(target=stats_flusher, daemon=True).start()"""

content = content.replace(old_stats_worker, new_stats_worker)


# 2. Fix notification_loop
content = re.sub(
    r"LIMIT 50",
    "LIMIT 200",
    content
)

old_loop_logic = """        for row in users:
            uid = row[0]
            try:
                # Network Call Outside the DB Transaction
                bot.send_message(uid, "🔄 <b>СИНХРОНИЗАЦИЯ ГОТОВА</b>\\nНовые знания ждут тебя.", parse_mode="HTML")
                try:
                    with db.db_session() as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute("UPDATE players SET notified = TRUE WHERE uid = %s", (uid,))
                            conn2.commit()
                except Exception as update_err:
                    print(f"/// DB UPDATE ERROR {uid}: {update_err}")

                time.sleep(0.2)
            except Exception as e:
                print(f"Notify Error {uid}: {e}")
                if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                    try:
                        with db.db_session() as conn3:
                            with conn3.cursor() as cur3:
                                cur3.execute("UPDATE players SET is_active = FALSE WHERE uid = %s", (uid,))
                                conn3.commit()
                    except Exception as block_err:
                        print(f"/// DB BLOCK ERROR {uid}: {block_err}")

        time.sleep(60)"""

new_loop_logic = """        for row in users:
            uid = row[0]
            try:
                bot.send_message(uid, "🔄 <b>СИНХРОНИЗАЦИЯ ГОТОВА</b>\\nНовые знания ждут тебя.", parse_mode="HTML")
                try:
                    with db.db_session() as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute("UPDATE players SET notified = TRUE WHERE uid = %s", (uid,))
                            conn2.commit()
                except Exception as update_err:
                    print(f"/// DB UPDATE ERROR {uid}: {update_err}")
            except Exception as e:
                print(f"Notify Error {uid}: {e}")
                if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                    try:
                        with db.db_session() as conn3:
                            with conn3.cursor() as cur3:
                                cur3.execute("UPDATE players SET is_active = FALSE WHERE uid = %s", (uid,))
                                conn3.commit()
                    except Exception as block_err:
                        print(f"/// DB BLOCK ERROR {uid}: {block_err}")

            # Rate limiting the telegram API call, not holding the DB connection inside sleep
            time.sleep(0.05)

        time.sleep(60)"""

content = content.replace(old_loop_logic, new_loop_logic)

with open("bot.py", "w") as f:
    f.write(content)
