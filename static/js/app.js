const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// 1. Принудительный viewport против зума
const viewportMeta = document.createElement('meta');
viewportMeta.name = 'viewport';
viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
document.head.appendChild(viewportMeta);

const urlParams = new URLSearchParams(window.location.search);
const uid = urlParams.get('uid') || (tg.initDataUnsafe?.user?.id);

if (!uid) {
    document.body.innerHTML = '<h2 style="color:red;text-align:center;margin-top:50px;">ОШИБКА АВТОРИЗАЦИИ (NO UID)</h2>';
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': window.tg && tg.initData ? tg.initData : (uid ? `query_id=mock&user=%7B%22id%22%3A${uid}%7D` : '')
    };
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
let lastStats = {atk: 0, def: 0, luck: 0, signal: 100};

// Константы раритетности
const RARITY_COLORS = {
    'common': 'var(--rarity-common)',
    'rare': 'var(--rarity-rare)',
    'epic': 'var(--rarity-epic)',
    'legendary': 'var(--rarity-legendary)'
};

const RARITY_NAMES = {
    'common': 'БАЗОВЫЙ',
    'rare': 'РЕДКИЙ',
    'epic': 'ЭЛИТНЫЙ',
    'legendary': 'РЕЛИКТ'
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

// DOM Элементы
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

// Таймеры для загрузки
const MIN_LOADING_TIME = 3000;
const startTime = Date.now();
let dataLoaded = false;
let introFinished = false;

// === ЛОГИКА ЗАГРУЗКИ ДАННЫХ ===
async function loadData() {
    const vfxVideo = document.querySelector('#eidos-loader video');
    if (vfxVideo) {
        vfxVideo.play().catch(err => console.log("Video wait for interaction"));
    }

    const loaderTimeout = setTimeout(() => {
        if (!dataLoaded && els.loading) {
            const videoLoader = document.getElementById('eidos-loader');
            if (videoLoader) videoLoader.style.display = 'none';
            els.loading.style.display = 'flex';
        }
    }, 3000);

    try {
        console.log("/// EIDOS: Fetching inventory...");
        const res = await fetch(`/api/inventory?uid=${uid}`, { headers: getHeaders() });
        if (!res.ok) throw new Error('API Error');
        
        inventoryData = await res.json();

        renderProfile();
        renderNexusGrid();
        renderDoll();
        renderInventory();
        
        dataLoaded = true;
        clearTimeout(loaderTimeout);
        
        checkAndRemoveLoader();
        
    } catch (e) {
        console.error('Fetch error:', e);
        const videoLoader = document.getElementById('eidos-loader');
        if (videoLoader) videoLoader.style.display = 'none';
        tg.showAlert('Сбой соединения с сервером Eidos.');
    }
}

// Проверка: и видео доиграло, и данные есть
let skipClicked = false;
let loaderFadeTimeout = null;

function checkAndRemoveLoader() {
    if (skipClicked) {
        if (dataLoaded) executeLoaderFade();
        return;
    }
    const elapsedTime = Date.now() - startTime;
    if (dataLoaded && elapsedTime >= MIN_LOADING_TIME) {
        executeLoaderFade();
    } else if (dataLoaded) {
        loaderFadeTimeout = setTimeout(executeLoaderFade, MIN_LOADING_TIME - elapsedTime);
    }
}

function executeLoaderFade() {
    const loader = document.getElementById('eidos-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.remove();
            if (els.loading) els.loading.style.display = 'none';
            pushLog('СИСТЕМА АКТИВИРОВАНА.', 'SYS');
            showView('view-nexus');
        }, 800);
    } else {
        if (els.loading) els.loading.style.display = 'none';
        showView('view-nexus');
    }
}

window.forceCloseLoader = function() {
    skipClicked = true;
    if (loaderFadeTimeout) {
        clearTimeout(loaderFadeTimeout);
        loaderFadeTimeout = null;
    }
    if (dataLoaded) {
        executeLoaderFade();
    } else {
        const loader = document.getElementById('eidos-loader');
        if (loader) loader.style.display = 'none';
        els.loading.style.display = 'flex';
    }
};

// === ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ DOM ===
document.addEventListener('DOMContentLoaded', () => {
    setupNexusGrid();
    
    const vfxVideo = document.querySelector('#eidos-loader video');
    if (vfxVideo) {
        vfxVideo.play().catch(() => {
            console.log("Автоплей заблокирован. Ожидание клика.");
        });
    }

    loadData();
});

// === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
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

