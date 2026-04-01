import re
import os
import textwrap

print("--- Patching static/inventory.html ---")
with open('static/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the stats-header
html = re.sub(r'<header class="stats-header">.*?</header>', '', html, flags=re.DOTALL)

# Insert the compact stats under the user-details
new_stats = """
                <div class="user-stats-line" style="display: flex; gap: 15px; justify-content: center; margin-top: 10px; font-size: 14px; color: #fff;">
                    <span title="АТК"><img src="IMG/eidos_weapon-attack.svg" style="width:14px; filter: invert(0.5) sepia(1) saturate(5) hue-rotate(330deg); vertical-align: middle;"> <span id="stat-atk" style="color: #ff4d4d;">0</span></span>
                    <span title="ЗАЩ"><img src="IMG/eidos_armor-defense.svg" style="width:14px; filter: invert(0.5) sepia(1) saturate(5) hue-rotate(200deg); vertical-align: middle;"> <span id="stat-def" style="color: #4da6ff;">0</span></span>
                    <span title="УДАЧА"><img src="IMG/eidos_luck-dice.svg" style="width:14px; filter: invert(0.5) sepia(1) saturate(5) hue-rotate(90deg); vertical-align: middle;"> <span id="stat-luck" style="color: #00ff41;">0</span></span>
                </div>
"""
html = html.replace('<div class="currency-display"', new_stats + '<div class="currency-display"')

# Add flex layout to view-nexus to center it
html = html.replace('<section id="view-nexus" class="view-panel active">', '<section id="view-nexus" class="view-panel active" style="display: flex; align-items: center; justify-content: center; height: 100vh;">')

# remove the glow from profile-name
html = html.replace('<h2 id="profile-name" style="color: #ffffff; text-shadow: 0 0 10px #ffffff;">ИДЕНТИФИКАЦИЯ...</h2>', '<h2 id="profile-name" style="color: #ffffff;">ИДЕНТИФИКАЦИЯ...</h2>')

with open('static/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("--- Patching static/css/style.css ---")
with open('static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Fix padding since header is removed
css = css.replace('padding-top: 90px;', 'padding-top: 20px;')

# Remove slime bars
css = re.sub(r'\.xp-bar-container\s*{[^}]+}', '', css)
css = re.sub(r'\.xp-bar-fill\s*{[^}]+}', '', css)

# Make equipped items full size and remove black background
css = re.sub(r'\.equip-slot\s*{[^}]+}',
'''.equip-slot {
    position: relative;
    width: 65px; height: 65px;
    background-color: transparent;
    border: 1px solid rgba(102, 252, 241, 0.3);
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
    transition: all 0.2s;
    overflow: hidden;
}''', css)

# Scale up equipped img
css += """
.equip-slot img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
"""

# Center and scale down Nexus grid
css = re.sub(r'\.nexus-grid\s*{[^}]+}',
'''.nexus-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(100px, 140px));
    justify-content: center;
    align-content: center;
    gap: 10px;
    padding: 10px;
    margin: 0 auto;
    height: 100%;
}''', css)

css = re.sub(r'min-height:\s*10vh;', 'min-height: 70px; aspect-ratio: 2/1;', css)

if '.nexus-tile img' not in css:
    css += '''
.nexus-tile img {
    width: 25px;
    height: 25px;
    margin-bottom: 5px;
    filter: drop-shadow(0 0 5px var(--eidos-neon));
}
.nexus-tile {
    font-size: 11px;
}
'''

# Center nexus container
css = re.sub(r'\.nexus-grid-container\s*{[^}]+}',
'''.nexus-grid-container {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 100%; height: auto;
    perspective: 700px;
    z-index: -1;
    display: flex;
    justify-content: center;
    align-items: center;
}''', css)

# Make sure active view-nexus is flex
css = re.sub(
    r'\.view-panel\.active\s*{[^}]+}',
    '''.view-panel.active {
    display: flex !important;
    flex-direction: column;
    animation: fadeScaleIn 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}''',
    css
)

with open('static/css/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("--- Patching static/js/app.js ---")
with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update renderDoll to use full size img for equipped items instead of SVG and remove text label
js = re.sub(
    r'const iconContent = getItemIcon\(item, slot\);.*?slotEl\.innerHTML = `.*?`;',
    '''
            // Modified renderDoll
            let imgHtml = '';
            if (item.type && item.type.startsWith('eidos_')) {
                imgHtml = `<img src="https://api.telegram.org/file/bot${window.tgBotToken || ''}/${item.item_id}" alt="item" style="width: 100%; height: 100%; object-fit: cover;">`;
            } else {
                imgHtml = `<img src="/api/inventory/image?item_id=${item.item_id}" alt="item" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='IMG/eidos_sys-warning.svg'">`;
            }
            slotEl.innerHTML = imgHtml;
            slotEl.onclick = () => openUnequipModal(slot, item);
    ''',
    js, flags=re.DOTALL
)
# Wait, actually let's just make it simple:
js = js.replace(
'''            const iconContent = getItemIcon(item, slot);
            slotEl.innerHTML = `
                <div style="font-size: 10px; color: #a0a0a0; position: absolute; top: 2px; left: 5px;">${slot.toUpperCase()}</div>
                <div style="width: 40px; height: 40px; margin: auto; display:flex; align-items:center; justify-content:center;">${iconContent}</div>
            `;
            slotEl.onclick = () => openUnequipModal(slot, item);''',
'''            const iconContent = getItemIcon(item, slot);
            // Extracted raw icon from getItemIcon if it's an img
            let rawIcon = iconContent;
            if (iconContent.includes('<img')) {
                rawIcon = iconContent.replace(/style="[^"]*"/, 'style="width: 100%; height: 100%; object-fit: cover;"');
            } else {
                rawIcon = `<div style="width: 100%; height: 100%; display:flex; align-items:center; justify-content:center;">${iconContent}</div>`;
            }
            slotEl.innerHTML = rawIcon;
            slotEl.onclick = () => openUnequipModal(slot, item);'''
)


# Fix nexus tile label size
js = re.sub(
    r'<span style="font-family: Orbitron; font-weight: bold; color: var\(--eidos-neon\); letter-spacing: 1px;">\$\{tile\.label\}</span>',
    '<span style="font-family: Orbitron; font-weight: bold; color: var(--eidos-neon); letter-spacing: 1px; font-size: 11px;">${tile.label}</span>',
    js
)
js = re.sub(
    r'<img src="IMG/\$\{tile\.icon\}" alt="\$\{tile\.label\}" style="width: 35px; height: 35px; margin-bottom: 10px; filter: drop-shadow\(0 0 5px var\(--eidos-neon\)\);">',
    '<img src="IMG/${tile.icon}" alt="${tile.label}" style="width: 25px; height: 25px; margin-bottom: 5px; filter: drop-shadow(0 0 5px var(--eidos-neon));">',
    js
)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("--- Patching bot.py ---")
with open('bot.py', 'r', encoding='utf-8') as f:
    bot = f.read()

# Fix inventory_equip to lookup inv_id
match = re.search(r'inv_id,\s*slot\s*=\s*None,\s*None\s*with db\.db_cursor\(\) as cur:', bot)
if not match:
    # Need to patch inventory_equip
    old_equip = """    data = flask.request.json
    uid, item_id = data.get('uid'), data.get('item_id')

    # In webapp, frontend sends item_id instead of inv_id for equipping.
    # We must find the inv_id in database.
    inv_id, slot = None, None
    with db.db_cursor() as cur:
        if cur:
            cur.execute("SELECT id, item_id FROM inventory WHERE uid=%s AND item_id=%s AND quantity > 0 LIMIT 1", (uid, item_id))
            row = cur.fetchone()
            if row:
                inv_id = row[0]
                import config
                info = config.ITEMS_INFO.get(item_id, {})
                slot = info.get('type')
                if slot in ['helmet']: slot = 'head'
                elif slot in ['armor']: slot = 'body'

    if inv_id and slot:
        success = db.equip_item(uid, inv_id, slot)"""

    # if it's already there, good, if not, let's inject it
    if 'SELECT id, item_id FROM inventory WHERE uid=%s AND item_id=%s AND quantity > 0 LIMIT 1' not in bot:
        bot = re.sub(
            r'uid, item_id = data\.get\(\'uid\'\), data\.get\(\'item_id\'\)\s*success = db\.equip_item\(uid, item_id\)',
            old_equip,
            bot
        )

# Fix equipped items having missing data
if '# --- Equipped (Enriching Data for WebApp) ---' in bot:
    new_equipped_block = """    # --- Equipped (Enriching Data for WebApp) ---
    raw_equipped = db.get_user_equipment(uid)
    equipped = {}
    for slot, item_data in raw_equipped.items():
        iid = item_data['item_id'] if isinstance(item_data, dict) else item_data
        if iid:
            info = config.ITEMS_INFO.get(iid, {})
            img_file_id = info.get('file_id')
            equipped[slot] = {
                "item_id": iid,
                "name": info.get('name', iid),
                "description": info.get('desc', "Данные отсутствуют."),
                "rarity": info.get('rarity', 'common'),
                "type": info.get('type', slot),
                "durability": item_data.get('durability', 100) if isinstance(item_data, dict) else 100,
                "stats": info.get('stats', {}),
                "image_url": f"/api/image/{img_file_id}" if img_file_id else None
            }
        else:
            equipped[slot] = None

    response_data = {
        "profile": profile,
        "items": items,
        "equipped": equipped
    }"""
    # Clean up the triple-quote indentation mess
    new_equipped_block = textwrap.dedent(new_equipped_block).strip()
    # Add back the base 4-space indent
    new_equipped_block = "\n".join("    " + line if line.strip() else "" for line in new_equipped_block.splitlines())

    pattern = r'[ ]*# --- Equipped \(Enriching Data for WebApp\) ---.*?response_data = \{.*?\}'
    bot = re.sub(pattern, new_equipped_block, bot, flags=re.DOTALL)
elif 'equipped = db.get_user_equipment(uid)' in bot:
    new_code = """    equipped_raw = db.get_user_equipment(uid)
    import config
    equipped = {}
    for slot, item_data in equipped_raw.items():
        if item_data and "item_id" in item_data:
            i_id = item_data["item_id"]
            info = config.ITEMS_INFO.get(i_id, {})
            # merge
            equipped[slot] = {
                "item_id": i_id,
                "durability": item_data.get("durability", 100),
                "name": info.get("name", i_id),
                "description": info.get("desc", "Данные отсутствуют."),
                "rarity": info.get("rarity", "common"),
                "type": info.get("type", slot),
                "stats": info.get("stats", {}),
                "image_url": f"/api/image/{info.get('file_id')}" if info.get('file_id') else None
            }
        else:
            equipped[slot] = None"""
    bot = bot.replace('equipped = db.get_user_equipment(uid)', new_code)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(bot)

print("ALL DONE")
