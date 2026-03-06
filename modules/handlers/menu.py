from modules.bot_instance import bot
import cache_db
import database as db
import config
from config import TITLES, SCHOOLS, SCHOOLS_INFO, PATH_CHANGE_COST, ACHIEVEMENTS_LIST
import keyboards as kb
from modules.services.utils import menu_update, get_menu_text, get_menu_image, draw_bar
from modules.texts import GAME_GUIDE_TEXTS
from modules.services.user import get_user_stats, get_level_progress_stats, get_profile_stats, get_syndicate_stats, perform_hard_reset
import time
import random
import html
from telebot import types

@bot.callback_query_handler(func=lambda call: call.data == "profile" or call.data.startswith("set_path_") or call.data.startswith("confirm_path_") or call.data == "change_path_menu" or call.data == "use_accelerator" or call.data == "activate_purification")
def profile_handler(call):
    uid = int(call.from_user.id)
    db.update_shadow_metric(uid, 'rapid_menu_clicks', 1)
    u = db.get_user(uid)
    if not u: return
    if call.data == "profile":
        from modules.services.glitch_system import check_micro_glitch
        glitch = check_micro_glitch(uid, u.get('level', 1))
        if glitch:
            # We don't block the profile, we just show a glitch alert/bonus
            bot.answer_callback_query(call.id, "🌀 СИСТЕМНАЯ АНОМАЛИЯ", show_alert=True)
            bot.send_message(uid, f"🌀 <b>СИСТЕМНАЯ АНОМАЛИЯ</b>\n\n{glitch['message']}", parse_mode="HTML")
            if glitch.get('effect'):
                db.update_user(uid, is_glitched=True, anomaly_buff_type=glitch['effect'],
                               anomaly_buff_expiry=int(time.time() + glitch.get('effect_duration', 3600)))
            if glitch.get('reward_item'):
                db.add_item_to_inventory(uid, glitch['reward_item'], 1)


    if call.data == "profile":
        stats, _ = get_user_stats(uid)
        perc, xp_need = get_level_progress_stats(u)
        p_bar = draw_bar(perc, 100, 10)
        ach_list = db.get_user_achievements(uid)
        has_accel = db.get_item_count(uid, 'accel') > 0
        has_purification = db.get_item_count(uid, 'purification_sync') > 0

        p_stats = get_profile_stats(uid)

        # Equipment List
        equipped = db.get_equipped_items(uid)
        equip_txt = ""
        if equipped:
            equip_txt = "\n🛡 <b>ЭКИПИРОВКА:</b>\n"
            for slot, item_id in equipped.items():
                info = config.EQUIPMENT_DB.get(item_id, {})
                name = info.get('name', item_id)
                stats_arr = []
                if info.get('atk'): stats_arr.append(f"⚔️{info['atk']}")
                if info.get('def'): stats_arr.append(f"🛡{info['def']}")
                if info.get('luck'): stats_arr.append(f"🍀{info['luck']}")

                # Special effects description (shortened)
                # We can't put full description here, it's too long.
                # Just name and stats is good as per request "full description of what is equipped ... so it would be clearer what his parameters are".

                stats_str = " | ".join(stats_arr)
                if stats_str: stats_str = f"({stats_str})"
                equip_txt += f"• {name} {stats_str}\n"

        # Formatting title logic
        level_for_title = u.get('level') or 1
        full_title = TITLES.get(level_for_title, 'Unknown')
        if '(' in full_title:
            title_name = full_title.split('(')[0].strip()
            title_desc = full_title.split('(')[1].replace(')', '').strip()
        else:
            title_name = full_title
            title_desc = "Данные отсутствуют"

        school_name = SCHOOLS.get(u['path'], 'ОБЩАЯ')

        accel_status = ""
        accel_exp = u.get('accel_exp') or 0
        try: accel_exp = float(accel_exp)
        except: accel_exp = 0

        if accel_exp > time.time():
             rem_hours = int((accel_exp - time.time()) / 3600)
             accel_status = f"\n⚡️ Ускоритель: <b>АКТИВЕН ({rem_hours}ч)</b>"

        from modules.services.utils import get_vip_prefix
        safe_name = html.escape(u['username'] or u['first_name'] or "Unknown")
        vip_name = get_vip_prefix(uid, safe_name)
        msg = (
            f"👤 <b>ПРОФИЛЬ: {vip_name}</b>\n"
            f"├ 🏫 Фракция: <b>{school_name}</b>\n"
            f"└ 🔰 Статус: <b>{title_name}</b> <i>({title_desc})</i>\n\n"
    
            f"📊 <b>LVL {u.get('level') or 1}</b> | <code>{p_bar}</code> ({perc}%)\n"
            f"├ 🔋 Опыт: <b>{int(u.get('xp', 0) or 0)}</b> (До повышения: {xp_need} XP)\n"
            f"└ 🔥 Стрик: <b>{p_stats['streak']} дн.</b> (+{p_stats['streak_bonus']}% к XP)\n\n"
    
            f"🗄 <b>АРХИВ ДАННЫХ</b>\n"
            f"├ 🕳 Рекорд глубины: <b>{p_stats['max_depth']}м</b>\n"
            f"├ 🏆 Ачивки: <b>{len(ach_list)}</b>\n"
            f"└ 🌐 Протоколы: <b>{db.get_archived_protocols_count(uid)}</b>\n\n"
    
            f"⚙️ <b>СНАРЯЖЕНИЕ И СТАТЫ</b>\n"
            f"├ ⚔️ ATK: <b>{stats['atk']}</b> | 🛡 DEF: <b>{stats['def']}</b> | 🍀 LUCK: <b>{stats['luck']}</b>\n"
            f"└ 🪙 Кошелек: <b>{int(u.get('biocoin', 0) or 0)} BC</b> {accel_status}\n"
        )

        # Determine avatar based on level
        avatar_id = config.USER_AVATARS.get(u.get('level') or 1)
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
               f"💳 Баланс: {int(u.get('xp', 0) or 0)} XP | {int(u.get('biocoin', 0) or 0)} BC\n\n"
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
    uid = int(call.from_user.id)
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

