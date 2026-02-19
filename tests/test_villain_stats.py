import unittest
from unittest.mock import MagicMock, patch
import sys
import copy

# Mock modules before importing logic/database
sys.modules['psycopg2'] = MagicMock()
sys.modules['telebot'] = MagicMock()
# We also need to mock extras for psycopg2
sys.modules['psycopg2.extras'] = MagicMock()

import logic

class TestVillainStatsFix(unittest.TestCase):
    def setUp(self):
        self.mock_user = {
            'uid': 123,
            'xp': 1000,
            'biocoin': 500,
            'level': 30, # High level
            'max_depth': 0,
            'path': 'general',
            'last_raid_date': '2023-01-01',
            'raid_count_today': 0
        }

        self.mock_stats = {'atk': 95, 'def': 65, 'luck': 10} # High stats

        self.mock_villain = {
            "id": 1,
            "name": "Ассасин Даркнета",
            "level": 4,
            "hp": 60,
            "atk": 18,
            "def": 5,
            "xp_reward": 90,
            "coin_reward": 60,
            "description": "Скрытный убийца."
        }

    @patch('logic.db')
    @patch('random.random')
    @patch('logic.get_user_stats')
    @patch('logic.get_biome_modifiers')
    @patch('logic.generate_random_event_type')
    def test_process_raid_step_no_scaling(self, mock_gen_event, mock_biome, mock_get_stats, mock_random, mock_db):
        # Setup mocks
        mock_random.return_value = 0.5
        mock_get_stats.return_value = (self.mock_stats, self.mock_user)
        mock_biome.return_value = {"name": "TestBiome", "mult": 1.0}
        mock_gen_event.return_value = 'combat'

        # Mock DB session and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock fetchone for raid session
        session_data = {
            'uid': 123,
            'depth': 0,
            'signal': 100,
            'start_time': 1234567890,
            'kills': 0,
            'riddles_solved': 0,
            'next_event_type': 'combat',
            'buffer_items': '',
            'buffer_xp': 0,
            'buffer_coins': 0,
            'current_enemy_id': None
        }

        mock_cursor.fetchone.side_effect = [
            None,
            session_data,
            {'text': 'Some content', 'type': 'neutral', 'val': 0}
        ]

        # Mock get_random_villain
        mock_db.get_random_villain.return_value = copy.deepcopy(self.mock_villain)

        # Mock other DB calls
        mock_db.get_inventory.return_value = []
        mock_db.get_raid_entry_cost.return_value = 100

        # Execute
        success, interface, _, _, _, _ = logic.process_raid_step(123)

        # Assertions
        self.assertTrue(success)

        # Check HP is exactly 60/60
        self.assertIn("60/60", interface)

        # Check Attack and Defense are displayed
        self.assertIn(f"👹 Враг ATK: {self.mock_villain['atk']}", interface)
        self.assertIn(f"🛡 DEF: {self.mock_villain['def']}", interface)

        # Verify get_random_villain was called
        mock_db.get_random_villain.assert_called()

        # Verify UPDATE raid_sessions set current_enemy_hp to 60 (not scaled)
        calls = mock_cursor.execute.call_args_list
        found_update = False
        for call in calls:
            args, _ = call
            query = args[0]
            if "UPDATE raid_sessions SET current_enemy_id=%s, current_enemy_hp=%s" in query:
                found_update = True
                params = args[1]
                self.assertEqual(params[1], 60) # HP should be 60

        self.assertTrue(found_update, "Could not find UPDATE query for enemy HP")

if __name__ == '__main__':
    unittest.main()
