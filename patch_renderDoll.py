import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

old_func = """function renderDoll() {
    const slots = ['head', 'weapon', 'body', 'software', 'artifact'];
    slots.forEach(slot => {
        const item = inventoryData.equipped[slot];
        const slotEl = document.getElementById(`slot-${slot}`);
        if (!slotEl) return;

        if (item) {
            const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
            slotEl.innerHTML = `
                <div class="equipped-item" style="border: 1px solid ${color}; box-shadow: inset 0 0 15px ${color}40; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; background: rgba(0,0,0,0.6);">
                    <div style="font-size: 28px; filter: drop-shadow(0 0 5px ${color});">${ICONS[slot] || ICONS['default']}</div>
                    <div style="font-size: 8px; color: ${color}; text-align: center; margin-top:5px; word-wrap: break-word; padding: 0 2px;">${item.name}</div>
                </div>`;
            slotEl.onclick = () => openUnequipModal(slot, item);
        } else {
            slotEl.innerHTML = `<div style="opacity: 0.15; font-size: 28px; display:flex; align-items:center; justify-content:center; height:100%;">${ICONS[slot] || ICONS['default']}</div>`;
            slotEl.onclick = null;
        }
    });
}"""

new_func = """function renderDoll() {
    const slots = ['head', 'weapon', 'body', 'software', 'artifact'];
    slots.forEach(slot => {
        const item = inventoryData.equipped[slot];
        const slotEl = document.getElementById(`slot-${slot}`);
        if (!slotEl) return;

        slotEl.setAttribute('data-slot-type', slot);

        const currentItemId = slotEl.getAttribute('data-item-id');
        const newItemId = item ? String(item.item_id) : 'empty';

        // Solid Check: если предмет тот же — не перерисовывать
        if (currentItemId === newItemId) return;
        slotEl.setAttribute('data-item-id', newItemId);

        if (item) {
            const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];

            // Visual excellence logic
            let extraStyle = '';
            let extraClass = '';
            if (item.rarity === 'legendary') {
                extraClass = 'overheatPulse';
                extraStyle = `border: 1px solid ${color};`;
            } else if (item.rarity === 'epic') {
                extraStyle = `border: 1px solid ${color}; box-shadow: inset 0 0 15px ${color}80;`;
            } else {
                extraStyle = `border: 1px solid ${color}; box-shadow: inset 0 0 15px ${color}40;`;
            }

            slotEl.innerHTML = `
                <div class="equipped-item ${extraClass}" style="${extraStyle} width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; background: rgba(0,0,0,0.6);">
                    <div style="font-size: 28px; filter: drop-shadow(0 0 5px ${color});">${ICONS[slot] || ICONS['default']}</div>
                    <div style="font-size: 8px; color: ${color}; text-align: center; margin-top:5px; word-wrap: break-word; padding: 0 2px;">${item.name}</div>
                </div>`;
            slotEl.onclick = () => openUnequipModal(slot, item);
        } else {
            // Empty state canonical icon
            let rawIcon = ICONS[slot] || ICONS['default'];
            let modifiedIcon = rawIcon.replace('<img ', '<img style="opacity: 0.1; filter: grayscale(1);" ');
            slotEl.innerHTML = `<div style="font-size: 28px; display:flex; align-items:center; justify-content:center; height:100%;">${modifiedIcon}</div>`;
            slotEl.onclick = null;
        }
    });
}"""

content = content.replace(old_func, new_func)

with open('static/js/app.js', 'w') as f:
    f.write(content)

print("Replaced!")
