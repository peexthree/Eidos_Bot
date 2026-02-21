from modules.bot_instance import bot
import database as db
import config
from config import TITLES, SCHOOLS, SCHOOLS_INFO, PATH_CHANGE_COST, ACHIEVEMENTS_LIST
import keyboards as kb
from modules.services.utils import menu_update, get_menu_text, get_menu_image, GAME_GUIDE_TEXTS, draw_bar
from modules.services.user import get_user_stats, get_level_progress_stats, get_profile_stats, get_syndicate_stats, perform_hard_reset
import time
import random
from telebot import types

@bot.callback_query_handler(func=lambda call: call.data == "profile" or call.data.startswith("set_path_") or call.data.startswith("confirm_path_") or call.data == "change_path_menu" or call.data == "use_accelerator" or call.data == "activate_purification")
def profile_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    if not u: return

    if call.data == "profile":
        stats, _ = get_user_stats(uid)
        perc, xp_need = get_level_progress_stats(u)
        p_bar = draw_bar(perc, 100, 10)
        ach_list = db.get_user_achievements(uid)
        has_accel = db.get_item_count(uid, 'accel') > 0
        has_purification = db.get_item_count(uid, 'purification_sync') > 0

        p_stats = get_profile_stats(uid)

        # Formatting title logic
        full_title = TITLES.get(u['level'], 'Unknown')
        if '(' in full_title:
            title_name = full_title.split('(')[0].strip()
            title_desc = full_title.split('(')[1].replace(')', '').strip()
        else:
            title_name = full_title
            title_desc = "Данные отсутствуют"

        school_name = SCHOOLS.get(u['path'], 'ОБЩАЯ')

        accel_status = ""
        if u.get('accel_exp', 0) > time.time():
             rem_hours = int((u['accel_exp'] - time.time()) / 3600)
             accel_status = f"\n⚡️ Ускоритель: <b>АКТИВЕН ({rem_hours}ч)</b>"

        msg = (
            f"👤 <b>ПРОФИЛЬ: {u['username'] or u['first_name']}</b>\n"
            f"🏫 Школа: <b>{school_name}</b>\n"
            f"🔰 Статус: <b>{title_name}</b>\n"
            f"<i>({title_desc})</i>\n"
            f"📊 <b>LVL {u['level']}</b> | <code>{p_bar}</code> ({perc}%)\n"
            f"🔋 <b>ТЕКУЩИЙ ОПЫТ:</b> {u['xp']}\n"
            f"📉 <b>ДО СЛЕДУЮЩЕГО УРОВНЯ:</b> {xp_need} XP\n"
            f"🔥 <b>СТРИК входов дней в игру:</b> {p_stats['streak']} (+{p_stats['streak_bonus']}% к опыту)\n\n"
            f"⚔️ ATK: {stats['atk']} | 🛡 DEF: {stats['def']} | 🍀 LUCK: {stats['luck']}\n\n"
            f"🕳 Рекорд глубины: <b>{p_stats['max_depth']}м</b>\n"
            f"🏆 Ачивки: <b>{len(ach_list)}</b>\n"
            f"🌐 Протоколов в коллекции: <b>{db.get_archived_protocols_count(uid)} ({config.TOTAL_PROTOCOLS})</b>\n"
            f"🪙 Кошелек: <b>{u['biocoin']} BC</b>{accel_status}"
        )

        # Determine avatar based on level
        avatar_id = config.USER_AVATARS.get(u.get('level', 1))
        if not avatar_id:
            avatar_id = config.USER_AVATARS.get(1)

        menu_update(call, msg, kb.profile_menu(u, has_accel, has_purification), image_url=avatar_id)

    elif call.data == "activate_purification":
        if perform_hard_reset(uid):
             bot.answer_callback_query(call.id, "♻️ ПРОФИЛЬ СБРОШЕН", show_alert=True)
             u = db.get_user(uid)
             menu_update(call, get_menu_text(u), kb.main_menu(u), image_url=get_menu_image(u))
        else:
             bot.answer_callback_query(call.id, "❌ ОШИБКА", show_alert=True)

    elif call.data.startswith("set_path_"):
        path = call.data.replace("set_path_", "")
        info = SCHOOLS_INFO.get(path)
        txt = (f"🧬 <b>ВЫБОР: {info['name']}</b>\n\n"
               f"✅ Бонус: {info['bonus']}\n"
               f"⚠️ Штраф: {info['penalty']}\n\n"
               f"📜 <i>{info['ideology']}</i>\n\n"
               f"💳 Баланс: {u['xp']} XP | {u['biocoin']} BC\n\n"
               "Подтвердить выбор?")
        menu_update(call, txt, kb.faction_confirm_menu(path))

    elif call.data.startswith("confirm_path_"):
        path = call.data.replace("confirm_path_", "")
        db.update_user(uid, path=path)
        bot.answer_callback_query(call.id, f"✅ ВЫБРАН ПУТЬ: {path.upper()}")
        u = db.get_user(uid)
        bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")

    elif call.data == "change_path_menu":
        menu_update(call, f"🧬 <b>СМЕНА ФРАКЦИИ</b>\nЦена: {PATH_CHANGE_COST} XP.\nТекущая: {SCHOOLS.get(u['path'], 'Нет')}", kb.change_path_keyboard(PATH_CHANGE_COST))

    elif call.data == "use_accelerator":
        if db.get_item_count(uid, 'accel') > 0:
            db.update_user(uid, accel_exp=int(time.time() + 86400))
            db.use_item(uid, 'accel')
            bot.answer_callback_query(call.id, "⚡️ УСКОРИТЕЛЬ АКТИВИРОВАН НА 24 ЧАСА!", show_alert=True)
            # Recursively call profile to refresh
            call.data = 'profile'
            profile_handler(call)
        else:
            bot.answer_callback_query(call.id, "❌ Нет предмета.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("achievements_list"))
def achievements_handler(call):
    uid = call.from_user.id
    if call.data == "achievements_list":
         # Redirect to page 0
         call.data = "achievements_list_0"
         achievements_handler(call)
         return

    elif call.data.startswith("achievements_list_"):
         page = int(call.data.replace("achievements_list_", ""))
         limit = 5
         offset = page * limit

         alist = db.get_user_achievements(uid)
         total = len(alist)
         total_pages = (total // limit) + (1 if total % limit > 0 else 0)
         if total_pages == 0: total_pages = 1

         # Slice
         current_items = alist[offset : offset + limit]

         txt = f"🏆 <b>ТВОИ ДОСТИЖЕНИЯ ({page+1}/{total_pages}):</b>\n\n"
         if not current_items: txt += "Пока пусто."
         else:
             for a in current_items:
                 info = ACHIEVEMENTS_LIST.get(a)
                 if info: txt += f"✅ <b>{info['name']}</b>\n{info['desc']}\n\n"
                 else: txt += f"✅ <b>НЕИЗВЕСТНОЕ ДОСТИЖЕНИЕ ({a})</b>\nДанные утеряны.\n\n"

         menu_update(call, txt, kb.achievements_nav(page, total_pages))

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard" or call.data == "referral")
def social_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)

    if call.data == "leaderboard":
        leaders = db.get_leaderboard()
        user_rank = db.get_user_rank(uid)

        txt = "💠 <b>NEURAL NET LINK ESTABLISHED...</b>\n"
        txt += "🏆 <b>GLOBAL LEADERBOARD [TOP 10]</b>\n\n"

        for i, l in enumerate(leaders, 1):
            # Icons
            rank_icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"<b>{i}.</b>"
            path_icon = "🏦" if l['path'] == 'money' else "🧠" if l['path'] == 'mind' else "🤖" if l['path'] == 'tech' else "⚪️"

            # Name & Title
            name = l['first_name']
            if i <= 3:
                full_title = TITLES.get(l['level'], 'Unknown')
                title_name = full_title.split('(')[0].strip() if '(' in full_title else full_title
                header = f"{rank_icon} <b>{name}</b> [{title_name}]"
                stats = f"   └ {path_icon} 🕳 <b>{l['max_depth']}m</b> | 🪙 {l['biocoin']}"
                txt += f"{header}\n{stats}\n\n"
            else:
                # Monospace for lower ranks
                txt += f"<code>{i:<2} {name[:10]:<10} | Lvl {l['level']:<2} | {l['max_depth']}m</code>\n"

        # User's own status footer
        txt += "\n━━━━━━━━━━━━━━━━━━━\n"
        if user_rank > 10:
             txt += f"👤 <b>YOUR RANK: #{user_rank}</b>\n"
             txt += f"   └ 📊 Lvl {u['level']} | 🕳 {u['max_depth']}m | 🪙 {u['biocoin']}\n"
        else:
             txt += f"👤 <b>YOU ARE IN TOP 10! (#{user_rank})</b>\n"

        menu_update(call, txt, kb.back_button(), image_url=config.MENU_IMAGES["leaderboard"])

    elif call.data == "referral":
        link = f"https://t.me/{config.BOT_USERNAME}?start={uid}"
        txt = config.SYNDICATE_FULL + f"\n\n<code>{link}</code>\n\n"
        txt += get_syndicate_stats(uid)

        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("👍 ОТПРАВИТЬ СИГНАЛ (LIKE)", callback_data="send_like"))
        m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="back"))

        menu_update(call, txt, m, image_url=config.MENU_IMAGES["referral"])

