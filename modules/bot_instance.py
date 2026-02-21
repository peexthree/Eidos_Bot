import telebot
import flask
import os
import config

# =============================================================
# ⚙️ НАСТРОЙКИ
# =============================================================

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("Error: BOT_TOKEN environment variable is not set.")
    # sys.exit(1)

WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')
# ADMIN_ID loaded from config

bot = telebot.TeleBot(TOKEN, threaded=False)
app = flask.Flask(__name__)
