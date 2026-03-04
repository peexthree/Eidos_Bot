with open("modules/handlers/menu.py", "r") as f:
    content = f.read()

old_quiz_logic = """        if ans == correct:
            db.increment_user_stat(uid, 'quiz_wins')
            db.add_xp_to_user(uid, 100)
            db.add_quiz_history(uid, qid)
            bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ОШИБКА", show_alert=True)

        # Return to guide
        call.data = "guide"
        guide_handler(call)"""

new_quiz_logic = """        if ans == correct:
            db.increment_user_stat(uid, 'quiz_wins')
            db.add_xp_to_user(uid, 100)
            db.add_quiz_history(uid, qid)
            # Fetch user again to get updated history
            u = db.get_user(uid)
            history = u.get('quiz_history', '') or ''
            available_after = [q for q in questions if q['id'] not in history]

            if not available_after:
                bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP\\n\\n🧠 Вы познали все тайны. Викторина завершена.", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ОШИБКА", show_alert=True)

        # Return to guide
        call.data = "guide"
        guide_handler(call)"""

content = content.replace(old_quiz_logic, new_quiz_logic)

with open("modules/handlers/menu.py", "w") as f:
    f.write(content)
