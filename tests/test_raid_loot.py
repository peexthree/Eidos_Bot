import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before importing modules
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
sys.modules['flask'] = MagicMock()

import unittest
from modules.services.raid import generate_loot, get_chest_drops

class TestRaidLoot(unittest.TestCase):

    @patch('random.uniform')
    def test_generate_loot_tiers(self, mock_uniform):
        # Test 🔴 [ПРОКЛЯТОЕ] (roll >= 98)
        mock_uniform.return_value = 98.0
        result = generate_loot(0, 0)
        self.assertEqual(result['prefix'], "🔴 [ПРОКЛЯТОЕ]")

        # Test 🟠 [ЛЕГЕНДА] (roll >= 93)
        mock_uniform.return_value = 93.0
        result = generate_loot(0, 0)
        self.assertEqual(result['prefix'], "🟠 [ЛЕГЕНДА]")

        # Test 🟣 [МИФ] (roll >= 84)
        mock_uniform.return_value = 84.0
        result = generate_loot(0, 0)
        self.assertEqual(result['prefix'], "🟣 [МИФ]")

        # Test 🔵 [РЕДКОЕ] (roll >= 64)
        mock_uniform.return_value = 64.0
        result = generate_loot(0, 0)
        self.assertEqual(result['prefix'], "🔵 [РЕДКОЕ]")

        # Test ⚪️ [ОБЫЧНОЕ] (roll < 64)
        mock_uniform.return_value = 63.9
        result = generate_loot(0, 0)
        self.assertEqual(result['prefix'], "⚪️ [ОБЫЧНОЕ]")

    @patch('random.uniform')
    def test_generate_loot_with_luck(self, mock_uniform):
        # Base roll 97.0, Luck 10 -> 97.0 + 1.0 = 98.0 -> 🔴 [ПРОКЛЯТОЕ]
        mock_uniform.return_value = 97.0
        result = generate_loot(0, 10)
        self.assertEqual(result['prefix'], "🔴 [ПРОКЛЯТОЕ]")

        # Base roll 92.0, Luck 10 -> 92.0 + 1.0 = 93.0 -> 🟠 [ЛЕГЕНДА]
        mock_uniform.return_value = 92.0
        result = generate_loot(0, 10)
        self.assertEqual(result['prefix'], "🟠 [ЛЕГЕНДА]")

    @patch('random.choice')
    @patch('random.randint')
    def test_get_chest_drops_pools(self, mock_randint, mock_choice):
        # Base pool (0 depth)
        mock_randint.return_value = 0 # No rare
        get_chest_drops(0, 0)
        base_pool = ['battery', 'compass', 'rusty_knife', 'hoodie', 'ram_chip']
        mock_choice.assert_called_with(base_pool)

        # Depth boundary 50 (Still base pool)
        get_chest_drops(50, 0)
        mock_choice.assert_called_with(base_pool)

        # Depth 51 (Base + >50 items)
        get_chest_drops(51, 0)
        pool_50 = base_pool + ['crowbar', 'leather_jacket', 'cpu_booster', 'neural_stimulator']
        mock_choice.assert_called_with(pool_50)

        # Depth boundary 150 (Still >50 pool)
        get_chest_drops(150, 0)
        mock_choice.assert_called_with(pool_50)

        # Depth 151 (Pool 50 + >150 items)
        get_chest_drops(151, 0)
        pool_150 = pool_50 + ['shock_baton', 'kevlar_vest', 'glitch_filter', 'emp_grenade', 'stealth_spray', 'data_spike']
        mock_choice.assert_called_with(pool_150)

        # Depth boundary 300 (Still >150 pool)
        get_chest_drops(300, 0)
        mock_choice.assert_called_with(pool_150)

        # Depth 301 (Pool 150 + >300 items)
        get_chest_drops(301, 0)
        pool_300 = pool_150 + ['cyber_katana', 'tactical_suit', 'ai_core', 'memory_wiper', 'abyssal_key']
        mock_choice.assert_called_with(pool_300)

    @patch('random.choice')
    @patch('random.randint')
    def test_get_chest_drops_luck(self, mock_randint, mock_choice):
        # random.randint(0, 100) + (luck * 0.5) > 90
        base_pool = ['battery', 'compass', 'rusty_knife', 'hoodie', 'ram_chip']
        rare_items = ['laser_pistol', 'nano_suit', 'backup_drive', 'nomad_goggles']

        # Just enough luck/roll
        mock_randint.return_value = 91
        get_chest_drops(0, 0)
        mock_choice.assert_called_with(base_pool + rare_items)

        # Luck pushes it over
        mock_randint.return_value = 86
        get_chest_drops(0, 10) # 86 + 5 = 91
        mock_choice.assert_called_with(base_pool + rare_items)

        # Not enough
        mock_randint.return_value = 85
        get_chest_drops(0, 10) # 85 + 5 = 90 (not > 90)
        mock_choice.assert_called_with(base_pool)

if __name__ == '__main__':
    unittest.main()
