import random, time
from datetime import datetime
from config import *
import database as db

# =============================================================
# 1. СИСТЕМА ФРАКЦИОННЫХ БОНУСОВ (ШКОЛЫ)
# =============================================================

def get_path_multiplier(u):
    bonuses = {"xp_mult": 1.0, "sig_prot": 1.0, "cd_mult": 1.0}
    if u['path'] == 'money': bonuses['xp_mult'] = 1.2
    elif u['path'] == 'mind': bonuses['sig_prot'] = 0.8
    elif u['path'] == 'tech': bonuses['cd_mult'] = 0.9
    return bonuses

# =============================================================
# 2. ТАЙМЕРЫ И ДЕШИФРАЦИЯ (АНТИ-СПАМ)
# =============================================================

def check_cooldown(uid, action_type):
    u = db.get_user(uid)
    if not u: return False, 0
    
    now = int(time.time())
    b = get_path_multiplier(u)
    
    if action_type == 'protocol':
        base_cd = COOLDOWN_ACCEL if u['accel_exp'] > now else COOLDOWN_BASE
        cd = base_cd * b['cd_mult']
        last = u['last_protocol_time']
    else: # signal
        cd = COOLDOWN_SIGNAL * b['cd_mult']
        last = u['last_signal_time']
        
    rem = int(cd - (now - last))
    return (rem <= 0), max(0, rem)

# =============================================================
# 3. ЭКОНОМИКА СОЗНАНИЯ (XP, СТРИКИ, УРОВНИ)
# =============================================================

def process_xp_logic(uid, amount, source='general'):
    u = db.get_user(uid)
    if not u: return 0, False, []
    
    b = get_path_multiplier(u)
    today = datetime.now().date()
    last_active = u['last_active']
    
    # Обработка формата даты (защита от дурака)
    if isinstance(last_active, str):
        try:
            last_active = datetime.strptime(last_active, "%Y-%m-%d").date()
        except ValueError:
            last_active = today # Если формат кривой, считаем что сегодня
    
    # Логика Стрика и Крио-защиты
    new_streak = u['streak']
    if last_active < today:
        if (today - last_active).days == 1:
            new_streak += 1
        else:
            if u['cryo'] > 0:
                db.update_user(uid, cryo=u['cryo'] - 1)
                # Стрик сохраняется благодаря Крио
            else:
                new_streak = 1
        db.update_user(uid, streak=new_streak, last_active=today)

    final_amount = amount * b['xp_mult'] if source == 'raid' else amount
    total_gain = int(final_amount + (new_streak * 2))
    
    new_xp = u['xp'] + total_gain
    new_lvl = u['level']
    
    # Проверка повышения уровня
    # (Предполагается, что LEVELS импортирован из config)
    for lvl, thr in sorted(LEVELS.items(), reverse=True):
        if new_xp >= thr:
            new_lvl = lvl
            break
            
    is_lvl_up = new_lvl > u['level']
    db.update_user(uid, xp=new_xp, level=new_lvl)
    
    # Проверка ачивок
    new_achs = check_achievements(uid)
    
    return total_gain, is_lvl_up, new_achs

# =============================================================
# 4. АВТОМАТИКА ДОСТИЖЕНИЙ
# =============================================================

def check_achievements(uid):
    u = db.get_user(uid)
    newly_unlocked = []
    # (Предполагается, что ACHIEVEMENTS_LIST импортирован из config)
    for ach_id, data in ACHIEVEMENTS_LIST.items():
        if not db.check_achievement_exists(uid, ach_id):
            if data['cond'](u):
                if db.grant_achievement(uid, ach_id, data['xp']):
                    newly_unlocked.append(data['name'])
    return newly_unlocked

# =============================================================
# 5. НУЛЕВОЙ СЛОЙ: ГЛУБОКАЯ ЛОГИКА (РЕЙД)
# =============================================================

