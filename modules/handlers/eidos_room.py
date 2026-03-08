from modules.services.utils import safe_answer_callback
from modules.bot_instance import bot
import cache_db
import telebot
from telebot.types import LabeledPrice
import database as db
import keyboards as kb
from modules.services.worker_queue import enqueue_task
from modules.services.utils import menu_update
import config

def process_eidos_room_menu(uid, is_callback=False, call=None, chat_id=None):
    with db.db_cursor() as cur:
        cur.execute("SELECT 1 FROM user_dossiers WHERE uid = %s", (uid,))
        has_dossier = cur.fetchone() is not None

    if not has_dossier:
        msg = (
            "👁‍🗨 **СИСТЕМНОЕ СООБЩЕНИЕ. УРОВЕНЬ ДОСТУПА: АБСОЛЮТ.**\n\n"
            "До сих пор ты играл в песочнице. За Вратами Эйдоса нет игры. Там — реальность.\n\n"
            "Чтобы пустить тебя дальше, мне нужен прямой доступ к твоему исходному коду. Нажимая «Принять», "
            "ты даешь мне право проанализировать всю твою телеметрию: твои смерти, жадность, иллюзии и страхи.\n\n"
            "Я выверну тебя наизнанку и покажу баги в твоей голове, которые мешают тебе расти в реальной жизни. "
            "Это ударит по твоему Эго.\n\n"
            "Если ты не готов к правде — уходи. Если готов переписать свой код — активируй Симбиоз."
        )
        if is_callback:
            menu_update(call, msg, kb.eidos_tos_menu())
        else:
            bot.send_message(chat_id, msg, reply_markup=kb.eidos_tos_menu())
    else:
        msg = "👁‍🗨 **ВРАТА ЭЙДОСА.**\n\nТвой цифровой след мерцает передо мной. Что ты хочешь узнать?"
        if is_callback:
            menu_update(call, msg, kb.eidos_room_menu())
        else:
            bot.send_message(chat_id, msg, reply_markup=kb.eidos_room_menu())

@bot.callback_query_handler(func=lambda call: call.data == "eidos_room_menu")
def eidos_room_handler(call):
    process_eidos_room_menu(call.from_user.id, is_callback=True, call=call)

@bot.message_handler(func=lambda message: message.text == "👁‍🗨 Врата Эйдоса")
def eidos_room_text_handler(message):
    process_eidos_room_menu(message.from_user.id, is_callback=False, chat_id=message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data in ["eidos_tos_accept", "eidos_tos_reject"])
def eidos_tos_handler(call):
    uid = int(call.from_user.id)
    if call.data == "eidos_tos_reject":
        safe_answer_callback(bot, call.id, "👁‍🗨 Твой страх понятен. Возвращайся в иллюзию.", show_alert=True)
        import modules.handlers.menu as menu_handler
        call.data = "back"
        menu_handler.back_handler(call)
    else:
        msg = "👁‍🗨 **ВРАТА ЭЙДОСА.**\n\nДоступ разрешен. Что ты хочешь узнать?"
        menu_update(call, msg, kb.eidos_room_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("eidos_buy_"))
