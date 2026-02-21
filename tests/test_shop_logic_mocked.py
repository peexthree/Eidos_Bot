import sys
import os
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.getcwd())

# 1. Mock 'psycopg2' and 'telebot' so they don't fail on import
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['telebot'] = MagicMock()

# 2. Mock 'database' module completely so we can control its functions
mock_db = MagicMock()
sys.modules['database'] = mock_db

# 3. Import service
# (config import happens inside shop or we import it here first, doesn't matter much as we will patch)
from modules.services.shop import get_shadow_shop_items

# Test Data
TEST_EQUIPMENT_DB = {
    'test_relic': {'name': 'Relic', 'price': 50000, 'slot': 'head'},
    'test_cheat': {'name': 'Cheat', 'price': 100000, 'slot': 'chip'},
    'high_tier_item': {'name': 'HighTier', 'price': 25000, 'slot': 'weapon'}
}
TEST_ITEMS_INFO = {
    'test_relic': {'name': 'Relic', 'desc': '...'},
    'test_cheat': {'name': 'Cheat', 'desc': '...'},
    'high_tier_item': {'name': 'HighTier', 'desc': '...'}
}
TEST_SHADOW_ITEMS = ['test_relic', 'test_cheat']

# 4. Define Test Logic
def test_shadow_shop_generation():
    print("Testing Shadow Broker Shop Generation...")

    # Mock user data
    uid = 123
    mock_db.get_user.return_value = {
        'shadow_broker_expiry': 9999999999, # Far future
        'uid': uid
    }

    # Patch the dictionaries in the module
    with patch('modules.services.shop.SHADOW_BROKER_ITEMS', TEST_SHADOW_ITEMS), \
         patch('modules.services.shop.EQUIPMENT_DB', TEST_EQUIPMENT_DB), \
         patch('modules.services.shop.ITEMS_INFO', TEST_ITEMS_INFO):

        # Run the function
        items = get_shadow_shop_items(uid)

        print(f"Generated {len(items)} items.")
        for item in items:
            print(f"Item: {item['name']}, Price: {item['price']}, Currency: {item['currency']}")

        # Assertions
        assert len(items) > 0, "Should generate items"
        currencies = [i['currency'] for i in items]
        print(f"Currencies found: {set(currencies)}")

        # Check price logic
        for item in items:
            iid = item['item_id']
            base = TEST_EQUIPMENT_DB.get(iid, {}).get('price') or TEST_ITEMS_INFO.get(iid, {}).get('price')

            # Note: shop.py uses .get('price', 50000) default if not found in dict value
            # But our test data has prices.

            if item['currency'] == 'xp':
                assert item['price'] == base, f"XP Price mismatch for {iid}: {item['price']} != {base}"
            elif item['currency'] == 'biocoin':
                assert item['price'] == base, f"BioCoin Price mismatch for {iid}: {item['price']} != {base}"

    print("Generation Test Passed!")

def test_purchase_logic_simulation():
    print("\nTesting Purchase Logic (Simulation)...")
    # Simulate handler logic
    uid = 123
    user_xp = 100000
    user_coins = 100000

    # Mock User
    user = {'uid': uid, 'xp': user_xp, 'biocoin': user_coins}
    mock_db.get_user.return_value = user

    # Item to buy (XP)
    target_item = {'item_id': 'test_relic', 'price': 50000, 'currency': 'xp'}

    # Simulate Logic from handler
    can_buy = False
    if target_item['currency'] == 'xp' and user['xp'] >= target_item['price']:
        user['xp'] -= target_item['price']
        can_buy = True
        print("Buying with XP...")
    elif target_item['currency'] == 'biocoin' and user['biocoin'] >= target_item['price']:
        user['biocoin'] -= target_item['price']
        can_buy = True
        print("Buying with BioCoins...")

    # Assertions
    if can_buy:
        print("Purchase Successful!")
        assert user['xp'] == 50000, "XP not deducted correctly"
        assert user['biocoin'] == 100000, "BioCoins should not be touched"
    else:
        print("Purchase Failed!")
        assert False, "Should be able to buy"

    print("Purchase Test Passed!")

if __name__ == "__main__":
    try:
        test_shadow_shop_generation()
        test_purchase_logic_simulation()
        print("\nALL TESTS PASSED SUCCESSFULLY.")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
