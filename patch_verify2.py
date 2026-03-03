with open('verify_updates.py', 'r') as f:
    content = f.read()

content = content.replace(
"""--- SETUP USER 123456 ---""",
"""db.init_db()

--- SETUP USER 123456 ---"""
)

with open('verify_updates.py', 'w') as f:
    f.write(content)
