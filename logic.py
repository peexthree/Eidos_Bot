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

GAME_GUIDE_TEXTS = {
    'intro': (
        "<b>👋 ЧТО ТАКОЕ ЭЙДОС?</b>\n\n"
        "Это мир киберпанка, где ты — цифровой призрак. Твоя цель — эволюционировать из простой программы в Бога Машины.\n\n"
        "Ты начинаешь в <b>Трущобах (0м)</b>, но чем глубже ты спускаешься в <b>Нулевой Слой</b>, тем сильнее становишься.\n"
        "Собирай XP (Опыт) и BioCoins (Деньги), покупай импланты и оружие, чтобы выжить."
    ),
    'combat': (
        "<b>⚔️ КАК ДРАТЬСЯ?</b>\n\n"
        "В бою у тебя есть 2 пути:\n"
        "1. <b>АТАКА:</b> Наносишь урон. Если у тебя мало здоровья (&lt;20%), включается <b>🩸 АДРЕНАЛИН</b> (Урон x2).\n"
        "2. <b>ПОБЕГ:</b> Шанс 50%. Если не повезет — получишь удар в спину.\n\n"
        "<b>💀 КАЗНЬ:</b> Если у врага меньше 10% HP, ты убиваешь его мгновенно.\n"
        "<b>🛡 ЗАЩИТА:</b> Твоя броня снижает входящий урон. Чем больше DEF, тем меньше ты получаешь."
    ),
    'biomes': (
        "<b>🌍 ЗОНЫ И БИОМЫ</b>\n\n"
        "Мир разделен на уровни глубины:\n"
        "🏙 <b>0-50м: Трущобы.</b> Слабые враги, мало лута.\n"
        "🏭 <b>51-150м: Промзона.</b> Опасные дроиды. (Лута больше в 1.5 раза).\n"
        "🌃 <b>151-300м: Неон-Сити.</b> Владения корпораций. (Лута x2.5).\n"
        "🕸 <b>301-500м: Глубокая Сеть.</b> Вирусы и глитчи. (Лута x3.5).\n"
        "🌌 <b>501+м: ПУСТОТА.</b> Процедурный ад. (Лута x5.0+)."
    ),
    'stats': (
        "<b>📊 ХАРАКТЕРИСТИКИ</b>\n\n"
        "<b>⚔️ ATK (Атака):</b> Твой урон. Влияет на скорость убийства врагов.\n"
        "<b>🛡 DEF (Защита):</b> Снижает урон от врагов и ловушек.\n"
        "<b>🍀 LUCK (Удача):</b> Влияет на криты (x1.5 урона) и шанс найти <b>ЛЕГЕНДАРНЫЙ</b> предмет.\n"
        "<b>📡 SIGNAL (Здоровье):</b> Если упадет до 0 — ты теряешь весь лут за рейд."
    ),
    'factions': (
        "<b>🧬 ФРАКЦИИ (СИНЕРГИЯ)</b>\n\n"
        "Выбирай путь с умом:\n"
        "🤖 <b>TECH:</b> -10% урона в Промзоне (свои механизмы не бьют).\n"
        "🏦 <b>MONEY:</b> +20% золота в Неон-Сити (ты знаешь правила рынка).\n"
        "🧠 <b>MIND:</b> +15% уворота в Глубокой Сети (сила мысли против вирусов)."
    )
}

def get_biome_modifiers(depth):
    """Возвращает конфиг зоны на основе глубины."""
    if depth <= 50:
        return {"name": "🏙 Трущобы", "mult": 1.0, "desc": "Грязные улицы, полные отбросов."}
    elif depth <= 150:
        return {"name": "🏭 Промзона", "mult": 1.5, "desc": "Шум заводских механизмов."}
    elif depth <= 300:
        return {"name": "🌃 Неон-Сити", "mult": 2.5, "desc": "Яркие огни и тени корпораций."}
    elif depth <= 500:
        return {"name": "🕸 Глубокая Сеть", "mult": 3.5, "desc": "Абстрактные коридоры данных."}
    else:
        # Procedural
        hex_code = hex(depth)[2:].upper()
        adj = random.choice(["Мертвый", "Забытый", "Холодный", "Вечный", "Нулевой"])
        noun = random.choice(["Сектор", "Кластер", "Горизонт", "Предел", "Вакуум"])
        name = f"🌌 {adj} {noun} [{hex_code}]"
        scale = 5.0 + ((depth - 500) * 0.01)
        return {"name": name, "mult": scale, "desc": "Здесь кончается реальность."}

