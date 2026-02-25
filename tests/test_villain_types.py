import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock database module before importing raid
sys.modules['database'] = MagicMock()
import database

# Mock config
sys.modules['config'] = MagicMock()
from config import ITEMS_INFO

from modules.services import raid

class TestVillainTypes(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        database.reset_mock()

        self.user = {'uid': 123, 'level': 10, 'xp': 1000, 'path': 'general', 'max_depth': 0}

        # Patch raid's imported get_user_stats
        raid.get_user_stats = MagicMock(return_value=({'atk': 10, 'def': 5, 'luck': 0}, self.user))

        database.get_equipped_items = MagicMock(return_value={})
        database.get_item_count = MagicMock(return_value=0)
        database.get_biome_modifiers = MagicMock(return_value={'name': 'Test Biome', 'mult': 1.0})

        # Patch utils imports if needed
        # raid.py imports get_biome_modifiers from utils
        raid.get_biome_modifiers = MagicMock(return_value={'name': 'Test Biome', 'mult': 1.0})

        # Mock session context manager
        self.mock_cursor = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_conn.cursor.return_value.__enter__.return_value = self.mock_cursor
        database.db_session.return_value.__enter__.return_value = self.mock_conn

    def test_villain_stats_as_strings(self):
        uid = 123

        session_data = {
            'uid': uid,
            'depth': 10,
            'signal': 100,
            'current_enemy_id': 1,
            'current_enemy_hp': 50,
            'next_event_type': 'combat',
            'event_streak': 0,
            'buffer_items': '',
            'buffer_xp': 0,
            'buffer_coins': 0
        }

        # 1. Session, 2. Scanner (combat block)
        self.mock_cursor.fetchone.side_effect = [
            session_data,
            {'quantity': 1, 'durability': 10}
        ]

        villain_data = {
            'id': 1,
            'name': 'Glitchy Mob',
            'hp': '100',  # String!
            'atk': '15',  # String!
            'def': '5',   # String!
            'image': 'test.jpg',
            'level': 5,   # Added level
            'xp_reward': 10,
            'coin_reward': 10,
            'description': 'A glitchy mob.'
        }
        database.get_villain_by_id.return_value = villain_data

        try:
            success, interface, extra, u, etype, cost = raid.process_raid_step(uid)
            self.assertTrue(success, "Function returned False")
            self.assertEqual(etype, 'combat')
        except TypeError as e:
            self.fail(f"process_raid_step raised TypeError with string stats: {e}")

if __name__ == '__main__':
    unittest.main()