def raid_step_logic(uid):
    u = db.get_user(uid)
    conn = db.get_db_connection()
    # Используем RealDictCursor из модуля db (убедись, что он там есть)
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
    s = cur.fetchone()
    if not s: 
        conn.close()
        return False, "Сбой связи", None

    b = get_path_multiplier(u)
    depth = s['depth'] + 1
    difficulty_mod = 1 + (depth // 50) * 0.2 
    
    # Выбор события
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    event = cur.fetchone()
    if not event:
        # Фоллбэк, если база пустая
        event = {'text': "Пустота...", 'type': 'neutral', 'val': 0}

    # Выбор подсказки
    cur.execute("SELECT text FROM raid_hints ORDER BY RANDOM() LIMIT 1")
    hint = cur.fetchone()
    hint_text = hint['text'] if hint else "Нет данных"

    riddle = None
    # Логика загадок (парсинг ответа)
    if "(Ответ:" in event['text']:
        raw_text = event['text'].split("(Ответ:")
        event_text = raw_text[0].strip()
        correct = raw_text[1].split(")")[0].strip()
        
        # Генерация вариантов ответа
        # (SYNC_CATEGORIES должен быть в config)
        category = next((c for c, t in SYNC_CATEGORIES.items() if any(item.lower() in correct.lower() for item in t)), "tech")
        wrong = random.sample([t for t in SYNC_CATEGORIES[category] if t.lower() not in correct.lower()], 2)
        opts = wrong + [correct]
        random.shuffle(opts)
        riddle = {"correct": correct, "options": opts}
    else:
        event_text = event['text']

    # Расчет урона и лута
    base_dmg = event['val'] if event['type'] == 'trap' else random.randint(3, 8)
    final_dmg = int(base_dmg * difficulty_mod * b['sig_prot'])
    
    new_sig = max(0, s['signal'] - (final_dmg if event['type'] != 'heal' else -20))
    # Хил (отрицательный урон) не может поднять сигнал выше 100
    if event['type'] == 'heal': new_sig = min(100, new_sig)
    
    new_buff = s['buffer_xp'] + (int(event['val'] * b['xp_mult']) if event['type'] == 'loot' else 0)

    # GAME OVER
    if new_sig <= 0:
        cur.execute("DELETE FROM raid_sessions WHERE uid = %s", (uid,))
        conn.commit(); conn.close()
        return False, "💀 <b>СИГНАЛ РАЗОРВАН.</b>\nТы слишком глубоко зашел. Весь буфер уничтожен.", None

    cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, buffer_xp=%s WHERE uid=%s", (depth, new_sig, new_buff, uid))
    if depth > u['max_depth']: db.update_user(uid, max_depth=depth)
    
    conn.commit(); conn.close()

    status = "🟢" if new_sig > 60 else "🟡" if new_sig > 30 else "🔴"
    
    # HTML ФОРМАТИРОВАНИЕ
    msg = (f"⚓️ <b>ГЛУБИНА: {depth} м</b>\n\n"
           f"{event_text}\n"
           f"\n🧭 <b>КОМПАС:</b> <i>{hint_text}</i>"
           f"\n\n🎒 <b>В МЕШКЕ:</b> {new_buff} XP\n"
           f"📡 <b>СИГНАЛ:</b> {status} {new_sig}%")
           
    return True, msg, riddle

# =============================================================
# 6. НОВОЕ: КОНТЕНТНЫЙ ДВИЖЕК (ДЛЯ СИНХРОНА И СИГНАЛА)
# =============================================================

def get_content_logic(c_type, path='general', level=1, has_decoder=False):
    """
    Получает знания из базы. 
    Если у игрока есть Дешифратор, он может получить контент на 1 уровень выше.
    """
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    effective_level = level + 1 if has_decoder else level
    
    if c_type == 'signal':
        cur.execute("SELECT id, text FROM raid_content WHERE type = 'loot' ORDER BY RANDOM() LIMIT 1")
    else:
        # Ищем протоколы, подходящие по школе и уровню
        cur.execute("""SELECT id, text FROM content 
                       WHERE type = 'protocol' 
                       AND (path = %s OR path = 'general') 
                       AND level <= %s 
                       ORDER BY RANDOM() LIMIT 1""", (path, effective_level))
    
    res = cur.fetchone()
    conn.close()
    return res

# =============================================================
# 7. НОВОЕ: СТАТИСТИКА ПРОГРЕССА (ДЛЯ ПРОФИЛЯ)
# =============================================================

def get_level_progress_stats(u):
    """Рассчитывает % опыта до следующего уровня"""
    xp = u['xp']
    lvl = u['level']
    
    current_threshold = LEVELS.get(lvl, 0)
    # Защита от кейса, когда уровень максимальный (нет следующего ключа)
    next_threshold = LEVELS.get(lvl + 1, current_threshold)
    
    if next_threshold == current_threshold:
        return 100, 0 # Максимальный уровень
    
    needed = next_threshold - current_threshold
    got = xp - current_threshold
    
    # Защита от деления на ноль, если пороги равны (хотя это баг конфига)
    if needed == 0: return 100, 0
        
    percent = int((got / needed) * 100)
    
    return min(max(percent, 0), 100), (next_threshold - xp)
