import sys
import unittest
from unittest.mock import MagicMock

# --- MOCKING DEPENDENCIES ---

# Helper to make decorators pass-through
def mock_decorator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

# Create mock modules
mock_bot_module = MagicMock()
mock_bot_instance = MagicMock()
mock_bot_instance.message_handler.side_effect = mock_decorator
mock_bot_module.bot = mock_bot_instance
sys.modules['modules.bot_instance'] = mock_bot_module

mock_db = MagicMock()
sys.modules['database'] = mock_db

mock_config = MagicMock()
mock_config.REFERRAL_BONUS = 100
sys.modules['config'] = mock_config

mock_kb = MagicMock()
sys.modules['keyboards'] = mock_kb

mock_combat = MagicMock()
sys.modules['modules.services.combat'] = mock_combat

mock_utils = MagicMock()
sys.modules['modules.services.utils'] = mock_utils

mock_user_service = MagicMock()
sys.modules['modules.services.user'] = mock_user_service

# Adjust path to find modules
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the module under test
try:
    from modules.handlers import start
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class TestSecurityVulnerability(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_bot_instance.reset_mock()
        mock_db.reset_mock()

    def test_grab_file_id_blocked_for_non_admin(self):
        """
        Test that grab_file_id BLOCKS non-admin users.
        """
        print("\n--- Testing Non-Admin Access ---")

        # 1. Setup mock message
        user_id = 12345
        message = MagicMock()
        message.from_user.id = user_id

        photo_obj = MagicMock()
        photo_obj.file_id = "test_file_id_123"
        message.photo = [photo_obj]

        # 2. Mock db.is_user_admin (User is NOT admin)
        mock_db.is_user_admin.return_value = False

        # 3. Call handler
        start.grab_file_id(message)

        # 4. Assert
        if mock_bot_instance.reply_to.called:
            print("[FAIL] bot.reply_to was called for non-admin!")
        else:
            print("[PASS] bot.reply_to was NOT called for non-admin.")

        mock_bot_instance.reply_to.assert_not_called()

    def test_grab_file_id_allowed_for_admin(self):
        """
        Test that grab_file_id ALLOWS admin users.
        """
        print("\n--- Testing Admin Access ---")

        # 1. Setup mock message
        user_id = 99999
        message = MagicMock()
        message.from_user.id = user_id

        photo_obj = MagicMock()
        photo_obj.file_id = "admin_file_id"
        message.photo = [photo_obj]

        # 2. Mock db.is_user_admin (User IS admin)
        mock_db.is_user_admin.return_value = True

        # 3. Call handler
        start.grab_file_id(message)

        # 4. Assert
        if mock_bot_instance.reply_to.called:
            print("[PASS] bot.reply_to was called for admin.")
        else:
            print("[FAIL] bot.reply_to was NOT called for admin!")

        mock_bot_instance.reply_to.assert_called()

if __name__ == '__main__':
    unittest.main()
