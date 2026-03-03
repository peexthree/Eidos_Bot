import database as db
import json
import random
from modules.services.content import get_content_logic

def patch_claim_body(uid, s, cur):
    depth = s['depth']
    grave = db.get_random_grave(depth)
    u = db.get_user(uid)

    extra_loot_msg = ""
    # 20% base chance to find a cache
    if random.random() < 0.2:
        db.add_item(uid, 'encrypted_cache', cursor=cur)
        extra_loot_msg += "\n📦 <b>НАЙДЕНО:</b> Зашифрованный кэш."

    # 15% chance to find a "Memory Fragment" (Lore/Protocol)
    if random.random() < 0.15:
        proto = get_content_logic('protocol', u.get('path', 'general'), u.get('level', 1))
        if proto:
            db.save_knowledge(uid, proto['id'])
            extra_loot_msg += f"\n📜 <b>ЛОГ:</b> {proto['text'][:50]}..."

    if grave:
        if db.delete_grave(grave['id']):
            try:
                loot = json.loads(grave['loot_json'])
                coins = loot.get('coins', 0)
                items_str = loot.get('items', '')
            except:
                coins = 0
                items_str = ""

            cur.execute("UPDATE raid_sessions SET buffer_coins=buffer_coins+%s WHERE uid=%s", (coins, uid))
            if items_str:
                cur.execute("UPDATE raid_sessions SET buffer_items = COALESCE(buffer_items, '') || ',' || %s WHERE uid=%s", (items_str, uid))

            return True, f"💰 <b>МАРОДЕРСТВО:</b> Вы забрали {coins} BC и снаряжение.{extra_loot_msg}", {'alert': f"💰 +{coins} BC"}, 'loot_claimed'

    if extra_loot_msg:
         return True, f"🔍 <b>ПОИСК:</b> Среди обломков вы нашли ценные данные.{extra_loot_msg}", {'alert': "📦 ДАННЫЕ НАЙДЕНЫ"}, 'loot_claimed'

    return False, "❌ Останки уже разграблены или исчезли.", None, 'neutral'
