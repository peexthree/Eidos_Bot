import time
import random
import database as db
import config
from config import SHADOW_BROKER_ITEMS, EQUIPMENT_DB, ITEMS_INFO

GACHA_PRICE = 1000

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

def process_gacha_purchase(uid):
    u = db.get_user(uid)
    if not u or u['biocoin'] < GACHA_PRICE:
        return False, "❌ Недостаточно BioCoins!"

    # Deduct
    db.update_user(uid, biocoin=u['biocoin'] - GACHA_PRICE, total_spent=u['total_spent'] + GACHA_PRICE)

    roll = random.random()
    reward = ""
    item_id = ""

    if roll < 0.05:
        # 5% - Fragment
        item_id = "fragment"
        reward = "🧩 ФРАГМЕНТ ДАННЫХ (Легендарный)"
    elif roll < 0.20:
         # 15% - Good Consumable
         item_id = random.choice(['neural_stimulator', 'emp_grenade', 'stealth_spray', 'abyssal_key'])
         reward = ITEMS_INFO[item_id]['name']
    elif roll < 0.40:
         # 20% - Standard Consumable
         item_id = random.choice(['battery', 'compass', 'master_key'])
         reward = ITEMS_INFO[item_id]['name']
    else:
         # 60% - Trash (XP consolation)
         scrap = random.randint(10, 50)
         db.add_xp_to_user(uid, scrap)
         return True, f"📂 <b>ПУСТО...</b>\n\nВнутри только мусорный код.\nВы извлекли {scrap} XP."

    if item_id:
        if db.add_item(uid, item_id):
             return True, f"🎁 <b>УСПЕХ!</b>\n\nВы получили: <b>{reward}</b>"
        else:
             # Inventory full - refund
             db.update_user(uid, biocoin=u['biocoin'] + GACHA_PRICE)
             return False, "🎒 Рюкзак полон! Средства возвращены."

    return False, "Error"
