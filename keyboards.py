import cache_db
from telebot import types
import time
import config
from config import LEVELS, PRICES, EQUIPMENT_DB, SLOTS, CURSED_CHEST_DROPS
from modules.services.crafting import crafting_service

# =============================================================
# ⚙️ ГЕНЕРАТОРЫ UI
# =============================================================

def get_progress_bar(current, total, length=10):
    if total == 0: return "░" * length
    percent = current / total
    filled_length = int(length * percent)
    filled = "█" * filled_length
    return filled + "░" * (length - filled_length)

# =============================================================
# 🌌 ГЛАВНЫЙ ТЕРМИНАЛ
# =============================================================

def glitch_question_answers(answers_list):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for idx, ans in enumerate(answers_list):
        markup.add(types.InlineKeyboardButton(ans['text'], callback_data=f"glitch_ans_{idx}"))
    return markup

def main_menu(u):
    import time
    import database as db
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # --- PHASE 1 RESTRICTION ---
    if u.get('onboarding_stage', 0) == 1:
        m.add(types.InlineKeyboardButton(f"👤 ПРОФИЛЬ", callback_data="profile"))
        return m

    # 1. Энергия
    eq_items = cache_db.get_cached_state(f"eq_{uid}", lambda: db.get_equipped_items(uid), ttl=10.0) or {}


    is_glitched = u.get('is_glitched', False)
    # New check: specific visual_distortion buff
    is_visual_dist = (u.get('anomaly_buff_type') == 'visual_distortion' and float(u.get('anomaly_buff_expiry') or 0) > time.time())

    sync_btn = "💠 СИНХРОН"
    signal_btn = "📡 СИГНАЛ"
    raid_btn = "─── 🌑 НУЛЕВОЙ СЛОЙ ───"
    profile_btn = "👤 ПРОФИЛЬ"
    inv_btn = "🎒 ИНВЕНТАРЬ"

    if is_glitched or is_visual_dist:
        sync_btn = "0101 СИНХРОН"
        signal_btn = "1010 СИГНАЛ"
        raid_btn = "─── [БИТЫЕ ДАННЫЕ] ───"
        profile_btn = "👤 П̷Р̷О̷Ф̷И̷Л̷Ь̷"
        inv_btn = "🎒 И̷Н̷В̷Е̷Н̷Т̷А̷Р̷Ь̷"


    if eq_items.get('head') == 'crown_paranoia':
        m.add(types.InlineKeyboardButton(f"🚫 {sync_btn} (BLOCKED)", callback_data="dummy"),
              types.InlineKeyboardButton(f"🚫 {signal_btn} (BLOCKED)", callback_data="dummy"))
    else:
        m.add(types.InlineKeyboardButton(sync_btn, callback_data="get_protocol"),
              types.InlineKeyboardButton(signal_btn, callback_data="get_signal"))
    
    m.add(types.InlineKeyboardButton(raid_btn, callback_data="zero_layer_menu"))


    current_lvl = int(u.get('level', 1) or 1)

    # PVP
    if current_lvl > config.QUARANTINE_LEVEL:
        m.add(types.InlineKeyboardButton("🌐 СЕТЕВАЯ ВОЙНА", callback_data="pvp_menu"))
    
    # [MODULE 5] Врата Эйдоса
    if current_lvl >= 10:
        m.add(types.InlineKeyboardButton("👁‍🗨 ВРАТА ЭЙДОСА", callback_data="eidos_room_menu"))

    # 3. Персонаж
    next_lvl_xp = LEVELS.get(current_lvl + 1, 999999)
    base_xp = LEVELS.get(current_lvl, 0)
    xp_in_level = max(0, int(u.get('xp', 0) or 0) - base_xp)
    needed = max(1, next_lvl_xp - base_xp)
    
    m.add(types.InlineKeyboardButton(f"{profile_btn} [{current_lvl}]", callback_data="profile"),
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop_menu"))

    m.add(types.InlineKeyboardButton(inv_btn, callback_data="inventory"), types.InlineKeyboardButton("📦 ВЕБ-ИНВЕНТАРЬ", web_app=types.WebAppInfo(url=f"{config.WEBHOOK_URL}/inventory")))
          
    # 4. Рейтинг и Социум
    m.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"),
          types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"))
          
    # 5. Знания & Гайды
    m.add(types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_menu"),
          types.InlineKeyboardButton("📚 ГАЙД", callback_data="guide"))

    m.add(types.InlineKeyboardButton("✉️ ОБРАТНАЯ СВЯЗЬ", callback_data="feedback_menu"))

    # --- DYNAMIC BUTTONS ---
    if u.get('shadow_broker_expiry', 0) > time.time():
        m.add(types.InlineKeyboardButton("🕶 ТЕНЕВОЙ БРОКЕР", callback_data="shadow_broker_menu"))

    # Check for cache (active or in inventory)
    has_cache_active = u.get('encrypted_cache_unlock_time', 0) > 0
    has_cache_item = cache_db.get_cached_state(f"inv_count_{uid}_encrypted_cache", lambda: db.get_item_count(uid, "encrypted_cache"), ttl=10.0) > 0

    if has_cache_active or has_cache_item:
        status_icon = "🔓" if (has_cache_active and time.time() >= u['encrypted_cache_unlock_time']) else "🔐"
        m.add(types.InlineKeyboardButton(f"{status_icon} ДЕШИФРАТОР", callback_data="decrypt_menu"))

    if u.get('is_admin') or str(uid) == str(config.ADMIN_ID):
        m.add(types.InlineKeyboardButton("⚡️ GOD MODE ⚡️", callback_data="admin_panel"))
        
    return m

# =============================================================
# 👤 ПРОФИЛЬ
# =============================================================

def profile_menu(u, has_accel=False, has_purification=False):
    m = types.InlineKeyboardMarkup(row_width=1)
    
    # Фракция
    if int(u.get('level', 1) or 1) >= 2:
        m.add(types.InlineKeyboardButton("🧬 ФРАКЦИЯ", callback_data="change_path_menu"))

    # Ускоритель
    if has_accel:
        m.add(types.InlineKeyboardButton("⚡️ АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accelerator"))

    # Очищение (Hard Reset)
    if has_purification:
        m.add(types.InlineKeyboardButton("🔮 АКТИВИРОВАТЬ ОЧИЩЕНИЕ", callback_data="activate_purification"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🎒 ИНВЕНТАРЬ (RPG UI)
# =============================================================

def inventory_menu(items, equipped, dismantle_mode=False, category='equip', has_legacy=False, uid=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Tabs
    m.add(types.InlineKeyboardButton(f"{'✅' if category=='equip' else ''} СНАРЯЖЕНИЕ", callback_data="inv_cat_equip"),
          types.InlineKeyboardButton(f"{'✅' if category=='consumable' else ''} РАСХОДНИКИ", callback_data="inv_cat_consumable"))

    mode_btn = "♻️ РЕЖИМ РАЗБОРА: ВКЛ" if dismantle_mode else "♻️ РАЗОБРАТЬ (вернешь от стоимости 10%)"
    mode_cb = "inv_mode_normal" if dismantle_mode else "inv_mode_dismantle"
    m.add(types.InlineKeyboardButton(mode_btn, callback_data=mode_cb))

    if has_legacy:
        m.add(types.InlineKeyboardButton("♻️ ПРЕОБРАЗОВАТЕЛЬ", callback_data="convert_legacy"))

    if (category == 'equip') and equipped:
        m.add(types.InlineKeyboardButton("─── 🛡 НАДЕТО ───", callback_data="dummy"))
        for slot, item_id in equipped.items():
            name = EQUIPMENT_DB.get(item_id, {}).get('name', '???')
            if not dismantle_mode:
                 m.add(types.InlineKeyboardButton(f"⬇️ {SLOTS.get(slot, slot)}: {name}", callback_data=f"view_item_eq_{slot}"))
    
    # Filter items
    filtered = []
    if items:
        if category == 'all': filtered = items
        elif category == 'equip': filtered = [i for i in items if i['item_id'] in EQUIPMENT_DB]
        elif category == 'consumable': filtered = [i for i in items if i['item_id'] not in EQUIPMENT_DB]

    if filtered:
        m.add(types.InlineKeyboardButton("─── 📦 РЮКЗАК ───", callback_data="dummy"))
        if category == 'equip' and not dismantle_mode:
            # Stacking logic for unequipped gear
            groups = {}
            for i in filtered:
                iid = i['item_id']
                if iid not in groups: groups[iid] = []
                groups[iid].append(i)

            for iid, group in groups.items():
                first = group[0]
                total_qty = sum(item['quantity'] for item in group)
                inv_id = first['id']
                durability = first.get('durability', 100)
                name = EQUIPMENT_DB[iid]['name']

                craft_icon = ' 🛠' if uid and crafting_service.can_craft(uid, iid) else ''
                display_name = f"{name} [{durability}]"
                if total_qty > 1:
                    display_name += f" (x{total_qty})"
                display_name += craft_icon

                m.add(types.InlineKeyboardButton(f"⬆️ {display_name}", callback_data=f"view_item_{inv_id}"))
        else:
            # Original individual/consumable logic (indented)
            for i in filtered:
                item_id = i['item_id']
                qty = i['quantity']
                inv_id = i.get('id')
                durability = i.get('durability', 100)

                if item_id in EQUIPMENT_DB:
                    name = EQUIPMENT_DB[item_id]['name']
                else:
                    info = config.ITEMS_INFO.get(item_id, {})
                    name = info.get('name', item_id)

                display_name = f"{name}"
                if item_id in EQUIPMENT_DB:
                    display_name += f" [{durability}]"
                elif qty > 1:
                    display_name += f" (x{qty})"

                if dismantle_mode:
                    m.add(types.InlineKeyboardButton(f"♻️ РАЗОБРАТЬ: {display_name}", callback_data=f"dismantle_{inv_id}"))
                else:
                    if item_id in EQUIPMENT_DB:
                        m.add(types.InlineKeyboardButton(f"⬆️ {display_name}", callback_data=f"view_item_{inv_id}"))
                    elif item_id == 'admin_key':
                        m.add(types.InlineKeyboardButton(f"🔴 ЮЗНУТЬ: {display_name}", callback_data="use_admin_key"))
                    else:
                        m.add(types.InlineKeyboardButton(f"{display_name}", callback_data=f"view_item_{inv_id}"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🎰 ЧЕРНЫЙ РЫНОК
# =============================================================

def shop_category_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🎁 ЛУТБОКС (GACHA)", callback_data="shop_gacha_menu"))
    m.add(types.InlineKeyboardButton("⚔️ ОРУЖИЕ", callback_data="shop_cat_weapon"),
          types.InlineKeyboardButton("👕 БРОНЯ", callback_data="shop_cat_armor"))
    m.add(types.InlineKeyboardButton("💾 ЧИПЫ", callback_data="shop_cat_chip"),
          types.InlineKeyboardButton("📦 РАСХОДНИКИ", callback_data="shop_cat_consumables"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def gacha_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"🎁 ОТКРЫТЬ (1000 BC)", callback_data="buy_gacha"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="shop_menu"))
    return m

def shop_section_menu(category):
    m = types.InlineKeyboardMarkup(row_width=2)

    if category == 'consumables':
        m.add(types.InlineKeyboardButton(f"🧭 КОМПАС ({PRICES['compass']} BC)", callback_data="view_shop_compass"),
              types.InlineKeyboardButton(f"🔑 КЛЮЧ ({PRICES['master_key']} BC)", callback_data="view_shop_master_key"))
        m.add(types.InlineKeyboardButton(f"🔋 БАТАРЕЯ ({PRICES['battery']} BC)", callback_data="view_shop_battery"),
              types.InlineKeyboardButton(f"🛡 ЭГИДА ({PRICES['aegis']} BC)", callback_data="view_shop_aegis"))
        m.add(types.InlineKeyboardButton(f"💉 СТИМУЛЯТОР ({PRICES['neural_stimulator']} BC)", callback_data="view_shop_neural_stimulator"),
              types.InlineKeyboardButton(f"💣 EMP-ЗАРЯД ({PRICES['emp_grenade']} BC)", callback_data="view_shop_emp_grenade"))
        m.add(types.InlineKeyboardButton(f"🌫 СТЕЛС-СПРЕЙ ({PRICES['stealth_spray']} BC)", callback_data="view_shop_stealth_spray"),
              types.InlineKeyboardButton(f"🌀 СТИРАТЕЛЬ ({PRICES['memory_wiper']} BC)", callback_data="view_shop_memory_wiper"))
        m.add(types.InlineKeyboardButton(f"🪛 ДАТА-ШИП ({PRICES['data_spike']} BC)", callback_data="view_shop_data_spike"),
              types.InlineKeyboardButton(f"👁‍🗨 КЛЮЧ БЕЗДНЫ ({PRICES['abyssal_key']} BC)", callback_data="view_shop_abyssal_key"))
        m.add(types.InlineKeyboardButton(f"📡 ТАКТИЧЕСКИЙ СКАНЕР ({PRICES['tactical_scanner']} BC)", callback_data="view_shop_tactical_scanner"))
        # Special Items
        m.add(types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} XP)", callback_data="view_shop_cryo"),
              types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="view_shop_accel"))
        m.add(types.InlineKeyboardButton(f"♻️ СИНХРОН ОЧИЩЕНИЯ ({PRICES['purification_sync']} BC)", callback_data="view_shop_purification_sync"))

    elif category in ['weapon', 'armor', 'chip']:
        items = []
        for k, v in EQUIPMENT_DB.items():
            if v.get('slot') == category and k not in CURSED_CHEST_DROPS:
                items.append((k, v))
        items.sort(key=lambda x: x[1]['price'])
        for k, v in items:
            m.add(types.InlineKeyboardButton(f"{v['name']} ({v['price']} BC)", callback_data=f"view_shop_{k}"))

    m.add(types.InlineKeyboardButton("🔙 К КАТЕГОРИЯМ", callback_data="shop_menu"))
    return m

# =============================================================
# 🕹 КОКПИТ РЕЙДА
# =============================================================

def raid_welcome_keyboard(cost):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🚀 ВЫБРАТЬ ТОЧКУ ВХОДА", callback_data="raid_select_depth"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back"))
    return m

def raid_depth_selection_menu(max_depth, cost):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🏙 0м (Начало) - {cost} XP", callback_data="raid_start_0"))
    if max_depth >= 300:
        m.add(types.InlineKeyboardButton(f"🏭 0-300м (Микс) - {cost} XP", callback_data="raid_start_range_0_300"))
    if max_depth >= 600:
        m.add(types.InlineKeyboardButton(f"🕸 300-600м (Глубина) - {cost} XP", callback_data="raid_start_range_300_600"))
    if max_depth >= 50: m.add(types.InlineKeyboardButton(f"🏭 50м - {cost} XP", callback_data="raid_start_50"))
    if max_depth >= 150: m.add(types.InlineKeyboardButton(f"🌃 150м - {cost} XP", callback_data="raid_start_150"))
    if max_depth >= 300: m.add(types.InlineKeyboardButton(f"🕸 300м - {cost} XP", callback_data="raid_start_300"))
    if max_depth >= 500: m.add(types.InlineKeyboardButton(f"🌌 500м - {cost} XP", callback_data="raid_start_500"))
    if max_depth > 0:
        m.add(types.InlineKeyboardButton(f"🕳 {max_depth}м (Рекорд) - {cost} XP", callback_data=f"raid_start_{max_depth}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="zero_layer_menu"))
    return m

def raid_action_keyboard(xp_cost, event_type='neutral', has_key=False, consumables={}, has_data_spike=False, has_architect_key=False):
    m = types.InlineKeyboardMarkup()
    battery_count = consumables.get('battery', 0)
    stimulator_count = consumables.get('neural_stimulator', 0)

    if event_type == 'combat':
        m.row(types.InlineKeyboardButton("⚔️ АТАКА", callback_data="combat_attack"),
              types.InlineKeyboardButton("🏃 БЕЖАТЬ", callback_data="combat_run"))
        emp_count = consumables.get('emp_grenade', 0)
        stealth_count = consumables.get('stealth_spray', 0)
        wiper_count = consumables.get('memory_wiper', 0)
        combat_items = []
        if emp_count > 0:
            combat_items.append(types.InlineKeyboardButton(f"💣 EMP (x{emp_count})", callback_data="combat_use_emp"))
        if stealth_count > 0:
            combat_items.append(types.InlineKeyboardButton(f"👻 STEALTH (x{stealth_count})", callback_data="combat_use_stealth"))
        if wiper_count > 0:
            combat_items.append(types.InlineKeyboardButton(f"🧹 WIPER (x{wiper_count})", callback_data="combat_use_wiper"))
        if combat_items:
             m.add(*combat_items)
        if battery_count > 0:
            m.add(types.InlineKeyboardButton(f"🔋 БАТАРЕЯ (x{battery_count})", callback_data="raid_use_battery"))
        if stimulator_count > 0:
            m.add(types.InlineKeyboardButton(f"💉 СТИМУЛЯТОР (x{stimulator_count})", callback_data="raid_use_stimulator"))
        return m

    if event_type == 'locked_chest':
        m.add(types.InlineKeyboardButton("🔓 ОТКРЫТЬ СУНДУК", callback_data="raid_open_chest"))
        if has_data_spike:
            m.add(types.InlineKeyboardButton("🪛 ВЗЛОМ (ДАТА-ШИП)", callback_data="raid_hack_chest"))
    if event_type == 'cursed_chest':
        m.add(types.InlineKeyboardButton("👁‍🗨 ОТКРЫТЬ (КЛЮЧ БЕЗДНЫ)", callback_data="raid_open_chest"))
        if has_data_spike:
            m.add(types.InlineKeyboardButton("🪛 ВЗЛОМ (ДАТА-ШИП 50%)", callback_data="raid_hack_chest"))
    if event_type == 'found_body':
        m.add(types.InlineKeyboardButton("💀 ОБЫСКАТЬ ТЕЛО", callback_data="raid_claim_body"))
    if event_type == 'anomaly_terminal':
        m.add(types.InlineKeyboardButton("🩸 СТАВКА: 30% HP", callback_data="anomaly_bet_hp"),
              types.InlineKeyboardButton("🎒 СТАВКА: 50% ЛУТА", callback_data="anomaly_bet_buffer"))
    if battery_count > 0:
        m.add(types.InlineKeyboardButton(f"🔋 ИСПОЛЬЗОВАТЬ БАТАРЕЮ (x{battery_count})", callback_data="raid_use_battery"))
    if stimulator_count > 0:
        m.add(types.InlineKeyboardButton(f"💉 ИСПОЛЬЗОВАТЬ СТИМУЛЯТОР (x{stimulator_count})", callback_data="raid_use_stimulator"))
    if has_architect_key:
        m.add(types.InlineKeyboardButton("🟠 ГЛУБОКОЕ СКАНЕРИОВАНИЕ", callback_data="raid_use_architect_key"))
    m.add(types.InlineKeyboardButton(f"👣 ШАГ ВГЛУБЬ (-{xp_cost} XP)", callback_data="raid_step"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    m = types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        clean_opt = opt[:30]
        m.add(types.InlineKeyboardButton(f"› {clean_opt}", callback_data=f"r_check_{clean_opt[:20]}"))
    return m

# =============================================================
# 🧬 ВЫБОР ФРАКЦИИ
# =============================================================

def path_selection_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("🏦 МАТЕРИЯ [+20% ДЕНЕГ]", callback_data="set_path_money"),
        types.InlineKeyboardButton("🧠 РАЗУМ [+10 ЗАЩИТЫ]", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🤖 ТЕХНО [+10 УДАЧИ]", callback_data="set_path_tech")
    )
    return m

def change_path_keyboard(cost):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton(f"🏦 МАТЕРИЯ (-{cost} XP)", callback_data="set_path_money"),
        types.InlineKeyboardButton(f"🧠 РАЗУМ (-{cost} XP)", callback_data="set_path_mind"),
        types.InlineKeyboardButton(f"🤖 ТЕХНО (-{cost} XP)", callback_data="set_path_tech")
    )
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="profile"))
    return m

def faction_confirm_menu(path):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_path_{path}"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="change_path_menu"))
    return m

# =============================================================
# 📓 ДНЕВНИК & ГАЙД
# =============================================================

def diary_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("✍️ НОВАЯ ЗАПИСЬ", callback_data="diary_new"),
        types.InlineKeyboardButton("📖 МОИ МЫСЛИ", callback_data="diary_read_0"),
        types.InlineKeyboardButton(f"💾 АРХИВ (500 XP)", callback_data="archive_list")
    )
    m.add(types.InlineKeyboardButton("🏆 ДОСТИЖЕНИЯ", callback_data="achievements_list"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def archive_nav(page, total_pages):
    m = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    if page > 0: btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"archive_list_{page-1}"))
    btns.append(types.InlineKeyboardButton(f"{page+1} / {total_pages}", callback_data="dummy"))
    if page < total_pages - 1: btns.append(types.InlineKeyboardButton("➡️", callback_data=f"archive_list_{page+1}"))
    m.add(*btns)
    m.add(types.InlineKeyboardButton("🔙 В МЕНЮ ДНЕВНИКА", callback_data="diary_menu"))
    return m

def diary_read_nav(page, total_pages):
    m = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    if page > 0: btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"diary_read_{page-1}"))
    btns.append(types.InlineKeyboardButton(f"{page+1} / {total_pages}", callback_data="dummy"))
    if page < total_pages - 1: btns.append(types.InlineKeyboardButton("➡️", callback_data=f"diary_read_{page+1}"))
    m.add(*btns)
    m.add(types.InlineKeyboardButton("🔙 В МЕНЮ ДНЕВНИКА", callback_data="diary_menu"))
    return m

