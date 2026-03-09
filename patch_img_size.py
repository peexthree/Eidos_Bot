import re

with open('static/css/style.css', 'r') as f:
    css_content = f.read()

# Make sure items in the inventory grid scale nicely
# add styling to .inv-item .full-size-img
css_additions = """
.inv-item .full-size-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
}
"""

if ".inv-item .full-size-img" not in css_content:
    css_content += "\n" + css_additions

with open('static/css/style.css', 'w') as f:
    f.write(css_content)

print("CSS inventory icons scaled.")
