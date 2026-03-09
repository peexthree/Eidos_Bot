import re

with open('static/js/app.js', 'r') as f:
    js_content = f.read()

# Replace openItemModal
old_func_start = """function openItemModal(item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];

    els.modalIcon.innerHTML = `<div style="width: 80px; height: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">${getItemIcon(item, item.type)}</div>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = RARITY_NAMES[item.rarity] || item.rarity;
    els.modalRarity.style.color = color;
    els.modalDesc.innerHTML = item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>';"""

new_func_start = """function openItemModal(item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];

    // Большое изображение
    els.modalIcon.innerHTML = `<div class="modal-large-image">${getItemIcon(item, item.type)}</div>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = RARITY_NAMES[item.rarity] || item.rarity;
    els.modalRarity.style.color = color;

    // Формируем блок статов
    let statsHtml = '';
    if (item.stats) {
        if (item.stats.atk) statsHtml += `<span style="color:#ff4d4d;">ATK: +${item.stats.atk}</span> `;
        if (item.stats.def) statsHtml += `<span style="color:#4da6ff;">DEF: +${item.stats.def}</span> `;
        if (item.stats.luck) statsHtml += `<span style="color:#00ff41;">LCK: +${item.stats.luck}</span> `;
    }
    const finalDesc = (item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>').replace(/\\n/g, '<br>');

    els.modalDesc.innerHTML = `<div class="modal-stats">${statsHtml}</div><div class="modal-lore">${finalDesc}</div>`;
"""

js_content = js_content.replace(old_func_start, new_func_start)


# Now patch openUnequipModal
old_unequip_start = """function openUnequipModal(slot, item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];

    els.modalIcon.innerHTML = `<div style="width: 80px; height: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">${getItemIcon(item, slot)}</div>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = 'ПОДКЛЮЧЕНО К ЯДРУ';
    els.modalRarity.style.color = '#00ff41';
    els.modalDesc.innerHTML = 'Инициировать извлечение модуля?';"""

new_unequip_start = """function openUnequipModal(slot, item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];

    els.modalIcon.innerHTML = `<div class="modal-large-image">${getItemIcon(item, slot)}</div>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = 'ПОДКЛЮЧЕНО К ЯДРУ';
    els.modalRarity.style.color = '#00ff41';

    let statsHtml = '';
    if (item.stats) {
        if (item.stats.atk) statsHtml += `<span style="color:#ff4d4d;">ATK: +${item.stats.atk}</span> `;
        if (item.stats.def) statsHtml += `<span style="color:#4da6ff;">DEF: +${item.stats.def}</span> `;
        if (item.stats.luck) statsHtml += `<span style="color:#00ff41;">LCK: +${item.stats.luck}</span> `;
    }
    const finalDesc = (item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>').replace(/\\n/g, '<br>');

    els.modalDesc.innerHTML = `<div class="modal-stats">${statsHtml}</div><div class="modal-lore">${finalDesc}</div><div style="margin-top:10px; color:#ffcc00;">Инициировать извлечение модуля?</div>`;"""

js_content = js_content.replace(old_unequip_start, new_unequip_start)


# Update getItemIcon to return a larger image and adapt for the container
old_get_item_icon = """function getItemIcon(item, fallbackType) {
    if (item && item.image_url && !item.image_url.includes('IMG/None') && item.image_url !== 'IMG/.png') {
        return `<img src="${item.image_url}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px; filter: drop-shadow(0 0 2px rgba(255,255,255,0.2));">`;
    }
    return ICONS[fallbackType] || ICONS['default'];
}"""

new_get_item_icon = """function getItemIcon(item, fallbackType) {
    if (item && item.image_url && !item.image_url.includes('IMG/None') && item.image_url !== 'IMG/.png') {
        return `<img class="full-size-img" src="${item.image_url}">`;
    }
    return `<div class="icon-fallback">${ICONS[fallbackType] || ICONS['default']}</div>`;
}"""

js_content = js_content.replace(old_get_item_icon, new_get_item_icon)


with open('static/js/app.js', 'w') as f:
    f.write(js_content)

print("JS modal update applied.")
