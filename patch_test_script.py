import re

with open('test_script.py', 'r') as f:
    content = f.read()

content = content.replace('await page.wait_for_selector("#profile-name", timeout=15000)', 'await page.wait_for_selector("#nexus-grid-content", timeout=15000)')

with open('test_script.py', 'w') as f:
    f.write(content)
