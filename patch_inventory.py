import re

with open('bot.py', 'r') as f:
    bot_content = f.read()

# WebApp inventory API patch
api_inventory_patch = """
@app.route('/api/inventory', methods=['GET'])
def inventory_api():
    uid_str = flask.request.args.get('uid')
    if not uid_str:
        return flask.jsonify({"error": "Missing uid"}), 400

    try:
        uid = int(uid_str)
    except ValueError:
        return flask.jsonify({"error": "Invalid uid type"}), 400

    try:
        inventory_data = []
        equipped_data = {}

        # Profile Data Fetching
        from modules.schemas import User # Pydantic import
        user_dict = db.get_user(uid)

        profile_data = {}
        if user_dict:
            # Strictly validate user structure again just for safety (or rely on DB return)
            try:
                user = User(**user_dict).model_dump()
            except Exception as e:
                print(f"/// API INVENTORY PYDANTIC USER ERROR: {e}")
                user = user_dict

            level = user.get('level', 1)
            avatar_file_id = config.USER_AVATARS.get(level, config.USER_AVATARS.get(1))
            avatar_url = None
            if avatar_file_id:
                try:
                    avatar_url = bot.get_file_url(avatar_file_id)
                except Exception as e:
                    print(f"/// API INVENTORY ERROR GETTING AVATAR: {e}")

            from modules.services.utils import get_user_display_name

            # Using basic stats logic
            path_str = str(user.get('path', 'general')).lower()
            faction_name = config.SCHOOLS.get(path_str, "НЕОФИТ")

            profile_data = {
                "name": get_user_display_name(user),
                "username": user.get('username', ''),
                "level": level,
                "faction": faction_name,
                "biocoin": user.get('biocoin', 0),
                "xp": user.get('xp', 0),
                "avatar_url": avatar_url
            }

        def get_image_url(item_id, info):
            if info.get('url'):
                return info.get('url')
            file_id = info.get('file_id')

            if not file_id:
                if hasattr(config, 'ITEM_IMAGES') and item_id in config.ITEM_IMAGES:
                    file_id = config.ITEM_IMAGES[item_id]

            if file_id:
                try:
                    return bot.get_file_url(file_id)
                except Exception as e:
                    pass
            return None

        # 1. Load Equipment
        raw_equipped = db.get_user_equipment(uid) if hasattr(db, 'get_user_equipment') else {}
        if raw_equipped:
            for slot, item_id in raw_equipped.items():
                if item_id:
                    info = config.ITEMS_INFO.get(item_id, {})
                    ui_slot = slot.replace('helmet', 'head').replace('armor', 'body')
                    equipped_data[ui_slot] = {
                        "item_id": item_id,
                        "name": info.get('name', item_id),
                        "type": ui_slot,
                        "desc": info.get('desc', ''),
                        "rarity": info.get('rarity', 'common'),
                        "image_url": get_image_url(item_id, info)
                    }

        # 2. Load Inventory
        items = db.get_inventory(uid)
        from modules.schemas import InventoryItem

        for item in items:
            # Validate through Pydantic
            try:
                valid_item = InventoryItem(**item)
            except Exception as valid_err:
                print(f"/// API INV PYDANTIC ITEM ERR (UID {uid}): {valid_err}")
                continue # Skip corrupted item records

            item_id = valid_item.item_id

            if item_id in getattr(config, 'PVP_ITEMS', []):
                continue

            qty = valid_item.quantity
            item_info = config.ITEMS_INFO.get(item_id, {})

            raw_type = item_info.get('type', 'misc')
            category = raw_type

            if raw_type in ['weapon'] or item_info.get('slot') == 'weapon':
                category = 'weapon'
            elif raw_type in ['head', 'helmet', 'body', 'armor'] or item_info.get('slot') in ['head', 'helmet', 'body', 'armor']:
                category = 'equip'
            elif raw_type in ['software'] or item_info.get('slot') == 'software':
                category = 'software'
            elif raw_type in ['artifact'] or item_info.get('slot') == 'artifact':
                category = 'artifact'
            elif raw_type in ['consumable', 'misc']:
                category = 'consumable'
            else:
                if item_id in getattr(config, 'EQUIPMENT_DB', {}):
                    slot = item_info.get('slot')
                    if slot in ['head', 'helmet', 'body', 'armor']:
                        category = 'equip'
                    else:
                        category = slot
                else:
                    category = 'consumable'

            inventory_data.append({
                "id": valid_item.id,
                "item_id": item_id,
                "name": item_info.get('name', item_id),
                "quantity": qty,
                "type": category,
                "desc": item_info.get('desc', ''),
                "rarity": item_info.get('rarity', 'common'),
                "usable": item_info.get('usable', False),
                "image_url": get_image_url(item_id, item_info)
            })

        return flask.jsonify({"items": inventory_data, "equipped": equipped_data, "profile": profile_data}), 200
    except Exception as e:
        print(f"/// API INVENTORY ERROR: {e}")
        import traceback
        traceback.print_exc()
        return flask.jsonify({"error": str(e)}), 500
"""

bot_content = re.sub(r'@app\.route\(\'/api/inventory\', methods=\[\'GET\'\]\)\ndef inventory_api\(\):.*?return flask\.jsonify\(\{"error": str\(e\)\}\), 500', api_inventory_patch.strip(), bot_content, flags=re.DOTALL)

with open('bot.py', 'w') as f:
    f.write(bot_content)
