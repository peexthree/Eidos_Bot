import random, time, re
from datetime import datetime
from config import *
import database as db

# =============================================================
# 1. СТАТИСТИКА И БОНУСЫ ШКОЛ [RPG]
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
        if u['path'] == 'mind': stats['def'] += 10
        elif u['path'] == 'tech': stats['luck'] += 10
        
    return stats, equipped

# =============================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================

def get_path_multiplier(u):
    bonuses = {"xp_mult": 1.0, "cd_mult": 1.0}
    if u['path'] == 'money': bonuses['xp_mult'] = 1.2
    elif u['path'] == 'tech': bonuses['cd_mult'] = 0.9
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
    if total <= 0: return "░" * length
    percent = current / total
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
    final_amount = int(amount * b['xp_mult'])
    
    today = datetime.now().date()
    last = u['last_active']
    if isinstance(last, str): last = datetime.strptime(last, "%Y-%m-%d").date()
    streak = u['streak']
    
    if last < today:
        if (today - last).days == 1: streak += 1
        elif u['cryo'] > 0: db.update_user(uid, cryo=u['cryo']-1)
        else: streak = 1
        db.update_user(uid, streak=streak, last_active=today)
        
    final_amount += (streak * 2) 
    
    # Реферальные (10% Боссу)
    if u['referrer'] and source == 'raid':
        ref_bonus = int(final_amount * 0.1)
        if ref_bonus > 0:
            db.add_xp_to_user(int(u['referrer']), ref_bonus)
            db.add_referral_profit(int(u['referrer']), ref_bonus, 0)
            
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
    if not u: return []
    for aid, data in ACHIEVEMENTS_LIST.items():
        if not db.check_achievement_exists(uid, aid):
            if data['cond'](u):
                if db.grant_achievement(uid, aid, data['xp']):
                    unlocked.append(data['name'])
    return unlocked

# =============================================================
# 4. ДВИЖОК РЕЙДА v8.0 (GOD EDITION)
# =============================================================

