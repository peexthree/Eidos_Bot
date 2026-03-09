const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// --- ИНЪЕКЦИЯ В НАТИВНЫЙ ИНТЕРФЕЙС TELEGRAM ---
// Окрашиваем хедер и фон самого Telegram в цвет нашей пустоты
tg.setHeaderColor('#030405');
tg.setBackgroundColor('#030405');

// Блокируем свайп вниз, который случайно закрывает WebApp (работает на новых версиях API)
if (tg.disableVerticalSwipes) {
    tg.disableVerticalSwipes();
}


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

// DOM Элементы (ТВЕРДОЕ ИСПРАВЛЕНИЕ: Геттеры защищают от падения, если элемент не найден)
const els = {
    get loading() { return document.getElementById('loading-overlay'); },
    get profileName() { return document.getElementById('profile-name'); },
    get profileLvl() { return document.getElementById('profile-lvl'); },
    get profileFaction() { return document.getElementById('profile-faction'); },
    get profileAvatar() { return document.getElementById('profile-avatar'); },
    get statAtk() { return document.getElementById('stat-atk'); },
    get statDef() { return document.getElementById('stat-def'); },
    get statLuck() { return document.getElementById('stat-luck'); },
    get statSignal() { return document.getElementById('stat-signal'); },
    get xpBar() { return document.getElementById('xp-bar'); },
    get xpText() { return document.getElementById('xp-text'); },
    get inventoryList() { return document.getElementById('inventory-list'); },
    get dollContainer() { return document.getElementById('doll-container'); },
    get tabs() { return document.querySelectorAll('.tab'); },
    get modal() { return document.getElementById('item-modal'); },
    get modalIcon() { return document.getElementById('modal-icon'); },
    get modalTitle() { return document.getElementById('modal-title'); },
    get modalRarity() { return document.getElementById('modal-rarity'); },
    get modalDesc() { return document.getElementById('modal-desc'); },
    get modalActions() { return document.getElementById('modal-actions'); },
    get modalClose() { return document.getElementById('modal-close'); }
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
        if (els.loading) els.loading.style.display = 'flex';
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
    if (els.profileName) els.profileName.innerText = p.name || 'ОБЪЕКТ НЕИЗВЕСТЕН';
    if (els.profileLvl) els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    if (els.profileFaction) els.profileFaction.innerText = p.faction || 'ФРАКЦИЯ: НЕЙТРАЛ';
    if (els.profileAvatar && p.avatar_url) els.profileAvatar.src = p.avatar_url;

    animateStatChange(els.statAtk, p.atk || 0);
    animateStatChange(els.statDef, p.def || 0);
    animateStatChange(els.statLuck, p.luck || 0);
    updateSignalUI();

    const xp = p.xp || 0;
    const nXp = p.next_xp || 100;
    if (els.xpText) els.xpText.innerText = `${xp} / ${nXp} ОПЫТ`;
    let pct = Math.min((xp / nXp) * 100, 100);
    if (els.xpBar) els.xpBar.style.width = pct + '%';
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
    if (els.statSignal) {
        els.statSignal.innerText = `${p.signal}%`;
        els.statSignal.style.color = p.signal > 50 ? '#00ff00' : (p.signal > 20 ? '#ffcc00' : '#ff3333');
    }
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
        return `<img class="full-size-img" src="${item.image_url}">`;
    }
    return `<div class="icon-fallback">${ICONS[fallbackType] || ICONS['default']}</div>`;
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

            // Modified renderDoll
            let imgHtml = '';
            if (item.type && item.type.startsWith('eidos_')) {
                imgHtml = `<img src="https://api.telegram.org/file/bot${window.tgBotToken || ''}/${item.item_id}" alt="item" style="width: 100%; height: 100%; object-fit: cover;">`;
            } else {
                imgHtml = `<img src="/api/inventory/image?item_id=${item.item_id}" alt="item" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='IMG/eidos_sys-warning.svg'">`;
            }
            slotEl.innerHTML = imgHtml;
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
    if (!els.inventoryList) return;
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
    
    // Большое изображение
    if (els.modalIcon) els.modalIcon.innerHTML = `<div class="modal-large-image">${getItemIcon(item, item.type)}</div>`;
    
    if (els.modalTitle) {
        els.modalTitle.innerText = item.name;
        els.modalTitle.style.color = color;
        els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    }
    if (els.modalRarity) {
        els.modalRarity.innerText = RARITY_NAMES[item.rarity] || item.rarity;
        els.modalRarity.style.color = color;
    }

    // Формируем блок статов
    let statsHtml = '';
    if (item.stats) {
        if (item.stats.atk) statsHtml += `<span style="color:#ff4d4d;">ATK: +${item.stats.atk}</span> `;
        if (item.stats.def) statsHtml += `<span style="color:#4da6ff;">DEF: +${item.stats.def}</span> `;
        if (item.stats.luck) statsHtml += `<span style="color:#00ff41;">LCK: +${item.stats.luck}</span> `;
    }
    const finalDesc = (item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>').replace(/\n/g, '<br>');

    if (els.modalDesc) els.modalDesc.innerHTML = `<div class="modal-stats">${statsHtml}</div><div class="modal-lore">${finalDesc}</div>`;

    if (els.modalActions) {
        els.modalActions.innerHTML = '';
        
        if (['weapon', 'head', 'body', 'software', 'artifact'].includes(item.type)) {
            // --- 4. Neural-Link Overcharge ---
            const btnEquipWrap = document.createElement('div');
            btnEquipWrap.className = 'equip-overcharge-wrap';

            const btnEquip = document.createElement('button');
            btnEquip.className = 'action-btn overcharge-btn';
            btnEquip.innerText = 'ЭКИПИРОВАТЬ (УДЕРЖИВАТЬ)';

            const overchargeRing = document.createElement('svg');
            overchargeRing.className = 'overcharge-ring';
            overchargeRing.innerHTML = '<circle cx="50%" cy="50%" r="48%" stroke-width="4%" fill="none"></circle>';

            btnEquipWrap.appendChild(btnEquip);
            btnEquipWrap.appendChild(overchargeRing);
            els.modalActions.appendChild(btnEquipWrap);

            let overchargeTimer = null;
            let overchargeProgress = 0;
            let isOvercharging = false;
            let lastHaptic = 0;

            const updateOvercharge = () => {
                if (!isOvercharging) return;
                overchargeProgress += 2; // ~50 frames for 100% -> ~800ms

                const circle = overchargeRing.querySelector('circle');
                if (circle) {
                    const circumference = 2 * Math.PI * 48; // assuming r=48% of 100
                    const dashoffset = circumference - (overchargeProgress / 100) * circumference;
                    circle.style.strokeDasharray = `${circumference}% ${circumference}%`;
                    circle.style.strokeDashoffset = `${dashoffset}%`;
                }

                // Haptic ticks
                if (overchargeProgress - lastHaptic >= 20) {
                    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
                    lastHaptic = overchargeProgress;
                    btnEquipWrap.style.transform = `scale(${1 - overchargeProgress * 0.0005}) rotate(${(Math.random()-0.5)*2}deg)`;
                }

                if (overchargeProgress >= 100) {
                    isOvercharging = false;
                    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('heavy');
                    btnEquipWrap.classList.add('overcharged');
                    setTimeout(() => {
                        performAction('/api/inventory/equip', {uid, item_id: item.item_id});
                    }, 200);
                } else {
                    overchargeTimer = requestAnimationFrame(updateOvercharge);
                }
            };

            const startOvercharge = (e) => {
                e.preventDefault();
                isOvercharging = true;
                overchargeProgress = 0;
                lastHaptic = 0;
                btnEquipWrap.classList.add('active');
                overchargeTimer = requestAnimationFrame(updateOvercharge);
            };

            const stopOvercharge = () => {
                isOvercharging = false;
                overchargeProgress = 0;
                btnEquipWrap.classList.remove('active');
                btnEquipWrap.style.transform = 'scale(1) rotate(0deg)';
                const circle = overchargeRing.querySelector('circle');
                if (circle) circle.style.strokeDashoffset = `301%`; // reset roughly
                if (overchargeTimer) cancelAnimationFrame(overchargeTimer);
            };

            btnEquip.addEventListener('touchstart', startOvercharge, {passive: false});
            btnEquip.addEventListener('mousedown', startOvercharge);
            btnEquip.addEventListener('touchend', stopOvercharge);
            btnEquip.addEventListener('mouseup', stopOvercharge);
            btnEquip.addEventListener('mouseleave', stopOvercharge);
        }
        
        if (item.type === 'consumable') {
            const btnUse = document.createElement('button');
            btnUse.className = 'action-btn';
            btnUse.innerText = 'ИСПОЛЬЗОВАТЬ';
            btnUse.onclick = () => performAction('/api/inventory/use', {uid, item_id: item.item_id});
            els.modalActions.appendChild(btnUse);
        }

        // --- 2. Haptic-Synced Matter Grinder ---
        const grinderContainer = document.createElement('div');
        grinderContainer.className = 'grinder-container';

        const grinderZone = document.createElement('div');
        grinderZone.className = 'grinder-zone';
        grinderZone.innerHTML = '<span>ПЕРЕТАЩИТЕ СЮДА</span>';

        const grinderDrag = document.createElement('div');
        grinderDrag.className = 'grinder-drag';
        grinderDrag.innerText = 'РАЗОБРАТЬ';

        grinderContainer.appendChild(grinderZone);
        grinderContainer.appendChild(grinderDrag);
        els.modalActions.appendChild(grinderContainer);

        let grinderStartY = 0;
        let grinderDragY = 0;
        const grinderMaxDrag = 60; // How far to drag down
        let isGrinderDragging = false;

        // Remove previous handlers if any
        if (window._grinderMoveHandler) document.removeEventListener('pointermove', window._grinderMoveHandler);
        if (window._grinderUpHandler) document.removeEventListener('pointerup', window._grinderUpHandler);

        grinderDrag.addEventListener('pointerdown', (e) => {
            isGrinderDragging = true;
            grinderStartY = e.clientY;
            grinderDrag.classList.add('dragging');
            grinderZone.classList.add('active-zone');
            if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
            e.preventDefault();
        });

        window._grinderMoveHandler = (e) => {
            if (!isGrinderDragging) return;
            grinderDragY = Math.max(0, Math.min(e.clientY - grinderStartY, grinderMaxDrag));
            grinderDrag.style.transform = `translateY(${grinderDragY}px)`;

            // Haptic feedback tension
            if (grinderDragY > 0 && Math.floor(grinderDragY) % 15 === 0) {
                if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
            }

            if (grinderDragY >= grinderMaxDrag) {
                grinderZone.classList.add('danger-zone');
                grinderZone.innerHTML = '<span style="color:#ff3333;text-shadow:0 0 5px #ff3333;">РАСЩЕПИТЬ!</span>';
            } else {
                grinderZone.classList.remove('danger-zone');
                grinderZone.innerHTML = '<span>ПЕРЕТАЩИТЕ СЮДА</span>';
            }
        };

        window._grinderUpHandler = (e) => {
            if (!isGrinderDragging) return;
            isGrinderDragging = false;
            grinderDrag.classList.remove('dragging');
            grinderZone.classList.remove('active-zone');

            if (grinderDragY >= grinderMaxDrag) {
                if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('heavy');
                grinderDrag.style.opacity = '0';
                grinderDrag.style.transform = `translateY(${grinderMaxDrag}px) scale(0)`;
                grinderZone.classList.add('explode-zone');

                setTimeout(() => {
                    performAction('/api/inventory/dismantle', {uid, item_id: item.item_id});
                }, 300);
            } else {
                grinderDrag.style.transform = 'translateY(0)';
                if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
            }
        };

        document.addEventListener('pointermove', window._grinderMoveHandler);
        document.addEventListener('pointerup', window._grinderUpHandler);
    }

    if (els.modal) els.modal.classList.add('active');

    // --- 1. Gyro-Kinetic Hologram Inspection ---
    if (item.rarity === 'epic' || item.rarity === 'legendary') {
        if (els.modalIcon) els.modalIcon.classList.add('holo-inspect');
        if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
            DeviceOrientationEvent.requestPermission().then(p => {
                if (p === 'granted') window.addEventListener('deviceorientation', handleGyro);
            }).catch(console.error);
        } else {
            window.addEventListener('deviceorientation', handleGyro);
        }
    } else {
        if (els.modalIcon) els.modalIcon.classList.remove('holo-inspect');
        window.removeEventListener('deviceorientation', handleGyro);
    }
}

