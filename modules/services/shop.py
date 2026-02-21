import time
import random
import database as db
import config
from config import SHADOW_BROKER_ITEMS, EQUIPMENT_DB, ITEMS_INFO

def get_shadow_shop_items(uid):
    u = db.get_user(uid)
    expiry = u.get('shadow_broker_expiry', 0)

    if expiry < time.time():
        return []

    # Stable random for the duration of this specific broker instance
    random.seed(expiry + uid)

    pool = SHADOW_BROKER_ITEMS[:]

    # Ensure unique selection
    if len(pool) > 3:
        selected = random.sample(pool, 3)
    else:
        selected = pool

    shop = []
    for item_id in selected:
        info = EQUIPMENT_DB.get(item_id) or ITEMS_INFO.get(item_id)
        if not info: continue

        base_price = info.get('price', 1000)

        # Strict Pricing Logic
        if base_price > 20000:
             curr = 'biocoin'
             price = base_price # No discount for high tier
        elif random.random() < 0.5:
            curr = 'xp'
            price = int(base_price * 2.0) # XP is cheaper, so cost is higher
        else:
            curr = 'biocoin'
            price = base_price # Standard price

        shop.append({
            'item_id': item_id,
            'name': info['name'],
            'price': price,
            'currency': curr,
            'desc': info.get('desc', '')
        })

    random.seed() # Reset seed
    return shop
