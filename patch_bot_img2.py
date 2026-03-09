import re

with open('config.py', 'r') as f:
    config_content = f.read()

# Let's ensure file_id is added to ITEMS_INFO
patch_code = """
# Auto-inject image IDs into ITEMS_INFO
for item_id, image_id in ITEM_IMAGES.items():
    if item_id in ITEMS_INFO:
        ITEMS_INFO[item_id]['file_id'] = image_id
"""

if "Auto-inject image IDs into ITEMS_INFO" not in config_content:
    config_content += "\n" + patch_code
    with open('config.py', 'w') as f:
        f.write(config_content)
        print("config updated")
