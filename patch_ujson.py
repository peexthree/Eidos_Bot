import os
import glob
import re

def replace_in_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replacing simple `import json` with `import ujson as json`
    new_content = re.sub(r'^import json$', 'import ujson as json', content, flags=re.MULTILINE)

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Patched {filepath}")

files = glob.glob('*.py') + glob.glob('modules/**/*.py', recursive=True)
for file in files:
    replace_in_file(file)