function renderProfile() {
    const p = inventoryData.profile;
    if (!p) return;
    els.profileName.innerText = p.name || 'ОБЪЕКТ НЕИЗВЕСТЕН';
    els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    els.profileFaction.innerText = p.faction || 'ФРАКЦИЯ: НЕЙТРАЛ';
    if (p.avatar_url) els.profileAvatar.src = p.avatar_url;

    animateStatChange(els.statAtk, p.atk || 0);
    animateStatChange(els.statDef, p.def || 0);
    animateStatChange(els.statLuck, p.luck || 0);
    updateSignalUI();

    const xp = p.xp || 0;
    const nXp = p.next_xp || 100;
    els.xpText.innerText = `${xp} / ${nXp} ОПЫТ`;
    let pct = Math.min((xp / nXp) * 100, 100);
    els.xpBar.style.width = pct + '%';
}

function animateStatChange(el, newValue) {
    if (!el) return;
    const oldVal = parseInt(el.innerText) || 0;
    el.innerText = newValue;
    if (newValue !== oldVal && oldVal !== 0) {
        el.classList.remove('stat-up', 'stat-down');
        void el.offsetWidth; 
        if (newValue > oldVal) {
            el.classList.add('stat-up');
        } else {
            el.classList.add('stat-down');
        }
        setTimeout(() => {
            el.classList.remove('stat-up', 'stat-down');
        }, 800);
    }
}

function updateSignalUI() {
    const p = inventoryData.profile;
    if (!p) return;
    els.statSignal.innerText = `${p.signal}%`;
    els.statSignal.style.color = p.signal > 50 ? '#00ff00' : (p.signal > 20 ? '#ffcc00' : '#ff3333');
    checkLowSignal(p.signal);
}

function checkLowSignal(signal) {
    if (signal < 20) {
        document.body.classList.add('low-signal');
        pushLog('CRITICAL SIGNAL LOSS. SYSTEM UNSTABLE.', 'ERR');
    } else {
        document.body.classList.remove('low-signal');
    }
}

function pushLog(text, type = "SYS") {
    const el = document.getElementById('action-log-text');
    const pEl = document.querySelector('.log-prefix');
    if (!el || !pEl) return;
    pEl.innerText = `[${type}]`;
    el.innerText = text;
}

// === УМНЫЙ ШЛЮЗ ИКОНОК ===
function getItemIcon(item, fallbackType) {
    if (item && item.image_url && !item.image_url.includes('IMG/None') && item.image_url !== 'IMG/.png') {
        return `<img src="${item.image_url}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px; filter: drop-shadow(0 0 2px rgba(255,255,255,0.2));">`;
    }
    return ICONS[fallbackType] || ICONS['default'];
}

// === РЕНДЕР КУКЛЫ (СЛОТЫ ЭКИПИРОВКИ) ===
function renderDoll() {
    const slots = ['head', 'weapon', 'body', 'software', 'artifact'];
    slots.forEach(slot => {
        const item = inventoryData.equipped[slot];
        const slotEl = document.getElementById(`slot-${slot}`);
        if (!slotEl) return;

        slotEl.setAttribute('data-slot-type', slot);

        const currentItemId = slotEl.getAttribute('data-item-id');
        const newItemId = item ? String(item.item_id) : 'empty';

        if (currentItemId === newItemId) return;
        slotEl.setAttribute('data-item-id', newItemId);

        if (item) {
            const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
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

            const iconContent = getItemIcon(item, slot);

            slotEl.innerHTML = `
                <div class="equipped-item ${extraClass}" style="${extraStyle} width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; cursor:pointer; background: rgba(0,0,0,0.6);">
                    <div style="width: 32px; height: 32px; display:flex; align-items:center; justify-content:center;">
                        ${iconContent}
                    </div>
                    <div style="font-size: 8px; color: ${color}; text-align: center; margin-top:5px; word-wrap: break-word; padding: 0 2px;">${item.name}</div>
                </div>`;
            slotEl.onclick = () => openUnequipModal(slot, item);
        } else {
            let rawIcon = ICONS[slot] || ICONS['default'];
            let modifiedIcon = rawIcon.replace('<img ', '<img style="opacity: 0.1; filter: grayscale(1);" ');
            slotEl.innerHTML = `<div style="width: 32px; height: 32px; margin: auto; display:flex; align-items:center; justify-content:center; height:100%;">${modifiedIcon}</div>`;
            slotEl.onclick = null;
        }
    });
}

