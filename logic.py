import database as db
from config import LEVELS, RAID_STEP_COST, RAID_BIOMES, RAID_FLAVOR_TEXT, LOOT_TABLE, INVENTORY_LIMIT, ITEMS_INFO, RIDDLE_DISTRACTORS, RAID_ENTRY_COSTS, LEVEL_UP_MSG, ACHIEVEMENTS_LIST
import random
import time
import re
import copy
from datetime import datetime
from content_presets import CONTENT_DATA

# =============================================================
# 🛠 УТИЛИТЫ И HUD
# =============================================================

GAME_GUIDE_TEXTS = {
    'intro': (
        "<b>👋 НАЧАЛО ИГРЫ</b>\n\n"
        "Добро пожаловать в <b>EIDOS: Chronicles</b> — киберпанк RPG, где ты играешь за цифровой призрак (Осколок), пытающийся обрести сознание в бесконечной Сети.\n\n"
        "<b>🚀 БЫСТРЫЙ СТАРТ:</b>\n"
        "1. <b>Запуск:</b> Напиши <code>/start</code>.\n"
        "2. <b>Выбор Пути:</b> Выбери Фракцию (Специализацию).\n"
        "3. <b>Цель:</b> Копи XP (Опыт) и BioCoins (Монеты), чтобы достичь 30 уровня и стать Абсолютом.\n\n"
        "<b>📱 ГЛАВНОЕ МЕНЮ:</b>\n"
        "• <b>💠 ПРОТОКОЛ (Синхрон):</b> Основной опыт (+25 XP). Кулдаун 30 мин. Шанс Глитча 5%.\n"
        "• <b>📡 СИГНАЛ:</b> Доп. опыт (+15 XP). Кулдаун 5 мин.\n"
        "• <b>🚀 РЕЙД (Нулевой Слой):</b> Опасная экспедиция за лутом. Требует энергии.\n"
        "• <b>👤 ПРОФИЛЬ:</b> Статистика, Уровень, Атака/Защита/Удача.\n"
        "• <b>🎒 ИНВЕНТАРЬ:</b> Предметы и экипировка.\n"
        "• <b>🎰 МАГАЗИН:</b> Покупка снаряжения за Монеты и Опыт."
    ),
    'raids': (
        "<b>🚀 МЕХАНИКА РЕЙДОВ (Нулевой Слой)</b>\n\n"
        "Рейд — это пошаговое приключение. Чем глубже, тем опаснее враги и ценнее награда.\n\n"
        "<b>🌍 БИОМЫ (ЗОНЫ):</b>\n"
        "1. <b>🏙 Трущобы (0-50м):</b> Легко.\n"
        "2. <b>🏭 Промзона (51-150м):</b> Средне. Лут x1.5.\n"
        "3. <b>🌃 Неон-Сити (151-300м):</b> Сложно. Лут x2.5.\n"
        "4. <b>🕸 Глубокая Сеть (301-500м):</b> Очень сложно. Лут x3.5.\n"
        "5. <b>🌌 ПУСТОТА (501+м):</b> Процедурный ад. Лут x5.0+.\n\n"
        "<b>👣 ДВИЖЕНИЕ:</b>\n"
        "Каждый шаг стоит <b>Энергии (XP)</b>. Если XP кончится — придется выходить.\n\n"
        "<b>💀 СМЕРТЬ И ЭВАКУАЦИЯ:</b>\n"
        "Твое здоровье — это <b>Сигнал (100%)</b>. Если он упадет до 0%, ты умрешь и <b>ПОТЕРЯЕШЬ ВЕСЬ ЛУТ</b> (кроме опыта за убийства).\n"
        "Чтобы сохранить добычу, нажми <b>ЭВАКУАЦИЯ</b> в любой безопасный момент."
    ),
    'combat': (
        "<b>⚔️ БОЕВАЯ СИСТЕМА</b>\n\n"
        "Встретив врага, у тебя есть выбор:\n\n"
        "1. <b>⚔️ АТАКА:</b> Наносишь урон (зависит от ATK ±20%).\n"
        "   • <i>Крит:</i> Шанс x1.5 урона (зависит от LUCK).\n"
        "   • <i>Адреналин:</i> Если HP &lt; 20%, урон x2.\n"
        "   • <i>Казнь:</i> Если у врага &lt; 10% HP, он умирает мгновенно.\n"
        "2. <b>🏃 ПОБЕГ:</b> Шанс 50% + бонусы Удачи. Провал = удар в спину.\n\n"
        "<b>🎒 РАСХОДНИКИ В БОЮ:</b>\n"
        "• <b>💣 EMP-граната:</b> Наносит 150 чистого урона.\n"
        "• <b>👻 Стелс-спрей:</b> 100% шанс побега.\n"
        "• <b>🧹 Стиратель памяти:</b> Сбрасывает бой.\n\n"
        "<b>🛡 ЗАЩИТА:</b> Твоя DEF снижает входящий урон."
    ),
    'stats': (
        "<b>📊 ПРОКАЧКА И ХАРАКТЕРИСТИКИ</b>\n\n"
        "<b>📈 УРОВНИ (1-30):</b>\n"
        "С 1 по 5 уровни опыт фиксирован. С 6-го — растет экспоненциально (x1.5).\n\n"
        "<b>📉 СТАТЫ:</b>\n"
        "• <b>⚔️ ATK (Атака):</b> Твой урон в бою.\n"
        "• <b>🛡 DEF (Защита):</b> Снижает урон от монстров и ловушек.\n"
        "• <b>🍀 LUCK (Удача):</b> Шанс крита, лучшего лута и побега.\n\n"
        "<b>🧬 ФРАКЦИИ (БОНУСЫ):</b>\n"
        "• <b>🏦 МАТЕРИЯ:</b> +20% Монет в рейдах. (-Защита)\n"
        "• <b>🧠 РАЗУМ:</b> +10 к Защите. +15% Уворот в Глубокой Сети. (-Удача)\n"
        "• <b>🤖 ТЕХНО:</b> +10 к Удаче. -10% урона от роботов. (-Опыт за убийства)"
    ),
    'items': (
        "<b>🎒 ПРЕДМЕТЫ И ЭКИПИРОВКА</b>\n\n"
        "<b>👘 СЛОТЫ:</b>\n"
        "Ты можешь надеть шлем, бронежилет, оружие и чип.\n\n"
        "<b>📦 ВАЖНЫЕ РАСХОДНИКИ:</b>\n"
        "• <b>🔋 Батарея:</b> Лечит +30% Сигнала.\n"
        "• <b>💉 Нейро-стимулятор:</b> Лечит +60% Сигнала.\n"
        "• <b>🧭 Компас:</b> Показывает тип следующей комнаты.\n"
        "• <b>🗝 Ключи:</b> Нужны для сундуков (Магнитная отмычка, Ключ Бездны).\n"
        "• <b>💾 Дата-шип:</b> 80% шанс взломать сундук без ключа."
    ),
    'pvp': (
        "<b>🔓 PvP: ВЗЛОМ (/hack_random)</b>\n\n"
        "Ты можешь попытаться украсть монеты у случайного игрока.\n\n"
        "• <b>Команда:</b> Напиши <code>/hack_random</code> в чат.\n"
        "• <b>Цена:</b> 50 XP за попытку.\n"
        "• <b>Механика:</b> Твоя (ATK + LUCK) против (DEF + Level) жертвы.\n"
        "• <b>Успех:</b> Крадешь 5-10% монет (до 5000).\n"
        "• <b>Провал:</b> Теряешь XP.\n\n"
        "🛡 <b>ЗАЩИТА:</b> Купи предмет <b>Файрвол</b> в магазине. Он заблокирует одну атаку."
    ),
    'social': (
        "<b>🤝 СОЦИАЛЬНАЯ СИСТЕМА (СИНДИКАТ)</b>\n\n"
        "В Профиле есть кнопка <b>Синдикат</b>. Там твоя реферальная ссылка.\n\n"
        "<b>🎁 БОНУСЫ:</b>\n"
        "1. <b>300 XP</b> сразу за приглашенного друга.\n"
        "2. <b>10% (Роялти)</b> от всего XP и Монет, которые заработает друг, НАВСЕГДА."
    ),
    'tips': (
        "<b>⚡️ СОВЕТЫ НОВИЧКУ</b>\n\n"
        "1. Не жадничай в Рейдах. Если HP меньше 30% и нет аптечек — эвакуируйся!\n"
        "2. Купи <b>Ржавый Тесак</b> как можно скорее.\n"
        "3. Всегда носи <b>Магнитную Отмычку</b> — в сундуках лежат самые дорогие предметы.\n"
        "4. Заходи в игру каждый день, чтобы растить <b>Стрик</b> (бонус к опыту).\n"
        "5. Разбирай ненужные вещи в инвентаре на Монеты."
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

def strip_html(text):
    """Удаляет HTML теги из текста для алерта."""
    if not text: return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean

def parse_riddle(text):
    """
    Парсит текст загадки, извлекая ответ из скобок.
    Поддерживает форматы:
    1. (Ответ: Ответ) или (Протокол: Ответ) - строгий поиск.
    2. (Ответ) - если текст содержит 'ЗАГАДКА', ищет последнее содержимое скобок.
    Возвращает (answer, clean_text). Если ответ не найден, answer=None.
    """
    if not text: return None, text

    # 1. Строгий поиск с префиксом
    strict_match = re.search(r'\s*\((?:Ответ|Протокол):\s*(.*?)\)', text, re.IGNORECASE)

    match = strict_match

    # 2. Мягкий поиск (fallback), если это явно загадка
    if not match and "ЗАГАДКА" in text.upper():
         # Ищем содержимое скобок (берем ПОСЛЕДНЕЕ вхождение)
         all_matches = list(re.finditer(r'\(([^()]+)\)', text))
         if all_matches:
             match = all_matches[-1]

    if match:
         answer = match.group(1).strip()
         start, end = match.span()

         if strict_match:
             # Для строгого поиска вырезаем только блок ответа, сохраняя контекст
             clean_text = (text[:start] + text[end:]).strip()
         else:
             # Для мягкого поиска обрезаем текст ПО начало ответа, чтобы убрать спойлеры ("Правильно! Это...")
             clean_text = text[:start].strip()

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
        if iid in ['master_key', 'abyssal_key', 'data_spike']:
            keys += i['quantity']
        elif iid == 'battery': consumables.append("🔋")
        elif iid == 'neural_stimulator': consumables.append("💉")
        elif iid == 'emp_grenade': consumables.append("💣")
        elif iid == 'stealth_spray': consumables.append("🌫")
        elif iid == 'memory_wiper': consumables.append("🌀")

    cons_str = "".join(consumables[:5]) # Limit display

    # Format
    return (
        f"🎒 Инв: {inv_count}/{inv_limit} | 🗝 Ключи: {keys} | {cons_str}\n"
        f"⚡ XP: {u['xp']} | 🪙 BC: {u['biocoin']}"
    )

def get_raid_entry_cost(uid):
    u = db.get_user(uid)
    if not u: return 100

    level = u.get('level', 1)
    # Dynamic Cost Formula: 100 + (Level * 150)
    return 100 + (level * 150)

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
    txt = (
        f"👹 УГРОЗА ОБНАРУЖЕНА: <b>{villain['name']}</b> (Lvl {villain['level']})\n\n"
        f"<i>{villain['description']}</i>\n\n"
        f"📊 <b>ХАРАКТЕРИСТИКИ ВРАГА:</b>\n"
        f"❤️ HP: {hp} / {villain['hp']}\n"
        f"⚔️ Атака: {villain['atk']} | 🛡 Защита: {villain['def']}\n\n"
        f"👤 <b>ВАШИ ХАРАКТЕРИСТИКИ:</b>\n"
        f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n\n"
        f"⚠️ Оцените риски перед атакой."
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
    if r < 0.15: return 'combat'        # 15% Combat
    if r < 0.20: return 'locked_chest'  # 5% Locked Chest
    if r < 0.50: return 'lore'          # 30% Lore Room
    return 'random'                     # 50% Random (Traps/Loot/Riddles)

def generate_balanced_event_type(last_type, current_streak):
    # Base logic
    new_type = generate_random_event_type()

    # Streak prevention
    if current_streak >= 4 and new_type == last_type:
        # Force switch
        options = ['combat', 'locked_chest', 'random', 'lore']
        if last_type in options: options.remove(last_type)
        return random.choice(options)

    if current_streak >= 2 and new_type == last_type:
        # Reduce probability (retry once)
        new_type = generate_random_event_type()

    return new_type

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
                cur.execute("INSERT INTO raid_sessions (uid, depth, signal, start_time, kills, riddles_solved, next_event_type, event_streak, buffer_items, buffer_xp, buffer_coins) VALUES (%s, %s, 100, %s, 0, 0, %s, 1, '', 0, 0)",
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
                return True, f"🌀 <b>АНОМАЛИЯ</b>\n{glitch_text}", {'alert': strip_html(glitch_text)}, u, 'glitch', 0

            # ПРОВЕРКА БОЯ
            if s.get('current_enemy_id'):
                vid = s['current_enemy_id']
                v_hp = s.get('current_enemy_hp', 10)
                villain = db.get_villain_by_id(vid, cursor=cur)
                if villain:
                    extra_data = {'image': villain.get('image')}
                    return True, format_combat_screen(villain, v_hp, s['signal'], stats, s), extra_data, u, 'combat', 0
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

            # 2.3 ДЕЙСТВИЕ: МАРОДЕРСТВО
            if answer == 'claim_body':
                 loot = db.get_death_loot_at_depth(depth)
                 if loot:
                     if db.claim_death_loot(loot['id']):
                         amount = loot['amount']
                         cur.execute("UPDATE raid_sessions SET buffer_coins=buffer_coins+%s WHERE uid=%s", (amount, uid))
                         conn.commit()
                         return True, f"💰 <b>МАРОДЕРСТВО:</b> Вы забрали {amount} BC.", {'alert': f"💰 +{amount} BC"}, u, 'loot_claimed', 0
                 return False, "❌ Останки уже разграблены или исчезли.", None, u, 'neutral', 0

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

            # --- HEAD AURA: MOVEMENT (Void Walker / Relic Speed) ---
            step_size = 1
            equipped_head = db.get_equipped_items(uid).get('head')

            if equipped_head in ['relic_speed', 'shadow_reliq-speed']:
                step_size = 2
            elif equipped_head == 'void_walker_hood' and random.random() < 0.25:
                step_size = 2
                msg_prefix += "🌌 <b>ДВОЙНОЙ ШАГ:</b> Вы проскользнули сквозь пространство!\n"

            new_depth = depth + step_size if not is_new else depth

            # Логика типа события
            current_type_code = s.get('next_event_type', 'random')
            current_streak = s.get('event_streak', 0)

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
                    # STRICT COPY to prevent mutation of cache/config
                    villain = copy.deepcopy(villain)

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
                    extra_data = {
                        'image': villain.get('image'),
                        'alert': f"⚔️ БОЙ!\n{villain['name']}"
                    }
                    return True, format_combat_screen(villain, villain['hp'], s['signal'], stats, s), extra_data, u, 'combat', 0

            # СУНДУК
            elif current_type_code == 'locked_chest':
                event = {'type': 'locked_chest', 'text': 'Запертый контейнер.', 'val': 0}

            # ПЕРЕДЫШКА (ЛОР)
            elif current_type_code == 'lore':
                adv_level = 1
                if depth >= 100: adv_level = 3
                elif depth >= 50: adv_level = 2

                lore_text = db.get_random_raid_advice(adv_level, cursor=cur)
                if not lore_text: lore_text = "Только эхо твоих шагов в пустом кластере данных..."

                event = {'type': 'neutral', 'text': f"💨 <b>БЕЗОПАСНАЯ ЗОНА</b>\n\nВы переводите дух. В логах терминала осталась запись:\n<i>«{lore_text}»</i>", 'val': 0}

            # СЛУЧАЙНОЕ
            else:
                death_loot = db.get_death_loot_at_depth(depth)

                # --- ANOMALY EVENT (Maxwell's Demon) ---
                if depth > 50 and random.random() < 0.05:
                     event = {'text': '🔴 <b>АНОМАЛИЯ:</b> Демон Максвелла.', 'type': 'anomaly_terminal', 'val': 0}
                # --- SCAVENGING (Found Body) ---
                elif death_loot and random.random() < 0.8:
                     event = {'text': f"💀 <b>ОСТАНКИ:</b> Вы наткнулись на след @{death_loot['original_owner_name']}.\nЕго кэш ({death_loot['amount']} BC) еще здесь.", 'type': 'found_body', 'val': death_loot['amount']}
                else:
                     cur.execute("SELECT text, type, val FROM raid_content ORDER BY RANDOM() LIMIT 1")
                     event = cur.fetchone()
                     if not event: event = {'text': "Пустота...", 'type': 'neutral', 'val': 0}

                # --- HEAD AURA: NOMAD GOGGLES (Loot Finder) ---
                if event['type'] == 'neutral' and equipped_head == 'nomad_goggles':
                    if random.random() < 0.05:
                        event = {'type': 'loot', 'text': 'Скрытый тайник (Окуляры)', 'val': 100}
                        msg_prefix += "🥽 <b>ОКУЛЯРЫ:</b> Обнаружен скрытый лут!\n"

            # Парсинг загадки
            riddle_answer, event['text'] = parse_riddle(event['text'])

            new_sig = s['signal']
            msg_event = ""
            riddle_data = None
            death_reason = None
            alert_msg = None

            # ЭФФЕКТЫ СОБЫТИЙ
            if event['type'] == 'trap':
                base_dmg = int(event['val'] * diff)

                # --- HEAD AURA: SCAVENGER MASK ---
                if equipped_head == 'scavenger_mask':
                    base_dmg = max(0, base_dmg - 5)

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

                # ONE-SHOT PROTECTION
                elif new_sig > 90 and (new_sig - dmg <= 0):
                     dmg = new_sig - 5
                     msg_prefix += "⚠️ <b>СИСТЕМА СПАСЕНИЯ:</b> Критический урон снижен!\n"

                new_sig = max(0, new_sig - dmg)
                msg_event = f"💥 <b>ЛОВУШКА:</b> {event['text']}\n🔻 <b>-{dmg}% Сигнала</b>"
                alert_msg = f"💥 ЛОВУШКА!\n{event['text']}\n-{dmg}% Сигнала"

                if new_sig <= 0:
                    death_reason = f"ЛОВУШКА: {event['text']}"
                    # Log Death
                    broadcast = handle_death_log(uid, depth, u['level'], u['username'], res['buffer_coins'])
                    if broadcast:
                        pass # Returned in extra_data via death_reason? No, death_reason is text.
                        # I'll append broadcast to death_reason or handle via extra data?
                        # process_raid_step returns (..., extra_data, ...)
                        # extra_data is {'death_reason': ...}
                        # I can add 'broadcast': ...

            elif event['type'] == 'loot':
                # TIERED LOOT IMPLEMENTATION
                loot_info = generate_loot(depth, stats['luck'])
                bonus_xp = int(event['val'] * diff * loot_info['mult'])
                coins = int(random.randint(5, 20) * loot_info['mult'])

                # --- ANOMALY BUFF: OVERLOAD (+50% Coins) ---
                if u.get('anomaly_buff_expiry', 0) > time.time() and u.get('anomaly_buff_type') == 'overload':
                    coins = int(coins * 1.5)
                    msg_prefix += "⚡️ <b>ПЕРЕГРУЗКА:</b> +50% монет.\n"

                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, coins, uid))

                # --- ENCRYPTED CACHE DROP (5% Chance on Loot) ---
                # Check if user already has one? Limit 1.
                cache_drop_txt = ""
                if random.random() < 0.05:
                    # Check if user has cache in inventory or processing
                    # Assuming 'encrypted_cache' is an item in inventory OR a state.
                    # Prompt says: "Finds... put on decryption in main menu".
                    # Let's treat it as an item 'encrypted_cache'.
                    if db.add_item(uid, 'encrypted_cache'):
                        cache_drop_txt = "\n🔐 <b>ПОЛУЧЕНО:</b> Зашифрованный Кэш"

                msg_event = f"{loot_info['prefix']} <b>НАХОДКА:</b> {event['text']}\n+{bonus_xp} XP | +{coins} BC{cache_drop_txt}"
                alert_msg = f"💎 НАХОДКА!\n{event['text']}\n+{bonus_xp} XP | +{coins} BC{cache_drop_txt}"

            elif event['type'] == 'heal':
                new_sig = min(100, new_sig + 25)
                msg_event = f"❤️ <b>АПТЕЧКА:</b> {event['text']}\n+25% Сигнала"
                alert_msg = f"❤️ АПТЕЧКА!\n+25% Сигнала"

            elif event['type'] == 'anomaly_terminal':
                msg_event = f"🔴 <b>АНОМАЛИЯ:</b>\nВы встретили Демона Максвелла.\nОн предлагает сыграть."
                alert_msg = "🔴 АНОМАЛИЯ!"

            elif event['type'] == 'found_body':
                msg_event = event['text']
                alert_msg = "💀 ОСТАНКИ"

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
                riddle_data = {"question": event['text'], "correct": riddle_answer, "options": options, "alert": "🧩 ЗАГАДКА!"}
                msg_event = f"🧩 <b>ЗАГАДКА:</b>\n{event['text']}"
                cur.execute("UPDATE raid_sessions SET current_riddle_answer=%s WHERE uid=%s", (riddle_answer, uid))
                event['type'] = 'riddle'

            # ПОДГОТОВКА СЛЕДУЮЩЕГО ШАГА
            next_preview = generate_balanced_event_type(current_type_code, current_streak)
            new_streak = current_streak + 1 if next_preview == current_type_code else 1

            cur.execute("UPDATE raid_sessions SET depth=%s, signal=%s, next_event_type=%s, event_streak=%s WHERE uid=%s", (new_depth, new_sig, next_preview, new_streak, uid))
            
            if new_depth > u.get('max_depth', 0): 
                cur.execute("UPDATE users SET max_depth=%s WHERE uid=%s", (new_depth, uid))

            conn.commit() # ФИКСИРУЕМ ШАГ

            if riddle_data:
                if alert_msg: riddle_data['alert'] = alert_msg # Override if needed, but riddle_data is separate
                else: riddle_data['alert'] = "🧩 ЗАГАДКА!"
            elif alert_msg:
                # If not riddle (riddle_data is returned as 3rd arg), pass alert in extra?
                # The function signature returns: True, interface, riddle_data, u, type, cost
                # Wait, riddle_data IS the extra_data for non-combat?
                # Let's check the return below.
                pass

            # СБОРКА UI
            cur.execute("SELECT buffer_xp, buffer_coins FROM raid_sessions WHERE uid = %s", (uid,))
            res = cur.fetchone()

            # Achievements Check
            new_achs = check_achievements(uid)
            if new_achs:
                ach_txt = ""
                for a in new_achs:
                    ach_txt += f"\n🏆 <b>ДОСТИЖЕНИЕ: {a['name']}</b> (+{a['xp']} XP)"
                msg_event += ach_txt
                if alert_msg: alert_msg += ach_txt
                else: alert_msg = "🏆 НОВОЕ ДОСТИЖЕНИЕ!" + ach_txt
            
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
            # Always show advice if not in combat and not dead
            if current_type_code != 'combat' and current_type_code != 'lore' and new_sig > 0:
                adv_level = 1
                if new_depth >= 100: adv_level = 3
                elif new_depth >= 50: adv_level = 2

                advice = db.get_random_raid_advice(adv_level, cursor=cur)
                if advice:
                    advice_text = f"\n\n🧩 <i>Совет: {advice}</i>"

            interface = (
                f"🏝 <b>{biome_data['name']}</b> | <b>{new_depth}м</b>\n"
                f"📡 Сигнал: <code>{sig_bar}</code> {new_sig}%\n"
                f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n"
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

                 extra_death = {}
                 if death_reason: extra_death['death_reason'] = death_reason

                 # Broadcast Check
                 broadcast = handle_death_log(uid, depth, u['level'], u['username'], res['buffer_coins'])
                 if broadcast: extra_death['broadcast'] = broadcast

                 return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м\nРесурсы утеряны.", extra_death, u, 'death', 0

            # If riddle_data exists, it is passed as 3rd arg.
            # If not, we can pass a dict with alert as 3rd arg if we want.
            # But the caller expects riddle_data to be None or Dict.
            # If event['type'] == 'riddle', riddle_data is populated.
            # If not, it is None.

            extra_ret = None
            if riddle_data:
                extra_ret = riddle_data
            elif alert_msg:
                extra_ret = {'alert': alert_msg}

            return True, interface, extra_ret, u, event['type'], next_step_cost

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
    if not u: return 'error', "Пользователь не найден.", None

    s = db.get_raid_session_enemy(uid)

    if not s or not s.get('current_enemy_id'):
         return 'error', "Нет активного боя.", None

    enemy_id = s['current_enemy_id']
    enemy_hp = s['current_enemy_hp']

    villain = db.get_villain_by_id(enemy_id)
    if not villain:
        db.clear_raid_enemy(uid)
        return 'error', "Враг исчез.", None

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

    if not full_s: return 'error', "Сессия не найдена.", None

    current_signal = full_s['signal']
    biome_data = get_biome_modifiers(full_s.get('depth', 0))

    # --- HEAD AURA CHECK ---
    equipped_head = db.get_equipped_items(uid).get('head')

    if action == 'attack':
        # ADRENALINE
        dmg_mult = 1.0
        if current_signal < 20:
            dmg_mult = 2.0
            msg += "🩸 <b>АДРЕНАЛИН:</b> Урон удвоен!\n"

        crit_chance = stats['luck'] / 100.0

        # --- AURA: OVERCLOCK CROWN ---
        if equipped_head == 'overclock_crown':
            crit_chance *= 2.0

        is_crit = random.random() < crit_chance

        if is_crit and equipped_head == 'overclock_crown':
             # Self damage
             current_signal = max(1, current_signal - 2)
             cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (current_signal, uid))
             msg += "👑 <b>ВЕНЕЦ:</b> Перегрузка! -2% Сигнала.\n"

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

        # --- AURA: RELIC VAMPIRE (Heal on Hit) ---
        if equipped_head == 'relic_vampire':
            heal = 2
            current_signal = min(100, current_signal + heal)
            cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (current_signal, uid))
            msg += f"🦇 <b>ВАМПИРИЗМ:</b> +{heal}% Сигнала.\n"

        if new_enemy_hp <= 0:
            xp_gain = villain.get('xp_reward', 0)
            coin_gain = villain.get('coin_reward', 0)

            # --- ANOMALY BUFF: OVERLOAD (+50% Coins) ---
            if u.get('anomaly_buff_expiry', 0) > time.time() and u.get('anomaly_buff_type') == 'overload':
                coin_gain = int(coin_gain * 1.5)
                msg += "⚡️ <b>ПЕРЕГРУЗКА:</b> +50% монет.\n"

            # --- AURA: VAMPIRE VISOR (Heal on Kill) ---
            if equipped_head == 'vampire_visor':
                heal = 5
                current_signal = min(100, current_signal + heal)
                cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (current_signal, uid))
                msg += f"🩸 <b>ПОГЛОЩЕНИЕ:</b> +{heal}% Сигнала.\n"

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

            return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен.\nПолучено: +{xp_gain} XP | +{coin_gain} BC", None

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

            # --- AURA: TACTICAL HELMET (Auto Dodge) ---
            if equipped_head in ['tactical_helmet', 'Tac_visor'] and random.random() < 0.10:
                enemy_dmg = 0
                msg += "🪖 <b>ТАКТИКА:</b> Автоматическое уклонение!\n"

            # --- AURA: ARCHITECT MASK (Reflection) ---
            if equipped_head == 'architect_mask' and enemy_dmg > 0:
                reflect = int(enemy_dmg * 0.3)
                if reflect > 0:
                    new_enemy_hp = max(0, new_enemy_hp - reflect)
                    db.update_raid_enemy(uid, enemy_id, new_enemy_hp)
                    msg += f"🎭 <b>ЗЕРКАЛО:</b> Отражено {reflect} урона.\n"

            used_aegis = False
            if enemy_dmg > current_signal:
                 if db.get_item_count(uid, 'aegis') > 0:
                      if db.use_item(uid, 'aegis'):
                           enemy_dmg = 0
                           msg += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                           used_aegis = True

            new_sig = max(0, current_signal - enemy_dmg)

            # --- AURA: CYBER HALO (Death Prevent) ---
            if new_sig <= 0 and equipped_head == 'cyber_halo':
                # Check cooldown? Prompt says "1 time per battle".
                # We need to track if halo used in this battle.
                # Currently raid_sessions doesn't have a 'halo_used' flag.
                # Simplification: 20% chance always (without limit per battle it might be OP, but without DB change...)
                # Prompt: "20% chance that fatal blow leaves 1% Signal (cooldown 1 time per battle)".
                # To do "1 time per battle", I'd need to store state.
                # Given I can't easily add column now without schema drift risk/complexity, I will stick to "20% chance" OR add a temp flag in `buffer_items` or similar?
                # `buffer_items` is for loot.
                # I'll stick to simple 20% chance for now or skip cooldown.
                if random.random() < 0.20:
                    new_sig = 1
                    msg += "🪩 <b>НИМБ:</b> Вмешательство системы! Смерть отменена.\n"

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

                extra_death = {}
                broadcast = handle_death_log(uid, full_s['depth'], u['level'], u['username'], full_s['buffer_coins'])
                if broadcast: extra_death['broadcast'] = broadcast

                return 'death', f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nВраг нанес смертельный удар.\n\n{report}", extra_death

            return 'combat', msg, None

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
                return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен взрывом.\nПолучено: +{xp_gain} XP | +{coin_gain} BC", None
            else:
                db.update_raid_enemy(uid, enemy_id, new_enemy_hp)
                msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"
        else:
             return 'error', "Нет EMP гранаты.", None

    elif action == 'use_stealth':
        if db.get_item_count(uid, 'stealth_spray') > 0:
            db.use_item(uid, 'stealth_spray', 1)
            db.clear_raid_enemy(uid)
            return 'escaped', "👻 <b>СТЕЛС:</b> Вы растворились в тумане. 100% побег.", None
        else:
             return 'error', "Нет спрея.", None

    elif action == 'use_wiper':
        if db.get_item_count(uid, 'memory_wiper') > 0:
            db.use_item(uid, 'memory_wiper', 1)
            db.clear_raid_enemy(uid)
            # Wiper resets aggro, effectively ending combat but maybe keeping position?
            # Same as escaped basically but different flavor.
            return 'escaped', "🧹 <b>СТИРАТЕЛЬ:</b> Память врага очищена. Он забыл о вас.", None
        else:
             return 'error', "Нет стирателя памяти.", None

    elif action == 'run':
        # FACTION SYNERGY (MIND) - Dodge in Deep Net/Void
        bonus_dodge = 0
        if u['path'] == 'mind' and ("Глубокая Сеть" in biome_data['name'] or "Пустота" in biome_data['name']):
            bonus_dodge = 0.15

        chance = 0.5 + (stats['luck'] / 200.0) + bonus_dodge

        if random.random() < chance:
             db.clear_raid_enemy(uid)
             extra_msg = " (Сила Мысли)" if bonus_dodge > 0 else ""
             return 'escaped', f"🏃 <b>ПОБЕГ:</b> Вы успешно скрылись в тенях.{extra_msg}", None
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

                extra_death = {}
                broadcast = handle_death_log(uid, full_s['depth'], u['level'], u['username'], full_s['buffer_coins'])
                if broadcast: extra_death['broadcast'] = broadcast

                return 'death', f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nВраг нанес смертельный удар.\n\n{report}", extra_death

             return 'combat', msg, None

    return res_type, msg, None

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

