from telebot import types
from config import ADMIN_ID, PRICES, SCHOOLS, LEVELS, EQUIPMENT_DB, ITEMS_INFO, SLOTS, ARCHIVE_COST

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
    
    # 3. Персонаж (Улучшенный прогресс-бар)
    current_lvl = u['level']
    next_lvl_xp = LEVELS.get(current_lvl + 1, 999999)
    base_xp = LEVELS.get(current_lvl, 0)
    xp_in_level = max(0, u['xp'] - base_xp)
    needed = max(1, next_lvl_xp - base_xp)
    p_bar = get_progress_bar(xp_in_level, needed)
    
    m.add(types.InlineKeyboardButton(f"👤 [{current_lvl}] {p_bar}", callback_data="profile"),
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))

    m.add(types.InlineKeyboardButton("🧬 ФРАКЦИЯ", callback_data="change_path_menu"),
          types.InlineKeyboardButton("🎒 ИНВЕНТАРЬ", callback_data="inventory"))
          
    # 4. Рейтинг и Социум
    m.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"),
          types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"))
          
    # 5. Знания & Гайды
    m.add(types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_menu"),
          types.InlineKeyboardButton("📚 ИНСТРУКЦИЯ (ГАЙД)", callback_data="guide"))

    if str(uid) == str(ADMIN_ID):
        m.add(types.InlineKeyboardButton("⚡️ GOD MODE ⚡️", callback_data="admin_panel"))
        
    return m

# =============================================================
# 📓 ДНЕВНИК И АРХИВ (v3.0)
# =============================================================

def diary_menu():
    """Меню дневника с разделом Архива"""
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("✍️ НОВАЯ ЗАПИСЬ", callback_data="diary_new"),
        types.InlineKeyboardButton("📖 МОИ МЫСЛИ (ПОЛНЫЙ ТЕКСТ)", callback_data="diary_read_0"),
        types.InlineKeyboardButton(f"💾 АРХИВ ПРОТОКОЛОВ ({ARCHIVE_COST} XP)", callback_data="diary_archive")
    )
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def diary_read_nav(page, total_pages):
    """Навигация по дневнику (по 1 записи на экран для читаемости)"""
    m = types.InlineKeyboardMarkup(row_width=3)
    
    btns = []
    if page > 0: btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"diary_read_{page-1}"))
    btns.append(types.InlineKeyboardButton(f"{page+1} / {total_pages}", callback_data="dummy"))
    if page < total_pages - 1: btns.append(types.InlineKeyboardButton("➡️", callback_data=f"diary_read_{page+1}"))
    
    m.add(*btns)
    m.add(types.InlineKeyboardButton("🔙 В МЕНЮ ДНЕВНИКА", callback_data="diary_menu"))
    return m

# =============================================================
# 🎒 ИНВЕНТАРЬ (RPG UI)
# =============================================================

def inventory_menu(items, equipped):
    m = types.InlineKeyboardMarkup(row_width=1)
    
    if equipped:
        m.add(types.InlineKeyboardButton("─── 🛡 НАДЕТО (Клик чтобы снять) ───", callback_data="dummy"))
        for slot, item_id in equipped.items():
            name = EQUIPMENT_DB.get(item_id, {}).get('name', '???')
            m.add(types.InlineKeyboardButton(f"⬇️ {SLOTS.get(slot, slot)}: {name}", callback_data=f"unequip_{slot}"))
    
    if items:
        m.add(types.InlineKeyboardButton("─── 📦 РЮКЗАК (Клик чтобы надеть) ───", callback_data="dummy"))
        for i in items:
            item_id = i['item_id']
            qty = i['quantity']
            if item_id in EQUIPMENT_DB:
                name = EQUIPMENT_DB[item_id]['name']
                m.add(types.InlineKeyboardButton(f"⬆️ {name} (x{qty})", callback_data=f"equip_{item_id}"))
            elif item_id == 'admin_key':
                m.add(types.InlineKeyboardButton(f"🔴 ЮЗНУТЬ: GLITCH KEY (x{qty})", callback_data="use_admin_key"))
            
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🎰 ЧЕРНЫЙ РЫНОК (С ОПИСАНИЕМ ПРЕДМЕТОВ)
# =============================================================

