import re
import os

html_path = 'static/inventory.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the built CSS and JS files
assets_dir = 'static/assets'
css_files = [f for f in os.listdir(assets_dir) if f.endswith('.css')]
js_files = [f for f in os.listdir(assets_dir) if f.endswith('.js')]

index_css = next((f for f in css_files if f.startswith('index-')), None)
index_js = next((f for f in js_files if f.startswith('index-')), None)
vendor_js = next((f for f in js_files if f.startswith('vendor-')), None)
query_js = next((f for f in js_files if f.startswith('query-')), None)
motion_js = next((f for f in js_files if f.startswith('motion-')), None)

if index_css:
    content = re.sub(
        r'<link rel="stylesheet" crossorigin href="/assets/index-.*?\.css">',
        f'<link rel="stylesheet" crossorigin href="/assets/{index_css}">',
        content
    )

if index_js:
    content = re.sub(
        r'<script type="module" crossorigin src="/assets/index-.*?\.js"></script>',
        f'<script type="module" crossorigin src="/assets/{index_js}"></script>',
        content
    )

if vendor_js:
    content = re.sub(
        r'<link rel="modulepreload" crossorigin href="/assets/vendor-.*?\.js">',
        f'<link rel="modulepreload" crossorigin href="/assets/{vendor_js}">',
        content
    )

if query_js:
    content = re.sub(
        r'<link rel="modulepreload" crossorigin href="/assets/query-.*?\.js">',
        f'<link rel="modulepreload" crossorigin href="/assets/{query_js}">',
        content
    )

if motion_js:
    content = re.sub(
        r'<link rel="modulepreload" crossorigin href="/assets/motion-.*?\.js">',
        f'<link rel="modulepreload" crossorigin href="/assets/{motion_js}">',
        content
    )


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated HTML with new hashes: JS: {index_js}, CSS: {index_css}")