def format_leaderboard_text(leaders, user_rank, u, sort_by):
    # Header
    title = "🏆 ЗАЛ СЛАВЫ: АБСОЛЮТ"
    if sort_by == 'depth': title = "🕳 ЗАЛ СЛАВЫ: БЕЗДНА"
    elif sort_by == 'biocoin': title = "🩸 ЗАЛ СЛАВЫ: КОРПОРАЦИЯ"
    elif sort_by == 'spent': title = "💎 ЗАЛ СЛАВЫ: СИНДИКАТ"

    txt = f"💠 <b>NEURAL NET LINK ESTABLISHED...</b>\n{title}\n\n"

    for i, l in enumerate(leaders, 1):
        # Medals
        rank_icon = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"<b>{i}.</b>"

        # Faction
        path_icon = "🏦" if l['path'] == 'money' else "🧠" if l['path'] == 'mind' else "🤖" if l['path'] == 'tech' else "👑"

        # Name
        name = l['first_name'] or "Unknown"
        # Sanitize name
        name = name.replace("<", "&lt;").replace(">", "&gt;")

        # Stats based on sort
        if sort_by == 'xp':
            val = f"{l['xp']:,} XP"
            detail = f"Lvl {l['level']}"
        elif sort_by == 'depth':
            val = f"{l['max_depth']}m"
            detail = f"{l['xp']:,} XP"
        elif sort_by == 'spent':
            val = f"{l.get('total_spent', 0):,} ⭐️"
            detail = f"Lvl {l['level']}"
        else: # biocoin
            val = f"{l['biocoin']:,} BC"
            detail = f"Lvl {l['level']}"

        from modules.services.utils import get_user_display_name
        # Custom data is fetched in get_leaderboard via JOIN
        custom_data = l.get('eidos_custom_data')

        username = l.get('username')
        if username:
            display_name = f"<code>@{username}</code>"
        else:
            display_name = f"<code>{html.escape(l['first_name'] or 'Unknown')}</code>"
        raw_name = username or l.get('first_name') or "Unknown"
        vip_display = get_user_display_name(l['uid'], raw_name, custom_data=custom_data).replace('<b>', '').replace('</b>', '')

        if i <= 3:
            header = f"{rank_icon} {vip_display} ({detail}) <i>{path_icon}</i> — <b>{val}</b>"
            txt += f"{header}\n"
        else:
            txt += f"{rank_icon} <b>{vip_display}</b> — {detail} ({val})\n"

    txt += "\n━━━━━━━━━━━━━━━━━━━\n"

    my_val = ""
    if sort_by == 'xp': my_val = f"{int(u.get('xp', 0) or 0):,} XP"
    elif sort_by == 'depth': my_val = f"{u['max_depth']}m"
    elif sort_by == 'spent': my_val = f"{u.get('total_spent', 0):,} ⭐️"
    else: my_val = f"{int(u.get('biocoin', 0) or 0):,} BC"

    txt += f"🎯 <b>Твой ранг: #{user_rank}</b>\n"
    txt += f"📊 <b>Твой результат: {my_val}</b>\n"

    # Flavor Text
    flavor = "📉 Система считает тебя статистической погрешностью. Работай."
    if user_rank == 1: flavor = "👑 Абсолютная Сингулярность. Матрица гнется под твой код."
    elif user_rank == 2: flavor = "🩸 Первый Претендент. Твой клинок уже у горла Архитектора."
    elif user_rank == 3: flavor = "🔥 Теневой Кардинал. Бронза, залитая кровью конкурентов."
    elif user_rank <= 5: flavor = "⚡️ Альфа-Узел. Твое имя вшито в корневые сертификаты Сети."
    elif user_rank <= 10: flavor = "👁‍🗨 Высший Совет. Ты в десятке тех, кто диктует правила Бездне."
    elif user_rank <= 15: flavor = "💀 Критическая Угроза. За твою голову уже назначена награда."
    elif user_rank <= 20: flavor = "⚙️ Элита Синдиката. Твои рейды изучают как учебное пособие."
    elif user_rank <= 30: flavor = "🧬 Высшая Мутация. Ты вырвался из серой массы. Система признала тебя."
    elif user_rank <= 40: flavor = "🔌 Проводник Хаоса. Стабильно опасен, расчетлив и смертоносен."
    elif user_rank <= 50: flavor = "🚪 Взломщик Периметра. Ты выбил дверь в Топ-50. Теперь выживай."
    else: flavor = "📉 Статистическая погрешность. Работай, чтобы стать кем-то."

    txt += f"{flavor}"

    return txt

