with open("modules/services/ai_worker.py", "r") as f:
    content = f.read()

old_dossier_call = """    ai_text = ""
    last_edit_time = time.time()
    for attempt in range(3):
        try:
            print(f"[AI WORKER] Sending request to OpenRouter for UID {uid}...", flush=True)
            stream = ai_client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True, timeout=15.0
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    ai_text += chunk.choices[0].delta.content
                    if ai_text.strip().lower().startswith("<!doctype") or ai_text.strip().lower().startswith("<html"):
                        print("/// CRITICAL: Received HTML instead of AI text. Aborting stream.", flush=True)
                        if loading_msg_id:
                            try: bot.edit_message_text("❌ Соединение с Нейро-ядром нестабильно. Ошибка протокола.", chat_id=chat_id, message_id=loading_msg_id)
                            except: pass
                        if refund_bc:
                            try:
                                u = db.get_user(uid)
                                if u:
                                    db.update_user(uid, biocoin=u.get("biocoin", 0) + refund_bc)
                                    bot.send_message(chat_id, f"💳 Ошибка нейро-сети. {refund_bc} BC возвращены на счет.")
                            except: pass
                        return
                    if loading_msg_id and time.time() - last_edit_time > 1.5:
                        try:
                            bot.edit_message_text(f"📡 УСТАНОВКА СОЕДИНЕНИЯ...\nДешифровка данных...\n\n{ai_text} █", chat_id=chat_id, message_id=loading_msg_id)
                            last_edit_time = time.time()
                        except Exception as e:
                            pass

            ai_text = ai_text.replace('```html', '').replace('```', '').strip()
            ai_text = sanitize_for_telegram(ai_text)
            logging.info(f"AI Worker successfully generated response for UID {uid}")
            print(f"[AI WORKER] Received response from OpenRouter for UID {uid}. Status OK.", flush=True)
            break
        except Exception as e:
            print(f"/// AI WORKER DOSSIER STREAM ERR: {e}", flush=True)
            time.sleep(2)"""

new_dossier_call = """    ai_text = ""
    last_edit_time = time.time()
    success = False

    for model_name in MODELS:
        try:
            ai_text = ""
            print(f"[AI WORKER] Sending request to OpenRouter ({model_name}) for UID {uid}...", flush=True)
            stream = ai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True, timeout=7.0
            )

            html_detected = False
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    ai_text += chunk.choices[0].delta.content
                    if ai_text.strip().lower().startswith("<!doctype") or ai_text.strip().lower().startswith("<html"):
                        print(f"/// CRITICAL: Received HTML instead of AI text from {model_name}. Aborting stream.", flush=True)
                        html_detected = True
                        break

                    if loading_msg_id and time.time() - last_edit_time > 1.5:
                        try:
                            bot.edit_message_text(f"📡 УСТАНОВКА СОЕДИНЕНИЯ...\nДешифровка данных...\n\n{ai_text} █", chat_id=chat_id, message_id=loading_msg_id)
                            last_edit_time = time.time()
                        except Exception as e:
                            pass

            if html_detected:
                continue

            ai_text = ai_text.replace('```html', '').replace('```', '').strip()
            ai_text = sanitize_for_telegram(ai_text)
            logging.info(f"AI Worker successfully generated response for UID {uid} via {model_name}")
            print(f"[AI WORKER] Received response from OpenRouter ({model_name}) for UID {uid}. Status OK.", flush=True)
            success = True
            break
        except Exception as e:
            print(f"/// AI WORKER DOSSIER STREAM ERR ({model_name}): {e}", flush=True)
            continue

    if not success:
        if loading_msg_id:
            try: bot.edit_message_text("❌ Все модели Нейро-ядра недоступны. Ошибка протокола.", chat_id=chat_id, message_id=loading_msg_id)
            except: pass
        if refund_bc:
            try:
                u = db.get_user(uid)
                if u:
                    db.update_user(uid, biocoin=u.get("biocoin", 0) + refund_bc)
                    bot.send_message(chat_id, f"💳 Ошибка нейро-сети. {refund_bc} BC возвращены на счет.")
            except: pass
        return"""

content = content.replace(old_dossier_call, new_dossier_call)

with open("modules/services/ai_worker.py", "w") as f:
    f.write(content)
