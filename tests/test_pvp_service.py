import unittest
from unittest.mock import MagicMock, patch
import sys
import json

# Mock modules before importing pvp
mock_db = MagicMock()
mock_config = MagicMock()
sys.modules['database'] = mock_db
sys.modules['config'] = mock_config

# Setup default config values needed by pvp.py
mock_config.PVP_CONSTANTS = {
    "SHIELD_DURATION": 14400,
    "PROTECTION_LIMIT": 500,
    "HACK_REWARD": 25,
    "STEAL_PERCENT": 0.10,
    "MAX_STEAL": 15
}
mock_config.QUARANTINE_LEVEL = 3
mock_config.SOFTWARE_DB = {
    "soft_brute_v1": {"type": "atk", "cost": 100},
    "soft_wall_v1": {"type": "def", "cost": 100},
    "soft_vpn_v1": {"type": "stl", "cost": 100}
}
mock_config.DECK_UPGRADES = {1: {"slots": 1, "cost": 0}}

from modules.services import pvp

class TestPVPService(unittest.TestCase):
    def setUp(self):
        mock_db.reset_mock()
        # Reset side effects
        mock_db.get_user.side_effect = None

    def test_find_target_success(self):
        mock_db.get_random_user_for_hack.return_value = 200
        mock_db.get_user.side_effect = lambda uid: {
            'uid': uid, 'level': 6, 'biocoin': 1000,
            'is_quarantined': False, 'username': 'Target', 'path': 'tech',
            'deck_config': json.dumps({"1": "soft_wall_v1"})
        } if uid == 200 else {'uid': 100, 'level': 10, 'path': 'mind'}

        mock_db.check_pvp_cooldown.return_value = False

        # Mock get_user_stats for threat calculation
        with patch('modules.services.pvp.get_user_stats') as mock_stats:
            mock_stats.return_value = ({'def': 10}, None)

            res = pvp.find_target(100)
            self.assertIsNotNone(res)
            self.assertEqual(res['uid'], 200)
            self.assertEqual(res['threat'], '🟡 СРЕДНИЙ')

    def test_execute_hack_success(self):
        # Setup Attacker and Target
        mock_db.get_user.side_effect = lambda uid: {
            'uid': 100, 'xp': 1000, 'biocoin': 500, 'username': 'Attacker', 'proxy_expiry': 0, 'path': 'money'
        } if uid == 100 else {
            'uid': 200, 'level': 5, 'biocoin': 2000, 'username': 'Target', 'path': 'mind',
            'deck_config': json.dumps({"1": "soft_wall_v1", "2": None, "3": None})
        }

        mock_db.check_pvp_cooldown.return_value = False
        mock_db.get_item_count.return_value = 0 # No firewall

        # Mock context manager
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.db_cursor.return_value.__enter__.return_value = mock_cursor

        # Mock fetchone for log_id and biocoin lock
        mock_cursor.fetchone.side_effect = [
            [2000], # SELECT biocoin FOR UPDATE
            [999]   # RETURNING id (log)
        ]

        # Override get_item_count to work with context manager mock if needed
        # But execute_hack calls db.get_item_count(..., cursor=cur)
        # We need to ensure db.get_item_count returns 0 when passed a cursor
        # Since we mocked the whole module db, we can set side_effect
        mock_db.get_item_count.return_value = 0

        # Attacker uses ATK (beats DEF) in slot 1
        selected_programs = {"1": "soft_brute_v1", "2": "soft_brute_v1", "3": None}

        res = pvp.execute_hack(100, 200, selected_programs)

        self.assertTrue(res['success'])
        self.assertFalse(res.get('blocked', False))
        self.assertGreater(res['stolen'], 0)

        # Verify DB calls
        # Should update attacker coin, target coin, target shield
        self.assertTrue(mock_cursor.execute.called)

    def test_execute_hack_firewall(self):
        # Reset side_effect from previous test
        mock_db.get_user.side_effect = None
        # Provide both users
        mock_db.get_user.side_effect = lambda uid: {
            'uid': 100, 'xp': 1000, 'biocoin': 500, 'username': 'Attacker', 'path': 'money', 'level': 5
        } if uid == 100 else {
            'uid': 200, 'xp': 1000, 'biocoin': 500, 'username': 'Target', 'path': 'mind', 'level': 5
        }

        # Mock context manager
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.db_session.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.db_cursor.return_value.__enter__.return_value = mock_cursor

        # Mock get_item_count to return 1 for firewall
        mock_db.get_item_count.return_value = 1

        res = pvp.execute_hack(100, 200, {})

        self.assertFalse(res['success'])
        self.assertTrue(res['blocked'])

        # Verify Firewall used
        mock_db.use_item.assert_called()

if __name__ == '__main__':
    unittest.main()
