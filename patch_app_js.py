import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace handleDrop error handling
new_handleDrop = """async function handleDrop(e, slotType) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');

    try {
        const dataStr = e.dataTransfer.getData('application/json');
        if (!dataStr) return;
        const data = JSON.parse(dataStr);

        if (data.action === 'equip') {
            // Normalize types
            let itemType = data.type;
            if (itemType === 'helmet') itemType = 'head';
            if (itemType === 'armor') itemType = 'body';

            // Check slot match
            if (itemType !== slotType) {
                if(window.tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');

                // Red flash effect
                document.body.style.boxShadow = 'inset 0 0 50px #ff3333';
                setTimeout(() => document.body.style.boxShadow = 'none', 300);

                if(window.tg) tg.showAlert(`Неверный слот! Этот предмет типа: ${data.type}`);
                else alert(`Неверный слот! Этот предмет типа: ${data.type}`);
                return;
            }
            await equipItemAPI(data.inv_id, data.item_id);
        }
    } catch (err) {
        console.error('Drop error', err);
    }
}"""

js = re.sub(r'async function handleDrop.*?catch \(err\) \{[^}]+\}\n\}', new_handleDrop, js, flags=re.DOTALL)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
