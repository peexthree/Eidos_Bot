with open('modules/handlers/eidos_room.py', 'r') as f:
    content = f.read()

content = content.replace(
"""    elif action == "symbiosis":
        if is_admin:
            bot.answer_callback_query(call.id, "⚡️ GOD MODE: Бесплатный доступ.", show_alert=False)
            db.set_state(uid, "awaiting_demiurge_question"); cache_db.clear_cache(uid)
            bot.send_message(uid, "👁‍🗨 Прямой канал связи с Создателем открыт. Напиши свой вопрос одним сообщением. Я прикреплю к нему твою психоматрицу.")
            return

        prices = [LabeledPrice(label="Протокол Симбиоза", amount=1000)]
        bot.send_invoice(
            call.message.chat.id,
            title="Протокол Симбиоза",
            description="Личный зашифрованный канал связи с Демиургом.",
            invoice_payload="eidos_symbiosis",
            provider_token="",
            currency="XTR",
            prices=prices
        )
        bot.answer_callback_query(call.id)""",
"""    elif action == "voice":
        if int(u.get('level', 1)) < 10:
            bot.answer_callback_query(call.id, "Твой нейроконтур не готов к Слиянию.", show_alert=True)
            return

        if is_admin:
            bot.answer_callback_query(call.id, "⚡️ GOD MODE: Бесплатный доступ.", show_alert=False)
            db.set_state(uid, "wait_eidos_premium_question"); cache_db.clear_cache(uid)
            bot.send_message(uid, "👁‍🗨 Глас Абсолюта готов. Опиши свою проблему, и я разберу твой код на части.")
            return

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
        bot.answer_callback_query(call.id)"""
)

content = content.replace(
"""    elif payload == "eidos_symbiosis":
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
            bot.send_message(config.ADMIN_ID, admin_msg[i:i+4000], parse_mode="Markdown")""",
"""    elif payload == "voice_of_eidos":
        db.set_state(uid, "wait_eidos_premium_question"); cache_db.clear_cache(uid)
        bot.send_message(uid, "👁‍🗨 Глас Абсолюта готов. Опиши свою проблему, и я разберу твой код на части.")

@bot.message_handler(func=lambda message: cache_db.get_cached_user_state(message.from_user.id) == 'wait_eidos_premium_question')
def handle_eidos_premium_question(message):
    uid = int(message.from_user.id)
    text = message.text

    db.delete_state(uid); cache_db.clear_cache(uid)
    bot.send_message(uid, "👁‍🗨 Запрос принят. Начинаю декомпиляцию твоей проблемы...")

    import threading
    from modules.services.ai_worker import generate_eidos_voice_worker
    threading.Thread(target=generate_eidos_voice_worker, args=(bot, message.chat.id, uid, text)).start()"""
)

with open('modules/handlers/eidos_room.py', 'w') as f:
    f.write(content)
