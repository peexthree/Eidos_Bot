import re

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'r') as f:
    content = f.read()

# Fix Unresolved reference 'removeInventory' -> decrease quantity or delete if 0
# Fix Unresolved reference 'addInventory' -> increase quantity or insert if not present

helper_methods = """
    private suspend fun addInventory(uid: Long, itemId: String, amount: Int) {
        val inventory = dao.getInventoryFlow(uid).first()
        val item = inventory.find { it.item_id == itemId }
        if (item != null) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity + amount))
        } else {
            dao.insertInventoryItem(InventoryItem(uid = uid, item_id = itemId, quantity = amount, is_equipped = false))
        }
    }

    private suspend fun removeInventory(uid: Long, itemId: String, amount: Int) {
        val inventory = dao.getInventoryFlow(uid).first()
        val item = inventory.find { it.item_id == itemId }
        if (item != null) {
            if (item.quantity > amount) {
                dao.updateInventoryItem(item.copy(quantity = item.quantity - amount))
            } else {
                dao.deleteInventoryItem(item)
            }
        }
    }
"""

if "private suspend fun addInventory" not in content:
    content = content.replace("class GameRepository(private val dao: EidosDao) {", "class GameRepository(private val dao: EidosDao) {\n" + helper_methods)

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'w') as f:
    f.write(content)
