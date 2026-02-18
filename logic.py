import database as db
from config import LEVELS, RAID_STEP_COST, RAID_BIOMES, RAID_FLAVOR_TEXT, LOOT_TABLE, INVENTORY_LIMIT, ITEMS_INFO, RIDDLE_DISTRACTORS, RAID_ENTRY_COSTS, LEVEL_UP_MSG
import random
import time
import re
from datetime import datetime
from content_presets import CONTENT_DATA

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

def generate_hud(uid, u, session_data, cursor=None):
    # Fetch inventory details
    inv_items = db.get_inventory(uid, cursor=cursor)
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

    # Items
    buffer_items_str = s.get('buffer_items', '')
    lost_items_list = ""
    if buffer_items_str:
        items = buffer_items_str.split(',')
        item_counts = {}
        for i in items:
            if i:
                name = ITEMS_INFO.get(i, {}).get('name', i)
                item_counts[name] = item_counts.get(name, 0) + 1

        lost_items_list = ", ".join([f"{k} x{v}" for k,v in item_counts.items()])
    else:
        lost_items_list = "Нет"

    return (
        f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\n"
        f"УТЕРЯНО:\n"
        f"• Данные (XP): {profit_xp}\n"
        f"• Энергоблоки (Coins): {profit_coins}\n"
        f"• Расходники: {lost_items_list}\n"
        f"⏱ Время: {mins}м {secs}с"
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

            if correct.lower().startswith(user_answer.lower()):
                # Correct
                bonus_xp = 100 + (s['depth'] * 2)
                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, riddles_solved=riddles_solved+1 WHERE uid=%s", (bonus_xp, uid))
                # Chance for drop
                msg = f"✅ <b>ВЕРНО!</b>\nПолучено: +{bonus_xp} XP."
                if random.random() < 0.3:
                    # Add to buffer
                    cur.execute("UPDATE raid_sessions SET buffer_items = buffer_items || ',battery' WHERE uid=%s", (uid,))
                    msg += "\n🎁 Награда: Батарея (В буфер)"
                return True, msg
            else:
                # Wrong - Damage
                dmg = 15
                new_sig = max(0, s['signal'] - dmg)
                cur.execute("UPDATE raid_sessions SET signal=%s WHERE uid=%s", (new_sig, uid))
                msg = f"❌ <b>ОШИБКА!</b>\nСистема защиты активирована.\n🔻 -{dmg}% Сигнала."
                return False, msg

def generate_random_event_type():
    r = random.random()
    if r < 0.15: return 'combat'
    if r < 0.30: return 'locked_chest'
    return 'random'

def process_raid_step(uid, answer=None):
    stats, u = get_user_stats(uid)
    if not u: return False, "User not found", None, None, 'error', 0
    
    # ИСПОЛЬЗУЕМ ОДНО СОЕДИНЕНИЕ (чтобы избежать зависания бота)
    with db.db_session() as conn:
        with conn.cursor(cursor_factory=db.RealDictCursor) as cur:
            # 1. ПОЛУЧАЕМ СЕССИЮ
            cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
            s = cur.fetchone()

            is_new = False
            
            # --- ЛОГИКА ВХОДА ---
            if not s:
                today = datetime.now().date()
                last = u.get('last_raid_date')
                
                # Сброс ежедневных лимитов (ПРЯМОЙ SQL)
                if str(last) != str(today):
                    cur.execute("UPDATE users SET raid_count_today=0, last_raid_date=%s WHERE uid=%s", (today, uid))
                    u['raid_count_today'] = 0

                # Проверка баланса
                cost = get_raid_entry_cost(uid)
                if u['xp'] < cost:
                    return False, f"🪫 <b>НЕДОСТАТОЧНО ЭНЕРГИИ</b>\nВход: {cost} XP\nУ вас: {u['xp']} XP", None, u, 'neutral', 0

                # Списание XP и вход (ПРЯМОЙ SQL)
                new_xp = u['xp'] - cost
                cur.execute("UPDATE users SET xp=%s, raid_count_today=raid_count_today+1, last_raid_date=%s WHERE uid=%s",
                           (new_xp, today, uid))
                u['xp'] = new_xp # Обновляем локально

                # Создаем сессию
                depth = u.get('max_depth', 0)
                first_next = generate_random_event_type()
                cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time, kills, riddles_solved, next_event_type, buffer_items, buffer_xp, buffer_coins) VALUES (%s, %s, 100, %s, 0, 0, %s, '', 0, 0)", 
                           (uid, depth, int(time.time()), first_next))
                
                conn.commit() # ВАЖНО: Сохраняем вход
                
                cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
                s = cur.fetchone()
                is_new = True

            # --- ДАЛЬШЕ ЛОГИКА ШАГА ---
            depth = s['depth']
            
            # ПРОВЕРКА БОЯ
            if s.get('current_enemy_id'):
                vid = s['current_enemy_id']
                v_hp = s.get('current_enemy_hp', 10)
                villain = db.get_villain_by_id(vid, cursor=cur)
                if villain:
                    return True, format_combat_screen(villain, v_hp, s['signal'], stats, s), None, u, 'combat', 0
                else:
                    cur.execute("UPDATE raid_sessions SET current_enemy_id=NULL WHERE uid=%s", (uid,))
                    conn.commit()

            # 2. ДЕЙСТВИЕ: ОТКРЫТИЕ СУНДУКА (ИСПРАВЛЕНО)
            if answer == 'open_chest':
                has_abyssal = db.get_item_count(uid, 'abyssal_key', cursor=cur) > 0
                has_master = db.get_item_count(uid, 'master_key', cursor=cur) > 0

                if not (has_abyssal or has_master):
                    return False, "🔒 <b>НУЖЕН КЛЮЧ</b>\nКупите [КЛЮЧ] или найдите [КЛЮЧ БЕЗДНЫ].", None, u, 'locked_chest', 0

                key_used = 'abyssal_key' if has_abyssal else 'master_key'
                
                # Удаляем ключ прямым запросом (чтобы не блокировать БД)
                cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE uid=%s AND item_id=%s", (uid, key_used))
                cur.execute("DELETE FROM inventory WHERE uid=%s AND item_id=%s AND quantity <= 0", (uid, key_used))

                bonus_xp = (300 + (depth * 5)) if key_used == 'abyssal_key' else (150 + (depth * 2))
                bonus_coins = (100 + (depth * 2)) if key_used == 'abyssal_key' else (50 + depth)

                # Дроп предмета
                loot_item_txt = ""
                if random.random() < 0.30: # 30% шанс на предмет
                     drops = ['battery', 'compass', 'rusty_knife']
                     l_item = random.choice(drops)
                     cur.execute("UPDATE raid_sessions SET buffer_items = buffer_items || ',' || %s WHERE uid=%s", (l_item, uid))
                     loot_item_txt = f"\n📦 Предмет: {ITEMS_INFO.get(l_item, {}).get('name')}"

                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
                conn.commit() 

                alert_txt = f"🔓 УСПЕХ!\nXP: +{bonus_xp}\nCoins: +{bonus_coins}{loot_item_txt}"
                
                # Возвращаем тип 'loot_opened' чтобы обновить кнопки
                return True, "СУНДУК ОТКРЫТ", {'alert': alert_txt}, u, 'loot_opened', 0

            # 3. ЦЕНА ШАГА
            step_cost = RAID_STEP_COST + (depth // 25)
            if not is_new and answer != 'open_chest':
                if u['xp'] < step_cost:
                    return False, f"🪫 <b>НЕТ ЭНЕРГИИ</b>\nНужно {step_cost} XP.", None, u, 'neutral', 0
                
                cur.execute("UPDATE users SET xp = xp - %s WHERE uid=%s", (step_cost, uid))
                u['xp'] -= step_cost

            # 4. ГЕНЕРАЦИЯ СОБЫТИЯ
            biome = RAID_BIOMES["wasteland"]
            if 50 <= depth < 100: biome = RAID_BIOMES["archive"]
            elif depth >= 100: biome = RAID_BIOMES["darknet"]

            new_depth = depth + 1 if not is_new else depth
            diff = biome['dmg_mod']

            # Логика типа события
            current_type_code = s.get('next_event_type', 'random')
            if current_type_code == 'random' or not current_type_code:
                first_next = generate_random_event_type()
                current_type_code = first_next

            event = None
            msg_prefix = ""

            # БОЙ
            if current_type_code == 'combat':
                villain = db.get_random_villain(depth // 20 + 1, cursor=cur)
                if villain:
                    cur.execute("UPDATE raid_sessions SET current_enemy_id=%s, current_enemy_hp=%s WHERE uid=%s", 
                               (villain['id'], villain['hp'], uid))
                    
                    next_preview = generate_random_event_type()
                    cur.execute("UPDATE raid_sessions SET next_event_type=%s WHERE uid=%s", (next_preview, uid))
                    conn.commit()
                    return True, format_combat_screen(villain, villain['hp'], s['signal'], stats, s), None, u, 'combat', 0

            # СУНДУК
            elif current_type_code == 'locked_chest':
                event = {'type': 'locked_chest', 'text': 'Запертый контейнер.', 'val': 0}

            # СЛУЧАЙНОЕ
            else:
                cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
                event = cur.fetchone()
                if not event: event = {'text': "Пустота...", 'type': 'neutral', 'val': 0}

            # Парсинг загадки
            riddle_answer = None
            if 'Ответ:' in event['text']:
                 match = re.search(r'\s*\(Ответ:\s*(.*?)\)', event['text'], re.IGNORECASE)
                 if match:
                     riddle_answer = match.group(1).strip()
                     event['text'] = re.sub(r'\s*\(.*?\)', '', event['text']).strip()

            new_sig = s['signal']
            msg_event = ""
            riddle_data = None

            # ЭФФЕКТЫ СОБЫТИЙ
            if event['type'] == 'trap':
                base_dmg = int(event['val'] * diff)
                dmg = max(5, base_dmg - stats['def'])
                
                # Проверка Эгиды (Прямой SQL для скорости)
                has_aegis = False
                cur.execute("SELECT quantity FROM inventory WHERE uid=%s AND item_id='aegis'", (uid,))
                ae_res = cur.fetchone()
                if ae_res and ae_res['quantity'] > 0 and (new_sig - dmg <= 0):
                    cur.execute("UPDATE inventory SET quantity = quantity - 1 WHERE uid=%s AND item_id='aegis'", (uid,))
                    cur.execute("DELETE FROM inventory WHERE uid=%s AND item_id='aegis' AND quantity <= 0", (uid,))
                    dmg = 0
                    msg_prefix += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"

                new_sig = max(0, new_sig - dmg)
                msg_event = f"💥 <b>ЛОВУШКА:</b> {event['text']}\n🔻 <b>-{dmg}% Сигнала</b>"

            elif event['type'] == 'loot':
                bonus_xp = int(event['val'] * diff)
                coins = int(random.randint(5, 20))
                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, coins, uid))
                msg_event = f"💎 <b>НАХОДКА:</b> {event['text']}\n+{bonus_xp} XP | +{coins} BC"

            elif event['type'] == 'heal':
                new_sig = min(100, new_sig + 25)
                msg_event = f"❤️ <b>АПТЕЧКА:</b> {event['text']}\n+25% Сигнала"

            else:
                msg_event = f"👣 {event['text']}"

            # ЗАГАДКА
            if riddle_answer:
                options = random.sample(RIDDLE_DISTRACTORS, 2) + [riddle_answer]
                random.shuffle(options)
                riddle_data = {"question": event['text'], "correct": riddle_answer, "options": options}
                msg_event = f"🧩 <b>ЗАГАДКА:</b>\n{event['text']}"
                cur.execute("UPDATE raid_sessions SET current_riddle_answer=%s WHERE uid=%s", (riddle_answer, uid))
                event['type'] = 'riddle'

            # ПОДГОТОВКА СЛЕДУЮЩЕГО ШАГА
            next_preview = generate_random_event_type()
            cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, next_event_type=%s WHERE uid=%s", (new_depth, new_sig, next_preview, uid))
            
            if new_depth > u.get('max_depth', 0): 
                cur.execute("UPDATE users SET max_depth=%s WHERE uid=%s", (new_depth, uid))

            conn.commit() # ФИКСИРУЕМ ШАГ

            # СБОРКА UI
            cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
            res = cur.fetchone()
            
            sig_bar = draw_bar(new_sig, 100, 8)
            
            # КОМПАС (БУДУЩЕЕ)
            comp_txt = ""
            # Проверяем наличие компаса (безопасно)
            cur.execute("SELECT quantity FROM inventory WHERE uid=%s AND item_id='compass'", (uid,))
            comp_q = cur.fetchone()
            if comp_q and comp_q['quantity'] > 0:
                 # Тратим заряд компаса
                 cur.execute("UPDATE inventory SET durability = durability - 1 WHERE uid=%s AND item_id='compass'", (uid,))
                 # Если сломался (условно, если есть механика поломки), но пока просто показываем
                 comp_map = {'combat': '⚔️ ВРАГ', 'trap': '💥 ЛОВУШКА', 'loot': '💎 ЛУТ', 'random': '❔ НЕИЗВЕСТНО', 'locked_chest': '🔒 СУНДУК'}
                 comp_res = comp_map.get(next_preview, '❔')
                 comp_txt = f"🧭 <b>КОМПАС (Дальше):</b> {comp_res}"
                 conn.commit()

            interface = (
                f"🏝 <b>{biome['name']}</b> | <b>{new_depth}м</b>\n"
                f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
                f"━━━━━━━━━━━━━━\n"
                f"{msg_prefix}{msg_event}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🎒 +{res['buffer_xp']} XP | 🪙 +{res['buffer_coins']} BC\n"
                f"{generate_hud(uid, u, res, cursor=cur)}\n"
                f"<i>{comp_txt}</i>"
            )
            
            next_step_cost = RAID_STEP_COST + (new_depth // 25)
            
            # СМЕРТЬ
            if new_sig <= 0:
                 cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))
                 conn.commit()
                 return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м\nРесурсы утеряны.", None, u, 'death', 0

            return True, interface, riddle_data, u, event['type'], next_step_cost

# =============================================================
# 👤 ПРОФИЛЬ И СИСТЕМЫ
# =============================================================

def get_level_progress_stats(u):
    if not u: return 0, 0
    level = u.get("level", 1)
    xp = u.get("xp", 0)

    target = LEVELS.get(level, 999999)
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

    txt += f"\n♻️ <b>СТОИМОСТЬ РАЗБОРА:</b> 10%"
    return txt

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
        if l in CONTENT_DATA:
            pool.extend(CONTENT_DATA[l])

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
            xp_gain = villain.get('xp_reward', 0)
            coin_gain = villain.get('coin_reward', 0)

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