def shop_menu(u):
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Расходники
    m.add(types.InlineKeyboardButton(f"🧭 КОМПАС ({PRICES['compass']} BC)", callback_data="buy_compass"),
          types.InlineKeyboardButton(f"🔑 КЛЮЧ ({PRICES['master_key']} BC)", callback_data="buy_master_key"))
    
    m.add(types.InlineKeyboardButton(f"🔋 БАТАРЕЯ ({PRICES['battery']} BC)", callback_data="buy_battery"),
          types.InlineKeyboardButton(f"🛡 ЭГИДА ({PRICES['aegis']} BC)", callback_data="buy_aegis"))

    # Снаряжение (Динамический вывод из базы)
    for k, v in EQUIPMENT_DB.items():
        m.add(types.InlineKeyboardButton(f"{v['name']} ({v['price']} BC)", callback_data=f"buy_{k}"))
          
    # Апгрейды
    m.add(types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} XP)", callback_data="buy_cryo"),
          types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="buy_accel"))

    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🕹 КОКПИТ РЕЙДА
# =============================================================

def raid_welcome_keyboard(cost):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton(f"🚀 ВОЙТИ (-{cost} XP)", callback_data="raid_enter"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="back"))
    return m

def raid_action_keyboard(xp_cost, event_type='neutral', has_key=False):
    m = types.InlineKeyboardMarkup()
    
    if event_type == 'locked_chest':
        if has_key: m.add(types.InlineKeyboardButton("🔓 ОТКРЫТЬ (НУЖЕН КЛЮЧ)", callback_data="raid_open_chest"))
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

def change_path_keyboard(cost):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton(f"🏦 МАТЕРИЯ (-{cost} XP)", callback_data="change_path_money"),
        types.InlineKeyboardButton(f"🧠 РАЗУМ (-{cost} XP)", callback_data="change_path_mind"),
        types.InlineKeyboardButton(f"🤖 ТЕХНО (-{cost} XP)", callback_data="change_path_tech")
    )
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# 🔙 ПРОЧЕЕ
# =============================================================

def back_button():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# ⚡️ GOD MODE (12 КНОПОК УПРАВЛЕНИЯ)
# =============================================================

def admin_keyboard():
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Группа 1: Коммуникация
    m.add(types.InlineKeyboardButton("📢 РАССЫЛКА", callback_data="admin_broadcast"),
          types.InlineKeyboardButton("✉️ ЛС ЮЗЕРУ", callback_data="admin_dm"))
          
    # Группа 2: Ресурсы
    m.add(types.InlineKeyboardButton("💰 ВЫДАТЬ XP/BC", callback_data="admin_give_res"),
          types.InlineKeyboardButton("🎁 ВЫДАТЬ ITEM", callback_data="admin_give_item_menu"))
          
    # Группа 3: Мир и Контент
    m.add(types.InlineKeyboardButton("📝 ДОБАВИТЬ СИНХРОН", callback_data="admin_add_content"),
          types.InlineKeyboardButton("🎭 НОВАЯ ЗАГАДКА", callback_data="admin_add_riddle"))
    
    # Группа 4: Техническое
    m.add(types.InlineKeyboardButton("📜 SQL КОНСОЛЬ", callback_data="admin_sql"),
          types.InlineKeyboardButton("📊 СТАТИСТИКА БД", callback_data="admin_db_stats"))
    
    m.add(types.InlineKeyboardButton("👥 СПИСОК ЮЗЕРОВ", callback_data="admin_user_list"),
          types.InlineKeyboardButton("🔍 ИНФО О ЮЗЕРЕ", callback_data="admin_user_info"))
          
    # Группа 5: Опасная зона
    m.add(types.InlineKeyboardButton("💀 ВАЙП ЮЗЕРА", callback_data="admin_wipe_user"),
          types.InlineKeyboardButton("♻️ RESTART BOT", callback_data="admin_restart"))
          
    m.add(types.InlineKeyboardButton("🔙 ВЫХОД", callback_data="back"))
    return m

def admin_item_select():
    m = types.InlineKeyboardMarkup(row_width=2)
    for k, v in EQUIPMENT_DB.items():
        m.add(types.InlineKeyboardButton(v['name'], callback_data=f"adm_give_{k}"))
    m.add(types.InlineKeyboardButton("🔑 MASTER KEY", callback_data="adm_give_master_key"),
          types.InlineKeyboardButton("🧭 COMPASS", callback_data="adm_give_compass"))
    m.add(types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="admin_panel"))
    return m
