from telebot import types
from config import ADMIN_ID, PRICES, SCHOOLS, LEVELS, EQUIPMENT_DB, ITEMS_INFO, SLOTS

# =============================================================
# 🛠 ТУЛКИТ ДИЗАЙНЕРА
# =============================================================

def get_progress_bar(current, total, length=8):
    if total <= 0: return "░" * length
    filled = int((current / total) * length)
    filled = min(max(filled, 0), length)
    return "█" * filled + "░" * (length - filled)

# =============================================================
# 🌌 ГЛАВНЫЙ ТЕРМИНАЛ
# =============================================================

def main_menu(u):
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # 1. Энергия
    m.add(types.InlineKeyboardButton("💠 СИНХРОНИЗАЦИЯ", callback_data="get_protocol"),
          types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal"))
    
    # 2. Рейд
    m.add(types.InlineKeyboardButton("─── 🌑 ЭКСПЕДИЦИЯ ───", callback_data="zero_layer_menu"))
    
    # 3. Персонаж
    current_lvl = u['level']
    next_lvl_xp = LEVELS.get(current_lvl + 1, LEVELS.get(current_lvl, 999999))
    base_xp = LEVELS.get(current_lvl, 0)
    xp_in_level = max(0, u['xp'] - base_xp)
    needed = max(1, next_lvl_xp - base_xp)
    p_bar = get_progress_bar(xp_in_level, needed)
    
    m.add(types.InlineKeyboardButton(f"👤 [{current_lvl}] {p_bar}", callback_data="profile"),
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
          
    # 4. Инвентарь & Рейтинг
    m.add(types.InlineKeyboardButton("🎒 ИНВЕНТАРЬ", callback_data="inventory"),
          types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"))
          
    # 5. Социум & Дневник (ВЕРНУЛИ)
    m.add(types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"),
          types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_menu"))

    if str(uid) == str(ADMIN_ID):
        m.add(types.InlineKeyboardButton("⚡️ GOD MODE ⚡️", callback_data="admin_panel"))
        
    return m

# =============================================================
# 📓 ДНЕВНИК (ЧИТАЛКА v2.0)
# =============================================================

def diary_menu():
    """Главное меню дневника"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✍️ НОВАЯ ЗАПИСЬ", callback_data="diary_new"),
          types.InlineKeyboardButton("📖 ЧИТАТЬ АРХИВ", callback_data="diary_read_0")) # 0 - первая страница
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def diary_read_nav(page, total_pages):
    """Навигация по страницам (чтобы текст был читабельным)"""
    m = types.InlineKeyboardMarkup(row_width=3)
    
    btns = []
    # Кнопка "Назад" (страница)
    if page > 0: 
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"diary_read_{page-1}"))
    else:
        btns.append(types.InlineKeyboardButton("🌑", callback_data="dummy"))
        
    # Индикатор
    btns.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="dummy"))
    
    # Кнопка "Вперед" (страница)
    if page < total_pages - 1: 
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"diary_read_{page+1}"))
    else:
        btns.append(types.InlineKeyboardButton("🌑", callback_data="dummy"))
    
    m.add(*btns)
    m.add(types.InlineKeyboardButton("🔙 В МЕНЮ ДНЕВНИКА", callback_data="diary_menu"))
    return m

# =============================================================
# 🎒 ИНВЕНТАРЬ (RPG UI)
# =============================================================

def inventory_menu(items, equipped):
    m = types.InlineKeyboardMarkup(row_width=1)
    
    # СЕКЦИЯ 1: НАДЕТО
    if equipped:
        m.add(types.InlineKeyboardButton("--- 🛡 НАДЕТО ---", callback_data="dummy"))
        for slot, item_id in equipped.items():
            name = EQUIPMENT_DB.get(item_id, {}).get('name', '???')
            m.add(types.InlineKeyboardButton(f"⬇️ СНЯТЬ: {name}", callback_data=f"unequip_{slot}"))
    
    # СЕКЦИЯ 2: РЮКЗАК
    if items:
        m.add(types.InlineKeyboardButton("--- 📦 РЮКЗАК ---", callback_data="dummy"))
        for i in items:
            item_id = i['item_id']
            qty = i['quantity']
            
            # Экипировка
            if item_id in EQUIPMENT_DB:
                name = EQUIPMENT_DB[item_id]['name']
                m.add(types.InlineKeyboardButton(f"⬆️ НАДЕТЬ: {name}", callback_data=f"equip_{item_id}"))
            
            # Активные предметы
            elif item_id == 'admin_key':
                m.add(types.InlineKeyboardButton(f"🔴 ЮЗНУТЬ: GLITCH KEY (x{qty})", callback_data="use_admin_key"))
            
            # Расходники (можно добавить кнопку "Выбросить" в будущем)
            
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🎰 МАГАЗИН (HYBRID: XP + BIOCOIN)
# =============================================================

def shop_menu(u):
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Расходники (BioCoin)
    m.add(types.InlineKeyboardButton(f"🧭 КОМПАС ({PRICES['compass']} BC)", callback_data="buy_compass"),
          types.InlineKeyboardButton(f"🔑 КЛЮЧ ({PRICES['master_key']} BC)", callback_data="buy_master_key"))
    
    m.add(types.InlineKeyboardButton(f"🔋 БАТАРЕЯ ({PRICES['battery']} BC)", callback_data="buy_battery"),
          types.InlineKeyboardButton(f"🛡 ЭГИДА ({PRICES['aegis']} BC)", callback_data="buy_aegis"))

    # Экипировка (BioCoin)
    m.add(types.InlineKeyboardButton(f"🔪 НОЖ ({EQUIPMENT_DB['rusty_knife']['price']} BC)", callback_data="buy_rusty_knife"),
          types.InlineKeyboardButton(f"🧥 ХУДИ ({EQUIPMENT_DB['hoodie']['price']} BC)", callback_data="buy_hoodie"))
          
    # Апгрейды (XP - по твоему старому конфигу)
    m.add(types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} BC)", callback_data="buy_cryo"),
          types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} BC)", callback_data="buy_accel"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🕹 КОКПИТ РЕЙДА
# =============================================================

def raid_action_keyboard(xp_cost, event_type='neutral', has_key=False):
    """Контекстная клавиатура: кнопки меняются от ситуации"""
    m = types.InlineKeyboardMarkup()
    
    # Сундук
    if event_type == 'locked_chest':
        if has_key: m.add(types.InlineKeyboardButton("🔓 ОТКРЫТЬ (КЛЮЧ)", callback_data="raid_open_chest"))
        else: m.add(types.InlineKeyboardButton("🔒 НУЖЕН КЛЮЧ", callback_data="shop_dummy"))
            
    m.add(types.InlineKeyboardButton(f"👣 ШАГ ВГЛУБЬ (-{xp_cost} XP)", callback_data="raid_step"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    m = types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        short = opt[:20]
        m.add(types.InlineKeyboardButton(f"› {opt}", callback_data=f"r_check_{short}"))
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

# =============================================================
# 🔙 ПРОЧЕЕ
# =============================================================

def back_button():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# ⚡️ GOD MODE (РАСШИРЕННАЯ АДМИНКА)
# =============================================================

def admin_keyboard():
    """
    Панель Демиурга. 10+ функций.
    """
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # 1. КОММУНИКАЦИЯ
    m.add(types.InlineKeyboardButton("📢 РАССЫЛКА", callback_data="admin_broadcast"),
          types.InlineKeyboardButton("✉️ ЛИЧНОЕ СООБЩЕНИЕ", callback_data="admin_dm"))
          
    # 2. ЭКОНОМИКА (Раздача)
    m.add(types.InlineKeyboardButton("💰 ВЫДАТЬ XP/COINS", callback_data="admin_give_res"),
          types.InlineKeyboardButton("🎁 ВЫДАТЬ ПРЕДМЕТ", callback_data="admin_give_item_menu"))
          
    # 3. БАЗА ДАННЫХ (Контроль)
    m.add(types.InlineKeyboardButton("📜 SQL ТЕРМИНАЛ", callback_data="admin_sql"),
          types.InlineKeyboardButton("📊 СТАТИСТИКА БД", callback_data="admin_db_stats"))
          
    # 4. КОНТЕНТ (Креатив)
    m.add(types.InlineKeyboardButton("📝 ДОБАВИТЬ СИНХРОН", callback_data="admin_add_content"),
          types.InlineKeyboardButton("🎭 ДОБАВИТЬ ЗАГАДКУ", callback_data="admin_add_riddle"))
          
    # 5. ОПАСНАЯ ЗОНА
    m.add(types.InlineKeyboardButton("💀 ВАЙП ЮЗЕРА", callback_data="admin_wipe_user"),
          types.InlineKeyboardButton("♻️ ПЕРЕЗАГРУЗКА БОТА", callback_data="admin_restart"))
          
    m.add(types.InlineKeyboardButton("🔙 ВЫХОД", callback_data="back"))
    return m

def admin_item_select():
    """Подменю для выбора предмета на выдачу"""
    m = types.InlineKeyboardMarkup(row_width=2)
    # Генерируем кнопки из конфига
    for k, v in EQUIPMENT_DB.items():
        m.add(types.InlineKeyboardButton(v['name'], callback_data=f"adm_give_{k}"))
        
    # Добавляем расходники
    m.add(types.InlineKeyboardButton("🔑 MASTER KEY", callback_data="adm_give_master_key"),
          types.InlineKeyboardButton("🧭 COMPASS", callback_data="adm_give_compass"))
          
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="admin_panel"))
    return m
