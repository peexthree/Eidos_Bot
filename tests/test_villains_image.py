import unittest
from unittest.mock import MagicMock, patch, call
import sys
import copy

# Mock modules before importing logic/database
sys.modules['psycopg2'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

# Re-import to ensure mocks are used if already imported
if 'database' in sys.modules: del sys.modules['database']
if 'logic' in sys.modules: del sys.modules['logic']

import database
import logic

class TestVillainsImage(unittest.TestCase):
    def test_init_db_adds_image_column(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        with patch('database.psycopg2.connect', return_value=mock_conn):
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            # Mock fetchone for constraint check
            mock_cursor.fetchone.return_value = [1]

            database.init_db()

            # Check if ALTER TABLE was called
            calls = mock_cursor.execute.call_args_list
            alter_call_found = False
            for c in calls:
                query = c[0][0]
                if "ALTER TABLE villains ADD COLUMN IF NOT EXISTS image TEXT" in query:
                    alter_call_found = True
                    break

            self.assertTrue(alter_call_found, "ALTER TABLE villains ADD COLUMN image not found in init_db calls")

    def test_populate_villains_inserts_image(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        with patch('database.db_session') as mock_session:
            mock_session.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            database.populate_villains()

            # Check if INSERT statement includes image
            calls = mock_cursor.execute.call_args_list
            insert_call_found = False
            for c in calls:
                query = c[0][0]
                if "INSERT INTO villains" in query and "image" in query:
                    # Check params
                    params = c[0][1]
                    if 'image' in params:
                        insert_call_found = True
                        break

            self.assertTrue(insert_call_found, "INSERT INTO villains with image column not found")

    @patch('logic.db')
    @patch('random.random')
    @patch('logic.get_user_stats')
    @patch('logic.get_biome_modifiers')
    @patch('logic.generate_random_event_type')
    def test_process_raid_step_returns_image(self, mock_gen_event, mock_biome, mock_get_stats, mock_random, mock_db):
        mock_user = {
            'uid': 123,
            'xp': 1000,
            'biocoin': 500,
            'level': 5,
            'max_depth': 0,
            'path': 'general',
            'last_raid_date': '2023-01-01',
            'raid_count_today': 0
        }
        mock_stats = {'atk': 10, 'def': 10, 'luck': 10}

        mock_villain = {
            "id": 1,
            "name": "TestVillain",
            "level": 4,
            "hp": 60,
            "atk": 18,
            "def": 5,
            "xp_reward": 90,
            "coin_reward": 60,
            "description": "Desc",
            "image": "test_file_id"
        }

        mock_random.return_value = 0.5
        mock_get_stats.return_value = (mock_stats, mock_user)
        mock_biome.return_value = {"name": "TestBiome", "mult": 1.0}
        mock_gen_event.return_value = 'combat' # Ensure next event is combat

        # Mock DB session
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

        # Side effects for fetchone:
        # 1. First call check for session (returns session)
        # 2. Inside process_raid_step, it might check other things.
        # Logic:
        # - fetch session (success)
        # - check glitch (random=0.5 > 0.05, so no)
        # - check current_enemy_id (None)
        # - check answer (None)
        # - check cost (ok)
        # - generate event: combat
        # - get random villain

        mock_cursor.fetchone.side_effect = [
            session_data, # Existing session
            # Logic then continues...
        ]

        mock_db.get_random_villain.return_value = copy.deepcopy(mock_villain)
        mock_db.get_inventory.return_value = []
        mock_db.get_raid_entry_cost.return_value = 100

        # Call logic
        success, interface, extra, _, _, _ = logic.process_raid_step(123)

        self.assertTrue(success)
        self.assertIsNotNone(extra)
        self.assertIn('image', extra)
        self.assertEqual(extra['image'], 'test_file_id')

        # Also check caption text format
        self.assertIn("👹 УГРОЗА ОБНАРУЖЕНА: <b>TestVillain</b>", interface)
        self.assertIn("<i>Desc</i>", interface)
        self.assertIn("❤️ HP: 60 / 60", interface)

if __name__ == '__main__':
    unittest.main()
