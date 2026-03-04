import sys
from unittest.mock import MagicMock

# Mock dependencies
m_telebot = MagicMock()
m_types = MagicMock()
m_telebot.types = m_types
sys.modules['telebot'] = m_telebot
sys.modules['telebot.types'] = m_types

m_db = MagicMock()
sys.modules['database'] = m_db

m_cache = MagicMock()
# Mock get_cached_state to return something sensible
m_cache.get_cached_state.return_value = {}
sys.modules['cache_db'] = m_cache

m_config = MagicMock()
m_config.QUARANTINE_LEVEL = 5
m_config.ADMIN_ID = 999
sys.modules['config'] = m_config

import keyboards as kb

def test_eidos_room_menu():
    print("Testing eidos_room_menu...")
    # Reset mock to track new calls
    m_types.InlineKeyboardMarkup.return_value.add.reset_mock()

    markup = kb.eidos_room_menu()

    # Check that add was called with 4 arguments (the 4 buttons)
    # or multiple times totaling 4 buttons.
    add_mock = markup.add
    print(f"Markup add call count: {add_mock.call_count}")

    total_buttons = 0
    for call in add_mock.call_args_list:
        total_buttons += len(call[0])

    print(f"Total buttons added: {total_buttons}")
    if total_buttons == 4:
        print("✅ Correct number of buttons in Eidos Room menu.")
    else:
        print(f"❌ Unexpected number of buttons: {total_buttons}")
        sys.exit(1)

def test_main_menu():
    print("\nTesting main_menu...")
    u = {
        'uid': 123,
        'level': 15,
        'xp': 1000,
        'onboarding_stage': 2,
        'shadow_broker_expiry': 0,
        'encrypted_cache_unlock_time': 0,
        'is_admin': False
    }

    # Mock config LEVELS
    kb.LEVELS = {15: 1000, 16: 2000}

    # Mock cache_db.get_cached_state for specific keys
    def side_effect(key, func, ttl=None):
        if "inv_count" in key: return 0
        return {}
    m_cache.get_cached_state.side_effect = side_effect

    markup = kb.main_menu(u)
    print("✅ main_menu generated successfully")

if __name__ == "__main__":
    try:
        test_eidos_room_menu()
        test_main_menu()
        print("\nVerification script finished successfully.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nVerification FAILED: {e}")
        sys.exit(1)
