import database as db
import random
import config
from modules.services.utils import zalgo_text

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


    u = db.get_user(uid)
    if not u: return None, None

    # 7. Pacifist Grinder (Пацифист-гриндер)
    if u.get('raids_done', 0) > 100 and u.get('kills', 0) < 10:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Сотня рейдов и чистые руки. Ты избегаешь конфликтов даже в симуляции. Чего ты стоишь в реальном бою?",
            GLITCH_AVATARS['system_gaze']
        ))

    # 8. Shuttle Syndrome (Синдром челнока)
    if metrics.get('low_value_extracts', 0) >= 3:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Твои амбиции измеряются копейками. Жалкое зрелище.",
            GLITCH_AVATARS['trash_dump']
        ))

    # 9. Suicidal Economy (Самоубийственная экономика)
    if metrics.get('zero_balance_purchases', 0) >= 1:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Обнуление баланса. Ты сжигаешь мосты, чтобы не оставлять себе пути к отступлению?",
            GLITCH_AVATARS['core_sync']
        ))

    # 10. Mad Rush (Безумный Раш)
    if u.get('max_depth', 0) > 50 and u.get('level', 1) < 5:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Ты бежишь в Бездну, игнорируя логику развития. Тебе не нужен лут, тебе нужен конец.",
            GLITCH_AVATARS['time_loop']
        ))

    # 11. Armor Rejection (Отказ от брони)
    if metrics.get('naked_raids', 0) >= 1:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Идешь голым на верную смерть. Гордыня или желание всё потерять?",
            GLITCH_AVATARS['memory_fragment']
        ))

    # 12. HP Micromanagement (Микро-менеджмент HP)
    if metrics.get('micro_hp_heals', 0) >= 5:
        possible_glitches.append((
            "👁‍🗨 *ГЛИТЧ:* Ты тратишь аптечку на царапину. Твоя тревожность обойдется тебе дороже, чем этот урон.",
            GLITCH_AVATARS['data_compression']
        ))

    if possible_glitches:
        if random.random() <= 0.50:
            glitch = random.choice(possible_glitches)
            return "<code>" + zalgo_text(glitch[0], 1) + "</code>", glitch[1]

    return None, None


GLITCH_QUESTIONS = [
    {
        'trigger': lambda m, u: m.get('consecutive_deaths', 0) >= 3,
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
        'trigger': lambda m, u: m.get('total_coins_earned', 0) > 10000 and (m.get('total_coins_spent', 0) / max(1, m.get('total_coins_earned', 0))) < 0.1,
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
         'trigger': lambda m, u: m.get('night_sessions_count', 0) >= 5,
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
         'trigger': lambda m, u: m.get('escapes_at_full_hp', 0) >= 10,
         'metric_reset': 'escapes_at_full_hp',
         'text': "👁‍🗨 **ИДЕАЛЬНЫЙ ПОБЕГ.**\n\nТы всегда уходишь вовремя, не рискуя ничем. Твоя осторожность — это мудрость или трусость перед лицом неизвестного?",
         'answers': [
             {'text': "Это стратегия выживания.", 'axis': 'glitch_stoic_answers'},
             {'text': "Я боюсь потерять прогресс.", 'axis': 'glitch_victim_answers'},
             {'text': "Мир слишком опасен для риска.", 'axis': 'glitch_chaos_answers'}
         ],
         'image': GLITCH_AVATARS['time_loop']
    },
    {
        'trigger': lambda m, u: u.get('kills', 0) > 1000 and u.get('level', 1) > 20,
        'metric_reset': None,
        'text': "👁‍🗨 **ТЫСЯЧА ТРУПОВ.**\n\nТвои логи залиты цифровой кровью. Ты перешагнул через тысячу строк кода, которые когда-то были врагами. Что ты чувствуешь, нажимая 'Атаковать'?",
        'answers': [
            {'text': "Это просто цифры, мне нужен лут.", 'axis': 'glitch_stoic_answers'},
            {'text': "Они стояли на моем пути.", 'axis': 'glitch_greed_answers'},
            {'text': "Я даже не смотрел, кого убиваю.", 'axis': 'glitch_chaos_answers'}
        ],
        'image': GLITCH_AVATARS['core_sync']
    },
    {
        'trigger': lambda m, u: m.get('rapid_menu_clicks', 0) >= 10,
        'metric_reset': 'rapid_menu_clicks',
        'text': "👁‍🗨 **ОБСЕССИЯ.**\n\nТы снова и снова проверяешь свои карманы. Данные не изменились с прошлой секунды. Зачем ты ищешь контроль там, где его нет?",
        'answers': [
            {'text': "Я должен быть уверен.", 'axis': 'glitch_victim_answers'},
            {'text': "Я ищу баги в твоем коде.", 'axis': 'glitch_chaos_answers'},
            {'text': "Просто привычка.", 'axis': 'glitch_stoic_answers'}
        ],
        'image': GLITCH_AVATARS['system_gaze']
    },
    {
        'trigger': lambda m, u: u.get('biocoin', 0) > 500000,
        'metric_reset': None,
        'text': "👁‍🗨 **ЦИФРОВОЙ ОЛИГАРХ.**\n\nПолмиллиона коинов. Ты скупил всё, что имеет ценность. Симуляция пройдена на уровне потребления. Что дальше?",
        'answers': [
            {'text': "Построю свою империю.", 'axis': 'glitch_greed_answers'},
            {'text': "Раздам тем, кто слабее.", 'axis': 'glitch_stoic_answers'},
            {'text': "Жду, когда ты бросишь мне настоящий вызов.", 'axis': 'glitch_chaos_answers'}
        ],
        'image': GLITCH_AVATARS['data_compression']
    }
]

def check_hard_glitch(uid):
    """
    Module 3: Hard Glitch Questions.
    Checks if user meets criteria for a hard glitch question.
    Returns question dict if triggered.
    """
    import time
    metrics = db.get_user_shadow_metrics(uid)
    if not metrics: return None

    # 24 hour cooldown check
    last_glitch = metrics.get('last_hard_glitch_time', 0)
    if time.time() - last_glitch < 86400:
        return None

    for q in GLITCH_QUESTIONS:
        if q['trigger'](metrics, db.get_user(uid)):
            return q
    return None
