from telebot import types
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
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # 1. Энергия
    m.add(types.InlineKeyboardButton("💠 СИНХРОН", callback_data="get_protocol"),
          types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal"))
    
    # 2. Рейд
    m.add(types.InlineKeyboardButton("─── 🌑 НУЛЕВОЙ СЛОЙ ───", callback_data="zero_layer_menu"))
    
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

    if u.get('is_admin') or str(uid) == str(config.ADMIN_ID):
        m.add(types.InlineKeyboardButton("⚡️ GOD MODE ⚡️", callback_data="admin_panel"))
        
    return m

# =============================================================
# 👤 ПРОФИЛЬ
# =============================================================

def profile_menu(u, has_accel=False):
    m = types.InlineKeyboardMarkup(row_width=1)
    
    # Фракция
    if u['level'] >= 2:
        m.add(types.InlineKeyboardButton("🧬 ФРАКЦИЯ", callback_data="change_path_menu"))

    # Ускоритель
    if has_accel:
        m.add(types.InlineKeyboardButton("⚡️ АКТИВИРОВАТЬ УСКОРИТЕЛЬ", callback_data="use_accelerator"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🎒 ИНВЕНТАРЬ (RPG UI)
# =============================================================

def inventory_menu(items, equipped, dismantle_mode=False, category='all'):
    m = types.InlineKeyboardMarkup(row_width=3)
    
    # Tabs
    m.add(types.InlineKeyboardButton(f"{'✅' if category=='all' else ''} ВСЕ", callback_data="inventory"),
          types.InlineKeyboardButton(f"{'✅' if category=='equip' else ''} ЭКИП", callback_data="inv_cat_equip"),
          types.InlineKeyboardButton(f"{'✅' if category=='consumable' else ''} РАСХОД", callback_data="inv_cat_consumable"))

    mode_btn = "♻️ РЕЖИМ РАЗБОРА: ВКЛ" if dismantle_mode else "♻️ РАЗОБРАТЬ ВЕЩИ (10%)"
    mode_cb = "inv_mode_normal" if dismantle_mode else "inv_mode_dismantle"
    m.add(types.InlineKeyboardButton(mode_btn, callback_data=mode_cb))

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
    m.add(types.InlineKeyboardButton("⚔️ ОРУЖИЕ", callback_data="shop_cat_weapon"),
          types.InlineKeyboardButton("👕 БРОНЯ", callback_data="shop_cat_armor"))
    m.add(types.InlineKeyboardButton("💾 ЧИПЫ", callback_data="shop_cat_chip"),
          types.InlineKeyboardButton("📦 РАСХОДНИКИ", callback_data="shop_cat_consumables"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
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
    m.add(types.InlineKeyboardButton(f"🚀 ВОЙТИ (-{cost} XP)", callback_data="raid_enter"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back"))
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

def guide_menu(page_key='intro'):
    m = types.InlineKeyboardMarkup(row_width=2)

    m.add(types.InlineKeyboardButton("👋 НАЧАЛО", callback_data="guide_page_intro"),
          types.InlineKeyboardButton("🚀 РЕЙДЫ", callback_data="guide_page_raids"))
    m.add(types.InlineKeyboardButton("⚔️ БОЙ", callback_data="guide_page_combat"),
          types.InlineKeyboardButton("📊 ПРОКАЧКА", callback_data="guide_page_stats"))
    m.add(types.InlineKeyboardButton("🎒 ПРЕДМЕТЫ", callback_data="guide_page_items"),
          types.InlineKeyboardButton("🔓 ВЗЛОМ", callback_data="guide_page_pvp"))
    m.add(types.InlineKeyboardButton("🤝 СИНДИКАТ", callback_data="guide_page_social"),
          types.InlineKeyboardButton("⚡️ СОВЕТЫ", callback_data="guide_page_tips"))

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
    m.add(types.InlineKeyboardButton("📚 СПРАВКА", callback_data="admin_guide"))
    m.add(types.InlineKeyboardButton("🔙 ВЫХОД", callback_data="back"))
    return m

def admin_users_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("➕ НАЗНАЧИТЬ АДМИНА", callback_data="admin_grant_admin"),
          types.InlineKeyboardButton("➖ СНЯТЬ АДМИНА", callback_data="admin_revoke_admin"))
    m.add(types.InlineKeyboardButton("💰 ВЫДАТЬ РЕСУРСЫ", callback_data="admin_give_res"),
          types.InlineKeyboardButton("🎁 ВЫДАТЬ ПРЕДМЕТ", callback_data="admin_give_item_menu"))
    m.add(types.InlineKeyboardButton("👥 СПИСОК ИГРОКОВ", callback_data="admin_user_list"),
          types.InlineKeyboardButton("✉️ ЛИЧНОЕ СООБЩЕНИЕ", callback_data="admin_dm_user"))
    m.add(types.InlineKeyboardButton("♻️ СБРОС (Reset)", callback_data="admin_reset_user"))
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
        elif item_id == 'admin_key':
             m.add(types.InlineKeyboardButton("🔴 ИСПОЛЬЗОВАТЬ", callback_data="use_admin_key"))

    m.add(types.InlineKeyboardButton("♻️ РАЗОБРАТЬ", callback_data=f"dismantle_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="inventory"))
    return m

def shop_item_details_keyboard(item_id, price, currency):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"💸 КУПИТЬ ({price} {currency.upper()})", callback_data=f"buy_{item_id}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="shop_menu"))
    return m
