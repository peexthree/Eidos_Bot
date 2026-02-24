
import unittest
from unittest.mock import MagicMock, patch
import sys
import json

# --- MOCKS SETUP ---
mock_bot_instance = MagicMock()
mock_bot = MagicMock()

# Configure callback_query_handler to be a transparent decorator
def handler_decorator(*args, **kwargs):
    def wrapper(f):
        return f
    return wrapper

mock_bot.callback_query_handler.side_effect = handler_decorator
mock_bot.message_handler.side_effect = handler_decorator

mock_bot_instance.bot = mock_bot
sys.modules['modules.bot_instance'] = mock_bot_instance

mock_db = MagicMock()
sys.modules['database'] = mock_db

mock_config = MagicMock()
mock_config.SOFTWARE_DB = {
    "soft_brute_v1": {"icon": "🔨", "name": "Brute", "cost": 100, "type": "atk", "power": 10, "desc": "Simple attack"}
}
mock_config.MENU_IMAGES = {"pvp_menu": "http://image.com/pvp.jpg"}
mock_config.ITEM_IMAGES = {}
mock_config.QUARANTINE_LEVEL = 5
sys.modules['config'] = mock_config

mock_kb = MagicMock()
sys.modules['keyboards'] = mock_kb

mock_utils = MagicMock()
sys.modules['modules.services.utils'] = mock_utils

mock_pvp_service = MagicMock()
sys.modules['modules.services.pvp'] = mock_pvp_service

mock_telebot = MagicMock()
sys.modules['telebot'] = mock_telebot
sys.modules['telebot.types'] = MagicMock()

# Now import the handler module
from modules.handlers import pvp

class TestPvpHandlersState(unittest.TestCase):
    def setUp(self):
        mock_db.reset_mock()
        mock_bot.reset_mock()
        mock_utils.reset_mock()
        mock_pvp_service.reset_mock()

    def test_pvp_atk_sel_handler_success(self):
        # Setup CallbackQuery
        call = MagicMock()
        call.data = "pvp_atk_sel_1_soft_brute_v1"
        call.from_user.id = 12345
        call.id = "call_id_1"

        # Mock db.get_full_state to return the correct tuple
        state_data = {
            'target_uid': 999,
            'slots': {"1": None, "2": None, "3": None},
            'target_info': {'uid': 999, 'name': 'Target', 'level': 5, 'est_loot': 100, 'threat': 'LOW', 'slots_preview': {}}
        }
        mock_db.get_full_state.return_value = ('pvp_attack_prep', json.dumps(state_data))

        # Mock other DB calls if needed
        mock_db.get_user.return_value = {'uid': 12345, 'level': 10, 'biocoin': 1000}

        # Execute
        pvp.pvp_atk_sel_handler(call)

        # Verify
        # 1. It should NOT answer with "Session expired"
        # 2. It SHOULD call db.set_state with updated slots

        self.assertTrue(mock_db.set_state.called)

        # Check arguments to set_state
        args, _ = mock_db.set_state.call_args
        uid_arg, state_arg, json_arg = args
        self.assertEqual(uid_arg, 12345)
        self.assertEqual(state_arg, 'pvp_attack_prep')

        saved_data = json.loads(json_arg)
        self.assertEqual(saved_data['slots']['1'], 'soft_brute_v1')

    def test_pvp_atk_sel_handler_session_expired(self):
        # Setup CallbackQuery
        call = MagicMock()
        call.data = "pvp_atk_sel_1_soft_brute_v1"
        call.from_user.id = 12345
        call.id = "call_id_1"

        # Mock db.get_full_state to return None
        mock_db.get_full_state.return_value = None
        mock_db.get_user.return_value = {'uid': 12345, 'level': 10, 'biocoin': 1000}
        mock_pvp_service.get_deck.return_value = {'level': 1, 'slots': 1, 'config': {}}

        # Execute
        pvp.pvp_atk_sel_handler(call)

        # Verify
        mock_bot.answer_callback_query.assert_called_with("call_id_1", "❌ Сессия истекла.", show_alert=True)
        # Should also redirect to pvp_menu_handler, which we can check via get_user call inside pvp_menu_handler
        # But simpler to just check it didn't call set_state
        self.assertFalse(mock_db.set_state.called)

if __name__ == '__main__':
    unittest.main()
