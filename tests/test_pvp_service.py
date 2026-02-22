import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock modules before importing pvp
mock_db = MagicMock()
mock_config = MagicMock()
sys.modules['database'] = mock_db
sys.modules['config'] = mock_config

from modules.services import pvp

class TestPVPService(unittest.TestCase):
    def setUp(self):
        mock_db.reset_mock()
        mock_config.reset_mock()

        # Setup default config
        mock_config.PVP_STEALTH_COST = 150

    def test_find_target_success(self):
        mock_db.get_random_user_for_hack.return_value = 200
        mock_db.get_user.side_effect = lambda uid: {
            'uid': uid, 'level': 5, 'biocoin': 1000,
            'is_quarantined': False, 'username': 'Target', 'path': 'tech'
        } if uid == 200 else {'uid': 100, 'level': 10, 'path': 'mind'}

        mock_db.check_pvp_cooldown.return_value = False

        # Mock get_user_stats for threat calculation
        with patch('modules.services.pvp.get_user_stats') as mock_stats:
            mock_stats.return_value = ({'def': 10}, None)

            res = pvp.find_target(100)
            self.assertIsNotNone(res)
            self.assertEqual(res['uid'], 200)
            self.assertEqual(res['threat'], '🟢 НИЗКИЙ')

    def test_perform_hack_success(self):
        # Setup Attacker and Target
        mock_db.get_user.side_effect = lambda uid: {
            'uid': 100, 'xp': 1000, 'biocoin': 500, 'username': 'Attacker', 'proxy_expiry': 0, 'path': 'money'
        } if uid == 100 else {
            'uid': 200, 'level': 5, 'biocoin': 2000, 'username': 'Target', 'path': 'mind'
        }

        mock_db.check_pvp_cooldown.return_value = False
        mock_db.get_item_count.return_value = 0 # No firewall

        # Mock context manager
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock fetchone for log_id
        mock_cursor.fetchone.return_value = [999]

        with patch('modules.services.pvp.calculate_hack_chance', return_value=100): # 100% chance
            with patch('modules.services.pvp.random.randint', return_value=1): # Success roll
                res = pvp.perform_hack(100, 200, method='normal')

                self.assertTrue(res['success'])
                self.assertFalse(res['blocked'])
                self.assertGreater(res['stolen'], 0)

                # Verify DB calls
                self.assertTrue(mock_cursor.execute.called)

    def test_perform_hack_firewall(self):
        # Reset side_effect from previous test
        mock_db.get_user.side_effect = None
        # Provide both users
        mock_db.get_user.side_effect = lambda uid: {
            'uid': 100, 'xp': 1000, 'biocoin': 500, 'username': 'Attacker', 'path': 'money', 'level': 5
        } if uid == 100 else {
            'uid': 200, 'xp': 1000, 'biocoin': 500, 'username': 'Target', 'path': 'mind', 'level': 5
        }

        mock_db.check_pvp_cooldown.return_value = False
        mock_db.get_item_count.return_value = 1 # Has Firewall

        # Mock context manager
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [999]

        res = pvp.perform_hack(100, 200)

        self.assertFalse(res['success'])
        self.assertTrue(res['blocked'])

        # Verify Firewall used
        mock_db.use_item.assert_called_with(200, 'firewall', 1, cursor=mock_cursor)

if __name__ == '__main__':
    unittest.main()
