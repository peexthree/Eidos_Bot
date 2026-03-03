import database as db
import random

def process_architect_key(uid, s, cur, u):
    """
    Эффект Ключа Архитектора: Глубокое Сканирование и Смена Фракции.
    Раскрывает 5 следующих шагов, восстанавливает 20% сигнала и меняет фракцию.
    """
    if db.get_item_count(uid, 'admin_key', cursor=cur) <= 0:
        return False, "❌ У вас нет Ключа Архитектора.", None, 'error'

    if db.use_item(uid, 'admin_key', cursor=cur):
        new_signal = min(100, s['signal'] + 20)

        predictions = []
        temp_streak = s['event_streak']
        temp_type = s['next_event_type']

        from modules.services.raid import generate_balanced_event_type

        events_map = {'combat': '⚔️', 'trap': '💥', 'loot': '💎', 'random': '❔', 'locked_chest': '🔒', 'cursed_chest': '🔴', 'lore': '📜', 'anomaly_terminal': '🔋', 'found_body': '💀'}

        for _ in range(5):
            predictions.append(events_map.get(temp_type, '❓'))
            temp_type = generate_balanced_event_type(temp_type, temp_streak)
            temp_streak = temp_streak + 1

        pred_str = " ".join(predictions)

        # Change Path to Architect
        db.update_user(uid, path='architect', cursor=cur)

        cur.execute("UPDATE raid_sessions SET signal = %s WHERE uid=%s", (new_signal, uid))

        alert = f"🟠 ГЛУБОКОЕ СКАНЕРИОВАНИЕ ЗАВЕРШЕНО\nБудущее: {pred_str}\n\nФРАКЦИЯ ИЗМЕНЕНА: АРХИТЕКТОР"
        return True, f"🛰 <b>СЕТЕВОЙ АНАЛИЗ:</b>\nСигнал усилен до {new_signal}%.\nМаршрут: {pred_str}\n\n🧿 <b>ВЫ СТАЛИ АРХИТЕКТОРОМ.</b>", {'alert': alert}, 'architect_used'

    return False, "⚠️ Сбой ключа.", None, 'error'
