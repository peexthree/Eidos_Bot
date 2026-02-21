import sys
from unittest.mock import MagicMock

# Mock psycopg2 before importing database
mock_psycopg2 = MagicMock()
sys.modules['psycopg2'] = mock_psycopg2
sys.modules['psycopg2.extras'] = MagicMock()

import unittest
from unittest.mock import patch
from modules.services import user as logic
import config

class TestLogic(unittest.TestCase):
    @patch('modules.services.user.db')
    def test_check_achievements(self, mock_db):
        # Setup
        uid = 123
        mock_db.get_user.return_value = {'level': 3, 'xp': 1000, 'biocoin': 2000, 'streak': 5, 'kills': 1, 'max_depth': 10}
        mock_db.get_user_achievements.return_value = [] # No achievements yet
        mock_db.grant_achievement.return_value = True

        # Act
        new_achs = logic.check_achievements(uid)

        # Assert
        ach_names = [a['name'] for a in new_achs]
        print("Triggered Achievements:", ach_names)

        self.assertIn("🐣 ВЫХОД ИЗ КОКОНА", ach_names) # lvl_2
        self.assertIn("🥚 ОПЕРАТОР", ach_names)       # lvl_3
        self.assertIn("💸 ПЕРВЫЙ КУШ", ach_names)     # money_1k
        self.assertIn("🤑 БОГАЧ 1000", ach_names)     # rich_1000
        self.assertIn("🩸 ПЕРВАЯ КРОВЬ", ach_names)   # first_blood
        self.assertIn("👣 ПЕРВЫЕ ШАГИ", ach_names)    # first_steps

    @patch('modules.services.user.db')
    def test_check_achievements_already_owned(self, mock_db):
        uid = 123
        mock_db.get_user.return_value = {'level': 5}
        mock_db.get_user_achievements.return_value = ['lvl_2', 'lvl_3', 'lvl_5']

        new_achs = logic.check_achievements(uid)
        self.assertEqual(len(new_achs), 0)

if __name__ == '__main__':
    unittest.main()
