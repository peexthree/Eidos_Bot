import re

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'r') as f:
    text = f.read()

start_pattern = r'private val anomalies = listOf\('
end_pattern = r'suspend fun handleAnomalyChoice\(uid: Long, optionId: String\).*?checkDeath\(uid\)\n    }'

# Split and replace
new_code = """    private val dynamicAnomalies = com.example.eidos.data.GameData.EVENTS.map { event ->
        val options = when (event.type) {
            "trap" -> listOf(
                AnomalyOption("accept", "ПРИНЯТЬ УДАР", "Потерять ${event.value} Сигнала"),
                AnomalyOption("dodge", "УВЕРНУТЬСЯ", "Попытка уклониться (шанс)")
            )
            "heal" -> listOf(
                AnomalyOption("accept", "ПРИНЯТЬ", "Восстановить ${event.value} Сигнала"),
                AnomalyOption("ignore", "ИГНОРИРОВАТЬ", "Пройти мимо")
            )
            "loot" -> listOf(
                AnomalyOption("accept", "ЗАБРАТЬ", "Получить +${event.value} BC/XP"),
                AnomalyOption("ignore", "ИГНОРИРОВАТЬ", "Оставить лежать")
            )
            else -> listOf(
                AnomalyOption("accept", "ПРОДОЛЖИТЬ", "Идти дальше")
            )
        }
        AnomalyEvent(event.id.toString(), event.text, options)
    }

    private val anomalies get() = dynamicAnomalies

    fun getAnomaly(id: String) = anomalies.find { it.id == id }

    suspend fun handleAnomalyChoice(uid: Long, optionId: String) {
        val session = dao.getRaidSession(uid) ?: return
        val player = dao.getPlayer(uid) ?: return
        val anomalyId = session.current_anomaly_id ?: return
        val gameEvent = com.example.eidos.data.GameData.EVENTS.find { it.id.toString() == anomalyId } ?: return

        if (optionId == "ignore") {
            dao.insertRaidSession(session.copy(current_anomaly_id = null))
            log(uid, "ОБХОД: Вы проигнорировали аномалию.", "info")
            return
        }

        when (gameEvent.type) {
            "trap" -> {
                if (optionId == "accept") {
                    val damage = gameEvent.value
                    dao.insertRaidSession(session.copy(signal = maxOf(0, session.signal - damage), current_anomaly_id = null))
                    damageArmorHelmet(uid, damage)
                    log(uid, "⚡ ПРЯМОЙ УДАР: -${damage} Сигнала.", "error")
                } else if (optionId == "dodge") {
                    val roll = (0..100).random()
                    val activeStats = getActiveStats(uid)
                    val dodgeChance = 30 + activeStats.luck
                    if (roll < dodgeChance) {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                        log(uid, "✨ УСПЕХ: Вы уклонились от ловушки!", "info")
                    } else {
                        val damage = (gameEvent.value * 1.5).toInt()
                        dao.insertRaidSession(session.copy(signal = maxOf(0, session.signal - damage), current_anomaly_id = null))
                        damageArmorHelmet(uid, damage)
                        log(uid, "💥 ПРОВАЛ: Уклонение не удалось! -${damage} Сигнала.", "error")
                    }
                }
            }
            "heal" -> {
                if (optionId == "accept") {
                    dao.updatePlayer(player.copy(hp = minOf(player.max_hp, player.hp + gameEvent.value)))
                    dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    log(uid, "💚 ВОССТАНОВЛЕНИЕ: +${gameEvent.value} HP.", "info")
                }
            }
            "loot" -> {
                if (optionId == "accept") {
                    val coins = gameEvent.value.toLong()
                    val xp = gameEvent.value.toLong()
                    dao.insertRaidSession(session.copy(
                        buffer_coins = session.buffer_coins + coins,
                        buffer_xp = session.buffer_xp + xp,
                        current_anomaly_id = null
                    ))
                    log(uid, "📦 НАЙДЕНО: +$coins BC, +$xp XP.", "loot")
                }
            }
            else -> {
                dao.insertRaidSession(session.copy(current_anomaly_id = null))
                log(uid, "💡 ИССЛЕДОВАНИЕ ПРОДОЛЖАЕТСЯ.", "info")
            }
        }
        checkDeath(uid)
    }"""

# Do replacement via regex
import re
new_text = re.sub(start_pattern + r'.*?' + end_pattern, new_code, text, flags=re.DOTALL)
with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'w') as f:
    f.write(new_text)

