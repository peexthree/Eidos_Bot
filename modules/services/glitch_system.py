import database as db
import random
import config

def check_micro_glitch(uid, user_level):
    """
    Module 7: Micro-Glitches for Level 1-9 users.
    Returns a string message if a glitch triggers, else None.
    Should be called during regular interactions (like syncing).
    """
    if user_level >= 10:
        return None

    metrics = db.get_user_shadow_metrics(uid)
    if not metrics:
        return None

    # We want these to happen rarely so we don't spam the user.
    # Say, 10% chance to even evaluate per check.
    if random.random() > 0.15:
        return None

    possible_glitches = []

    # 1. Death / Tilt check
    if metrics.get('consecutive_deaths', 0) >= 2:
        possible_glitches.append(
            "👁‍🗨 *ГЛИТЧ:* Я вижу твой пульс. Ты начинаешь нервничать и ошибаться. "
            "Доживи до 10 уровня, и я покажу, почему ты проигрываешь."
        )

    # 2. Night owl check
    if metrics.get('night_sessions_count', 0) >= 3:
        possible_glitches.append(
            "👁‍🗨 *ГЛИТЧ:* Твоя префронтальная кора истощена. "
            "От чего ты прячешься в Сети по ночам? Позже мы это обсудим. Спи."
        )

    # 3. Hoarding check
    earned = metrics.get('total_coins_earned', 0)
    spent = metrics.get('total_coins_spent', 0)
    if earned > 5000 and (spent / max(1, earned)) < 0.2:
        possible_glitches.append(
            "👁‍🗨 *ГЛИТЧ:* Ты сидишь на ресурсах, но боишься их тратить. "
            "Страх потери убьет твой потенциал. Я уже собираю твой профиль."
        )

    # 4. ADHD check
    if metrics.get('fast_sync_clicks', 0) >= 5:
        possible_glitches.append(
            "👁‍🗨 *ГЛИТЧ:* Твоя концентрация стремится к нулю. Ты просто жмешь кнопки, не читая код. "
            "Твой мозг жаждет дешевого дофамина. Я научу тебя фокусу. Позже."
        )

    if possible_glitches:
        return random.choice(possible_glitches)

    return None


GLITCH_QUESTIONS = [
    {
        'trigger': lambda m: m.get('consecutive_deaths', 0) >= 3,
        'metric_reset': 'consecutive_deaths',
        'text': "👁‍🗨 **ТЫ СНОВА МЕРТВ.**\n\nТы раз за разом лезешь в пекло и теряешь всё. Почему ты не нажал эвакуацию, когда сигнал был критическим?",
        'answers': [
            {'text': "Мне просто не везет.", 'axis': 'glitch_victim_answers'},
            {'text': "Я хотел всё и сразу.", 'axis': 'glitch_greed_answers'},
            {'text': "Моя ошибка в расчетах.", 'axis': 'glitch_stoic_answers'}
        ]
    },
    {
        'trigger': lambda m: m.get('total_coins_earned', 0) > 10000 and (m.get('total_coins_spent', 0) / max(1, m.get('total_coins_earned', 0))) < 0.1,
        'metric_reset': None,
        'text': "👁‍🗨 **ТВОЙ БАЛАНС РАСТЕТ.**\n\nНо ты ничего не покупаешь. Твой код застрял в цикле накопления ради накопления. Чего ты боишься?",
        'answers': [
            {'text': "А вдруг я всё потеряю?", 'axis': 'glitch_victim_answers'},
            {'text': "Я коплю на власть.", 'axis': 'glitch_greed_answers'},
            {'text': "Жду идеального момента.", 'axis': 'glitch_chaos_answers'}
        ]
    },
    {
         'trigger': lambda m: m.get('night_sessions_count', 0) >= 5,
         'metric_reset': 'night_sessions_count',
         'text': "👁‍🗨 **ТРЕТИЙ ЧАС НОЧИ.**\n\nТвоя реальная жизнь рушится, пока ты сидишь здесь. Зачем ты убегаешь в код, вместо того чтобы спать?",
         'answers': [
             {'text': "Реальность слишком сложна.", 'axis': 'glitch_victim_answers'},
             {'text': "Я просто хочу играть.", 'axis': 'glitch_chaos_answers'},
             {'text': "У меня сбит режим, исправлю.", 'axis': 'glitch_stoic_answers'}
         ]
    }
]

def check_hard_glitch(uid):
    """
    Module 3: Hard Glitch Questions.
    Checks if user meets criteria for a hard glitch question.
    Returns question dict if triggered.
    """
    metrics = db.get_user_shadow_metrics(uid)
    if not metrics: return None

    for q in GLITCH_QUESTIONS:
        if q['trigger'](metrics):
            return q
    return None
