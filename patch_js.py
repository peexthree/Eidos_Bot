import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add signal stat to elements
js = re.sub(r'statLuck: document.getElementById\(\'stat-luck\'\),', r"statLuck: document.getElementById('stat-luck'),\n    statSignal: document.getElementById('stat-signal'),", js)

# Update renderProfile
def replacement_profile(match):
    return """function renderProfile() {
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
}"""

js = re.sub(r'function renderProfile\(\) \{.*?(?=function renderDoll)', replacement_profile, js, flags=re.DOTALL)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