@bot.callback_query_handler(func=lambda call: call.data == "leaderboard" or call.data.startswith("lb_") or call.data == "referral")
def social_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)

    if call.data == "leaderboard" or call.data.startswith("lb_"):
        # Determine sort mode
        sort_by = 'xp'
        if call.data == 'lb_depth': sort_by = 'depth'
        elif call.data == 'lb_biocoin': sort_by = 'biocoin'
        elif call.data == 'lb_spent': sort_by = 'spent'

        leaders = db.get_leaderboard(limit=10, sort_by=sort_by)
        user_rank = db.get_user_rank(uid, sort_by=sort_by)

        txt = format_leaderboard_text(leaders, user_rank, u, sort_by)

        menu_update(call, txt, kb.leaderboard_menu(current_sort=sort_by, leaders=leaders), image_url=config.MENU_IMAGES["leaderboard"])

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
    uid = int(call.from_user.id)
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
    uid = int(call.from_user.id)

    if call.data == "diary_menu":
        menu_update(call, "📓 <b>ЛИЧНЫЙ ДНЕВНИК</b>\nЗдесь ты можешь записывать свои мысли.", kb.diary_menu(), image_url=config.MENU_IMAGES["diary_menu"])

    elif call.data == "diary_new":
        db.set_state(uid, "waiting_for_diary_entry"); cache_db.clear_cache(uid)
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
                if e.get('created_at'):
                    dt = e['created_at'].strftime('%d.%m %H:%M')
                else:
                    dt = "??.?? ??:??"
                txt += f"📅 <b>{dt}</b>\n{e['entry']}\n\n"

            # ONBOARDING PHASE 3
            markup = kb.diary_read_nav(page, total_pages)
            u = db.get_user(uid)
            if u and u.get('onboarding_stage', 0) == 3:
                markup.add(types.InlineKeyboardButton("✅ Я ПОНЯЛ", callback_data="onboarding_understood"))

            menu_update(call, txt, markup)

