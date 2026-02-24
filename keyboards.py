from telebot import types
import time
import config
from config import LEVELS, PRICES, EQUIPMENT_DB, SLOTS, SCHOOLS, ARCHIVE_COST, GUIDE_PAGES, CURSED_CHEST_DROPS

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
    eq_items = db.get_equipped_items(uid)
    if eq_items.get('head') == 'crown_paranoia':
        m.add(types.InlineKeyboardButton("🚫 СИНХРОН (BLOCKED)", callback_data="dummy"),
              types.InlineKeyboardButton("🚫 СИГНАЛ (BLOCKED)", callback_data="dummy"))
    else:
        m.add(types.InlineKeyboardButton("💠 СИНХРОН", callback_data="get_protocol"),
              types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal"))
    
    # 2. Рейд
    m.add(types.InlineKeyboardButton("─── 🌑 НУЛЕВОЙ СЛОЙ ───", callback_data="zero_layer_menu"))

    # PVP
    if u['level'] > config.QUARANTINE_LEVEL:
        m.add(types.InlineKeyboardButton("🌐 СЕТЕВАЯ ВОЙНА", callback_data="pvp_menu"))
    
    # 3. Персонаж
    current_lvl = u['level']
    next_lvl_xp = LEVELS.get(current_lvl + 1, 999999)
    base_xp = LEVELS.get(current_lvl, 0)
    xp_in_level = max(0, u['xp'] - base_xp)
    needed = max(1, next_lvl_xp - base_xp)
    p_bar = get_progress_bar(xp_in_level, needed)
    
    m.add(types.InlineKeyboardButton(f"👤 ПРОФИЛЬ [{current_lvl}]", callback_data="profile"),
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop_menu"))

    m.add(types.InlineKeyboardButton("🎒 ИНВЕНТАРЬ", callback_data="inventory"))
          
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
    has_cache_item = db.get_item_count(uid, 'encrypted_cache') > 0

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
    if u['level'] >= 2:
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

def inventory_menu(items, equipped, dismantle_mode=False, category='equip', has_legacy=False):
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Tabs (Removed "ALL")
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
            # Assuming equipped items passed as a dict {slot: item_id}, but we might need durability?
            # Ideally equipped should be a dict of item details or fetch logic handles display.
            # Current caller passes `db.get_equipped_items(uid)` which returns {slot: item_id}.
            # We can't display durability here easily without fetching it again or changing caller.
            # For now, keep it simple or user can click to see details.
            if dismantle_mode:
                 pass
            else:
                 m.add(types.InlineKeyboardButton(f"⬇️ {SLOTS.get(slot, slot)}: {name}", callback_data=f"view_item_eq_{slot}"))
    
    # Filter items
    filtered = []
    if items:
        # 'all' removed from logic mostly, but keep for safety if passed
        if category == 'all': filtered = items
        elif category == 'equip': filtered = [i for i in items if i['item_id'] in EQUIPMENT_DB]
        elif category == 'consumable': filtered = [i for i in items if i['item_id'] not in EQUIPMENT_DB]

    if filtered:
        m.add(types.InlineKeyboardButton("─── 📦 РЮКЗАК ───", callback_data="dummy"))
        for i in filtered:
            item_id = i['item_id']
            qty = i['quantity']
            inv_id = i.get('id') # New unique ID
            durability = i.get('durability', 100)

            # Fetch nice name from config
            if item_id in EQUIPMENT_DB:
                name = EQUIPMENT_DB[item_id]['name']
            else:
                # Try ITEMS_INFO, fallback to item_id
                info = config.ITEMS_INFO.get(item_id, {})
                name = info.get('name', item_id)

            display_name = f"{name}"
            if item_id in EQUIPMENT_DB:
                display_name += f" [{durability}]"
            elif qty > 1:
                display_name += f" (x{qty})"

            if dismantle_mode:
                # Кнопка разбора
                m.add(types.InlineKeyboardButton(f"♻️ РАЗОБРАТЬ: {display_name}", callback_data=f"dismantle_{inv_id}"))
            else:
                if item_id in EQUIPMENT_DB:
                    # Use unique ID for equipment
                    m.add(types.InlineKeyboardButton(f"⬆️ {display_name}", callback_data=f"view_item_{inv_id}"))
                elif item_id == 'admin_key':
                    m.add(types.InlineKeyboardButton(f"🔴 ЮЗНУТЬ: {display_name}", callback_data="use_admin_key"))
                else:
                    # For consumables, we can still use inv_id as it refers to the stack
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
        # Sort by price cheap to expensive
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

    # Standard Points
    m.add(types.InlineKeyboardButton(f"🏙 0м (Начало) - {cost} XP", callback_data="raid_start_0"))

    # Biome Ranges
    if max_depth >= 300:
        m.add(types.InlineKeyboardButton(f"🏭 0-300м (Микс) - {cost} XP", callback_data="raid_start_range_0_300"))

    if max_depth >= 600:
        m.add(types.InlineKeyboardButton(f"🕸 300-600м (Глубина) - {cost} XP", callback_data="raid_start_range_300_600"))

    # Specific Checkpoints
    if max_depth >= 50: m.add(types.InlineKeyboardButton(f"🏭 50м - {cost} XP", callback_data="raid_start_50"))
    if max_depth >= 150: m.add(types.InlineKeyboardButton(f"🌃 150м - {cost} XP", callback_data="raid_start_150"))
    if max_depth >= 300: m.add(types.InlineKeyboardButton(f"🕸 300м - {cost} XP", callback_data="raid_start_300"))
    if max_depth >= 500: m.add(types.InlineKeyboardButton(f"🌌 500м - {cost} XP", callback_data="raid_start_500"))

    # Max Depth
    if max_depth > 0:
        m.add(types.InlineKeyboardButton(f"🕳 {max_depth}м (Рекорд) - {cost} XP", callback_data=f"raid_start_{max_depth}"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="zero_layer_menu"))
    return m

def raid_action_keyboard(xp_cost, event_type='neutral', has_key=False, consumables={}, has_data_spike=False):
    m = types.InlineKeyboardMarkup()
    
    battery_count = consumables.get('battery', 0)
    stimulator_count = consumables.get('neural_stimulator', 0)

    if event_type == 'combat':
        m.row(types.InlineKeyboardButton("⚔️ АТАКА", callback_data="combat_attack"),
              types.InlineKeyboardButton("🏃 БЕЖАТЬ", callback_data="combat_run"))

        # Combat Consumables
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

        # Healing in combat
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
            
    m.add(types.InlineKeyboardButton(f"👣 ШАГ ВГЛУБЬ (-{xp_cost} XP)", callback_data="raid_step"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    m = types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        # Truncate just in case, but keep clean
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
    # Changed to show details first via "set_path_" callbacks in logic if needed,
    # but here we follow the "Detailed Description" request.
    # The callback should trigger a message with details + "Confirm" button.
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
          types.InlineKeyboardButton("🔓 ВЗЛОМ", callback_data="guide_page_pvp"))
    m.add(types.InlineKeyboardButton("🤝 СИНДИКАТ", callback_data="guide_page_social"),
          types.InlineKeyboardButton("⚡️ СОВЕТЫ", callback_data="guide_page_tips"))

    # Check quiz availability (Hardcoded count for now, needs sync with handler)
    # Questions are: q1, q2, q3, q4
    if u:
        history = u.get('quiz_history', '') or ''
        answered_count = history.count(',') # Simple counting, imperfect but fast
        if "q1" in history and "q2" in history and "q3" in history and "q4" in history:
            pass # All done
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
        # If item_id is too long, truncate? Usually IDs are short.
        # But let's keep it simple.
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
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_panel"))
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
    # Added durability and inv_id args
    m = types.InlineKeyboardMarkup(row_width=2)

    if durability is not None and durability <= 0:
        # Broken
        if inv_id:
            m.add(types.InlineKeyboardButton("🛠 ПОЧИНИТЬ (15% цены)", callback_data=f"repair_{inv_id}"))
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ (5% цены)", callback_data=f"dismantle_{inv_id}"))
    else:
        if is_equipped:
            # Unequip needs slot. If we passed item_id, we need to find slot.
            # Or passed unequip callback can figure it out?
            # Current `unequip_{slot}`. We need slot.
            info = EQUIPMENT_DB.get(item_id)
            slot = info['slot'] if info else None
            if slot:
                 m.add(types.InlineKeyboardButton("📦 СНЯТЬ", callback_data=f"unequip_{slot}"))
        else:
            # Check if equippable
            if item_id in EQUIPMENT_DB:
                 # Pass inv_id if available, otherwise fallback to item_id (legacy)
                 cb = f"equip_{inv_id}" if inv_id else f"equip_{item_id}"
                 m.add(types.InlineKeyboardButton("🛡 НАДЕТЬ", callback_data=cb))
            else:
                 # Consumables / Misc
                 m.add(types.InlineKeyboardButton("⚡️ ИСПОЛЬЗОВАТЬ", callback_data=f"use_item_{item_id}"))

        # Dismantle
        if inv_id:
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"dismantle_{inv_id}"))
        else:
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"dismantle_{item_id}"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="inventory"))
    return m

