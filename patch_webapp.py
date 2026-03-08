import re

# --- 1. Patch HTML ---
filepath = 'static/inventory.html'
with open(filepath, 'r') as f:
    content = f.read()

# Replace Navigation Tabs
old_nav = """    <nav class="bottom-nav">
        <div class="nav-item active" data-target="view-inventory">
            <div class="nav-icon"><img src="IMG/eidos_demiurge-user.svg" alt="Профиль"></div>
            <div class="nav-label">ПРОФИЛЬ</div>
        </div>
        <div class="nav-item" data-target="view-shop">
            <div class="nav-icon"><img src="IMG/eidos_black-market.svg" alt="Магазин"></div>
            <div class="nav-label">МАГАЗИН</div>
        </div>
        <div class="nav-item" data-target="view-craft">
            <div class="nav-icon"><img src="IMG/eidos_forge-craft.svg" alt="Крафт"></div>
            <div class="nav-label">КРАФТ</div>
        </div>
        <div class="nav-item" data-target="view-raids">
            <div class="nav-icon"><img src="IMG/eidos_raid-boss.svg" alt="Рейды"></div>
            <div class="nav-label">РЕЙДЫ</div>
        </div>
        <div class="nav-item" data-target="view-social">
            <div class="nav-icon"><img src="IMG/eidos_comm-link.svg" alt="Сеть"></div>
            <div class="nav-label">СЕТЬ</div>
        </div>
    </nav>"""

new_nav = """    <nav class="bottom-nav">
        <div class="nav-item active" data-target="view-inventory">
            <div class="nav-icon"><img src="IMG/nav_head-psycho.svg" alt="Профиль"></div>
            <div class="nav-label">PSYCHO-PROFILE</div>
        </div>
        <div class="nav-item" data-target="view-shop">
            <div class="nav-icon"><img src="IMG/eidos_inventory-cache.svg" alt="Кэш"></div>
            <div class="nav-label">CACHE</div>
        </div>
        <div class="nav-item" data-target="view-social">
            <div class="nav-icon"><img src="IMG/eidos_terminal-log.svg" alt="Терминал"></div>
            <div class="nav-label">TERMINAL</div>
        </div>
    </nav>"""

content = content.replace(old_nav, new_nav)

with open(filepath, 'w') as f:
    f.write(content)

# --- 2. Patch CSS ---
filepath_css = 'static/css/style.css'
with open(filepath_css, 'r') as f:
    css_content = f.read()

# Add styles for CRT and translation
css_content += """
.sys-scanline {
    opacity: 0.05 !important;
}

.terminal-text {
    text-shadow: 0 0 5px rgba(0,255,65,0.4);
}

.views-container {
    transform: translate3d(0,0,0);
}

/* Skeleton Loaders */
.skeleton-box {
    background-color: #333;
    animation: pulse 1.5s infinite;
    border-radius: 4px;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
"""

# Update colors
css_content = css_content.replace('--tg-theme-button-color: #45a29e;', '--tg-theme-button-color: #00ff41;')
css_content = css_content.replace('--tg-theme-bg-color: #0b0c10;', '--tg-theme-bg-color: #0a0a0a;')

with open(filepath_css, 'w') as f:
    f.write(css_content)

# --- 3. Patch JS ---
filepath_js = 'static/js/app.js'
with open(filepath_js, 'r') as f:
    js_content = f.read()

# Throttle and lock
lock_code = """
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
"""

js_content = js_content.replace('let inventoryData =', lock_code + '\nlet inventoryData =')
js_content = js_content.replace("await fetch('/api/inventory/equip'", "await fetchWithLock('/api/inventory/equip'")
js_content = js_content.replace("await fetch('/api/inventory/unequip'", "await fetchWithLock('/api/inventory/unequip'")

with open(filepath_js, 'w') as f:
    f.write(js_content)

print("WebApp Refactored.")