@bot.message_handler(func=lambda m: cache_db.get_cached_user_state(m.from_user.id) == 'waiting_for_diary_entry', content_types=['text'])
def diary_text_handler(m):
    uid = int(m.from_user.id)
    db.add_diary_entry(uid, m.text)
    db.delete_state(uid); cache_db.clear_cache(uid)
    bot.send_message(uid, "✅ <b>ЗАПИСЬ СОХРАНЕНА.</b>", parse_mode="HTML")
    bot.send_message(uid, "📓 ДНЕВНИК", reply_markup=kb.diary_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("archive_list"))
def archive_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)

    if call.data == "archive_list":
         if int(u.get('xp', 0) or 0) >= config.ARCHIVE_COST:
             db.update_user(uid, xp=int(u.get('xp', 0) or 0)-config.ARCHIVE_COST)
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
    uid = int(call.from_user.id)
    u = db.get_user(uid)

    # Questions with IDs
    questions = [
        {"id": "q1", "q": "Как называется путешествие?", "a": ["Нулевой слой", "Сеть", "Дыра"], "c": "Нулевой слой"},
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
            # Fetch user again to get updated history
            u = db.get_user(uid)
            history = u.get('quiz_history', '') or ''
            available_after = [q for q in questions if q['id'] not in history]

            if not available_after:
                bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP\n\n🧠 Вы познали все тайны. Викторина завершена.", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "✅ ВЕРНО! +100 XP", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ОШИБКА", show_alert=True)

        # Return to guide
        call.data = "guide"
        guide_handler(call)

@bot.callback_query_handler(func=lambda call: call.data == "send_like")
def like_handler(call):
    uid = int(call.from_user.id)
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
    uid = int(call.from_user.id)

    from modules.handlers.glitch_handler import check_for_glitch_state
    if check_for_glitch_state(uid, bot, call.message.chat.id):
        try: bot.answer_callback_query(call.id)
        except: pass
        return

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


@bot.callback_query_handler(func=lambda call: call.data == "feedback_menu")
def feedback_init_handler(call):
    uid = int(call.from_user.id)
    db.set_state(uid, "waiting_for_feedback"); cache_db.clear_cache(uid)
    msg = (
        "✉️ <b>ОБРАТНАЯ СВЯЗЬ</b>\n\n"
        "Опиши найденный баг или предложение по улучшению.\n"
        "Я передам сообщение Создателю.Если это полезная находка, то тебя щедро наградят \n\n"
        "<i>Напиши текст и отправь в чат.</i>"
    )
    menu_update(call, msg, kb.back_button())

