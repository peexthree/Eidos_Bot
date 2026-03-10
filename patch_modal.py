import re

with open('frontend_v2/src/components/ItemModal.jsx', 'r') as f:
    content = f.read()

content = content.replace(
    "const isEquipped = item && Object.values(equipped).some(val => \n    val === item.id || (val && typeof val === 'object' && val.item_id === item.id)\n  );",
    "const itemId = item?.id || item?.item_id;\n  const isEquipped = itemId && Object.values(equipped).some(val => \n    val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))\n  );"
)

content = content.replace(
    "val === item.id || (val && typeof val === 'object' && val.item_id === item.id)",
    "val === itemId || (val && typeof val === 'object' && (val.item_id === itemId || val.id === itemId))"
)

content = content.replace(
    "item_id: item.id",
    "item_id: itemId"
)

with open('frontend_v2/src/components/ItemModal.jsx', 'w') as f:
    f.write(content)

print("Patched ItemModal.jsx")
