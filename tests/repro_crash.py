
import sys
import os
import unittest
from unittest.mock import MagicMock

# 1. Mock External Packages in sys.modules
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# 2. Mock 'config' module before importing application code
sys.modules['config'] = MagicMock()
import config
# Setup config values needed for tests
config.SOFTWARE_DB = {
    "soft_brute_v1": {"name": "Brute", "type": "atk", "power": 1, "cost": 100, "icon": "🔴", "desc": "desc"},
    "soft_wall_v1": {"name": "Wall", "type": "def", "power": 1, "cost": 100, "icon": "🔵", "desc": "desc"}
}
config.PVP_HARDWARE = ['firewall']
config.ITEMS_INFO = {
    "firewall": {"name": "Firewall", "desc": "desc"}
}
config.PRICES = {"firewall": 1000}
config.DECK_UPGRADES = {1: {"slots": 1, "cost": 0}}
config.QUARANTINE_LEVEL = 5
config.MENU_IMAGES = {"pvp_menu": "url"}

# 3. Mock 'database' module (PARTIALLY)
# We want to verify that db functions accept 'cursor' kwarg.
# But we can't import real database.py easily without real psycopg2.
# So we mock the module, BUT we set up side_effects that check kwargs.

sys.modules['database'] = MagicMock()
import database as db

# Verification Logic for mocked DB functions
def mock_use_item(uid, item_id, qty=1, cursor=None):
    if cursor:
        print(f"VERIFIED: use_item called with cursor={cursor}")
        return True
    return True

def mock_get_item_count(uid, item_id, cursor=None):
    if cursor:
        print(f"VERIFIED: get_item_count called with cursor={cursor}")
    return 1

# Assign side effects
db.use_item.side_effect = mock_use_item
db.get_item_count.side_effect = mock_get_item_count

# 4. Import the handler under test
from modules.handlers import pvp as pvp_handler

class TestPvPCrash(unittest.TestCase):

    def setUp(self):
        self.uid = 123456
        self.call = MagicMock()
        self.call.from_user.id = self.uid
        self.call.id = "query_id"
        self.call.message.chat.id = 111
        self.call.message.message_id = 222
        self.call.data = ""

    def test_dismantle_safe(self):
        print("\nTesting safe dismantle with cursor verification...")
        self.call.data = "pvp_dismantle_soft_brute_v1"

        # Setup DB Mocks
        db.get_user.return_value = {
            'uid': self.uid, 'level': 10, 'biocoin': 1000,
            'deck_level': 1, 'deck_config': '{"1": null}',
            'active_hardware': '{}'
        }
        db.get_inventory.return_value = [
            {'item_id': 'soft_brute_v1', 'quantity': 1, 'durability': 10, 'id': 1}
        ]

        # Mock Context Manager for db_session
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        try:
            pvp_handler.pvp_inventory_handler(self.call)
        except Exception as e:
            self.fail(f"Safe dismantle crashed: {e}")

if __name__ == '__main__':
    unittest.main()