@bot.message_handler(func=lambda m: cache_db.get_cached_user_state(m.from_user.id) == 'waiting_for_feedback', content_types=['text'])
def feedback_process_handler(m):
    uid = int(m.from_user.id)
    text = m.text
    u = db.get_user(uid)
    username = u.get('username', 'NoUsername')
    first_name = u.get('first_name', 'Unknown')

    # Send to Admin
    safe_first_name = html.escape(first_name)
    safe_text = html.escape(text)
    admin_msg = (
        f"📩 <b>FEEDBACK RECEIVED</b>\n"
        f"From: {safe_first_name} (@{username}) [ID: {uid}]\n\n"
        f"{safe_text}"
    )
    try:
        bot.send_message(config.ADMIN_ID, admin_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Feedback Error: {e}")

    db.delete_state(uid); cache_db.clear_cache(uid)
    bot.send_message(uid, "✅ <b>СООБЩЕНИЕ ОТПРАВЛЕНО.</b>\nСпасибо за вклад в развитие Системы.", parse_mode="HTML")

    # Return to menu
    try:
        bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")
    except:
        bot.send_message(uid, get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_user_"))
def view_user_handler(call):
    uid_str = call.data.replace("view_user_", "")
    try:
        target_uid = int(uid_str)
    except ValueError:
        bot.answer_callback_query(call.id, "Ошибка ID", show_alert=True)
        return

    stats, tu = get_user_stats(target_uid)
    if not tu:
        bot.answer_callback_query(call.id, "Пользователь не найден.", show_alert=True)
        return

    from modules.services.user import get_profile_stats
    profile_txt = get_profile_stats(target_uid)

    # Prepend info about who this is
    final_txt = f"👁 <b>НАБЛЮДЕНИЕ ЗА ОБЪЕКТОМ:</b> {tu['username'] or tu['first_name']}\n\n{profile_txt}"

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 ВЕРНУТЬСЯ К РЕЙТИНГУ", callback_data="leaderboard"))

    avatar = get_menu_image(tu)
    menu_update(call, final_txt, m, image_url=avatar)

@bot.callback_query_handler(func=lambda call: call.data == "find_user_dossier_init")
def find_user_dossier_init_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно BioCoin (нужно 100 BC)", show_alert=True)
        return

    txt = "⚠️ <b>Внимание!</b> Доступ к защищенному досье «Паспорт Осколка» стоит <b>100 BC</b>.\nПродолжить?"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("✅ Да, взломать (100 BC)", callback_data="find_user_dossier_confirm"))
    m.add(types.InlineKeyboardButton("❌ Отмена", callback_data="leaderboard"))

    menu_update(call, txt, m)


@bot.callback_query_handler(func=lambda call: call.data == "find_user_dossier_confirm")
def find_user_dossier_confirm_handler(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно BioCoin", show_alert=True)
        return

    db.update_user(uid, biocoin=int(u.get('biocoin', 0)) - 100)
    bot.answer_callback_query(call.id, "💰 [ВЗЛОМ: -100 BC]", show_alert=False)
    db.set_state(uid, "await_dossier_search"); cache_db.clear_cache(uid)

    txt = "⚠️ <b>СИСТЕМА:</b> Введите никнейм пользователя (можно без @) для взлома его досье.\n<i>(Вы можете скопировать ник из списка Зала Славы)</i>"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("❌ Отмена", callback_data="leaderboard"))

    menu_update(call, txt, m)

@bot.message_handler(func=lambda m: cache_db.get_cached_user_state(m.from_user.id) == "await_dossier_search")
def process_dossier_search(m):
    uid = int(m.from_user.id)
    u = db.get_user(uid)
    if not u: return

    target_name = m.text.strip().lstrip('@')

    # Try finding user
    target_uid = None
    target_user_data = None
    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        if cur:
            cur.execute("SELECT uid, username, first_name, level, xp, biocoin, total_spent, path FROM players WHERE username ILIKE %s OR first_name ILIKE %s LIMIT 1", (target_name, target_name))
            res = cur.fetchone()
            if res:
                target_uid = res['uid']
                target_user_data = dict(res)

    if not target_uid:
        bot.send_message(m.chat.id, f"❌ Объект <b>@{target_name}</b> не найден в базе данных.", parse_mode="HTML")
        db.delete_state(uid); cache_db.clear_cache(uid)
        return

    db.delete_state(uid); cache_db.clear_cache(uid)

    msg = bot.send_message(m.chat.id, "📡 <b>УСТАНОВКА СОЕДИНЕНИЯ...</b>\nВзлом защищенного сервера. Инициализация протокола «Паспорт Осколка»...", parse_mode="HTML")

    from modules.services.ai_worker import generate_user_dossier_worker
    import threading
    from modules.services.worker_queue import enqueue_task
    enqueue_task(generate_user_dossier_worker, m.chat.id, uid, target_user_data, msg.message_id)



# --- Dossier Interactions ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("dossier_attack_"))
def dossier_attack_handler(call):
    uid = int(call.from_user.id)
    target_uid = int(call.data.split("_")[2])

    # Check hourly rate limit
    throttle_key = f"dossier_atk_{uid}_{target_uid}"
    if not cache_db.check_throttle(uid, throttle_key, 3600):
        bot.answer_callback_query(call.id, "⚠️ На этого игрока можно нападать не чаще раза в час.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "📡 Инициализация боевого протокола...")

    target_user = db.get_user(target_uid)
    if not target_user:
        bot.send_message(uid, "❌ Объект потерял сигнал.")
        return

    txt = f"🎯 <b>ОБЪЕКТ ОБНАРУЖЕН:</b> {target_user.get('username') or target_user.get('first_name') or 'Unknown'}\n"
    txt += f"📊 Уровень: {target_user.get('level', 1)}\n\nНачать взлом?"

    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ НАПАСТЬ", callback_data=f"pvp_atk_direct_{target_uid}"))
    m.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="leaderboard"))

    bot.send_message(uid, txt, reply_markup=m, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pvp_atk_direct_"))
def pvp_atk_direct_handler(call):
    target_uid = int(call.data.split("_")[3])
    # Prepare target data and redirect to pvp search logic
    from modules.handlers.pvp import pvp_search_handler
    # We fake the message for pvp_search_handler logic if needed,
    # but pvp_search_handler usually does random.
    # Let's use pvp_attack_prep logic directly.

    with db.db_cursor(cursor_factory=db.RealDictCursor) as cur:
        cur.execute("SELECT * FROM players WHERE uid = %s", (target_uid,))
        target = cur.fetchone()

    if not target:
        bot.answer_callback_query(call.id, "❌ Объект исчез.")
        return

    # Extract slots for preview (standard pvp logic)
    target_slots = {}
    with db.db_cursor() as cur:
        cur.execute("SELECT slot_id, item_id FROM user_pvp_deck WHERE uid = %s", (target_uid,))
        for sid, iid in cur.fetchall():
            target_slots[sid] = config.SOFTWARE_DB[iid]['icon']

    safe_target = {
        'uid': target_uid,
        'name': target.get('username') or target.get('first_name') or "Unknown",
        'level': target['level'],
        'slots_preview': target_slots
    }

    state_data = {
        'target_uid': target_uid,
        'target_info': safe_target,
        'slots': {} # Attacker starts with empty selection or current deck
    }

    # Load current deck for attacker
    with db.db_cursor() as cur:
        cur.execute("SELECT slot_id, item_id FROM user_pvp_deck WHERE uid = %s", (call.from_user.id,))
        for sid, iid in cur.fetchall():
            state_data['slots'][str(sid)] = iid

    db.set_state(call.from_user.id, 'pvp_attack_prep', json.dumps(state_data))

    from modules.handlers.pvp import _show_attack_screen
    _show_attack_screen(call, safe_target, state_data['slots'])

@bot.callback_query_handler(func=lambda call: call.data.startswith("dossier_msg_"))
def dossier_msg_init(call):
    uid = int(call.from_user.id)
    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.answer_callback_query(call.id, "❌ Недостаточно BioCoin (нужно 100 BC)", show_alert=True)
        return

    target_uid = int(call.data.split("_")[2])
    db.set_state(uid, f"await_dossier_msg_{target_uid}"); cache_db.clear_cache(uid)

    bot.send_message(uid, "✉️ <b>ОТПРАВКА СООБЩЕНИЯ (100 BC)</b>\nВведите текст сообщения для этого пользователя. Он увидит, от кого оно пришло.", parse_mode="HTML")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: str(cache_db.get_cached_user_state(m.from_user.id) or "").startswith("await_dossier_msg_"))
