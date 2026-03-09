import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Make sure onClick handles 'INVENTORY' correctly
# If INVENTORY is clicked, we probably want to setView('INVENTORY') rather than open modal.
# Let's adjust the row for INVENTORY:
# <HexButton title="ИНВЕНТАРЬ" iconUrl="/IMG/eidos_inventory.svg" tgImageUrl={getImg("inventory")} onClick={(img) => { setView('INVENTORY'); }} />

content = content.replace(
    '<HexButton title="ИНВЕНТАРЬ" iconUrl="/IMG/eidos_inventory.svg" tgImageUrl={getImg("inventory")} onClick={(img) => setView(\'INVENTORY\')} />',
    '<HexButton title="ИНВЕНТАРЬ" iconUrl="/IMG/eidos_inventory.svg" tgImageUrl={getImg("inventory")} onClick={(img) => { setView(\'INVENTORY\'); }} />'
)

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)
