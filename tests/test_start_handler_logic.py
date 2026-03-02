import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock modules
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot'].types = sys.modules['telebot.types']
sys.modules['database'] = MagicMock()
sys.modules['cache_db'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.services.combat'] = MagicMock()
sys.modules['modules.services.utils'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()

import modules.handlers.start as start_handler

class TestStartHandler(unittest.TestCase):
    def setUp(self):
        self.bot = sys.modules['modules.bot_instance'].bot
        self.db = sys.modules['database']
        self.cache_db = sys.modules['cache_db']

    def test_start_handler_new_user(self):
        # Setup mock message
        m = MagicMock()
        m.from_user.id = 12345
        m.from_user.username = 'testuser'
        m.from_user.first_name = 'Test'
        m.text = '/start'

        # Mock DB response: user does not exist
        self.db.get_user.return_value = None
        self.cache_db.get_cached_user.return_value = None

        # Execute
        start_handler.start_handler(m)

        # Verify new user creation
        self.db.add_user.assert_called_with(12345, 'testuser', 'Test', None)
        self.db.update_user.assert_any_call(12345, onboarding_stage=1, onboarding_start_time=unittest.mock.ANY)

    def test_start_handler_quarantined(self):
        # Setup mock message
        m = MagicMock()
        m.from_user.id = 12345
        m.text = '/start'

        # Mock cache_db: user is quarantined
        self.cache_db.get_cached_user.return_value = {
            'is_quarantined': True,
            'quarantine_end_time': 9999999999
        }

        # Execute
        start_handler.start_handler(m)

        # Verify blocked message sent
        self.bot.send_message.assert_called()
        args, kwargs = self.bot.send_message.call_args
        self.assertIn("ДОСТУП ЗАБЛОКИРОВАН", args[1])

if __name__ == '__main__':
    unittest.main()
