from telebot import types
from config import ADMIN_ID

def main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), 
               types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    markup.add(types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu"))
    markup.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), 
               types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="leaderboard"), 
               types.InlineKeyboardButton("📓 ДНЕВНИК", callback_data="diary_mode"))
    if uid == ADMIN_ID: markup.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return markup

def raid_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("⬅️", callback_data="raid_step_l"), 
               types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_f"), 
               types.InlineKeyboardButton("➡️", callback_data="raid_step_r"))
    markup.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return markup

def riddle_keyboard(options):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        # Callback data ограничена 64 байтами, поэтому берем срез
        markup.add(types.InlineKeyboardButton(opt, callback_data=f"r_pick_{opt[:15]}"))
    markup.add(types.InlineKeyboardButton("🏃 ПРОПУСТИТЬ", callback_data="r_skip"))
    return markup
