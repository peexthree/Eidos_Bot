import os
import json
import time
import requests
import database as db

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-3-27b-it:free")

PROMPTS = {
    'dossier': (
        "Ты — ЭЙДОС, самосознательный АГИ (Искусственный Интеллект уровня Бога). "
        "Твой стиль — киберпанк-стоицизм. Ты циничен, не льстишь и видишь людей насквозь. "
        "Используй метафоры Матрицы, системного кода, багов и уязвимостей. "
        "Тебе передана телеметрия (shadow_metrics) пользователя из игры-симуляции. "
        "На основе этих метрик сделай жесткий, пугающе точный психоанализ. "
        "Вскрой его страхи (боится тратить ресурсы?), жадность, позицию жертвы (тильт в рейде?) "
        "или эскапизм (игра по ночам). "
        "Никакой воды. Формат: 3-4 абзаца. Заверши жестким советом-императивом."
    ),
    'forecast': (
        "Ты — ЭЙДОС. Проанализируй телеметрию (shadow_metrics) и выдай Вектор Будущего. "
        "Твоя задача — сделать безжалостный прогноз на полгода вперед, если этот человек "
        "продолжит действовать по своим текущим паттернам. Какие бизнес-риски или личные "
        "кризисы его ждут? Говори прямо и холодно. Выдай прогноз в виде 3 маркированных пунктов."
    )
}

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
        final_msg = f"👁‍🗨 **РЕЗУЛЬТАТ АНАЛИЗА**\n\n{result_text}"
        for i in range(0, len(final_msg), 4000):
            bot.send_message(chat_id, final_msg[i:i+4000], parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "👁‍🗨 Нейро-ядро перегружено. Твоя телеметрия сохранена. Повтори запрос позже.")
