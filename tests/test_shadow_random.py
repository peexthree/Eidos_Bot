import unittest
from unittest.mock import MagicMock, patch
import sys
import random

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['flask'] = MagicMock()
db_mock = MagicMock()
sys.modules['database'] = db_mock

import logic
import config

class TestShadowRandom(unittest.TestCase):
    def test_deterministic_generation(self):
        # Mock user
        uid = 12345
        expiry = 1000000

        # Mock Config Items
        config.SHADOW_BROKER_ITEMS = ['item1', 'item2', 'item3', 'item4', 'item5']
        config.EQUIPMENT_DB = {
            'item1': {'name': 'I1', 'price': 1000},
            'item2': {'name': 'I2', 'price': 2000},
            'item3': {'name': 'I3', 'price': 3000},
            'item4': {'name': 'I4', 'price': 4000},
            'item5': {'name': 'I5', 'price': 5000},
        }

        db_mock.get_user.return_value = {'shadow_broker_expiry': expiry}

        # Run 1
        with patch('time.time', return_value=expiry - 100):
            shop1 = logic.get_shadow_shop_items(uid)

        # Run 2 (Same inputs)
        with patch('time.time', return_value=expiry - 50):
            shop2 = logic.get_shadow_shop_items(uid)

        # Verify identical results
        self.assertEqual(len(shop1), 3)
        self.assertEqual(len(shop2), 3)

        ids1 = [i['item_id'] for i in shop1]
        ids2 = [i['item_id'] for i in shop2]
        self.assertEqual(ids1, ids2)

        prices1 = [i['price'] for i in shop1]
        prices2 = [i['price'] for i in shop2]
        self.assertEqual(prices1, prices2)

        currencies1 = [i['currency'] for i in shop1]
        currencies2 = [i['currency'] for i in shop2]
        self.assertEqual(currencies1, currencies2)

    def test_random_isolation(self):
        # Verify that calling the function doesn't affect global random state
        uid = 123
        expiry = 1000
        db_mock.get_user.return_value = {'shadow_broker_expiry': expiry}

        random.seed(42)
        state_before = random.getstate()

        with patch('time.time', return_value=expiry - 10):
            logic.get_shadow_shop_items(uid)

        state_after = random.getstate()
        self.assertEqual(state_before, state_after)

if __name__ == '__main__':
    unittest.main()
