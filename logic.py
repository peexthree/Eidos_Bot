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
# 5. НУЛЕВОЙ СЛОЙ: ГЛУБОКАЯ ЛОГИКА (РЕЙД V2)
# =============================================================

def raid_step_logic(uid, answer=None):
    """
    answer: 
      - None (обычный шаг или начало)
      - 'skip' (пропуск загадки с уроном)
      - <строка> (вариант ответа игрока)
    """
    u = db.get_user(uid)
    conn = db.get_db_connection()
    cur = conn.cursor(cursor_factory=db.RealDictCursor)
    
    cur.execute("SELECT * FROM raid_sessions WHERE uid = %s", (uid,))
    s = cur.fetchone()
    
    if not s: 
        conn.close()
        return False, "Сбой сессии. Перезайди.", None, u

    # --- ФАЗА 1: ПРОВЕРКА ОТВЕТА (ЕСЛИ БЫЛ) ---
    msg_prefix = ""
    damage = 0
    xp_penalty = 0
    
    if answer:
        # Получаем данные о текущем событии (нужно было хранить state, но для простоты
        # мы считаем, что answer приходит только если была загадка)
        pass 
        # В этой архитектуре сложно валидировать ответ без хранения 'current_riddle' в БД.
        # Упростим: Если answer пришел, мы проверяем его на лету в bot.py или здесь?
        # ДАВАЙ ПЕРЕПИШЕМ ЛОГИКУ В BOT.PY ЧТОБЫ ОНА ПЕРЕДАВАЛА РЕЗУЛЬТАТ ПРОВЕРКИ.
        # Но чтобы не ломать структуру, сделаем так:
        # Логика шага просто генерирует НОВОЕ событие.
        # А обработка правильности ответа будет ВНЕ этой функции (в bot.py перед вызовом step).
    
    # Списание цены шага (Настоящий XP)
    if u['xp'] < RAID_STEP_COST:
        conn.close()
        return False, "🪫 <b>НЕДОСТАТОЧНО ЭНЕРГИИ</b>\nТы слишком слаб, чтобы идти дальше.", None, u

    db.update_user(uid, xp=u['xp'] - RAID_STEP_COST)
    u['xp'] -= RAID_STEP_COST # Обновляем локально для отображения

    # --- ФАЗА 2: ГЕНЕРАЦИЯ НОВОГО СОБЫТИЯ ---
    depth = s['depth'] + 1
    difficulty_mod = 1 + (depth // 50) * 0.2 
    
    # Выбор события
    cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
    event = cur.fetchone()
    if not event: event = {'text': "Пустота...", 'type': 'neutral', 'val': 0}

    # Выбор подсказки
    cur.execute("SELECT text FROM raid_hints ORDER BY RANDOM() LIMIT 1")
    hint = cur.fetchone()
    hint_text = hint['text'] if hint else "..."

    # Обработка Загадок
    riddle_data = None
    clean_text = event['text']
    
    if "(Ответ:" in event['text']:
        # ПАРСИНГ: Разделяем текст вопроса и ответ
        parts = event['text'].split("(Ответ:")
        clean_text = parts[0].strip() # Текст без ответа
        correct = parts[1].split(")")[0].strip()
        
        # Генерация вариантов
        category = "tech" # Заглушка, можно улучшить поиск категории
        # Генерируем 2 неправильных варианта из базы (или хардкод для надежности)
        wrongs = ["Ошибка", "Сбой", "Пустота", "Иллюзия", "Симулякр"]
        options = random.sample(wrongs, 2) + [correct]
        random.shuffle(options)
        
        riddle_data = {
            "question": clean_text,
            "correct": correct,
            "options": options
        }
        # Урон при ошибке считаем тут же
        event['type'] = 'riddle' 
        event['val'] = 15 # Урон за ошибку

    # Расчет (если это не загадка, урон наносится сразу)
    # Если загадка - урон нанесется только если юзер ошибется (в след. шаге)
    
    base_dmg = event['val']
    if event['type'] == 'trap':
        final_dmg = int(base_dmg * difficulty_mod)
        new_sig = max(0, s['signal'] - final_dmg)
        msg_prefix += f"💥 ЛОВУШКА! -{final_dmg}% Сигнала.\n"
    elif event['type'] == 'heal':
        new_sig = min(100, s['signal'] + 20)
        msg_prefix += "❤️ ВОССТАНОВЛЕНИЕ.\n"
    elif event['type'] == 'loot':
        bonus = int(event['val'])
        # Лут идет в буфер
        cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s WHERE uid = %s", (bonus, uid))
        msg_prefix += f"💎 НАЙДЕНЫ ДАННЫЕ: +{bonus} XP (в мешок).\n"
        new_sig = s['signal']
    else: # neutral / riddle
        new_sig = s['signal']

    # Сохраняем прогресс
    cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s WHERE uid=%s", (depth, new_sig, uid))
    if depth > u['max_depth']: db.update_user(uid, max_depth=depth)
    
    # Читаем актуальный буфер
    cur.execute("SELECT buffer_xp FROM raid_sessions WHERE uid = %s", (uid,))
    current_buffer = cur.fetchone()['buffer_xp']
    conn.commit(); conn.close()

    if new_sig <= 0:
        db.admin_exec_query(f"DELETE FROM raid_sessions WHERE uid = {uid}")
        return False, "💀 <b>СИГНАЛ ПОТЕРЯН</b>\nТвое сознание растворилось в шуме.", None, u

    status_icon = "🟢" if new_sig > 60 else "🟡" if new_sig > 30 else "🔴"
    
    # ФОРМИРУЕМ UI
    msg = (f"⚓️ <b>ГЛУБИНА: {depth} м</b>\n"
           f"{msg_prefix}\n"
           f"{clean_text}\n"
           f"🧭 <i>{hint_text}</i>\n\n"
           f"🎒 Мешок: <b>{current_buffer} XP</b>\n"
           f"📡 Сигнал: {status_icon} <b>{new_sig}%</b>\n"
           f"🔋 Твой заряд: <b>{u['xp']} XP</b> (Шаг: -{RAID_STEP_COST})")

    return True, msg, riddle_data, u

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