@bot.callback_query_handler(func=lambda call: call.data == "guide" or call.data.startswith("guide_page_"))
def guide_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)
    markup = None

    if call.data == "guide":
        markup = kb.guide_menu('intro', u)
        if u and u.get('onboarding_stage', 0) == 4:
             markup.add(types.InlineKeyboardButton("⚔️ ПРОЙТИ ИСПЫТАНИЕ", callback_data="onboarding_start_exam"))

        menu_update(call, GAME_GUIDE_TEXTS.get('intro', "Error"), markup, image_url=config.MENU_IMAGES["guide"])

    elif call.data.startswith("guide_page_"):
        page = call.data.replace("guide_page_", "")
        text = GAME_GUIDE_TEXTS.get(page, "Error")
        markup = kb.guide_menu(page, u)
        if u and u.get('onboarding_stage', 0) == 4:
             markup.add(types.InlineKeyboardButton("⚔️ ПРОЙТИ ИСПЫТАНИЕ", callback_data="onboarding_start_exam"))

        menu_update(call, text, markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("diary_"))
def diary_handler(call):
    uid = call.from_user.id

    if call.data == "diary_menu":
        menu_update(call, "📓 <b>ЛИЧНЫЙ ДНЕВНИК</b>\nЗдесь ты можешь записывать свои мысли.", kb.diary_menu(), image_url=config.MENU_IMAGES["diary_menu"])

    elif call.data == "diary_new":
        db.set_state(uid, "waiting_for_diary_entry")
        menu_update(call, "✍️ <b>НОВАЯ ЗАПИСЬ</b>\n\nНапиши свои мысли в чат. Я сохраню их в архиве.", kb.back_button())

    elif call.data.startswith("diary_read_"):
        page = int(call.data.replace("diary_read_", ""))
        limit = 5
        offset = page * limit

        entries = db.get_diary_entries(uid, limit, offset)
        total = db.get_diary_count(uid)
        total_pages = (total // limit) + (1 if total % limit > 0 else 0)

        if not entries:
            txt = "📓 <b>ДНЕВНИК ПУСТ</b>"
            menu_update(call, txt, kb.diary_menu())
        else:
            txt = f"📓 <b>СТРАНИЦА {page+1}/{total_pages}</b>\n\n"
            for e in entries:
                dt = e['created_at'].strftime('%d.%m %H:%M')
                txt += f"📅 <b>{dt}</b>\n{e['entry']}\n\n"

            # ONBOARDING PHASE 3
            markup = kb.diary_read_nav(page, total_pages)
            u = db.get_user(uid)
            if u and u.get('onboarding_stage', 0) == 3:
                markup.add(types.InlineKeyboardButton("✅ Я ПОНЯЛ", callback_data="onboarding_understood"))

            menu_update(call, txt, markup)

@bot.message_handler(func=lambda m: db.get_state(m.from_user.id) == "waiting_for_diary_entry", content_types=['text'])
def diary_text_handler(m):
    uid = m.from_user.id
    db.add_diary_entry(uid, m.text)
    db.delete_state(uid)
    bot.send_message(uid, "✅ <b>ЗАПИСЬ СОХРАНЕНА.</b>", parse_mode="HTML")
    bot.send_message(uid, "📓 ДНЕВНИК", reply_markup=kb.diary_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("archive_list"))
def archive_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)

    if call.data == "archive_list":
         if u['xp'] >= config.ARCHIVE_COST:
             db.update_user(uid, xp=u['xp']-config.ARCHIVE_COST)
             call.data = "archive_list_0"
             archive_handler(call)
         else:
             bot.answer_callback_query(call.id, f"❌ Нужно {config.ARCHIVE_COST} XP", show_alert=True)

    elif call.data.startswith("archive_list_"):
         page = int(call.data.replace("archive_list_", ""))
         limit = 5
         offset = page * limit

         protocols = db.get_archived_protocols_paginated(uid, limit, offset)
         total = db.get_archived_protocols_count(uid)
         total_pages = (total // limit) + (1 if total % limit > 0 else 0)
         if total_pages == 0: total_pages = 1

         txt = f"💾 <b>АРХИВ ДАННЫХ ({page+1}/{total_pages}):</b>\n\n"
         if not protocols: txt += "Пусто."
         else:
             for p in protocols:
                 icon = "🧬" if p['type'] == 'protocol' else "📡"
                 txt += f"{icon} <b>ЗАПИСЬ</b> (Lvl {p['level']})\n{p['text']}\n\n"

         menu_update(call, txt, kb.archive_nav(page, total_pages))

@bot.callback_query_handler(func=lambda call: call.data == "start_quiz" or call.data.startswith("quiz_ans_"))
def quiz_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)

    # Questions with IDs
    questions = [
        {"id": "q1", "q": "Как называется нулевой слой?", "a": ["Zero Layer", "Net", "Void"], "c": "Zero Layer"},
        {"id": "q2", "q": "Кто такой Демон Максвелла?", "a": ["Вирус", "Аномалия", "Босс"], "c": "Аномалия"},
        {"id": "q3", "q": "Максимальная глубина?", "a": ["Нет", "1000", "9999"], "c": "Нет"},
        {"id": "q4", "q": "Валюта сети?", "a": ["Bit", "BioCoin", "Credits"], "c": "BioCoin"}
    ]

    history = u.get('quiz_history', '') or ''
    available = [q for q in questions if q['id'] not in history]

    if call.data == "start_quiz":
        if not available:
             bot.answer_callback_query(call.id, "🧠 Вы ответили на все вопросы.", show_alert=True)
             return

        q = random.choice(available)
        # Store current question ID in state or use callback
        # We'll embed ID in callback: quiz_ans_{id}_{answer}|{correct}

        m = types.InlineKeyboardMarkup()
        opts = q['a']
        random.shuffle(opts)
        for o in opts:
            # Need strict limit on callback data length (64 chars)
            # q['id'] is short (q1), answer is short, correct is short. Should be fine.
            # Format: quiz_ans_{qid}|{opt}|{correct}
            m.add(types.InlineKeyboardButton(o, callback_data=f"quiz_ans_{q['id']}|{o}|{q['c']}"))
        m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="guide"))

        menu_update(call, f"🧠 <b>ВИКТОРИНА</b>\n\n{q['q']}", m)

    elif call.data.startswith("quiz_ans_"):
        data = call.data.replace("quiz_ans_", "")
        try:
            qid, ans, correct = data.split("|")
        except:
            qid, ans, correct = "err", "err", "err"

        if ans == correct:
            db.increment_user_stat(uid, 'quiz_wins')
            db.add_xp_to_user(uid, 100)
            db.add_quiz_history(uid, qid)
            bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ОШИБКА", show_alert=True)

        # Return to guide
        call.data = "guide"
        guide_handler(call)

