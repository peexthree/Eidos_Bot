import random
import time
import database as db
import config
from config import EQUIPMENT_DB
from content_presets import CONTENT_DATA

def get_content_logic(c_type, path='general', level=1, decoder=False):
    # FORCE RANDOM PATH FOR PROTOCOLS (Module 1)
    if c_type == 'protocol':
        path = 'all'

    # 1. Try DB first
    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        query = "SELECT * FROM content WHERE type=%s AND level <= %s"
        params = [c_type, level]

        if path != 'all':
            if path != 'general':
                query += " AND (path=%s OR path='general')"
                params.append(path)
            else:
                query += " AND path='general'"
        # If 'all', we don't filter by path, so we get random path

        query += " ORDER BY RANDOM() LIMIT 1"
        cur.execute(query, tuple(params))
        res = cur.fetchone()

        if res: return res

    # 2. Fallback to PRESETS
    pool = []
    for l in range(1, level + 1):
        if l in CONTENT_DATA:
            pool.extend(CONTENT_DATA[l])

    filtered = [c for c in pool if c['type'] == c_type]

    if path != 'all':
        if path == 'general':
            filtered = [c for c in filtered if c['path'] == 'general']
        else:
            filtered = [c for c in filtered if c['path'] == path or c['path'] == 'general']

    if filtered:
        choice = random.choice(filtered).copy()
        return choice

    return None

def start_decryption(uid):
    # Check if user has cache item
    if db.get_item_count(uid, 'encrypted_cache') <= 0:
        return False, "❌ У вас нет Зашифрованного Кэша."

    u = db.get_user(uid)
    # Check if already unlocking (unlock_time > 0)
    unlock_time = u.get('encrypted_cache_unlock_time', 0)
    try:
        unlock_time = float(unlock_time)
    except (ValueError, TypeError):
        unlock_time = 0

    if unlock_time > 0:
        # If time passed, tell them to claim. If not, tell them to wait.
        if time.time() >= unlock_time:
             return False, "✅ Кэш уже взломан! Нажмите 'Открыть'."
        else:
             return False, "⏳ Процесс уже идет."

    # Calc time
    base_hours = 4.0
    # Faction Bonus
    if u['path'] == 'tech':
        base_hours = 2.0

    # Item Bonus
    has_decoder = db.get_item_count(uid, 'decoder') > 0
    if has_decoder:
        base_hours /= 2.0

    unlock_time = int(time.time() + (base_hours * 3600))

    # Consume item to start
    if db.use_item(uid, 'encrypted_cache', 1):
        db.update_user(uid, encrypted_cache_unlock_time=unlock_time, encrypted_cache_type='standard')
        hours_fmt = f"{base_hours}ч" if base_hours.is_integer() else f"{base_hours}ч"
        return True, f"🔐 <b>РАСШИФРОВКА ЗАПУЩЕНА</b>\n⏱ Время: {hours_fmt}\n\n<i>Система подбирает ключи...</i>"

    return False, "⚠️ Ошибка предмета."

def claim_decrypted_cache(uid):
    u = db.get_user(uid)
    unlock_time = u.get('encrypted_cache_unlock_time', 0)
    try:
        unlock_time = float(unlock_time)
    except (ValueError, TypeError):
        unlock_time = 0

    if unlock_time == 0:
        return False, "❌ Нет активных контейнеров."

    if time.time() < unlock_time:
        rem = int((unlock_time - time.time()) // 60)
        hours = rem // 60
        mins = rem % 60
        return False, f"⏳ <b>ОСТАЛОСЬ:</b> {hours}ч {mins}м"

    # Grant Loot
    xp = random.randint(500, 1500)
    coins = random.randint(500, 1000)

    db.add_xp_to_user(uid, xp)
    db.update_user(uid, biocoin=u['biocoin'] + coins)

    msg = f"⚡️ +{xp} XP\n🪙 +{coins} BC"

    # Rare Item Drop (30% chance) - TIERED SYSTEM
    if random.random() < 0.30:
        import config
        candidates = []
        roll = random.random()

        if roll < 0.05: # Legendary/Mythical (5% of 30% ~ 1.5%)
             candidates = [k for k,v in config.EQUIPMENT_DB.items() if v['price'] >= 10000]
        elif roll < 0.25: # Epic (20%)
             candidates = [k for k,v in config.EQUIPMENT_DB.items() if v['price'] >= 4000 and v['price'] < 10000]
        else: # Rare (75%)
             candidates = [k for k,v in config.EQUIPMENT_DB.items() if v['price'] >= 1000 and v['price'] < 4000]

        # Fallback if empty (e.g. config changes)
        if not candidates:
             candidates = [k for k,v in config.EQUIPMENT_DB.items() if v['price'] >= 1000]

        if candidates:
            item = random.choice(candidates)
            db.add_item(uid, item)
            name = config.EQUIPMENT_DB[item]['name']
            tier_icon = "🟠" if roll < 0.05 else "🟣" if roll < 0.25 else "🔵"
            msg += f"\n📦 <b>ПРЕДМЕТ:</b> {tier_icon} {name}"

    # Reset
    db.update_user(uid, encrypted_cache_unlock_time=0, encrypted_cache_type=None)

    return True, f"🔓 <b>КОНТЕЙНЕР ВЗЛОМАН!</b>\n\n{msg}"

def get_decryption_status(uid):
    u = db.get_user(uid)
    unlock_time = u.get('encrypted_cache_unlock_time', 0)
    try:
        unlock_time = float(unlock_time)
    except (ValueError, TypeError):
        unlock_time = 0

    if unlock_time == 0:
        count = db.get_item_count(uid, 'encrypted_cache')
        if count > 0:
            return "ready_to_start", f"📦 Кэш в инвентаре: {count} шт."
        return "none", "Нет контейнеров."

    if time.time() < unlock_time:
        rem = int((unlock_time - time.time()) // 60)
        hours = rem // 60
        mins = rem % 60
        return "in_progress", f"⏳ {hours}ч {mins}м"

    return "ready_to_claim", "✅ <b>ГОТОВО!</b>"

def check_shadow_broker_trigger(uid):
    u = db.get_user(uid)
    if not u: return False, 0

    # Don't trigger if already active
    expiry = u.get('shadow_broker_expiry', 0)
    try:
        expiry = float(expiry)
    except (ValueError, TypeError):
        expiry = 0

    if expiry > time.time():
        return False, 0

    # 5% chance (per TZ/README)
    if random.random() < 0.05:
        expiry = int(time.time() + 900) # 15 mins
        db.set_shadow_broker(uid, expiry)
        return True, expiry
    return False, 0

def get_full_archive_chunks(uid):
    protocols = db.get_archived_protocols(uid)
    if not protocols:
        return ["💾 <b>АРХИВ ПРОТОКОЛОВ</b>\n\nПусто."]

    chunks = []
    current_chunk = "💾 <b>ПОЛНЫЙ АРХИВ ПРОТОКОЛОВ</b>\n\n"

    for i, p in enumerate(protocols, 1):
        entry = f"💠 <b>ЗАПИСЬ #{i}</b>\n{p['text']}\n\n"
        if len(current_chunk) + len(entry) > 4000:
            chunks.append(current_chunk)
            current_chunk = entry
        else:
            current_chunk += entry

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
