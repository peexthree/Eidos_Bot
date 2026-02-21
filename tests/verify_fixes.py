import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock psycopg2 before importing database
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.extras'].RealDictCursor = MagicMock()

import logic
import config
# Note: config might have been imported by logic already, but we need to patch it.

class TestFixes(unittest.TestCase):
    def test_shadow_broker_high_price(self):
        # Mock SHADOW_BROKER_ITEMS and EQUIPMENT_DB
        # logic.get_shadow_shop_items imports config inside the function.
        # We need to patch config in sys.modules or where logic imports it.

        # We'll use patch.dict on config.EQUIPMENT_DB if possible, but config is a module.
        # logic.py: import config (at top level too?) No, check logic.py
        # logic.py imports config at top level: from config import ...
        # AND get_shadow_shop_items does: import config

        # We need to patch 'config.SHADOW_BROKER_ITEMS' and 'config.EQUIPMENT_DB'

        with patch('config.SHADOW_BROKER_ITEMS', ['expensive_item']), \
             patch('config.EQUIPMENT_DB', {'expensive_item': {'name': 'Expensive', 'price': 50000, 'desc': 'Wow'}}), \
             patch('logic.db.get_user', return_value={'shadow_broker_expiry': 9999999999}), \
             patch('random.random', return_value=0.1):

            # 0.1 < 0.5 usually means XP, but we expect BioCoin due to price check > 20000

            items = logic.get_shadow_shop_items(123)
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertEqual(item['item_id'], 'expensive_item')
            self.assertEqual(item['currency'], 'biocoin')
            # Price should be 0.8 * 50000 = 40000
            self.assertEqual(item['price'], 40000)

    def test_convert_legacy_items(self):
        # Mock DB cursor for conversion
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        # Context manager support
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # logic.convert_legacy_items uses db_session
        with patch('logic.db.db_session') as mock_session:
             mock_session.return_value.__enter__.return_value = mock_conn

             # The function iterates 3 keys: shadow_reliq-speed, shadow_relic_speed, Tac_visor
             # fetchone is called 3 times.

             mock_cur.fetchone.side_effect = [
                 (2, 100), # shadow_reliq-speed found (qty=2)
                 None,     # shadow_relic_speed not found
                 None      # Tac_visor not found
             ]

             msg = logic.convert_legacy_items(123)

             # Check for INSERT call (relic_speed)
             # Arg 1 is query, Arg 2 is params (uid, new_id, qty, dur, qty)

             insert_calls = []
             for call in mock_cur.execute.call_args_list:
                 args = call[0]
                 if "INSERT INTO inventory" in args[0]:
                     insert_calls.append(args[1])

             self.assertTrue(len(insert_calls) >= 1, "Should have called INSERT")

             found_insert = False
             for params in insert_calls:
                 # params[1] is item_id
                 if params[1] == 'relic_speed':
                     self.assertEqual(params[2], 2)
                     found_insert = True
                     break
             self.assertTrue(found_insert, "Did not find INSERT for relic_speed")

             # Check for DELETE call (shadow_reliq-speed)
             delete_calls = []
             for call in mock_cur.execute.call_args_list:
                 args = call[0]
                 if "DELETE FROM inventory" in args[0]:
                     delete_calls.append(args[1])

             self.assertTrue(len(delete_calls) >= 1, "Should have called DELETE")

             found_delete = False
             for params in delete_calls:
                 if params[1] == 'shadow_reliq-speed':
                     found_delete = True
                     break
             self.assertTrue(found_delete, "Did not find DELETE for shadow_reliq-speed")

if __name__ == '__main__':
    unittest.main()
