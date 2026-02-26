import unittest
from unittest.mock import MagicMock
import sys

# Mock config
sys.modules['config'] = MagicMock()
from config import LEVELS, PRICES

# Mock database
sys.modules['database'] = MagicMock()

# Mock telebot
# We need to ensure 'from telebot import types' gets our mock
mock_telebot = MagicMock()
sys.modules['telebot'] = mock_telebot
# types needs to be an attribute of telebot AND a module?
# Usually 'from package import module' looks in sys.modules first.
mock_types = MagicMock()
sys.modules['telebot.types'] = mock_types
# Also set attribute just in case
mock_telebot.types = mock_types

import keyboards as kb

class TestPvpCrash(unittest.TestCase):
    def test_pvp_vendetta_menu_crash(self):
        print("\n--- TEST: PVP VENDETTA MENU NULL ID ---")
        print(f"kb.types: {kb.types}")
        print(f"mock_types: {mock_types}")

        attackers = [
            {'id': None, 'username': 'Ghost', 'level': 1, 'timestamp': 100000}
        ]

        kb.pvp_vendetta_menu(attackers)

        found_buggy_callback = False
        # Check call_args_list on the object that kb.types.InlineKeyboardButton points to
        print(f"Calls: {kb.types.InlineKeyboardButton.call_args_list}")

        for call in kb.types.InlineKeyboardButton.call_args_list:
            kwargs = call[1]
            if "callback_data" in kwargs:
                if kwargs["callback_data"] == "pvp_revenge_confirm_None":
                    found_buggy_callback = True

        if found_buggy_callback:
            print("✅ REPRODUCED: Found 'pvp_revenge_confirm_None' button.")
        else:
            print("❓ NOT REPRODUCED")

if __name__ == '__main__':
    unittest.main()
