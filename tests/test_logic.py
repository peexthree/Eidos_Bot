import unittest
import sys
from unittest.mock import MagicMock

# Mock modules that are not available in the environment
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['pyTelegramBotAPI'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Mock database module which depends on psycopg2
sys.modules['database'] = MagicMock()

from logic import get_path_multiplier

class TestGetPathMultiplier(unittest.TestCase):
    def test_money_path(self):
        user = {'path': 'money'}
        expected = {"xp_mult": 1.2, "cd_mult": 1.0}
        self.assertEqual(get_path_multiplier(user), expected)

    def test_tech_path(self):
        user = {'path': 'tech'}
        expected = {"xp_mult": 1.0, "cd_mult": 0.9}
        self.assertEqual(get_path_multiplier(user), expected)

    def test_default_path(self):
        user = {'path': 'general'}
        expected = {"xp_mult": 1.0, "cd_mult": 1.0}
        self.assertEqual(get_path_multiplier(user), expected)

    def test_unknown_path(self):
        user = {'path': 'unknown'}
        expected = {"xp_mult": 1.0, "cd_mult": 1.0}
        self.assertEqual(get_path_multiplier(user), expected)

if __name__ == '__main__':
    unittest.main()