def generate_loot(depth, luck):
    """Генерирует тир лута на основе удачи."""
    roll = random.randint(0, 100) + (luck * 0.5)

    if roll >= 95:
        return {"prefix": "🟠 [ЛЕГЕНДА]", "mult": 5.0, "icon": "🟠"}
    elif roll >= 80:
        return {"prefix": "🟣 [ЭПИК]", "mult": 2.5, "icon": "🟣"}
    elif roll >= 50:
        return {"prefix": "🔵 [РЕДКИЙ]", "mult": 1.5, "icon": "🔵"}
    else:
        return {"prefix": "⚪️ [ОБЫЧНЫЙ]", "mult": 1.0, "icon": "⚪️"}

def parse_riddle(text):
    """
    Парсит текст загадки, извлекая ответ из скобок.
    Поддерживает форматы:
    1. (Ответ: Ответ) или (Протокол: Ответ) - строгий поиск.
    2. (Ответ) - если текст содержит 'ЗАГАДКА', ищет в конце строки.
    Возвращает (answer, clean_text). Если ответ не найден, answer=None.
    """
    if not text: return None, text

    # 1. Строгий поиск с префиксом
    match = re.search(r'\s*\((?:Ответ|Протокол):\s*(.*?)\)', text, re.IGNORECASE)

    # 2. Мягкий поиск (fallback), если это явно загадка
    if not match and "ЗАГАДКА" in text.upper():
         # Ищем содержимое скобок в самом конце строки
         match = re.search(r'\s*\(([^()]+)\)\s*$', text)

    if match:
         answer = match.group(1).strip()
         start, end = match.span()
         clean_text = (text[:start] + text[end:]).strip()
         return answer, clean_text

    return None, text

def get_full_archive_chunks(uid):
    protocols = db.get_archived_protocols(uid)
    if not protocols:
        return ["💾 <b>АРХИВ ПРОТОКОЛОВ</b>\n\nПусто."]

    chunks = []
    current_chunk = "💾 <b>ПОЛНЫЙ АРХИВ ПРОТОКОЛОВ</b>\n\n"

    for i, p in enumerate(protocols, 1):
        entry = f"💠 <b>ЗАПИСЬ #{i}</b>\n{p['text']}\n\n"
        if len(current_chunk) + len(entry) > 4000:
            chunks.append(current_chunk)
            current_chunk = entry
        else:
            current_chunk += entry

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

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

