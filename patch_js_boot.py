import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Remove the default call to loadData() at the end
js = re.sub(r'loadData\(\);\s*$', 'showBootSequence();\n', js)

# Inject Ghost Stats and Sounds into drag events
new_dragstart = """
        if (isEquippable) {
            card.ondragstart = (e) => {
                const data = {
                    action: 'equip',
                    inv_id: item.id,
                    item_id: item.item_id,
                    type: item.type
                };
                e.dataTransfer.setData('application/json', JSON.stringify(data));

                // Audio Context Haptics
                if(window.tg && tg.HapticFeedback) {
                    if(item.rarity === 'legendary') tg.HapticFeedback.notificationOccurred('success');
                    else tg.HapticFeedback.impactOccurred('medium');
                }

                // Thermal Emission
                if(item.rarity === 'legendary') card.classList.add('legendary-glow');

                // Action Log
                pushLog(`[PREPARING TO EQUIP]: ${item.name}`, 'SYNC');
            };

            card.ondragend = (e) => {
                card.classList.remove('legendary-glow');
                clearPreviewStats();
            };
        }
"""

js = re.sub(r'        if \(isEquippable\) \{\n            card\.ondragstart = \(e\) => \{.*?\};\n        \}', new_dragstart, js, flags=re.DOTALL)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
