from telebot import types
from config import ADMIN_ID

def main_menu(uid):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("👁 СИНХРОН", callback_data="get_protocol"), 
          types.InlineKeyboardButton("📶 СИГНАЛ", callback_data="get_signal"))
    m.add(types.InlineKeyboardButton("🌑 НУЛЕВОЙ СЛОЙ", callback_data="zero_layer_menu"))
    m.add(types.InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"), 
          types.InlineKeyboardButton("🎰 РЫНОК", callback_data="shop"))
    if uid == ADMIN_ID: m.add(types.InlineKeyboardButton("⚙️ ADMIN", callback_data="admin_panel"))
    return m

def raid_keyboard():
    m = types.InlineKeyboardMarkup(row_width=3)
    m.add(types.InlineKeyboardButton("⬅️", callback_data="raid_step_l"), 
          types.InlineKeyboardButton("⬆️ ВПЕРЕД", callback_data="raid_step_f"), 
          types.InlineKeyboardButton("➡️", callback_data="raid_step_r"))
    m.add(types.InlineKeyboardButton("📦 ЭВАКУАЦИЯ", callback_data="raid_extract"))
    return m
