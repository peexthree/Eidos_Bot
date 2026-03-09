import re

with open('static/js/app.js', 'r') as f:
    js_content = f.read()

# Replace openItemModal
old_modal_start = "function openItemModal(item) {"
# Let's write a better patch using regex or exact block replacement
