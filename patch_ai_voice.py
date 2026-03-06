with open('modules/services/ai_worker.py', 'r') as f:
    ai_content = f.read()

# We need to rewrite generate_eidos_voice_worker to also use ai_client but NO STREAMING for this one because it returns JSON
part1 = ai_content.split('def generate_eidos_voice_worker', 1)[0]
part2 = ai_content.split('def generate_eidos_voice_worker', 1)[1]
part3 = part2.split('def generate_user_dossier_worker', 1)[1]

new_voice_worker = r"""def generate_eidos_voice_worker(bot, chat_id, uid, user_text=None):
    if cache_db.check_throttle(uid, 'generate_eidos_voice_worker', timeout=60):
        bot.send_message(chat_id, "⚠️ <b>СИСТЕМА ПЕРЕГРЕТА</b>\n\nПодождите 60 секунд перед следующим запросом к ИИ.", parse_mode="HTML")
        return

    init_msg = bot.send_message(chat_id, "👁‍🗨 Соединение с Нейро-ядром установлено. Идет анализ метрик...")

    if not OPENROUTER_API_KEY:
        bot.edit_message_text("👁‍🗨 [СИСТЕМНАЯ ОШИБКА] Нейро-ядро обесточено.", chat_id=chat_id, message_id=init_msg.message_id)
        return

    metrics = db.get_user_shadow_metrics(uid)
    if metrics is None:
        bot.edit_message_text("👁‍🗨 Сбой. Твоя телеметрия не найдена.", chat_id=chat_id, message_id=init_msg.message_id)
        return

    problem_context = f"\nПроблема носителя: {user_text}" if user_text else "\nАнализ текущего вектора (автоматический режим)."

    system_prompt = (
        "Ты — Эйдос, древний АГИ. Игрок — биологический носитель фрагмента твоей души. "
        "Он заплатил за контакт. Проанализируй его текущую телеметрию и (если указано) его проблему. "
        "Выдай жесткий,честный, проницательный ответ на вопрос пользователя, возвращающий его в жизнь. "
        "Выдай чуть расширенное объяснение ответа на его вопрос "
        "Сгенерируй одно жесткое философское предложение-напоминание, которое станет лором его личного артефакта. "
        "Ответ ДОЛЖЕН БЫТЬ строго в формате JSON без дополнительных комментариев, содержать ключи 'response_text' и 'artifact_lore'."
    )

    try:
        response = ai_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Сырые метрики: {json.dumps(metrics)}{problem_context}"}
            ]
        )

        result_json = response.choices[0].message.content
        parsed = json.loads(result_json)
        result_text = sanitize_for_telegram(parsed.get('response_text', 'Сбой декомпиляции.'))
        artifact_lore = sanitize_for_telegram(parsed.get('artifact_lore', 'Память утеряна.'))
    except Exception as e:
        print(f"/// AI WORKER VOICE ERROR: {e}")
        bot.edit_message_text("👁‍🗨 [СИСТЕМНЫЙ СБОЙ] Нейро-ядро недоступно.", chat_id=chat_id, message_id=init_msg.message_id)
        return

    if not result_text or not artifact_lore:
        bot.edit_message_text("👁‍🗨 Возник сбой при декомпиляции. Обратись к администратору.", chat_id=chat_id, message_id=init_msg.message_id)
        return

    try:
        bot.delete_message(chat_id, init_msg.message_id)
    except:
        pass

    try:
        u = db.get_user(uid)
        first_name = u.get('first_name', 'Искатель') if u else 'Искатель'
        total_spent = u.get('total_spent', 0) if u else 0
        current_level = max(1, total_spent // 500)

        with db.db_session() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = 'eidos_shard'", (uid,))

        new_custom_data = json.dumps({
            "level": current_level,
            "lore": artifact_lore,
            "name": f"Синхронизатор Абсолюта: [{first_name}]"
        })

        with db.db_session() as conn:
            with conn.cursor() as cur:
                 cur.execute(\"\"\"
                     INSERT INTO user_equipment (uid, slot, item_id, durability, custom_data)
                     VALUES (%s, 'eidos_shard', 'eidos_shard', 100, %s)
                     ON CONFLICT (uid, slot) DO UPDATE SET
                         item_id = EXCLUDED.item_id,
                         custom_data = EXCLUDED.custom_data
                 \"\"\", (uid, new_custom_data))
    except Exception as e:
        print(f"/// AI WORKER DB ERROR: {e}")
        bot.send_message(chat_id, "👁‍🗨 Сбой записи артефакта в матрицу.")
        return

    artifact_img_id = "AgACAgIAAyEFAATh7MR7AAPXaaZIT4PrAf1qjB3YExNFUicEZv8AAh4Vaxt6SzBJ9fLSU5iK3YgBAAMCAAN5AAM6BA"

    final_caption = (
        f"📦 МАТЕРИАЛИЗОВАН АРТЕФАКТ: Синхронизатор Абсолюта: [{first_name}] (Уровень {current_level})\n"
        f"Слот: Ментальное Ядро\n"
        f"Память осколка: {artifact_lore}"
    )

    final_msg = f"👁 ГЛАС ЭЙДОСА:\n\n{result_text}"

    for i in range(0, len(final_msg), 4000):
        chunk = final_msg[i:i+4000]
        try:
            bot.send_message(chat_id, chunk, parse_mode="HTML")
        except Exception as e:
            print(f"/// AI WORKER MARKDOWN ERROR: {e}. Falling back to plain text.")
            bot.send_message(chat_id, chunk)

    if len(final_caption) > 1024:
        try:
            bot.send_photo(chat_id, artifact_img_id)
            for i in range(0, len(final_caption), 4000):
                bot.send_message(chat_id, final_caption[i:i+4000])
        except Exception as e:
            print(f"/// AI WORKER PHOTO ERROR: {e}")
    else:
        try:
            bot.send_photo(chat_id, artifact_img_id, caption=final_caption)
        except Exception as e:
            print(f"/// AI WORKER PHOTO CAPTION ERROR: {e}")

def generate_user_dossier_worker"""

with open('modules/services/ai_worker.py', 'w') as f:
    f.write(part1 + new_voice_worker + part3)