def shop_item_details_keyboard(item_id, price, currency):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"💸 КУПИТЬ ({price} {currency.upper()})", callback_data=f"buy_{item_id}"))
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

    # Slots
    slots_row = []
    for i in range(1, 4): # Max 3
        if i <= deck['slots']:
            sid = deck['config'].get(str(i))
            icon = "🕸"
            if sid and sid in config.SOFTWARE_DB:
                icon = config.SOFTWARE_DB[sid]['icon']

            slots_row.append(types.InlineKeyboardButton(f"[{icon}] Слот {i}", callback_data=f"pvp_slot_{i}"))
        else:
            slots_row.append(types.InlineKeyboardButton("🔒", callback_data=f"pvp_slot_locked"))

    m.add(*slots_row)

    # Upgrade
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

    for item in inventory:
        item_id = item['id']
        name = item['name']
        qty = item['quantity']
        is_hw = item.get('category') == 'hardware'

        # Icon based on type
        icon = item.get('icon', '📦')

        if is_hw:
            # Check if active
            is_active = active_hardware.get(item_id, False)
            state_icon = "🟢 АКТИВЕН" if is_active else "🔴 НЕАКТИВЕН"
            toggle_action = "pvp_hw_unequip_" if is_active else "pvp_hw_equip_"
            toggle_btn_text = f"🛑 ВЫКЛЮЧИТЬ" if is_active else f"⚡️ ВКЛЮЧИТЬ"

            # Row 1: Info
            m.add(types.InlineKeyboardButton(f"{icon} {name} (x{qty}) | {state_icon}", callback_data="dummy"))
            # Row 2: Actions
            m.row(
                types.InlineKeyboardButton(toggle_btn_text, callback_data=f"{toggle_action}{item_id}"),
                types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"pvp_dismantle_{item_id}")
            )

        else:
            # Software
            m.add(types.InlineKeyboardButton(f"{icon} {name} (x{qty})", callback_data="dummy"))
            m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"pvp_dismantle_{item_id}"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_software_select_menu(inventory, slot_id, mode='defense'):
    # mode: 'defense' (equips to deck) or 'attack' (selects for battle)
    m = types.InlineKeyboardMarkup(row_width=1)

    # Empty/Unequip
    cb_prefix = "pvp_equip_" if mode == 'defense' else "pvp_atk_sel_"

    m.add(types.InlineKeyboardButton("🚫 ОЧИСТИТЬ СЛОТ", callback_data=f"{cb_prefix}{slot_id}_empty"))

    if not inventory:
        m.add(types.InlineKeyboardButton("У вас нет программ", callback_data="dummy"))

    for item in inventory:
        # Item: {'id': ..., 'name': ..., 'icon': ..., 'type': ...}
        # Name already contains icon in config
        txt = f"{item['name']} ({item['type'].upper()})"
        m.add(types.InlineKeyboardButton(txt, callback_data=f"{cb_prefix}{slot_id}_{item['id']}"))

    back_cb = "pvp_config" if mode == 'defense' else "pvp_attack_prep"
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data=back_cb))
    return m

