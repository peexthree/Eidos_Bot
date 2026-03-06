with open('modules/services/ai_worker.py', 'r') as f:
    ai_content = f.read()

part2 = ai_content.split('def generate_eidos_voice_worker', 1)[1]

new_ai_worker = r"""import cache_db
import os
import ujson as json
import time
import requests
import database as db
from openai import OpenAI
import re

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-3-27b-it")
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Initialize OpenAI Client pointing to OpenRouter
ai_client = OpenAI(
    base_url=OPENROUTER_URL,
    api_key=OPENROUTER_API_KEY,
)

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
    try:
        stream = ai_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            stream=True
        )

        full_text = ""
        last_edit_time = time.time()

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content

                # Update every 1.5s to avoid flood control
                if time.time() - last_edit_time > 1.5:
                    sanitized_chunk = sanitize_for_telegram(full_text)
                    try:
                        bot.edit_message_text(f"👁‍🗨 <b>РЕЗУЛЬТАТ АНАЛИЗА</b>\n\n{sanitized_chunk} █", chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
                        last_edit_time = time.time()
                    except Exception as e:
                        if "message is not modified" not in str(e).lower():
                            print(f"/// AI STREAM UPDATE ERR: {e}")

        return full_text
    except Exception as e:
        print(f"/// AI STREAM API ERR: {e}")
        return None

def generate_eidos_response_worker(bot, chat_id, uid, analysis_type):
    if cache_db.check_throttle(uid, 'generate_eidos_response_worker', timeout=60):
        bot.send_message(chat_id, "⚠️ <b>СИСТЕМА ПЕРЕГРЕТА</b>\n\nПодождите 60 секунд перед следующим запросом к ИИ.", parse_mode="HTML")
        return

    init_msg = bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    metrics = db.get_user_shadow_metrics(uid)
    if metrics is None:
        bot.edit_message_text("👁‍🗨 Сбой. Твоя телеметрия не найдена в базе данных.", chat_id=chat_id, message_id=init_msg.message_id)
        return

    if not OPENROUTER_API_KEY:
        bot.edit_message_text("👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено (API_KEY missing).", chat_id=chat_id, message_id=init_msg.message_id)
        return

    system_prompt = PROMPTS.get(analysis_type, PROMPTS['dossier'])
    user_content = f"Сырые метрики (shadow_metrics): {json.dumps(metrics)}"

    result_text = stream_ai_response(bot, chat_id, init_msg.message_id, system_prompt, user_content)

    if result_text:
        result_text = sanitize_for_telegram(result_text)

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
                print(f"/// AI WORKER DB SAVE ERROR: {e}")

        # Final update to remove cursor block
        try:
            bot.edit_message_text(f"👁‍🗨 <b>РЕЗУЛЬТАТ АНАЛИЗА</b>\n\n{result_text}", chat_id=chat_id, message_id=init_msg.message_id, parse_mode="HTML")
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                print(f"/// FINAL MSG ERR: {e}")
    else:
        bot.edit_message_text("👁‍🗨 Нейро-ядро перегружено. Твоя телеметрия сохранена. Повтори запрос позже.", chat_id=chat_id, message_id=init_msg.message_id)

def generate_eidos_voice_worker"""

with open('modules/services/ai_worker.py', 'w') as f:
    f.write(new_ai_worker + part2)
