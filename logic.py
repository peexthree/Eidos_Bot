import random, time, re
from datetime import datetime
from config import *
import database as db

# =============================================================
# 1. СТАТИСТИКА И БОНУСЫ ШКОЛ
# =============================================================

def get_user_stats(uid):
    """Считает сумму статов (Шмот + Школа)"""
    stats = {'atk': 0, 'def': 0, 'luck': 0}
    
    # 1. Считаем от экипировки
    equipped = db.get_equipped_items(uid)
    for slot, item_id in equipped.items():
        item_stats = EQUIPMENT_DB.get(item_id, {})
        stats['atk'] += item_stats.get('atk', 0)
        stats['def'] += item_stats.get('def', 0)
        stats['luck'] += item_stats.get('luck', 0)
        
    # 2. Добавляем бонусы Школы (Фракции)
    u = db.get_user(uid)
    if u:
        # Разум = Танк (+Защита)
        if u['path'] == 'mind': 
            stats['def'] += 10
        # Техно = Скаут (+Удача/Крит)
        elif u['path'] == 'tech': 
            stats['luck'] += 10
        # Материя = Банкир (Бонус монет считается отдельно в луте)
        
    return stats, equipped

# =============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================

def get_path_multiplier(u):
    """Бонусы для 'мирных' действий (Синхрон/Сигнал)"""
    bonuses = {"xp_mult": 1.0, "cd_mult": 1.0}
    if u['path'] == 'money': bonuses['xp_mult'] = 1.2 # Быстрее качает уровень
    elif u['path'] == 'tech': bonuses['cd_mult'] = 0.9 # Быстрее откатываются скиллы
    return bonuses

def check_cooldown(uid, action_type):
    u = db.get_user(uid)
    if not u: return False, 0
    now = int(time.time())
    b = get_path_multiplier(u)
    
    if action_type == 'protocol':
        base_cd = COOLDOWN_ACCEL if u['accel_exp'] > now else COOLDOWN_BASE
        cd = base_cd * b['cd_mult']
        last = u['last_protocol_time']
    else: 
        cd = COOLDOWN_SIGNAL * b['cd_mult']
        last = u['last_signal_time']
        
    rem = int(cd - (now - last))
    return (rem <= 0), max(0, rem)

def draw_bar(current, total, length=10):
    percent = current / total if total > 0 else 0
    fill = int(length * percent)
    fill = max(0, min(length, fill))
    return "█" * fill + "░" * (length - fill)

# =============================================================
# 3. ЭКОНОМИКА (XP + REFERRAL)
# =============================================================

def process_xp_logic(uid, amount, source='general'):
    u = db.get_user(uid)
    if not u: return 0, False, []
    
    b = get_path_multiplier(u)
    
    # 1. Расчет XP (С учетом школы)
    final_amount = int(amount * b['xp_mult'])
    
    # 2. Стрик (Дисциплина)
    today = datetime.now().date()
    last = u['last_active']
    if isinstance(last, str): last = datetime.strptime(last, "%Y-%m-%d").date()
    streak = u['streak']
    
    if last < today:
        if (today - last).days == 1:
            streak += 1
        elif u['cryo'] > 0:
            db.update_user(uid, cryo=u['cryo']-1) # Крио спасает
        else:
            streak = 1 # Сброс
        db.update_user(uid, streak=streak, last_active=today)
        
    final_amount += (streak * 2) 
    
    # 3. Реферальные (10% Боссу)
    if u['referrer'] and source == 'raid':
        ref_bonus = int(final_amount * 0.1)
        if ref_bonus > 0:
            db.add_xp_to_user(u['referrer'], ref_bonus)
            db.add_referral_profit(u['referrer'], ref_bonus, 0)
            
    # 4. Level Up
    new_xp = u['xp'] + final_amount
    new_lvl = u['level']
    for lvl, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr:
            new_lvl = lvl
            break
            
    is_up = new_lvl > u['level']
    db.update_user(uid, xp=new_xp, level=new_lvl)
    
    return final_amount, is_up, check_achievements(uid)

def check_achievements(uid):
    u = db.get_user(uid)
    unlocked = []
    for aid, data in ACHIEVEMENTS_LIST.items():
        if not db.check_achievement_exists(uid, aid):
            if data['cond'](u):
                if db.grant_achievement(uid, aid, data['xp']):
                    unlocked.append(data['name'])
    return unlocked

# =============================================================
# 4. ДВИЖОК РЕЙДА v7.5 (С БОНУСАМИ ШКОЛ)
# =============================================================

