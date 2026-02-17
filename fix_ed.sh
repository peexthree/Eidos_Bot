ed logic.py <<END
234,235c
        msg_event = f"❤️ <b>АПТЕЧКА:</b> {desc}\n+25% Сигнала."
.
w
q
END

ed bot.py <<END
/msg = (/
.,/)/c
            msg = (f"👤 <b>ПРОФИЛЬ: {u['first_name']}</b>\\n"
                   f"🔰 Статус: <code>{TITLES.get(u['level'])}</code>\\n"
                   f"📊 LVL {u['level']} | {p_bar} ({perc}%)\\n"
                   f"💡 До апа: {xp_need} XP\\n\\n"
                   f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\\n"
                   f"🏫 Школа: <code>{SCHOOLS.get(u['path'], 'Общая')}</code>\\n"
                   f"🔋 Энергия: {u['xp']} | 🪙 BioCoins: {u['biocoin']}\\n\\n"
                   f"🏆 Ачивки: <b>{len(ach_list)}</b>\\n"
                   f"🔥 Стрик: <b>{streak} дн.</b> (Бонус: +{streak_bonus} XP)\\n"
                   f"🕳 Рекорд глубины: <b>{max_depth}м</b>")
.
w
q
END
