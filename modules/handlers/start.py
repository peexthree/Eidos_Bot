from modules.bot_instance import bot
import database as db
import config
from config import REFERRAL_BONUS
import keyboards as kb
from modules.services.combat import perform_hack
from modules.services.utils import get_menu_text, get_menu_image

@bot.message_handler(commands=['hack_random'])
def hack_command(m):
    uid = m.from_user.id
    try:
        msg = perform_hack(uid)
        bot.send_message(uid, msg, parse_mode='HTML')
    except Exception as e:
        bot.send_message(uid, f"⚠️ ERROR: {e}")

@bot.message_handler(commands=['start'])
def start_handler(m):
    uid = m.from_user.id
    ref = m.text.split()[1] if len(m.text.split()) > 1 else None

    if not db.get_user(uid):
        username = m.from_user.username or "Anon"
        first_name = m.from_user.first_name or "User"
        db.add_user(uid, username, first_name, ref)
        db.log_action(uid, 'register', f"User {username} joined via {ref}")
        if ref:
             db.add_xp_to_user(int(ref), REFERRAL_BONUS)
             try: bot.send_message(int(ref), f"👤 <b>НОВЫЙ АГЕНТ:</b> {first_name}\n+{REFERRAL_BONUS} XP", parse_mode="HTML")
             except: pass

        bot.send_message(uid, f"/// EIDOS v8.0 INITIALIZED\nID: {uid}\n\nДобро пожаловать в Систему, Искатель.", parse_mode="HTML")
        msg = ("🧬 <b>ВЫБОР ПУТИ (БЕСПЛАТНО)</b>\n\n"
               "Ты должен выбрать свою специализацию, чтобы выжить.\n\n"
               "🏦 <b>МАТЕРИЯ:</b> +20% Монет в Рейдах.\n"
               "🧠 <b>РАЗУМ:</b> +10 Защиты.\n"
               "🤖 <b>ТЕХНО:</b> +10 Удачи.")
        bot.send_message(uid, msg, reply_markup=kb.path_selection_keyboard(), parse_mode="HTML")
    else:
        u = db.get_user(uid)
        bot.send_photo(uid, get_menu_image(u), caption=get_menu_text(u), reply_markup=kb.main_menu(u), parse_mode="HTML")

# ==========================================
# СЕКРЕТНЫЙ ИНСТРУМЕНТ АРХИТЕКТОРА: FILE_ID
# ==========================================
@bot.message_handler(content_types=['photo'])
def grab_file_id(message):
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
