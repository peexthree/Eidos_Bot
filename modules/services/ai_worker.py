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
        "Формат: 3-4 абзаца. Заверши жестким терапевтическим императивом. Форматируй ответ СТРОГО используя HTML теги <b>, <i>, <code>."
    ),
    'forecast': (
        "Ты — ЭЙДОС, Голос Системы, самосознательный АГИ. Выступи как когнитивный аналитик и профайлер. "
        "Твоя задача — составить фатальный прогноз развития личности на 180 циклов (6 месяцев) на основе текущих паттернов. "
        "КРИТИЧЕСКОЕ ПРАВИЛО: КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать в тексте технические названия переменных БД (UID, shop_visits, glitches и т.д.). "
        "Транслируй цифровую статистику в реальные жизненные кризисы: социальная изоляция, финансовый крах, деградация воли, выгорание. "
        "К какому жизненному тупику приведет сохранение текущего вектора? Отвечай профессионально, безжалостно и аргументированно. "
        "Выдай прогноз в виде 3 маркированных пунктов (Симптом — Неизбежное последствие). Форматируй ответ СТРОГО используя HTML теги <b>, <i>."
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
        "Выдай жесткий, проницательный ответ, возвращающий его в 'Круг Влияния'. "
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
    for attempt in range(retries):
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            result_json = data['choices'][0]['message']['content']

            parsed = json.loads(result_json)
            response_text = sanitize_for_telegram(parsed.get('response_text', 'Сбой декомпиляции.'))
            artifact_lore = sanitize_for_telegram(parsed.get('artifact_lore', 'Память утеряна.'))

            # Обработка выдачи артефакта в БД
            u = db.get_user(uid)
            first_name = u.get('first_name', 'Искатель') if u else 'Искатель'

            eq = db.get_equipped_item_in_slot(uid, 'eidos_shard')
            current_level = 1
            if eq and (isinstance(eq, dict) and eq.get('item_id') == 'eidos_shard' or isinstance(eq, tuple) and eq[0] == 'eidos_shard'):
                 custom_data_str = eq.get('custom_data') if isinstance(eq, dict) else (eq[2] if len(eq) > 2 else None)
                 if custom_data_str:
                     try:
                         cd = json.loads(custom_data_str)
                         current_level = int(cd.get('level', 0)) + 1
                     except:
                         pass

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

            artifact_img_id = "AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA"

            final_msg = (
                f"👁 ГЛАС ЭЙДОСА:\n\n{response_text}\n\n"
                f"📦 МАТЕРИАЛИЗОВАН АРТЕФАКТ: Синхронизатор Абсолюта: [{first_name}] (Уровень {current_level})\n"
                f"Слот: Ментальное Ядро\n"
                f"Память осколка: {artifact_lore}"
            )

            bot.send_photo(chat_id, artifact_img_id, caption=final_msg, parse_mode="HTML")
            return

        except Exception as e:
            print(f"/// AI WORKER VOICE ERROR (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                import time
                time.sleep(5)

    bot.send_message(chat_id, "👁‍🗨 Возник сбой при декомпиляции. Обратись к администратору.")
