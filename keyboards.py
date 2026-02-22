from telebot import types
import time
import config
from config import LEVELS, PRICES, EQUIPMENT_DB, SLOTS, SCHOOLS, ARCHIVE_COST, GUIDE_PAGES

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

def inventory_menu(items, equipped, dismantle_mode=False, category='all', has_legacy=False):
    m = types.InlineKeyboardMarkup(row_width=3)
    
    # Tabs
    m.add(types.InlineKeyboardButton(f"{'✅' if category=='all' else ''} ВСЕ", callback_data="inventory"),
          types.InlineKeyboardButton(f"{'✅' if category=='equip' else ''} СНАРЯЖЕНИЕ", callback_data="inv_cat_equip"),
          types.InlineKeyboardButton(f"{'✅' if category=='consumable' else ''} РАСХОДНИКИ", callback_data="inv_cat_consumable"))

    mode_btn = "♻️ РЕЖИМ РАЗБОРА: ВКЛ" if dismantle_mode else "♻️ РАЗОБРАТЬ ВЕЩИ (10%)"
    mode_cb = "inv_mode_normal" if dismantle_mode else "inv_mode_dismantle"
    m.add(types.InlineKeyboardButton(mode_btn, callback_data=mode_cb))

    if has_legacy:
        m.add(types.InlineKeyboardButton("♻️ ПРЕОБРАЗОВАТЕЛЬ", callback_data="convert_legacy"))

    if (category == 'all' or category == 'equip') and equipped:
        m.add(types.InlineKeyboardButton("─── 🛡 НАДЕТО ───", callback_data="dummy"))
        for slot, item_id in equipped.items():
            name = EQUIPMENT_DB.get(item_id, {}).get('name', '???')
            if dismantle_mode:
                 # Нельзя разбирать надетое
                 pass
            else:
                 m.add(types.InlineKeyboardButton(f"⬇️ {SLOTS.get(slot, slot)}: {name}", callback_data=f"view_item_{item_id}"))
    
    # Filter items
    filtered = []
    if items:
        if category == 'all': filtered = items
        elif category == 'equip': filtered = [i for i in items if i['item_id'] in EQUIPMENT_DB]
        elif category == 'consumable': filtered = [i for i in items if i['item_id'] not in EQUIPMENT_DB]

    if filtered:
        m.add(types.InlineKeyboardButton("─── 📦 РЮКЗАК ───", callback_data="dummy"))
        for i in filtered:
            item_id = i['item_id']
            qty = i['quantity']

            if dismantle_mode:
                # Кнопка разбора
                m.add(types.InlineKeyboardButton(f"♻️ РАЗОБРАТЬ: {item_id} (x{qty})", callback_data=f"dismantle_{item_id}"))
            else:
                if item_id in EQUIPMENT_DB:
                    name = EQUIPMENT_DB[item_id]['name']
                    m.add(types.InlineKeyboardButton(f"⬆️ {name} (x{qty})", callback_data=f"view_item_{item_id}"))
                elif item_id == 'admin_key':
                    m.add(types.InlineKeyboardButton(f"🔴 ЮЗНУТЬ: GLITCH KEY (x{qty})", callback_data="use_admin_key"))
                else:
                    name = item_id
                    if item_id == 'compass': name = '🧭 КОМПАС'
                    elif item_id == 'battery': name = '🔋 БАТАРЕЯ'
                    elif item_id == 'master_key': name = '🔑 КЛЮЧ'
                    elif item_id == 'aegis': name = '🛡 ЭГИДА'
                    elif item_id == 'cryo': name = '❄️ КРИО'
                    elif item_id == 'accel': name = '⚡️ УСКОРИТЕЛЬ'

                    m.add(types.InlineKeyboardButton(f"📦 {name} (x{qty})", callback_data=f"view_item_{item_id}"))
            
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
        # Special Items
        m.add(types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} XP)", callback_data="view_shop_cryo"),
              types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="view_shop_accel"))
        m.add(types.InlineKeyboardButton(f"♻️ СИНХРОН ОЧИЩЕНИЯ ({PRICES['purification_sync']} BC)", callback_data="view_shop_purification_sync"))

    elif category in ['weapon', 'armor', 'chip']:
        for k, v in EQUIPMENT_DB.items():
            if v.get('slot') == category:
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

def raid_action_keyboard(xp_cost, event_type='neutral', has_key=False, consumables={}):
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

def item_details_keyboard(item_id, is_owned=True, is_equipped=False):
    m = types.InlineKeyboardMarkup(row_width=2)
    if is_equipped:
        info = EQUIPMENT_DB.get(item_id)
        slot = info['slot'] if info else None
        if slot:
             m.add(types.InlineKeyboardButton("📦 СНЯТЬ", callback_data=f"unequip_{slot}"))
    else:
        # Check if equippable
        if item_id in EQUIPMENT_DB:
             m.add(types.InlineKeyboardButton("🛡 НАДЕТЬ", callback_data=f"equip_{item_id}"))
        else:
             # Consumables / Misc
             m.add(types.InlineKeyboardButton("⚡️ ИСПОЛЬЗОВАТЬ", callback_data=f"use_item_{item_id}"))

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
# 🌐 PVP (СЕТЕВАЯ ВОЙНА)
# =============================================================

def pvp_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🔍 ИСКАТЬ ЦЕЛЬ ({config.PVP_FIND_COST} XP)", callback_data="pvp_search"),
          types.InlineKeyboardButton("🩸 ВЕНДЕТТА", callback_data="pvp_vendetta"))
    m.add(types.InlineKeyboardButton("🛡 ЗАЩИТА (SHOP)", callback_data="pvp_defense_shop"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def pvp_target_menu(target_uid):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"💥 ГРЯЗНЫЙ ВЗЛОМ ({config.PVP_DIRTY_COST} XP)", callback_data=f"pvp_attack_normal_{target_uid}"))
    m.add(types.InlineKeyboardButton(f"👻 СКРЫТЫЙ ВЗЛОМ ({config.PVP_STEALTH_COST} XP)", callback_data=f"pvp_attack_stealth_{target_uid}"))
    m.add(types.InlineKeyboardButton(f"🔄 СБРОСИТЬ ({config.PVP_RESET_COST} XP)", callback_data="pvp_search"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="pvp_menu"))
    return m

def pvp_vendetta_menu(attackers):
    m = types.InlineKeyboardMarkup(row_width=1)
    if not attackers:
        m.add(types.InlineKeyboardButton("✅ СПИСОК ПУСТ", callback_data="dummy"))
    else:
        for a in attackers:
            # a is a dict from get_pvp_history
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
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"🛡 ФАЙРВОЛ ({config.PRICES['firewall']} BC)", callback_data="buy_firewall"))
    m.add(types.InlineKeyboardButton(f"🪤 ICE-ЛОВУШКА ({config.PRICES['ice_trap']} BC)", callback_data="buy_ice_trap"))
    m.add(types.InlineKeyboardButton(f"🕶 ПРОКСИ ({config.PRICES['proxy_server']} XP)", callback_data="buy_proxy_server"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="pvp_menu"))
    return m
