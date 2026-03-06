const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Enforce viewport to prevent zooming (as per memory directives)
const viewportMeta = document.createElement('meta');
viewportMeta.name = 'viewport';
viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
document.head.appendChild(viewportMeta);

const urlParams = new URLSearchParams(window.location.search);
const uid = urlParams.get('uid') || (tg.initDataUnsafe?.user?.id);

if (!uid) {
    document.body.innerHTML = '<h2 style="color:red;text-align:center;margin-top:50px;">ОШИБКА АВТОРИЗАЦИИ (NO UID)</h2>';
}

let inventoryData = { items: [], equipped: {}, profile: {} };
let currentFilter = 'all';

// Constants
const RARITY_COLORS = {
    'common': 'var(--rarity-common)',
    'rare': 'var(--rarity-rare)',
    'epic': 'var(--rarity-epic)',
    'legendary': 'var(--rarity-legendary)'
};

const RARITY_NAMES = {
    'common': 'Обычный',
    'rare': 'Редкий',
    'epic': 'Эпический',
    'legendary': 'Легендарный'
};

const ICONS = {
    'weapon': '⚔️',
    'head': '🪖',
    'body': '🦺',
    'software': '💾',
    'artifact': '💎',
    'consumable': '💊',
    'misc': '📦',
    'default': '❓'
};

// DOM Elements
const els = {
    loading: document.getElementById('loading-overlay'),
    profileName: document.getElementById('profile-name'),
    profileLvl: document.getElementById('profile-lvl'),
    profileFaction: document.getElementById('profile-faction'),
    profileAvatar: document.getElementById('profile-avatar'),
    statAtk: document.getElementById('stat-atk'),
    statDef: document.getElementById('stat-def'),
    statLuck: document.getElementById('stat-luck'),
    xpBar: document.getElementById('xp-bar'),
    xpText: document.getElementById('xp-text'),
    inventoryList: document.getElementById('inventory-list'),
    dollContainer: document.getElementById('doll-container'),
    tabs: document.querySelectorAll('.tab'),
    modal: document.getElementById('item-modal'),
    modalIcon: document.getElementById('modal-icon'),
    modalTitle: document.getElementById('modal-title'),
    modalRarity: document.getElementById('modal-rarity'),
    modalDesc: document.getElementById('modal-desc'),
    modalActions: document.getElementById('modal-actions'),
    modalClose: document.getElementById('modal-close')
};

