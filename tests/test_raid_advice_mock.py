import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock telebot before importing logic/bot
sys.modules['telebot'] = MagicMock()

import logic
import database

class TestRaidAdvice(unittest.TestCase):

    def test_advice_appears(self):
        with patch('logic.db.db_session') as mock_db_session, \
             patch('logic.db.get_user') as mock_get_user, \
             patch('logic.db.get_item_count') as mock_get_item_count, \
             patch('logic.db.get_random_villain') as mock_get_villain, \
             patch('logic.db.get_random_raid_advice') as mock_get_advice, \
             patch('logic.generate_random_event_type') as mock_gen_event:

            # Setup mocks
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            # Mock session context manager
            mock_db_session.return_value.__enter__.return_value = mock_conn

            # Mock cursor context manager.
            # logic.py calls conn.cursor(cursor_factory=...).
            # We must ensure it returns the context manager that yields our mock_cursor.
            cursor_ctx = MagicMock()
            cursor_ctx.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = cursor_ctx

            # Mock user
            mock_get_user.return_value = {
                'uid': 123, 'xp': 1000, 'biocoin': 500, 'max_depth': 10,
                'level': 5, 'path': 'general', 'raid_count_today': 0,
                'last_raid_date': '2023-01-01'
            }

            # Mock advice
            mock_get_advice.return_value = "Stay frosty."

            # Mock event generation
            mock_gen_event.return_value = 'random'

            mock_cursor.fetchone.side_effect = [
                # 1. Session
                {
                    'depth': 10, 'signal': 100, 'start_time': 1234567890,
                    'current_enemy_id': None, 'next_event_type': 'random',
                    'buffer_xp': 0, 'buffer_coins': 0, 'buffer_items': ''
                },
                # 2. Event Content
                {'text': "You see a wall.", 'type': 'neutral', 'val': 0},
                # 3. Buffer XP/Coins for UI
                {'buffer_xp': 10, 'buffer_coins': 5},
                # 4. Compass check
                {'quantity': 0},
                # 5. Inventory for HUD (get_inventory called by generate_hud)
                # get_inventory calls fetchall? No, it calls fetchall.
                # But fetchone side_effect is for fetchone calls.
                # get_inventory calls fetchall.
            ]

            # Mock fetchall for inventory
            mock_cursor.fetchall.return_value = []

            # Mock random
            with patch('random.random', return_value=0.1):
                res, txt, riddle, u, etype, cost = logic.process_raid_step(123)

                self.assertTrue(res)
                self.assertIn("🧩 <i>Совет: Stay frosty.</i>", txt)
                mock_get_advice.assert_called_with(1, cursor=mock_cursor)

    def test_advice_level_logic(self):
        with patch('logic.db.db_session') as mock_db_session, \
             patch('logic.db.get_user') as mock_get_user, \
             patch('logic.db.get_item_count') as mock_get_item_count, \
             patch('logic.db.get_random_villain') as mock_get_villain, \
             patch('logic.db.get_random_raid_advice') as mock_get_advice, \
             patch('logic.generate_random_event_type') as mock_gen_event:

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db_session.return_value.__enter__.return_value = mock_conn
            cursor_ctx = MagicMock()
            cursor_ctx.__enter__.return_value = mock_cursor
            mock_conn.cursor.return_value = cursor_ctx

            mock_get_user.return_value = {'uid': 123, 'xp': 1000, 'biocoin': 500, 'max_depth': 100, 'level': 5, 'path': 'general'}

            mock_gen_event.return_value = 'random'
            mock_get_advice.return_value = "Advice"

            mock_cursor.fetchall.return_value = []

            def run_step(depth):
                # Reset side_effect for next run
                mock_cursor.fetchone.side_effect = [
                    {'depth': depth, 'signal': 100, 'start_time': 0, 'next_event_type': 'random', 'buffer_xp': 0, 'buffer_coins': 0, 'buffer_items': ''},
                    {'text': "Event", 'type': 'neutral', 'val': 0},
                    {'buffer_xp': 0, 'buffer_coins': 0},
                    {'quantity': 0}
                ]
                with patch('random.random', return_value=0.1):
                    logic.process_raid_step(123)

            # Test Level 1
            run_step(10)
            mock_get_advice.assert_called_with(1, cursor=mock_cursor)

            # Test Level 2
            run_step(60)
            mock_get_advice.assert_called_with(2, cursor=mock_cursor)

            # Test Level 3
            run_step(120)
            mock_get_advice.assert_called_with(3, cursor=mock_cursor)

if __name__ == '__main__':
    unittest.main()
