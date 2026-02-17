import database as db
from config import LEVELS, RAID_STEP_COST, RAID_BIOMES, RAID_FLAVOR_TEXT, LOOT_TABLE, INVENTORY_LIMIT, ITEMS_INFO, RIDDLE_DISTRACTORS, RAID_ENTRY_COSTS
import random
import time
import re
from datetime import datetime

# =============================================================
# 🛠 УТИЛИТЫ И HUD
# =============================================================

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
    
    return stats, u

def draw_bar(curr, total, length=10):
    if total <= 0: return "░" * length
    p = max(0.0, min(1.0, curr / total))
    filled = int(length * p)
    return "█" * filled + "░" * (length - filled)

def generate_hud(uid, u, session_data):
    # Fetch inventory details
    inv_items = db.get_inventory(uid)
    inv_count = sum(i['quantity'] for i in inv_items)
    inv_limit = INVENTORY_LIMIT

    keys = 0
    consumables = []

    for i in inv_items:
        iid = i['item_id']
        if iid in ['master_key', 'abyssal_key']:
            keys += i['quantity']
        elif iid == 'battery':
            consumables.append("🔋")
        elif iid == 'neural_stimulator':
            consumables.append("💉")

    cons_str = "".join(consumables[:3]) # Limit display

    # Format
    return (
        f"🎒 Инв: {inv_count}/{inv_limit} | 🗝 Ключи: {keys} | {cons_str}\n"
        f"⚡ XP: {u['xp']} | 🪙 BC: {u['biocoin']}"
    )

def get_raid_entry_cost(uid):
    u = db.get_user(uid)
    if not u: return RAID_ENTRY_COSTS[0]

    today = datetime.now().date()
    last = u.get('last_raid_date')

    if not last or str(last) != str(today):
        return RAID_ENTRY_COSTS[0]

    count = u.get('raid_count_today', 0)
    idx = min(count, len(RAID_ENTRY_COSTS) - 1)
    return RAID_ENTRY_COSTS[idx]

def generate_raid_report(uid, s):
    # Time
    duration = int(time.time() - s['start_time'])
    mins = duration // 60
    secs = duration % 60

    kills = s.get('kills', 0)
    riddles = s.get('riddles_solved', 0)
    profit_xp = s.get('buffer_xp', 0)
    profit_coins = s.get('buffer_coins', 0)

    return (
        f"🏁 <b>ЭКСПЕДИЦИЯ ЗАВЕРШЕНА</b>\n"
        f"⏱ Время: {mins}м {secs}с\n"
        f"💀 Убито врагов: {kills}\n"
        f"🧠 Решено загадок: {riddles}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💎 <b>ДОБЫЧА:</b>\n"
        f"📈 Чистый профит: +{profit_xp} XP | +{profit_coins} BC"
    )

# =============================================================
# ⚔️ БОЕВКА И СОБЫТИЯ
# =============================================================

def format_combat_screen(villain, hp, signal, stats, session):
    sig_bar = draw_bar(signal, 100, 8)
    hp_bar = draw_bar(hp, villain['hp'], 8)
    win_chance = min(95, max(10, 50 + (stats['atk'] - villain['def']) * 2))
    
    txt = (
        f"⚠️ <b>ВНИМАНИЕ! ОБНАРУЖЕНА УГРОЗА!</b>\n\n"
        f"👹 <b>{villain['name']}</b> (Lvl {villain['level']})\n"
        f"❤️ HP: <code>{hp_bar}</code> {hp}/{villain['hp']}\n"
        f"📝 <i>{villain['description']}</i>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📡 Твой Сигнал: <code>{sig_bar}</code> {signal}%\n"
        f"⚔️ Твоя ATK: {stats['atk']} | 🛡 DEF: {stats['def']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 <b>ШАНС ПОБЕДЫ: ~{win_chance}%</b>\n"
        f"💀 При побеге: 50% шанс получить удар в спину."
    )
    return txt

