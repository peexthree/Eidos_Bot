import re

with open('verify_webapp.py', 'r') as f:
    content = f.read()

# Since we removed bottom-nav, we must click the nexus tiles instead to navigate
content = content.replace('await page.click("div[data-target=\'view-shop\']")', 'await page.click(".nexus-tile:nth-child(3)")')
content = content.replace('await page.click("div[data-target=\'view-social\']")', 'await page.click(".nexus-tile:nth-child(6)")')

with open('verify_webapp.py', 'w') as f:
    f.write(content)
