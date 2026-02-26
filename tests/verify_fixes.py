import unittest
from unittest.mock import MagicMock, patch
import sys
import random

# Mock modules BEFORE importing app modules
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['flask'] = MagicMock()

telebot = MagicMock()
sys.modules['telebot'] = telebot
sys.modules['telebot.apihelper'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()

# Import utils
from modules.services.utils import strip_html

class TestFixes(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<b>Test</b>"), "Test")
        self.assertEqual(strip_html("No tags"), "No tags")
        self.assertEqual(strip_html("<i>Italic</i> and <b>Bold</b>"), "Italic and Bold")
        self.assertEqual(strip_html(""), "")

    @patch('modules.services.shop.db')
    @patch('modules.services.shop.random')
    def test_gacha_odds(self, mock_random, mock_db):
        from modules.services.shop import process_gacha_purchase

        # Mock user
        mock_db.get_user.return_value = {'biocoin': 2000, 'total_spent': 0}
        mock_db.add_item.return_value = True

        # Test Equipment Drop (Roll < 0.05 but >= 0.01)
        mock_random.random.return_value = 0.03
        # Need to mock random.choice for equipment
        mock_random.choice.return_value = "void_cannon"

        # We need config.EQUIPMENT_DB to have void_cannon
        with patch.dict('config.EQUIPMENT_DB', {'void_cannon': {'name': 'Void Cannon', 'price': 50000}}):
             success, msg = process_gacha_purchase(123)
             self.assertTrue(success)
             self.assertIn("Void Cannon", msg)

    @patch('modules.services.raid.db')
    @patch('modules.services.raid.random')
    def test_cursed_chest_logic(self, mock_random, mock_db):
        from modules.services.raid import process_raid_step

        # Mock User
        mock_db.get_user.return_value = {'level': 10, 'xp': 1000, 'max_depth': 100}
        mock_db.get_user_stats.return_value = ({'atk':10, 'def':10, 'luck':10}, {'level':10, 'xp':1000, 'max_depth':100})

        # Mock Session with current_event_type = 'cursed_chest'
        # Note: We added current_event_type column usage
        session = {
            'uid': 123, 'depth': 10, 'signal': 100,
            'current_event_type': 'cursed_chest',
            'next_event_type': 'combat', # Should be ignored
            'buffer_xp': 0, 'buffer_coins': 0
        }

        # Mock DB Cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = session

        # Mock Item Counts (has key)
        def get_item_count_side_effect(uid, item_id, cursor=None):
            if item_id == 'abyssal_key': return 1
            return 0
        mock_db.get_item_count.side_effect = get_item_count_side_effect
        mock_db.use_item.return_value = True

        # Mock Drops (Red)
        mock_random.random.return_value = 0.1 # < 0.5 -> Red
        mock_random.choice.return_value = 'credit_slicer'

        # Run
        with patch.dict('config.ITEMS_INFO', {'credit_slicer': {'name': 'Credit Slicer'}}):
             res, txt, extra, u, etype, cost = process_raid_step(123, answer='open_chest')

             self.assertTrue(res)
             # Alert text is constructed in raid.py
             # We expect "🔴 ПРОКЛЯТЫЙ ЛУТ" in alert.
             # extra['alert']
             self.assertIn("ПРОКЛЯТЫЙ ЛУТ", extra['alert'])
             self.assertIn("Credit Slicer", extra['alert'])

             # Verify it used current_event_type logic, not next_event_type (combat)
             # If it used combat (is_cursed=False), it would call get_chest_drops -> random normal loot
             # Since we mocked random < 0.5 inside cursed block, if we see "ПРОКЛЯТЫЙ ЛУТ", it worked.

if __name__ == '__main__':
    unittest.main()
