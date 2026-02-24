import time
from datetime import date
import database as db
from config import LEVELS, LEVEL_UP_MSG, ACHIEVEMENTS_LIST, ITEMS_INFO

def check_daily_streak(uid):
    u = db.get_user(uid)
    if not u: return

    last_active = u.get('last_active')
    # Ensure date object
    if not last_active:
        db.update_user(uid, last_active=date.today())
        return

    today = date.today()

    if last_active == today:
        return

    delta = (today - last_active).days

    # --- NIGHT VISITS (03:00 - 05:00) ---
    import datetime
    now_hour = datetime.datetime.now().hour
    if 3 <= now_hour < 5:
        db.increment_user_stat(uid, 'night_visits')

    if delta == 1:
        # Streak continues
        new_streak = u.get('streak', 0) + 1
        db.update_user(uid, streak=new_streak, last_active=today)

    elif delta > 1:
        # Streak broken
        cryo_count = db.get_item_count(uid, 'cryo')
        if cryo_count > 0:
            db.use_item(uid, 'cryo', 1)
            db.update_user(uid, last_active=today)
            db.log_action(uid, 'streak_saved', f"Cryo used. Streak: {u.get('streak')}")
            try:
                from modules.bot_instance import bot
                bot.send_message(uid, "❄️ <b>КРИО-СТАЗИС ОТКЛЮЧЕН</b>\n\nВаш стрик сохранен благодаря капсуле.", parse_mode="HTML")
            except: pass
        else:
            # Penalty
            current_streak = u.get('streak', 1)
            current_xp = u.get('xp', 0)

            penalty_xp = int(current_xp * 0.1)
            new_xp = max(0, current_xp - penalty_xp)

            db.update_user(uid, streak=1, xp=new_xp, last_active=today)
            db.log_action(uid, 'streak_lost', f"Lost {penalty_xp} XP. Old streak: {current_streak}")

            try:
                from modules.bot_instance import bot
                bot.send_message(uid, f"📉 <b>НЕЙРОННЫЙ РАСПАД</b>\n\nВы отсутствовали {delta} дн.\n• Стрик сброшен.\n• Потеряно: {penalty_xp} XP.\n\n<i>Купите КРИО-капсулу, чтобы избежать этого.</i>", parse_mode="HTML")
            except: pass

def get_level_progress_stats(u):
    if not u: return 0, 0
    level = u.get("level", 1)
    xp = u.get("xp", 0)

    target = LEVELS.get(level, 999999)
    if level == 1:
        prev_target = 0
    else:
        prev_target = LEVELS.get(level - 1, 0)

    needed = target - xp
    total = target - prev_target
    current = xp - prev_target

    if total <= 0: perc = 100
    else: perc = int((current / total) * 100)

    return max(0, perc), max(0, needed)

def check_level_up(uid):
    u = db.get_user(uid)
    if not u: return None, None

    current_level = u.get('level', 1)
    xp = u.get('xp', 0)
    new_level = current_level

    while True:
        target = LEVELS.get(new_level)
        if target and xp >= target:
            new_level += 1
        else:
            break

    if new_level > current_level:
        db.update_user(uid, level=new_level)
        msg = LEVEL_UP_MSG.get(new_level, f"🔓 <b>LVL {new_level}</b>\nУровень повышен!")
        return new_level, msg

    return None, None

def get_profile_stats(uid):
    u = db.get_user(uid)
    if not u: return None

    streak = u.get('streak', 0)
    level = u.get('level', 1)

    streak_bonus = streak * 50
    income_total = (level * 1000) + streak_bonus + (u.get('ref_profit_xp', 0) + u.get('ref_profit_coins', 0))

    return {
        "streak": streak,
        "streak_bonus": streak_bonus,
        "max_depth": u.get('max_depth', 0),
        "raid_count": u.get('raid_count_today', 0),
        "income_total": income_total
    }