def generate_raid_report(uid, s, success=False):
    # Time
    duration = int(time.time() - s['start_time'])
    mins = duration // 60
    secs = duration % 60

    kills = s.get('kills', 0)
    riddles = s.get('riddles_solved', 0)
    depth = s.get('depth', 0)
    profit_xp = s.get('buffer_xp', 0)
    profit_coins = s.get('buffer_coins', 0)

    # Items
    buffer_items_str = s.get('buffer_items', '')
    items_list_str = ""
    if buffer_items_str:
        items = buffer_items_str.split(',')
        item_counts = {}
        for i in items:
            if i:
                name = ITEMS_INFO.get(i, {}).get('name', i)
                item_counts[name] = item_counts.get(name, 0) + 1

        items_list_str = ", ".join([f"{k} x{v}" for k,v in item_counts.items()])
    else:
        items_list_str = "Нет"

    if success:
        return (
            f"✅ <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"ПОЛУЧЕНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Предметы: {items_list_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 СТАТИСТИКА:\n"
            f"• Глубина: {depth}\n"
            f"• Убийств: {kills}\n"
            f"• Загадок: {riddles}\n"
            f"⏱ Время: {mins}м {secs}с"
        )
    else:
        return (
            f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\n"
            f"УТЕРЯНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Расходники: {items_list_str}\n"
            f"⏱ Время: {mins}м {secs}с"
        )

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

            correct_full = s['current_riddle_answer']

            # Split correct answer logic
            parts = re.split(r'\s+(?:или|и)\s+', correct_full, flags=re.IGNORECASE)
            valid_answers = [p.strip().lower() for p in parts if p.strip()]

            user_ans_lower = user_answer.lower()
            is_correct = False
            for va in valid_answers:
                if va.startswith(user_ans_lower):
                     is_correct = True
                     break

            # Reset riddle
            cur.execute("UPDATE raid_sessions SET current_riddle_answer=NULL WHERE uid=%s", (uid,))

            if is_correct:
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

def scale_enemy_stats(villain, user_stats, u):
    """
    Dynamically adjusts enemy stats to be challenging but winnable based on user power.
    Target: Fight lasts ~8-12 turns. Player survives ~6-8 hits unhealed.
    """
    # 1. Calculate Player Power
    p_atk = max(5, user_stats['atk']) # Floor at 5
    p_def = user_stats['def']

    # 2. Target Enemy HP (Player Atk * 8..12)
    target_hp = p_atk * 10

    # 3. Target Enemy Atk (Player HP / 6..8) + Mitigation
    # Player HP is Signal (100). Mitigation = Def / (Def + 100)
    mitigation = p_def / (p_def + 100)
    target_dmg_per_hit = 15 # 100 / 7 approx
    # Raw Dmg needed to deal 15 dmg after mitigation:
    # X * (1 - mit) = 15 => X = 15 / (1 - mit)
    target_atk = int(target_dmg_per_hit / (1.0 - mitigation))

    # 4. Scale existing villain stats (preserve flavor if possible)
    # If villain is WAY too strong, nerf it.
    if villain['hp'] > target_hp * 2:
        villain['hp'] = int(target_hp * 1.5) # Still tough, but not 100x

    if villain['atk'] > target_atk * 2:
        villain['atk'] = int(target_atk * 1.5)

    # 5. Buff if too weak (e.g. Level 30 player vs Level 1 mob)
    if villain['hp'] < target_hp * 0.5:
        villain['hp'] = int(target_hp * 0.8)

    if villain['atk'] < target_atk * 0.5:
        villain['atk'] = int(target_atk * 0.8)

    return villain

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
            
            # --- [MODULE 2] GLITCH MECHANIC (5%) ---
            if random.random() < 0.05 and not s.get('current_enemy_id'):
                glitch_roll = random.random()
                glitch_text = ""

                if glitch_roll < 0.4: # Positive
                    bonus = int(depth * 10) + 100
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s WHERE uid=%s", (bonus, uid))
                    glitch_text = f"✨ <b>СБОЙ РЕАЛЬНОСТИ (ПОЗИТИВ):</b> Вы нашли потерянный фрагмент памяти. +{bonus} XP."

                elif glitch_roll < 0.7: # Heal
                    cur.execute("UPDATE raid_sessions SET signal=LEAST(100, signal+50) WHERE uid=%s", (uid,))
                    glitch_text = f"❤️ <b>СБОЙ РЕАЛЬНОСТИ (ЛЕЧЕНИЕ):</b> Сигнал внезапно восстановился. +50%."

                else: # Negative
                    loss = int(depth * 5)
                    cur.execute("UPDATE raid_sessions SET buffer_coins=GREATEST(0, buffer_coins-%s) WHERE uid=%s", (loss, uid))
                    glitch_text = f"⚠️ <b>ГЛИТЧ (ОШИБКА):</b> Часть данных повреждена. -{loss} BC из буфера."

                # We just return this as an event
                return True, f"🌀 <b>АНОМАЛИЯ</b>\n{glitch_text}", None, u, 'glitch', 0

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
                has_spike = db.get_item_count(uid, 'data_spike', cursor=cur) > 0

                if not (has_abyssal or has_master or has_spike):
                    return False, "🔒 <b>НУЖЕН КЛЮЧ</b>\nКупите [КЛЮЧ], [ДАТА-ШИП] или найдите [КЛЮЧ БЕЗДНЫ].", None, u, 'locked_chest', 0

                key_used = None
                
                # Priority: Abyssal -> Master -> Spike
                if has_abyssal: key_used = 'abyssal_key'
                elif has_master: key_used = 'master_key'
                else: key_used = 'data_spike'

                # Spike Logic (80% chance)
                spike_success = True
                if key_used == 'data_spike':
                    if random.random() > 0.8:
                        spike_success = False

                # Consume item
                db.use_item(uid, key_used, 1, cursor=cur)

                if not spike_success:
                    conn.commit()
                    return False, "❌ <b>ВЗЛОМ ПРОВАЛЕН</b>\nДата-шип сломался.", None, u, 'locked_chest', 0

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

            # 2.5 ДЕЙСТВИЕ: ИСПОЛЬЗОВАНИЕ РАСХОДНИКОВ
            if answer == 'use_battery':
                 if db.get_item_count(uid, 'battery', cursor=cur) > 0:
                      if db.use_item(uid, 'battery', cursor=cur):
                           new_signal = min(100, s['signal'] + 30)
                           cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_signal, uid))
                           conn.commit()
                           s['signal'] = new_signal
                           alert_txt = f"🔋 ЭНЕРГИЯ ВОССТАНОВЛЕНА\nСигнал: {new_signal}%"
                           return True, "ЗАРЯД ИСПОЛЬЗОВАН", {'alert': alert_txt}, u, 'battery_used', 0
                 return False, "❌ НЕТ БАТАРЕИ", None, u, 'battery_error', 0

            if answer == 'use_stimulator':
                 if db.get_item_count(uid, 'neural_stimulator', cursor=cur) > 0:
                      if db.use_item(uid, 'neural_stimulator', cursor=cur):
                           new_signal = min(100, s['signal'] + 60)
                           cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_signal, uid))
                           conn.commit()
                           s['signal'] = new_signal
                           alert_txt = f"💉 СТИМУЛЯТОР ВВЕДЕН\nСигнал: {new_signal}%"
                           return True, "СТИМУЛЯТОР ИСПОЛЬЗОВАН", {'alert': alert_txt}, u, 'battery_used', 0
                 return False, "❌ НЕТ СТИМУЛЯТОРА", None, u, 'battery_error', 0

            # 3. ЦЕНА ШАГА
            step_cost = RAID_STEP_COST + (depth // 25)
            if not is_new and answer != 'open_chest' and answer != 'use_battery':
                if u['xp'] < step_cost:
                    return False, f"🪫 <b>НЕТ ЭНЕРГИИ</b>\nНужно {step_cost} XP.", None, u, 'neutral', 0
                
                cur.execute("UPDATE users SET xp = xp - %s WHERE uid=%s", (step_cost, uid))
                u['xp'] -= step_cost

            # 4. ГЕНЕРАЦИЯ СОБЫТИЯ
            # SCALING BIOMES IMPLEMENTATION
            biome_data = get_biome_modifiers(depth)
            diff = biome_data.get('mult', 1.0)
            new_depth = depth + 1 if not is_new else depth

            # Логика типа события
            current_type_code = s.get('next_event_type', 'random')
            if current_type_code == 'random' or not current_type_code:
                first_next = generate_random_event_type()
                current_type_code = first_next

            event = None
            msg_prefix = ""

            # БОЙ
            if current_type_code == 'combat':
                # Mob Scaling (Module 5)
                # Cap mob level at User Level + 1 (was +5) to prevent impossible mechanical fights for low levels deep diving
                mob_level = min(30, (depth // 20) + 1, u['level'] + 1)
                villain = db.get_random_villain(mob_level, cursor=cur)

                if villain:
                    # Dynamic Balance (New Function)
                    villain = scale_enemy_stats(villain, stats, u)

                    # Dynamic Stats Scaling for Deep Levels
                    if depth > 100:
                        # Reduced scaling from 1% to 0.5% per meter
                        scale_mult = 1.0 + ((depth - 100) * 0.005)
                        villain['hp'] = int(villain['hp'] * scale_mult)
                        villain['atk'] = int(villain['atk'] * scale_mult)
                        villain['xp_reward'] = int(villain['xp_reward'] * scale_mult)
                        villain['coin_reward'] = int(villain['coin_reward'] * scale_mult)

                    # ELITE MOBS IMPLEMENTATION
                    is_elite = False
                    if random.random() < 0.10: # 10% Chance
                        is_elite = True
                        villain['hp'] *= 2
                        villain['name'] = f"☠️ [ЭЛИТА] {villain['name']}"

                    cur.execute("UPDATE raid_sessions SET current_enemy_id=%s, current_enemy_hp=%s, is_elite=%s WHERE uid=%s",
                               (villain['id'], villain['hp'], is_elite, uid))
                    
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
            riddle_answer, event['text'] = parse_riddle(event['text'])

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
                # TIERED LOOT IMPLEMENTATION
                loot_info = generate_loot(depth, stats['luck'])
                bonus_xp = int(event['val'] * diff * loot_info['mult'])
                coins = int(random.randint(5, 20) * loot_info['mult'])

                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, coins, uid))
                msg_event = f"{loot_info['prefix']} <b>НАХОДКА:</b> {event['text']}\n+{bonus_xp} XP | +{coins} BC"

            elif event['type'] == 'heal':
                new_sig = min(100, new_sig + 25)
                msg_event = f"❤️ <b>АПТЕЧКА:</b> {event['text']}\n+25% Сигнала"

            else:
                msg_event = f"👣 {event['text']}"

            # ЗАГАДКА
            if riddle_answer:
                # Split options
                parts = re.split(r'\s+(?:или|и)\s+', riddle_answer, flags=re.IGNORECASE)
                valid_answers = [p.strip() for p in parts if p.strip()]
                button_answer = valid_answers[0] if valid_answers else riddle_answer

                options = random.sample(RIDDLE_DISTRACTORS, 2) + [button_answer]
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

            # ЛОР / СОВЕТЫ
            advice_text = ""
            # Only show advice if not in combat and not dead, 40% chance
            if current_type_code != 'combat' and new_sig > 0 and random.random() < 0.4:
                adv_level = 1
                if new_depth >= 100: adv_level = 3
                elif new_depth >= 50: adv_level = 2

                advice = db.get_random_raid_advice(adv_level, cursor=cur)
                if advice:
                    advice_text = f"\n\n🧩 <i>Совет: {advice}</i>"

            interface = (
                f"🏝 <b>{biome_data['name']}</b> | <b>{new_depth}м</b>\n"
                f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
                f"━━━━━━━━━━━━━━\n"
                f"{msg_prefix}{msg_event}{advice_text}\n"
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

    return False, "⚠️ СИСТЕМНАЯ ОШИБКА", None, u, 'error', 0

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

def format_inventory(uid, category='all'):
    items = db.get_inventory(uid)
    equipped = db.get_equipped_items(uid)
    u = db.get_user(uid)
    inv_limit = INVENTORY_LIMIT

    from config import EQUIPMENT_DB

    txt = f"🎒 <b>РЮКЗАК [{len(items)}/{inv_limit}]</b>\n\n"

    if category == 'all' or category == 'equip':
        if equipped:
            txt += "<b>🛡 ЭКИПИРОВАНО:</b>\n"
            for slot, iid in equipped.items():
                name = ITEMS_INFO.get(iid, {}).get('name', iid)
                txt += f"• {name}\n"
            txt += "\n"

    # Filter
    filtered = []
    if category == 'all': filtered = items
    elif category == 'equip': filtered = [i for i in items if i['item_id'] in EQUIPMENT_DB]
    elif category == 'consumable': filtered = [i for i in items if i['item_id'] not in EQUIPMENT_DB]

    if filtered:
        txt += "<b>📦 ПРЕДМЕТЫ:</b>\n"
        for i in filtered:
            iid = i['item_id']
            name = ITEMS_INFO.get(iid, {}).get('name', iid)
            qty = i['quantity']
            desc = ITEMS_INFO.get(iid, {}).get('desc', '')[:30] + "..."

            qty_str = f" (x{qty})" if qty > 1 else ""
            txt += f"• <b>{name}</b>{qty_str}\n  <i>{desc}</i>\n"
    else:
        txt += "<i>Пусто...</i>\n"

    txt += f"\n♻️ <b>СТОИМОСТЬ РАЗБОРА:</b> 10%"
    return txt

# =============================================================
# ⚔️ БОЕВАЯ СИСТЕМА И КОНТЕНТ
# =============================================================

def get_content_logic(c_type, path='general', level=1, decoder=False):
    # FORCE RANDOM PATH FOR PROTOCOLS (Module 1)
    if c_type == 'protocol':
        path = 'all'

    # 1. Try DB first
    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        query = "SELECT * FROM content WHERE type=%s AND level <= %s"
        params = [c_type, level]

        if path != 'all':
            if path != 'general':
                query += " AND (path=%s OR path='general')"
                params.append(path)
            else:
                query += " AND path='general'"
        # If 'all', we don't filter by path, so we get random path

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

    if path != 'all':
        if path == 'general':
            filtered = [c for c in filtered if c['path'] == 'general']
        else:
            filtered = [c for c in filtered if c['path'] == path or c['path'] == 'general']

    if filtered:
        choice = random.choice(filtered).copy()
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

    # ELITE STATS BUFF
    if s.get('is_elite'):
        villain['hp'] *= 2
        villain['atk'] = int(villain['atk'] * 1.5)
        villain['xp_reward'] *= 3
        villain['coin_reward'] *= 3
        villain['name'] = f"☠️ [ЭЛИТА] {villain['name']}"

    msg = ""
    res_type = 'next_turn'

    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
        full_s = cur.fetchone()

    if not full_s: return 'error', "Сессия не найдена."

    current_signal = full_s['signal']
    biome_data = get_biome_modifiers(full_s.get('depth', 0))

    if action == 'attack':
        # ADRENALINE
        dmg_mult = 1.0
        if current_signal < 20:
            dmg_mult = 2.0
            msg += "🩸 <b>АДРЕНАЛИН:</b> Урон удвоен!\n"

        is_crit = random.random() < (stats['luck'] / 100.0)
        base_dmg = int(stats['atk'] * (1.5 if is_crit else 1.0) * dmg_mult)

        # RNG VARIANCE (Module 2)
        variance = random.uniform(0.8, 1.2)
        dmg = int(base_dmg * variance)
        dmg = max(1, dmg)

        # EXECUTION
        if enemy_hp < (villain['hp'] * 0.1):
            dmg = 999999
            msg += "💀 <b>КАЗНЬ:</b> Вы жестоко добиваете врага.\n"

        new_enemy_hp = enemy_hp - dmg

        crit_msg = " (КРИТ!)" if is_crit else ""

        # Detailed Logs
        if dmg < 999999: # Don't log normal hit on execution
            if variance > 1.1:
                msg += f"⚔️ <b>КРИТИЧЕСКИЙ УДАР!</b> Вы замахнулись на {base_dmg}, но нанесли {dmg}!{crit_msg}\n"
            elif variance < 0.9:
                msg += f"⚔️ <b>СКОЛЬЗЯЩИЙ УДАР...</b> Вы замахнулись на {base_dmg}, но нанесли всего {dmg}.{crit_msg}\n"
            else:
                msg += f"⚔️ <b>АТАКА:</b> Вы нанесли {dmg} урона{crit_msg}.\n"

        if new_enemy_hp <= 0:
            xp_gain = villain.get('xp_reward', 0)
            coin_gain = villain.get('coin_reward', 0)

            # FACTION SYNERGY (MONEY)
            if u['path'] == 'money':
                if "Неон-Сити" in biome_data['name']:
                    coin_gain = int(coin_gain * 1.2)
                    msg += "🏦 <b>ЗНАНИЕ РЫНКА:</b> +20% монет в Неон-Сити.\n"

            # Legacy tech penalty
            if u['path'] == 'tech': xp_gain = int(xp_gain * 0.9)

            db.clear_raid_enemy(uid)
            with db.db_cursor() as cur:
                cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s, kills = kills + 1 WHERE uid=%s",
                            (xp_gain, coin_gain, uid))

            return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен.\nПолучено: +{xp_gain} XP | +{coin_gain} BC"

        else:
            db.update_raid_enemy(uid, enemy_id, new_enemy_hp)
            msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"

            # ENEMY ATTACK LOGIC
            raw_enemy_dmg = villain['atk']

            # FACTION SYNERGY (TECH)
            if u['path'] == 'tech' and "Промзона" in biome_data['name']:
                 raw_enemy_dmg *= 0.9
                 msg += "🤖 <b>СВОЙ-ЧУЖОЙ:</b> -10% урона от механизмов.\n"

            # MITIGATION FORMULA
            # Def / (Def + 100)
            mitigation = stats['def'] / (stats['def'] + 100)
            enemy_dmg = int(raw_enemy_dmg * (1.0 - mitigation))

            # CHIP DAMAGE (Min 5%)
            min_dmg = int(raw_enemy_dmg * 0.05)
            enemy_dmg = max(min_dmg, enemy_dmg)

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

    elif action == 'use_emp':
        if db.get_item_count(uid, 'emp_grenade') > 0:
            db.use_item(uid, 'emp_grenade', 1)
            dmg = 150
            new_enemy_hp = enemy_hp - dmg
            msg += f"💣 <b>EMP ЗАРЯД:</b> Нанесено 150 чистого урона!\n"

            if new_enemy_hp <= 0:
                xp_gain = villain.get('xp_reward', 0)
                coin_gain = villain.get('coin_reward', 0)
                db.clear_raid_enemy(uid)
                with db.db_cursor() as cur:
                    cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s, kills = kills + 1 WHERE uid=%s",
                                (xp_gain, coin_gain, uid))
                return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен взрывом.\nПолучено: +{xp_gain} XP | +{coin_gain} BC"
            else:
                db.update_raid_enemy(uid, enemy_id, new_enemy_hp)
                msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"
        else:
             return 'error', "Нет EMP гранаты."

    elif action == 'use_stealth':
        if db.get_item_count(uid, 'stealth_spray') > 0:
            db.use_item(uid, 'stealth_spray', 1)
            db.clear_raid_enemy(uid)
            return 'escaped', "👻 <b>СТЕЛС:</b> Вы растворились в тумане. 100% побег."
        else:
             return 'error', "Нет спрея."

    elif action == 'use_wiper':
        if db.get_item_count(uid, 'memory_wiper') > 0:
            db.use_item(uid, 'memory_wiper', 1)
            db.clear_raid_enemy(uid)
            # Wiper resets aggro, effectively ending combat but maybe keeping position?
            # Same as escaped basically but different flavor.
            return 'escaped', "🧹 <b>СТИРАТЕЛЬ:</b> Память врага очищена. Он забыл о вас."
        else:
             return 'error', "Нет стирателя памяти."

    elif action == 'run':
        # FACTION SYNERGY (MIND) - Dodge in Deep Net/Void
        bonus_dodge = 0
        if u['path'] == 'mind' and ("Глубокая Сеть" in biome_data['name'] or "Пустота" in biome_data['name']):
            bonus_dodge = 0.15

        chance = 0.5 + (stats['luck'] / 200.0) + bonus_dodge

        if random.random() < chance:
             db.clear_raid_enemy(uid)
             extra_msg = " (Сила Мысли)" if bonus_dodge > 0 else ""
             return 'escaped', f"🏃 <b>ПОБЕГ:</b> Вы успешно скрылись в тенях.{extra_msg}"
        else:
             msg += "🚫 <b>ПОБЕГ НЕ УДАЛСЯ.</b> Враг атакует!\n"

    # --- SHARED ENEMY TURN LOGIC (Run Fail or EMP survival) ---
    if action in ['run', 'use_emp']: # If we are here, it means we failed run or used EMP and enemy is alive
             raw_enemy_dmg = villain['atk']

             # Apply Tech Synergy here too? Logic implies damage reduction works always.
             if u['path'] == 'tech' and "Промзона" in biome_data['name']:
                 raw_enemy_dmg *= 0.9

             mitigation = stats['def'] / (stats['def'] + 100)
             enemy_dmg = int(raw_enemy_dmg * (1.0 - mitigation))
             min_dmg = int(raw_enemy_dmg * 0.05)
             enemy_dmg = max(min_dmg, enemy_dmg)

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

