import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Add view switching and nexus grid rendering
js_addition = """
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.add('active');
        if (window.tg && tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred('light');
        }
    }
}

function renderNexusGrid() {
    const gridContent = document.getElementById('nexus-grid-content');
    if (!gridContent) return;

    const profile = inventoryData.profile || {};
    const items = inventoryData.items || [];

    // Calculate raid cooldown string if any
    let raidCooldownStr = '';
    if (profile.raid_cooldown && new Date() < new Date(profile.raid_cooldown)) {
        const diffMs = new Date(profile.raid_cooldown) - new Date();
        const diffMins = Math.ceil(diffMs / 60000);
        raidCooldownStr = `<div class="nexus-tile-status nexus-tile-cooldown"><img src="IMG/eidos_time-cycle.svg">${diffMins}m</div>`;
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

    tilesData.forEach((tile, index) => {
        const tileEl = document.createElement('div');
        tileEl.className = 'nexus-tile stagger-boot';

        // Access Control Logic
        const pLevel = profile.level || 1;
        if (pLevel < tile.reqLevel) {
            tileEl.classList.add('sector-locked');
            tileEl.innerHTML = `
                <img class="nexus-tile-icon" src="IMG/eidos_security-key.svg" alt="LOCKED">
                <div class="nexus-tile-label">УРОВЕНЬ ${tile.reqLevel}</div>
            `;
            tileEl.addEventListener('click', () => {
                if(window.tg && tg.showAlert) tg.showAlert('УРОВЕНЬ ДОСТУПА НЕДОСТАТОЧЕН');
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
            });
        } else {
            tileEl.innerHTML = `
                ${tile.status}
                <img class="nexus-tile-icon" src="IMG/${tile.icon}" alt="${tile.label}">
                <div class="nexus-tile-label">${tile.label}</div>
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
"""

if "function showView(viewId)" not in content:
    content += "\n" + js_addition

# Ensure we call renderNexusGrid after loadData
if "renderNexusGrid();" not in content:
    content = content.replace("renderProfile();", "renderProfile();\n        renderNexusGrid();")

with open('static/js/app.js', 'w') as f:
    f.write(content)
