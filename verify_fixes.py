import sys
from unittest.mock import MagicMock, patch

# Mock EVERYTHING that menu.py imports
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['cache_db'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.texts'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()
sys.modules['modules.services.glitch_system'] = MagicMock()

import html
# Mock database
mock_db = MagicMock()
sys.modules['database'] = mock_db

# Mock config
mock_config = MagicMock()
mock_config.MENU_IMAGES = {"leaderboard": "http://example.com/lb.jpg"}
sys.modules['config'] = mock_config

# Import handler after mocks
from modules.handlers.menu import format_leaderboard_text, find_user_dossier_init_handler, process_dossier_search

def test_leaderboard_nicknames():
    leaders = [{
        'uid': 123,
        'first_name': 'TestUser',
        'username': 'test_user',
        'xp': 1000,
        'level': 5,
        'max_depth': 100,
        'biocoin': 500,
        'total_spent': 0,
        'path': 'tech'
    }]
    u = {'xp': 100, 'level': 1}

    with patch('modules.handlers.menu.get_user_display_name', side_effect=lambda uid, name, custom_data=None: name):
        txt = format_leaderboard_text(leaders, 1, u, 'xp')
        print(f"Leaderboard text snippet: {txt[:200]}")
        assert "<code>@test_user</code>" in txt
        print("✅ Leaderboard nickname wrapping verified.")

def test_dossier_init_uses_menu_update():
    call = MagicMock()
    call.from_user.id = 123
    mock_db.get_user.return_value = {'biocoin': 200}

    with patch('modules.handlers.menu.menu_update') as mock_menu_update:
        find_user_dossier_init_handler(call)
        mock_menu_update.assert_called_once()
        print("✅ find_user_dossier_init_handler uses menu_update verified.")

def test_dossier_search_query():
    m = MagicMock()
    m.from_user.id = 123
    m.text = "@target_user"
    mock_db.get_user.return_value = {'biocoin': 200}

    mock_conn = MagicMock()
    mock_db.get_connection.return_value = mock_conn
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_cur.fetchone.return_value = None # User not found is fine for query check

    try:
        process_dossier_search(m)
    except Exception as e:
        # It might fail later due to threading or other things, but we care about the query
        pass

    # Check if any call to execute used "FROM players"
    found = False
    for call_obj in mock_cur.execute.call_args_list:
        query = call_obj[0][0]
        if "FROM players" in query:
            found = True
            break
    assert found
    print("✅ process_dossier_search uses 'players' table verified.")

if __name__ == "__main__":
    try:
        test_leaderboard_nicknames()
        test_dossier_init_uses_menu_update()
        test_dossier_search_query()
        print("\nAll targeted verifications passed!")
    except Exception as e:
        print(f"\nVerification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
