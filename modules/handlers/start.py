import cache_db
from modules.bot_instance import bot
import database as db
import config
from config import REFERRAL_BONUS
import keyboards as kb
from modules.services.combat import perform_hack
from modules.services.utils import get_menu_text, get_menu_image
from modules.services.user import check_daily_streak
import html
import traceback
import time

def check_quarantine(uid):
    try:
        u = cache_db.get_cached_user(uid)
        if not u: return False, 0

        if u.get('is_quarantined'):
            end_time = u.get('quarantine_end_time', 0)
            if time.time() < float(end_time or 0):
                return True, int((float(end_time) - time.time()) / 3600)
            else:
                db.update_user(uid, is_quarantined=False)
                return False, 0

        level = int(u.get('level', 1))
        stage = int(u.get('onboarding_stage', 0))
        if level < 2 and stage > 0:
            start_time = float(u.get('onboarding_start_time', 0))
            if start_time > 0 and (time.time() - start_time) > 86400:
                db.quarantine_user(uid)
                return True, 24
    except Exception as e:
        print(f"/// ERROR IN check_quarantine: {e}")
        traceback.print_exc()

    return False, 0


@bot.message_handler(commands=['hack_random'])
def hack_command(m):
    uid = int(m.from_user.id)
    try:
        db.update_shadow_metric(uid, 'hack_random_uses', 1)
        msg = perform_hack(uid)
        bot.send_message(uid, msg, parse_mode='HTML')
    except Exception as e:
        bot.send_message(uid, f"⚠️ ERROR: {e}")

@bot.message_handler(commands=['start'])
def start_handler(m):
    uid = int(m.from_user.id)
    print(f"/// DEBUG: Entering start_handler for user {uid}")
    try:
        # --- QUARANTINE CHECK ---
        print(f"/// START_HANDLER: Performing quarantine check for {uid}")
        is_q, rem_hours = check_quarantine(uid)
        if is_q:
            print(f"/// START_HANDLER: User {uid} is quarantined")
            msg = (
                "⛔️ <b>ДОСТУП ЗАБЛОКИРОВАН</b>\n\n"
                "Ты упустил окно возможностей. Система распознала в тебе спящий NPC.\n"
                "Возвращайся в свой сон.\n\n"
                f"⏳ Повторная попытка Сборки будет доступна через <b>{rem_hours} часов</b>."
            )
            bot.send_message(uid, msg, parse_mode="HTML")
            return

        ref = m.text.split()[1] if len(m.text.split()) > 1 else None

        print(f"/// START_HANDLER: Checking user {uid} existence in DB")
        u_exists = db.get_user(uid)
        print(f"/// START_HANDLER: User exists: {bool(u_exists)}")

        if not u_exists:
            username = m.from_user.username or "Anon"
            first_name = m.from_user.first_name or "User"

            print(f"/// START_HANDLER: Adding new user {uid}")
            db.add_user(uid, username, first_name, ref); cache_db.clear_cache(uid)
            db.log_action(uid, 'register', f"User {username} joined via {ref}")

            if ref:
                print(f"/// START_HANDLER: Applying referral bonus for {ref}")
                try:
                    db.add_xp_to_user(int(ref), REFERRAL_BONUS)
                    safe_name = html.escape(first_name)
                    bot.send_message(int(ref), f"👤 <b>НОВЫЙ АГЕНТ:</b> {safe_name}\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
                except Exception as ref_err:
                    print(f"/// START_HANDLER: Referral error: {ref_err}")

            # INIT ONBOARDING
            print(f"/// START_HANDLER: Initializing onboarding for {uid}")
            db.update_user(uid, onboarding_stage=1, onboarding_start_time=int(time.time())); cache_db.clear_cache(uid)

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

            u = cache_db.get_cached_user(uid)
            try:
                bot.send_photo(uid, get_menu_image(u), caption=msg, reply_markup=kb.main_menu(u), parse_mode="HTML")
            except Exception as e:
                print(f"/// START_HANDLER: Photo send failed, falling back to message: {e}")
                bot.send_message(uid, msg, reply_markup=kb.main_menu(u), parse_mode="HTML")
        else:
            print(f"/// START_HANDLER: Returning user {uid}, checking streak")
            check_daily_streak(uid)
            u = cache_db.get_cached_user(uid)
            bot.send_message(uid, "Инициализация интерфейса...", reply_markup=kb.get_main_reply_keyboard(u))
            bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")
            print(f"/// START_HANDLER: Interface initialized for user {uid}")
    except Exception as e:
        print(f"/// CRITICAL ERROR IN START HANDLER for user {getattr(m.from_user, 'id', 'Unknown')}: {e}")
        traceback.print_exc()

# ==========================================
# СЕКРЕТНЫЙ ИНСТРУМЕНТ АРХИТЕКТОРА: FILE_ID
# ==========================================
@bot.message_handler(content_types=['photo'])
def grab_file_id(message):
    uid = int(message.from_user.id)
    if not db.is_user_admin(uid):
        return

    file_id = message.photo[-1].file_id
    text = (
        "✅ **Медиа-файл загружен в кэш Telegram.**\n\n"
        "Твой `file_id`:\n"
        f"`{file_id}`\n\n"
        "_(Нажми на код, чтобы скопировать)_"
    )
    bot.reply_to(message, text, parse_mode="Markdown")
