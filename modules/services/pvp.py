import time
import random
import json
import database as db
import config
from modules.services.user import get_user_stats

# =============================================================================
# DECK & INVENTORY MANAGEMENT (v2.0)
# =============================================================================

def get_deck(uid):
    """
    Retrieves the user's cyber deck configuration.
    Returns: {'level': int, 'slots': int, 'config': dict}
    """
    user = db.get_user(uid)
    if not user:
        return None

    level = user.get('deck_level', 1)

    # Get max slots for level
    upgrade_info = config.DECK_UPGRADES.get(level, {"slots": 1})
    max_slots = upgrade_info['slots']

    # Parse config
    config_json = user.get('deck_config')
    deck_config = {}
    if config_json:
        try:
            deck_config = json.loads(config_json)
        except:
            deck_config = {"1": "soft_brute_v1"} # Fallback default
    else:
        deck_config = {"1": "soft_brute_v1"}

    # Ensure config has entries for all slots (even if None)
    for i in range(1, max_slots + 1):
        if str(i) not in deck_config:
            deck_config[str(i)] = None

    return {
        'level': level,
        'slots': max_slots,
        'config': deck_config
    }

def set_slot(uid, slot_id, software_id):
    """
    Equips software into a deck slot.
    slot_id: str ("1", "2", "3")
    software_id: str (from config.SOFTWARE_DB) or None to unequip
    """
    user = db.get_user(uid)
    if not user: return False, "User not found"

    # Validate software ownership
    if software_id:
        count = db.get_item_count(uid, software_id)
        if count < 1:
            return False, "❌ Программа не куплена!"

        # Verify valid software
        if software_id not in config.SOFTWARE_DB:
            return False, "❌ Неизвестная программа."

    # Get current deck
    deck_data = get_deck(uid)
    current_config = deck_data['config']
    max_slots = deck_data['slots']

    if int(slot_id) > max_slots:
        return False, f"❌ Слот {slot_id} недоступен (Уровень деки мал)."

    # Check for duplicates (One item - One slot)
    if software_id:
        for s, val in current_config.items():
            if val == software_id and str(s) != str(slot_id):
                return False, "❌ Эта программа уже установлена в другой слот!"

    # Update config
    current_config[str(slot_id)] = software_id

    new_config_json = json.dumps(current_config)
    db.update_user(uid, deck_config=new_config_json)

    return True, "✅ Программа установлена."

def upgrade_deck(uid):
    """
    Upgrades deck level using BioCoins.
    """
    user = db.get_user(uid)
    current_level = user.get('deck_level', 1)
    next_level = current_level + 1

    if next_level not in config.DECK_UPGRADES:
        return False, "❌ Максимальный уровень!"

    cost = config.DECK_UPGRADES[next_level]['cost']

    # Transaction with Atomic Check
    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                # Deduct BioCoins safely
                cur.execute("UPDATE users SET biocoin = biocoin - %s WHERE uid = %s AND biocoin >= %s", (cost, uid, cost))
                if cur.rowcount == 0:
                    return False, f"❌ Не хватает BioCoins ({cost} нужно)."

                # Upgrade Level
                cur.execute("UPDATE users SET deck_level = %s WHERE uid = %s", (next_level, uid))
        return True, f"🆙 Дека улучшена до уровня {next_level}!"
    except Exception as e:
        return False, f"Error: {e}"

def buy_software(uid, software_id, is_hardware=False):
    """
    Purchases software/hardware using BioCoins (or XP for Proxy).
    """
    msg = None
    if is_hardware:
        from config import ITEMS_INFO, PRICES
        if software_id not in ITEMS_INFO: return False, "Товар не найден."
        info = ITEMS_INFO[software_id]
        cost = PRICES.get(software_id, 0)
        currency = 'xp' if software_id == 'proxy_server' else 'biocoin'
    else:
        soft = config.SOFTWARE_DB.get(software_id)
        if not soft: return False, "Программа не найдена."
        cost = soft['cost']
        currency = 'biocoin'
        info = soft

    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                if currency == 'biocoin':
                    cur.execute("UPDATE users SET biocoin = biocoin - %s WHERE uid = %s AND biocoin >= %s", (cost, uid, cost))
                else:
                    cur.execute("UPDATE users SET xp = xp - %s WHERE uid = %s AND xp >= %s", (cost, uid, cost))

                if cur.rowcount == 0:
                    return False, f"❌ Не хватает средств ({cost} {currency.upper()} нужно)."

                # Special logic for Proxy
                if software_id == 'proxy_server':
                    expiry = int(time.time() + 86400) # 24h
                    cur.execute("UPDATE users SET proxy_expiry = %s WHERE uid = %s", (expiry, uid))
                    msg = "🕶 Прокси активирован на 24 часа."
                else:
                    # Add Item
                    added = db.add_item(uid, software_id, cursor=cur)
                    if not added:
                        raise ValueError("Инвентарь полон!")

                    msg = f"💾 {info['name']} приобретен!"

        if msg is None:
            return False, "❌ Ошибка транзакции (Инвентарь полон?)"

        return True, msg
    except Exception as e:
        return False, f"Error: {e}"

