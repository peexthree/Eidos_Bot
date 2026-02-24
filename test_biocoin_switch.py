import sys
from unittest.mock import MagicMock

# Mocks
mock_db = MagicMock()
sys.modules['database'] = mock_db

mock_config = MagicMock()
mock_config.SOFTWARE_DB = {
    "soft_brute_v1": {"name": "Brute", "type": "atk", "power": 1, "cost": 100, "durability": 10, "icon": "R"},
}
mock_config.DECK_UPGRADES = {1: {'slots': 3}}
mock_config.PVP_CONSTANTS = {
    "SHIELD_DURATION": 3600,
    "PROTECTION_LIMIT": 500,
    "HACK_REWARD": 25,
    "STEAL_PERCENT": 0.1,
    "MAX_STEAL": 15
}
mock_config.QUARANTINE_LEVEL = 5
sys.modules['config'] = mock_config

mock_user_service = MagicMock()
mock_user_service.get_user_stats.return_value = ({'def': 10}, None)
sys.modules['modules.services.user'] = mock_user_service

# Import
from modules.services import pvp

def test_buy_software_biocoin():
    print("Testing Buy Software with BioCoins...")

    # User has 200 BC
    mock_db.get_user.return_value = {'biocoin': 200}

    # Mock context manager
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Simulate DB Update success (rowcount > 0)
    mock_cursor.rowcount = 1

    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_db.db_session.return_value.__enter__.return_value = mock_conn

    success, msg = pvp.buy_software(123, "soft_brute_v1")
    print(f"Result: {success}, {msg}")

    assert success == True
    # Verify we updated 'biocoin' and not 'data_balance'
    args = mock_cursor.execute.call_args[0]
    sql = args[0]
    print(f"SQL Executed: {sql}")
    assert "UPDATE players SET biocoin =" in sql

if __name__ == "__main__":
    try:
        test_buy_software_biocoin()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
