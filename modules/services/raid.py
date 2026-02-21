import random
import time
import copy
import re
from datetime import datetime
import database as db
from config import RAID_STEP_COST, ITEMS_INFO, RIDDLE_DISTRACTORS
from modules.services.user import get_user_stats, check_achievements
from modules.services.utils import (
    get_biome_modifiers, generate_hud, strip_html, parse_riddle,
    format_combat_screen, generate_raid_report, handle_death_log,
    draw_bar
)

def get_raid_entry_cost(uid):
    u = db.get_user(uid)
    if not u: return 100

    level = u.get('level', 1)
    # Dynamic Cost Formula: 100 + (Level * 150)
    return 100 + (level * 150)

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

def generate_loot(depth, luck):
    """Генерирует тир лута на основе удачи (Новая система редкости)."""
    # Base roll 0-100
    roll = random.uniform(0, 100)

    # Luck adjustment: Every 10 luck adds 1% to roll
    roll += (luck * 0.1)

    if roll >= 98:
        return {"prefix": "🔴 [ПРОКЛЯТОЕ]", "mult": 10.0, "icon": "🔴"}
    elif roll >= 93:
        return {"prefix": "🟠 [ЛЕГЕНДА]", "mult": 5.0, "icon": "🟠"}
    elif roll >= 84:
        return {"prefix": "🟣 [МИФ]", "mult": 2.5, "icon": "🟣"}
    elif roll >= 64:
        return {"prefix": "🔵 [РЕДКОЕ]", "mult": 1.5, "icon": "🔵"}
    else:
        return {"prefix": "⚪️ [ОБЫЧНОЕ]", "mult": 1.0, "icon": "⚪️"}

def get_chest_drops(depth, luck):
    pool = ['battery', 'compass', 'rusty_knife', 'hoodie', 'ram_chip']

    # Depth scaling
    if depth > 50:
        pool.extend(['crowbar', 'leather_jacket', 'cpu_booster', 'neural_stimulator'])
    if depth > 150:
        pool.extend(['shock_baton', 'kevlar_vest', 'glitch_filter', 'emp_grenade', 'stealth_spray', 'data_spike'])
    if depth > 300:
        pool.extend(['cyber_katana', 'tactical_suit', 'ai_core', 'memory_wiper', 'abyssal_key'])

    # Luck roll for rare
    if random.randint(0, 100) + (luck * 0.5) > 90:
        pool.extend(['laser_pistol', 'nano_suit', 'backup_drive', 'nomad_goggles'])

    return random.choice(pool)

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

def process_raid_step(uid, answer=None, start_depth=None):
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
                if start_depth is not None:
                     depth = start_depth

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
                     l_item = get_chest_drops(depth, stats['luck'])
                     cur.execute("UPDATE raid_sessions SET buffer_items = buffer_items || ',' || %s WHERE uid=%s", (l_item, uid))
                     loot_item_txt = f"\n📦 Предмет: {ITEMS_INFO.get(l_item, {}).get('name')}"

                cur.execute("UPDATE raid_sessions SET buffer_xp=buffer_xp+%s, buffer_coins=buffer_coins+%s WHERE uid=%s", (bonus_xp, bonus_coins, uid))
                conn.commit()

                alert_txt = f"🔓 УСПЕХ!\nXP: +{bonus_xp}\nCoins: +{bonus_coins}{loot_item_txt}"

                # Возвращаем тип 'loot_opened' чтобы обновить кнопки
                return True, "СУНДУК ОТКРЫТ", {'alert': alert_txt}, u, 'loot_opened', 0

            # 2.3 ДЕЙСТВИЕ: МАРОДЕРСТВО
            if answer == 'claim_body':
                 grave = db.get_random_grave(depth)
                 if grave:
                     if db.delete_grave(grave['id']):
                         import json
                         try:
                             loot = json.loads(grave['loot_json'])
                             coins = loot.get('coins', 0)
                             items_str = loot.get('items', '')
                         except:
                             coins = 0
                             items_str = ""

                         cur.execute("UPDATE raid_sessions SET buffer_coins=buffer_coins+%s WHERE uid=%s", (coins, uid))
                         if items_str:
                             cur.execute("UPDATE raid_sessions SET buffer_items = buffer_items || ',' || %s WHERE uid=%s", (items_str, uid))

                         conn.commit()
                         return True, f"💰 <b>МАРОДЕРСТВО:</b> Вы забрали {coins} BC и снаряжение.", {'alert': f"💰 +{coins} BC"}, u, 'loot_claimed', 0
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
            msg_prefix = ""

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
                # Use new grave system
                grave = db.get_random_grave(depth)

                # --- ANOMALY EVENT (Maxwell's Demon) ---
                if depth > 50 and random.random() < 0.05:
                     event = {'text': '🔴 <b>АНОМАЛИЯ:</b> Демон Максвелла.', 'type': 'anomaly_terminal', 'val': 0}
                # --- SCAVENGING (Found Body) ---
                elif grave and random.random() < 0.3: # 30% chance if grave exists
                     # Load loot to show value?
                     import json
                     try:
                         loot = json.loads(grave['loot_json'])
                         coins = loot.get('coins', 0)
                     except: coins = 0

                     event = {'text': f"💀 <b>ОСТАНКИ:</b> Вы наткнулись на след @{grave['owner_name']}.\nТруп еще теплый...", 'type': 'found_body', 'val': grave['id']} # Pass ID as val
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
                 report = generate_raid_report(uid, s)
                 cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))

                 # Save Grave (Loot)
                 import json
                 grave_loot = {'coins': s['buffer_coins'], 'items': s.get('buffer_items', '')}
                 if s['buffer_coins'] > 0 or s.get('buffer_items'):
                     db.save_raid_grave(depth, json.dumps(grave_loot), u['username'] or "Unknown")

                 db.log_action(uid, 'death', f"Depth: {depth}, Reason: {death_reason}")
                 conn.commit()

                 extra_death = {}
                 if death_reason: extra_death['death_reason'] = death_reason

                 # Broadcast Check
                 broadcast = handle_death_log(uid, depth, u['level'], u['username'], s['buffer_coins'])
                 if broadcast: extra_death['broadcast'] = broadcast

                 return False, f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nГлубина: {new_depth}м\n\n{report}", extra_death, u, 'death', 0

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
