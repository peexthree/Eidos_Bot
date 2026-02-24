import time
import random
import database as db
import config
from modules.services.user import get_user_stats

def find_target(attacker_uid):
    """
    Finds a random target for PVP.
    """
    for _ in range(10):
        target_uid = db.get_random_user_for_hack(attacker_uid)
        if not target_uid: continue

        target = db.get_user(target_uid)
        if not target: continue

        if target.get('level', 1) <= config.QUARANTINE_LEVEL: continue
        if db.check_pvp_cooldown(attacker_uid, target_uid): continue
        if target.get('is_quarantined'): continue

        real_bal = target.get('biocoin', 0)
        est_base = int(real_bal * 0.075)
        est_base = min(est_base, 5000)
        if est_base < 100: est_base = 100

        est_min = int(est_base * 0.8)
        est_max = int(est_base * 1.2)

        t_stats, _ = get_user_stats(target_uid)
        threat = "🟢 НИЗКИЙ"
        if t_stats['def'] > 50: threat = "🔴 ВЫСОКИЙ"
        elif t_stats['def'] > 20: threat = "🟡 СРЕДНИЙ"

        return {
            'uid': target_uid,
            'name': target.get('username') or target.get('first_name') or "Unknown",
            'level': target.get('level', 1),
            'est_loot_min': est_min,
            'est_loot_max': est_max,
            'threat': threat
        }

    return None

def calculate_hack_chance(attacker_uid, target_uid):
    a_stats, _ = get_user_stats(attacker_uid)
    t_stats, _ = get_user_stats(target_uid)
    target = db.get_user(target_uid)

    a_score = a_stats['atk'] + (a_stats['luck'] * 1.5)
    d_score = t_stats['def'] + (target['level'] * 5)

    diff = a_score - d_score
    chance = 50 + (diff * 0.5)

    return max(10, min(90, int(chance)))

def perform_hack(attacker_uid, target_uid, method='normal', revenge_amount=0):
    """
    Executes the hack.
    method: 'normal', 'stealth', 'revenge'
    revenge_amount: If method='revenge', try to steal this amount.
    """
    attacker = db.get_user(attacker_uid)
    target = db.get_user(target_uid)

    if not attacker or not target:
        return {'success': False, 'msg': "User not found"}

    # 1. Check Costs
    cost_xp = 0
    if method == 'stealth':
        cost_xp = config.PVP_STEALTH_COST
    elif method == 'revenge':
        cost_xp = 50
    elif method == 'normal':
        cost_xp = config.PVP_DIRTY_COST

    if attacker['xp'] < cost_xp:
        return {'success': False, 'msg': f"Not enough XP (Need {cost_xp})"}

    # 2. Check Cooldown (Skip for Revenge)
    if method != 'revenge':
        if db.check_pvp_cooldown(attacker_uid, target_uid):
            return {'success': False, 'msg': "Target on cooldown (12h)"}

    # CROWN OF PARANOIA (Target) - Immune to PvP
    target_head = db.get_equipped_items(target_uid).get('head')
    if target_head == 'crown_paranoia':
        return {'success': False, 'msg': "🛡 TARGET IS UNTOUCHABLE (Paranoia Crown)"}

    # 3. Anonymity Check
    is_anonymous = False
    if attacker.get('proxy_expiry', 0) > time.time():
        is_anonymous = True

    # 4. Calculate Outcome
    chance = calculate_hack_chance(attacker_uid, target_uid)

    # JUDAS SHELL (Target) - Def = 0 (effectively increases hack chance significantly)
    target_armor = db.get_equipped_items(target_uid).get('armor')
    if target_armor == 'judas_shell':
        chance = 99 # Guaranteed mostly

    roll = random.randint(1, 100)
    is_success = roll <= chance

    # 5. Defense Items Check (Pre-check logic, actual check in DB)
    blocked_by_firewall = False

    # 6. Execute Transaction
    stolen = 0
    lost_xp = 0
    ice_trap_triggered = False
    log_id = None

    try:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                # Lock Target Row & Get Fresh Balance
                cur.execute("SELECT biocoin FROM users WHERE uid = %s FOR UPDATE", (target_uid,))
                res = cur.fetchone()
                target_bal = res[0] if res else 0

                # Check Firewall (Atomic)
                firewalls = db.get_item_count(target_uid, 'firewall', cursor=cur)
                if firewalls > 0:
                    blocked_by_firewall = True
                    is_success = False
                    db.use_item(target_uid, 'firewall', 1, cursor=cur)

                # Pay Cost
                if cost_xp > 0:
                    cur.execute("UPDATE users SET xp = xp - %s WHERE uid = %s", (cost_xp, attacker_uid))

                if not blocked_by_firewall and is_success:
                    amount = 0
                    if method == 'revenge':
                        # Try to recover specific amount
                        amount = min(revenge_amount, target_bal)
                    else:
                        # Standard Steal
                        percent = random.uniform(0.05, 0.10)

                        # JUDAS SHELL (Target) - Double Steal
                        if target_armor == 'judas_shell':
                            percent *= 2.0

                        amount = int(target_bal * percent)
                        amount = min(amount, 5000 * (2 if target_armor == 'judas_shell' else 1))

                    # Prevent negative
                    amount = max(0, amount)

                    if amount > 0:
                        stolen = amount
                        cur.execute("UPDATE users SET biocoin = biocoin - %s WHERE uid = %s", (stolen, target_uid))
                        cur.execute("UPDATE users SET biocoin = biocoin + %s WHERE uid = %s", (stolen, attacker_uid))

                elif not blocked_by_firewall and not is_success:
                    # Failure Logic (Ice Trap)
                    traps = db.get_item_count(target_uid, 'ice_trap', cursor=cur)
                    if traps > 0:
                        ice_trap_triggered = True
                        steal_xp = 200
                        cur.execute("UPDATE users SET xp = GREATEST(0, xp - %s) WHERE uid = %s", (steal_xp, attacker_uid))
                        cur.execute("UPDATE users SET xp = xp + %s WHERE uid = %s", (steal_xp, target_uid))
                        lost_xp = steal_xp
                        db.use_item(target_uid, 'ice_trap', 1, cursor=cur)

                # Logging
                if not is_success and method == 'stealth':
                    is_anonymous = True
                if attacker.get('proxy_expiry', 0) > time.time():
                    is_anonymous = True

                is_revenged_log = (method == 'revenge' and is_success)

                cur.execute("""
                    INSERT INTO pvp_logs (attacker_uid, target_uid, stolen_coins, success, timestamp, is_revenged, is_anonymous)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (attacker_uid, target_uid, stolen, is_success, int(time.time()), is_revenged_log, is_anonymous))
                log_id = cur.fetchone()[0]

    except Exception as e:
        print(f"PVP Transaction Error: {e}")
        return {'success': False, 'msg': f"Database Error: {e}"}

    target_name = target.get('username') or target.get('first_name') or "Unknown"

    return {
        'success': is_success,
        'stolen': stolen,
        'blocked': blocked_by_firewall,
        'ice_trap': ice_trap_triggered,
        'lost_xp': lost_xp,
        'anonymous': is_anonymous,
        'target_name': target_name,
        'log_id': log_id
    }

def get_revenge_list(uid):
    return db.get_pvp_history(uid)
