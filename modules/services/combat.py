import random
import time
import database as db
import json
from modules.services.user import get_user_stats
from modules.services.utils import get_biome_modifiers, generate_raid_report, handle_death_log

def process_combat_action(uid, action):
    stats, u = get_user_stats(uid)
    if not u: return 'error', "Пользователь не найден.", None

    s = db.get_raid_session_enemy(uid)

    if not s or not s.get('current_enemy_id'):
         return 'error', "Нет активного боя.", None

    enemy_id = s['current_enemy_id']
    try:
        enemy_hp = int(s.get('current_enemy_hp', 0))
    except:
        return 'error', "Ошибка данных боя (HP).", None

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
        if not cur: return 'error', "Database Error", None
        cur.execute("SELECT * FROM raid_sessions WHERE uid=%s", (uid,))
        full_s = cur.fetchone()

        if not full_s: return 'error', "Сессия не найдена.", None

        current_signal = full_s['signal']
        biome_data = get_biome_modifiers(full_s.get('depth', 0))

        # --- ITEM CHECKS ---
        # Use shared cursor to optimize DB calls inside transaction
        eq_items = db.get_equipped_items(uid, cursor=cur)
        equipped_head = eq_items.get('head')
        equipped_weapon = eq_items.get('weapon')
        equipped_armor = eq_items.get('armor')
        equipped_chip = eq_items.get('chip')

        try:
            mech_data = json.loads(full_s.get('mechanic_data', '{}') or '{}')
        except: mech_data = {}

        # --- MECHANICS: SCHRODINGER'S ARMOR ---
        if equipped_armor == 'schrodinger_armor':
            sch_def = mech_data.get('schrodinger_def')
            if sch_def is not None:
                stats['def'] = sch_def
                # msg += f"🎲 <b>ШРЕДИНГЕР:</b> DEF={sch_def}\n" # Optional spam

        # --- MECHANICS: MARTYR'S HALO ---
        if equipped_head == 'martyr_halo':
            if current_signal <= 10:
                bonus_luck = 200
                msg += "🕯 <b>МУЧЕНИК:</b> Смертельная удача (+200)!\n"
            else:
                bonus_luck = int((100 - current_signal) * 2)
            stats['luck'] += bonus_luck

        if action == 'attack':
            # --- ADRENALINE LOGIC ---
            dmg_mult = 1.0
            is_adrenaline = False
            if current_signal < 20:
                dmg_mult = 2.0
                is_adrenaline = True
                msg += "🩸 <b>АДРЕНАЛИН:</b> Урон удвоен!\n"

            # Log initial stats for debugging
            print(f"/// COMBAT DEBUG: UID={uid} | ATK={stats['atk']} | LUCK={stats['luck']} | Signal={current_signal} | Adrenaline={is_adrenaline}")

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

            # 1. CREDIT SLICER (Weapon)
            if equipped_weapon == 'credit_slicer':
                burn = int(u['biocoin'] * 0.01)
                if burn > 0:
                    # Using separate cursor or ensuring update_user uses current cursor via helper?
                    # db.update_user creates new session. Since we are inside a session, mixing is tricky unless update_user supports cursor.
                    # db.update_user does NOT support cursor.
                    # We should do inline update here to stay atomic.
                    cur.execute("UPDATE players SET biocoin = GREATEST(0, biocoin - %s) WHERE uid = %s", (burn, uid))
                    base_dmg += burn
                    msg += f"🔪 <b>РЕЗАК:</b> Сожжено {burn} BC ради урона.\n"

            # 2. EMPATH'S NEURO-WHIP (Weapon)
            if equipped_weapon == 'empath_whip':
                base_dmg = int(villain['atk'] * 1.5)
                msg += f"🏏 <b>ЭМПАТИЯ:</b> Возврат агрессии.\n"

            # 3. CACHE WIPER (Weapon)
            if equipped_weapon == 'cache_wiper':
                base_dmg += 200 # Weapon base
                # Loot wipe handled in kill block

            # RNG VARIANCE (Module 2)
            variance = random.uniform(0.8, 1.2)
            dmg = int(base_dmg * variance)
            dmg = max(1, dmg)

            # 4. BANHAMMER SHARD (Weapon)
            ban_triggered = False
            if equipped_weapon == 'banhammer_shard':
                if random.random() < 0.01:
                    dmg = 999999
                    ban_triggered = True
                    msg += "🔨 <b>БАН-ХАММЕР:</b> УДАЛЕНИЕ ОБЪЕКТА ИЗ РЕАЛЬНОСТИ.\n"

            # EXECUTION
            if enemy_hp < (villain['hp'] * 0.1):
                dmg = 999999
                msg += "💀 <b>КАЗНЬ:</b> Вы жестоко добиваете врага.\n"

            new_enemy_hp = enemy_hp - dmg

            print(f"/// COMBAT DEBUG: DMG={dmg} | Enemy HP: {enemy_hp} -> {new_enemy_hp}")

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

                # CACHE WIPER (No Loot)
                if equipped_weapon == 'cache_wiper':
                    xp_gain = 0
                    coin_gain = 0
                    msg += "🔫 <b>СТИРАТЕЛЬ:</b> Лут удален вместе с врагом.\n"

                # BANHAMMER BONUS (x10 XP)
                if ban_triggered:
                    xp_gain *= 10
                    msg += "🔨 <b>БАН-БОНУС:</b> Опыт x10!\n"

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

                # db.clear_raid_enemy(uid) -> Inline
                cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))

                # Update buffer (re-using cur)
                cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s, kills = kills + 1 WHERE uid=%s",
                            (xp_gain, coin_gain, uid))

                db.increment_user_stat(uid, 'kills', cursor=cur)

                return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен.\nПолучено: +{xp_gain} XP | +{coin_gain} BC", None

            else:
                # db.update_raid_enemy(uid, enemy_id, new_enemy_hp) -> Inline
                cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, new_enemy_hp, uid))

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

                # 5. ERROR 404 MIRROR (Armor)
                if equipped_armor == 'error_404_mirror' and enemy_dmg > 0:
                    if random.random() < 0.5:
                        # Reflect full damage? Desc: "Hit pass through you and hit monster"
                        # Assume self=0, monster takes enemy_dmg
                        new_enemy_hp = max(0, new_enemy_hp - enemy_dmg)
                        # db.update_raid_enemy(uid, enemy_id, new_enemy_hp) -> Inline
                        cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, new_enemy_hp, uid))

                        enemy_dmg = 0
                        msg += "🪞 <b>404:</b> Удар прошел сквозь текстуры и задел врага!\n"

                # --- AURA: ARCHITECT MASK (Reflection) ---
                if equipped_head == 'architect_mask' and enemy_dmg > 0:
                    reflect = int(enemy_dmg * 0.3)
                    if reflect > 0:
                        new_enemy_hp = max(0, new_enemy_hp - reflect)
                        # db.update_raid_enemy(uid, enemy_id, new_enemy_hp) -> Inline
                        cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, new_enemy_hp, uid))

                        msg += f"🎭 <b>ЗЕРКАЛО:</b> Отражено {reflect} урона.\n"

                # 6. GRANDFATHER PARADOX (Weapon) - Delayed Damage
                if equipped_weapon == 'grandfather_paradox' and enemy_dmg > 0:
                    # Add to queue
                    dmg_queue = mech_data.get('paradox_queue', [])
                    dmg_queue.append({'dmg': enemy_dmg, 'turns': 3})
                    mech_data['paradox_queue'] = dmg_queue

                    cur.execute("UPDATE raid_sessions SET mechanic_data = %s WHERE uid = %s", (json.dumps(mech_data), uid))

                    msg += "🕰 <b>ПАРАДОКС:</b> Урон отложен на 3 хода.\n"
                    enemy_dmg = 0

                used_aegis = False
                if enemy_dmg > current_signal:
                     if db.get_item_count(uid, 'aegis', cursor=cur) > 0:
                          if db.use_item(uid, 'aegis', cursor=cur):
                               enemy_dmg = 0
                               msg += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                               used_aegis = True

                new_sig = max(0, current_signal - enemy_dmg)

                if new_sig <= 0:
                    db.update_shadow_metric(uid, 'consecutive_deaths', 1)

                # --- AURA: CYBER HALO (Death Prevent) ---
                if new_sig <= 0 and equipped_head == 'cyber_halo':
                    if random.random() < 0.20:
                        new_sig = 1
                        msg += "🪩 <b>НИМБ:</b> Вмешательство системы! Смерть отменена.\n"

                # 7. THERMONUCLEAR SHROUD (Armor) - Prevent Death
                if new_sig <= 0 and equipped_armor == 'thermonuclear_shroud':
                    new_sig = 1
                    new_enemy_hp = 0 # Kill enemy
                    # db.update_raid_enemy(uid, enemy_id, 0) -> Inline
                    cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, 0, uid))

                    # Wipe Loot
                    cur.execute("UPDATE raid_sessions SET buffer_xp = 0, buffer_coins = 0, buffer_items = '' WHERE uid=%s", (uid,))

                    msg += "☢️ <b>САВАН:</b> ВЗРЫВ ЯДРА! Враг уничтожен, лут уничтожен, вы живы.\n"

                cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_sig, uid))

                if enemy_dmg > 0:
                    msg += f"🔻 <b>УДАР:</b> Вы получили -{enemy_dmg}% Сигнала.\n"
                elif used_aegis:
                    pass
                else:
                    msg += f"🛡 <b>БЛОК:</b> Урон поглощен броней.\n"

                if new_sig <= 0:
                    report = generate_raid_report(uid, full_s)
                    cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))

                    extra_death = {}
                    broadcast = handle_death_log(uid, full_s['depth'], u['level'], u['username'], full_s['buffer_coins'], cursor=cur)
                    if broadcast: extra_death['broadcast'] = broadcast

                    return 'death', f"💀 <b>СИГНАЛ ПОТЕРЯН</b>\nВраг нанес смертельный удар.\n\n{report}", extra_death

                return 'combat', msg, None

        elif action == 'use_emp':
            if db.get_item_count(uid, 'emp_grenade', cursor=cur) > 0:
                db.use_item(uid, 'emp_grenade', 1, cursor=cur)
                dmg = 150
                new_enemy_hp = enemy_hp - dmg
                msg += f"💣 <b>EMP ЗАРЯД:</b> Нанесено 150 чистого урона!\n"

                if new_enemy_hp <= 0:
                    xp_gain = villain.get('xp_reward', 0)
                    coin_gain = villain.get('coin_reward', 0)
                    # db.clear_raid_enemy(uid) -> Inline
                    cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))

                    cur.execute("UPDATE raid_sessions SET buffer_xp = buffer_xp + %s, buffer_coins = buffer_coins + %s, kills = kills + 1 WHERE uid=%s",
                                (xp_gain, coin_gain, uid))

                    db.increment_user_stat(uid, 'kills', cursor=cur)

                    return 'win', f"{msg}💀 <b>ПОБЕДА:</b> Враг уничтожен взрывом.\nПолучено: +{xp_gain} XP | +{coin_gain} BC", None
                else:
                    # db.update_raid_enemy(uid, enemy_id, new_enemy_hp) -> Inline
                    cur.execute("UPDATE raid_sessions SET current_enemy_id = %s, current_enemy_hp = %s WHERE uid = %s", (enemy_id, new_enemy_hp, uid))
                    msg += f"👺 <b>ВРАГ:</b> {villain['name']} (HP: {new_enemy_hp}/{villain['hp']})\n"
            else:
                 return 'error', "Нет EMP гранаты.", None

        elif action == 'use_stealth':
            if db.get_item_count(uid, 'stealth_spray', cursor=cur) > 0:
                db.use_item(uid, 'stealth_spray', 1, cursor=cur)
                # db.clear_raid_enemy(uid) -> Inline
                cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))
                return 'escaped', "👻 <b>СТЕЛС:</b> Вы растворились в тумане. 100% побег.", None
            else:
                 return 'error', "Нет спрея.", None

        elif action == 'use_wiper':
            if db.get_item_count(uid, 'memory_wiper', cursor=cur) > 0:
                db.use_item(uid, 'memory_wiper', 1, cursor=cur)
                # db.clear_raid_enemy(uid) -> Inline
                cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))
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
                 # db.clear_raid_enemy(uid) -> Inline
                 cur.execute("UPDATE raid_sessions SET current_enemy_id = NULL, current_enemy_hp = NULL WHERE uid = %s", (uid,))

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
                     if db.get_item_count(uid, 'aegis', cursor=cur) > 0:
                          if db.use_item(uid, 'aegis', cursor=cur):
                               enemy_dmg = 0
                               msg += "🛡 <b>ЭГИДА:</b> Смертельный урон заблокирован!\n"
                               used_aegis = True

                 new_sig = max(0, current_signal - enemy_dmg)
                 if new_sig <= 0:
                     db.update_shadow_metric(uid, 'consecutive_deaths', 1)

                 cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_sig, uid))

                 if enemy_dmg > 0:
                     msg += f"🔻 <b>УДАР:</b> -{enemy_dmg}% Сигнала.\n"
                 elif used_aegis:
                     pass
                 else:
                     msg += f"🛡 <b>БЛОК:</b> Урон поглощен броней.\n"

                 if new_sig <= 0:
                    report = generate_raid_report(uid, full_s)
                    cur.execute("DELETE FROM raid_sessions WHERE uid=%s", (uid,))

                    extra_death = {}
                    broadcast = handle_death_log(uid, full_s['depth'], u['level'], u['username'], full_s['buffer_coins'], cursor=cur)
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
