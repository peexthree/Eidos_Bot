import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Make forceCloseLoader available on window for testing
if "function forceCloseLoader()" in content:
    content = content.replace("function forceCloseLoader() {", "window.forceCloseLoader = forceCloseLoader;\nfunction forceCloseLoader() {")

with open('static/js/app.js', 'w') as f:
    f.write(content)