// Main Load Function
async function loadData() {
    showLoading(true);
    try {
        const res = await fetch(`/api/inventory?uid=${uid}`);
        if (!res.ok) throw new Error('API Error');
        inventoryData = await res.json();

        renderProfile();
        renderDoll();
        renderInventory();
    } catch (e) {
        console.error('Fetch error:', e);
        tg.showAlert('Сбой соединения с сервером Eidos.');
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    els.loading.style.display = show ? 'flex' : 'none';
}

function renderProfile() {
    const p = inventoryData.profile;
    if (!p) return;

    els.profileName.innerText = p.name || 'Аноним';
    els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    els.profileFaction.innerText = p.faction || 'Неизвестно';

    if (p.avatar_url) {
        els.profileAvatar.src = p.avatar_url;
    }

    els.statAtk.innerText = p.atk || 0;
    els.statDef.innerText = p.def || 0;
    els.statLuck.innerText = p.luck || 0;

    const xp = p.xp || 0;
    const max_xp = p.max_xp || 1000;
    const pct = Math.min(100, Math.max(0, (xp / max_xp) * 100));

    els.xpBar.style.width = `${pct}%`;
    els.xpText.innerText = `${xp} / ${max_xp} XP`;
}

function renderDoll() {
    const slots = ['head', 'body', 'weapon', 'software', 'artifact'];

    slots.forEach(slotType => {
        const slotEl = document.getElementById(`slot-${slotType}`);
        if (!slotEl) return;

        const item = inventoryData.equipped[slotType];

        // Setup drop zone
        slotEl.ondragover = (e) => handleDragOver(e, slotType);
        slotEl.ondragleave = (e) => handleDragLeave(e);
        slotEl.ondrop = (e) => handleDrop(e, slotType);

        if (item) {
            const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
            const icon = item.image_url ? `<img src="${item.image_url}" alt="icon">` : `<span style="font-size:24px; color:${color}">${ICONS[slotType] || ICONS['default']}</span>`;

            slotEl.innerHTML = `
                <div class="equip-slot-label">${slotType.toUpperCase()}</div>
                <div class="equipped-item" draggable="true" onclick="openUnequipModal('${slotType}')" style="box-shadow: inset 0 0 10px ${color}40; border: 1px solid ${color};">
                    ${icon}
                    <span class="equipped-item-name" style="color:${color}">${item.name}</span>
                </div>
            `;

            // Drag to unequip
            const dragEl = slotEl.querySelector('.equipped-item');
            dragEl.ondragstart = (e) => {
                e.dataTransfer.setData('application/json', JSON.stringify({ action: 'unequip', slot: slotType }));
                tg.HapticFeedback.impactOccurred('light');
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
}

function renderInventory() {
    els.inventoryList.innerHTML = '';

    let filtered = inventoryData.items || [];
    if (currentFilter === 'equip') {
        filtered = filtered.filter(i => ['weapon', 'head', 'body', 'software', 'artifact'].includes(i.type));
    } else if (currentFilter === 'consumable') {
        filtered = filtered.filter(i => ['consumable', 'misc'].includes(i.type));
    } else if (currentFilter === 'shop') {
        els.inventoryList.innerHTML = '<div style="text-align:center; padding: 20px; color:#888;">Модуль магазина в разработке...</div>';
        return;
    }

    if (filtered.length === 0) {
        els.inventoryList.innerHTML = '<div style="text-align:center; padding: 20px; color:#888;">Ничего не найдено</div>';
        return;
    }

    filtered.forEach(item => {
        const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
        const rName = RARITY_NAMES[item.rarity] || 'Обычный';
        const iconHtml = item.image_url
            ? `<img src="${item.image_url}" alt="icon">`
            : `<span style="color:${color}">${ICONS[item.type] || ICONS['default']}</span>`;

        const card = document.createElement('div');
        card.className = 'item-card';
        // Only equipment is draggable
        const isEquippable = ['weapon', 'head', 'body', 'software', 'artifact'].includes(item.type);
        if (isEquippable) card.draggable = true;

        card.innerHTML = `
            <div class="item-icon">${iconHtml}</div>
            <div class="item-details">
                <div class="item-name glitch-hover" style="color:${color}">${item.name}</div>
                <div class="item-rarity" style="color:${color}80">${rName}</div>
            </div>
            ${item.quantity > 1 ? `<div class="item-qty">x${item.quantity}</div>` : ''}
        `;

        card.onclick = () => {
            tg.HapticFeedback.impactOccurred('light');
            openModal(item);
        };

        if (isEquippable) {
            card.ondragstart = (e) => {
                e.dataTransfer.setData('application/json', JSON.stringify({
                    action: 'equip',
                    inv_id: item.id,
                    item_id: item.item_id,
                    type: item.type
                }));
                tg.HapticFeedback.impactOccurred('medium');
            };
        }

        els.inventoryList.appendChild(card);
    });
}

// Drag and Drop Handlers
function handleDragOver(e, slotType) {
    e.preventDefault();
    try {
        // Can't easily read dataTransfer data in dragover, so we just allow drop
        // Validation happens in drop
        e.currentTarget.classList.add('drag-over');
    } catch(err){}
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

async function handleDrop(e, slotType) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');

    try {
        const dataStr = e.dataTransfer.getData('application/json');
        if (!dataStr) return;
        const data = JSON.parse(dataStr);

        if (data.action === 'equip') {
            // Check slot match
            if (data.type !== slotType) {
                tg.HapticFeedback.notificationOccurred('error');
                tg.showAlert(`Неверный слот! Этот предмет типа: ${data.type}`);
                return;
            }
            await equipItemAPI(data.inv_id, data.item_id);
        }
    } catch (err) {
        console.error('Drop error', err);
    }
}

// API Calls
async function equipItemAPI(inv_id, item_id) {
    tg.HapticFeedback.notificationOccurred('success');
    showLoading(true);
    try {
        const res = await fetch('/api/inventory/equip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ uid, inv_id, item_id })
        });
        const data = await res.json();
        if (data.success) {
            await loadData(); // Reload everything to get new stats and items
            closeModal();
        } else {
            tg.showAlert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (e) {
        tg.showAlert('Сбой сети при экипировке.');
    } finally {
        showLoading(false);
    }
}

async function unequipItemAPI(slotType) {
    tg.HapticFeedback.notificationOccurred('success');
    showLoading(true);
    try {
        const res = await fetch('/api/inventory/unequip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ uid, slot: slotType })
        });
        const data = await res.json();
        if (data.success) {
            await loadData();
            closeModal();
        } else {
            tg.showAlert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (e) {
        tg.showAlert('Сбой сети при снятии.');
    } finally {
        showLoading(false);
    }
}

// Modals
let currentModalItem = null;
let currentModalSlot = null;

function openModal(item) {
    currentModalItem = item;
    currentModalSlot = null;

    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    const rName = RARITY_NAMES[item.rarity] || 'Обычный';

    els.modalIcon.innerHTML = item.image_url
        ? `<img src="${item.image_url}" alt="icon">`
        : `<span style="color:${color}">${ICONS[item.type] || ICONS['default']}</span>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;

    els.modalRarity.innerText = rName;
    els.modalRarity.style.color = color;

    els.modalDesc.innerText = item.desc || "Описание отсутствует.";

    els.modalActions.innerHTML = '';
    const isEquippable = ['weapon', 'head', 'body', 'software', 'artifact'].includes(item.type);

    if (isEquippable) {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.innerText = 'УСТАНОВИТЬ В СЛОТ';
        btn.onclick = () => equipItemAPI(item.id, item.item_id);
        els.modalActions.appendChild(btn);
    }

    els.modal.style.display = 'flex';
}

function openUnequipModal(slotType) {
    const item = inventoryData.equipped[slotType];
    if (!item) return;

    currentModalItem = null;
    currentModalSlot = slotType;

    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    const rName = RARITY_NAMES[item.rarity] || 'Обычный';

    els.modalIcon.innerHTML = item.image_url
        ? `<img src="${item.image_url}" alt="icon">`
        : `<span style="color:${color}">${ICONS[slotType] || ICONS['default']}</span>`;

    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;

    els.modalRarity.innerText = rName;
    els.modalRarity.style.color = color;

    els.modalDesc.innerText = item.desc || "Экипировано";

    els.modalActions.innerHTML = '';
    const btn = document.createElement('button');
    btn.className = 'action-btn danger';
    btn.innerText = 'СНЯТЬ';
    btn.onclick = () => unequipItemAPI(slotType);
    els.modalActions.appendChild(btn);

    els.modal.style.display = 'flex';
}

function closeModal() {
    els.modal.style.display = 'none';
    currentModalItem = null;
    currentModalSlot = null;
}

els.modalClose.onclick = closeModal;

// Setup Tabs
els.tabs.forEach(tab => {
    tab.onclick = (e) => {
        tg.HapticFeedback.impactOccurred('light');
        els.tabs.forEach(t => t.classList.remove('active'));
        e.currentTarget.classList.add('active');
        currentFilter = e.currentTarget.dataset.filter;
        renderInventory();
    };
});

// Setup drag to unequip outside slots
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', e => {
    e.preventDefault();
    // If dropped somewhere that isn't an equip slot and data is unequip
    if (!e.target.closest('.equip-slot')) {
        const dataStr = e.dataTransfer.getData('application/json');
        if (dataStr) {
            try {
                const data = JSON.parse(dataStr);
                if (data.action === 'unequip' && data.slot) {
                    unequipItemAPI(data.slot);
                }
            } catch(err){}
        }
    }
});

// Initialize
tg.MainButton.text = "ЗАКРЫТЬ ИНТЕРФЕЙС";
tg.MainButton.show();
tg.MainButton.onClick(() => tg.close());

loadData();
