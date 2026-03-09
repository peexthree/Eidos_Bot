import re

file_path = 'frontend_v2/src/components/EquipDoll.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace getItem logic to return slotData directly if it has an image_url or name.
# The issue says: "Ensure CharacterDoll.jsx checks for LOWERCASE keys (weapon, body, head, software) as sent by the backend's enriched_equipped dict. Render the item's image_url when found."
# In EquipDoll.jsx, `slotData` represents `equipped?.head` for example, which is the enriched object from the backend (or string ID, or basic object).
new_get_item = """  const getItem = (slotData) => {
    if (!slotData) return undefined;

    // If it's already an enriched item from the backend, use it directly!
    if (typeof slotData === 'object' && (slotData.image_url || slotData.name)) {
        return slotData;
    }

    let targetId = slotData;
    if (typeof slotData === 'object' && slotData.item_id) {
       targetId = slotData.item_id;
    } else if (typeof slotData === 'object' && slotData.id) {
       targetId = slotData.id;
    }

    // Fallback: search in inventory
    return inventory.find(i => String(i?.id) === String(targetId));
  };"""

content = re.sub(r'  const getItem = \(slotData\) => \{[\s\S]*?  \};', new_get_item, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("EquipDoll.jsx patched.")
