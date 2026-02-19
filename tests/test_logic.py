import unittest
import sys
from unittest.mock import MagicMock, patch
from datetime import date

# Mock database dependencies to avoid connection errors
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Save original database module if it exists
original_db = sys.modules.get('database')

# Mock database module (logic.py imports 'database as db')
# We need to do this before importing logic
db_mock = MagicMock()
sys.modules['database'] = db_mock

# Now import logic
import logic

# Restore original database module to avoid polluting other tests
if original_db:
    sys.modules['database'] = original_db
else:
    del sys.modules['database']

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
        self.assertIn("ЭНЕРГО-ЯЧЕЙКА", txt) # Assuming ITEMS_INFO fallback uses id if name missing or check real name
        self.assertIn("ТЕСАК", txt) # Assuming EQUIPMENT_DB fallback

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
        # 1. Normal Cases
        self.assertEqual(logic.draw_bar(50, 100, 10), "█████░░░░░")
        self.assertEqual(logic.draw_bar(0, 100, 10), "░░░░░░░░░░")
        self.assertEqual(logic.draw_bar(100, 100, 10), "██████████")

        # 2. Custom Length
        self.assertEqual(logic.draw_bar(50, 100, 4), "██░░")
        self.assertEqual(logic.draw_bar(25, 100, 4), "█░░░")

        # 3. Boundary / Overflow / Underflow
        self.assertEqual(logic.draw_bar(150, 100, 10), "██████████")  # Cap at max
        self.assertEqual(logic.draw_bar(-10, 100, 10), "░░░░░░░░░░")  # Cap at min

        # 4. Zero or Negative Total
        self.assertEqual(logic.draw_bar(10, 0, 10), "░░░░░░░░░░")
        self.assertEqual(logic.draw_bar(10, -50, 10), "░░░░░░░░░░")

        # 5. Floating Point
        self.assertEqual(logic.draw_bar(50.5, 100, 10), "█████░░░░░")

        # 6. Rounding Checks
        # 33% of 10 is 3.3 -> 3 blocks
        self.assertEqual(logic.draw_bar(33, 100, 10), "███░░░░░░░")
        # 99% of 10 is 9.9 -> 9 blocks (int truncation)
        self.assertEqual(logic.draw_bar(99, 100, 10), "█████████░")

        # 7. Small totals
        self.assertEqual(logic.draw_bar(1, 1, 5), "█████")
        self.assertEqual(logic.draw_bar(0, 1, 5), "░░░░░")

    @patch('logic.db.get_user')
    @patch('logic.db.update_user')
    def test_check_level_up(self, mock_update, mock_get_user):
        # Case 0: Level 0 -> 1 (100 XP needed)
        mock_get_user.return_value = {'level': 0, 'xp': 100}
        new_level, msg = logic.check_level_up(1)
        self.assertEqual(new_level, 1)
        mock_update.assert_called_with(1, level=1)

        # Case 1: No level up (xp < target)
        # Level 1 target is 500.
        mock_get_user.return_value = {'level': 1, 'xp': 450}
        new_level, msg = logic.check_level_up(1)
        self.assertIsNone(new_level)

        # Case 2: Level up (xp >= target)
        # Level 1 -> 2 (500 XP needed)
        mock_get_user.return_value = {'level': 1, 'xp': 550}
        new_level, msg = logic.check_level_up(1)
        self.assertEqual(new_level, 2)
        mock_update.assert_called_with(1, level=2)
        self.assertIn("LVL 2", msg)

        # Case 3: Multiple levels (xp >= target for 2 levels)
        # Level 1 -> 2 (500 xp needed)
        # Level 2 -> 3 (1500 xp needed)
        # So if we have 1600 XP, we skip from 1 to 3
        mock_get_user.return_value = {'level': 1, 'xp': 1600}
        new_level, msg = logic.check_level_up(1)
        self.assertEqual(new_level, 3)
        mock_update.assert_called_with(1, level=3)

if __name__ == '__main__':
    unittest.main()