def get_software_inventory(uid):
    """
    Returns list of owned PVP items (Software + Hardware).
    """
    all_items = db.get_inventory(uid)
    software = []
    for item in all_items:
        sid = item['item_id']

        # Check Software
        if sid in config.SOFTWARE_DB:
            info = config.SOFTWARE_DB[sid]
            software.append({
                'id': sid,
                'name': info['name'],
                'type': info['type'],
                'icon': info['icon'],
                'power': info['power'],
                'desc': info['desc'],
                'quantity': item['quantity'],
                'durability': item['durability'],
                'category': 'software'
            })

        # Check Hardware
        elif sid in config.PVP_HARDWARE:
            from config import ITEMS_INFO
            info = ITEMS_INFO.get(sid, {})
            software.append({
                'id': sid,
                'name': info.get('name', sid),
                'type': 'hardware',
                'icon': '🛠',
                'power': 'N/A',
                'desc': info.get('desc', ''),
                'quantity': item['quantity'],
                'durability': item['durability'],
                'category': 'hardware'
            })

    return software

# =============================================================================
# BATTLE ENGINE (v2.0)
# =============================================================================

def find_target(attacker_uid):
    """
    Finds a random target for PVP (v2.0 Logic).
    """
    for _ in range(15):
        target_uid = db.get_random_user_for_hack(attacker_uid)
        if not target_uid: continue

        target = db.get_user(target_uid)
        if not target: continue

        # V2 Checks:
        if target.get('biocoin', 0) < config.PVP_CONSTANTS['PROTECTION_LIMIT']: continue
        if target.get('shield_until', 0) > time.time(): continue

        if target.get('level', 1) <= config.QUARANTINE_LEVEL: continue
        if db.check_pvp_cooldown(attacker_uid, target_uid): continue
        if target.get('is_quarantined'): continue

        # Calculate Loot Estimate
        real_bal = target.get('biocoin', 0)
        steal_percent = config.PVP_CONSTANTS.get('STEAL_PERCENT', 0.10)

        est_amount = int(real_bal * steal_percent)

        # Scan slots (Masked)
        target_deck = get_deck(target_uid)
        slots_preview = {}
        for i in range(1, 4):
            val = target_deck['config'].get(str(i))
            if i > target_deck['slots']:
                slots_preview[i] = "🔒" # Locked slot
            elif val:
                slots_preview[i] = "❓"
            else:
                slots_preview[i] = "🕸" # Empty

        t_stats, _ = get_user_stats(target_uid)
        threat = "🟡 СРЕДНИЙ"

        return {
            'uid': target_uid,
            'name': target.get('username') or target.get('first_name') or "Unknown",
            'level': target.get('level', 1),
            'est_loot': est_amount,
            'slots_preview': slots_preview,
            'threat': threat
        }

    return None

def calculate_battle(attacker_deck, defender_deck):
    """
    Simulates 3 rounds of Rock-Paper-Scissors.
    ATK > DEF > STL > ATK
    """
    log = []
    score_attacker = 0
    score_defender = 0

    for i in range(1, 4):
        slot_str = str(i)

        atk_soft_id = attacker_deck.get(slot_str)
        def_soft_id = defender_deck.get(slot_str)

        atk_info = config.SOFTWARE_DB.get(atk_soft_id) if atk_soft_id else None
        def_info = config.SOFTWARE_DB.get(def_soft_id) if def_soft_id else None

        atk_type = atk_info['type'] if atk_info else None
        def_type = def_info['type'] if def_info else None

        round_res = "draw"

        if not atk_type and not def_type:
            round_res = "draw"
        elif not atk_type:
            round_res = "loss"
        elif not def_type:
            round_res = "win"
        else:
            if atk_type == def_type:
                round_res = "draw"
            elif (atk_type == 'atk' and def_type == 'def') or \
                 (atk_type == 'def' and def_type == 'stl') or \
                 (atk_type == 'stl' and def_type == 'atk'):
                round_res = "win"
            else:
                round_res = "loss"

        if round_res == "win":
            score_attacker += 1
        elif round_res == "loss":
            score_defender += 1

        log.append({
            'round': i,
            'atk_soft': atk_info,
            'def_soft': def_info,
            'result': round_res
        })

    is_success = score_attacker >= 2
    return is_success, log