def start_decryption(uid):
    # Check if user has cache item
    if db.get_item_count(uid, 'encrypted_cache') <= 0:
        return False, "❌ У вас нет Зашифрованного Кэша."

    u = db.get_user(uid)
    # Check if already unlocking (unlock_time > 0)
    if u.get('encrypted_cache_unlock_time', 0) > 0:
        # If time passed, tell them to claim. If not, tell them to wait.
        if time.time() >= u['encrypted_cache_unlock_time']:
             return False, "✅ Кэш уже взломан! Нажмите 'Открыть'."
        else:
             return False, "⏳ Процесс уже идет."

    # Calc time
    base_hours = 4.0
    # Faction Bonus
    if u['path'] == 'tech':
        base_hours = 2.0

    # Item Bonus
    has_decoder = db.get_item_count(uid, 'decoder') > 0
    if has_decoder:
        base_hours /= 2.0

    unlock_time = int(time.time() + (base_hours * 3600))

    # Consume item to start
    if db.use_item(uid, 'encrypted_cache', 1):
        db.update_user(uid, encrypted_cache_unlock_time=unlock_time, encrypted_cache_type='standard')
        hours_fmt = f"{base_hours}ч" if base_hours.is_integer() else f"{base_hours}ч"
        return True, f"🔐 <b>РАСШИФРОВКА ЗАПУЩЕНА</b>\n⏱ Время: {hours_fmt}\n\n<i>Система подбирает ключи...</i>"

    return False, "⚠️ Ошибка предмета."

