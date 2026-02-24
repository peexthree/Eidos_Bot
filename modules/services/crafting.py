import config
import database as db
import random

class CraftingService:
    RARITY_TIERS = {
        "⚪️": 1,
        "🔵": 2,
        "🟣": 3,
        "🟠": 4,
        "🔴": 5
    }

    def __init__(self):
        self.tier_map = {} # {tier: {slot: [item_ids]}}
        self.item_tier = {} # {item_id: tier}
        self._build_rarity_map()

    def _build_rarity_map(self):
        for item_id, data in config.EQUIPMENT_DB.items():
            name = data.get('name', '')
            slot = data.get('slot', 'misc')

            tier = 0
            for emoji, t in self.RARITY_TIERS.items():
                if emoji in name:
                    tier = t
                    break

            if tier > 0:
                if tier not in self.tier_map:
                    self.tier_map[tier] = {}
                if slot not in self.tier_map[tier]:
                    self.tier_map[tier][slot] = []

                self.tier_map[tier][slot].append(item_id)
                self.item_tier[item_id] = tier

    def get_item_tier(self, item_id):
        return self.item_tier.get(item_id, 0)

    def can_craft(self, uid, item_id):
        # 1. Check if item is equipment (in map)
        tier = self.get_item_tier(item_id)
        if tier == 0: return False

        # 2. Check if not max tier
        if tier >= 5: return False

        # 3. Check inventory count >= 3
        count = db.get_item_count(uid, item_id)
        return count >= 3

    def get_next_tier_candidates(self, item_id):
        tier = self.get_item_tier(item_id)
        if tier == 0 or tier >= 5: return []

        slot = config.EQUIPMENT_DB.get(item_id, {}).get('slot')
        next_tier = tier + 1

        return self.tier_map.get(next_tier, {}).get(slot, [])

    def craft_item(self, uid, item_id):
        if not self.can_craft(uid, item_id):
            return False, "❌ Недостаточно предметов или максимальный уровень."

        candidates = self.get_next_tier_candidates(item_id)
        if not candidates:
            return False, "❌ Невозможно создать предмет следующего уровня (нет вариантов)."

        new_item_id = random.choice(candidates)
        durability = config.ITEMS_INFO.get(new_item_id, {}).get('durability', 100)

        # Result container
        res_success = False
        res_msg = "❌ Неизвестная ошибка."

        try:
            with db.db_session() as conn:
                if not conn: return False, "❌ Ошибка БД."

                with conn.cursor() as cur:
                    # 1. Lock and Check Quantity
                    # FOR UPDATE ensures no one else modifies this row while we are checking
                    cur.execute("SELECT quantity FROM inventory WHERE uid = %s AND item_id = %s FOR UPDATE", (uid, item_id))
                    row = cur.fetchone()

                    if not row or row[0] < 3:
                        res_msg = "❌ Недостаточно предметов (нужно 3 в инвентаре, снимите если надето)."
                        raise ValueError("Not enough items")

                    # 2. Update Inventory (Consume)
                    new_qty = row[0] - 3
                    if new_qty == 0:
                        cur.execute("DELETE FROM inventory WHERE uid = %s AND item_id = %s", (uid, item_id))
                    else:
                        cur.execute("UPDATE inventory SET quantity = %s WHERE uid = %s AND item_id = %s", (new_qty, uid, item_id))

                    # 3. Add Reward
                    cur.execute("""
                        INSERT INTO inventory (uid, item_id, quantity, durability) VALUES (%s, %s, 1, %s)
                        ON CONFLICT (uid, item_id) DO UPDATE SET quantity = inventory.quantity + 1
                    """, (uid, new_item_id, durability))

                    res_success = True
                    res_msg = new_item_id

        except ValueError:
            pass # Handled by db_session rollback
        except Exception as e:
            print(f"/// CRAFT EXCEPTION: {e}")
            res_success = False
            res_msg = "❌ Ошибка транзакции."

        return res_success, res_msg

crafting_service = CraftingService()
