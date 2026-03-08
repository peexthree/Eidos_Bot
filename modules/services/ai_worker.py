import cache_db
import os
import json
import time
import requests
import database as db
from openai import OpenAI
import re
import logging
import config

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-3-27b-it")
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Initialize OpenAI Client safely
ai_client = None
if OPENROUTER_API_KEY:
    try:
        ai_client = OpenAI(
            base_url=OPENROUTER_URL,
            api_key=OPENROUTER_API_KEY,
        )
    except Exception as e:
        print(f"/// AI CLIENT INIT ERROR: {e}", flush=True)
else:
    print("/// OPENROUTER_API_KEY is missing! AI features will be disabled.", flush=True)

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

def sanitize_for_telegram(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'</?(br|p|div)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li>(.*?)</li>', r'• \1\n', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'</?(ul|ol|li)>', '', text, flags=re.IGNORECASE)

    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'a', 'code', 'pre']
    tag_pattern = r'</?([a-zA-Z0-9]+)[^>]*>'

    def replacer(match):
        tag_name = match.group(1).lower()
        if tag_name in allowed_tags:
            return match.group(0)
        return ''

    text = re.sub(tag_pattern, replacer, text)

    for tag in ['b', 'i', 'code', 'u', 's', 'strong', 'em']:
        open_count = text.lower().count(f'<{tag}>')
        close_count = text.lower().count(f'</{tag}>')
        if open_count > close_count:
            text += f'</{tag}>' * (open_count - close_count)

    return text.strip()