def process_riddle_answer(uid, user_answer):
    with db.db_session() as conn:
        with conn.cursor(cursor_factory=db.RealDictCursor) as cur:
            cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
            s = cur.fetchone()
            if not s or not s.get('current_riddle_answer'):
                return False, "Загадка не активна."

            correct = s['current_riddle_answer']

            # Reset riddle
            cur.execute("UPDATE raid_sessions SET current_riddle_answer=NULL WHERE uid=%s", (uid,))

            if user_answer.lower() == correct.lower():
                # Correct
                bonus_xp = 100 + (s['depth'] * 2)
                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, riddles_solved=riddles_solved+1 WHERE uid=%s", (bonus_xp, uid))
                # Chance for drop
                msg = f"✅ <b>ВЕРНО!</b>\nПолучено: +{bonus_xp} XP."
                if random.random() < 0.3:
                    db.add_item(uid, 'battery')
                    msg += "\n🎁 Награда: Батарея"
                return True, msg
            else:
                # Wrong - Damage
                dmg = 15
                new_sig = max(0, s['signal'] - dmg)
                cur.execute("UPDATE raid_sessions SET signal=%s WHERE uid=%s", (new_sig, uid))
                msg = f"❌ <b>ОШИБКА!</b>\nСистема защиты активирована.\n🔻 -{dmg}% Сигнала."
                return False, msg