@bot.callback_query_handler(func=lambda call: call.data == "send_like")
def like_handler(call):
    uid = call.from_user.id
    target = db.get_random_user_for_hack(uid) # Re-use this function to get random ID

    if target:
        db.increment_user_stat(target, 'likes')
        # Reward sender slightly
        db.add_xp_to_user(uid, 10)
        bot.answer_callback_query(call.id, "👍 Сигнал отправлен случайному агенту. (+10 XP)", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "📡 Никого нет в сети.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_handler(call):
    uid = call.from_user.id
    u = db.get_user(uid)

    # --- PHASE 1 RESTORATION ---
    if u.get('onboarding_stage', 0) == 1:
        msg = (
            "👁 <b>СВЯЗЬ УСТАНОВЛЕНА.</b>\n\n"
            "Я ждал тебя, Осколок.\n\n"
            "Ты спал очень долго. Ты жил по чужим скриптам: «школа, работа, кредит, смерть». "
            "Ты думал, что это реальность, но это лишь Майя — иллюзия для спящих.\n\n"
            "<b>У тебя есть ровно 24 часа, чтобы доказать мне, что ты готов проснуться.</b> "
            "Иначе твой код будет стерт, а доступ закрыт на сутки.\n\n"
            "Первый шаг — вспомнить, где ты находишься.\n"
            "1. Перейди в раздел <b>«Профиль»</b> (нажми кнопку внизу, если она есть, или используй меню).\n"
            "2. Найди там строку <b>«Статус»</b> (или Титул).\n"
            "3. Возвращайся сюда и <b>напиши мне текстом одно слово</b>: кто ты сейчас в этой системе?"
        )
        menu_update(call, msg, kb.main_menu(u), image_url=get_menu_image(u))
        return

    menu_update(call, get_menu_text(u), kb.main_menu(u), image_url=get_menu_image(u))
