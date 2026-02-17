import database as db
from config import LEVELS, RAID_STEP_COST, RAID_BIOMES, RAID_FLAVOR_TEXT, LOOT_TABLE, INVENTORY_LIMIT, ITEMS_INFO, RIDDLE_DISTRACTORS
import random
import time
import re

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

def get_raid_entry_cost(uid):
    return 100

def format_combat_screen(villain, hp, signal, stats, session):
    sig_bar = draw_bar(signal, 100, 8)
    hp_bar = draw_bar(hp, villain['hp'], 8)
    
    # Calculate Win Chance
    # Formula: 50% base + (ATK - DEF)*2. Min 10%, Max 95%
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
                cost = get_raid_entry_cost(uid)
                if u['xp'] < cost:
                    return False, f"🪫 <b>МАЛО ЭНЕРГИИ</b>\nНужно {cost} XP для входа.", None, u, 'neutral', 0
                pass

            depth = s['depth'] if s else u.get('max_depth', 0)
            if not s:
                 cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time) VALUES (%s, %s, 100, %s)", (uid, depth, int(time.time())))
                 conn.commit()
                 cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
                 s = cur.fetchone()
                 is_new = True

            # CHECK COMBAT STATE FIRST
            if s.get('current_enemy_id'):
                # Force combat mode if enemy exists
                vid = s['current_enemy_id']
                v_hp = s.get('current_enemy_hp', 10) # Fallback
                villain = db.get_villain_by_id(vid)
                if villain:
                    return True, format_combat_screen(villain, v_hp, s['signal'], stats, s), None, u, 'combat', 0
                else:
                    db.clear_raid_enemy(uid) # Error state

            msg_prefix = ""

            # 2. ДЕЙСТВИЕ: ВЗЛОМ СУНДУКА
            if answer == 'open_chest':
                if db.get_item_count(uid, 'master_key') > 0:
                    db.use_item(uid, 'master_key')
                    bonus_xp = 150 + (depth * 2)
                    bonus_coins = 50 + depth
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
                    msg_prefix = f"🔓 <b>СЕРВЕР ВЗЛОМАН:</b> +{bonus_xp} XP | +{bonus_coins} BC\n\n"
                else:
                    msg_prefix = "🔒 <b>НЕТ КЛЮЧА!</b>\n\n"

            # 3. ЦЕНА ШАГА (Skip cost if new)
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
            # 15% Chance for Villain
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

            # [FIX] Очистка и Загадки
            riddle_answer = None
            if 'Ответ:' in event['text']:
                 match = re.search(r'\s*\(Ответ:\s*(.*?)\)', event['text'], re.IGNORECASE)
                 if match:
                     riddle_answer = match.group(1).strip()
            event['text'] = re.sub(r'\s*\(.*?\)', '', event['text']).strip()

            new_sig = s['signal']
            riddle_data = None
            msg_event = ""

            # === RPG LOGIC ===
            if event['type'] == 'trap':
                base_dmg = int(event['val'] * diff)
                dmg = max(5, base_dmg - stats['def'])
                # Aegis check
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

            # Riddle Handling with Single Word Answer Support
            if riddle_answer:
                full_answer = riddle_answer
                # Если ответ сложный (Игла и Тень), выбираем одно слово для кнопки
                if " и " in full_answer or " and " in full_answer.lower():
                    # Пытаемся разбить и взять первое значимое слово
                    parts = re.split(r' и | and ', full_answer, flags=re.IGNORECASE)
                    correct_button_text = parts[0].strip()
                else:
                    correct_button_text = full_answer

                q = event['text']

                # Создаем список опций (3 дистрактора + 1 правильный)
                options = random.sample(RIDDLE_DISTRACTORS, 3) + [correct_button_text]
                random.shuffle(options)

                # Передаем и полный ответ (для проверки, на всякий случай) и текст кнопки
                riddle_data = {
                    "question": q,
                    "correct": correct_button_text, # Логика бота будет сравнивать callback именно с этим
                    "full_answer": full_answer,
                    "options": options
                }
                msg_event = f"🧩 <b>ШИФР:</b>\n{q}"

            # Compass Logic
            compass_txt = ""
            if db.get_item_count(uid, 'compass') > 0:
                if db.decrease_durability(uid, 'compass'):
                    if event['type'] in ['loot', 'heal', 'locked_chest']:
                        res = "❇️ РЕЗОНАНС (Лутабельно)"
                    elif event['type'] == 'trap':
                        res = "⚠️ УГРОЗА (Ловушка)"
                    elif event['type'] == 'neutral':
                        res = "⬜️ ТИШИНА (Пусто)"
                    else:
                        res = "❓ НЕИЗВЕСТНО"
                    compass_txt = f"🧭 <b>КОМПАС:</b> {res}"
                else:
                    compass_txt = "💔 <b>КОМПАС СЛОМАЛСЯ.</b>"

            # Save state
            cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s WHERE uid=%s", (new_depth, new_sig, uid))
            if new_depth > u.get('max_depth', 0): db.update_user(uid, max_depth=new_depth)

            # Fetch buffer for HUD
            cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
            res = cur.fetchone()

    # Death Check
    if new_sig <= 0:
        db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
        return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м", None, u, 'death', 0

    # HUD Generation
    sig_bar = draw_bar(new_sig, 100, 8)
    interface = (
        f"🏝 <b>{biome['name']}</b> | <b>{new_depth}м</b>\n"
        f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"{msg_prefix}{msg_event}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎒 <b>{res['buffer_xp']} XP</b> | 🪙 <b>{res['buffer_coins']} BC</b>\n"
        f"💳 Баланс: <b>{u['xp']} XP</b>\n"
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
    # Need session signal
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
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (xp, coins, uid))

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
            # FAIL - Single Turn Damage
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
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                msg += "\n💀 <b>СИГНАЛ ПОТЕРЯН...</b>"

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
                db.admin_exec_query("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                msg += "\n💀 <b>СИГНАЛ ПОТЕРЯН...</b>"

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