def raid_step_logic(uid, answer=None):
    u = db.get_user(uid)
    stats, _ = get_user_stats(uid) 
    
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    # 1. Сессия
    cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
    s = cur.fetchone()
    
    if not s:
        # Вход платный (растет от уровня/глубины, пока фикс)
        if u['xp'] < RAID_COST:
            conn.close()
            return False, f"🪫 <b>НЕТ ЭНЕРГИИ</b>\nНужно {RAID_COST} XP.", None, u, 'neutral'
            
        db.update_user(uid, xp=u['xp'] - RAID_COST)
        cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time) VALUES (%s, %s, 100, %s)", (uid, u.get('max_depth', 0), int(time.time())))
        conn.commit()
        cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
        s = cur.fetchone()

    depth = s['depth']
    msg_prefix = ""

    # 2. Сундук (Действие)
    if answer == 'open_chest':
        if db.get_item_count(uid, 'master_key') > 0:
            db.use_item(uid, 'master_key')
            bonus_xp = 100 + (depth * 2)
            bonus_coins = 50 + int(depth/2)
            
            cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
            msg_prefix = f"🔓 <b>ВЗЛОМАН:</b> +{bonus_xp} XP | +{bonus_coins} BC\n\n"
        else:
            msg_prefix = "🔒 <b>НЕТ КЛЮЧА.</b>\n"

    # 3. Цена шага
    step_cost = RAID_STEP_COST + int(depth / 20)
    if u['xp'] < step_cost:
        conn.close()
        return False, f"🪫 <b>ИСТОЩЕНИЕ</b>\nНужно {step_cost} XP.", None, u, 'neutral'

    db.update_user(uid, xp=u['xp'] - step_cost)
    u['xp'] -= step_cost

    # 4. Биом
    biome = RAID_BIOMES["wasteland"]
    if 50 <= depth < 100: biome = RAID_BIOMES["archive"]
    elif depth >= 100: biome = RAID_BIOMES["darknet"]

    # 5. Событие
    new_depth = depth + 1
    
    if random.random() < 0.15:
        event = {'type': 'locked_chest', 'text': 'Зашифрованный контейнер.', 'val': 0}
    else:
        cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
        event = cur.fetchone()
        if not event: event = {'text': "Пустота...", 'type': 'neutral', 'val': 0}

    new_sig = s['signal']
    diff = biome['dmg_mod'] 
    riddle_data = None
    msg_event = ""

    # === [RPG LOGIC] ===
    
    if event['type'] == 'trap':
        base_dmg = int(event['val'] * diff)
        dmg = max(1, base_dmg - stats['def']) # DEF снижает урон
        
        # Эгида
        if db.get_item_count(uid, 'aegis') > 0 and (new_sig - dmg <= 0):
            db.use_item(uid, 'aegis')
            dmg = 0
            msg_prefix += "🛡 <b>ЭГИДА:</b> Смерть предотвращена!\n"
        
        new_sig = max(0, new_sig - dmg)
        flavor = random.choice(RAID_FLAVOR_TEXT['trap'])
        msg_event = f"💥 <b>УДАР:</b> {flavor}\n🔻 <b>-{dmg}% Сигнала</b> (Броня: {stats['def']})"
        
    elif event['type'] == 'loot':
        base_val = int(event['val'] * diff)
        
        # [BONUS] Школа Материи (+20% к монетам)
        coin_mult = 1.2 if u['path'] == 'money' else 1.0
        
        bonus_xp = int(base_val * (1 + stats['atk']/100))
        # Формула монет: Рандом * Удача * Школа
        coins = int(random.randint(5, 15) * (1 + stats['luck']/20) * coin_mult) 
        
        cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, coins, uid))
        
        flavor = random.choice(RAID_FLAVOR_TEXT['loot'])
        msg_event = f"💎 <b>НАХОДКА:</b> {flavor}\n✳️ +{bonus_xp} XP | 🪙 +{coins} BC"
        
        # Дроп предметов
        inv_size = db.get_inventory_size(uid)
        if inv_size < INVENTORY_LIMIT:
            dice = random.random()
            # Удача повышает шанс дропа
            drop_chance = 1.0 * (1 + stats['luck']/100) 
            
            for item, chance in LOOT_TABLE.items():
                if dice < (chance * drop_chance):
                    if 'biocoin' in item:
                        extra_c = 50 if 'bag' in item else 10
                        cur.execute("UPDATE raid_sessions SET buffer_coins=buffer_coins+%s WHERE uid=%s", (extra_c, uid))
                        msg_prefix += f"💰 <b>Мелочь: +{extra_c} BC</b>\n"
                    else:
                        if db.add_item(uid, item):
                            item_name = ITEMS_INFO.get(item, {}).get('name', item)
                            msg_prefix += f"🎁 <b>ЛУТ:</b> {item_name}!\n"
                    break
        else:
            msg_prefix += "🎒 <b>РЮКЗАК ПОЛОН!</b> Лут оставлен.\n"
            
    elif event['type'] == 'heal':
        new_sig = min(100, new_sig + 20)
        msg_event = "❤️ <b>ПРИВАЛ:</b> +20% Сигнала."
    elif event['type'] == 'locked_chest':
        msg_event = "🔒 <b>КОНТЕЙНЕР:</b> Нужен Ключ."
    else: 
        flavor = random.choice(RAID_FLAVOR_TEXT['empty'])
        msg_event = f"👣 {flavor}"

    # Загадки
    match = re.search(r'\s*\(Ответ:\s*(.*?)\)', event['text'], re.IGNORECASE)
    if match:
        correct = match.group(1).strip()
        q = event['text'].replace(match.group(0), "").strip()
        wrongs = ["Сбой", "Ошибка", "Пустота", "Фантом", "Шум"]
        options = random.sample(wrongs, 2) + [correct]
        random.shuffle(options)
        riddle_data = {"question": q, "correct": correct, "options": options}
        msg_event = f"🧩 <b>ЗАГАДКА:</b>\n{q}"

    # Компас
    compass_txt = ""
    if db.get_item_count(uid, 'compass') > 0:
        if db.decrease_durability(uid, 'compass'):
            pred = random.choice(['trap', 'loot', 'neutral'])
            compass_txt = f"🧭 <b>СЕНСОРЫ:</b> {pred.upper()} (LUCK {stats['luck']})"
        else:
            compass_txt = "💔 <b>КОМПАС:</b> Сломался."

    # Сохранение
    cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s WHERE uid=%s", (new_depth, new_sig, uid))
    if new_depth > u.get('max_depth', 0): 
        db.update_user(uid, max_depth=new_depth)
        if new_depth == 50: db.grant_achievement(uid, "depth_50", 500)
    
    cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
    res = cur.fetchone()
    conn.commit(); conn.close()

    # Смерть
    if new_sig <= 0:
        db.admin_exec_query(f"DELETE FROM raid_sessions WHERE uid={uid}")
        
        # Шанс поломки (20%)
        broken = None
        if random.random() < 0.2:
            broken = db.break_equipment_randomly(uid)
            
        death_msg = f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м\n❌ Весь лут потерян."
        if broken:
            death_msg += f"\n💔 <b>СЛОМАНО:</b> {ITEMS_INFO.get(broken, {}).get('name', 'Предмет')}."
            
        return False, death_msg, None, u, 'death'

    sig_bar = draw_bar(new_sig, 100, 10)
    keys = db.get_item_count(uid, 'master_key')
    bats = db.get_item_count(uid, 'battery')
    
    interface = (
        f"<b>{biome['name']}</b> | {new_depth}м\n"
        f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"{msg_prefix}{msg_event}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎒 <b>{res['buffer_xp']} XP</b> | 🪙 <b>{res['buffer_coins']} BC</b>\n"
        f"🔑 {keys} | 🔋 {bats}\n"
        f"⚔️ {stats['atk']} 🛡 {stats['def']} 🍀 {stats['luck']}\n"
        f"<i>{compass_txt}</i>"
    )
    return True, interface, riddle_data, u, event['type']

# =============================================================
# 5. КОНТЕНТ (STANDARD)
# =============================================================

def get_content_logic(c_type, path='general', level=1, has_decoder=False):
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    eff_lvl = level + 1 if has_decoder else level
    
    if c_type == 'signal':
        cur.execute("SELECT text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
    else:
        cur.execute("SELECT text FROM content WHERE type='protocol' AND (path=%s OR path='general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, eff_lvl))
    
    res = cur.fetchone()
    conn.close()
    return res

def get_level_progress_stats(u):
    xp, lvl = u['xp'], u['level']
    cur_t = LEVELS.get(lvl, 0)
    nxt_t = LEVELS.get(lvl+1, LEVELS.get(lvl, 999999))
    need = nxt_t - cur_t
    got = max(0, xp - cur_t)
    perc = int((got / needed) * 100) if need > 0 else 100
    return min(perc, 100), nxt_t - xp
