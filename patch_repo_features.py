import re

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'r') as f:
    content = f.read()

features = """
    suspend fun buyShadowBrokerItem(uid: Long, itemId: String) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(itemId) ?: return
        val xpCost = meta.price * 5
        
        if (player.xp < xpCost) {
            log(uid, "Недостаточно XP.", "error")
            return
        }
        dao.updatePlayer(player.copy(xp = player.xp - xpCost))
        dao.addInventory(uid, itemId, 1)
        log(uid, "Куплен редкий предмет: ${meta.name}", "success")
    }

    suspend fun gambleHP(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val hpCost = (player.max_hp * 0.3).toInt()
        
        if (player.hp <= hpCost) {
            log(uid, "Недостаточно Сигнала для сделки.", "error")
            return
        }
        
        dao.updatePlayer(player.copy(hp = player.hp - hpCost))
        val rareItems = getAllItemsMetadata().filter { it.rarity == "rare" || it.rarity == "epic" }
        if (rareItems.isNotEmpty() && Math.random() > 0.5) {
            val wonItem = rareItems.random()
            dao.addInventory(uid, wonItem.id, 1)
            log(uid, "Сделка удалась! Получено: ${wonItem.name}", "success")
        } else {
            log(uid, "Сделка провалилась. Вы потеряли Сигнал.", "error")
        }
    }

    suspend fun gambleLoot(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val cost = 500
        
        if (player.biocoin < cost) {
            log(uid, "Недостаточно BC для сделки.", "error")
            return
        }
        
        dao.updatePlayer(player.copy(biocoin = player.biocoin - cost, hp = player.max_hp))
        log(uid, "Сделка удалась. Сигнал полностью восстановлен.", "success")
    }

    suspend fun onPvpWin(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val reward = 500
        dao.updatePlayer(player.copy(biocoin = player.biocoin + reward))
        log(uid, "Успешный взлом. Украдено $reward BC.", "success")
    }

    suspend fun onPvpLose(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val penalty = 200
        dao.updatePlayer(player.copy(biocoin = maxOf(0, player.biocoin - penalty)))
        log(uid, "Взлом провален. ICE списал $penalty BC.", "error")
    }
"""

if "suspend fun buyShadowBrokerItem" not in content:
    content = content.replace("suspend fun buyItem", features + "\n    suspend fun buyItem")

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'w') as f:
    f.write(content)
