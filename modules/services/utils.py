import re
import random
import time
from telebot import types
from telebot.apihelper import ApiTelegramException
import config
from config import WELCOME_VARIANTS, MENU_IMAGE_URL, MENU_IMAGE_URL_MONEY, MENU_IMAGE_URL_MIND, MENU_IMAGE_URL_TECH, INVENTORY_LIMIT
import database as db
from modules.bot_instance import bot

# =============================================================
# 🛠 УТИЛИТЫ UI (из logic.py)
# =============================================================

GAME_GUIDE_TEXTS = {
    'intro': (
        "<b>👋 НАЧАЛО ИГРЫ</b>\n\n"
        "Добро пожаловать в <b>EIDOS: Chronicles</b> — киберпанк RPG, где ты играешь за цифровой призрак (Осколок), пытающийся обрести сознание в бесконечной Сети.\n\n"
        "<b>🚀 БЫСТРЫЙ СТАРТ:</b>\n"
        "1. <b>Запуск:</b> Напиши <code>/start</code>.\n"
        "2. <b>Выбор Пути:</b> Выбери Фракцию (Специализацию).\n"
        "3. <b>Цель:</b> Копи XP (Опыт) и BioCoins (Монеты), чтобы достичь 30 уровня и стать Абсолютом.\n\n"
        "<b>📱 ГЛАВНОЕ МЕНЮ:</b>\n"
        "• <b>💠 ПРОТОКОЛ (Синхрон):</b> Основной опыт (+25 XP). Кулдаун 30 мин. Шанс Глитча 5%.\n"
        "• <b>📡 СИГНАЛ:</b> Доп. опыт (+15 XP). Кулдаун 5 мин.\n"
        "• <b>🚀 РЕЙД (Нулевой Слой):</b> Опасная экспедиция за лутом. Требует энергии.\n"
        "• <b>👤 ПРОФИЛЬ:</b> Статистика, Уровень, Атака/Защита/Удача.\n"
        "• <b>🎒 ИНВЕНТАРЬ:</b> Предметы и экипировка.\n"
        "• <b>🎰 МАГАЗИН:</b> Покупка снаряжения за Монеты и Опыт.\n"
        "• <b>🔐 ДЕШИФРАТОР:</b> Взлом найденных в рейде зашифрованных кэшей."
    ),
    'raids': (
        "<b>🚀 МЕХАНИКА РЕЙДОВ (Нулевой Слой)</b>\n\n"
        "Рейд — это пошаговое приключение. Чем глубже, тем опаснее враги и ценнее награда.\n\n"
        "<b>🌍 БИОМЫ (ЗОНЫ):</b>\n"
        "1. <b>🏙 Трущобы (0-50м):</b> Легко.\n"
        "2. <b>🏭 Промзона (51-150м):</b> Средне. Лут x1.5.\n"
        "3. <b>🌃 Неон-Сити (151-300м):</b> Сложно. Лут x2.5.\n"
        "4. <b>🕸 Глубокая Сеть (301-500м):</b> Очень сложно. Лут x3.5.\n"
        "5. <b>🌌 ПУСТОТА (501+м):</b> Процедурный ад. Лут x5.0+.\n\n"
        "<b>👣 ДВИЖЕНИЕ:</b>\n"
        "Каждый шаг стоит <b>Энергии (XP)</b>. Если XP кончится — придется выходить.\n\n"
        "<b>💀 СМЕРТЬ И ЭВАКУАЦИЯ:</b>\n"
        "Твое здоровье — это <b>Сигнал (100%)</b>. Если он упадет до 0%, ты умрешь и <b>ПОТЕРЯЕШЬ ВЕСЬ ЛУТ</b> (кроме опыта за убийства).\n"
        "Чтобы сохранить добычу, нажми <b>ЭВАКУАЦИЯ</b> в любой безопасный момент.\n\n"
        "<b>👹 АНОМАЛИИ:</b>\n"
        "Глубоко в сети обитает Демон Максвелла. Он предлагает рискованные пари на HP или Лут. Победа удваивает ресурсы, поражение вешает дебафф 'Коррозия'."
    ),
    'shadow_broker': (
        "<b>🕶 ТЕНЕВОЙ БРОКЕР (ЧЕРНЫЙ РЫНОК ДАННЫХ)</b>\n\n"
        "[ЛОР]: <i>«Есть данные, которые Система стирает. А есть те, кто их восстанавливает.»</i>\n"
        "Теневой Брокер — это не личность, а анонимный протокол обмена запрещенными артефактами. Он появляется в разрывах соединения (2% шанс при любом действии) и существует ровно до тех пор, пока его не засекли сканеры (15 минут).\n\n"
        "<b>АСCОРТИМЕНТ:</b>\n"
        "Здесь продается то, что нарушает законы физики симуляции:\n"
        "• <b>Реликвии Первой Волны:</b> Оружие Архитекторов.\n"
        "• <b>Глитч-Артефакты:</b> Предметы с красным кодом редкости.\n"
        "• <b>Запретные Чипы:</b> Модули, дающие бессмертие или ломающие правила.\n\n"
        "<b>ЦЕНА:</b>\n"
        "Брокер не верит в кредиты. За лучшие товары он требует <b>Чистый Опыт (XP)</b> — саму суть вашей личности, или огромные суммы BioCoin."
    ),
    'decryption': (
        "<b>🔐 КВАНТОВЫЙ ДЕШИФРАТОР</b>\n\n"
        "[ЛОР]: <i>«Любой замок — это просто уравнение, которое еще не решили.»</i>\n"
        "Зашифрованные Кэши — это «черные ящики» удаленных пользователей. В них хранится самое ценное, что успел накопить Искатель перед окончательной дефрагментацией.\n\n"
        "<b>ПРОЦЕСС ВЗЛОМА:</b>\n"
        "Замки используют полиморфное шифрование. Чтобы открыть кэш, твоему интерфейсу нужно время на перебор миллиардов комбинаций (брутфорс).\n"
        "• <b>Базовое время:</b> 4 часа.\n"
        "• <b>Ускорение:</b> Фракция [ТЕХНО] или модуль [ДЕШИФРАТОР] сокращают время вдвое.\n\n"
        "<b>НАГРАДА:</b>\n"
        "Внутри всегда лежит валюта и опыт. Но с шансом 30% там можно найти экипировку Мифического (🟣) или Легендарного (🟠) уровня."
    ),
    'maxwell': (
        "<b>👹 ДЕМОН МАКСВЕЛЛА (СОРТИРОВЩИК ЭНТРОПИИ)</b>\n\n"
        "[ЛОР]: <i>«Порядок рождается из Хаоса. Я — тот, кто держит дверь.»</i>\n"
        "Древняя ИИ-сущность, обитающая на глубине ниже 50 метров. Он контролирует потоки данных между слоями реальности.\n\n"
        "<b>СДЕЛКА С ДЕМОНОМ:</b>\n"
        "Если ты встретишь его, он предложит сыграть в вероятность.\n"
        "• <b>Ставка HP:</b> Ты рискуешь жизнью ради удвоения награды.\n"
        "• <b>Ставка Лута:</b> Ты рискуешь всем, что нашел, ради усиления.\n\n"
        "Победа дает бафф <b>[ПЕРЕГРУЗКА]</b>. Поражение вешает проклятие <b>[КОРРОЗИЯ]</b>."
    ),
    'combat': (
        "<b>⚔️ БОЕВАЯ СИСТЕМА</b>\n\n"
        "Встретив врага, у тебя есть выбор:\n\n"
        "1. <b>⚔️ АТАКА:</b> Наносишь урон (зависит от ATK ±20%).\n"
        "   • <i>Крит:</i> Шанс x1.5 урона (зависит от LUCK).\n"
        "   • <i>Адреналин:</i> Если HP &lt; 20%, урон x2.\n"
        "   • <i>Казнь:</i> Если у врага &lt; 10% HP, он умирает мгновенно.\n"
        "2. <b>🏃 ПОБЕГ:</b> Шанс 50% + бонусы Удачи. Провал = удар в спину.\n\n"
        "<b>🎒 РАСХОДНИКИ В БОЮ:</b>\n"
        "• <b>💣 EMP-граната:</b> Наносит 150 чистого урона.\n"
        "• <b>👻 Стелс-спрей:</b> 100% шанс побега.\n"
        "• <b>🧹 Стиратель памяти:</b> Сбрасывает бой.\n\n"
        "<b>🛡 ЗАЩИТА:</b> Твоя DEF снижает входящий урон."
    ),
    'stats': (
        "<b>📊 ПРОКАЧКА И ХАРАКТЕРИСТИКИ</b>\n\n"
        "<b>📈 УРОВНИ (1-30):</b>\n"
        "С 1 по 5 уровни опыт фиксирован. С 6-го — растет экспоненциально (x1.5).\n\n"
        "<b>📉 СТАТЫ:</b>\n"
        "• <b>⚔️ ATK (Атака):</b> Твой урон в бою.\n"
        "• <b>🛡 DEF (Защита):</b> Снижает урон от монстров и ловушек.\n"
        "• <b>🍀 LUCK (Удача):</b> Шанс крита, лучшего лута и побега.\n\n"
        "<b>🧬 ФРАКЦИИ (БОНУСЫ):</b>\n"
        "• <b>🏦 МАТЕРИЯ:</b> +20% Монет в рейдах. (-Защита)\n"
        "• <b>🧠 РАЗУМ:</b> +10 к Защите. +15% Уворот в Глубокой Сети. (-Удача)\n"
        "• <b>🤖 ТЕХНО:</b> +10 к Удаче. -10% урона от роботов. (-Опыт за убийства)"
    ),
    'items': (
        "<b>🎒 ПРЕДМЕТЫ И ЭКИПИРОВКА</b>\n\n"
        "<b>👘 СЛОТЫ:</b>\n"
        "Ты можешь надеть шлем, бронежилет, оружие и чип.\n\n"
        "<b>📦 ВАЖНЫЕ РАСХОДНИКИ:</b>\n"
        "• <b>🔋 Батарея:</b> Лечит +30% Сигнала.\n"
        "• <b>💉 Нейро-стимулятор:</b> Лечит +60% Сигнала.\n"
        "• <b>🧭 Компас:</b> Показывает тип следующей комнаты.\n"
        "• <b>🗝 Ключи:</b> Нужны для сундуков (Магнитная отмычка, Ключ Бездны).\n"
        "• <b>💾 Дата-шип:</b> 80% шанс взломать сундук без ключа."
    ),
    'pvp': (
        "<b>🔓 PvP: ВЗЛОМ (/hack_random)</b>\n\n"
        "Ты можешь попытаться украсть монеты у случайного игрока.\n\n"
        "• <b>Команда:</b> Напиши <code>/hack_random</code> в чат.\n"
        "• <b>Цена:</b> 50 XP за попытку.\n"
        "• <b>Механика:</b> Твоя (ATK + LUCK) против (DEF + Level) жертвы.\n"
        "• <b>Успех:</b> Крадешь 5-10% монет (до 5000).\n"
        "• <b>Провал:</b> Теряешь XP.\n\n"
        "🛡 <b>ЗАЩИТА:</b> Купи предмет <b>Файрвол</b> в магазине. Он заблокирует одну атаку."
    ),
    'social': (
        "<b>🤝 СОЦИАЛЬНАЯ СИСТЕМА (СИНДИКАТ)</b>\n\n"
        "В Профиле есть кнопка <b>Синдикат</b>. Там твоя реферальная ссылка.\n\n"
        "<b>🎁 БОНУСЫ:</b>\n"
        "1. <b>300 XP</b> сразу за приглашенного друга.\n"
        "2. <b>10% (Роялти)</b> от всего XP и Монет, которые заработает друг, НАВСЕГДА."
    ),
    'tips': (
        "<b>⚡️ СОВЕТЫ НОВИЧКУ</b>\n\n"
        "1. Не жадничай в Рейдах. Если HP меньше 30% и нет аптечек — эвакуируйся!\n"
        "2. Купи <b>Ржавый Тесак</b> как можно скорее.\n"
        "3. Всегда носи <b>Магнитную Отмычку</b> — в сундуках лежат самые дорогие предметы.\n"
        "4. Заходи в игру каждый день, чтобы растить <b>Стрик</b> (бонус к опыту).\n"
        "5. Разбирай ненужные вещи в инвентаре на Монеты."
    )
}

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
    if not match and "ЗАГАДКА" in text.upper():
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

def format_combat_screen(villain, hp, signal, stats, session):
    txt = (
        f"👹 УГРОЗА ОБНАРУЖЕНА: <b>{villain['name']}</b> (Lvl {villain['level']})\n\n"
        f"<i>{villain['description']}</i>\n\n"
        f"📊 <b>ХАРАКТЕРИСТИКИ ВРАГА:</b>\n"
        f"❤️ HP: {hp} / {villain['hp']}\n"
        f"⚔️ Атака: {villain['atk']} | 🛡 Защита: {villain['def']}\n\n"
        f"👤 <b>ВАШИ ХАРАКТЕРИСТИКИ:</b>\n"
        f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n\n"
        f"⚠️ Оцените риски перед атакой."
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

def handle_death_log(uid, depth, u_level, username, buffer_coins):
    broadcast_msg = None
    # Level 5+ and Depth 50+ (Lowered for visibility)
    if u_level >= 5 and depth >= 50:
         # Log loot (only if worth it)
         if buffer_coins > 10:
             db.log_death_loot(depth, buffer_coins, username)

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