// === РЕНДЕР ИНВЕНТАРЯ (СПИСОК ЛУТА) ===
function renderInventory() {
    els.inventoryList.innerHTML = '';
    
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
        
        const iconContent = getItemIcon(item, item.type);

        card.innerHTML = `
            <div class="item-icon" style="color:${color}; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">${iconContent}</div>
            <div class="item-details" style="flex: 1; margin-left: 10px;">
                <div class="item-name" style="color:${color}; font-weight: bold; font-size: 14px; text-shadow: 0 0 5px ${color};">${item.name}</div>
                <div class="item-rarity" style="opacity:0.8; font-size:10px; color: #a0a0a0; text-transform: uppercase;">${RARITY_NAMES[item.rarity] || item.rarity}</div>
            </div>
            ${item.quantity > 1 ? `<div class="item-qty" style="color:#000; background:#66FCF1; padding:2px 6px; border-radius:4px; font-size:12px; font-weight: bold;">x${item.quantity}</div>` : ''}
        `;
        card.onclick = () => openItemModal(item);
        fragment.appendChild(card);
    });

    els.inventoryList.appendChild(fragment);
}

// === ЛОГИКА ВКЛАДОК (ФИЛЬТРЫ) ===
document.querySelectorAll('.tab[data-filter]').forEach(tab => {
    tab.addEventListener('click', (e) => {
        document.querySelectorAll('.tab[data-filter]').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentFilter = tab.getAttribute('data-filter');
        if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
        renderInventory();
    });
});

// === МОДАЛЬНЫЕ ОКНА И ДЕЙСТВИЯ ===
function openItemModal(item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    
    els.modalIcon.innerHTML = `<div style="width: 80px; height: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">${getItemIcon(item, item.type)}</div>`;
    
    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = RARITY_NAMES[item.rarity] || item.rarity;
    els.modalRarity.style.color = color;
    els.modalDesc.innerHTML = item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>';
    
    els.modalActions.innerHTML = '';
    
    if (['weapon', 'head', 'body', 'software', 'artifact'].includes(item.type)) {
        const btnEquip = document.createElement('button');
        btnEquip.className = 'action-btn';
        btnEquip.innerText = 'ЭКИПИРОВАТЬ';
        btnEquip.onclick = () => {
            if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
            performAction('/api/inventory/equip', {uid, item_id: item.item_id});
        };
        els.modalActions.appendChild(btnEquip);
    }
    
    if (item.type === 'consumable') {
        const btnUse = document.createElement('button');
        btnUse.className = 'action-btn';
        btnUse.innerText = 'ИСПОЛЬЗОВАТЬ';
        btnUse.onclick = () => performAction('/api/inventory/use', {uid, item_id: item.item_id});
        els.modalActions.appendChild(btnUse);
    }

    const btnDismantle = document.createElement('button');
    btnDismantle.className = 'action-btn';
    btnDismantle.style.borderColor = '#ff3333';
    btnDismantle.style.color = '#ff3333';
    btnDismantle.innerText = 'РАЗОБРАТЬ';
    btnDismantle.onclick = () => {
        if (window.tg && tg.showConfirm) {
            tg.showConfirm(`Разобрать объект [${item.name}] на компоненты?`, (confirmed) => {
                if (confirmed) performAction('/api/inventory/dismantle', {uid, item_id: item.item_id});
            });
        } else {
            performAction('/api/inventory/dismantle', {uid, item_id: item.item_id});
        }
    };
    els.modalActions.appendChild(btnDismantle);

    els.modal.classList.add('active');
}

function openUnequipModal(slot, item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    
    els.modalIcon.innerHTML = `<div style="width: 80px; height: 80px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">${getItemIcon(item, slot)}</div>`;
    
    els.modalTitle.innerText = item.name;
    els.modalTitle.style.color = color;
    els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    els.modalRarity.innerText = 'ПОДКЛЮЧЕНО К ЯДРУ';
    els.modalRarity.style.color = '#00ff41';
    els.modalDesc.innerHTML = 'Инициировать извлечение модуля?';
    
    els.modalActions.innerHTML = '';
    const btnUnequip = document.createElement('button');
    btnUnequip.className = 'action-btn';
    btnUnequip.innerText = 'ИЗВЛЕЧЬ';
    btnUnequip.onclick = () => {
        if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        performAction('/api/inventory/unequip', {uid, slot: slot});
    };
    els.modalActions.appendChild(btnUnequip);

    els.modal.classList.add('active');
}

