import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Make sure we declare lastStats globally if it doesn't exist
if "let lastStats = " not in content:
    content = content.replace("let currentFilter = 'all';", "let currentFilter = 'all';\nlet lastStats = {atk: 0, def: 0, luck: 0, signal: 100};")

old_render = """function renderProfile() {
    const p = inventoryData.profile;
    if (!p) return;
    els.profileName.innerText = p.name || 'Аноним';
    els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    els.profileFaction.innerText = p.faction || 'Неизвестно';
    els.profileAvatar.src = p.avatar_url || 'IMG/default_avatar.png';
    document.getElementById('profile-biocoins').innerText = p.biocoins || 0;

    // Статы
    els.statAtk.innerText = p.atk || 0;
    els.statDef.innerText = p.def || 0;
    els.statLuck.innerText = p.luck || 0;
    els.statSignal.innerText = (p.signal || 100) + '%';"""

new_render = """function renderProfile() {
    const p = inventoryData.profile;
    if (!p) return;
    els.profileName.innerText = p.name || 'Аноним';
    els.profileLvl.innerText = `Lvl ${p.level || 1}`;
    els.profileFaction.innerText = p.faction || 'Неизвестно';
    els.profileAvatar.src = p.avatar_url || 'IMG/default_avatar.png';
    document.getElementById('profile-biocoins').innerText = p.biocoins || 0;

    // Функция для анимации статов
    const updateStat = (el, key, newVal) => {
        const oldVal = lastStats[key];
        el.innerText = key === 'signal' ? newVal + '%' : newVal;
        if (oldVal !== undefined && newVal !== oldVal) {
            el.classList.remove('stat-up', 'stat-down');
            // Принудительный reflow
            void el.offsetWidth;
            if (newVal > oldVal) {
                el.classList.add('stat-up');
            } else {
                el.classList.add('stat-down');
            }
            setTimeout(() => { el.classList.remove('stat-up', 'stat-down'); }, 800);
        }
        lastStats[key] = newVal;
    };

    // Статы
    updateStat(els.statAtk, 'atk', p.atk || 0);
    updateStat(els.statDef, 'def', p.def || 0);
    updateStat(els.statLuck, 'luck', p.luck || 0);
    updateStat(els.statSignal, 'signal', p.signal || 100);"""

content = content.replace(old_render, new_render)

with open('static/js/app.js', 'w') as f:
    f.write(content)

print("Profile logic updated for micro-animations.")
