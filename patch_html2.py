import re

with open('static/inventory.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace loading overlay with boot sequence
new_loading = """    <!-- Boot Sequence (Loading Screen) -->
    <div id="loading-overlay">
        <div class="boot-terminal">
            <div id="boot-text"></div>
            <div class="cursor">_</div>
        </div>
    </div>"""

html = re.sub(r'    <!-- Loading Screen -->\n    <div id="loading-overlay">.*?</div>\n    </div>', new_loading, html, flags=re.DOTALL)

# Add Action Log terminal to the bottom
new_action_log = """    <!-- Action Log Terminal (Fixed Bottom) -->
    <div class="action-log-terminal" id="action-log-terminal">
        <div class="log-content">
            <span class="log-prefix">[SYS]</span> <span id="action-log-text">SYSTEM INITIALIZED. WAITING FOR INPUT...</span>
        </div>
    </div>"""

html = html.replace('<!-- Bottom Navigation Bar -->', new_action_log + '\n\n    <!-- Bottom Navigation Bar -->')

with open('static/inventory.html', 'w', encoding='utf-8') as f:
    f.write(html)
