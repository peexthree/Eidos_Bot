import re
import random
import time
from telebot import types
from telebot.apihelper import ApiTelegramException
import config
from config import WELCOME_VARIANTS, MENU_IMAGE_URL, MENU_IMAGE_URL_MONEY, MENU_IMAGE_URL_MIND, MENU_IMAGE_URL_TECH, MENU_IMAGE_URL_ARCHITECT, INVENTORY_LIMIT
import database as db
from modules.bot_instance import bot
from modules.texts import GAME_GUIDE_TEXTS

# =============================================================
# 🛠 УТИЛИТЫ UI (из logic.py)
# =============================================================


def add_biocoin(uid, amount, cursor=None, **kwargs):
    """
    Safely adds biocoin to user and tracks total_coins_earned in shadow metrics.
    """
    if amount <= 0:
        if kwargs: db.update_user(uid, cursor=cursor, **kwargs)
        return

    db.update_shadow_metric(uid, 'total_coins_earned', amount)

    # We use a direct SQL update for atomicity
    sql = "UPDATE players SET biocoin = biocoin + %s"
    params = [amount]

    if kwargs:
        for k, v in kwargs.items():
            sql += f", {k} = %s"
            params.append(v)

    sql += " WHERE uid = %s"
    params.append(uid)

    if cursor:
        cursor.execute(sql, tuple(params))
    else:
        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))

def strip_html(text):
    """Удаляет HTML теги из текста для алерта."""
    if not text: return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean

def draw_bar(curr, total, length=10):
    if total <= 0: return "░" * length
    p = max(0.0, min(1.0, curr / total))
    filled = int(length * p)
    return "█" * filled + "░" * (length - filled)

def parse_riddle(text):
    """
    Парсит текст загадки, извлекая ответ из скобок.
    Поддерживает форматы:
    1. (Ответ: Ответ) или (Протокол: Ответ) - строгий поиск.
    2. (Ответ) - если текст содержит 'ЗАГАДКА', ищет последнее содержимое скобок.
    Возвращает (answer, clean_text). Если ответ не найден, answer=None.
    """
    if not text: return None, text

    # 1. Строгий поиск с префиксом
    strict_match = re.search(r'\s*\((?:Ответ|Протокол):\s*(.*?)\)', text, re.IGNORECASE)

    match = strict_match

    # 2. Мягкий поиск (fallback), если это явно загадка
    if not match and "ЗАГАДКА" in str(text or '').upper():
         # Ищем содержимое скобок (берем ПОСЛЕДНЕЕ вхождение)
         all_matches = list(re.finditer(r'\(([^()]+)\)', text))
         if all_matches:
             match = all_matches[-1]

    if match:
         answer = match.group(1).strip()
         start, end = match.span()

         if strict_match:
             # Для строгого поиска вырезаем только блок ответа, сохраняя контекст
             clean_text = (text[:start] + text[end:]).strip()
         else:
             # Для мягкого поиска обрезаем текст ПО начало ответа, чтобы убрать спойлеры ("Правильно! Это...")
             clean_text = text[:start].strip()

         return answer, clean_text

    return None, text

def generate_hud(uid, u, session_data, cursor=None):
    # Fetch inventory details
    inv_items = db.get_inventory(uid, cursor=cursor)
    inv_count = sum(i['quantity'] for i in inv_items)
    inv_limit = INVENTORY_LIMIT

    keys = 0
    consumables = []

    for i in inv_items:
        iid = i['item_id']
        if iid in ['master_key', 'abyssal_key', 'data_spike']:
            keys += i['quantity']
        elif iid == 'battery': consumables.append("🔋")
        elif iid == 'neural_stimulator': consumables.append("💉")
        elif iid == 'emp_grenade': consumables.append("💣")
        elif iid == 'stealth_spray': consumables.append("🌫")
        elif iid == 'memory_wiper': consumables.append("🌀")

    cons_str = "".join(consumables[:5]) # Limit display

    # Format
    return (
        f"🎒 Инв: {inv_count}/{inv_limit} | 🗝 Ключи: {keys} | {cons_str}\n"
        f"⚡ XP: {u['xp']} | 🪙 BC: {u['biocoin']}"
    )

def format_combat_screen(villain, hp, signal, stats, session, win_chance=None):
    # Scanner Logic
    scanner_txt = "⚠️ Оцените риски перед атакой."

    if win_chance is not None:
        scanner_txt = f"📊 <b>ШАНС ПОБЕДЫ: ~{win_chance}%</b> (Сканер активен)"

    txt = (
        f"👹 УГРОЗА ОБНАРУЖЕНА: <b>{villain['name']}</b> (Lvl {villain['level']})\n\n"
        f"<i>{villain['description']}</i>\n\n"
        f"📊 <b>ХАРАКТЕРИСТИКИ ВРАГА:</b>\n"
        f"❤️ HP: {hp} / {villain['hp']}\n"
        f"⚔️ Атака: {villain['atk']} | 🛡 Защита: {villain['def']}\n\n"
        f"👤 <b>ВАШИ ХАРАКТЕРИСТИКИ:</b>\n"
        f"📡 Сигнал: {signal}%\n"
        f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n\n"
        f"{scanner_txt}"
    )
    return txt

