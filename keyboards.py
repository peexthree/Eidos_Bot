from telebot import types
from config import ADMIN_ID, PRICES, PATH_CHANGE_COST

def main_menu(uid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), 
          types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    m.add(types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu"))
    m.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), 
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    m.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"), 
          types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"))
    if uid == ADMIN_ID: m.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return m

def shop_menu():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton(f"❄️ КРИО ({PRICES['cryo']} XP)", callback_data="buy_cryo"),
          types.InlineKeyboardButton(f"⚡️ УСКОРИТЕЛЬ ({PRICES['accel']} XP)", callback_data="buy_accel"),
          types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))
    return m

def raid_keyboard():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(types.InlineKeyboardButton("⬅️", callback_data="raid_step_l"), 
          types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_f"), 
          types.InlineKeyboardButton("➡️", callback_data="raid_step_r"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m

def riddle_keyboard(options):
    m = types.InlineKeyboardMarkup(row_width=1)
    for opt in options: m.add(types.InlineKeyboardButton(opt, callback_data=f"r_p_{opt[:15]}"))
    m.add(types.InlineKeyboardButton("🏃 ПРОПУСТИТЬ", callback_data="r_skip"))
    return m
