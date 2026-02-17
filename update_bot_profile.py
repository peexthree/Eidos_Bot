import re

with open('bot.py', 'r') as f:
    content = f.read()

old_profile = r'elif call.data == "profile":.*?menu_update\(call, msg, kb.back_button\(\)\)'
# This regex needs to be careful with matching across lines.
# The block spans multiple lines.

new_profile = '''elif call.data == "profile":
            stats, _ = logic.get_user_stats(uid)
            perc, xp_need = logic.get_level_progress_stats(u)
            p_bar = kb.get_progress_bar(perc, 100)

            ach_list = db.get_user_achievements(uid)
            streak = u.get('streak', 0)
            max_depth = u.get('max_depth', 0)
            # Assuming streak implies daily consistency bonus
            streak_bonus = streak * 5

            msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\n"
                   f"📊 LVL {u['level']} | {p_bar} ({perc}%)\n"
                   f"💡 До апа: {xp_need} XP\n\n"
                   f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\n"
                   f"🔋 Энергия: {u['xp']} | 🪙 BioCoins: {u['biocoin']}\n\n"
                   f"🏆 Ачивки: <b>{len(ach_list)}</b>\n"
                   f"🔥 Стрик: <b>{streak} дн.</b> (Бонус: +{streak_bonus} XP)\n"
                   f"🕳 Рекорд глубины: <b>{max_depth}м</b>")
            menu_update(call, msg, kb.back_button())'''

# Using re.DOTALL to match across lines
content = re.sub(old_profile, new_profile, content, flags=re.DOTALL)

with open('bot.py', 'w') as f:
    f.write(content)
