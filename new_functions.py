
# =============================================================
# ⚔️ БОЕВАЯ СИСТЕМА И КОНТЕНТ
# =============================================================

def get_content_logic(c_type, path='general', level=1, decoder=False):
    # 1. Try DB first
    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        query = "SELECT * FROM content WHERE type=%s AND level <= %s"
        params = [c_type, level]

        if path != 'general':
            query += " AND (path=%s OR path='general')"
            params.append(path)
        else:
            query += " AND path='general'"

        query += " ORDER BY RANDOM() LIMIT 1"
        cur.execute(query, tuple(params))
        res = cur.fetchone()

        if res: return res

    # 2. Fallback to PRESETS
    pool = []
    for l in range(1, level + 1):
        if l in LEVEL_CONTENT:
            pool.extend(LEVEL_CONTENT[l])

    filtered = [c for c in pool if c['type'] == c_type]

    if path == 'general':
        filtered = [c for c in filtered if c['path'] == 'general']
    else:
        filtered = [c for c in filtered if c['path'] == path or c['path'] == 'general']

    if filtered:
        choice = random.choice(filtered).copy()
        choice['id'] = 0
        return choice

    return None

def process_combat_action(uid, action):
    stats, u = get_user_stats(uid)
    if not u: return 'error', "Пользователь не найден."

    s = db.get_raid_session_enemy(uid)

    if not s or not s.get('current_enemy_id'):
         return 'error', "Нет активного боя."

    enemy_id = s['current_enemy_id']
    enemy_hp = s['current_enemy_hp']

    villain = db.get_villain_by_id(enemy_id)
    if not villain:
        db.clear_raid_enemy(uid)
        return 'error', "Враг исчез."

    msg = ""
    res_type = 'next_turn'

    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
        full_s = cur.fetchone()

    if not full_s: return 'error', "Сессия не найдена."

    current_signal = full_s['signal']

    if action == 'attack':
        is_crit = random.random() < (stats['luck'] / 100.0)
        dmg = int(stats['atk'] * (1.5 if is_crit else 1.0))
        dmg = int(dmg * random.uniform(0.8, 1.2))
        dmg = max(1, dmg)

        new_enemy_hp = enemy_hp - dmg
        crit_msg = " (КРИТ!)" if is_crit else ""
        msg += f"⚔️ <b>АТАКА:</b> Вы нанесли {dmg} урона{crit_msg}.\n"

        if new_enemy_hp <= 0:
            xp_gain = villain['xp']
            coin_gain = random.randint(villain.get('min_coins', 10), villain.get('max_coins', 50))

            if u['path'] == 'money': coin_gain = int(coin_gain * 1.2)
            if u['path'] == 'tech': xp_gain = int(xp_gain * 0.9)

            db.clear_raid_enemy(uid)
            with db.db_cursor() as cur:
                cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s, kills = kills + 1 WHERE uid=%s",
                            (xp_gain, coin_gain, uid))

            return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен.\nПолучено: +{xp_gain} XP | +{coin_gain} BC"

        else:
            db.update_raid_enemy(uid, enemy_id, new_enemy_hp)
            msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"

            enemy_dmg = max(0, villain['atk'] - stats['def'])

            used_aegis = False
            if enemy_dmg > current_signal:
                 if db.get_item_count(uid, 'aegis') > 0:
                      if db.use_item(uid, 'aegis'):
                           enemy_dmg = 0
                           msg += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                           used_aegis = True

            new_sig = max(0, current_signal - enemy_dmg)
            with db.db_cursor() as cur:
                cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_sig, uid))

            if enemy_dmg > 0:
                msg += f"🔻 <b>УДАР:</b> Вы получили -{enemy_dmg}% Сигнала.\n"
            elif used_aegis:
                pass
            else:
                msg += f"🛡 <b>БЛОК:</b> Урон поглощен броней.\n"

            if new_sig <= 0:
                report = generate_raid_report(uid, full_s)
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                return 'death', f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nВраг нанес смертельный удар.\n\n{report}"

            return 'combat', msg

    elif action == 'run':
        chance = 0.5 + (stats['luck'] / 200.0)
        if random.random() < chance:
             db.clear_raid_enemy(uid)
             return 'escaped', "🏃 <b>ПОБЕГ:</b> Вы успешно скрылись в тенях."
        else:
             msg += "🚫 <b>ПОБЕГ НЕ УДАЛСЯ.</b> Враг атакует!\n"
             enemy_dmg = max(0, villain['atk'] - stats['def'])

             used_aegis = False
             if enemy_dmg > current_signal:
                 if db.get_item_count(uid, 'aegis') > 0:
                      if db.use_item(uid, 'aegis'):
                           enemy_dmg = 0
                           msg += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                           used_aegis = True

             new_sig = max(0, current_signal - enemy_dmg)
             with db.db_cursor() as cur:
                cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_sig, uid))

             if enemy_dmg > 0:
                 msg += f"🔻 <b>УДАР:</b> -{enemy_dmg}% Сигнала.\n"
             elif used_aegis:
                 pass
             else:
                 msg += f"🛡 <b>БЛОК:</b> Урон поглощен броней.\n"

             if new_sig <= 0:
                report = generate_raid_report(uid, full_s)
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                return 'death', f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nВраг нанес смертельный удар.\n\n{report}"

             return 'combat', msg

    return res_type, msg
