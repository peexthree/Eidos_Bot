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
        "<b>👋 НАЧАЛО ИГРЫ: EIDOS CHRONICLES</b>\n\n"
        "Добро пожаловать в цифровую симуляцию. Ты — Осколок, цифровой призрак, стремящийся обрести сознание.\n\n"
        "<b>🚀 БЫСТРЫЙ СТАРТ:</b>\n"
        "1. <b>Уровень:</b> Копи опыт (XP), чтобы повышать уровень. С 6-го уровня опыт растет экспоненциально.\n"
        "2. <b>Валюта:</b> BioCoins (BC) — основная валюта для торговли.\n"
        "3. <b>Цель:</b> Достичь 30 уровня и статуса «Абсолют».\n\n"
        "<b>📱 ГЛАВНОЕ МЕНЮ:</b>\n"
        "• <b>💠 ПРОТОКОЛ (Синхрон):</b> +25 XP. Раз в 30 мин. Шанс Глитча 5%.\n"
        "• <b>📡 СИГНАЛ:</b> +15 XP. Раз в 5 мин.\n"
        "• <b>🚀 РЕЙД (Нулевой Слой):</b> Основной способ добычи лута и монет.\n"
        "• <b>👤 ПРОФИЛЬ:</b> Твои статы, экипировка и фракция.\n"
        "• <b>🎒 ИНВЕНТАРЬ:</b> Управление предметами.\n"
        "• <b>🎰 РЫНОК:</b> Покупка снаряжения и расходников.\n"
        "• <b>🌐 СЕТЕВАЯ ВОЙНА:</b> PvP режим (с 3 уровня)."
    ),
    'raids': (
        "<b>🚀 РЕЙДЫ: НУЛЕВОЙ СЛОЙ</b>\n\n"
        "Опасная экспедиция в глубины сети. Каждый шаг стоит XP. Чем глубже — тем сложнее враги и лучше награда.\n\n"
        "<b>🌍 БИОМЫ И ГЛУБИНА:</b>\n"
        "1. <b>🏙 Трущобы (0-50м):</b> Множитель лута x1.0. Безопасно для новичков.\n"
        "2. <b>🏭 Промзона (51-150м):</b> Лут x1.5. Враги бьют больнее.\n"
        "3. <b>🌃 Неон-Сити (151-300м):</b> Лут x2.5. Элитные мобы.\n"
        "4. <b>🕸 Глубокая Сеть (301-500м):</b> Лут x3.5. Зона смерти.\n"
        "5. <b>🌌 ПУСТОТА (501+м):</b> Лут x5.0+. Процедурный ад.\n\n"
        "<b>⚙️ МЕХАНИКА:</b>\n"
        "• <b>Сигнал (HP):</b> Твое здоровье. Если упадет до 0% — ты умрешь и <b>ПОТЕРЯЕШЬ ВЕСЬ ЛУТ</b>. Эвакуируйся, пока жив!\n"
        "• <b>Глитч (5%):</b> Случайное событие при шаге. Может дать XP, вылечить или отнять монеты.\n"
        "• <b>Загадки:</b> Правильный ответ дает XP и предметы. Ошибка — урон.\n"
        "• <b>Могилы:</b> Можно найти останки других игроков и забрать их лут.\n"
        "• <b>Аномалии:</b> Демон Максвелла предложит сыграть на HP или Лут."
    ),
    'combat': (
        "<b>⚔️ БОЕВАЯ СИСТЕМА</b>\n\n"
        "Встретив врага, у тебя есть выбор:\n\n"
        "1. <b>⚔️ АТАКА:</b> Наносишь урон. Формула: <code>ATK ± 20%</code>.\n"
        "   • <i>Крит:</i> Шанс зависит от LUCK. Урон x1.5.\n"
        "   • <i>Адреналин:</i> Если HP &lt; 20%, урон удваивается.\n"
        "   • <i>Казнь:</i> Если у врага &lt; 10% HP, он умирает мгновенно.\n"
        "2. <b>🏃 ПОБЕГ:</b> Шанс 50% + (LUCK / 2). Провал означает получение удара.\n\n"
        "<b>🛡 ЗАЩИТА:</b>\n"
        "Урон врага снижается твоей DEF. Формула защиты: <code>Урон * (1 - DEF / (DEF + 100))</code>.\n\n"
        "<b>💣 БОЕВЫЕ РАСХОДНИКИ:</b>\n"
        "• <b>EMP-граната:</b> 150 чистого урона.\n"
        "• <b>Стелс-спрей:</b> 100% шанс побега.\n"
        "• <b>Стиратель памяти:</b> Сбрасывает бой, враг забывает тебя."
    ),
    'stats': (
        "<b>📊 ХАРАКТЕРИСТИКИ И ФРАКЦИИ</b>\n\n"
        "<b>📈 СТАТЫ:</b>\n"
        "• <b>⚔️ ATK:</b> Твой урон.\n"
        "• <b>🛡 DEF:</b> Снижение входящего урона.\n"
        "• <b>🍀 LUCK:</b> Шанс крита, побега и редкого лута.\n\n"
        "<b>🧬 ФРАКЦИИ (ПУТИ):</b>\n"
        "Выбор доступен со 2 уровня. Смена стоит XP.\n\n"
        "1. <b>🏦 МАТЕРИЯ (Money):</b>\n"
        "   • <i>Бонус:</i> +20% Монет в рейдах.\n"
        "   • <i>Штраф:</i> -Защита от ловушек.\n\n"
        "2. <b>🧠 РАЗУМ (Mind):</b>\n"
        "   • <i>Бонус:</i> +10 DEF. +15% Уклонение в Глубокой Сети.\n"
        "   • <i>Штраф:</i> -Удача при поиске лута.\n\n"
        "3. <b>🤖 ТЕХНО (Tech):</b>\n"
        "   • <i>Бонус:</i> +10 LUCK. -10% урона от роботов.\n"
        "   • <i>Штраф:</i> -10% XP за убийства."
    ),
    'items': (
        "<b>🎒 ПРЕДМЕТЫ И ЭКИПИРОВКА</b>\n\n"
        "<b>👘 СЛОТЫ:</b>\n"
        "• <b>Оружие:</b> Определяет ATK.\n"
        "• <b>Броня:</b> Определяет DEF.\n"
        "• <b>Голова:</b> Дает уникальные пассивные ауры (Вампиризм, Сканер, Уклонение).\n"
        "• <b>Чип:</b> Модификаторы статов и механик.\n\n"
        "<b>📦 ПОЛЕЗНЫЕ РАСХОДНИКИ:</b>\n"
        "• <b>🔋 Батарея:</b> +30% HP.\n"
        "• <b>💉 Стимулятор:</b> +60% HP.\n"
        "• <b>🧭 Компас:</b> Показывает следующую комнату.\n"
        "• <b>📡 Сканер:</b> Рассчитывает шанс победы.\n"
        "• <b>🗝 Магнитная отмычка:</b> Открывает обычные сундуки.\n"
        "• <b>👁‍🗨 Ключ Бездны:</b> Открывает ВСЕ сундуки (включая Проклятые)."
    ),
    'crafting': (
        "<b>🛠 КРАФТИНГ (СИНТЕЗ)</b>\n\n"
        "Ты можешь улучшать снаряжение, объединяя копии.\n\n"
        "<b>🔹 ПРАВИЛА:</b>\n"
        "1. Собери <b>3 одинаковых предмета</b> одного уровня редкости в инвентаре (не надетых).\n"
        "2. Нажми «🛠 КРАФТ» в меню просмотра предмета.\n"
        "3. Ты получишь <b>1 случайный предмет</b> следующего уровня редкости (того же типа).\n\n"
        "<b>🔸 УРОВНИ РЕДКОСТИ:</b>\n"
        "⚪️ [1] Обычное\n"
        "🔵 [2] Редкое\n"
        "🟣 [3] Мифическое\n"
        "🟠 [4] Легендарное\n"
        "🔴 [5] Проклятое / Реликвия (Нельзя скрафтить, только найти)\n\n"
        "<b>🧩 ФРАГМЕНТЫ:</b>\n"
        "Собери <b>5 Фрагментов данных</b>, чтобы синтезировать случайный предмет 🔴 Красного уровня."
    ),
    'economy': (
        "<b>💰 ЭКОНОМИКА И ТОРГОВЛЯ</b>\n\n"
        "<b>🪙 ВАЛЮТЫ:</b>\n"
        "• <b>BioCoin (BC):</b> Основные деньги. Добываются в рейдах и PvP.\n"
        "• <b>XP (Опыт):</b> Энергия для действий и прокачки. Также используется как валюта у Теневого Брокера.\n\n"
        "<b>🏪 МАГАЗИНЫ:</b>\n"
        "1. <b>🎰 Рынок:</b> Стандартное снаряжение и расходники.\n"
        "2. <b>🕶 Теневой Брокер:</b> Появляется случайно (2% шанс). Продает имба-вещи за XP или огромные суммы. Ассортимент меняется.\n\n"
        "<b>🎁 ЛУТБОКСЫ (GACHA):</b>\n"
        "В Магазине можно купить Лутбокс за 1000 BC. Шанс выпадения:\n"
        "• ⚪️ Обычное: 50%\n"
        "• 🔵 Редкое: 30%\n"
        "• 🟣 Мифическое: 15%\n"
        "• 🟠 Легендарное: 4%\n"
        "• 🔴 Проклятое: 1%"
    ),
    'pvp': (
        "<b>🌐 СЕТЕВАЯ ВОЙНА (PvP 2.0)</b>\n\n"
        "Хакерские дуэли за ресурсы. Доступно с 3 уровня.\n\n"
        "<b>🧠 СИСТЕМА «КАМЕНЬ-НОЖНИЦЫ-БУМАГА»:</b>\n"
        "Бой идет 3 раунда. Ты настраиваешь свою Кибер-Деку заранее.\n"
        "• 🔴 <b>ATK (Брутфорс)</b> побеждает 🔵 DEF.\n"
        "• 🔵 <b>DEF (Стена)</b> побеждает 🟢 STL.\n"
        "• 🟢 <b>STL (Стелс)</b> побеждает 🔴 ATK.\n\n"
        "<b>🏆 УСЛОВИЯ ПОБЕДЫ:</b>\n"
        "Выиграй 2 раунда из 3. Ничья (одинаковый тип софта) не дает очков.\n\n"
        "<b>💰 НАГРАДА:</b>\n"
        "• Кража ~10% монет жертвы.\n"
        "• Майнинг (бонусные монеты).\n"
        "• При провале ты теряешь XP.\n\n"
        "<b>🛠 ЗАЩИТА:</b>\n"
        "• <b>Файрвол:</b> Блокирует 1 атаку полностью.\n"
        "• <b>ICE-Ловушка:</b> Крадет XP у хакера при неудачном взломе.\n"
        "• <b>Прокси:</b> Скрывает твое имя и защищает от мести."
    ),
    'social': (
        "<b>🤝 СИНДИКАТ (РЕФЕРАЛЫ)</b>\n\n"
        "Создавай свою сеть влияния.\n\n"
        "<b>🎁 БОНУСЫ:</b>\n"
        "1. <b>+300 XP</b> сразу за каждого приглашенного.\n"
        "2. <b>10% Роялти:</b> Ты получаешь 10% от всех монет и опыта, которые зарабатывают твои рефералы. ВЕЧНО.\n\n"
        "Кнопка «Синдикат» в главном меню покажет твою статистику и ссылку."
    ),
    'tips': (
        "<b>⚡️ СОВЕТЫ ОПЫТНОГО СТАЛКЕРА</b>\n\n"
        "1. <b>Жадность убивает:</b> Если HP ниже 40%, а аптечек нет — жми Эвакуацию. Лучше вынести мало, чем потерять всё.\n"
        "2. <b>Ключи:</b> Всегда носи с собой 1-2 Магнитные отмычки. В закрытых сундуках лут лучше.\n"
        "3. <b>Ауры:</b> Шлемы дают пассивные бонусы. «Окуляры Кочевника» помогут найти лут, а «Вампир» сэкономит аптечки.\n"
        "4. <b>Крафт:</b> Не продавай всё подряд. Копи одинаковые предметы, чтобы скрафтить более редкие.\n"
        "5. <b>Стрик:</b> Заходи каждый день. Бонус к опыту растет с каждым днем.\n"
        "6. <b>PVP:</b> Настрой защиту в меню «Сетевая Война», иначе тебя ограбят, пока ты спишь."
    ),
    'shadow_broker': (
        "<b>🕶 ТЕНЕВОЙ БРОКЕР</b>\n\n"
        "Неуловимый торговец черного рынка. Он появляется случайно (шанс 2% при любом действии).\n\n"
        "• <b>Товар:</b> Только высший тир (🟣, 🟠, 🔴) и уникальные Реликвии.\n"
        "• <b>Валюта:</b> XP (твоя жизнь) или огромные суммы BC.\n"
        "• <b>Время:</b> У тебя есть всего 15 минут, прежде чем он исчезнет.\n"
        "• <b>Эксклюзив:</b> Только у него можно купить «Синхрон Очищения» (сброс профиля) и «Бог-Мод Чип»."
    ),
    'decryption': (
        "<b>🔐 ДЕШИФРАТОР КЭШЕЙ</b>\n\n"
        "Иногда в рейдах выпадают «Зашифрованные Кэши».\n\n"
        "• Чтобы открыть кэш, нужно запустить процесс расшифровки в Главном Меню.\n"
        "• <b>Время:</b> 4 часа (2 часа с модулем Дешифратор).\n"
        "• <b>Лут:</b> Внутри много валюты и высокий шанс на 🟣/🟠 экипировку."
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
