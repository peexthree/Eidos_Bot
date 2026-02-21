import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock db dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()

# Mock database module before importing logic
db_mock = MagicMock()
sys.modules['database'] = db_mock

import logic

class TestNewMechanics(unittest.TestCase):

    def test_biomes(self):
        self.assertEqual(logic.get_biome_modifiers(10)['name'], "🏙 Трущобы")
        self.assertEqual(logic.get_biome_modifiers(100)['name'], "🏭 Промзона")
        self.assertEqual(logic.get_biome_modifiers(200)['name'], "🌃 Неон-Сити")
        self.assertEqual(logic.get_biome_modifiers(400)['name'], "🕸 Глубокая Сеть")
        self.assertTrue("🌌" in logic.get_biome_modifiers(600)['name'])
        self.assertGreater(logic.get_biome_modifiers(600)['mult'], 5.0)

    def test_loot_tiers(self):
        # Test Legendary (Roll 100 + Luck)
        # 100 luck * 0.5 = 50. Roll 50 => 100 total.
        with patch('random.randint', return_value=50):
            loot = logic.generate_loot(1, 100)
            self.assertEqual(loot['prefix'], "🟠 [ЛЕГЕНДА]")
            self.assertEqual(loot['mult'], 5.0)

        # Test Common (Low roll)
        with patch('random.randint', return_value=10):
            loot = logic.generate_loot(1, 0)
            self.assertEqual(loot['prefix'], "⚪️ [ОБЫЧНЫЙ]")

    @patch('logic.db.get_user')
    @patch('logic.db.get_raid_session_enemy')
    @patch('logic.db.get_villain_by_id')
    @patch('logic.db.db_cursor')
    @patch('logic.db.get_equipped_items')
    def test_combat_execution(self, mock_eq, mock_cursor, mock_villain, mock_s, mock_user):
        # Mock User
        mock_user.return_value = {'uid': 1, 'path': 'general', 'xp': 100, 'biocoin': 100, 'level': 1}
        mock_eq.return_value = {}

        # Mock Session Enemy
        # Enemy has 100 Max HP. Current HP = 9 (Execution range < 10)
        mock_s.return_value = {'current_enemy_id': 1, 'current_enemy_hp': 9, 'is_elite': False}

        # Mock Villain
        mock_villain.return_value = {'id': 1, 'name': 'Mob', 'hp': 100, 'atk': 10, 'def': 0, 'xp_reward': 10, 'coin_reward': 10}

        # Mock Full Session (for depth/signal)
        # Using context manager mock for db_cursor
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = {'uid': 1, 'depth': 10, 'signal': 100}

        # Action
        res_type, msg, extra = logic.process_combat_action(1, 'attack')

        self.assertEqual(res_type, 'win')
        self.assertIn("КАЗНЬ", msg)

    @patch('logic.db.get_user')
    @patch('logic.db.get_raid_session_enemy')
    @patch('logic.db.get_villain_by_id')
    @patch('logic.db.db_cursor')
    @patch('logic.db.get_equipped_items')
    def test_combat_adrenaline(self, mock_eq, mock_cursor, mock_villain, mock_s, mock_user):
        mock_user.return_value = {'uid': 1, 'path': 'general', 'xp': 100, 'biocoin': 100, 'level': 1}
        mock_eq.return_value = {}
        mock_s.return_value = {'current_enemy_id': 1, 'current_enemy_hp': 100, 'is_elite': False}
        mock_villain.return_value = {'id': 1, 'name': 'Mob', 'hp': 200, 'atk': 10, 'def': 0, 'xp_reward': 10, 'coin_reward': 10}

        mock_cur = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cur
        # Low Signal -> Adrenaline
        mock_cur.fetchone.return_value = {'uid': 1, 'depth': 10, 'signal': 15}

        # Mock random to avoid crit variance
        with patch('random.random', return_value=0.5), patch('random.uniform', return_value=1.0):
            res_type, msg, extra = logic.process_combat_action(1, 'attack')

        self.assertIn("АДРЕНАЛИН", msg)

    @patch('logic.db.get_user')
    @patch('logic.db.get_raid_session_enemy')
    @patch('logic.db.get_villain_by_id')
    @patch('logic.db.db_cursor')
    @patch('logic.db.get_equipped_items')
    def test_elite_scaling(self, mock_eq, mock_cursor, mock_villain, mock_s, mock_user):
        mock_user.return_value = {'uid': 1, 'path': 'general', 'xp': 100, 'biocoin': 100, 'level': 1}
        mock_eq.return_value = {}
        # Is Elite
        mock_s.return_value = {'current_enemy_id': 1, 'current_enemy_hp': 100, 'is_elite': True}

        villain_data = {'id': 1, 'name': 'Mob', 'hp': 100, 'atk': 10, 'def': 0, 'xp_reward': 10, 'coin_reward': 10}
        mock_villain.return_value = villain_data

        mock_cur = MagicMock()
        mock_cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = {'uid': 1, 'depth': 10, 'signal': 100}

        # Kill the mob to check rewards
        mock_s.return_value['current_enemy_hp'] = 1 # One shot range

        with patch('random.random', return_value=0.5):
            res_type, msg, extra = logic.process_combat_action(1, 'attack')

        # Check if villain dict was modified in place (buffed)
        self.assertIn("[ЭЛИТА]", villain_data['name'])
        self.assertEqual(villain_data['atk'], 15) # 10 * 1.5
        self.assertEqual(villain_data['xp_reward'], 30) # 10 * 3

if __name__ == '__main__':
    unittest.main()
