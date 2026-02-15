import telebot
import flask
from config import TOKEN, ADMIN_ID, MENU_IMAGE_URL
import database as db
import keyboards as kb

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if not db.get_user(uid):
        # Логика регистрации...
        pass
    bot.send_photo(m.chat.id, MENU_IMAGE_URL, caption="/// СИСТЕМА ONLINE", reply_markup=kb.main_menu(uid))

# Сюда переедут все @bot.callback_query_handler...

if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=5000)
