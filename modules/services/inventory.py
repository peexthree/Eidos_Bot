import database as db
from config import ITEMS_INFO, EQUIPMENT_DB, INVENTORY_LIMIT, PVP_ITEMS

def format_inventory(uid, category='all'):
    items = db.get_inventory(uid)
    equipped = db.get_equipped_items(uid)
    u = db.get_user(uid)
    inv_limit = INVENTORY_LIMIT

    txt = f"🎒 <b>РЮКЗАК [{len(items)}/{inv_limit}]</b>\n\n"

    if category == 'all' or category == 'equip':
        if equipped:
            txt += "<b>🛡 ЭКИПИРОВАНО:</b>\n"
            for slot, iid in equipped.items():
                name = ITEMS_INFO.get(iid, {}).get('name', iid)
                txt += f"• {name}\n"
            txt += "\n"

    # Filter out PVP items from general inventory
    non_pvp_items = [i for i in items if i['item_id'] not in PVP_ITEMS]

    # Filter
    filtered = []
    if category == 'all': filtered = non_pvp_items
    elif category == 'equip': filtered = [i for i in non_pvp_items if i['item_id'] in EQUIPMENT_DB]
    elif category == 'consumable': filtered = [i for i in non_pvp_items if i['item_id'] not in EQUIPMENT_DB]

    if filtered:
        txt += "<b>📦 ПРЕДМЕТЫ:</b>\n"
        for i in filtered:
            iid = i['item_id']
            name = ITEMS_INFO.get(iid, {}).get('name', iid)
            qty = i['quantity']
            desc = ITEMS_INFO.get(iid, {}).get('desc', '')[:30] + "..."

            qty_str = f" (x{qty})" if qty > 1 else ""
            txt += f"• <b>{name}</b>{qty_str}\n  <i>{desc}</i>\n"
    else:
        txt += "<i>Пусто...</i>\n"

    txt += f"\n♻️ <b>СТОИМОСТЬ РАЗБОРА:</b> 10%"
    return txt

def check_legacy_items(uid):
    """Проверяет наличие устаревших предметов для конвертации."""
    legacy_ids = ['shadow_reliq-speed', 'shadow_relic_speed', 'Tac_visor']
    with db.db_cursor() as cur:
        if not cur: return False
        cur.execute("SELECT 1 FROM inventory WHERE uid=%s AND item_id = ANY(%s) LIMIT 1", (uid, legacy_ids))
        return cur.fetchone() is not None

def convert_legacy_items(uid):
    """Конвертирует устаревшие предметы в актуальные."""
    conversions = {
        'shadow_reliq-speed': 'relic_speed',
        'shadow_relic_speed': 'relic_speed',
        'Tac_visor': 'tactical_helmet'
    }

    msg = ""
    # Используем db_session для атомарности
    with db.db_session() as conn:
        with conn.cursor() as cur:
            for old_id, new_id in conversions.items():
                cur.execute("SELECT quantity, durability FROM inventory WHERE uid=%s AND item_id=%s", (uid, old_id))
                res = cur.fetchone()
                if res:
                    qty, dur = res
                    # Добавляем новый предмет
                    db.add_item(uid, new_id, qty, cursor=cur, specific_durability=dur)

                    # Удаляем старый
                    cur.execute("DELETE FROM inventory WHERE uid=%s AND item_id=%s", (uid, old_id))

                    old_name = EQUIPMENT_DB.get(old_id, {}).get('name', old_id)
                    new_name = EQUIPMENT_DB.get(new_id, {}).get('name', new_id)
                    msg += f"✅ {old_name} -> {new_name} (x{qty})\n"

    return msg if msg else "Нет предметов для конвертации."
