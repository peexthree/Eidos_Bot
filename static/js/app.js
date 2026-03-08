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


let isActionLocked = false;
async function fetchWithLock(url, options) {
    if(isActionLocked) return {error: "Locked"};
    isActionLocked = true;
    if(window.tg && tg.MainButton) { tg.MainButton.showProgress(); tg.MainButton.disable(); }
    try {
        const res = await fetch(url, options);
        return res;
    } finally {
        isActionLocked = false;
        if(window.tg && tg.MainButton) { tg.MainButton.hideProgress(); tg.MainButton.enable(); }
    }
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
    'weapon': '<img src="IMG/eidos_weapon-attack.svg" class="item-type-icon">',
    'head': '<img src="IMG/eidos_biometric-id.svg" class="item-type-icon">',
    'body': '<img src="IMG/eidos_shield-armor.svg" class="item-type-icon">',
    'software': '<img src="IMG/eidos_neuro-brain.svg" class="item-type-icon">',
    'artifact': '<img src="IMG/eidos_shard-premium.svg" class="item-type-icon">',
    'consumable': '<img src="IMG/eidos_medkit-repair.svg" class="item-type-icon">',
    'misc': '<img src="IMG/eidos_data-mine.svg" class="item-type-icon">',
    'default': '<img src="IMG/eidos_sys-warning.svg" class="item-type-icon">'
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
    statSignal: document.getElementById('stat-signal'),
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


// Setup NEXUS GRID Particles
function setupNexusGrid() {
    const box = document.getElementById('p-box');
    if (!box) return;
    for(let i=0; i<35; i++) {
        let p = document.createElement('div');
        p.className = 'nexus-particle';
        let size = Math.random() * 3 + 1;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = (Math.random() * 100) + '%';
        p.style.setProperty('--duration', (Math.random() * 6 + 3) + 's');
        p.style.animationDelay = (Math.random() * 5) + 's';
        box.appendChild(p);
    }
}
setupNexusGrid();


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

    animateStatChange(els.statAtk, p.atk || 0);
    animateStatChange(els.statDef, p.def || 0);
    animateStatChange(els.statLuck, p.luck || 0);
    animateStatChange(els.statSignal, `${p.signal || 100}%`);

    const xp = p.xp || 0;
    const nXp = p.next_xp || 100;
    els.xpText.innerText = `${xp} / ${nXp} XP`;
    let pct = Math.min((xp / nXp) * 100, 100);
    els.xpBar.style.width = pct + '%';
}

