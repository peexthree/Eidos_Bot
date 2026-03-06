import re

# 1. Patch database.py to remove while True: sleep() thread for XP cache
with open('database.py', 'r') as f:
    db_content = f.read()

# Replace threading with function that APScheduler will call
new_flush_xp_cache = """
def _flush_xp_cache():
    with _xp_cache_lock:
        if not _xp_cache:
            return
        cache_copy = dict(_xp_cache)
        _xp_cache.clear()

    try:
        with db_session() as conn:
            with conn.cursor() as cur:
                uids = list(cache_copy.keys())
                if not uids:
                    return

                # Fetch referrers in batch
                cur.execute("SELECT uid, referrer FROM players WHERE uid = ANY(%s)", (uids,))
                referrers = {row[0]: row[1] for row in cur.fetchall()}

                player_updates = []
                ref_updates = {}
                gen_updates = []

                for uid, amount in cache_copy.items():
                    if amount == 0:
                        continue

                    profit = 0
                    ref_id = None
                    actual_amount = amount

                    if amount > 0:
                        ref_id = referrers.get(uid)
                        if ref_id:
                            profit = int(amount * 0.1)
                            actual_amount = amount - profit

                    player_updates.append((uid, actual_amount))

                    if profit > 0 and ref_id:
                        # We need to accumulate ref profits in case multiple referrals are updated
                        if ref_id not in ref_updates:
                            ref_updates[ref_id] = 0
                        ref_updates[ref_id] += profit

                        gen_updates.append((uid, profit))

                if player_updates:
                    execute_values(cur,
                        "UPDATE players SET xp = xp + data.amount FROM (VALUES %s) AS data (uid, amount) WHERE players.uid = data.uid",
                        player_updates
                    )

                if ref_updates:
                    ref_data = [(rid, p) for rid, p in ref_updates.items()]
                    execute_values(cur,
                        "UPDATE players SET xp = xp + data.amount, ref_profit_xp = ref_profit_xp + data.amount FROM (VALUES %s) AS data (uid, amount) WHERE players.uid = data.uid",
                        ref_data
                    )

                if gen_updates:
                    execute_values(cur,
                        "UPDATE players SET generated_ref_xp = generated_ref_xp + data.amount FROM (VALUES %s) AS data (uid, amount) WHERE players.uid = data.uid",
                        gen_updates
                    )

            conn.commit()
    except Exception as e:
        print(f"/// XP FLUSH ERROR: {e}")
        try:
            conn.rollback()
        except:
            pass
        # Restore the failed XP updates back to cache so they aren't lost
        with _xp_cache_lock:
            for uid, amount in cache_copy.items():
                _xp_cache[uid] = _xp_cache.get(uid, 0) + amount
"""

# Regex substitution
db_content = re.sub(r'def _flush_xp_cache\(\):.*?threading\.Thread\(target=_flush_xp_cache, daemon=True\)\.start\(\)', new_flush_xp_cache.strip() + '\n', db_content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(db_content)


# 2. Patch bot.py to use APScheduler
with open('bot.py', 'r') as f:
    bot_content = f.read()

# Remove old threads
bot_content = re.sub(r'def stats_flusher\(\):.*?threading\.Thread\(target=stats_flusher, daemon=True\)\.start\(\)', '', bot_content, flags=re.DOTALL)
bot_content = re.sub(r'def notification_loop\(\):.*?threading\.Thread\(target=notification_loop, daemon=True\)\.start\(\)', '', bot_content, flags=re.DOTALL)

# Insert APScheduler and new functions
aps_imports = """
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# -- SCHEDULER JOBS --
def aps_stats_flusher():
    with _stats_lock:
        if not _stats_cache:
            return
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

def aps_notification_loop():
    if getattr(db, '_formatted_db_url', None) is None:
        db.init_pool()

    users = []
    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                now = int(time.time())
                cur.execute(\"\"\"
                    SELECT uid FROM players
                    WHERE last_protocol_time > 0
                    AND (last_protocol_time + 1800) < %s
                    AND notified = FALSE
                    AND is_active = TRUE
                    LIMIT 200
                \"\"\", (now,))
                users = cur.fetchall()
    except Exception as db_err:
        print(f"/// NOTIFICATION LOOP DB ERROR: {db_err}")
        return

    for row in users:
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
        time.sleep(0.05)

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(aps_stats_flusher, IntervalTrigger(seconds=30), id='stats_flusher', replace_existing=True)
scheduler.add_job(db._flush_xp_cache, IntervalTrigger(seconds=60), id='xp_flusher', replace_existing=True)
scheduler.add_job(aps_notification_loop, IntervalTrigger(seconds=60), id='notification_loop', replace_existing=True)
scheduler.start()
print("/// APSCHEDULER STARTED WITH JOBS: stats_flusher(30s), xp_flusher(60s), notification_loop(60s)")
"""

bot_content = re.sub(r'start_worker\(bot\)\nthreading\.Thread\(target=system_startup, daemon=True\)\.start\(\)', aps_imports + '\nstart_worker(bot)\nthreading.Thread(target=system_startup, daemon=True).start()', bot_content)


with open('bot.py', 'w') as f:
    f.write(bot_content)
