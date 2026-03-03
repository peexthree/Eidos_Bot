with open('config.py', 'r') as f:
    content = f.read()

content = content.replace(
"""EQUIPMENT_DB = {""",
"""EQUIPMENT_DB = {
    # ==========================
    # АБСОЛЮТ (VIP)
    # ==========================
    "eidos_shard": {
        "name": "👁 СИНХРОНИЗАТОР АБСОЛЮТА",
        "slot": "eidos_shard", "atk": 0, "def": 0, "luck": 0, "price": 0,
        "desc": "[ЭЙДОС]: Дает особый статус. Создан из чистого опыта."
    },"""
)

with open('config.py', 'w') as f:
    f.write(content)