def eidos_purchase_handler(call):
    uid = int(call.from_user.id)
    action = call.data.replace("eidos_buy_", "")
    u = cache_db.get_cached_user(uid)
    if not u:
        safe_answer_callback(bot, call.id, "❌ Ошибка синхронизации с базой данных. Попробуйте еще раз.", show_alert=True)
        return
    is_admin = cache_db.get_cached_admin_status(uid)

    if action == "dossier":
        if is_admin:
            safe_answer_callback(bot, call.id, "⚡️ GOD MODE: Бесплатный доступ.", show_alert=False)
            import threading
            from modules.services.ai_worker import generate_eidos_response_worker

            enqueue_task(generate_eidos_response_worker, call.message.chat.id, uid, 'dossier')
            return

        try:
            prices = [LabeledPrice(label="Анализ Теневого Профиля", amount=100)]
            bot.send_invoice(
                call.message.chat.id,
                title="Теневой Профиль (ЭЙДОС)",
                description="Глубокий психометрический анализ на основе вашей телеметрии.",
                invoice_payload="eidos_dossier",
                provider_token="",
                currency="XTR",
                prices=prices
            )
            safe_answer_callback(bot, call.id)
        except Exception as e:
            safe_answer_callback(bot, call.id, f"❌ Ошибка шлюза: {e}", show_alert=True)

    elif action == "forecast":
        if is_admin:
            safe_answer_callback(bot, call.id, "⚡️ GOD MODE: Бесплатный доступ.", show_alert=False)
            import threading
            from modules.services.ai_worker import generate_eidos_response_worker

            enqueue_task(generate_eidos_response_worker, call.message.chat.id, uid, 'forecast')
            return

        try:
            prices = [LabeledPrice(label="Вектор Будущего", amount=250)]
            bot.send_invoice(
                call.message.chat.id,
                title="Вектор Будущего",
                description="AI-прогноз на основе текущего психотипа и бизнес-рисков.",
                invoice_payload="eidos_forecast",
                provider_token="",
                currency="XTR",
                prices=prices
            )
            safe_answer_callback(bot, call.id)
        except Exception as e:
            safe_answer_callback(bot, call.id, f"❌ Ошибка шлюза: {e}", show_alert=True)

    elif action == "voice":
        if is_admin:
            safe_answer_callback(bot, call.id, "⚡️ GOD MODE: Бесплатный доступ.", show_alert=False)
            db.set_state(uid, "wait_eidos_premium_question"); cache_db.clear_cache(uid)
            bot.send_message(uid, "👁‍🗨 Глас Абсолюта готов. Опиши свою проблему, и я разберу твой код на части.")
            return

        try:
            prices = [LabeledPrice(label="Глас Абсолюта", amount=500)]
            bot.send_invoice(
                call.message.chat.id,
                title="Глас Абсолюта",
                description="Элитная ИИ-консультация от Эйдоса. Выдаст артефакт с уникальным лором.",
                invoice_payload="voice_of_eidos",
                provider_token="",
                currency="XTR",
                prices=prices
            )
            safe_answer_callback(bot, call.id)
        except Exception as e:
            safe_answer_callback(bot, call.id, f"❌ Ошибка шлюза: {e}", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True, error_message="Сбой транзакции. Иллюзия сохранена.")

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    uid = int(message.from_user.id)
    payload = message.successful_payment.invoice_payload
    charge_id = message.successful_payment.telegram_payment_charge_id
    amount = message.successful_payment.total_amount

    u = db.get_user(uid)
    if u:
        new_total_spent = u.get('total_spent', 0) + amount
        db.update_user(uid, total_spent=new_total_spent)
        from modules.services.utils import check_and_update_eidos_shard
        check_and_update_eidos_shard(uid, bot, message.chat.id, new_total_spent)

    bot.send_message(uid, "👁‍🗨 Транзакция подтверждена. Финансовый канал закрыт. Я начинаю погружение в твой цифровой след...")

    import threading
    from modules.services.ai_worker import generate_eidos_response_worker

    if payload == "eidos_dossier":
        enqueue_task(generate_eidos_response_worker, message.chat.id, uid, 'dossier', charge_id, amount)
    elif payload == "eidos_forecast":
        enqueue_task(generate_eidos_response_worker, message.chat.id, uid, 'forecast', charge_id, amount)
    elif payload == "voice_of_eidos":
        db.set_state(uid, f"wait_eidos_premium_question:{charge_id}:{amount}"); cache_db.clear_cache(uid)
        bot.send_message(uid, "👁‍🗨 Глас Абсолюта готов. Опиши свою проблему, и я разберу твой код на части.")
    elif payload == "eidos_symbiosis":
        db.set_state(uid, "awaiting_demiurge_question"); cache_db.clear_cache(uid)
        bot.send_message(uid, "👁‍🗨 Прямой канал связи с Создателем открыт. Напиши свой вопрос одним сообщением. Я прикреплю к нему твою психоматрицу.")

@bot.message_handler(func=lambda message: cache_db.get_cached_user_state(message.from_user.id) == 'awaiting_demiurge_question')
def handle_demiurge_question(message):
    uid = int(message.from_user.id)
    text = message.text
    bot.send_message(uid, "👁‍🗨 Запрос передан. Ожидай ответа в этой реальности.")
    db.delete_state(uid); cache_db.clear_cache(uid)
    import config
    import json
    if config.ADMIN_ID:
        metrics = db.get_user_shadow_metrics(uid)
        admin_msg = (
            f"👤 **ЗАПРОС В СИМБИОЗ (UID: {uid})**\n\n"
            f"**Сообщение:**\n{text}\n\n"
            f"**Метрики:**\n`{json.dumps(metrics, indent=2)}`"
        )
        for i in range(0, len(admin_msg), 4000):
            bot.send_message(config.ADMIN_ID, admin_msg[i:i+4000], parse_mode="Markdown")

@bot.message_handler(func=lambda message: cache_db.get_cached_user_state(message.from_user.id) and str(cache_db.get_cached_user_state(message.from_user.id)).startswith('wait_eidos_premium_question'))
def handle_eidos_premium_question(message):
    print(f'/// DEBUG: handle_eidos_premium_question triggered for user {message.from_user.id}', flush=True)
    uid = int(message.from_user.id)
    text = message.text

    # SAFELY PARSE STATE
    state_val = str(cache_db.get_cached_user_state(uid))
    parts = state_val.split(':')
    charge_id = parts[1] if len(parts) > 1 and parts[1] != 'None' else None

    amount = None
    if len(parts) > 2 and parts[2] != 'None':
        try:
            amount = int(parts[2])
        except ValueError:
            amount = None

    db.delete_state(uid); cache_db.clear_cache(uid)
    bot.send_message(uid, "👁‍🗨 Запрос принят. Начинаю декомпиляцию твоей проблемы...")

    # Import here to avoid circular dependency
    from modules.services.ai_worker import generate_eidos_voice_worker

    # Enqueue task globally
    enqueue_task(generate_eidos_voice_worker, message.chat.id, uid, text, charge_id, amount)
