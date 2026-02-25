import sys
from unittest.mock import MagicMock, patch
import unittest

# Mock dependencies before importing modules
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Import the function to test
# We need to import it AFTER mocking sys.modules because it imports database/config which import external libs
from modules.services.raid import get_raid_entry_cost

class TestRaidEntryCost(unittest.TestCase):

    @patch('modules.services.raid.db.get_user')
    def test_cost_calculation_level_1(self, mock_get_user):
        """Test cost calculation for a level 1 user."""
        mock_get_user.return_value = {'level': 1, 'uid': 123}
        # 100 + (1 * 150) = 250
        cost = get_raid_entry_cost(123)
        self.assertEqual(cost, 250)

    @patch('modules.services.raid.db.get_user')
    def test_cost_calculation_level_10(self, mock_get_user):
        """Test cost calculation for a level 10 user."""
        mock_get_user.return_value = {'level': 10, 'uid': 123}
        # 100 + (10 * 150) = 1600
        cost = get_raid_entry_cost(123)
        self.assertEqual(cost, 1600)

    @patch('modules.services.raid.db.get_user')
    def test_cost_calculation_no_level(self, mock_get_user):
        """Test cost calculation for a user with no level (default 1)."""
        # User dict must not be empty to pass 'if not u' check
        mock_get_user.return_value = {'uid': 123}
        # 'level' missing, defaults to 1 -> 100 + (1 * 150) = 250
        cost = get_raid_entry_cost(123)
        self.assertEqual(cost, 250)

    @patch('modules.services.raid.db.get_user')
    def test_user_not_found(self, mock_get_user):
        """Test cost calculation when user is not found."""
        mock_get_user.return_value = None
        # Should return 100
        cost = get_raid_entry_cost(123)
        self.assertEqual(cost, 100)

if __name__ == '__main__':
    unittest.main()
