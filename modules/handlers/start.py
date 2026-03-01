from modules.bot_instance import bot
import database as db
import config
from config import REFERRAL_BONUS
import keyboards as kb
from modules.services.combat import perform_hack
from modules.services.utils import get_menu_text, get_menu_image
from modules.services.user import check_daily_streak
import html

@bot.message_handler(commands=['hack_random'])
def hack_command(m):
    uid = m.from_user.id
    try:
        db.update_shadow_metric(uid, 'hack_random_uses', 1)
        msg = perform_hack(uid)
        bot.send_message(uid, msg, parse_mode='HTML')
    except Exception as e:
        bot.send_message(uid, f"⚠️ ERROR: {e}")

import traceback

@bot.message_handler(commands=['start'])
def start_handler(m):
    try:
        uid = m.from_user.id
        ref = m.text.split()[1] if len(m.text.split()) > 1 else None

        print(f"/// START_HANDLER: check user {uid} existence")
        u_exists = db.get_user(uid)
        print(f"/// START_HANDLER: check user {uid} existence complete")

        if not u_exists:
            username = m.from_user.username or "Anon"
            first_name = m.from_user.first_name or "User"

            print(f"/// START_HANDLER: add user {uid}")
            db.add_user(uid, username, first_name, ref)
            print(f"/// START_HANDLER: add user {uid} complete")

            print(f"/// START_HANDLER: log action for {uid}")
            db.log_action(uid, 'register', f"User {username} joined via {ref}")
            print(f"/// START_HANDLER: log action for {uid} complete")

            if ref:
                 print(f"/// START_HANDLER: add xp to user {ref}")
                 db.add_xp_to_user(int(ref), REFERRAL_BONUS)
                 print(f"/// START_HANDLER: add xp to user {ref} complete")
                 try:
                     safe_name = html.escape(first_name)
                     bot.send_message(int(ref), f"👤 <b>НОВЫЙ АГЕНТ:</b> {safe_name}\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
                 except: pass

            # INIT ONBOARDING
            import time
            db.update_user(uid, onboarding_stage=1, onboarding_start_time=int(time.time()))

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
            # Show main menu immediately so they can see Profile
            u = db.get_user(uid)
            try:
                bot.send_photo(uid, get_menu_image(u), caption=msg, reply_markup=kb.main_menu(u), parse_mode="HTML")
            except:
                bot.send_message(uid, msg, reply_markup=kb.main_menu(u), parse_mode="HTML")
        else:
            check_daily_streak(uid)
            u = db.get_user(uid)
            bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")
    except Exception as e:
        print(f"/// ERROR IN START HANDLER: {e}")
        traceback.print_exc()

# ==========================================
# СЕКРЕТНЫЙ ИНСТРУМЕНТ АРХИТЕКТОРА: FILE_ID
# ==========================================
@bot.message_handler(content_types=['photo'])
def grab_file_id(message):
    uid = message.from_user.id
    # SECURITY: Prevent unauthorized access to file IDs. Only admins allowed.
    if not db.is_user_admin(uid):
        return

    # Берем самую качественную версию картинки (она всегда последняя в списке)
    file_id = message.photo[-1].file_id

    # Формируем ответ, делаем ID моноширинным, чтобы он копировался по клику
    text = (
        "✅ **Медиа-файл загружен в кэш Telegram.**\n\n"
        "Твой `file_id`:\n"
        f"`{file_id}`\n\n"
        "_(Нажми на код, чтобы скопировать)_"
    )

    bot.reply_to(message, text, parse_mode="Markdown")
