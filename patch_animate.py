import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

old_func = """function animateStatChange(el, newValue) {
    if (!el) return;

}"""

new_func = """function animateStatChange(el, newValue) {
    if (!el) return;
    const oldVal = parseInt(el.innerText) || 0;
    el.innerText = newValue;
    if (newValue !== oldVal && oldVal !== 0) {
        el.classList.remove('stat-up', 'stat-down');
        void el.offsetWidth; // force reflow
        if (newValue > oldVal) {
            el.classList.add('stat-up');
        } else {
            el.classList.add('stat-down');
        }
        setTimeout(() => {
            el.classList.remove('stat-up', 'stat-down');
        }, 800);
    }
}"""

content = content.replace(old_func, new_func)

with open('static/js/app.js', 'w') as f:
    f.write(content)

print("Updated animateStatChange.")
