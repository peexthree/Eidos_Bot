import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# 1. Add getHeaders
get_headers_code = """
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': window.tg && tg.initData ? tg.initData : ''
    };
}
"""
if "function getHeaders" not in content:
    content = content.replace("let isActionLocked = false;", get_headers_code + "\nlet isActionLocked = false;")

# 2. Update fetchWithLock to not just fetch, wait, it's performAction that needs getHeaders. Let's see performAction.
old_perform_action = """async function performAction(endpoint, payload) {
    els.modal.classList.remove('active');
    const res = await fetchWithLock(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });"""

new_perform_action = """async function performAction(endpoint, payload) {
    els.modal.classList.remove('active');
    const res = await fetchWithLock(endpoint, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });"""

content = content.replace(old_perform_action, new_perform_action)

# Update loadData to use getHeaders for GET
old_load_data_fetch = "const res = await fetch(`/api/inventory?uid=${uid}`);"
new_load_data_fetch = "const res = await fetch(`/api/inventory?uid=${uid}`, { headers: getHeaders() });"
content = content.replace(old_load_data_fetch, new_load_data_fetch)

# Add Haptic Feedback in Modals
old_open_item_modal = """function openItemModal(item) {
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    els.modalIcon.innerHTML = ICONS[item.type] || ICONS['default'];"""

new_open_item_modal = """function openItemModal(item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    els.modalIcon.innerHTML = ICONS[item.type] || ICONS['default'];"""
content = content.replace(old_open_item_modal, new_open_item_modal)

old_open_unequip_modal = """function openUnequipModal(slot, item) {
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    els.modalIcon.innerHTML = ICONS[slot];"""

new_open_unequip_modal = """function openUnequipModal(slot, item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    els.modalIcon.innerHTML = ICONS[slot];"""
content = content.replace(old_open_unequip_modal, new_open_unequip_modal)

old_btn_equip = """btnEquip.onclick = () => performAction('/api/inventory/equip', {uid, item_id: item.item_id});"""
new_btn_equip = """btnEquip.onclick = () => {
        if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        performAction('/api/inventory/equip', {uid, item_id: item.item_id});
    };"""
content = content.replace(old_btn_equip, new_btn_equip)

old_btn_unequip = """btnUnequip.onclick = () => performAction('/api/inventory/unequip', {uid, slot: slot});"""
new_btn_unequip = """btnUnequip.onclick = () => {
        if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        performAction('/api/inventory/unequip', {uid, slot: slot});
    };"""
content = content.replace(old_btn_unequip, new_btn_unequip)


with open('static/js/app.js', 'w') as f:
    f.write(content)
print("Fetch and security updated")
