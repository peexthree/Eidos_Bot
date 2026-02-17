import unittest
import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Mock internal modules
import logic

class TestLogic(unittest.TestCase):
    def test_get_raid_entry_cost(self):
        # Basic check for now as function is simple
        self.assertEqual(logic.get_raid_entry_cost(123), 100)

    def test_draw_bar(self):
        bar = logic.draw_bar(50, 100, 10)
        self.assertEqual(bar, "█████░░░░░")

        bar_full = logic.draw_bar(100, 100, 10)
        self.assertEqual(bar_full, "██████████")

        bar_empty = logic.draw_bar(0, 100, 10)
        self.assertEqual(bar_empty, "░░░░░░░░░░")

if __name__ == '__main__':
    unittest.main()
