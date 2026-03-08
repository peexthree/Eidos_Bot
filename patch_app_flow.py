import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Replace MIN_LOADING_TIME = 8000
content = content.replace("const MIN_LOADING_TIME = 8000;", "const MIN_LOADING_TIME = 3000;")

# Make sure executeLoaderFade calls showView('view-nexus')
old_fade = """function executeLoaderFade() {
    const loader = document.getElementById('eidos-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.remove();
            if (els.loading) els.loading.style.display = 'none';
            pushLog('СИСТЕМА АКТИВИРОВАНА.', 'SYS');
        }, 800);
    }
}"""

new_fade = """function executeLoaderFade() {
    const loader = document.getElementById('eidos-loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => {
            loader.remove();
            if (els.loading) els.loading.style.display = 'none';
            pushLog('СИСТЕМА АКТИВИРОВАНА.', 'SYS');
            showView('view-nexus');
        }, 800);
    }
}"""

content = content.replace(old_fade, new_fade)

# The ID of nexus grid was changed from 'nexus-grid-content' to 'nexus-grid-tiles' in HTML. Let's fix JS:
if "getElementById('nexus-grid-content')" in content:
    content = content.replace("getElementById('nexus-grid-content')", "getElementById('nexus-grid-tiles')")

# Also the class is view-panel, not view in HTML. But showView removes/adds active on .view elements:
if "document.querySelectorAll('.view')" in content:
    # let's just make sure both .view and .view-panel are handled or we revert to .view in HTML.
    # Instruction was: class="view-panel active".
    # Let's update showView to handle .view-panel as well, or just select by ID.
    pass

old_show_view = """function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));"""

new_show_view = """function showView(viewId) {
    document.querySelectorAll('.view, .view-panel').forEach(v => v.classList.remove('active'));"""

content = content.replace(old_show_view, new_show_view)

with open('static/js/app.js', 'w') as f:
    f.write(content)

print("Flow JS updated")