def get_syndicate_stats(uid):
    refs = db.get_referrals_stats(uid)
    if not refs: return "🌐 <b>СЕТЬ ОФФЛАЙН</b>\nНет подключенных узлов."

    txt = f"🔗 <b>СЕТЬ ({len(refs)} узлов):</b>\n\n"
    total_profit = 0

    for r in refs:
        if isinstance(r, dict):
             username = r.get('username', 'Anon')
             level = r.get('level', 1)
             profit = r.get('ref_profit_xp', 0) + r.get('ref_profit_coins', 0)
        else:
             username = r[0]
             level = r[2]
             profit = r[3] + r[4]

        total_profit += profit
        txt += f"👤 <b>@{username}</b> (Lvl {level})\n   └ 💸 Роялти: +{profit}\n"

    txt += f"\n💰 <b>ВСЕГО ПОЛУЧЕНО:</b> {total_profit}"
    return txt

def check_achievements(uid):
    u = db.get_user(uid)
    if not u: return []

    new_achs = []
    user_achs = db.get_user_achievements(uid)

    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if ach_id in user_achs: continue

        try:
            if data['cond'](u):
                if db.grant_achievement(uid, ach_id, data['xp']):
                    new_achs.append(data)
        except: pass

    return new_achs

def get_user_stats(uid):
    u = db.get_user(uid)
    if not u: return None, None

    eq = db.get_equipped_items(uid)
    stats = {'atk': 0, 'def': 0, 'luck': 0}

    for slot, item_id in eq.items():
        info = ITEMS_INFO.get(item_id, {})
        stats['atk'] += info.get('atk', 0)
        stats['def'] += info.get('def', 0)
        stats['luck'] += info.get('luck', 0)

    # School bonus
    if u['path'] == 'mind': stats['def'] += 10
    elif u['path'] == 'tech': stats['luck'] += 10

    # --- ANOMALY DEBUFF: CORROSION ---
    if u.get('anomaly_buff_expiry', 0) > time.time() and u.get('anomaly_buff_type') == 'corrosion':
        stats['atk'] = int(stats['atk'] * 0.8)
        stats['def'] = int(stats['def'] * 0.8)

    # --- IMPOSTER SYNDROME (Chip) ---
    if eq.get('chip') == 'imposter_syndrome':
        # Fetch Top 1 stats
        top_user_data = db.get_leaderboard(limit=1, sort_by='xp')
        if top_user_data:
            top_u = top_user_data[0]
            # Avoid self-copy if already top 1? The item says "copy ... player at 1st place".
            # If self is 1st, it copies self (no change).
            if str(top_u['uid']) != str(uid):
                # We need to get stats of that user.
                # WARNING: Recursion if we call get_user_stats again?
                # No, db.get_equipped_items is separate.
                # But get_user_stats calls get_equipped_items.
                # We need to calculate their stats manually here to avoid recursion loop if they also have Imposter Syndrome (though unlikely to matter, just one level).
                # Actually, better to just get their base stats from equipment.

                top_eq = db.get_equipped_items(top_u['uid'])
                top_stats = {'atk': 0, 'def': 0, 'luck': 0}
                for _, t_item in top_eq.items():
                    t_info = ITEMS_INFO.get(t_item, {})
                    top_stats['atk'] += t_info.get('atk', 0)
                    top_stats['def'] += t_info.get('def', 0)
                    top_stats['luck'] += t_info.get('luck', 0)

                # Apply school bonus for them
                if top_u['path'] == 'mind': top_stats['def'] += 10
                elif top_u['path'] == 'tech': top_stats['luck'] += 10

                stats = top_stats

    return stats, u

def perform_hard_reset(uid):
    u = db.get_user(uid)
    if not u: return False

    # Archive Data
    import json
    inv = db.get_inventory(uid)
    eq = db.get_equipped_items(uid)
    ach = db.get_user_achievements(uid)

    archive = {
        'user': u,
        'inventory': inv,
        'equipment': eq,
        'achievements': ach
    }

    try:
        db.save_history(uid, json.dumps(archive, default=str))
        db.hard_reset_user(uid)
        db.log_action(uid, 'hard_reset', 'User initiated purification sync')
        return True
    except Exception as e:
        print(f"Hard Reset Error: {e}")
        return False