def achievements_nav(page, total_pages):
    m = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    if page > 0: btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"achievements_list_{page-1}"))
    btns.append(types.InlineKeyboardButton(f"{page+1} / {total_pages}", callback_data="dummy"))
    if page < total_pages - 1: btns.append(types.InlineKeyboardButton("➡️", callback_data=f"achievements_list_{page+1}"))
    m.add(*btns)
    m.add(types.InlineKeyboardButton("🔙 В МЕНЮ ДНЕВНИКА", callback_data="diary_menu"))
    return m

def guide_menu(page_key='intro', u=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👋 НАЧАЛО", callback_data="guide_page_intro"),
          types.InlineKeyboardButton("🚀 РЕЙДЫ", callback_data="guide_page_raids"))
    m.add(types.InlineKeyboardButton("⚔️ БОЙ", callback_data="guide_page_combat"),
          types.InlineKeyboardButton("📊 ПРОКАЧКА", callback_data="guide_page_stats"))
    m.add(types.InlineKeyboardButton("🎒 ПРЕДМЕТЫ", callback_data="guide_page_items"),
          types.InlineKeyboardButton("🛠 КРАФТ", callback_data="guide_page_crafting"))
    m.add(types.InlineKeyboardButton("💰 ЭКОНОМИКА", callback_data="guide_page_economy"),
          types.InlineKeyboardButton("🔓 ВЗЛОМ (PvP)", callback_data="guide_page_pvp"))
    m.add(types.InlineKeyboardButton("🤝 СИНДИКАТ", callback_data="guide_page_social"),
          types.InlineKeyboardButton("⚡️ СОВЕТЫ", callback_data="guide_page_tips"))

    if u:
        history = u.get('quiz_history', '') or ''
        if "q1" in history and "q2" in history and "q3" in history and "q4" in history:
            pass
        else:
            m.add(types.InlineKeyboardButton("🧠 QUIZ (ВИКТОРИНА)", callback_data="start_quiz"))
    else:
        m.add(types.InlineKeyboardButton("🧠 QUIZ (ВИКТОРИНА)", callback_data="start_quiz"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def back_button():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# ⚡️ ADMIN
# =============================================================

def admin_main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👥 ПОЛЬЗОВАТЕЛИ", callback_data="admin_menu_users"),
          types.InlineKeyboardButton("📝 КОНТЕНТ", callback_data="admin_menu_content"))
    m.add(types.InlineKeyboardButton("📢 РАССЫЛКА", callback_data="admin_menu_broadcast"),
          types.InlineKeyboardButton("⚙️ СИСТЕМА", callback_data="admin_menu_system"))
    m.add(types.InlineKeyboardButton("🕶 ВЫЗВАТЬ БРОКЕРА", callback_data="admin_summon_broker"),
          types.InlineKeyboardButton("🗑 ЧИСТКА ИНВЕНТАРЯ", callback_data="admin_fix_inventory"))
    m.add(types.InlineKeyboardButton("📚 СПРАВКА", callback_data="admin_guide"))
    m.add(types.InlineKeyboardButton("🔙 ВЫХОД", callback_data="back"))
    return m

def admin_inventory_keyboard(items):
    m = types.InlineKeyboardMarkup(row_width=1)
    if not items:
        m.add(types.InlineKeyboardButton("✅ ИНВЕНТАРЬ ПУСТ", callback_data="dummy"))
    for i in items:
        item_id = i['item_id']
        qty = i['quantity']
        m.add(types.InlineKeyboardButton(f"🗑 DELETE: {item_id} (x{qty})", callback_data=f"admin_del_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
    return m

def admin_users_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("➕ НАЗНАЧИТЬ АДМИНА", callback_data="admin_grant_admin"),
          types.InlineKeyboardButton("➖ СНЯТЬ АДМИНА", callback_data="admin_revoke_admin"))
    m.add(types.InlineKeyboardButton("💰 ВЫДАТЬ РЕСУРСЫ", callback_data="admin_give_res"),
          types.InlineKeyboardButton("🎁 ВЫДАТЬ ПРЕДМЕТ", callback_data="admin_give_item_menu"))
    m.add(types.InlineKeyboardButton("👥 СПИСОК ИГРОКОВ", callback_data="admin_user_list"),
          types.InlineKeyboardButton("✉️ ЛИЧНОЕ СООБЩЕНИЕ", callback_data="admin_dm_user"))
    m.add(types.InlineKeyboardButton("♻️ СБРОС (Reset)", callback_data="admin_reset_user"),
          types.InlineKeyboardButton("🗑 УДАЛИТЬ (Hard Delete)", callback_data="admin_delete_user"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
    return m

def admin_content_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("➕ ЗАГАДКА", callback_data="admin_add_riddle"),
          types.InlineKeyboardButton("➕ ПРОТОКОЛ", callback_data="admin_add_content"),
          types.InlineKeyboardButton("➕ СИГНАЛ", callback_data="admin_add_signal"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
    return m

def admin_broadcast_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📢 ВСЕМ ИГРОКАМ", callback_data="admin_broadcast"),
          types.InlineKeyboardButton("📡 В КАНАЛ", callback_data="admin_post_channel"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
    return m

def admin_system_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("📜 SQL ЗАПРОС", callback_data="admin_sql"))
    m.add(types.InlineKeyboardButton("🔓 Сброс блока игрока (ID)", callback_data="admin_unstick_user"))
    m.add(types.InlineKeyboardButton("🌐 Сброс блока у всех", callback_data="admin_unstick_all"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
    return m

def admin_unstick_all_confirm():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✅ Да, сбросить всех", callback_data="admin_unstick_all_exec"))
    m.add(types.InlineKeyboardButton("🔙 Отмена", callback_data="admin_menu_system"))
    return m


def admin_item_select():
    m = types.InlineKeyboardMarkup(row_width=2)
    for k, v in EQUIPMENT_DB.items():
        m.add(types.InlineKeyboardButton(v['name'], callback_data=f"adm_give_{k}"))
    m.add(types.InlineKeyboardButton("🔑 MASTER KEY", callback_data="adm_give_master_key"),
          types.InlineKeyboardButton("🧭 COMPASS", callback_data="adm_give_compass"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="admin_menu_users"))
    return m

def item_details_keyboard(item_id, is_owned=True, is_equipped=False, durability=None, inv_id=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    if durability is not None and durability <= 0:
        if inv_id:
            m.add(types.InlineKeyboardButton("🛠 ПОЧИНИТЬ (15% цены)", callback_data=f"repair_{inv_id}"))
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ (5% цены)", callback_data=f"dismantle_{inv_id}"))
    else:
        if is_equipped:
            info = EQUIPMENT_DB.get(item_id)
            slot = info['slot'] if info else None
            if slot:
                 m.add(types.InlineKeyboardButton("📦 СНЯТЬ", callback_data=f"unequip_{slot}"))
        else:
            if item_id in EQUIPMENT_DB:
                 cb = f"equip_{inv_id}" if inv_id else f"equip_{item_id}"
                 m.add(types.InlineKeyboardButton("🛡 НАДЕТЬ", callback_data=cb))
            else:
                 m.add(types.InlineKeyboardButton("⚡️ ИСПОЛЬЗОВАТЬ", callback_data=f"use_item_{item_id}"))
        if inv_id:
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"dismantle_{inv_id}"))
        else:
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"dismantle_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="inventory"))
    return m

def shop_item_details_keyboard(item_id, price, currency):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"💸 КУПИТЬ ({price} {currency.upper()})", callback_data=f"buy_{item_id}"))
    m.add(types.InlineKeyboardButton("🛒 УКАЗАТЬ КОЛИЧЕСТВО", callback_data=f"buy_qty_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="shop_menu"))
    return m

def shadow_shop_menu(items):
    m = types.InlineKeyboardMarkup(row_width=1)
    for item in items:
        price_txt = f"{item['price']} {'XP' if item['currency']=='xp' else 'BC'}"
        m.add(types.InlineKeyboardButton(f"{item['name']} - {price_txt}", callback_data=f"view_shadow_{item['item_id']}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def shadow_item_details_keyboard(item_id, price, currency):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"💸 КУПИТЬ ({price} {currency.upper()})", callback_data=f"buy_shadow_{item_id}"))
    m.add(types.InlineKeyboardButton("🛒 УКАЗАТЬ КОЛИЧЕСТВО", callback_data=f"buy_shadow_qty_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="shadow_broker_menu"))
    return m

def decrypt_menu(status):
    m = types.InlineKeyboardMarkup(row_width=1)
    if status == "ready_to_start":
        m.add(types.InlineKeyboardButton("🔐 НАЧАТЬ РАСШИФРОВКУ", callback_data="decrypt_start"))
    elif status == "ready_to_claim":
        m.add(types.InlineKeyboardButton("🔓 ОТКРЫТЬ КОНТЕЙНЕР", callback_data="decrypt_claim"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def anomaly_keyboard():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🩸 СТАВКА: 30% HP", callback_data="anomaly_bet_hp"),
          types.InlineKeyboardButton("🎒 СТАВКА: 50% ЛУТА", callback_data="anomaly_bet_buffer"))
    m.add(types.InlineKeyboardButton("🏃 УЙТИ", callback_data="raid_step"))
    return m

# =============================================================
# 🧩 ONBOARDING / СБОРКА
# =============================================================

def onboarding_phase2_keyboard():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="onboarding_signal"),
          types.InlineKeyboardButton("💠 СИНХРОН", callback_data="onboarding_synch"))
    return m

def onboarding_phase3_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("✅ Я ПОНЯЛ", callback_data="onboarding_understood"))
    return m

def onboarding_exam_keyboard():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⚔️ ПРОЙТИ ИСПЫТАНИЕ", callback_data="onboarding_start_exam"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🌐 PVP (СЕТЕВАЯ ВОЙНА v2.0)
# =============================================================

def pvp_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"📡 ПОИСК ЦЕЛИ ({config.PVP_FIND_COST} XP)", callback_data="pvp_search"))
    m.add(types.InlineKeyboardButton("🛡 НАСТРОИТЬ ЗАЩИТУ", callback_data="pvp_config"))
    m.add(types.InlineKeyboardButton("🎒 ИНВЕНТАРЬ ПО", callback_data="pvp_inventory"))
    m.add(types.InlineKeyboardButton("🏪 МАГАЗИН СОФТА", callback_data="pvp_shop"))
    m.add(types.InlineKeyboardButton("🩸 ВЕНДЕТТА", callback_data="pvp_vendetta"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def pvp_config_menu(deck):
    m = types.InlineKeyboardMarkup(row_width=3)
    slots_row = []
    for i in range(1, 4):
        if i <= deck['slots']:
            sid = deck['config'].get(str(i))
            icon = "🕸"
            if sid and sid in config.SOFTWARE_DB:
                icon = config.SOFTWARE_DB[sid]['icon']
            slots_row.append(types.InlineKeyboardButton(f"[{icon}] Слот {i}", callback_data=f"pvp_slot_{i}"))
        else:
            slots_row.append(types.InlineKeyboardButton("🔒", callback_data=f"pvp_slot_locked"))
    m.add(*slots_row)
    next_lvl = deck['level'] + 1
    if next_lvl in config.DECK_UPGRADES:
        cost = config.DECK_UPGRADES[next_lvl]['cost']
        m.add(types.InlineKeyboardButton(f"🔼 АПГРЕЙД ДЕКИ ({cost} BC)", callback_data="pvp_upgrade_deck"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_inventory_menu(inventory, active_hardware={}):
    m = types.InlineKeyboardMarkup(row_width=1)
    if not inventory:
        m.add(types.InlineKeyboardButton("✅ ИНВЕНТАРЬ ПУСТ", callback_data="dummy"))
    def add_separator(text):
        m.add(types.InlineKeyboardButton(f"─── {text} ───", callback_data="dummy"))
    software = [i for i in inventory if i.get('category') == 'software']
    hardware = [i for i in inventory if i.get('category') == 'hardware']
    if software:
        add_separator("💾 ПРОГРАММЫ")
        for item in software:
            item_id = item['id']
            name = item['name']
            qty = item['quantity']
            icon = item.get('icon', '💾')
            type_str = item.get('type', 'UNK').upper()
            m.add(types.InlineKeyboardButton(f"{icon} {name} [{type_str}] x{qty}", callback_data="dummy"))
            m.add(types.InlineKeyboardButton(f"♻️ РАЗОБРАТЬ ({name})", callback_data=f"pvp_dismantle_{item_id}"))
    if hardware:
        add_separator("🛠 ЖЕЛЕЗО")
        for item in hardware:
            item_id = item['id']
            name = item['name']
            qty = item['quantity']
            icon = item.get('icon', '🛠')
            is_active = active_hardware.get(item_id, False)
            state_text = "🟢 ONLINE" if is_active else "🔴 OFFLINE"
            toggle_action = "pvp_hw_unequip_" if is_active else "pvp_hw_equip_"
            toggle_btn = f"🛑 ВЫКЛ" if is_active else f"⚡️ ВКЛ"
            m.add(types.InlineKeyboardButton(f"{icon} {name} (x{qty}) | {state_text}", callback_data="dummy"))
            m.row(
                types.InlineKeyboardButton(toggle_btn, callback_data=f"{toggle_action}{item_id}"),
                types.InlineKeyboardButton("♻️ УТИЛЬ", callback_data=f"pvp_dismantle_{item_id}")
            )
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_software_select_menu(inventory, slot_id, mode='defense'):
    m = types.InlineKeyboardMarkup(row_width=1)
    cb_prefix = "pvp_equip_" if mode == 'defense' else "pvp_atk_sel_"
    m.add(types.InlineKeyboardButton("🚫 ОЧИСТИТЬ СЛОТ", callback_data=f"{cb_prefix}{slot_id}_empty"))
    if not inventory:
        m.add(types.InlineKeyboardButton("У вас нет программ", callback_data="dummy"))
    for item in inventory:
        txt = f"{item['name']} ({item['type'].upper()})"
        m.add(types.InlineKeyboardButton(txt, callback_data=f"{cb_prefix}{slot_id}_{item['id']}"))
    back_cb = "pvp_config" if mode == 'defense' else "pvp_attack_prep"
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data=back_cb))
    return m

def pvp_shop_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("─── 💾 ПРОГРАММЫ ───", callback_data="dummy"))
    for sid, info in config.SOFTWARE_DB.items():
        txt = f"{info['name']} — {info['cost']} BC"
        m.add(types.InlineKeyboardButton(txt, callback_data=f"pvp_buy_{sid}"))
    m.add(types.InlineKeyboardButton("─── 🛠 ЖЕЛЕЗО ───", callback_data="dummy"))
    p_firewall = PRICES.get('firewall', 1000)
    p_ice = PRICES.get('ice_trap', 2000)
    p_proxy = PRICES.get('proxy_server', 500)
    m.add(types.InlineKeyboardButton(f"🛡 ФАЙРВОЛ ({p_firewall} BC)", callback_data="pvp_buy_hw_firewall"))
    m.add(types.InlineKeyboardButton(f"🪤 ICE-ЛОВУШКА ({p_ice} BC)", callback_data="pvp_buy_hw_ice_trap"))
    m.add(types.InlineKeyboardButton(f"🕶 ПРОКСИ ({p_proxy} XP)", callback_data="pvp_buy_hw_proxy_server"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_shop_confirm(sid, is_hardware=False):
    if is_hardware:
        from config import ITEMS_INFO
        info = ITEMS_INFO.get(sid, {})
        cost = PRICES.get(sid, 0)
        currency = "XP" if sid == "proxy_server" else "BC"
    else:
        info = config.SOFTWARE_DB[sid]
        cost = info['cost']
        currency = "BC"
    m = types.InlineKeyboardMarkup(row_width=2)
    cb_data = f"pvp_buy_confirm_hw_{sid}" if is_hardware else f"pvp_buy_confirm_{sid}"
    m.add(types.InlineKeyboardButton(f"✅ КУПИТЬ ({cost} {currency})", callback_data=cb_data))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="pvp_shop"))
    return m

def pvp_target_menu(target_uid, selected_slots={}):
    m = types.InlineKeyboardMarkup(row_width=3)
    slots_row = []
    for i in range(1, 4):
        sid = selected_slots.get(str(i))
        icon = "🕸"
        if sid and sid in config.SOFTWARE_DB:
            icon = config.SOFTWARE_DB[sid]['icon']
        slots_row.append(types.InlineKeyboardButton(f"[{icon}]", callback_data=f"pvp_atk_slot_{i}"))
    m.add(*slots_row)
    m.add(types.InlineKeyboardButton("☠️ НАЧАТЬ ВЗЛОМ", callback_data="pvp_execute_attack"))
    m.add(types.InlineKeyboardButton("🎲 СЛУЧАЙНЫЙ НАБОР", callback_data="pvp_atk_random"))
    m.add(types.InlineKeyboardButton("🔙 СБРОС ЦЕЛИ", callback_data="pvp_menu"))
    return m

def pvp_vendetta_menu(attackers):
    m = types.InlineKeyboardMarkup(row_width=1)
    if not attackers:
        m.add(types.InlineKeyboardButton("✅ СПИСОК ПУСТ", callback_data="dummy"))
    else:
        for a in attackers:
            log_id = a['id']
            if not log_id: continue
            name = a['username'] or a['first_name'] or "Unknown"
            stolen = a.get('stolen_coins', 0)
            success = a.get('success', False)
            is_revenged = a.get('is_revenged', False)
            try:
                time_ago = int((time.time() - a['timestamp']) / 3600)
                time_str = f"{time_ago}ч" if time_ago > 0 else "Сейчас"
            except:
                time_str = "?"
            from modules.services.utils import get_vip_prefix
            vip_name = get_vip_prefix(a['attacker_uid'], name).replace('<b>', '').replace('</b>', '')
            if not success:
                btn_text = f"🛡 {vip_name} | ⛔️ Blocked ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            elif is_revenged:
                btn_text = f"✅ {vip_name} | ♻️ {stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            else:
                btn_text = f"🩸 {vip_name} | -{stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            m.add(types.InlineKeyboardButton(btn_text, callback_data=cb))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_revenge_confirm(log_id, name):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"🩸 ОТОМСТИТЬ {name} (-50 XP)", callback_data=f"pvp_revenge_exec_{log_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_vendetta"))
    return m

def pvp_defense_shop():
    return pvp_shop_menu()

def leaderboard_menu(current_sort='xp', leaders=None):
    m = types.InlineKeyboardMarkup(row_width=2)
    txt_xp = "🏆 ОПЫТ"
    txt_depth = "🕳 ГЛУБИНА"
    txt_bio = "🩸 КАПИТАЛ"
    txt_spent = "💎 СИНДИКАТ"
    if current_sort == 'xp': txt_xp = f"✅ {txt_xp}"
    elif current_sort == 'depth': txt_depth = f"✅ {txt_depth}"
    elif current_sort == 'biocoin': txt_bio = f"✅ {txt_bio}"
    elif current_sort == 'spent': txt_spent = f"✅ {txt_spent}"

    m.add(types.InlineKeyboardButton("🔍 Найти досье (Паспорт Осколка)", callback_data="find_user_dossier_init"))

    m.add(
        types.InlineKeyboardButton(txt_xp, callback_data="lb_xp"),
        types.InlineKeyboardButton(txt_depth, callback_data="lb_depth")
    )
    m.add(
        types.InlineKeyboardButton(txt_bio, callback_data="lb_biocoin"),
        types.InlineKeyboardButton(txt_spent, callback_data="lb_spent")
    )
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ В МЕНЮ", callback_data="back"))
    return m

# =============================================================
# 👁‍🗨 КОМНАТА ЭЙДОСА (МОДУЛЬ 5, 6, 8)
# =============================================================

def eidos_tos_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("[ПРИНЯТЬ УСЛОВИЯ. НАЧАТЬ СКАНИРОВАНИЕ]", callback_data="eidos_tos_accept"),
        types.InlineKeyboardButton("[ОТМЕНА. Я НЕ ГОТОВ К ПРАВДЕ]", callback_data="eidos_tos_reject")
    )
    return markup

def eidos_room_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👁‍🗨 ПОЛУЧИТЬ ДОСЬЕ (100 ⭐️)", callback_data="eidos_buy_dossier"),
        types.InlineKeyboardButton("🔮 ВЕКТОР БУДУЩЕГО (250 ⭐️)", callback_data="eidos_buy_forecast"),
        types.InlineKeyboardButton("👁 Глас Абсолюта (500 ⭐️)", callback_data="eidos_buy_voice"),
        types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back")
    )
    return markup

def get_main_reply_keyboard(user):
    from telebot import types
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if int(user.get('level', 1) or 1) >= 10:
        m.add(types.KeyboardButton('👁‍🗨 Врата Эйдоса'), types.KeyboardButton('/start'))
    else:
        m.add(types.KeyboardButton('/start'))
    return m