# =============================================================
# 🛠 УТИЛИТЫ UI (из bot.py)
# =============================================================

def get_consumables(uid):
    inv = db.get_inventory(uid)
    cons = {}
    for i in inv:
        if i['item_id'] in ['battery', 'neural_stimulator', 'emp_grenade', 'stealth_spray', 'memory_wiper', 'data_spike']:
            cons[i['item_id']] = i['quantity']
    return cons

def get_menu_text(u):
    return random.choice(WELCOME_VARIANTS)

def get_menu_image(u):
    p = u.get("path", "unknown")
    if p == "money": return MENU_IMAGE_URL_MONEY
    elif p == "mind": return MENU_IMAGE_URL_MIND
    elif p == "tech": return MENU_IMAGE_URL_TECH
    elif p == "architect": return MENU_IMAGE_URL_ARCHITECT
    return MENU_IMAGE_URL

def menu_update(call, text, markup=None, image_url=None):
    try:
        if image_url:
            media = types.InputMediaPhoto(image_url, caption=text, parse_mode="HTML")
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            if call.message.content_type == "photo":
                 bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
            else:
                 bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except ApiTelegramException as e:
        if "message is not modified" in e.description:
            return # Ignore if content matches

        if e.error_code == 403 or "blocked" in e.description:
            db.set_user_active(call.from_user.id, False)
            return

        print(f"/// MENU UPDATE API ERR: {e}")
        # Fallback for API errors (e.g. message too old, content not modified, invalid file id)
        try:
            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        except ApiTelegramException as e2:
            print(f"/// MENU UPDATE FALLBACK ERR: {e2}")
            # Try text only if image failed
            if image_url:
                try:
                    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
                except: pass
        except: pass

    except Exception as e:
        print(f"/// MENU UPDATE ERR: {e}")
        try:
            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=text, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        except ApiTelegramException as e:
             if e.error_code == 403 or "blocked" in e.description:
                db.set_user_active(call.from_user.id, False)
        except: pass

def loading_effect(chat_id, message_id, final_text, final_kb, image_id=None):
    if image_id:
        try:
            media = types.InputMediaPhoto(image_id, caption="<code>/// DOWNLOAD: ▪️▫️▫️▫️▫️ 0%</code>", parse_mode="HTML")
            bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_id)
        except ApiTelegramException as e:
             if e.error_code == 403 or "blocked" in e.description:
                 db.set_user_active(chat_id, False)
                 return # Stop if blocked
        except Exception as e:
            print(f"/// LOADING EFFECT IMG ERR: {e}")

    steps = ["▪️▪️▫️▫️▫️ 25%", "▪️▪️▪️▫️▫️ 50%", "▪️▪️▪️▪️▫️ 75%", "▪️▪️▪️▪️▪️ 100%"]
    try:
        for s in steps:
            try:
                bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=f"<code>/// DOWNLOAD: {s}</code>", parse_mode="HTML")
            except:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"<code>/// DOWNLOAD: {s}</code>", parse_mode="HTML")
                except: pass
            time.sleep(0.3)
        try:
             bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=final_text, reply_markup=final_kb, parse_mode="HTML")
        except:
             bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=final_text, reply_markup=final_kb, parse_mode="HTML")
    except ApiTelegramException as e:
         if e.error_code == 403 or "blocked" in e.description:
             db.set_user_active(chat_id, False)
             return
    except:
        try:
            bot.send_message(chat_id, final_text, reply_markup=final_kb, parse_mode="HTML")
        except: pass

def get_biome_modifiers(depth):
    """Возвращает конфиг зоны на основе глубины."""
    if depth <= 50:
        return {"name": "🏙 Трущобы", "mult": 1.0, "desc": "Грязные улицы, полные отбросов."}
    elif depth <= 150:
        return {"name": "🏭 Промзона", "mult": 1.5, "desc": "Шум заводских механизмов."}
    elif depth <= 300:
        return {"name": "🌃 Неон-Сити", "mult": 2.5, "desc": "Яркие огни и тени корпораций."}
    elif depth <= 500:
        return {"name": "🕸 Глубокая Сеть", "mult": 3.5, "desc": "Абстрактные коридоры данных."}
    else:
        # Procedural
        hex_code = hex(depth)[2:].upper()
        adj = random.choice(["Мертвый", "Забытый", "Холодный", "Вечный", "Нулевой"])
        noun = random.choice(["Сектор", "Кластер", "Горизонт", "Предел", "Вакуум"])
        name = f"🌌 {adj} {noun} [{hex_code}]"
        scale = 5.0 + ((depth - 500) * 0.01)
        return {"name": name, "mult": scale, "desc": "Здесь кончается реальность."}

