import sys
from unittest.mock import MagicMock
sys.modules['openai'] = MagicMock()
sys.modules['sentry_sdk'] = MagicMock()
sys.modules['sentry_sdk.integrations'] = MagicMock()
sys.modules['sentry_sdk.integrations.flask'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['requests'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()
import sys
from unittest.mock import MagicMock

# 1. Mock bot to return the actual function from decorator
mock_bot = MagicMock()
def decorator(func):
    return func
mock_bot.message_handler.return_value = decorator

sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.bot_instance'].bot = mock_bot

sys.modules['cache_db'] = MagicMock()
sys.modules['database'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['modules.services.combat'] = MagicMock()
sys.modules['modules.services.utils'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()

import modules.handlers.start as start_handler
import database as db
import cache_db

m = MagicMock()
m.from_user.id = 12345
m.text = '/start'

# Case: Quarantined user
cache_db.get_cached_user.return_value = {
    'is_quarantined': True,
    'quarantine_end_time': 9999999999
}

print("\n--- Testing Quarantined User ---")
start_handler.start_handler(m)

print(f"bot.send_message called: {mock_bot.send_message.called}")
# Should have sent "ДОСТУП ЗАБЛОКИРОВАН"
if mock_bot.send_message.call_args:
    args, kwargs = mock_bot.send_message.call_args
    print(f"Message contains 'ДОСТУП ЗАБЛОКИРОВАН': {'ДОСТУП ЗАБЛОКИРОВАН' in args[1]}")
else:
    print("Message contains 'ДОСТУП ЗАБЛОКИРОВАН': False")