if (els.modalClose) {
    els.modalClose.onclick = () => {
        if(window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
        els.modal.classList.remove('active');
    };
}

// === ОТПРАВКА ДЕЙСТВИЯ НА БЭКЕНД ===
async function performAction(endpoint, payload) {
    els.modal.classList.remove('active');
    const res = await fetchWithLock(endpoint, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });
    
    if (res && res.ok) {
        if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        pushLog('ТРАНЗАКЦИЯ УСПЕШНА', 'SYS');
        loadData(); 
    } else {
        if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
        pushLog('ОТКАЗ СИСТЕМЫ', 'ERR');
        if(window.tg && tg.showAlert) tg.showAlert('Операция отклонена сервером.');
    }
}

// === НАВИГАЦИЯ И ВИДИМОСТЬ (С КНОПКОЙ НАЗАД) ===
tg.MainButton.text = "ЗАКРЫТЬ ТЕРМИНАЛ";
tg.MainButton.show();
tg.MainButton.onClick(() => tg.close());

// Слушатель нативной кнопки "Назад" в Telegram
if (tg.BackButton) {
    tg.BackButton.onClick(() => {
        showView('view-nexus');
    });
}

function showView(viewId) {
    document.querySelectorAll('.view-panel').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.add('active');
        if (window.tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred('light');
        }
        
        // Логика кнопки "Назад": показываем везде, кроме Нексуса
        if (viewId === 'view-nexus') {
            if (tg.BackButton) tg.BackButton.hide();
        } else {
            if (tg.BackButton) tg.BackButton.show();
        }
    }
}

function renderNexusGrid() {
    const gridContent = document.getElementById('nexus-grid-tiles');
    if (!gridContent) return;

    const profile = inventoryData.profile || {};
    const items = inventoryData.items || [];

    let raidCooldownStr = '';
    if (profile.raid_cooldown && new Date() < new Date(profile.raid_cooldown)) {
        const diffMs = new Date(profile.raid_cooldown) - new Date();
        const diffMins = Math.ceil(diffMs / 60000);
        raidCooldownStr = `<div class="nexus-tile-status nexus-tile-cooldown"><img src="IMG/eidos_time-cycle.svg">${diffMins}м</div>`;
    }

    const tilesData = [
        { id: 'view-inventory', label: 'ПРОФИЛЬ', icon: 'eidos_demiurge-user.svg', reqLevel: 1, status: '' },
        { id: 'view-inventory', label: 'ИНВЕНТАРЬ', icon: 'eidos_inventory-cache.svg', reqLevel: 1, status: `<div class="nexus-tile-status">${items.length}</div>` },
        { id: 'view-shop', label: 'МАРКЕТ', icon: 'eidos_black-market.svg', reqLevel: 2, status: `<div class="nexus-tile-status">${profile.biocoins || 0}</div>` },
        { id: 'view-raids', label: 'РЕЙДЫ', icon: 'eidos_raid-boss.svg', reqLevel: 3, status: raidCooldownStr },
        { id: 'view-arena', label: 'АРЕНА', icon: 'eidos_arena-pvp.svg', reqLevel: 5, status: '' },
        { id: 'view-social', label: 'СЕТЬ', icon: 'eidos_neuro-brain.svg', reqLevel: 1, status: '' }
    ];

    const fragment = document.createDocumentFragment();

    tilesData.forEach((tile) => {
        const tileEl = document.createElement('div');
        tileEl.className = 'nexus-tile stagger-boot';

        const pLevel = profile.level || 1;
        if (pLevel < tile.reqLevel) {
            tileEl.classList.add('sector-locked');
            tileEl.innerHTML = `
                <img class="nexus-tile-icon" src="IMG/eidos_security-key.svg" alt="LOCKED">
                <div class="nexus-tile-label" style="color:#888;">ДОСТУП ЗАКРЫТ</div>
            `;
            tileEl.addEventListener('click', () => {
                if(window.tg && tg.showAlert) tg.showAlert(`ТРЕБУЕТСЯ УРОВЕНЬ ${tile.reqLevel} ДЛЯ ДОСТУПА.`);
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
            });
        } else {
            tileEl.innerHTML = `
                ${tile.status}
                <img class="nexus-tile-icon" src="IMG/${tile.icon}" alt="${tile.label}">
                <div class="nexus-tile-label" style="color:#fff; text-shadow: 0 0 5px #66FCF1;">${tile.label}</div>
            `;
            tileEl.addEventListener('click', () => {
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
                showView(tile.id);
            });
        }
        fragment.appendChild(tileEl);
    });

    gridContent.innerHTML = '';
    gridContent.appendChild(fragment);
}