function openUnequipModal(slot, item) {
    if (window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    const color = RARITY_COLORS[item.rarity] || RARITY_COLORS['common'];
    
    if (els.modalIcon) els.modalIcon.innerHTML = `<div class="modal-large-image">${getItemIcon(item, slot)}</div>`;
    
    if (els.modalTitle) {
        els.modalTitle.innerText = item.name;
        els.modalTitle.style.color = color;
        els.modalTitle.style.textShadow = `0 0 8px ${color}`;
    }
    
    if (els.modalRarity) {
        els.modalRarity.innerText = 'ПОДКЛЮЧЕНО К ЯДРУ';
        els.modalRarity.style.color = '#00ff41';
    }

    let statsHtml = '';
    if (item.stats) {
        if (item.stats.atk) statsHtml += `<span style="color:#ff4d4d;">ATK: +${item.stats.atk}</span> `;
        if (item.stats.def) statsHtml += `<span style="color:#4da6ff;">DEF: +${item.stats.def}</span> `;
        if (item.stats.luck) statsHtml += `<span style="color:#00ff41;">LCK: +${item.stats.luck}</span> `;
    }
    const finalDesc = (item.description || '<i style="color:#555;">ДАННЫЕ ОТСУТСТВУЮТ.</i>').replace(/\n/g, '<br>');

    if (els.modalDesc) els.modalDesc.innerHTML = `<div class="modal-stats">${statsHtml}</div><div class="modal-lore">${finalDesc}</div><div style="margin-top:10px; color:#ffcc00;">Инициировать извлечение модуля?</div>`;
    
    if (els.modalActions) {
        els.modalActions.innerHTML = '';
        const btnUnequip = document.createElement('button');
        btnUnequip.className = 'action-btn';
        btnUnequip.innerText = 'ИЗВЛЕЧЬ';
        btnUnequip.onclick = () => {
            if (window.tg && tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
            performAction('/api/inventory/unequip', {uid, slot: slot});
        };
        els.modalActions.appendChild(btnUnequip);
    }

    if (els.modal) els.modal.classList.add('active');
}

if (els.modalClose) {
    els.modalClose.onclick = () => {
        if(window.tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
        if (els.modal) els.modal.classList.remove('active');
        window.removeEventListener('deviceorientation', handleGyro); // Убираем гироскоп при закрытии
    };
}

// === ОТПРАВКА ДЕЙСТВИЯ НА БЭКЕНД ===
async function performAction(endpoint, payload) {
    if (els.modal) els.modal.classList.remove('active');
    window.removeEventListener('deviceorientation', handleGyro); // Убираем гироскоп
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
if (tg.MainButton) {
    tg.MainButton.text = "ЗАКРЫТЬ ТЕРМИНАЛ";
    tg.MainButton.show();
    tg.MainButton.onClick(() => tg.close());
}

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
            if (tg.BackButton && window.Telegram.WebApp.isExpanded) tg.BackButton.show();
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

// ТВЕРДОЕ ИСПРАВЛЕНИЕ: Добавлена недостающая функция гироскопа, из-за которой падал скрипт
window.handleGyro = function(event) {
    const icon = document.querySelector('.holo-inspect .modal-large-image');
    if (!icon) return;
    const tiltX = Math.max(-20, Math.min(20, (event.beta || 0) - 45));
    const tiltY = Math.max(-20, Math.min(20, (event.gamma || 0)));
    icon.style.transform = `perspective(600px) rotateX(${-tiltX}deg) rotateY(${tiltY}deg)`;
};
