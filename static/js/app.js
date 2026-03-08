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

// Константы раритетности
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
const MIN_LOADING_TIME = 8000; 
const startTime = Date.now();
let dataLoaded = false;
let introFinished = false;

// === ЛОГИКА ЗАГРУЗКИ ДАННЫХ ===
async function loadData() {
    // Включаем программный лоадер (старый) только если данные грузятся долго (>500ms)
    const loaderTimeout = setTimeout(() => {
        if (!dataLoaded) els.loading.style.display = 'flex';
    }, 500);

    try {
        const res = await fetch(`/api/inventory?uid=${uid}`);
        if (!res.ok) throw new Error('API Error');
        inventoryData = await res.json();

        renderProfile();
        renderDoll();
        renderInventory();
        
        dataLoaded = true;
        clearTimeout(loaderTimeout);
        checkAndRemoveLoader(); // Проверяем, можно ли убирать заставку
    } catch (e) {
        console.error('Fetch error:', e);
        tg.showAlert('Сбой соединения с сервером Eidos.');
    }
}

// Проверка: и видео доиграло, и данные есть
function checkAndRemoveLoader() {
    const elapsedTime = Date.now() - startTime;
    if (dataLoaded && elapsedTime >= MIN_LOADING_TIME) {
        executeLoaderFade();
    } else if (dataLoaded) {
        // Ждем остаток времени видео
        setTimeout(executeLoaderFade, MIN_LOADING_TIME - elapsedTime);
    }
}

function executeLoaderFade() {
    const loader = document.getElementById('eidos-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.remove();
            els.loading.style.display = 'none'; // Убираем и старый лоадер тоже
            pushLog('СИСТЕМА АКТИВИРОВАНА.', 'SYS');
        }, 800);
    }
}

// Принудительный пропуск (Skip)
window.forceCloseLoader = function() {
    if (dataLoaded) {
        executeLoaderFade();
    } else {
        // Если данные еще не пришли, просто прячем видео и показываем старый лоадер
        document.getElementById('eidos-loader').style.display = 'none';
        els.loading.style.display = 'flex';
    }
};

// === ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ DOM ===
document.addEventListener('DOMContentLoaded', () => {
    // 1. Запуск NEXUS GRID
    setupNexusGrid();
    
    // 2. Принудительный старт видео (лечим "черный экран")
    const vfxVideo = document.querySelector('#eidos-loader video');
    if (vfxVideo) {
        vfxVideo.play().catch(() => {
            console.log("Автоплей заблокирован. Ожидание клика.");
        });
    }

    // 3. Запуск загрузки данных
    loadData();
});

// === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ОСТАВЛЕНЫ БЕЗ ИЗМЕНЕНИЙ) ===

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
    els.profileName.innerText = p.name || 'Аноним';
    els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    els.profileFaction.innerText = p.faction || 'Неизвестно';
    if (p.avatar_url) els.profileAvatar.src = p.avatar_url;

    animateStatChange(els.statAtk, p.atk || 0);
    animateStatChange(els.statDef, p.def || 0);
    animateStatChange(els.statLuck, p.luck || 0);
    updateSignalUI();

    const xp = p.xp || 0;
    const nXp = p.next_xp || 100;
    els.xpText.innerText = `${xp} / ${nXp} XP`;
    let pct = Math.min((xp / nXp) * 100, 100);
    els.xpBar.style.width = pct + '%';
}

function animateStatChange(el, newValue) {
    if (!el) return;

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

// Рендер куклы и инвентаря (сокращено для краткости, используй свои рабочие функции)
function renderDoll() { /* Твоя логика отрисовки слотов */ }
function renderInventory() { /* Твоя логика отрисовки карточек */ }

// Главная кнопка Telegram
tg.MainButton.text = "ЗАКРЫТЬ ИНТЕРФЕЙС";
tg.MainButton.show();
tg.MainButton.onClick(() => tg.close());
