import re

with open('database.py', 'r') as f:
    content = f.read()

# Replace garbage
content = re.sub(r'# === ВОССТАНОВЛЕННЫЕ ФУНКЦИИ КОНТЕНТА ===.*?def get_user_equipment', 'def get_user_equipment', content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)