def raid_step_logic(uid, answer=None):
    """
    answer: None, 'open_chest', 'attack', 'run'
    """
    u = db.get_user(uid)
    stats, _ = get_user_stats(uid) 
    
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    # 1. СЕССИЯ: Проверка и Починка кнопки «Начать»
    cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
    s = cur.fetchone()
    
    is_new_session = False
    if not s:
        if u['xp'] < RAID_COST:
            conn.close()
            return False, f"🪫 <b>НЕДОСТАТОЧНО ЭНЕРГИИ</b>\nВход: {RAID_COST} XP.", None, u, 'neutral'
            
        db.update_user(uid, xp=u['xp'] - RAID_COST)
        u['xp'] -= RAID_COST
        cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time) VALUES (%s, %s, 100, %s)", 
                    (uid, u.get('max_depth', 0), 100, int(time.time())))
        conn.commit()
        # [FIX] Сразу читаем новую сессию, чтобы кнопка «Начать» сработала мгновенно
        cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
        s = cur.fetchone()
        is_new_session = True

    depth = s['depth']
    msg_prefix = ""

    # 2. ДЕЙСТВИЯ (Сундук)
    if answer == 'open_chest':
        if db.get_item_count(uid, 'master_key') > 0:
            db.use_item(uid, 'master_key')
            bonus_xp = 150 + (depth * 3)
            bonus_coins = 60 + depth
            cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s WHERE uid = %s", (bonus_xp, bonus_coins, uid))
            msg_prefix = f"🔓 <b>ВЗЛОМАН:</b> +{bonus_xp} XP | +{bonus_coins} BC\n\n"
        else:
            msg_prefix = "🔒 <b>НУЖЕН КЛЮЧ!</b>\n\n"

    # 3. ЦЕНА ШАГА
    step_cost = RAID_STEP_COST + (depth // 25)
    if u['xp'] < step_cost:
        conn.close()
        return False, f"🪫 <b>ИСТОЩЕНИЕ</b>\nНужно {step_cost} XP.", None, u, 'neutral'

    db.update_user(uid, xp=u['xp'] - step_cost)
    u['xp'] -= step_cost

    # 4. БИОМ
    biome = RAID_BIOMES["wasteland"]
    if 50 <= depth < 100: biome = RAID_BIOMES["archive"]
    elif depth >= 100: biome = RAID_BIOMES["darknet"]
    
    new_depth = depth + 1
    diff = biome['dmg_mod'] 

    # 5. ГЕНЕРАЦИЯ СОБЫТИЯ
    if not is_new_session and random.random() < 0.12:
        event = {'type': 'locked_chest', 'text': 'Запертый контейнер данных.', 'val': 0}
    else:
        cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
        event = cur.fetchone()
        if not event: event = {'text': "Пустота серверов...", 'type': 'neutral', 'val': 0}

    new_sig = s['signal']
    riddle_data = None
    msg_event = ""

    # === [RPG LOGIC] ===
    if event['type'] == 'trap':
        base_dmg = int(event['val'] * diff)
        dmg = max(5, base_dmg - stats['def']) # Защита работает!
        
        # Эгида (спасение)
        if db.get_item_count(uid, 'aegis') > 0 and (new_sig - dmg <= 0):
            db.use_item(uid, 'aegis')
            dmg = 0
            msg_prefix += "🛡 <b>ЭГИДА:</b> Смерть предотвращена!\n"
        
        new_sig = max(0, new_sig - dmg)
        flavor = random.choice(RAID_FLAVOR_TEXT['trap'])
        msg_event = f"💥 <b>УГРОЗА:</b> {flavor}\n🔻 <b>-{dmg}% Сигнала</b> (DEF: {stats['def']})"
        
    elif event['type'] == 'loot':
        # [FIX] Бонус Школы Материи (+20% BioCoins)
        coin_mult = 1.2 if u['path'] == 'money' else 1.0
        
        bonus_xp = int(event['val'] * diff * (1 + stats['atk']/100))
        coins = int(random.randint(10, 25) * (1 + stats['luck']/20) * coin_mult) 
        
        cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s WHERE uid = %s", (bonus_xp, coins, uid))
        
        flavor = random.choice(RAID_FLAVOR_TEXT['loot'])
        msg_event = f"💎 <b>НАХОДКА:</b> {flavor}\n✳️ +{bonus_xp} XP | 🪙 +{coins} BC"
        
        # Дроп предметов
        if db.get_inventory_size(uid) < INVENTORY_LIMIT:
            dice = random.random()
            drop_chance = 1.0 + (stats['luck'] / 100)
            for item, chance in LOOT_TABLE.items():
                if dice < (chance * drop_chance):
                    if 'biocoin' in item:
                        val = 50 if 'bag' in item else 15
                        cur.execute("UPDATE raid_sessions SET buffer_coins = buffer_coins + %s WHERE uid = %s", (val, uid))
                        msg_prefix += f"💰 Мелочь: +{val} BC\n"
                    else:
                        if db.add_item(uid, item):
                            msg_prefix += f"🎁 <b>ЛУТ:</b> {ITEMS_INFO.get(item, {}).get('name', item)}\n"
                    break
        else:
            msg_prefix += "🎒 <b>СУМКА ПОЛНА!</b> Лут потерян.\n"
            
    elif event['type'] == 'heal':
        new_sig = min(100, new_sig + 25)
        msg_event = "❤️ <b>ВОССТАНОВЛЕНИЕ:</b> +25% Сигнала."
    else: 
        flavor = random.choice(RAID_FLAVOR_TEXT['empty'])
        msg_event = f"👣 {flavor}"

    # Загадки
    match = re.search(r'\s*\(Ответ:\s*(.*?)\)', event['text'], re.IGNORECASE)
    if match:
        correct = match.group(1).strip()
        q = event['text'].replace(match.group(0), "").strip()
        wrongs = ["Сбой", "Ошибка", "Пустота", "Глитч", "Шум"]
        options = random.sample(wrongs, 2) + [correct]
        random.shuffle(options)
        riddle_data = {"question": q, "correct": correct, "options": options}
        msg_event = f"🧩 <b>ЗАГАДКА:</b>\n{q}"

    # [FIX] Честный Компас (видит текущую опасность)
    compass_txt = ""
    if db.get_item_count(uid, 'compass') > 0:
        if db.decrease_durability(uid, 'compass'):
            comp_res = "БЕЗОПАСНО" if event['type'] in ['loot', 'heal', 'neutral'] else "⚠️ УГРОЗА"
            compass_txt = f"🧭 <b>СКАНЕР:</b> {comp_res} (LUCK: {stats['luck']})"
        else:
            compass_txt = "💔 <b>КОМПАС СГОРЕЛ.</b>"

    # 6. ФИНАЛИЗАЦИЯ
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
        # Шанс 25% сломать шмотку при смерти
        broken = db.break_equipment_randomly(uid) if random.random() < 0.25 else None
        death_msg = f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина {new_depth}м стала пределом.\n❌ Лут стерт."
        if broken: death_msg += f"\n💔 <b>РАЗРУШЕНО:</b> {ITEMS_INFO.get(broken, {}).get('name', 'Предмет')}."
        return False, death_msg, None, u, 'death'

    # HUD (Интерфейс)
    sig_bar = draw_bar(new_sig, 100, 8)
    interface = (
        f"🏝 <b>{biome['name']}</b> | <b>{new_depth}м</b>\n"
        f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
        f"━━━━━━━━━━━━━━\n"
        f"{msg_prefix}{msg_event}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎒 <b>{res['buffer_xp']} XP</b> | 🪙 <b>{res['buffer_coins']} BC</b>\n"
        f"⚔️ {stats['atk']} 🛡 {stats['def']} 🍀 {stats['luck']}\n"
        f"<i>{compass_txt}</i>"
    )
    return True, interface, riddle_data, u, event['type']

def get_content_logic(c_type, path='general', level=1, has_decoder=False):
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    eff_lvl = level + 1 if has_decoder else level
    if c_type == 'signal': cur.execute("SELECT text FROM content WHERE type='signal' ORDER BY RANDOM() LIMIT 1")
    else: cur.execute("SELECT text FROM content WHERE type='protocol' AND (path=%s OR path='general') AND level <= %s ORDER BY RANDOM() LIMIT 1", (path, eff_lvl))
    res = cur.fetchone()
    conn.close()
    return res

def get_level_progress_stats(u):
    xp, lvl = u['xp'], u['level']
    cur_t = LEVELS.get(lvl, 0)
    nxt_t = LEVELS.get(lvl+1, 999999)
    need = nxt_t - cur_t
    got = max(0, xp - cur_t)
    perc = int((got / need) * 100) if need > 0 else 100
    return min(perc, 100), max(0, nxt_t - xp)
