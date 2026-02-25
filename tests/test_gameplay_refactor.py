import sys
import unittest
import unittest.mock
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# Mock telebot properly
mock_telebot = MagicMock()
sys.modules['telebot'] = mock_telebot
sys.modules['telebot.apihelper'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()

sys.modules['flask'] = MagicMock()

# Mock bot instance
mock_bot_instance = MagicMock()
sys.modules['modules.bot_instance'] = mock_bot_instance
sys.modules['modules.bot_instance'].bot = MagicMock()

# Mock database
sys.modules['database'] = MagicMock()

# Import the module under test
from modules.handlers import gameplay

class TestGameplayRefactor(unittest.TestCase):

    @patch('modules.handlers.gameplay.process_raid_step')
    @patch('modules.handlers.gameplay.menu_update')
    @patch('modules.handlers.gameplay.get_consumables')
    @patch('modules.handlers.gameplay.kb')
    @patch('modules.handlers.gameplay.bot')
    def test_handle_raid_action_success(self, mock_bot, mock_kb, mock_get_consumables, mock_menu_update, mock_process_raid_step):
        # Setup
        call_obj = MagicMock()
        call_obj.id = 12345
        uid = 999

        # Mock process_raid_step result
        # res, txt, extra, new_u, etype, cost
        mock_process_raid_step.return_value = (True, "Step Text", {'alert': 'Alert Msg'}, {}, 'neutral', 10)

        mock_get_consumables.return_value = {'battery': 1}
        mock_kb.raid_action_keyboard.return_value = "MARKUP"

        # Execute
        gameplay.handle_raid_action(call_obj, uid)

        # Verify
        mock_process_raid_step.assert_called_once_with(uid)
        mock_bot.answer_callback_query.assert_called_with(call_obj.id, 'Alert Msg', show_alert=True)
        mock_kb.raid_action_keyboard.assert_called_with(10, 'neutral', consumables={'battery': 1}, has_data_spike=False)
        mock_menu_update.assert_called_with(call_obj, "Step Text", "MARKUP", image_url=None)

    @patch('modules.handlers.gameplay.process_raid_step')
    @patch('modules.handlers.gameplay.menu_update')
    @patch('modules.handlers.gameplay.bot')
    def test_handle_raid_action_failure(self, mock_bot, mock_menu_update, mock_process_raid_step):
        # Setup
        call_obj = MagicMock()
        call_obj.id = 12345
        uid = 999

        # Mock failure
        mock_process_raid_step.return_value = (False, "Failure Text", {}, {}, 'error', 0)

        # Execute
        gameplay.handle_raid_action(call_obj, uid)

        # Verify
        mock_bot.answer_callback_query.assert_called_with(call_obj.id, "Failure Text", show_alert=True)
        mock_menu_update.assert_not_called()

    @patch('modules.handlers.gameplay.process_raid_step')
    @patch('modules.handlers.gameplay.menu_update')
    @patch('modules.handlers.gameplay.bot')
    @patch('modules.handlers.gameplay.get_consumables')
    @patch('modules.handlers.gameplay.kb')
    def test_handle_raid_action_custom_callback(self, mock_kb, mock_get_consumables, mock_bot, mock_menu_update, mock_process_raid_step):
        call_obj = MagicMock()
        call_obj.id = 12345
        uid = 999

        mock_process_raid_step.return_value = (True, "Success", {}, {}, 'neutral', 10)
        mock_get_consumables.return_value = {}

        # Custom callback
        callback_mock = MagicMock(return_value=True) # Returns True (alert handled)

        gameplay.handle_raid_action(call_obj, uid, custom_success_callback=callback_mock)

        callback_mock.assert_called_once_with(call_obj, uid, {})
        # Ensure default alert NOT called
        mock_bot.answer_callback_query.assert_not_called()

    @patch('modules.handlers.gameplay.process_raid_step')
    @patch('modules.handlers.gameplay.menu_update')
    @patch('modules.handlers.gameplay.bot')
    @patch('modules.handlers.gameplay.get_consumables')
    @patch('modules.handlers.gameplay.kb')
    def test_handle_raid_action_text_prefix(self, mock_kb, mock_get_consumables, mock_bot, mock_menu_update, mock_process_raid_step):
        call_obj = MagicMock()
        call_obj.id = 12345
        uid = 999

        mock_process_raid_step.return_value = (True, "Main Text", {}, {}, 'neutral', 0)
        mock_get_consumables.return_value = {}

        gameplay.handle_raid_action(call_obj, uid, text_prefix="PREFIX\n")

        mock_menu_update.assert_called_with(call_obj, "PREFIX\nMain Text", unittest.mock.ANY, image_url=None)

if __name__ == '__main__':
    unittest.main()
