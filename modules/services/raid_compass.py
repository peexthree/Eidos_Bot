import database as db
import random

def get_compass_prediction(uid, next_preview, is_architect, cur):
    """
    Улучшенная логика компаса.
    15% шанс на 'Критический успех' — показать сразу 2 шага.
    """
    comp_map = {
        'combat': '⚔️ ВРАГ', 'trap': '💥 ЛОВУШКА', 'loot': '💎 ЛУТ',
        'random': '❔ НЕИЗВЕСТНО', 'locked_chest': '🔒 СУНДУК',
        'cursed_chest': '🔴 ПРОКЛЯТИЕ', 'lore': '📜 ЛОР',
        'anomaly_terminal': '🔋 АНОМАЛИЯ', 'found_body': '💀 ОСТАНКИ'
    }

    comp_res = comp_map.get(next_preview, '❔')
    prefix = "🧿 <b>ОКО (Дальше):</b>" if is_architect else "🧭 <b>КОМПАС (Дальше):</b>"

    # Critical Success (15%)
    crit_msg = ""
    if random.random() < 0.15:
        # Get one more step
        from modules.services.raid import generate_balanced_event_type
        # We don't have streak here, but can estimate
        second_step = generate_balanced_event_type(next_preview, 1)
        comp_res_2 = comp_map.get(second_step, '❔')
        crit_msg = f" ➔ {comp_res_2} (КРИТ!)"

    return f"{prefix} {comp_res}{crit_msg}"