def generate_raid_report(uid, s, success=False):
    # Time
    duration = int(time.time() - s['start_time'])
    mins = duration // 60
    secs = duration % 60

    kills = s.get('kills', 0)
    riddles = s.get('riddles_solved', 0)
    depth = s.get('depth', 0)
    profit_xp = s.get('buffer_xp', 0)
    profit_coins = s.get('buffer_coins', 0)

    # Items
    buffer_items_str = s.get('buffer_items', '')
    items_list_str = ""
    from config import ITEMS_INFO
    if buffer_items_str:
        items = buffer_items_str.split(',')
        item_counts = {}
        for i in items:
            if i:
                name = ITEMS_INFO.get(i, {}).get('name', i)
                item_counts[name] = item_counts.get(name, 0) + 1

        items_list_str = ", ".join([f"{k} x{v}" for k,v in item_counts.items()])
    else:
        items_list_str = "Нет"

    if success:
        return (
            f"✅ <b>ЭВАКУАЦИЯ УСПЕШНА</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"ПОЛУЧЕНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Предметы: {items_list_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📊 СТАТИСТИКА:\n"
            f"• Глубина: {depth}\n"
            f"• Убийств: {kills}\n"
            f"• Загадок: {riddles}\n"
            f"⏱ Время: {mins}м {secs}с"
        )
    else:
        return (
            f"--- СВЯЗЬ ПРЕРВАНА. ОБЪЕКТ УНИЧТОЖЕН ---\n"
            f"УТЕРЯНО:\n"
            f"• Данные (XP): {profit_xp}\n"
            f"• Энергоблоки (Coins): {profit_coins}\n"
            f"• Расходники: {items_list_str}\n"
            f"⏱ Время: {mins}м {secs}с"
        )

def handle_death_log(uid, depth, u_level, username, buffer_coins, cursor=None):
    broadcast_msg = None
    # Level 5+ and Depth 50+ (Lowered for visibility)
    if u_level >= 5 and depth >= 50:
         # Log loot (only if worth it)
         if buffer_coins > 10:
             db.log_death_loot(depth, buffer_coins, username, cursor=cursor)

         broadcast_msg = (f"💀 <b>СИСТЕМНЫЙ НЕКРОЛОГ</b>\n"
                          f"Искатель @{username} (Lvl {u_level}) уничтожен на глубине {depth}м.\n"
                          f"Остаточный кэш: {buffer_coins} BC.\n"
                          f"Сектор нестабилен.")
    return broadcast_msg

def split_long_message(text, chunk_size=4000):
    """
    Splits a long string into chunks of at most chunk_size characters.
    Tries to split at double newlines (\\n\\n) to preserve block formatting.
    """
    if len(text) <= chunk_size:
        return [text]

    parts = text.split("\n\n")
    # If the text ends with \n\n, split returns an empty string at the end.
    # We remove it to avoid creating an artificial last chunk.
    if parts and not parts[-1]:
        parts.pop()

    chunks = []
    current_chunk = ""

    for part in parts:
        block = part + "\n\n"

        if len(current_chunk) + len(block) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = block
        else:
            current_chunk += block

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

import html

def int_to_roman(num):
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
        ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
        ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def get_vip_prefix(uid, first_name, custom_data=None):
    """
    Returns the VIP formatted name if the user has the 'eidos_shard' equipped.
    Format: ⚜️ <b>[I] {first_name}</b> or 👤 {first_name}
    Safely escapes the first_name.
    If custom_data is None, fetches from the database.
    """
    safe_name = html.escape(first_name or "Unknown")

    if custom_data is None:
        import database as db
        eq = db.get_equipped_item_in_slot(uid, 'eidos_shard')
        if eq and isinstance(eq, dict) and eq.get('item_id') == 'eidos_shard':
            custom_data = eq.get('custom_data')
        elif eq and isinstance(eq, tuple) and eq[0] == 'eidos_shard':
            custom_data = eq[2] if len(eq) > 2 else None

    if custom_data:
        try:
            import json
            data = json.loads(custom_data)
            level = int(data.get('level', 1))
            roman_lvl = int_to_roman(level)
            return f"⚜️ <b>[{roman_lvl}] {safe_name}</b>"
        except Exception as e:
            print(f"Error parsing eidos_shard custom_data for {uid}: {e}")

    return f"👤 {safe_name}"
