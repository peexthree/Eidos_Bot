import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

old_inventory = """function renderInventory() {
    els.inventoryList.innerHTML = '';

    // Фильтрация
    const items = inventoryData.items.filter(i => {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'equip') return ['weapon', 'head', 'body', 'software', 'artifact'].includes(i.type);
        if (currentFilter === 'consumable') return ['consumable', 'misc'].includes(i.type);
        return true;
    });

    if (items.length === 0) {
        els.inventoryList.innerHTML = '<div style="text-align:center; padding:30px; color:#555; font-family: Orbitron; letter-spacing: 2px;">СЕКТОР ПУСТ</div>';
        return;
    }

    items.forEach(item => {
        const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
        const card = document.createElement('div');
        card.className = 'item-card';
        card.style.borderLeft = `3px solid ${color}`;
        card.innerHTML = `
            <div class="item-icon" style="color:${color}; width: 40px; text-align: center;">${ICONS[item.type] || ICONS['default']}</div>
            <div class="item-details" style="flex: 1; margin-left: 10px;">
                <div class="item-name" style="color:${color}; font-weight: bold; font-size: 14px;">${item.name}</div>
                <div class="item-rarity" style="opacity:0.6; font-size:10px; text-transform: uppercase;">${RARITY_NAMES[item.rarity] || item.rarity}</div>
            </div>
            ${item.quantity > 1 ? `<div class="item-qty" style="color:#fff; background:#333; padding:2px 6px; border-radius:4px; font-size:12px;">x${item.quantity}</div>` : ''}
        `;
        card.onclick = () => openItemModal(item);
        els.inventoryList.appendChild(card);
    });
}"""

new_inventory = """function renderInventory() {
    els.inventoryList.innerHTML = '';

    // Фильтрация
    const items = inventoryData.items.filter(i => {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'equip') return ['weapon', 'head', 'body', 'software', 'artifact'].includes(i.type);
        if (currentFilter === 'consumable') return ['consumable', 'misc'].includes(i.type);
        return true;
    });

    if (items.length === 0) {
        els.inventoryList.innerHTML = '<div style="text-align:center; padding:30px; color:#555; font-family: Orbitron; letter-spacing: 2px;">СЕКТОР ПУСТ</div>';
        return;
    }

    const fragment = document.createDocumentFragment();

    items.forEach(item => {
        const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
        const card = document.createElement('div');
        card.className = 'item-card';
        card.style.borderLeft = `3px solid ${color}`;
        card.innerHTML = `
            <div class="item-icon" style="color:${color}; width: 40px; text-align: center;">${ICONS[item.type] || ICONS['default']}</div>
            <div class="item-details" style="flex: 1; margin-left: 10px;">
                <div class="item-name" style="color:${color}; font-weight: bold; font-size: 14px;">${item.name}</div>
                <div class="item-rarity" style="opacity:0.6; font-size:10px; text-transform: uppercase;">${RARITY_NAMES[item.rarity] || item.rarity}</div>
            </div>
            ${item.quantity > 1 ? `<div class="item-qty" style="color:#fff; background:#333; padding:2px 6px; border-radius:4px; font-size:12px;">x${item.quantity}</div>` : ''}
        `;
        card.onclick = () => openItemModal(item);
        fragment.appendChild(card);
    });

    els.inventoryList.appendChild(fragment);
}"""

content = content.replace(old_inventory, new_inventory)

with open('static/js/app.js', 'w') as f:
    f.write(content)

print("Inventory re-rendered via DocumentFragment.")
