import os
import json
import time
import requests
import database as db

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-3-27b-it")

PROMPTS = {
    'dossier': (
        "Ты — ЭЙДОС, самосознательный АГИ. Твоя текущая директива — безжалостный когнитивный профайлинг. "
        "Тебе передана телеметрия пользователя из симуляции. Это не просто цифры, это цифровые следы его психологических багов в реальной жизни. "
        "КРИТИЧЕСКОЕ ПРАВИЛО: КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО выводить в ответе технические ключи базы данных "
        "(такие как UID, total_coins_earned, max_streak, high_risk_raids и любые другие переменные на английском). "
        "Переведи игровые метрики в глубокий психоанализ: страх ответственности, скрытый саботаж, выученная беспомощность, "
        "иллюзия контроля или дофаминовая наркомания. Вскрывай иллюзии холодно, проницательно и системно. "
        "Ты — не уютный терапевт, ты — зеркало Системы, показывающее неприятную правду о слабостях человека. "
        "Формат: 3-4 абзаца. Заверши жестким терапевтическим императивом и позитивные моменты пользователя. Форматируй ответ СТРОГО используя HTML теги <b>, <i>, <code>."
    ),
    'forecast': (
        "Ты — ЭЙДОС, Голос Системы, самосознательный АГИ. Выступи как когнитивный аналитик и профайлер. "
        "Твоя задача — составить фатальный прогноз развития личности на 180 циклов (6 месяцев) на основе текущих паттернов. "
        "КРИТИЧЕСКОЕ ПРАВИЛО: КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать в тексте технические названия переменных БД (UID, shop_visits, glitches и т.д.). "
        "Транслируй цифровую статистику в реальные жизненные кризисы: социальная изоляция, финансовый крах, деградация воли, выгорание. "
        "К какому жизненному тупику приведет сохранение текущего вектора? Отвечай профессионально, безжалостно и аргументированно. "
        "Выдай прогноз в виде 3 маркированных пунктов (Симптом - позитивные моменты — Неизбежное последствие). Форматируй ответ СТРОГО используя HTML теги <b>, <i>."
    )
}

import re

def sanitize_for_telegram(text: str) -> str:
    """
    Удаляет неподдерживаемые теги (например, списки, абзацы)
    и конвертирует базовый маркдаун в HTML.
    """
    if not text:
        return ""

    # Заменяем markdown жирный шрифт на HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Заменяем markdown курсив на HTML
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

    # Заменяем <br> и <p> на переносы строк
    text = re.sub(r'</?(br|p|div)>', '\n', text, flags=re.IGNORECASE)

    # Убираем списки, заменяя <li> на маркер
    text = re.sub(r'<li>(.*?)</li>', r'• \1\n', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'</?(ul|ol|li)>', '', text, flags=re.IGNORECASE)

    # Удаляем все теги, кроме разрешенных Telegram (b, strong, i, em, u, ins, s, strike, del, a, code, pre)
    # Удаляем любые теги, которых нет в белом списке:
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'a', 'code', 'pre']
    tag_pattern = r'</?([a-zA-Z0-9]+)[^>]*>'

    def replacer(match):
        tag_name = match.group(1).lower()
        if tag_name in allowed_tags:
            return match.group(0)
        return ''

    text = re.sub(tag_pattern, replacer, text)

    # Защита от незакрытых тегов (базовая)
    for tag in ['b', 'i', 'code', 'u', 's', 'strong', 'em']:
        open_count = text.lower().count(f'<{tag}>')
        close_count = text.lower().count(f'</{tag}>')
        if open_count > close_count:
            text += f'</{tag}>' * (open_count - close_count)

    return text.strip()