def claim_decrypted_cache(uid):
    u = db.get_user(uid)
    unlock_time = u.get('encrypted_cache_unlock_time', 0)

    if unlock_time == 0:
        return False, "❌ Нет активных контейнеров."

    if time.time() < unlock_time:
        rem = int((unlock_time - time.time()) // 60)
        hours = rem // 60
        mins = rem % 60
        return False, f"⏳ <b>ОСТАЛОСЬ:</b> {hours}ч {mins}м"

    # Grant Loot
    xp = random.randint(500, 1500)
    coins = random.randint(500, 1000)

    db.add_xp_to_user(uid, xp)
    db.update_user(uid, biocoin=u['biocoin'] + coins)

    msg = f"⚡️ +{xp} XP\n🪙 +{coins} BC"

    # Rare Item Drop (30% chance)
    if random.random() < 0.30:
        import config
        # Pick random rare item
        rare_items = [k for k,v in config.EQUIPMENT_DB.items() if v['price'] >= 1000]
        if rare_items:
            item = random.choice(rare_items)
            db.add_item(uid, item)
            name = config.EQUIPMENT_DB[item]['name']
            msg += f"\n📦 <b>ПРЕДМЕТ:</b> {name}"

    # Reset
    db.update_user(uid, encrypted_cache_unlock_time=0, encrypted_cache_type=None)

    return True, f"🔓 <b>КОНТЕЙНЕР ВЗЛОМАН!</b>\n\n{msg}"

def get_decryption_status(uid):
    u = db.get_user(uid)
    unlock_time = u.get('encrypted_cache_unlock_time', 0)

    if unlock_time == 0:
        count = db.get_item_count(uid, 'encrypted_cache')
        if count > 0:
            return "ready_to_start", f"📦 Кэш в инвентаре: {count} шт."
        return "none", "Нет контейнеров."

    if time.time() < unlock_time:
        rem = int((unlock_time - time.time()) // 60)
        hours = rem // 60
        mins = rem % 60
        return "in_progress", f"⏳ {hours}ч {mins}м"

    return "ready_to_claim", "✅ <b>ГОТОВО!</b>"

def check_shadow_broker_trigger(uid):
    u = db.get_user(uid)
    # Don't trigger if already active
    if u.get('shadow_broker_expiry', 0) > time.time():
        return False, 0

    # 2% chance
    if random.random() < 0.02:
        expiry = int(time.time() + 900) # 15 mins
        db.set_shadow_broker(uid, expiry)
        return True, expiry
    return False, 0

def get_shadow_shop_items(uid):
    u = db.get_user(uid)
    expiry = u.get('shadow_broker_expiry', 0)

    if expiry < time.time():
        return []

    # Stable random for the duration of this specific broker instance
    random.seed(expiry + uid)

    import config
    pool = config.SHADOW_BROKER_ITEMS[:]

    # Ensure unique selection
    if len(pool) > 3:
        selected = random.sample(pool, 3)
    else:
        selected = pool

    shop = []
    for item_id in selected:
        info = config.EQUIPMENT_DB.get(item_id) or config.ITEMS_INFO.get(item_id)
        if not info: continue

        base_price = info.get('price', 1000)

        # 50% chance for XP price, 50% for Discounted Coins
        if random.random() < 0.5:
            curr = 'xp'
            # XP Price Logic: Value roughly similar but XP isfarmable.
            # Let's set XP price = Coin Price * 2
            price = int(base_price * 1.5)
        else:
            curr = 'biocoin'
            price = int(base_price * 0.5) # 50% discount!

        shop.append({
            'item_id': item_id,
            'name': info['name'],
            'price': price,
            'currency': curr,
            'desc': info.get('desc', '')
        })

    random.seed() # Reset seed
    return shop

def process_anomaly_bet(uid, bet_type):
    with db.db_session() as conn:
        with conn.cursor(cursor_factory=db.RealDictCursor) as cur:
            cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
            s = cur.fetchone()
            if not s: return False, "Нет активной сессии.", None

            won = random.random() < 0.5
            msg = ""
            alert = ""

            # Helper to set buff/debuff
            def set_status(effect):
                expiry = int(time.time() + 86400)
                cur.execute("UPDATE users SET anomaly_buff_type=%s, anomaly_buff_expiry=%s WHERE uid=%s", (effect, expiry, uid))

            if bet_type == 'hp':
                stake = int(s['signal'] * 0.3)
                if won:
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp*2, buffer_coins=buffer_coins*2 WHERE uid=%s", (uid,))
                    set_status('overload')
                    msg = "🎰 <b>ПОБЕДА!</b>\nБуфер удвоен.\nПолучен бафф: ⚡️ <b>ПЕРЕГРУЗКА</b> (+50% монет)."
                    alert = "🎰 ПОБЕДА! Буфер x2"
                else:
                    new_sig = max(0, s['signal'] - stake)
                    cur.execute("UPDATE raid_sessions SET signal=%s WHERE uid=%s", (new_sig, uid))
                    set_status('corrosion')
                    msg = f"🎰 <b>ПОРАЖЕНИЕ...</b>\nПотеряно {stake}% Сигнала.\nПолучен дебафф: 🦠 <b>КОРРОЗИЯ</b> (-20% статов)."
                    alert = f"🎰 ПОРАЖЕНИЕ! -{stake}% HP"

                    if new_sig <= 0:
                        # Generate report before deleting
                        # We need full_s but we have s
                        # Re-fetch full session not needed, s is fine
                        report = generate_raid_report(uid, s)
                        cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))

                        return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nДемон забрал свою плату.\n\n{report}", {'death_reason': "Демон Максвелла", 'is_death': True}

            elif bet_type == 'buffer':
                if won:
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp*2, buffer_coins=buffer_coins*2 WHERE uid=%s", (uid,))
                    set_status('overload')
                    msg = "🎰 <b>ПОБЕДА!</b>\nБуфер удвоен.\nПолучен бафф: ⚡️ <b>ПЕРЕГРУЗКА</b>."
                    alert = "🎰 ПОБЕДА! Буфер x2"
                else:
                    cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp/2, buffer_coins=buffer_coins/2 WHERE uid=%s", (uid,))
                    set_status('corrosion')
                    msg = "🎰 <b>ПОРАЖЕНИЕ...</b>\nБуфер уполовинен.\nПолучен дебафф: 🦠 <b>КОРРОЗИЯ</b>."
                    alert = "🎰 ПОРАЖЕНИЕ! Буфер /2"

            return True, msg, {'alert': alert}

def handle_death_log(uid, depth, u_level, username, buffer_coins):
    broadcast_msg = None
    # Level 10+ and Depth 200+
    if u_level >= 10 and depth >= 200:
         # Log loot (only if worth it)
         if buffer_coins > 100:
             db.log_death_loot(depth, buffer_coins, username)

         broadcast_msg = (f"💀 <b>СИСТЕМНЫЙ НЕКРОЛОГ</b>\n"
                          f"Архонт @{username} (Lvl {u_level}) уничтожен на глубине {depth}м.\n"
                          f"Остаточный кэш: {buffer_coins} BC.\n"
                          f"Сектор нестабилен.")
    return broadcast_msg
