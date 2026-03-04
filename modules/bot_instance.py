import telebot
import flask
import os

# =============================================================
# ⚙️ НАСТРОЙКИ
# =============================================================

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN environment variable is not set.")

WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')

# Enable Middleware
telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