def perform_hack(attacker_uid):
    # 1. Get Attacker Stats
    stats, atk_u = get_user_stats(attacker_uid)
    if not atk_u: return "❌ Ошибка авторизации."

    # Cost
    HACK_COST_XP = 50
    if atk_u['xp'] < HACK_COST_XP:
        return f"🪫 Не хватает энергии. Нужно {HACK_COST_XP} XP."

    # 2. Get Random Target
    target_uid = db.get_random_user_for_hack(attacker_uid)
    if not target_uid: return "❌ Некого взламывать."

    def_stats, def_u = get_user_stats(target_uid)
    if not def_u: return "❌ Цель потеряна."

    # 3. Formula
    # (Int + Luck) vs (Defense + Level*2)
    # Using ATK as Int equivalent for hacking context + Luck
    atk_score = stats['atk'] + stats['luck'] + random.randint(1, 20)
    def_score = def_stats['def'] + (def_u['level'] * 2) + random.randint(1, 20)

    # Check for Firewall (Target Item)
    has_firewall = db.get_item_count(target_uid, 'firewall') > 0

    msg = ""

    if has_firewall:
        # Consume Firewall
        db.use_item(target_uid, 'firewall', 1)
        # Pay Cost
        db.update_user(attacker_uid, xp=max(0, atk_u['xp'] - HACK_COST_XP))
        msg = f"🛡 <b>ВЗЛОМ ПРЕДОТВРАЩЕН!</b>\nУ @{def_u['username']} сработал Файрвол."

    elif atk_score > def_score:
        # Steal 5-10% coins
        steal_perc = random.uniform(0.05, 0.10)
        steal_amount = int(def_u['biocoin'] * steal_perc)
        steal_amount = min(steal_amount, 5000) # Cap
        if steal_amount < 0: steal_amount = 0

        # Transaction
        db.update_user(attacker_uid, biocoin=atk_u['biocoin'] + steal_amount, xp=atk_u['xp'] - HACK_COST_XP)
        db.update_user(target_uid, biocoin=max(0, def_u['biocoin'] - steal_amount))

        msg = (f"🔓 <b>ВЗЛОМ УСПЕШЕН!</b>\n"
               f"Жертва: @{def_u['username']}\n"
               f"Украдено: {steal_amount} BC")
    else:
        # Penalty: Lose XP
        loss_xp = 100
        db.update_user(attacker_uid, xp=max(0, atk_u['xp'] - HACK_COST_XP - loss_xp))
        msg = (f"🚫 <b>ВЗЛОМ ПРОВАЛЕН!</b>\n"
               f"Жертва: @{def_u['username']}\n"
               f"Защита оказалась сильнее.\n"
               f"Штраф: -{loss_xp} XP")

    return msg