def stream_ai_response(bot, chat_id, msg_id, system_prompt, user_content):
    if not ai_client:
        return None
    try:
        stream = ai_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            stream=True, timeout=15.0
        )

        full_text = ""
        last_edit_time = time.time()

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content

                if time.time() - last_edit_time > 1.5:
                    sanitized_chunk = sanitize_for_telegram(full_text)
                    try:
                        bot.edit_message_text(f"👁‍🗨 <b>РЕЗУЛЬТАТ АНАЛИЗА</b>\n\n{sanitized_chunk} █", chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
                        last_edit_time = time.time()
                    except Exception as e:
                        if "message is not modified" not in str(e).lower():
                            print(f"/// AI STREAM UPDATE ERR: {e}", flush=True)

        return full_text
    except Exception as e:
        print(f"/// AI STREAM API ERR: {e}", flush=True)
        return None

def generate_eidos_response_worker(bot, chat_id, uid, analysis_type, charge_id=None, amount=None):
    print(f"[AI WORKER] Started processing request for UID {uid}", flush=True)
    if cache_db.check_throttle(uid, 'generate_eidos_response_worker', timeout=60):
        bot.send_message(chat_id, "⚠️ <b>СИСТЕМА ПЕРЕГРЕТА</b>\n\nПодождите 60 секунд перед следующим запросом к ИИ.", parse_mode="HTML")
        return

    init_msg = bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    def handle_failure(error_msg):
        bot.edit_message_text(error_msg, chat_id=chat_id, message_id=init_msg.message_id)
        if charge_id:
            try:
                bot.refund_star_payment(uid, charge_id)
                u = db.get_user(uid)
                if u and amount:
                    db.update_user(uid, total_spent=max(0, u.get('total_spent', 0) - amount))
                bot.send_message(chat_id, f"💳 Средства (Stars) были возвращены на ваш баланс из-за сбоя системы.")
            except Exception as e:
                print(f"/// AI REFUND ERROR: {e}", flush=True)

    try:
        metrics = db.get_user_shadow_metrics(uid)
        if metrics is None:
            handle_failure("👁‍🗨 Сбой. Твоя телеметрия не найдена в базе данных.")
            return

        if not ai_client:
            handle_failure("👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено (API connection failed).")
            return

        system_prompt = PROMPTS.get(analysis_type, PROMPTS['dossier'])
        user_content = f"Сырые метрики (shadow_metrics): {json.dumps(metrics)}"

        print(f"[AI WORKER] Sending request to OpenRouter for UID {uid}...", flush=True)
        result_text = stream_ai_response(bot, chat_id, init_msg.message_id, system_prompt, user_content)

        if result_text:
            result_text = sanitize_for_telegram(result_text)
            print(f"[AI WORKER] Received response from OpenRouter for UID {uid}. Status OK.", flush=True)

            if analysis_type == 'dossier':
                try:
                    with db.db_cursor() as cur:
                        if cur:
                            cur.execute("INSERT INTO user_dossiers (uid, dossier_text) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET dossier_text = EXCLUDED.dossier_text, generated_at = CURRENT_TIMESTAMP", (uid, result_text))
                except Exception as e:
                    print(f"/// AI WORKER DB SAVE ERROR: {e}", flush=True)

            try:
                print(f"[AI WORKER] Attempting to send text to Telegram for UID {uid}...", flush=True)
                final_text = f"👁‍🗨 <b>РЕЗУЛЬТАТ АНАЛИЗА</b>\n\n{result_text}"
                if len(final_text) > 4000:
                    bot.delete_message(chat_id, init_msg.message_id)
                    for i in range(0, len(final_text), 4000):
                        chunk = final_text[i:i+4000]
                        try:
                            bot.send_message(chat_id, chunk, parse_mode="HTML")
                            print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
                        except Exception as e:
                            print(f"/// AI WORKER MARKDOWN ERROR: {e}", flush=True)
                            bot.send_message(chat_id, chunk)
                else:
                    bot.edit_message_text(final_text, chat_id=chat_id, message_id=init_msg.message_id, parse_mode="HTML")
                    print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
            except Exception as e:
                if "message is not modified" not in str(e).lower():
                    print(f"/// FINAL MSG ERR: {e}", flush=True)
                    bot.send_message(chat_id, result_text[:4000]) # Fallback plain text
                    print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
        else:
            handle_failure("👁‍🗨 Нейро-ядро перегружено или недоступно. Твоя телеметрия сохранена. Повтори запрос позже.")
    except Exception as e:
        import traceback; print(f"[AI WORKER] FATAL ERROR for UID {uid}: {str(e)}", flush=True); traceback.print_exc()
        handle_failure("👁‍🗨 Произошла непредвиденная ошибка при генерации ответа.")

def generate_eidos_voice_worker(bot, chat_id, uid, user_text=None, charge_id=None, amount=None):
    print(f"[AI WORKER] Started processing request for UID {uid}", flush=True)
    if cache_db.check_throttle(uid, 'generate_eidos_voice_worker', timeout=60):
        bot.send_message(chat_id, "⚠️ <b>СИСТЕМА ПЕРЕГРЕТА</b>\n\nПодождите 60 секунд перед следующим запросом к ИИ.", parse_mode="HTML")
        return

    init_msg = bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    def handle_failure(error_msg):
        bot.edit_message_text(error_msg, chat_id=chat_id, message_id=init_msg.message_id)
        if charge_id:
            try:
                bot.refund_star_payment(uid, charge_id)
                u = db.get_user(uid)
                if u and amount:
                    db.update_user(uid, total_spent=max(0, u.get('total_spent', 0) - amount))
                bot.send_message(chat_id, f"💳 Средства (Stars) были возвращены на ваш баланс из-за сбоя системы.")
            except Exception as e:
                print(f"/// AI REFUND ERROR: {e}", flush=True)

    try:
        if not ai_client:
            handle_failure("👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено.")
            return

        metrics = db.get_user_shadow_metrics(uid)
        if metrics is None:
            handle_failure("👁‍🗨 Сбой. Твоя телеметрия не найдена.")
            return

        problem_context = f"\nПроблема носителя: {user_text}" if user_text else "\nАнализ текущего вектора (автоматический режим)."

        system_prompt = (
            "Ты — Эйдос, древний АГИ. Игрок — биологический носитель фрагмента твоей души. "
            "Он заплатил за контакт. Проанализируй его текущую телеметрию и (если указано) его проблему. "
            "Выдай жесткий,честный, проницательный ответ на вопрос пользователя, возвращающий его в жизнь. "
            "Выдай чуть расширенное объяснение ответа на его вопрос "
            "Сгенерируй одно жесткое философское предложение-напоминание, которое станет лором его личного артефакта. "
            "Твой ответ ДОЛЖЕН БЫТЬ строго в следующем текстовом формате:\n"
            "ОТВЕТ: <твой жесткий философский ответ и анализ>\n\n"
            "ЛОР: <одно философское предложение для артефакта>"
        )

        full_text = ""
        last_edit_time = time.time()
        try:
            print(f"[AI WORKER] Sending request to OpenRouter for UID {uid}...", flush=True)
            stream = ai_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Сырые метрики: {json.dumps(metrics)}{problem_context}"}
                ],
                stream=True, timeout=15.0
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_text += chunk.choices[0].delta.content
                    if time.time() - last_edit_time > 1.5:
                        sanitized_chunk = sanitize_for_telegram(full_text)
                        try:
                            bot.edit_message_text(f"👁‍🗨 <b>СИНХРОНИЗАЦИЯ...</b>\n\n{sanitized_chunk} █", chat_id=chat_id, message_id=init_msg.message_id, parse_mode="HTML")
                            last_edit_time = time.time()
                        except Exception as e:
                            pass

            parts = full_text.split("ЛОР:")
            if len(parts) > 1:
                result_text = sanitize_for_telegram(parts[0].replace("ОТВЕТ:", "").strip())
                artifact_lore = sanitize_for_telegram(parts[1].strip())
                print(f"[AI WORKER] Received response from OpenRouter for UID {uid}. Status OK.", flush=True)
            else:
                result_text = sanitize_for_telegram(full_text.replace("ОТВЕТ:", "").strip())
                artifact_lore = "Память утеряна."

        except Exception as e:
            print(f"/// AI WORKER VOICE ERROR: {e}", flush=True)
            handle_failure("👁‍🗨 [СИСТЕМНЫЙ СБОЙ] Нейро-ядро недоступно.")
            return

        if not result_text or not artifact_lore:
            handle_failure("👁‍🗨 Возник сбой при декомпиляции. Обратись к администратору.")
            return

        try:
            bot.delete_message(chat_id, init_msg.message_id)
        except:
            pass

        try:
            u = db.get_user(uid)
            first_name = u.get('first_name', 'Искатель') if u else 'Искатель'
            total_spent = u.get('total_spent', 0) if u else 0
            current_level = max(1, total_spent // 500)

            new_custom_data = json.dumps({
                "level": current_level,
                "lore": artifact_lore,
                "name": f"Синхронизатор Абсолюта: [{first_name}]"
            })

            with db.db_cursor() as cur:
                if cur:
                    cur.execute("DELETE FROM user_equipment WHERE uid = %s AND item_id = 'eidos_shard'", (uid,))
                    cur.execute("INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data) VALUES (%s, 'eidos_shard', 'eidos_shard', 100, %s) ON CONFLICT (uid, slot) DO UPDATE SET item_id = EXCLUDED.item_id, custom_data = EXCLUDED.custom_data", (uid, new_custom_data))

        except Exception as e:
            print(f"/// AI WORKER DB ERROR: {e}", flush=True)
            handle_failure("👁‍🗨 Сбой записи артефакта в матрицу.")
            return

        artifact_img_id = "AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA"

        final_caption = (
            f"📦 МАТЕРИАЛИЗОВАН АРТЕФАКТ: Синхронизатор Абсолюта: [{first_name}] (Уровень {current_level})\n"
            f"Слот: Ментальное Ядро\n"
            f"Память осколка: {artifact_lore}"
        )

        print(f"[AI WORKER] Attempting to send text to Telegram for UID {uid}...", flush=True)
        final_msg = f"👁 ГЛАС ЭЙДОСА:\n\n{result_text}"

        for i in range(0, len(final_msg), 4000):
            chunk = final_msg[i:i+4000]
            try:
                bot.send_message(chat_id, chunk, parse_mode="HTML")
                print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
            except Exception as e:
                print(f"/// AI WORKER MARKDOWN ERROR: {e}. Falling back to plain text.", flush=True)
                bot.send_message(chat_id, chunk)

        if len(final_caption) > 1024:
            try:
                bot.send_photo(chat_id, artifact_img_id)
                for i in range(0, len(final_caption), 4000):
                    bot.send_message(chat_id, final_caption[i:i+4000])
                    print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
            except Exception as e:
                print(f"/// AI WORKER PHOTO ERROR: {e}", flush=True)
        else:
            try:
                bot.send_photo(chat_id, artifact_img_id, caption=final_caption)
                print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
            except Exception as e:
                print(f"/// AI WORKER PHOTO CAPTION ERROR: {e}", flush=True)

    except Exception as e:
        import traceback; print(f"[AI WORKER] FATAL ERROR for UID {uid}: {str(e)}", flush=True); traceback.print_exc()
        handle_failure("👁‍🗨 Произошла непредвиденная ошибка при генерации ответа.")

def generate_user_dossier_worker(bot, chat_id, uid, target_user_data, loading_msg_id=None, refund_bc=None):
    print(f"[AI WORKER] Started processing request for UID {uid}", flush=True)
    if cache_db.check_throttle(uid, 'generate_user_dossier_worker', timeout=60):
        bot.send_message(chat_id, "⚠️ <b>СИСТЕМА ПЕРЕГРЕТА</b>\n\nПодождите 60 секунд перед следующим запросом к ИИ.", parse_mode="HTML")
        if 'loading_msg_id' in locals() and loading_msg_id:
            try: bot.delete_message(chat_id, loading_msg_id)
            except: pass
        return

    import database as db
    from modules.services.user import get_profile_stats
    import random
    import urllib.parse

    def update_progress(perc, status):
        if loading_msg_id:
            bar = '█' * (perc // 10) + '░' * (10 - (perc // 10))
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=loading_msg_id,
                    text=f"📡 <b>УСТАНОВКА СОЕДИНЕНИЯ...</b>\n{status}... [<code>{bar}</code>] {perc}%",
                    parse_mode="HTML"
                )
            except: pass

    update_progress(10, "Инициализация протоколов")

    target_uid = target_user_data['uid']
    t_name = target_user_data.get('username') or target_user_data.get('first_name') or "Unknown"
    t_level = target_user_data.get('level', 1)
    t_xp = target_user_data.get('xp', 0)
    t_path = target_user_data.get('path', 'None')
    t_spent = target_user_data.get('total_spent', 0)

    update_progress(30, "Дешифровка логов игрока")

    profile_stats = get_profile_stats(target_uid)
    raid_count = profile_stats.get('raid_count', 0) if profile_stats else 0
    max_depth = profile_stats.get('max_depth', 0) if profile_stats else 0

    shadows = db.get_user_shadow_metrics(target_uid) or {}
    glitches_count = shadows.get('glitches_encountered_count', 0)
    stability = max(0, 100 - (glitches_count * 7))

    update_progress(50, "Компиляция психопрофиля")

    equip_list = []
    with db.db_cursor() as cur:
        if cur:
            cur.execute("SELECT item_id FROM user_equipment WHERE uid = %s", (target_uid,))
            equipped = cur.fetchall()
            if equipped:
                for (eid,) in equipped:
                    if eid in config.ITEMS_INFO:
                        equip_list.append(config.ITEMS_INFO[eid]['name'])
                    elif hasattr(config, 'EQUIPMENT_DB') and eid in config.EQUIPMENT_DB:
                        equip_list.append(config.EQUIPMENT_DB[eid]['name'])

    inv_text = ", ".join(equip_list) if equip_list else "Отсутствует"

    threat_level = "MINIMAL"
    if t_level >= 30 or t_spent > 5000:
        threat_level = "CRITICAL_ANOMALY"
    elif t_level >= 15 or t_spent > 1000:
        threat_level = "HIGH_DEVIANT"
    elif t_level >= 5:
        threat_level = "MEDIUM_DEVIANT"

    d_id = f"{random.randint(1000, 9999)}-{t_name.upper()[:10]}"
    school_name = getattr(config, 'SCHOOLS', {}).get(t_path, 'ОБЩАЯ')

    sys_prompt = (
        "Ты — бездушная кибер-система «Эйдос», проводящая глубокий психоанализ и технический аудит объекта.\n"
        "Твоя задача — составить ДОСЬЕ в жестком стиле киберпанка/CIA. Язык: русский.\n\n"
        "СТРОГО СОБЛЮДАЙ СЛЕДУЮЩИЙ ФОРМАТ (используй HTML теги <b>, <i>, <code>):\n"
        "🗄 /// [DOSSIER_ID: " + d_id + "]\n"
        "<b>ОБЪЕКТ:</b> @" + t_name + "\n"
        "<b>СТАТУС:</b> Под наблюдением Эйдоса\n"
        "<b>УРОВЕНЬ:</b> " + str(t_level) + "\n"
        "<b>ФРАКЦИЯ:</b> " + school_name + "\n"
        "<b>ЭКИПИРОВКА:</b> " + inv_text[:200] + "\n\n"
        "[ СИСТЕМНЫЙ АНАЛИЗ ]\n"
        "● <b>УРОВЕНЬ УГРОЗЫ:</b> " + threat_level + " (на русском)\n"
        "● <b>СТАБИЛЬНОСТЬ:</b> " + str(stability) + "% (" + str(glitches_count) + " критических взлома в логах)\n"
        "● <b>КЛАССИФИКАЦИЯ:</b> [придумай на основе статов, напр. Охотник за Глубиной, Техно-Наемник и т.д.]\n\n"
        "[ ТЕХНОЛОГИЧЕСКИЙ СЛЕД ]\n\n"
        "<b>СИГНАТУРА:</b> [проанализируй снаряжение, выдели главное]\n"
        "<b>ВЕРДИКТ:</b> [Техническое заключение об опасности снаряжения]\n\n"
        "[ ПСИХОПРОФИЛЬ ]\n"
        "[Глубокий, мрачный анализ личности игрока на основе его достижений и трат. Используй цитаты в кавычках.]\n\n"
        "[ ДИРЕКТИВА ЭЙДОСА ]\n"
        "<b>Опираться на объект в долгосрочных союзах —</b> [ВЕРДИКТ].\n"
        "<b>Использовать как таран в зонах высокого сопротивления —</b> [ВЕРДИКТ].\n\n"
        "ВАЖНО: НЕ используй Markdown, НЕ используй блоки кода ```html или ```. Только чистый текст с HTML тегами <b>, <i>, <code>."
    )

    user_prompt = (
        f"Данные объекта: {t_name}\n"
        f"Уровень: {t_level}, Опыт: {t_xp}\n"
        f"Путь: {t_path}\n"
        f"Рейды: {raid_count}, Макс. Глубина: {max_depth}м\n"
        f"Взломы системы: {glitches_count}\n"
        f"Потрачено: {t_spent} Stars\n"
        f"Экипировка: {inv_text}\n\n"
        f"Сгенерируй Паспорт Осколка по шаблону."
    )

    update_progress(70, "Запрос к архивам OpenRouter")

    if not ai_client:
        bot.edit_message_text("❌ [СИСТЕМНЫЙ СБОЙ] ИИ-ядро не подключено.", chat_id=chat_id, message_id=loading_msg_id)
        if refund_bc:
            try:
                u = db.get_user(uid)
                if u:
                    db.update_user(uid, biocoin=u.get("biocoin", 0) + refund_bc)
                    bot.send_message(chat_id, f"💳 Ошибка нейро-сети. {refund_bc} BC возвращены на счет.")
            except: pass
        return

    ai_text = ""
    last_edit_time = time.time()
    for attempt in range(3):
        try:
            print(f"[AI WORKER] Sending request to OpenRouter for UID {uid}...", flush=True)
            stream = ai_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True, timeout=15.0
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    ai_text += chunk.choices[0].delta.content
                    if loading_msg_id and time.time() - last_edit_time > 1.5:
                        sanitized_chunk = sanitize_for_telegram(ai_text)
                        try:
                            bot.edit_message_text(f"📡 <b>УСТАНОВКА СОЕДИНЕНИЯ...</b>\nДешифровка данных...\n\n{sanitized_chunk} █", chat_id=chat_id, message_id=loading_msg_id, parse_mode="HTML")
                            last_edit_time = time.time()
                        except Exception as e:
                            pass

            ai_text = ai_text.replace('```html', '').replace('```', '').strip()
            ai_text = sanitize_for_telegram(ai_text)
            print(f"[AI WORKER] Received response from OpenRouter for UID {uid}. Status OK.", flush=True)
            break
        except Exception as e:
            print(f"/// AI WORKER DOSSIER STREAM ERR: {e}", flush=True)
            time.sleep(2)

    if loading_msg_id:
        try: bot.delete_message(chat_id, loading_msg_id)
        except: pass

    if not ai_text:
        bot.send_message(chat_id, "❌ Не удалось пробить защиту объекта. Системный сбой.", parse_mode="HTML")
        if refund_bc:
            try:
                u = db.get_user(uid)
                if u:
                    db.update_user(uid, biocoin=u.get("biocoin", 0) + refund_bc)
                    bot.send_message(chat_id, f"💳 Ошибка нейро-сети. {refund_bc} BC возвращены на счет.")
            except: pass
        return

    try:
        # ИСПРАВЛЕНИЕ 3: Переход на db_cursor()
        with db.db_cursor() as cur:
            if cur:
                cur.execute("INSERT INTO user_dossiers (uid, dossier_text) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET dossier_text = EXCLUDED.dossier_text, generated_at = CURRENT_TIMESTAMP", (target_uid, ai_text))
    except Exception as e:
        print(f"/// AI WORKER DB INSERT ERROR: {e}", flush=True)

    img_id = getattr(config, 'USER_AVATARS', {}).get(t_level, getattr(config, 'USER_AVATARS', {}).get(1))

    from telebot import types
    m = types.InlineKeyboardMarkup(row_width=1)

    share_msg = f"Эйдос присвоил статус в системе. Узнай свой уровень угрозы в @Eidos_Chronicles_bot"
    share_url = f"https://t.me/share/url?url=https://t.me/Eidos_Chronicles_bot&text={urllib.parse.quote(share_msg)}"
    m.add(types.InlineKeyboardButton("📢 Поделиться Досье", url=share_url))

    if target_uid != uid:
        m.add(types.InlineKeyboardButton("⚔️ Атаковать (PvP)", callback_data=f"dossier_attack_{target_uid}"))
        m.add(types.InlineKeyboardButton("✉️ Отправить сообщение (100 BC)", callback_data=f"dossier_msg_{target_uid}"))

    m.add(types.InlineKeyboardButton("🔙 Вернуться к рейтингу", callback_data="leaderboard"))

    try:
        print(f"[AI WORKER] Attempting to send text to Telegram for UID {uid}...", flush=True)
        if img_id:
            bot.send_photo(chat_id, img_id, caption="<b>СОБРАНО ДОСЬЕ</b>", parse_mode="HTML")
        if len(ai_text) > 4000:
            for i in range(0, len(ai_text), 4000):
                bot.send_message(chat_id, ai_text[i:i+4000], parse_mode="HTML", reply_markup=m if i+4000 >= len(ai_text) else None)
                print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
        else:
            bot.send_message(chat_id, ai_text, parse_mode="HTML", reply_markup=m)
            print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
    except Exception:
        bot.send_message(chat_id, f"<b>СОБРАНО ДОСЬЕ</b>\n\n{ai_text}", parse_mode="HTML", reply_markup=m)
        print(f"[AI WORKER] Successfully sent Telegram message for UID {uid}.", flush=True)
