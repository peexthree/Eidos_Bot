import re

with open('frontend_v2/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("INITIALIZING NEURAL LINK...", "ESTABLISHING NEURAL LINK...")

with open('frontend_v2/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
