from modules.bot_instance import bot
import database as db
import keyboards as kb
from modules.services.glitch_system import check_hard_glitch, GLITCH_QUESTIONS
from modules.services.utils import strip_html, zalgo_text
import time
import cache_db

def check_for_glitch_state(uid, bot, chat_id):
    state_tuple = db.get_full_state(uid)
    if state_tuple and state_tuple[0] == 'glitch_question':
        try:
            q_idx = int(state_tuple[1])
            q_data = GLITCH_QUESTIONS[q_idx]
            msg = "<code>" + zalgo_text(q_data['text'], 1) + "</code>"
            img = q_data.get('image')
            if img:
                bot.send_photo(chat_id, img, caption=msg, reply_markup=kb.glitch_question_answers(q_data['answers']), parse_mode='HTML')
            else:
                bot.send_message(chat_id, msg, reply_markup=kb.glitch_question_answers(q_data['answers']), parse_mode='HTML')
        except:
            bot.send_message(chat_id, zalgo_text("👁‍🗨 Иллюзия выбора отключена. Ответь на вопрос.", 1))
        return True

    # Check if we should trigger a hard glitch right now
    glitch_data = check_hard_glitch(uid)
    if glitch_data:
        db.set_state(uid, 'glitch_question', str(GLITCH_QUESTIONS.index(glitch_data)))
        cache_db.clear_cache(uid)
        msg = "<code>" + zalgo_text(glitch_data['text'], 1) + "</code>"
        img = glitch_data.get('image')
        time.sleep(1.5)
        if img:
            bot.send_photo(chat_id, img, caption=msg, reply_markup=kb.glitch_question_answers(glitch_data['answers']), parse_mode='HTML')
        else:
            bot.send_message(chat_id, msg, reply_markup=kb.glitch_question_answers(glitch_data['answers']), parse_mode='HTML')
        return True

    return False

@bot.message_handler(func=lambda m: cache_db.get_cached_user_state(m.from_user.id) == 'glitch_question')
def block_glitch_msg(m):
    bot.send_message(m.chat.id, zalgo_text("👁‍🗨 Иллюзия выбора отключена. Ответь на вопрос.", 1))

@bot.callback_query_handler(func=lambda call: cache_db.get_cached_user_state(call.from_user.id) == 'glitch_question' and not call.data.startswith('glitch_ans_'))
def block_glitch_call(call):
    bot.answer_callback_query(call.id, zalgo_text("👁‍🗨 Иллюзия выбора отключена.", 1), show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('glitch_ans_'))
def handle_glitch_answer(call):
    uid = int(call.from_user.id)
    state_tuple = db.get_full_state(uid)

    if not state_tuple or state_tuple[0] != 'glitch_question':
        bot.answer_callback_query(call.id, "Ответ уже не актуален.")
        return

    try:
        q_idx = int(state_tuple[1])
        ans_idx = int(call.data.replace('glitch_ans_', ''))

        q_data = GLITCH_QUESTIONS[q_idx]
        ans_data = q_data['answers'][ans_idx]

        # 1. Increment correct metric
        db.update_shadow_metric(uid, ans_data['axis'], 1)

        # 2. Reset trigger metric if applicable
        if q_data['metric_reset']:
             metrics = db.get_user_shadow_metrics(uid)
             current_val = metrics.get(q_data['metric_reset'], 0)
             if current_val > 0:
                 db.update_shadow_metric(uid, q_data['metric_reset'], -current_val)

        # 3. Set Cooldown for hard glitch
        import time
        db.set_shadow_metric(uid, 'last_hard_glitch_time', int(time.time()))

        # 4. Clear state
        db.delete_state(uid)
        cache_db.clear_cache(uid)

        # Edit photo or text
        if call.message.content_type == 'photo':
            bot.edit_message_caption("👁‍🗨 Ответ записан. Матрица продолжает работу.", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("👁‍🗨 Ответ записан. Матрица продолжает работу.", call.message.chat.id, call.message.message_id)

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"GLITCH HANDLER ERROR: {e}")
        db.delete_state(uid)
        cache_db.clear_cache(uid)
        bot.answer_callback_query(call.id, "Сбой.", show_alert=True)
