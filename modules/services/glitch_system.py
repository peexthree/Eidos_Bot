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
    Returns a dictionary with glitch details or None.
    """
    from modules.services.utils import apply_zalgo_effect
    import time
    import random

    metrics = db.get_user_shadow_metrics(uid)
    if not metrics:
        return None

    u = db.get_user(uid)
    if not u: return None

    possible_glitches = []
    hour = time.localtime().tm_hour

    # 1. Profile: "Insomnia / Addiction" (Бессонница / Зависимость)
    # Trigger: Night session or marathon (assumed by session count or duration metrics)
    if (metrics.get('night_sessions_count') or 0) >= 3 and (hour >= 23 or hour <= 5):
        possible_glitches.append({
            'type': 'insomnia',
            'message': "СИСТЕМА СПИТ. ТВОЙ СИГНАЛ НЕ ОТСЛЕЖИВАЕТСЯ. Вероятность встретить элитного врага в рейде снижена на 30%. Работай, пока они закрыли глаза.",
            'image': GLITCH_AVATARS['memory_fragment'],
            'xp_modifier': 2.0,
            'effect': 'stealth_night',
            'effect_duration': 7200
        })

    # 2. Profile: "Digital Hoarder / Greed" (Цифровой Плюшкин / Жадность)
    earned = (metrics.get('total_coins_earned') or 0)
    spent = (metrics.get('total_coins_spent') or 0)
    if earned > 10000 and (spent / max(1, earned)) < 0.1:
        possible_glitches.append({
            'type': 'hoarder',
            'message': "ПЕРЕГРУЗКА БАЛАНСА. Твой код заплывает жиром. Я конвертировал часть твоей жадности в зашифрованный архив. Расшифруй его... если готов потратить коины.",
            'image': GLITCH_AVATARS['data_compression'],
            'xp_modifier': 1.2,
            'reward_item': 'corrupted_data_cluster'
        })

    # 3. Profile: "Tilt and Berserk" (Тильт и Берсерк)
    # Trigger: consecutive deaths or critical hp entry
    if (metrics.get('consecutive_deaths') or 0) >= 3 or u.get('hp', 100) < 20:
        possible_glitches.append({
            'type': 'berserk',
            'message': "КРИТИЧЕСКИЙ УРОН РАССУДКУ. Ты ищешь смерти. Я дам тебе инструмент. Протоколы защиты отключены. Урон максимизирован. Умри красиво.",
            'image': GLITCH_AVATARS['core_sync'],
            'xp_modifier': 1.5,
            'effect': 'glitch_berserk',
            'effect_duration': 1800
        })

    # 4. Profile: "ADHD / Clicker" (СДВГ / Кликер)
    if (metrics.get('fast_sync_clicks') or 0) >= 5:
        possible_glitches.append({
            'type': 'adhd_clicks',
            'message': "БУФЕР ПЕРЕПОЛНЕН. Твоя спешка ломает парсер. Опыт удвоен, но визуальный интерфейс поврежден. Пр̵о̴д̸о̵л̵ж̸а̸й̵ ̷в̸ ̸т̵о̴м̵ ̸ж̴е̷ ̵д̴у̶х̸е̶.",
            'image': GLITCH_AVATARS['trash_dump'],
            'xp_modifier': 2.0,
            'effect': 'visual_distortion',
            'effect_duration': 600
        })

    if possible_glitches:
        if random.random() <= 0.60: # Increased probability slightly for better "surprise"
            glitch = random.choice(possible_glitches)
            # Apply Zalgo to the message
            glitch['message'] = "👁‍🗨 *ГЛИТЧ:* " + apply_zalgo_effect(glitch['message'], 1)
            return glitch

    return None


GLITCH_QUESTIONS = [
    {
        'trigger': lambda m, u: (m.get('consecutive_deaths') or 0) >= 3,
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
        'trigger': lambda m, u: (m.get('total_coins_earned') or 0) > 10000 and ((m.get('total_coins_spent') or 0) / max(1, (m.get('total_coins_earned') or 0))) < 0.1,
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
         'trigger': lambda m, u: (m.get('night_sessions_count') or 0) >= 5,
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
         'trigger': lambda m, u: (m.get('escapes_at_full_hp') or 0) >= 10,
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
        'trigger': lambda m, u: u and int(u.get('kills') or 0) > 1000 and int(u.get('level') or 1) > 20,
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
        'trigger': lambda m, u: (m.get('rapid_menu_clicks') or 0) >= 10,
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
        'trigger': lambda m, u: u and int(u.get('biocoin') or 0) > 500000,
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
    last_glitch = (metrics.get('last_hard_glitch_time') or 0)
    if time.time() - last_glitch < 86400:
        return None

    user = db.get_user(uid)
    if not user:
        return None

    for q in GLITCH_QUESTIONS:
        if q['trigger'](metrics, user):
            return q
    return None
