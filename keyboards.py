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
    """
    Интерфейс уровня 'Архитектор'.
    Кнопки сгруппированы по смысловым блокам.
    """
    uid = u['uid']
    m = types.InlineKeyboardMarkup(row_width=2)
    
    # БЛОК 1: ГЕНЕРАЦИЯ ЭНЕРГИИ (CORE)
    btn_sync = types.InlineKeyboardButton("💠 СИНХРОНИЗАЦИЯ", callback_data="get_protocol")
    btn_sig = types.InlineKeyboardButton("📡 СИГНАЛ", callback_data="get_signal")
    m.add(btn_sync, btn_sig)
    
    # БЛОК 2: ЭКСПЕДИЦИИ (RISK)
    m.add(types.InlineKeyboardButton("─── 🌑 НУЛЕВОЙ СЛОЙ ───", callback_data="zero_layer_menu"))
    
    # БЛОК 3: ПЕРСОНАЛЬНЫЕ ДАННЫЕ (STATS)
    # Показываем уровень и прогресс
    # Защита от кейса макс. уровня
    current_lvl = u['level']
    next_lvl_xp = LEVELS.get(current_lvl + 1, LEVELS.get(current_lvl, 999999))
    prev_lvl_xp = LEVELS.get(current_lvl, 0)
    
    # Расчет прогресса внутри уровня, а не с нуля
    xp_in_level = u['xp'] - prev_lvl_xp
    needed_in_level = next_lvl_xp - prev_lvl_xp
    
    p_bar = get_progress_bar(xp_in_level, needed_in_level)
    
    m.add(
        types.InlineKeyboardButton(f"👤 [{current_lvl}] {p_bar}", callback_data="profile"),
        types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop")
    )
    
    # БЛОК 4: СОЦИАЛЬНЫЙ ГРАФ (NETWORK)
    m.add(
        types.InlineKeyboardButton("🏆 ТОП-10", callback_data="leaderboard"),
        types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode") # Пока заглушка или нет?
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
        # Кнопка неактивна для покупки, но показывает статус (можно сделать dummy callback)
        m.add(types.InlineKeyboardButton(accel_btn, callback_data="shop_dummy"))
    else:
        accel_btn = f"⚡️ УСКОРИТЕЛЬ ⚡️ ─── {PRICES['accel']} XP"
        m.add(types.InlineKeyboardButton(accel_btn, callback_data="buy_accel"))
    
    # ДЕШИФРАТОР
    # Если дешифратор есть (например, bool флаг или счетчик), можно менять текст
    # Но пока по твоей логике это просто покупка
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
# 🕹 КОКПИТ РЕЙДА (GAME DESIGN)
# =============================================================

def raid_keyboard():
    m = types.InlineKeyboardMarkup()
    # Логика кнопок перемещения должна совпадать с bot.py
    # В твоем коде логики перемещения (step_f, step_l) пока нет явной обработки направления, 
    # обычно это просто "следующий шаг". Сделаем унификацию.
    
    m.row(types.InlineKeyboardButton("🔼 ВГЛУБЬ", callback_data="raid_step"))
    
    # Если ты планируешь механику выбора пути (лево/право), оставь так. 
    # Если нет — упрости до одной кнопки "Дальше".
    # Сейчас сделаю заглушки для визуальной красоты, но функционал "Шаг"
    
    # m.row(
    #     types.InlineKeyboardButton("⬅️", callback_data="raid_step"),
    #     types.InlineKeyboardButton("⏺", callback_data="raid_info"), # Просто инфо о статусе
    #     types.InlineKeyboardButton("➡️", callback_data="raid_step")
    # )
    
    m.row(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ (СОХРАНИТЬ ВСЁ)", callback_data="raid_extract"))
    return m

def riddle_keyboard(options, correct_answer):
    """
    Клавиатура для загадок.
    ВАЖНО: callback_data должна содержать ответ, чтобы проверить его в bot.py.
    Но передавать весь текст опасно (лимит 64 байта).
    Лучше передавать хэш или индекс, но для простоты передадим урезанный текст.
    """
    m = types.InlineKeyboardMarkup(row_width=1)
    
    # Перемешиваем варианты уже на входе, здесь просто рендерим
    for opt in options:
        # Обрезаем callback_data до 60 символов, чтобы не словить ошибку Telegram
        # Добавляем префикс r_ans_ для отлова в хендлере
        cb_data = f"r_ans_{opt[:20]}" 
        m.add(types.InlineKeyboardButton(f"› {opt}", callback_data=cb_data))
    
    # Опция "Не знаю" — это пропуск с уроном
    # m.add(types.InlineKeyboardButton("☣️ ПРОПУСТИТЬ (-ЗДОРОВЬЕ)", callback_data="raid_skip_riddle"))
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

def admin_keyboard():
    """Меню админа"""
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("📢 РАССЫЛКА", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("📊 СТАТИСТИКА", callback_data="admin_stats"),
        types.InlineKeyboardButton("➕ НАЧИСЛИТЬ XP", callback_data="admin_give_xp"),
        types.InlineKeyboardButton("🔙 ВЫХОД", callback_data="back")
    )
    return m
