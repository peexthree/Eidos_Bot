import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

new_doll = """function renderDoll() {
    const equipped = inventoryData.equipped || {};

    const slotsMap = {
        'head': els.dollContainer.querySelector('#slot-head'),
        'weapon': els.dollContainer.querySelector('#slot-weapon'),
        'body': els.dollContainer.querySelector('#slot-body'),
        'software': els.dollContainer.querySelector('#slot-software'),
        'artifact': els.dollContainer.querySelector('#slot-artifact')
    };

    Object.keys(slotsMap).forEach(slotType => {
        const item = equipped[slotType];
        const slotEl = slotsMap[slotType];
        if (!slotEl) return;

        slotEl.ondragover = (e) => handleDragOver(e, slotType);
        slotEl.ondragleave = (e) => handleDragLeave(e);
        slotEl.ondrop = (e) => handleDrop(e, slotType);

        if (item) {
            const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
            const icon = item.image_url ? `<img src="${item.image_url}" alt="icon">` : `<span style="font-size:24px; color:${color}">${ICONS[slotType] || ICONS['default']}</span>`;

            // Generate durability UI
            let durHtml = '';
            if (item.durability !== undefined && item.durability !== null) {
                const isLow = item.durability <= 3;
                durHtml = `<div class="item-durability ${isLow ? 'low' : ''}">ОЗ: ${item.durability}</div>`;
            }

            slotEl.innerHTML = `
                <div class="equip-slot-label">${slotType.toUpperCase()}</div>
                <div class="equipped-item" draggable="true" onclick="openUnequipModal('${slotType}')" style="box-shadow: inset 0 0 10px ${color}40; border: 1px solid ${color};">
                    ${icon}
                    <span class="equipped-item-name" style="color:${color}">${item.name}</span>
                    ${durHtml}
                </div>
            `;

            const dragEl = slotEl.querySelector('.equipped-item');
            dragEl.ondragstart = (e) => {
                e.dataTransfer.setData('application/json', JSON.stringify({ action: 'unequip', slot: slotType }));
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
            };
        } else {
            slotEl.style.borderColor = '#444';
            slotEl.innerHTML = `
                <div class="equip-slot-label">${slotType.toUpperCase()}</div>
                <div style="opacity: 0.3; font-size: 24px;">${ICONS[slotType] || '⬛'}</div>
                <div style="font-size: 10px; color: #666; margin-top: 5px;">ПУСТО</div>
            `;
            slotEl.onclick = null;
        }
    });
}"""

js = re.sub(r'function renderDoll\(\) \{[\s\S]*?(?=function renderInventory)', new_doll + '\n\n', js)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
