import time
import random
import database as db
import config
from config import SHADOW_BROKER_ITEMS, EQUIPMENT_DB, ITEMS_INFO, CURSED_CHEST_DROPS

GACHA_PRICE = 1000

def get_shadow_shop_items(uid):
    u = db.get_user(uid)
    expiry = u.get('shadow_broker_expiry', 0)

    if expiry < time.time():
        return []

    # Stable random for the duration of this specific broker instance
    random.seed(expiry + uid)

    # 1. Base Pool: SHADOW_BROKER_ITEMS from config
    pool = list(SHADOW_BROKER_ITEMS)

    # 2. Add High-Tier Equipment (Price > 20000) to mix
    high_tier = [k for k, v in EQUIPMENT_DB.items() if v.get('price', 0) > 20000]
    pool.extend(high_tier)

    # Deduplicate
    pool = list(set(pool))

    # Select 3 random items
    if len(pool) > 3:
        selected = random.sample(pool, 3)
    else:
        selected = pool

    shop = []
    for item_id in selected:
        info = EQUIPMENT_DB.get(item_id) or ITEMS_INFO.get(item_id)
        if not info: continue

        base_price = info.get('price', 50000)

        # Currency Logic: 50% chance for XP (Life), 50% for BioCoins
        # "XP (Your Life) or Huge Sums of BioCoins"
        if random.random() < 0.5:
            curr = 'xp'
            price = base_price # 1 XP = 1 BioCoin value in this context (Life is expensive)
        else:
            curr = 'biocoin'
            price = base_price

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

    if roll < 0.01:
        # 1% - Cursed Item (Red)
        item_id = random.choice(CURSED_CHEST_DROPS)
        # Fetch name from EQUIPMENT_DB since they are equipment
        reward = EQUIPMENT_DB.get(item_id, {}).get('name', '🔴 ПРОКЛЯТЫЙ АРТЕФАКТ')

    elif roll < 0.06:
        # 5% - Fragment
        item_id = "fragment"
        reward = "🧩 ФРАГМЕНТ ДАННЫХ (Легендарный)"
    elif roll < 0.21:
         # 15% - Good Consumable
         item_id = random.choice(['neural_stimulator', 'emp_grenade', 'stealth_spray', 'abyssal_key'])
         reward = ITEMS_INFO[item_id]['name']
    elif roll < 0.41:
         # 20% - Standard Consumable
         item_id = random.choice(['battery', 'compass', 'master_key'])
         reward = ITEMS_INFO[item_id]['name']
    else:
         # 59% - Trash (XP consolation)
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