def execute_hack(attacker_uid, target_uid, selected_programs):
    """
    Orchestrates the battle.
    """
    attacker = db.get_user(attacker_uid)
    target = db.get_user(target_uid)

    if not attacker or not target:
        return {'success': False, 'msg': "Error loading users"}

    # 1. Check for Hardware Defense (Firewall)
    blocked_by_fw = False
    with db.db_cursor() as cur:
        fw_count = db.get_item_count(target_uid, 'firewall', cursor=cur)
        if fw_count > 0:
            db.use_item(target_uid, 'firewall', 1, cursor=cur)
            blocked_by_fw = True

    if blocked_by_fw:
        return {
            'success': False,
            'log': [],
            'stolen': 0,
            'reward': 0,
            'target_name': target.get('username') or "Unknown",
            'log_id': None,
            'lost_xp': 0,
            'blocked': True
        }

    # 2. Battle
    target_deck_data = get_deck(target_uid)
    target_config = target_deck_data['config']

    success, battle_log = calculate_battle(selected_programs, target_config)

    stolen_coins = 0
    reward_coins = 0
    lost_xp = 0
    ice_trap_triggered = False

    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                # Lock target
                cur.execute("SELECT biocoin FROM users WHERE uid = %s FOR UPDATE", (target_uid,))
                real_bal = cur.fetchone()[0]

                if success:
                    # Reward Coins (Mining)
                    reward_coins = config.PVP_CONSTANTS['HACK_REWARD'] + random.randint(0, 10)

                    # Steal Coins
                    steal_pct = config.PVP_CONSTANTS['STEAL_PERCENT']
                    amount = int(real_bal * steal_pct)
                    amount = min(amount, int(real_bal * (config.PVP_CONSTANTS['MAX_STEAL']/100)))

                    # Total Gain
                    total_gain = reward_coins + amount
                    cur.execute("UPDATE users SET biocoin = biocoin + %s WHERE uid = %s", (total_gain, attacker_uid))

                    if amount > 0:
                        stolen_coins = amount
                        cur.execute("UPDATE users SET biocoin = biocoin - %s WHERE uid = %s", (amount, target_uid))

                    # Set Shield
                    shield_end = int(time.time() + config.PVP_CONSTANTS['SHIELD_DURATION'])
                    cur.execute("UPDATE users SET shield_until = %s WHERE uid = %s", (shield_end, target_uid))

                else:
                    # Failure Logic
                    # Check ICE Trap
                    traps = db.get_item_count(target_uid, 'ice_trap', cursor=cur)

                    lost_xp = 100 # Base penalty

                    if traps > 0:
                        ice_trap_triggered = True
                        db.use_item(target_uid, 'ice_trap', 1, cursor=cur)
                        lost_xp = 300 # Enhanced penalty

                        # Steal XP (give to defender)
                        cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (lost_xp, target_uid))

                    cur.execute("UPDATE users SET xp = GREATEST(0, xp - %s) WHERE uid = %s", (lost_xp, attacker_uid))

                # Reduce Durability of used programs (Attacker)
                for slot, soft_id in selected_programs.items():
                    if soft_id:
                        db.decrease_durability(attacker_uid, soft_id, amount=1)

                # Log
                is_anonymous = False
                if attacker.get('proxy_expiry', 0) > time.time():
                    is_anonymous = True

                cur.execute("""
                    INSERT INTO pvp_logs (attacker_uid, target_uid, stolen_coins, success, timestamp, is_revenged, is_anonymous)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (attacker_uid, target_uid, stolen_coins, success, int(time.time()), False, is_anonymous))
                log_id = cur.fetchone()[0]

                # Update last hack target
                cur.execute("UPDATE users SET last_hack_target = %s WHERE uid = %s", (target_uid, attacker_uid))

    except Exception as e:
        return {'success': False, 'msg': f"DB Error: {e}"}

    return {
        'success': success,
        'log': battle_log,
        'stolen': stolen_coins,
        'reward': reward_coins,
        'target_name': target.get('username') or "Unknown",
        'log_id': log_id,
        'lost_xp': lost_xp,
        'ice_trap': ice_trap_triggered
    }

# =============================================================================
# LEGACY STUBS
# =============================================================================

def perform_hack(attacker_uid, target_uid, method='normal', revenge_amount=0):
    return {'success': False, 'msg': "Module updating..."}

def get_revenge_list(uid):
    return db.get_pvp_history(uid)