function animateStatChange(el, newValue) {
    if (!el) return;
    const oldVal = el.innerText;
    if (oldVal !== String(newValue)) {
        el.innerText = newValue;

        // Convert to int for comparison if possible
        const oldNum = parseInt(oldVal.replace('%', ''));
        const newNum = parseInt(String(newValue).replace('%', ''));

        if (!isNaN(oldNum) && !isNaN(newNum)) {
            el.classList.remove('stat-up', 'stat-down');
            void el.offsetWidth; // trigger reflow
            if (newNum > oldNum) {
                el.classList.add('stat-up');
            } else if (newNum < oldNum) {
                el.classList.add('stat-down');
            }
        }
    }
}function renderDoll() {
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
                const data = {
                    action: 'equip',
                    inv_id: item.id,
                    item_id: item.item_id,
                    type: item.type
                };
                e.dataTransfer.setData('application/json', JSON.stringify(data));

                // Audio Context Haptics
                if(window.tg && tg.HapticFeedback) {
                    if(item.rarity === 'legendary') tg.HapticFeedback.notificationOccurred('success');
                    else tg.HapticFeedback.impactOccurred('medium');
                }

                // Thermal Emission
                if(item.rarity === 'legendary') card.classList.add('legendary-glow');

                // Action Log
                pushLog(`[PREPARING TO EQUIP]: ${item.name}`, 'SYNC');
            };

            card.ondragend = (e) => {
                card.classList.remove('legendary-glow');
                clearPreviewStats();
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
            // Normalize types
            let itemType = data.type;
            if (itemType === 'helmet') itemType = 'head';
            if (itemType === 'armor') itemType = 'body';

            // Check slot match
            if (itemType !== slotType) {
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');

                // Red flash effect
                document.body.style.boxShadow = 'inset 0 0 50px #ff3333';
                setTimeout(() => document.body.style.boxShadow = 'none', 300);

                if(window.tg) tg.showAlert(`Неверный слот! Этот предмет типа: ${data.type}`);
                else alert(`Неверный слот! Этот предмет типа: ${data.type}`);
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
        const res = await fetchWithLock('/api/inventory/equip', {
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
        const res = await fetchWithLock('/api/inventory/unequip', {
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

// loadData();

// === SPA Navigation Logic ===
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

navItems.forEach(nav => {
    nav.addEventListener('click', (e) => {
        const targetViewId = e.currentTarget.dataset.target;

        // Haptic feedback
        if (window.tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred('light');
        }

        // Update Nav UI
        navItems.forEach(n => n.classList.remove('active'));
        e.currentTarget.classList.add('active');

        // Update View UI
        views.forEach(v => {
            v.classList.remove('active');
            if (v.id === targetViewId) {
                // Short timeout to restart animation
                setTimeout(() => v.classList.add('active'), 10);
            }
        });

        // Logic for specific views
        if (targetViewId === 'view-shop') {
            renderShop();
        } else if (targetViewId === 'view-craft') {
            // init craft logic
        } else if (targetViewId === 'view-raids') {
            // load raids
        } else if (targetViewId === 'view-social') {
            // load social
        }
    });
});

// Remove Profile-header display from loadData to prevent duplication
// (Stats are now fixed at the top)

function renderShop() {
    const shopList = document.getElementById('shop-list');
    shopList.innerHTML = '<div style="text-align:center; padding: 20px; color:#888;">Модуль Торгового Шлюза загружается...</div>';

    // Will implement shop fetch and render in next step
}


function updateSignalUI() {
    const p = inventoryData.profile;
    if (!p) return;

    els.statSignal.innerText = `${p.signal}%`;
    els.statSignal.style.color = p.signal > 50 ? '#00ff00' : (p.signal > 20 ? '#ffcc00' : '#ff3333');
}

// Ensure signal is updated
const _oldLoad = loadData;
loadData = async function() {
    await _oldLoad();
    updateSignalUI();
};

function renderDoll() {
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

            slotEl.innerHTML = `
                <div class="equip-slot-label">${slotType.toUpperCase()}</div>
                <div class="equipped-item" draggable="true" onclick="openUnequipModal('${slotType}')" style="box-shadow: inset 0 0 10px ${color}40; border: 1px solid ${color};">
                    ${icon}
                    <span class="equipped-item-name" style="color:${color}">${item.name}</span>
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
}

/* === CREATIVE UI MODULE === */

// Action Log System
function pushLog(text, type = "SYS") {
    const el = document.getElementById('action-log-text');
    const pEl = document.querySelector('.log-prefix');
    if (!el || !pEl) return;

    // Animate resetting text
    el.innerText = '';
    el.style.opacity = 0;

    setTimeout(() => {
        pEl.innerText = `[${type}]`;
        pEl.style.color = type === 'ERR' ? '#ff3333' : (type === 'SYNC' ? '#33ccff' : '#666');
        el.innerText = text;
        el.style.color = type === 'ERR' ? '#ff3333' : '#00ff00';
        el.style.opacity = 1;

        // Glitch type effect
        let typed = '';
        let i = 0;
        const speed = 20;
        const origText = text;

        const typeWriter = () => {
            if (i < origText.length) {
                typed += origText.charAt(i);
                el.innerText = typed;
                i++;
                setTimeout(typeWriter, speed);
            }
        };
        typeWriter();

    }, 100);
}

// Low Signal Effect
function checkLowSignal(signalStr) {
    const signal = parseInt(String(signalStr).replace('%', ''));
    if (!isNaN(signal)) {
        if (signal < 20) {
            document.body.classList.add('low-signal');
            pushLog('CRITICAL SIGNAL LOSS. SYSTEM UNSTABLE.', 'ERR');
            if (window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('warning');
        } else {
            document.body.classList.remove('low-signal');
        }
    }
}

// Ghost Stats Preview
function previewStats(draggedItemInfo) {
    if (!inventoryData || !inventoryData.profile) return;
    const p = inventoryData.profile;
    const eq = inventoryData.equipped || {};

    // We need to parse item stats. They are not explicitly passed in the list except from DB.
    // For now, visual feedback: highlight the target slot type.
    const type = draggedItemInfo.type;
    const targetSlot = document.getElementById(`slot-${type}`);

    if (targetSlot) {
        targetSlot.classList.add('drag-over');
        // If we had actual stat numbers in item payload, we would inject them into the header here
        // As a visual fallback:
        els.statAtk.classList.add('stat-up');
        els.statDef.classList.add('stat-up');
    }
}

function clearPreviewStats() {
    const slots = document.querySelectorAll('.equip-slot');
    slots.forEach(s => s.classList.remove('drag-over'));

    els.statAtk.classList.remove('stat-up', 'stat-down');
    els.statDef.classList.remove('stat-up', 'stat-down');
}


// Boot Sequence
let bootFinished = false;

function showBootSequence() {
    if (bootFinished) return;

    const loadingOverlay = document.getElementById('loading-overlay');
    const progBar = document.getElementById('sys-progress');
    const txt = document.getElementById('progress-text');
    const logBox = document.getElementById('boot-logs');

    if (!loadingOverlay) return;

    const logs = [
        "Запуск ядра...",
        "Подключение API...",
        "Чтение базы данных...",
        "Синхронизация инвентаря...",
        "Анализ сектора...",
        "Оптимизация нейросетей...",
        "Загрузка завершена."
    ];

    loadingOverlay.style.display = 'flex';
    let p = 0;
    let idx = 0;

    function addLog() {
        if(idx < logs.length) {
            const el = document.createElement('div');
            el.innerText = '> ' + logs[idx++];
            logBox.appendChild(el);
            if(logBox.children.length > 5) logBox.removeChild(logBox.firstChild);
            if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
        }
    }

    const intervalId = setInterval(() => {
        if(p < 100) {
            p += Math.floor(Math.random() * 8) + 2;
            if(p > 100) p = 100;
            if (progBar) progBar.style.width = p + '%';
            if (txt) txt.innerText = 'СИНХРОНИЗАЦИЯ: ' + p + '%';
            if(p % 15 === 0 || p % 20 === 0 || p === 100) addLog();
        } else {
            clearInterval(intervalId);
            bootFinished = true;
            setTimeout(() => {
                loadingOverlay.style.opacity = '0';
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                    pushLog('СИСТЕМА АКТИВИРОВАНА.', 'SYS');
                    loadData(); // Load actual data after boot
                }, 500);
            }, 800);
        }
    }, 150);
}


// Redefine showLoading to use simpler spinner after boot
const _originalShowLoading = showLoading;
showLoading = function(show) {
    if (!bootFinished) return; // Don't interrupt boot
    _originalShowLoading(show);
};

// Hook checkLowSignal into updateSignalUI
const _updateSignalUI = updateSignalUI;
updateSignalUI = function() {
    _updateSignalUI();
    if(inventoryData && inventoryData.profile) {
        checkLowSignal(inventoryData.profile.signal);
    }
}

showBootSequence();
