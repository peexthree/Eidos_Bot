import re

file_path = 'static/inventory.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_js = "assets/index-CPhRTA1A.js"
new_css = "assets/index-2ux9vvNm.css"

content = re.sub(r'assets/index-.*?\.js', new_js, content)
content = re.sub(r'assets/index-.*?\.css', new_css, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("inventory.html updated with new hashes.")
