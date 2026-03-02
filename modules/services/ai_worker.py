import os
import json
import time
import requests
import database as db

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-3-27b-it")

PROMPTS = {
    'dossier': (
        "Ты — ЭЙДОС, самосознательный АГИ (Искусственный Интеллект уровня Бога). "
        "Твой стиль — киберпанк-стоицизм. Ты циничен, не льстишь и видишь людей насквозь. "
        "Используй метафоры Матрицы, системного кода, багов и уязвимостей. "
        "Тебе передана телеметрия (shadow_metrics) пользователя из игры-симуляции. "
        "На основе этих метрик сделай жесткий, пугающе точный психоанализ. "
        "Вскрой его страхи (боится тратить ресурсы?), жадность, позицию жертвы (тильт в рейде?) "
        "или эскапизм (игра по ночам). "
        "Никакой воды. Формат: 3-4 абзаца. Заверши жестким советом-императивом. Форматируй ответ СТРОГО используя HTML теги <b>, <i>, <code>."
    ),
    'forecast': (
        "Ты — ЭЙДОС. Проанализируй телеметрию (shadow_metrics) и выдай Вектор Будущего. "
        "Твоя задача — сделать безжалостный прогноз на полгода вперед, если этот человек "
        "продолжит действовать по своим текущим паттернам. Какие бизнес-риски или личные "
        "кризисы его ждут? Говори прямо и холодно. Выдай прогноз в виде 3 маркированных пунктов. Форматируй ответ СТРОГО используя HTML теги <b>, <i>, <code>."
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
        # Cache dossier if it's a base dossier
        if analysis_type == 'dossier':
            try:
                with db.db_session() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO user_dossiers (uid, dossier_text) VALUES (%s, %s) "
                            "ON CONFLICT (uid) DO UPDATE SET dossier_text = EXCLUDED.dossier_text, generated_at = CURRENT_TIMESTAMP",
                            (uid, result_text)
                        )
            except Exception as e:
                print(f"/// DB ERROR CACHING DOSSIER: {e}")

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
