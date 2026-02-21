import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules before import
sys.modules["telebot"] = MagicMock()
sys.modules["telebot.types"] = MagicMock()
sys.modules["telebot.apihelper"] = MagicMock()
sys.modules["config"] = MagicMock()
sys.modules["database"] = MagicMock()

# Import the module under test
# We need to mock 'modules.bot_instance' so 'from modules.bot_instance import bot' works
mock_bot_instance = MagicMock()
sys.modules["modules.bot_instance"] = mock_bot_instance
mock_bot = MagicMock()
mock_bot_instance.bot = mock_bot

# Mock ApiTelegramException class to be usable in try-except blocks
class MockApiTelegramException(Exception):
    def __init__(self, function_name, result, result_json):
        self.function_name = function_name
        self.result = result
        self.result_json = result_json
        self.error_code = 400
        self.description = "Bad Request"

# Inject MockApiTelegramException into telebot.apihelper
sys.modules["telebot.apihelper"].ApiTelegramException = MockApiTelegramException

from modules.services import utils

class TestMenuUpdate(unittest.TestCase):
    def setUp(self):
        self.mock_bot = mock_bot
        self.mock_bot.reset_mock()

        self.call = MagicMock()
        self.call.message.chat.id = 123
        self.call.message.message_id = 456
        self.call.from_user.id = 789

    def test_menu_update_fallback_image(self):
        # Simulate edit_message_media raising ApiTelegramException
        def side_effect(*args, **kwargs):
            raise MockApiTelegramException("test", "result", "Bad Request: message to edit not found")

        self.mock_bot.edit_message_media.side_effect = side_effect

        # Call menu_update with image_url
        print("Calling menu_update...")
        utils.menu_update(self.call, "test text", markup=None, image_url="http://fake.url")

        # Verify that send_photo was called as fallback
        if self.mock_bot.send_photo.called:
            print("SUCCESS: send_photo called as fallback")
        else:
            print("FAILURE: send_photo NOT called as fallback")
            self.fail("send_photo NOT called as fallback")

if __name__ == "__main__":
    unittest.main()