def process_dossier_msg(m):
    uid = int(m.from_user.id)
    state = db.get_state(uid)
    try:
        target_uid = int(state.split("_")[3])
    except:
        db.delete_state(uid); cache_db.clear_cache(uid)
        return

    u = db.get_user(uid)
    if not u: return

    if int(u.get('biocoin', 0)) < 100:
        bot.send_message(m.chat.id, "❌ Недостаточно BioCoin.")
        db.delete_state(uid); cache_db.clear_cache(uid)
        return

    msg_text = m.text.strip()
    if not msg_text:
        bot.send_message(m.chat.id, "❌ Сообщение не может быть пустым.")
        return

    db.update_user(uid, biocoin=int(u.get('biocoin', 0)) - 100)
    db.delete_state(uid)

    sender_name = u.get('username') or u.get('first_name') or "Unknown"
    target_text = f"📩 <b>ВХОДЯЩИЙ СИГНАЛ</b>\nОт: @{sender_name}\n\n{msg_text}"

    try:
        bot.send_message(target_uid, target_text, parse_mode="HTML")
        bot.send_message(m.chat.id, "✅ Сообщение успешно доставлено по защищенному каналу.")
    except:
        bot.send_message(m.chat.id, "❌ Не удалось доставить сообщение. BC возвращены.")
        db.update_user(uid, biocoin=db.get_user(uid).get('biocoin', 0) + 100)