def pvp_shop_menu():
    m = types.InlineKeyboardMarkup(row_width=1)

    # Standard Software
    m.add(types.InlineKeyboardButton("─── 💾 ПРОГРАММЫ ───", callback_data="dummy"))
    for sid, info in config.SOFTWARE_DB.items():
        # Name has icon
        txt = f"{info['name']} — {info['cost']} BC"
        m.add(types.InlineKeyboardButton(txt, callback_data=f"pvp_buy_{sid}"))

    # Hardware / Consumables
    m.add(types.InlineKeyboardButton("─── 🛠 ЖЕЛЕЗО ───", callback_data="dummy"))

    # Prices for Hardware from config (assumed merged or standard)
    p_firewall = PRICES.get('firewall', 1000)
    p_ice = PRICES.get('ice_trap', 2000)
    p_proxy = PRICES.get('proxy_server', 500) # XP?

    m.add(types.InlineKeyboardButton(f"🛡 ФАЙРВОЛ ({p_firewall} BC)", callback_data="pvp_buy_hw_firewall"))
    m.add(types.InlineKeyboardButton(f"🪤 ICE-ЛОВУШКА ({p_ice} BC)", callback_data="pvp_buy_hw_ice_trap"))
    m.add(types.InlineKeyboardButton(f"🕶 ПРОКСИ ({p_proxy} XP)", callback_data="pvp_buy_hw_proxy_server"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_shop_confirm(sid, is_hardware=False):
    # Retrieve info
    if is_hardware:
        from config import ITEMS_INFO
        info = ITEMS_INFO.get(sid, {})
        cost = PRICES.get(sid, 0)
        # Proxy uses XP
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
    # Pre-attack screen
    m = types.InlineKeyboardMarkup(row_width=3)

    # Slot Buttons (to change programs)
    slots_row = []
    for i in range(1, 4):
        sid = selected_slots.get(str(i))
        icon = "🕸"
        if sid and sid in config.SOFTWARE_DB:
            icon = config.SOFTWARE_DB[sid]['icon']
        slots_row.append(types.InlineKeyboardButton(f"[{icon}]", callback_data=f"pvp_atk_slot_{i}"))

    m.add(*slots_row)

    # Action
    # Check if at least one program is selected? (Optional)
    # The game says "At least 2 wins", so user should probably equip items.
    m.add(types.InlineKeyboardButton("☠️ НАЧАТЬ ВЗЛОМ", callback_data="pvp_execute_attack"))

    # Randomizer?
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
            name = a['username'] or a['first_name'] or "Unknown"
            lvl = a.get('level', 1)
            time_ago = int((time.time() - a['timestamp']) / 3600)
            btn_text = f"🩸 {name} (Lvl {lvl}) - {time_ago}ч назад"
            m.add(types.InlineKeyboardButton(btn_text, callback_data=f"pvp_revenge_confirm_{log_id}"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m

def pvp_revenge_confirm(log_id, name):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"🩸 ОТОМСТИТЬ {name} (-50 XP)", callback_data=f"pvp_revenge_exec_{log_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_vendetta"))
    return m

def pvp_defense_shop():
    # Deprecated in v2.0 but kept for safety if old callbacks exist
    return pvp_shop_menu()

def leaderboard_menu(current_sort='xp'):
    m = types.InlineKeyboardMarkup(row_width=3)

    # Text for buttons
    txt_xp = "🏆 ОПЫТ"
    txt_depth = "🕳 ГЛУБИНА"
    txt_bio = "🩸 КАПИТАЛ"

    # Mark active
    if current_sort == 'xp': txt_xp = f"✅ {txt_xp}"
    elif current_sort == 'depth': txt_depth = f"✅ {txt_depth}"
    elif current_sort == 'biocoin': txt_bio = f"✅ {txt_bio}"

    m.add(
        types.InlineKeyboardButton(txt_xp, callback_data="lb_xp"),
        types.InlineKeyboardButton(txt_depth, callback_data="lb_depth"),
        types.InlineKeyboardButton(txt_bio, callback_data="lb_biocoin")
    )
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ В МЕНЮ", callback_data="back"))
    return m
