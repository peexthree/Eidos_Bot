from telebot import types
import time
from config import ADMIN_ID, PRICES, PATH_CHANGE_COST, SCHOOLS, TITLES, LEVELS

# =============================================================
# 🛠 ТУЛКИТ ДИЗАЙНЕРА (ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ)
# =============================================================

def get_progress_bar(current, total, length=8):
    """Визуальный индикатор прогресса для кнопок"""
    filled = int(current / total * length) if total > 0 else 0
    return "█" * filled + "░" * (length - filled)

# =============================================================
# 🌌 ГЛАВНЫЙ ТЕРМИНАЛ (ОСНОВНОЕ МЕНЮ)
# =============================================================

def main_menu(u):
    """
    Интерфейс уровня 'Архитектор'.
    Кнопки сгруппированы по смысловым блокам.
    """
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # БЛОК 1: ГЕНЕРАЦИЯ ЭНЕРГИИ (CORE)
    m.add(
        types.InlineKeyboardButton("💠 СИНХРОНИЗАЦИЯ", callback_data="get_protocol"),
        types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal")
    )
    
    # БЛОК 2: ЭКСПЕДИЦИИ (RISK)
    m.add(types.InlineKeyboardButton("─── 🌑 НУЛЕВОЙ СЛОЙ ───", callback_data="zero_layer_menu"))
    
    # БЛОК 3: ПЕРСОНАЛЬНЫЕ ДАННЫЕ (STATS)
    # Показываем уровень и прогресс
    next_lvl_xp = LEVELS.get(u['level'] + 1, LEVELS[u['level']])
    p_bar = get_progress_bar(u['xp'], next_lvl_xp)
    
    m.add(
        types.InlineKeyboardButton(f"👤 [{u['level']}] {p_bar}", callback_data="profile"),
        types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop")
    )
    
    # БЛОК 4: СОЦИАЛЬНЫЙ ГРАФ (NETWORK)
    m.add(
        types.InlineKeyboardButton("🏆 ТОП-10", callback_data="leaderboard"),
        types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode")
    )
    
    m.add(
        types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"),
        types.InlineKeyboardButton("📚 ГАЙД", callback_data="guide")
    )

    if uid == ADMIN_ID:
        m.add(types.InlineKeyboardButton("⚡️ ТЕРМИНАЛ УПРАВЛЕНИЯ ⚡️", callback_data="admin_panel"))
        
    return m

# =============================================================
# 🎰 ЧЕРНЫЙ РЫНОК (DOPAMINE DESIGN)
# =============================================================

def shop_menu(u):
    """
    Магазин в стиле 'Dark Web'.
    """
    m = types.InlineKeyboardMarkup(row_width=1)
    now = time.time()
    
    # КРИО: Показываем 'Запас'
    m.add(types.InlineKeyboardButton(
        f"❄️ КРИО-КАПСУЛА [{u['cryo']}] ─── {PRICES['cryo']} XP", 
        callback_data="buy_cryo"
    ))
    
    # УСКОРИТЕЛЬ
    if u['accel_exp'] > now:
        rem_min = int((u['accel_exp'] - now) // 60)
        accel_btn = f"⚡️ УСКОРИТЕЛЬ [АКТИВЕН: {rem_min}м]"
    else:
        accel_btn = f"⚡️ УСКОРИТЕЛЬ ⚡️ ─── {PRICES['accel']} XP"
    m.add(types.InlineKeyboardButton(accel_btn, callback_data="buy_accel"))
    
    # ДЕШИФРАТОР
    m.add(types.InlineKeyboardButton(
        f"🔑 ДЕШИФРАТОР ─── {PRICES['decoder']} XP", 
        callback_data="buy_decoder"
    ))
    
    # ПУТЬ
    curr_school = SCHOOLS.get(u['path'], "НЕ ВЫБРАНО")
    m.add(types.InlineKeyboardButton(
        f"⚙️ СМЕНА ВЕКТОРА [{curr_school}]", 
        callback_data="change_path"
    ))
    
    m.add(types.InlineKeyboardButton("🔙 НАЗАД В ХАБ", callback_data="back"))
    return m

# =============================================================
# 🕹 КОКПИТ РЕЙДА (GAME DESIGN)
# =============================================================

def raid_keyboard():
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_f"))
    m.row(
        types.InlineKeyboardButton("⬅️ ЛЕВО", callback_data="raid_step_l"),
        types.InlineKeyboardButton("⏺", callback_data="raid_stay"),
        types.InlineKeyboardButton("➡️ ПРАВО", callback_data="raid_step_r")
    )
    m.row(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ (СОХРАНИТЬ ВСЁ)", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    m = types.InlineKeyboardMarkup(row_width=1)
    sorted_opts = sorted(options, key=len)
    for opt in sorted_opts:
        m.add(types.InlineKeyboardButton(f"› {opt.upper()}", callback_data=f"r_p_{opt[:15]}"))
    
    m.add(types.InlineKeyboardButton("☣️ ПРОПУСТИТЬ (УРОН)", callback_data="raid_step_skip"))
    return m

# =============================================================
# 🧬 ВЫБОР ФРАКЦИИ (MARKETING PSYCHOLOGY)
# =============================================================

def path_selection_keyboard():
    """
    Каждая школа должна выглядеть как элитный клуб.
    """
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("🏦 ШКОЛА МАТЕРИИ [КАПИТАЛ]", callback_data="set_path_money"),
        types.InlineKeyboardButton("🧠 ШКОЛА РАЗУМА [ВЛИЯНИЕ]", callback_data="set_path_mind"),
        types.InlineKeyboardButton("🤖 ШКОЛА СИНГУЛЯРНОСТИ [AI]", callback_data="set_path_tech")
    )
    return m

# =============================================================
# 🔙 УНИВЕРСАЛЬНАЯ КНОПКА ВОЗВРАТА
# =============================================================

def back_button():
    """Создает стандартную кнопку возврата в главное меню"""
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m
