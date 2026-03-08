import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Make forceCloseLoader available on window for testing by appending it
if "function forceCloseLoader()" in content:
    content += "\nwindow.forceCloseLoader = forceCloseLoader;\n"

with open('static/js/app.js', 'w') as f:
    f.write(content)
