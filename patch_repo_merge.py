import re

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'r') as f:
    content = f.read()

merge_logic = """
    suspend fun mergeItems(uid: Long, itemId: String) {
        val meta = getItemMetadata(itemId) ?: return
        val inventory = dao.getInventoryFlow(uid).first()
        val item = inventory.find { it.item_id == itemId }

        if (item == null || item.quantity < 3) {
            log(uid, "Для синтеза требуется 3 шт. ${meta.name}.", "error")
            return
        }

        val allItems = getAllItemsMetadata()
        val nextRarity = when(meta.rarity) {
            "common" -> "uncommon"
            "uncommon" -> "rare"
            "rare" -> "epic"
            "epic" -> "legendary"
            "legendary" -> "relic"
            else -> return
        }

        val possibleUpgrades = allItems.filter { it.type == meta.type && it.rarity == nextRarity }
        if (possibleUpgrades.isEmpty()) {
            log(uid, "Нет доступных улучшений для этого типа.", "error")
            return
        }

        val upgradedItem = possibleUpgrades.random()

        dao.removeInventory(uid, itemId, 3)
        dao.addInventory(uid, upgradedItem.id, 1)
        log(uid, "УСПЕШНЫЙ СИНТЕЗ! 3x ${meta.name} -> 1x ${upgradedItem.name}", "success")
    }
"""

if "suspend fun mergeItems" not in content:
    content = content.replace("suspend fun dismantleItem", merge_logic + "\n    suspend fun dismantleItem")

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'w') as f:
    f.write(content)
