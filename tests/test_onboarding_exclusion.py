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

# 1. Mock bot
mock_bot = MagicMock()
handlers = []
def register_handler(f, **kw):
    handlers.append((f, kw))
    return f

# Correct side_effect to handle Telebot decorator pattern
def message_handler_decorator(*args, **kwargs):
    def wrapper(f):
        return register_handler(f, **kwargs)
    return wrapper

mock_bot.message_handler.side_effect = message_handler_decorator

sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.bot_instance'].bot = mock_bot

sys.modules['cache_db'] = MagicMock()
sys.modules['database'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['modules.services.utils'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()

import modules.handlers.onboarding as onboarding

# Find phase1_wrong_text_handler
wrong_handler_entry = [h for h in handlers if h[0].__name__ == 'phase1_wrong_text_handler'][0]
handler_func = wrong_handler_entry[0]
filter_func = wrong_handler_entry[1]['func']

# Mock message for /start
m_start = MagicMock()
m_start.text = '/start'
m_start.from_user.id = 12345

# Mock user in stage 1
sys.modules['cache_db'].get_cached_user.return_value = {'onboarding_stage': 1}

print(f"Filter result for '/start': {filter_func(m_start)}")

# Mock message for plain text
m_text = MagicMock()
m_text.text = 'random'
m_text.from_user.id = 12345
print(f"Filter result for 'random': {filter_func(m_text)}")
