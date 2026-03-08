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
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies BEFORE importing the handler
sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['cache_db'] = MagicMock()
sys.modules['database'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['modules.services.combat'] = MagicMock()
sys.modules['modules.services.utils'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()


# Setup proper bot decorator mocking
mock_bot = MagicMock()
def decorator(func):
    return func
mock_bot.message_handler.return_value = decorator
sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.bot_instance'].bot = mock_bot

import modules.handlers.start as start_handler
import database as db
import cache_db


class TestStartHandler(unittest.TestCase):
    def test_start_handler_logic(self):
        m = MagicMock()
        m.from_user.id = 12345
        m.from_user.username = 'testuser'
        m.from_user.first_name = 'Test'
        m.text = '/start'

        import database as db
        import cache_db

        cache_db.get_cached_user.return_value = None
        db.get_user.return_value = None

        print("\n--- Executing start_handler ---")
        start_handler.start_handler(m)
        print("--- Execution finished ---")

        db.add_user.assert_called()
        print("PASS: add_user was called")

if __name__ == '__main__':
    unittest.main()
