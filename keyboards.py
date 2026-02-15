from telebot import types
import time
from config import ADMIN_ID, PRICES, PATH_CHANGE_COST, SCHOOLS, TITLES, LEVELS

# =============================================================
# 🛠 ТУЛКИТ ДИЗАЙНЕРА (ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ)
# =============================================================

def get_progress_bar(current, total, length=8):
    """Визуальный индикатор прогресса для кнопок"""
    if total <= 0: return "░" * length
    filled = int((current / total) * length)
    filled = min(max(filled, 0), length) # Защита от выхода за границы
    return "█" * filled + "░" * (length - filled)

# =============================================================
# 🌌 ГЛАВНЫЙ ТЕРМИНАЛ (ОСНОВНОЕ МЕНЮ)
# =============================================================

def main_menu(u):
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # Блок 1: Энергия
    m.add(types.InlineKeyboardButton("💠 СИНХРОНИЗАЦИЯ", callback_data="get_protocol"),
          types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal"))
    
    # Блок 2: Рейд
    m.add(types.InlineKeyboardButton("─── 🌑 НУЛЕВОЙ СЛОЙ ───", callback_data="zero_layer_menu"))
    
    # Блок 3: Статистика и Профиль
    current_lvl = u['level']
    next_lvl_xp = LEVELS.get(current_lvl + 1, LEVELS.get(current_lvl, 999999))
    base_xp = LEVELS.get(current_lvl, 0)
    
    # Считаем прогресс внутри текущего уровня
    xp_in_level = max(0, u['xp'] - base_xp)
    needed_in_level = max(1, next_lvl_xp - base_xp)
    
    p_bar = get_progress_bar(xp_in_level, needed_in_level)
    
    m.add(types.InlineKeyboardButton(f"👤 [{current_lvl}] {p_bar}", callback_data="profile"),
          types.InlineKeyboardButton("🎰 МАГАЗИН", callback_data="shop"))
    
    # Блок 4: Социум
    m.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"),
          types.InlineKeyboardButton("🔗 СИНДИКАТ", callback_data="referral"))
    
    # Блок 5: Знания
    m.add(types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"),
          types.InlineKeyboardButton("📚 ГАЙД", callback_data="guide"))

    if str(uid) == str(ADMIN_ID):
        m.add(types.InlineKeyboardButton("⚡️ GOD MODE ⚡️", callback_data="admin_panel"))
        
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
        m.add(types.InlineKeyboardButton(accel_btn, callback_data="shop_dummy"))
    else:
        accel_btn = f"⚡️ УСКОРИТЕЛЬ ⚡️ ─── {PRICES['accel']} XP"
        m.add(types.InlineKeyboardButton(accel_btn, callback_data="buy_accel"))
    
    # ДЕШИФРАТОР
    m.add(types.InlineKeyboardButton(
        f"🔑 ДЕШИФРАТОР ─── {PRICES['decoder']} XP", 
        callback_data="buy_decoder"
    ))
    
    # ПУТЬ
    curr_school_code = u.get('path', 'general')
    curr_school = SCHOOLS.get(curr_school_code, "ОБЩИЙ ПОТОК")
    m.add(types.InlineKeyboardButton(
        f"⚙️ СМЕНА ВЕКТОРА [{curr_school}]", 
        callback_data="change_path"
    ))
    
    m.add(types.InlineKeyboardButton("🔙 НАЗАД В ХАБ", callback_data="back"))
    return m

# =============================================================
# 🕹 КОКПИТ РЕЙДА (GAME DESIGN - V2)
# =============================================================

def raid_action_keyboard():
    """
    Основная клавиатура действий в рейде (V2).
    Используется, когда нет активной загадки.
    """
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("👣 ШАГ В ТЕМНОТУ (-5 XP)", callback_data="raid_step"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    """
    Клавиатура для ответов на загадки (V2).
    Генерирует кнопки r_check_... которые ждет bot.py.
    """
    m = types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        # Обрезаем callback_data до безопасной длины (Telegram лимит 64 байта)
        # В bot.py мы проверяем вхождение (ans in correct), так что частичное совпадение сработает
        short_opt = opt[:20] 
        m.add(types.InlineKeyboardButton(f"› {opt}", callback_data=f"r_check_{short_opt}"))
    return m

# Старую функцию raid_keyboard удаляем, так как она дублирует функционал
# и может запутать бота.

# =============================================================
# 🧬 ВЫБОР ФРАКЦИИ (MARKETING PSYCHOLOGY)
# =============================================================

def path_selection_keyboard():
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
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

# =============================================================
# ⚡️ АДМИН-ПАНЕЛЬ
# =============================================================

def admin_keyboard():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
          types.InlineKeyboardButton("📜 SQL запрос", callback_data="admin_sql"))
    m.add(types.InlineKeyboardButton("👥 Users Count", callback_data="admin_users_count"),
          types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"))
    m.add(types.InlineKeyboardButton("➕ НАЧИСЛИТЬ XP", callback_data="admin_give_xp"),
          types.InlineKeyboardButton("🔙 Выход", callback_data="back"))
    return m