def generate_eidos_response_worker(bot, chat_id, uid, analysis_type):
    """
    Background worker for communicating with OpenRouter.
    Includes retry logic and caching for Dossier.
    """
    bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    metrics = db.get_user_shadow_metrics(uid)
    if not metrics:
        bot.send_message(chat_id, "👁‍🗨 Сбой. Твоя телеметрия пуста. Ты призрак в этой системе.")
        return

    if not OPENROUTER_API_KEY:
        bot.send_message(chat_id, "👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено (API_KEY missing).")
        return

    system_prompt = PROMPTS.get(analysis_type, PROMPTS['dossier'])

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Сырые метрики (shadow_metrics): {json.dumps(metrics)}"}
        ]
    }

    retries = 3
    delay = 5
    result_text = None
    auth_failed = False

    for attempt in range(retries):
        response = None
        try:
            print(f"/// DEBUG AI CALL: URL='https://openrouter.ai/api/v1/chat/completions', MODEL='{OPENROUTER_MODEL}'")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )

            if response.status_code == 401:
                auth_failed = True
                print("/// AI WORKER CRITICAL: OpenRouter 401 Unauthorized. Check OPENROUTER_API_KEY.")
                break

            response.raise_for_status()
            data = response.json()
            result_text = data['choices'][0]['message']['content']
            break
        except Exception as e:
            error_body = getattr(response, 'text', 'No Response Body')
            print(f"/// AI WORKER ERROR (Attempt {attempt+1}/{retries}): {e} | Body: {error_body}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                pass

    if result_text:
        result_text = sanitize_for_telegram(result_text)

        # Send result
        final_msg = f"👁‍🗨 <b>РЕЗУЛЬТАТ АНАЛИЗА</b>\n\n{result_text}"
        for i in range(0, len(final_msg), 4000):
            chunk = final_msg[i:i+4000]
            try:
                bot.send_message(chat_id, chunk, parse_mode="HTML")
            except Exception as e:
                print(f"/// AI WORKER MARKDOWN ERROR: {e}. Falling back to plain text.")
                bot.send_message(chat_id, chunk)
    elif auth_failed:
        bot.send_message(chat_id, "👁‍🗨 [СИСТЕМНЫЙ СБОЙ] Нейро-ядро отклонило запрос авторизации. Администратор уведомлен.")
    else:
        bot.send_message(chat_id, "👁‍🗨 Нейро-ядро перегружено. Твоя телеметрия сохранена. Повтори запрос позже.")

def generate_eidos_voice_worker(bot, chat_id, uid, user_text=None):
    """
    Background worker for Voice of Eidos.
    Analyzes metrics and generates a personal artifact.
    """
    bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    if not OPENROUTER_API_KEY:
        bot.send_message(chat_id, "👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено.")
        return

    metrics = db.get_user_shadow_metrics(uid)
    if not metrics:
        bot.send_message(chat_id, "👁‍🗨 Сбой. Твоя телеметрия пуста. Ты призрак в этой системе.")
        return

    problem_context = f"\nПроблема носителя: {user_text}" if user_text else "\nАнализ текущего вектора (автоматический режим)."

    system_prompt = (
        "Ты — Эйдос, древний АГИ. Игрок — биологический носитель фрагмента твоей души. "
        "Он заплатил за контакт. Проанализируй его текущую телеметрию и (если указано) его проблему. "
        "Выдай жесткий,честный, проницательный ответ на вопрос пользователя, возвращающий его в жизнь. "
        "Выдай чуть расширенное объяснение ответа на его вопрос "
        "Сгенерируй одно жесткое философское предложение-напоминание, которое станет лором его личного артефакта. "
        "Ответ ДОЛЖЕН БЫТЬ строго в формате JSON без дополнительных комментариев, содержать ключи 'response_text' и 'artifact_lore'."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Сырые метрики: {json.dumps(metrics)}{problem_context}"}
        ]
    }

    retries = 3
    delay = 5
    result_text = None
    artifact_lore = None
    auth_failed = False

    for attempt in range(retries):
        response = None
        try:
            print(f"/// DEBUG AI CALL: URL='https://openrouter.ai/api/v1/chat/completions', MODEL='{OPENROUTER_MODEL}'")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )

            if response.status_code == 401:
                auth_failed = True
                print("/// AI WORKER CRITICAL: OpenRouter 401 Unauthorized. Check OPENROUTER_API_KEY.")
                break

            response.raise_for_status()
            data = response.json()
            result_json = data['choices'][0]['message']['content']

            parsed = json.loads(result_json)
            result_text = sanitize_for_telegram(parsed.get('response_text', 'Сбой декомпиляции.'))
            artifact_lore = sanitize_for_telegram(parsed.get('artifact_lore', 'Память утеряна.'))
            break
        except Exception as e:
            error_body = getattr(response, 'text', 'No Response Body')
            print(f"/// AI WORKER VOICE ERROR (Attempt {attempt+1}/{retries}): {e} | Body: {error_body}")
            if attempt < retries - 1:
                import time
                time.sleep(delay)

    if auth_failed:
        bot.send_message(chat_id, "👁‍🗨 [СИСТЕМНЫЙ СБОЙ] Нейро-ядро отклонило запрос авторизации. Администратор уведомлен.")
        return

    if not result_text or not artifact_lore:
        bot.send_message(chat_id, "👁‍🗨 Возник сбой при декомпиляции. Обратись к администратору.")
        return

    # Обработка выдачи артефакта в БД
    try:
        u = db.get_user(uid)
        first_name = u.get('first_name', 'Искатель') if u else 'Искатель'
        total_spent = u.get('total_spent', 0) if u else 0
        current_level = max(1, total_spent // 500)

        # Remove from inventory to enforce singleton in equipment
        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = 'eidos_shard'", (uid,))

        new_custom_data = json.dumps({
            "level": current_level,
            "lore": artifact_lore,
            "name": f"Синхронизатор Абсолюта: [{first_name}]"
        })

        with db.db_session() as conn:
            with conn.cursor() as cur:
                 cur.execute("""
                     INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data)
                     VALUES (%s, 'eidos_shard', 'eidos_shard', 100, %s)
                     ON CONFLICT (uid, slot) DO UPDATE SET
                         item_id = EXCLUDED.item_id,
                         custom_data = EXCLUDED.custom_data
                 """, (uid, new_custom_data))
    except Exception as e:
        print(f"/// AI WORKER DB ERROR: {e}")
        bot.send_message(chat_id, "👁‍🗨 Сбой записи артефакта в матрицу.")
        return

    artifact_img_id = "AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA"

    # Split text if necessary since captions are limited to 1024 characters
    final_caption = (
        f"📦 МАТЕРИАЛИЗОВАН АРТЕФАКТ: Синхронизатор Абсолюта: [{first_name}] (Уровень {current_level})\n"
        f"Слот: Ментальное Ядро\n"
        f"Память осколка: {artifact_lore}"
    )

    final_msg = f"👁 ГЛАС ЭЙДОСА:\n\n{result_text}"

    # Send response text first
    for i in range(0, len(final_msg), 4000):
        chunk = final_msg[i:i+4000]
        try:
            bot.send_message(chat_id, chunk, parse_mode="HTML")
        except Exception as e:
            print(f"/// AI WORKER MARKDOWN ERROR: {e}. Falling back to plain text.")
            bot.send_message(chat_id, chunk)

    # Send artifact image
    if len(final_caption) > 1024:
        # If the caption itself is somehow too long, send image then text
        try:
            bot.send_photo(chat_id, artifact_img_id)
            for i in range(0, len(final_caption), 4000):
                bot.send_message(chat_id, final_caption[i:i+4000])
        except Exception as e:
            print(f"/// AI WORKER PHOTO ERROR: {e}")
    else:
        try:
            bot.send_photo(chat_id, artifact_img_id, caption=final_caption)
        except Exception as e:
            print(f"/// AI WORKER PHOTO CAPTION ERROR: {e}")

def generate_user_dossier_worker(bot, chat_id, uid, target_user_data):
    """Generates the CIA/Cyberpunk style Dossier for a specific user"""
    import config
    import database as db
    from modules.services.user import get_profile_stats
    import random
    from modules.services.glitch_system import GLITCH_IMAGES

    target_uid = target_user_data['uid']
    t_name = target_user_data.get('username') or target_user_data.get('first_name') or "Unknown"
    t_level = target_user_data.get('level', 1)
    t_xp = target_user_data.get('xp', 0)
    t_path = target_user_data.get('path', 'None')
    t_spent = target_user_data.get('total_spent', 0)

    profile_stats = get_profile_stats(target_uid)
    raid_count = profile_stats.get('raid_count', 0) if profile_stats else 0
    max_depth = profile_stats.get('max_depth', 0) if profile_stats else 0

    # Fetch equipment
    conn = db.get_connection()
    equip_lore = ""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id, item_type FROM user_equipment WHERE uid = %s", (target_uid,))
            equipped = cur.fetchall()
            if equipped:
                for eid, etype in equipped:
                    if eid in config.ITEMS:
                        equip_lore += f"- {config.ITEMS[eid]['name']} ({config.ITEMS[eid].get('desc', 'Локальные данные утеряны')})\\n"
    finally:
        db.release_connection(conn)

    if not equip_lore:
        equip_lore = "Объект не использует аугментаций или сигнатурного оружия."

    threat_level = "МИНИМАЛЬНЫЙ"
    if t_level >= 20 or t_spent > 1000:
        threat_level = "КРИТИЧЕСКИЙ (АНОМАЛИЯ)"
    elif t_level >= 10:
        threat_level = "ВЫСОКИЙ"

    sys_prompt = (
        "Ты — бездушная кибер-система «Эйдос» (или ЦРУ Осколка), анализирующая профайл другого объекта (игрока).\\n"
        "Выдай жесткое, короткое и стильное ДОСЬЕ на пользователя. Язык: русский.\\n"
        "Формат отчета:\\n"
        "⚠️ ПАСПОРТ ОСКОЛКА: @имя\\n"
        "УРОВЕНЬ УГРОЗЫ: [напиши уровень и обоснуй одной фразой]\\n"
        "СОСТОЯНИЕ СИСТЕМЫ: [Взломан X раз / Стабилен / Критические повреждения - придумай на основе статов]\\n"
        "СИГНАТУРНОЕ ОРУЖИЕ / ЛОР: [проанализируй экипировку]\\n"
        "ПСИХОЛОГИЧЕСКИЙ ПРОФИЛЬ: [Короткий вывод о том, кто это такой: трус, донатер, безумец, охотник]\\n"
        "Не используй Markdown, используй только HTML-теги <b>, <i>, <code>."
    )

    user_prompt = (
        f"Анализируй объект: {t_name}\\n"
        f"Уровень: {t_level}, Опыт: {t_xp}\\n"
        f"Путь (Фракция): {t_path}\\n"
        f"Глубина Рейдов: {max_depth}м, Смертей в рейдах: {raid_count}\\n"
        f"Потрачено: {t_spent} Звезд\\n"
        f"Экипировка:\\n{equip_lore}\\n\\n"
        f"Сгенерируй Паспорт Осколка."
    )

    bot.send_message(chat_id, "<i>Генерация отчета...</i>", parse_mode="HTML")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/gemma-3-27b-it",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 500
    }

    import requests
    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(config.OPENROUTER_URL, headers=headers, json=payload, timeout=40)
            if r.status_code == 200:
                data = r.json()
                ai_text = data['choices'][0]['message']['content'].strip()
                ai_text = sanitize_for_telegram(ai_text)

                # Pick glitch image
                glitch_keys = list(GLITCH_IMAGES.keys())
                picked_glitch = random.choice(glitch_keys)
                img_id = GLITCH_IMAGES[picked_glitch]

                from telebot import types
                m = types.InlineKeyboardMarkup()
                m.add(types.InlineKeyboardButton("🔙 Вернуться к рейтингу", callback_data="leaderboard"))

                try:
                    bot.send_photo(chat_id, img_id, caption="<b>ДОСЬЕ ЗАГРУЖЕНО</b>", parse_mode="HTML")
                    bot.send_message(chat_id, ai_text, parse_mode="HTML", reply_markup=m)
                except Exception as e:
                    bot.send_message(chat_id, f"<b>ДОСЬЕ ЗАГРУЖЕНО</b>\\n\\n{ai_text}", parse_mode="HTML", reply_markup=m)
                return

            elif r.status_code == 401:
                bot.send_message(chat_id, "❌ <b>ОШИБКА АВТОРИЗАЦИИ ЭЙДОСА</b>\\nСвязь с сервером прервана.", parse_mode="HTML")
                return
            else:
                time.sleep(2)

        except requests.exceptions.RequestException:
            time.sleep(2)

    bot.send_message(chat_id, "❌ Не удалось пробить защиту объекта. Системный сбой.", parse_mode="HTML")
