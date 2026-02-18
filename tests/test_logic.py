import unittest
import sys
from unittest.mock import MagicMock, patch
from datetime import date

# Mock database dependencies to avoid connection errors
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Mock database module (logic.py imports 'database as db')
# We need to do this before importing logic
db_mock = MagicMock()
sys.modules['database'] = db_mock

# Now import logic
import logic

class TestLogic(unittest.TestCase):

    @patch('logic.db.get_user')
    def test_get_raid_entry_cost(self, mock_get_user):
        # Case 1: First time today
        mock_get_user.return_value = {'raid_count_today': 0, 'last_raid_date': date.today()}
        # Assuming RAID_ENTRY_COSTS = [100, 200, 400]
        self.assertEqual(logic.get_raid_entry_cost(1), 100)

        # Case 2: Second time
        mock_get_user.return_value = {'raid_count_today': 1, 'last_raid_date': date.today()}
        self.assertEqual(logic.get_raid_entry_cost(1), 200)

        # Case 3: Third time (Max)
        mock_get_user.return_value = {'raid_count_today': 2, 'last_raid_date': date.today()}
        self.assertEqual(logic.get_raid_entry_cost(1), 400)

        # Case 4: Different date (should reset logic-wise, function returns base)
        mock_get_user.return_value = {'raid_count_today': 5, 'last_raid_date': date(2020, 1, 1)}
        self.assertEqual(logic.get_raid_entry_cost(1), 100)

    @patch('logic.db.get_inventory')
    @patch('logic.db.get_equipped_items')
    @patch('logic.db.get_user')
    def test_format_inventory(self, mock_user, mock_eq, mock_inv):
        mock_inv.return_value = [{'item_id': 'battery', 'quantity': 1}]
        mock_eq.return_value = {'weapon': 'rusty_knife'}
        mock_user.return_value = {'uid': 1}

        txt = logic.format_inventory(1)
        self.assertIn("РЮКЗАК", txt)
        self.assertIn("БАТАРЕЯ", txt) # Assuming ITEMS_INFO fallback uses id if name missing or check real name
        self.assertIn("НОЖ", txt) # Assuming EQUIPMENT_DB fallback

    @patch('logic.db.get_user')
    def test_get_profile_stats(self, mock_get_user):
        mock_get_user.return_value = {
            'level': 2,
            'streak': 3,
            'max_depth': 50,
            'ref_profit_xp': 100,
            'ref_profit_coins': 50,
            'raid_count_today': 1
        }
        stats = logic.get_profile_stats(1)
        self.assertEqual(stats['streak'], 3)
        self.assertEqual(stats['max_depth'], 50)
        # Income: (2 * 1000) + (3 * 50) + 150 = 2000 + 150 + 150 = 2300
        self.assertEqual(stats['income_total'], 2300)

    def test_draw_bar(self):
        bar = logic.draw_bar(50, 100, 10)
        self.assertEqual(bar, "█████░░░░░")

    @patch('logic.db.get_user')
    @patch('logic.db.update_user')
    def test_check_level_up(self, mock_update, mock_get_user):
        # Case 1: No level up (xp < target)
        # Level 1 target is 100.
        mock_get_user.return_value = {'level': 1, 'xp': 50}
        new_level, msg = logic.check_level_up(1)
        self.assertIsNone(new_level)
        mock_update.assert_not_called()

        # Case 2: Level up (xp >= target)
        mock_get_user.return_value = {'level': 1, 'xp': 150}
        new_level, msg = logic.check_level_up(1)
        self.assertEqual(new_level, 2)
        mock_update.assert_called_with(1, level=2)
        self.assertIn("LVL 2", msg)

        # Case 3: Multiple levels (xp >= target for 2 levels)
        # Level 1 -> 2 (100 xp needed)
        # Level 2 -> 3 (500 xp needed)
        mock_get_user.return_value = {'level': 1, 'xp': 600}
        new_level, msg = logic.check_level_up(1)
        self.assertEqual(new_level, 3)
        mock_update.assert_called_with(1, level=3)

if __name__ == '__main__':
    unittest.main()
