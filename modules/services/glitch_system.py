import database as db
import random
import config

GLITCH_AVATARS = {
    'time_loop': 'AgACAgIAAyEFAATh7MR7AAPUaaYyM0FpO62yfwABAbAAAR03QpgqfgAC5xRrG3pLMEmCHTsgD2qdoAEAAwIAA3kAAzoE',
    'system_gaze': 'AgACAgIAAyEFAATh7MR7AAPTaaYyM4VDX21drMJeqU6IiT7LthsAAuYUaxt6SzBJAAHGB5xVpHBFAQADAgADeQADOgQ',
    'memory_fragment': 'AgACAgIAAyEFAATh7MR7AAPPaaYyM9yN2aWl9gXlt4JkObHoNQAD4hRrG3pLMEkTDXHebfXD-QEAAwIAA3kAAzoE',
    'core_sync': 'AgACAgIAAyEFAATh7MR7AAPSaaYyM1sMEAABs-jT4AP2BaODFDJNAALlFGsbekswSWIMAtqUNijTAQADAgADeQADOgQ',
    'trash_dump': 'AgACAgIAAyEFAATh7MR7AAPRaaYyMydzITwrhRoVxSTDIigNyhYAAuQUaxt6SzBJdUnIFBn6y0MBAAMCAAN5AAM6BA',
    'data_compression': 'AgACAgIAAyEFAATh7MR7AAPQaaYyMmSSmGsK6ZIJ_uR-u2AOK10AAuMUaxt6SzBJ6slGvqalqPMBAAMCAAN5AAM6BA'
}

def check_micro_glitch(uid, user_level):
    """
    Module 7: Micro-Glitches.
    Returns (message, image_id) if a glitch triggers, else (None, None).
    """
    metrics = db.get_user_shadow_metrics(uid)
    if not metrics:
        return None, None

    possible_glitches = []

    # 1. Death / Tilt check (Level < 10)
    if user_level < 10 and metrics.get('consecutive_deaths', 0) >= 2:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Я вижу твой пульс. Ты начинаешь нервничать и ошибаться. "
            "Доживи до 10 уровня, и я покажу, почему ты проигрываешь.",
            GLITCH_AVATARS['system_gaze']
        ))

    # 2. Night owl check
    if metrics.get('night_sessions_count', 0) >= 3:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Твоя префронтальная кора истощена. "
            "От чего ты прячешься в Сети по ночам? Позже мы это обсудим. Спи.",
            GLITCH_AVATARS['memory_fragment']
        ))

    # 3. Hoarding check
    earned = metrics.get('total_coins_earned', 0)
    spent = metrics.get('total_coins_spent', 0)
    if earned > 5000 and (spent / max(1, earned)) < 0.2:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Ты сидишь на ресурсах, но боишься их тратить. "
            "Страх потери убьет твой потенциал. Я уже собираю твой профиль.",
            GLITCH_AVATARS['data_compression']
        ))

    # 4. ADHD check
    if metrics.get('fast_sync_clicks', 0) >= 5:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Твоя концентрация стремится к нулю. Ты просто жмешь кнопки, не читая код. "
            "Твой мозг жаждет дешевого дофамина. Я научу тебя фокусу. Позже.",
            GLITCH_AVATARS['trash_dump']
        ))

    # 5. Safe player check
    if metrics.get('safe_zone_raids', 0) >= 10 and metrics.get('high_risk_raids', 0) == 0:
         possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Ты выбираешь только безопасные пути. "
            "Эволюция не происходит в зоне комфорта. Ты просто архивируешь своё время.",
            GLITCH_AVATARS['time_loop']
         ))

    # 6. High Roller check
    if metrics.get('high_risk_raids', 0) >= 5:
         possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Твой риск-профиль зашкаливает. Ты ищешь смерти или подтверждения своего превосходства? "
            "Я зафиксировал этот паттерн саморазрушения.",
            GLITCH_AVATARS['core_sync']
         ))

    if possible_glitches:
        if random.random() <= 0.50:
            return random.choice(possible_glitches)

    return None, None


GLITCH_QUESTIONS = [
    {
        'trigger': lambda m: m.get('consecutive_deaths', 0) >= 3,
        'metric_reset': 'consecutive_deaths',
        'text': "👁‍🗨 **ТЫ СНОВА МЕРТВ.**\n\nТы раз за разом лезешь в пекло и теряешь всё. Почему ты не нажал эвакуацию, когда сигнал был критическим?",
        'answers': [
            {'text': "Мне просто не везет.", 'axis': 'glitch_victim_answers'},
            {'text': "Я хотел всё и сразу.", 'axis': 'glitch_greed_answers'},
            {'text': "Моя ошибка в расчетах.", 'axis': 'glitch_stoic_answers'}
        ],
        'image': GLITCH_AVATARS['system_gaze']
    },
    {
        'trigger': lambda m: m.get('total_coins_earned', 0) > 10000 and (m.get('total_coins_spent', 0) / max(1, m.get('total_coins_earned', 0))) < 0.1,
        'metric_reset': None,
        'text': "👁‍🗨 **ТВОЙ БАЛАНС РАСТЕТ.**\n\nНо ты ничего не покупаешь. Твой код застрял в цикле накопления ради накопления. Чего ты боишься?",
        'answers': [
            {'text': "А вдруг я всё потеряю?", 'axis': 'glitch_victim_answers'},
            {'text': "Я коплю на власть.", 'axis': 'glitch_greed_answers'},
            {'text': "Жду идеального момента.", 'axis': 'glitch_chaos_answers'}
        ],
        'image': GLITCH_AVATARS['data_compression']
    },
    {
         'trigger': lambda m: m.get('night_sessions_count', 0) >= 5,
         'metric_reset': 'night_sessions_count',
         'text': "👁‍🗨 **ТРЕТИЙ ЧАС НОЧИ.**\n\nТвоя реальная жизнь рушится, пока ты сидишь здесь. Зачем ты убегаешь в код, вместо того чтобы спать?",
         'answers': [
             {'text': "Реальность слишком сложна.", 'axis': 'glitch_victim_answers'},
             {'text': "Я просто хочу играть.", 'axis': 'glitch_chaos_answers'},
             {'text': "У меня сбит режим, исправлю.", 'axis': 'glitch_stoic_answers'}
         ],
         'image': GLITCH_AVATARS['memory_fragment']
    },
    {
         'trigger': lambda m: m.get('escapes_at_full_hp', 0) >= 10,
         'metric_reset': 'escapes_at_full_hp',
         'text': "👁‍🗨 **ИДЕАЛЬНЫЙ ПОБЕГ.**\n\nТы всегда уходишь вовремя, не рискуя ничем. Твоя осторожность — это мудрость или трусость перед лицом неизвестного?",
         'answers': [
             {'text': "Это стратегия выживания.", 'axis': 'glitch_stoic_answers'},
             {'text': "Я боюсь потерять прогресс.", 'axis': 'glitch_victim_answers'},
             {'text': "Мир слишком опасен для риска.", 'axis': 'glitch_chaos_answers'}
         ],
         'image': GLITCH_AVATARS['time_loop']
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