def process_raid_step(uid, answer=None):
    stats, u = get_user_stats(uid)
    if not u: return False, "User not found", None, None, 'error', 0
    
    with db.db_session() as conn:
        with conn.cursor(cursor_factory=db.RealDictCursor) as cur:
            # 1. СЕССИЯ
            cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
            s = cur.fetchone()

            is_new = False
            if not s:
                # ENTRY LOGIC
                today = datetime.now().date()
                last = u.get('last_raid_date')
                if str(last) != str(today):
                    db.reset_daily_stats(uid)
                    u = db.get_user(uid)

                cost = get_raid_entry_cost(uid)
                if u['xp'] < cost:
                    return False, f"🪫 <b>МАЛО ЭНЕРГИИ</b>\nНужно {cost} XP для погружения.", None, u, 'neutral', 0

                db.update_user(uid, xp=u['xp'] - cost, raid_count_today=u.get('raid_count_today', 0) + 1, last_raid_date=today)
                u['xp'] -= cost
                pass

            depth = s['depth'] if s else u.get('max_depth', 0)
            if not s:
                 cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time, kills, riddles_solved) VALUES (%s, %s, 100, %s, 0, 0)", (uid, depth, int(time.time())))
                 conn.commit()
                 cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
                 s = cur.fetchone()
                 is_new = True

            # CHECK COMBAT
            if s.get('current_enemy_id'):
                vid = s['current_enemy_id']
                v_hp = s.get('current_enemy_hp', 10)
                villain = db.get_villain_by_id(vid)
                if villain:
                    return True, format_combat_screen(villain, v_hp, s['signal'], stats, s), None, u, 'combat', 0
                else:
                    db.clear_raid_enemy(uid)

            # CHECK RIDDLE STATE (If waiting for answer)
            if s.get('current_riddle_answer'):
                # Force riddle screen again if not answered
                # Ideally we shouldn't be here unless 'raid_step' was called without answering
                # But let's clear it if we move forward (skip riddle penalty?)
                # For simplicity: Clear it and deal damage if skipped.
                cur.execute("UPDATE raid_sessions SET signal = signal - 10, current_riddle_answer=NULL WHERE uid=%s", (uid,))
                # msg_prefix = "🚫 <b>ЗАГАДКА ПРОПУЩЕНА:</b> -10% Сигнала.\n"

            msg_prefix = ""

            # 2. ДЕЙСТВИЕ: ВЗЛОМ/ИСПОЛЬЗОВАНИЕ
            if answer == 'open_chest':
                if db.get_item_count(uid, 'abyssal_key') > 0:
                     db.use_item(uid, 'abyssal_key')
                     bonus_xp = 300 + (depth * 5)
                     bonus_coins = 100 + (depth * 2)
                     cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
                     msg_prefix = f"🗝 <b>КЛЮЧ БЕЗДНЫ:</b> +{bonus_xp} XP | +{bonus_coins} BC\n\n"
                elif db.get_item_count(uid, 'master_key') > 0:
                    db.use_item(uid, 'master_key')
                    bonus_xp = 150 + (depth * 2)
                    bonus_coins = 50 + depth
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
                    msg_prefix = f"🔓 <b>СЕРВЕР ВЗЛОМАН:</b> +{bonus_xp} XP | +{bonus_coins} BC\n\n"
                else:
                    msg_prefix = "🔒 <b>НЕТ КЛЮЧА!</b>\n\n"

            # 3. ЦЕНА ШАГА
            step_cost = RAID_STEP_COST + (depth // 25)
            if not is_new:
                if u['xp'] < step_cost:
                    return False, f"🪫 <b>ВЫДОХСЯ</b>\nНужно {step_cost} XP.", None, u, 'neutral', 0
                db.update_user(uid, xp=u['xp'] - step_cost)
                u['xp'] -= step_cost

            # 4. БИОМ
            biome = RAID_BIOMES["wasteland"]
            if 50 <= depth < 100: biome = RAID_BIOMES["archive"]
            elif depth >= 100: biome = RAID_BIOMES["darknet"]

            new_depth = depth + 1 if not is_new else depth
            diff = biome['dmg_mod']

            # 5. ГЕНЕРАЦИЯ СОБЫТИЯ
            if not is_new and random.random() < 0.15:
                villain = db.get_random_villain(depth // 20 + 1)
                if villain:
                    db.update_raid_enemy(uid, villain['id'], villain['hp'])
                    return True, format_combat_screen(villain, villain['hp'], s['signal'], stats, s), None, u, 'combat', 0

            if not is_new and random.random() < 0.15:
                event = {'type': 'locked_chest', 'text': 'Зашифрованный контейнер с лутом.', 'val': 0}
            else:
                cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
                event = cur.fetchone()
                if not event: event = {'text': "Пустые коридоры кода...", 'type': 'neutral', 'val': 0}

            # RIDDLE PARSING
            riddle_answer = None
            if 'Ответ:' in event['text']:
                 match = re.search(r'\s*\(Ответ:\s*(.*?)\)', event['text'], re.IGNORECASE)
                 if match:
                     riddle_answer = match.group(1).strip()
            event['text'] = re.sub(r'\s*\(.*?\)', '', event['text']).strip()

            new_sig = s['signal']
            riddle_data = None
            msg_event = ""

            # RPG LOGIC
            if event['type'] == 'trap':
                base_dmg = int(event['val'] * diff)
                dmg = max(5, base_dmg - stats['def'])
                if db.get_item_count(uid, 'aegis') > 0 and (new_sig - dmg <= 0):
                    db.use_item(uid, 'aegis')
                    dmg = 0
                    msg_prefix += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                new_sig = max(0, new_sig - dmg)
                flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['trap'])
                msg_event = f"💥 <b>ЛОВУШКА:</b> {flavor}\n🔻 <b>-{dmg}% Сигнала</b> (Защита: {stats['def']})"

            elif event['type'] == 'loot':
                coin_mult = 1.2 if u['path'] == 'money' else 1.0
                bonus_xp = int(event['val'] * diff * (1 + stats['atk']/100))
                coins = int(random.randint(5, 20) * (1 + stats['luck']/20) * coin_mult)
                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, coins, uid))
                flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['loot'])
                msg_event = f"💎 <b>ЛУТ:</b> {flavor}\n✳️ +{bonus_xp} XP | 🪙 +{coins} BC"
                # Drop Item
                if db.get_inventory_size(uid) < INVENTORY_LIMIT:
                    dice = random.random()
                    drop_chance = 1.0 + (stats['luck'] / 100)
                    for item, chance in LOOT_TABLE.items():
                        if dice < (chance * drop_chance):
                            if 'biocoin' in item:
                                extra_c = 50 if 'bag' in item else 15
                                cur.execute("UPDATE raid_sessions SET buffer_coins=buffer_coins+%s WHERE uid=%s", (extra_c, uid))
                                msg_prefix += f"💰 Найдено: +{extra_c} BC\n"
                            else:
                                if db.add_item(uid, item):
                                    msg_prefix += f"🎁 <b>ВЕЩЬ:</b> {ITEMS_INFO.get(item, {}).get('name', item)}\n"
                            break

            elif event['type'] == 'heal':
                new_sig = min(100, new_sig + 25)
                desc = event["text"] if len(event.get("text","")) > 15 else "Найден источник энергии."
                msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."
            else:
                flavor = event['text'] if len(event.get('text','')) > 15 else random.choice(RAID_FLAVOR_TEXT['empty'])
                msg_event = f"👣 {flavor}"

            # Riddle Setup
            if riddle_answer:
                full_answer = riddle_answer
                # Extract simple answer for button
                if " и " in full_answer or " and " in full_answer.lower():
                    parts = re.split(r' и | and ', full_answer, flags=re.IGNORECASE)
                    correct_button_text = parts[0].strip()
                else:
                    correct_button_text = full_answer

                q = event['text']
                options = random.sample(RIDDLE_DISTRACTORS, 3) + [correct_button_text]
                random.shuffle(options)

                riddle_data = {
                    "question": q,
                    "correct": correct_button_text,
                    "options": options
                }
                msg_event = f"🧩 <b>ШИФР:</b>\n{q}"
                # Save answer to DB for checking later
                cur.execute("UPDATE raid_sessions SET current_riddle_answer=%s WHERE uid=%s", (correct_button_text, uid))
                # Need to update event type so bot knows to show buttons
                event['type'] = 'riddle'

            # Compass
            compass_txt = ""
            if db.get_item_count(uid, 'compass') > 0:
                if db.decrease_durability(uid, 'compass'):
                    if event['type'] in ['loot', 'heal', 'locked_chest']: res = "❇️ РЕЗОНАНС (Лутабельно)"
                    elif event['type'] == 'trap': res = "⚠️ УГРОЗА (Ловушка)"
                    elif event['type'] == 'neutral': res = "⬜️ ТИШИНА (Пусто)"
                    elif event['type'] == 'riddle': res = "🧩 ЗАГАДКА"
                    else: res = "❓ НЕИЗВЕСТНО"
                    compass_txt = f"🧭 <b>КОМПАС:</b> {res}"
                else:
                    compass_txt = "💔 <b>КОМПАС СЛОМАЛСЯ.</b>"

            # Save state
            cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s WHERE uid=%s", (new_depth, new_sig, uid))
            if new_depth > u.get('max_depth', 0): db.update_user(uid, max_depth=new_depth)

            # Fetch buffer for HUD
            cur.execute("SELECT buffer_xp, buffer_coins, kills, riddles_solved FROM raid_sessions WHERE uid = %s", (uid,))
            res = cur.fetchone()

    # Death Check
    if new_sig <= 0:
        report = generate_raid_report(uid, s) # Use session state
        db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м\n\n{report}", None, u, 'death', 0

    # HUD
    hud_bar = generate_hud(uid, u, res)
    sig_bar = draw_bar(new_sig, 100, 8)

    interface = (
        f"🏝 <b>{biome['name']}</b> | <b>{new_depth}м</b>\n"
        f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"{msg_prefix}{msg_event}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎒 <b>+{res['buffer_xp']} XP</b> | 🪙 <b>+{res['buffer_coins']} BC</b>\n"
        f"{hud_bar}\n"
        f"⚔️ ATK {stats['atk']} | 🛡 DEF {stats['def']}\n"
        f"<i>{compass_txt}</i>"
    )
    next_step_cost = RAID_STEP_COST + (new_depth // 25)
    return True, interface, riddle_data, u, event['type'], next_step_cost

def process_combat_action(uid, action):
    stats, u = get_user_stats(uid)
    if not u: return "error", "Error"

    s = db.get_raid_session_enemy(uid)
    if not s or not s['current_enemy_id']:
        return "error", "Враг исчез или вы не в бою."

    villain = db.get_villain_by_id(s['current_enemy_id'])

    with db.db_session() as conn:
        with conn.cursor(cursor_factory=db.RealDictCursor) as cur:
            cur.execute("SELECT signal, buffer_xp, buffer_coins FROM raid_sessions WHERE uid=%s", (uid,))
            session_data = cur.fetchone()

    if not session_data: return "error", "Session lost"

    signal = session_data['signal']
    msg = ""
    result_type = "combat"

    if action == "attack":
        win_chance = min(95, max(10, 50 + (stats['atk'] - villain['def']) * 2))
        roll = random.uniform(0, 100)

        if roll <= win_chance:
            # WIN
            db.clear_raid_enemy(uid)
            xp = villain['xp_reward']
            coins = villain['coin_reward']
            with db.db_session() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s, kills=kills+1 WHERE uid=%s", (xp, coins, uid))

            msg = (f"⚔️ <b>ПОБЕДА!</b>\n"
                   f"Вы уничтожили {villain['name']}.\n"
                   f"🎁 Получено: +{xp} XP | +{coins} BC")

            # 20% Drop Chance
            if random.random() < 0.2:
                 item = "battery" if random.random() < 0.5 else "master_key"
                 db.add_item(uid, item)
                 msg += f"\n📦 Найден предмет: {ITEMS_INFO.get(item, {}).get('name', item)}"

            result_type = "win"
        else:
            # FAIL
            dmg = max(5, villain['atk'] - stats['def'])
            new_sig = max(0, signal - dmg)
            with db.db_session() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE raid_sessions SET signal=%s WHERE uid=%s", (new_sig, uid))

            msg = (f"💢 <b>ПРОМАХ!</b>\n"
                   f"{villain['name']} контратакует!\n"
                   f"🔻 -{dmg}% Сигнала.")

            if new_sig <= 0:
                result_type = "death"
                # Need session for report
                with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
                    full_s = cur.fetchone()

                report = generate_raid_report(uid, full_s)
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                msg += f"\n💀 <b>СИГНАЛ ПОТЕРЯН...</b>\n\n{report}"

    elif action == "run":
        if random.random() < 0.5:
            db.clear_raid_enemy(uid)
            msg = "🏃 <b>УСПЕШНЫЙ ПОБЕГ!</b>\nВы скрылись в цифровом шуме."
            result_type = "escaped"
        else:
            dmg = int(villain['atk'] * 0.5)
            new_sig = max(0, signal - dmg)
            with db.db_session() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE raid_sessions SET signal=%s WHERE uid=%s", (new_sig, uid))

            msg = (f"🚫 <b>НЕ ВЫШЛО!</b>\n"
                   f"Враг ударил в спину.\n"
                   f"🔻 -{dmg}% Сигнала.")

            if new_sig <= 0:
                result_type = "death"
                with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
                    full_s = cur.fetchone()

                report = generate_raid_report(uid, full_s)
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                msg += f"\n💀 <b>СИГНАЛ ПОТЕРЯН...</b>\n\n{report}"

    return result_type, msg

def get_content_logic(c_type, path='general', level=1, has_decoder=False):
    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        if not cur: return None
        eff_lvl = level + 1 if has_decoder else level
        if c_type == 'signal': cur.execute("SELECT text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
        else: cur.execute("SELECT text FROM content WHERE type='protocol' AND (path=%s OR path='general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, eff_lvl))
        return cur.fetchone()

def get_level_progress_stats(u):
    xp, lvl = u['xp'], u['level']
    cur_t = LEVELS.get(lvl, 0)
    nxt_t = LEVELS.get(lvl+1, 999999)
    need = nxt_t - cur_t
    got = max(0, xp - cur_t)
    perc = int((got / need) * 100) if need > 0 else 100
    return min(perc, 100), max(0, nxt_t - xp)

# =============================================================
# 👤 ПРОФИЛЬ И СИСТЕМЫ
# =============================================================

def get_profile_stats(uid):
    u = db.get_user(uid)
    if not u: return None

    # Income calculation (Estimated Monthly)
    # Base: Level * 1000 + Daily Streak Bonus (Streak * 50)
    streak = u.get('streak', 0)
    base_income = (u['level'] * 1000) + (streak * 50)
    ref_income = u.get('ref_profit_xp', 0) + u.get('ref_profit_coins', 0)

    return {
        "streak": streak,
        "max_depth": u.get('max_depth', 0),
        "income_base": base_income,
        "income_refs": ref_income,
        "income_total": base_income + ref_income,
        "raid_count": u.get('raid_count_today', 0)
    }

def get_syndicate_stats(uid):
    refs = db.get_referrals_stats(uid)
    if not refs: return "🌐 <b>СЕТЬ ОФФЛАЙН</b>\nНет подключенных узлов."

    txt = f"🔗 <b>СЕТЬ ({len(refs)} узлов):</b>\n\n"
    total_profit = 0

    for r in refs:
        # Check if dictionary or tuple
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

def format_inventory(uid):
    items = db.get_inventory(uid)
    equipped = db.get_equipped_items(uid)
    u = db.get_user(uid)
    inv_limit = INVENTORY_LIMIT

    txt = f"🎒 <b>РЮКЗАК [{len(items)}/{inv_limit}]</b>\n\n"

    if equipped:
        txt += "<b>🛡 ЭКИПИРОВАНО:</b>\n"
        for slot, iid in equipped.items():
            name = ITEMS_INFO.get(iid, {}).get('name', iid)
            txt += f"• {name}\n"
        txt += "\n"

    if items:
        txt += "<b>📦 ПРЕДМЕТЫ:</b>\n"
        for i in items:
            iid = i['item_id']
            name = ITEMS_INFO.get(iid, {}).get('name', iid)
            qty = i['quantity']
            desc = ITEMS_INFO.get(iid, {}).get('desc', '')[:30] + "..."
            txt += f"• <b>{name}</b> x{qty}\n  <i>{desc}</i>\n"
    else:
        txt += "<i>Пусто...</i>\n"

    # Dismantle info
    txt += f"\n♻️ <b>СТОИМОСТЬ РАЗБОРА:</b> 10%"
    return txt
