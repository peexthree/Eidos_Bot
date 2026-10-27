package io.eidos.zerolayer.data

import android.content.Context
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import java.util.concurrent.ConcurrentHashMap
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.decodeFromStream
import kotlinx.serialization.encodeToString
import java.util.Date
import java.text.SimpleDateFormat

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

object ShadowBrokerPrices {
    fun getXpPrice(meta: GameRepository.ItemMetadata): Long {
        val r = meta.rarity.lowercase()
        val name = meta.name
        val isCursedOrRelic = r in listOf("cursed", "relic") || name.contains("💀") || name.contains("👁") || name.contains("🔴") || meta.type == "cursed"
        val isLegendary = r == "legendary" || name.contains("🟠")
        val isEpicOrChip = r == "epic" || meta.type == "chip"

        return when {
            isCursedOrRelic -> 50000L
            isLegendary -> 20000L
            isEpicOrChip -> 8000L
            else -> 3000L
        }
    }

    fun getBcPrice(meta: GameRepository.ItemMetadata): Long {
        val r = meta.rarity.lowercase()
        val name = meta.name
        val isCursedOrRelic = r in listOf("cursed", "relic") || name.contains("💀") || name.contains("👁") || name.contains("🔴") || meta.type == "cursed"
        val isLegendary = r == "legendary" || name.contains("🟠")
        val isEpicOrChip = r == "epic" || meta.type == "chip"

        return when {
            isCursedOrRelic -> 25000L
            isLegendary -> 10000L
            isEpicOrChip -> 4000L
            else -> 1500L
        }
    }
}

class GameRepository(private val context: Context, private val originalDao: EidosDao) {

    private val dao = object : EidosDao by originalDao {
        override suspend fun insertPlayer(player: Player) {
            val updated = player.copy(
                state_version = player.state_version + 1,
                updated_at = System.currentTimeMillis()
            )
            originalDao.insertPlayer(updated)
        }

        override suspend fun updatePlayer(player: Player) {
            val updated = player.copy(
                state_version = player.state_version + 1,
                updated_at = System.currentTimeMillis()
            )
            originalDao.updatePlayer(updated)
        }
    }

    private val dbMutex = Mutex()

    // ⚡ IN-MEMORY OVERDRIVE & OVERCHARGE STATE (ZERO ROOM MIGRATION)
    private val overdriveChargeMap = ConcurrentHashMap<Long, Int>()
    private val overchargeTierMap = ConcurrentHashMap<Long, Int>()

    private val _overdriveChargeFlow = MutableStateFlow(0)
    val overdriveChargeFlow: StateFlow<Int> = _overdriveChargeFlow.asStateFlow()

    private val _overchargeTierFlow = MutableStateFlow(0)
    val overchargeTierFlow: StateFlow<Int> = _overchargeTierFlow.asStateFlow()

    private val _combatEventFlow = MutableSharedFlow<CombatVisualEvent>(extraBufferCapacity = 16)
    val combatEventFlow: SharedFlow<CombatVisualEvent> = _combatEventFlow.asSharedFlow()

    fun getOverdriveCharge(uid: Long): Int = overdriveChargeMap.getOrDefault(uid, 0)
    suspend fun setOverdriveCharge(uid: Long, charge: Int) {
        val clamped = charge.coerceIn(0, 100)
        overdriveChargeMap[uid] = clamped
        _overdriveChargeFlow.value = clamped
        val player = dao.getPlayer(uid)
        if (player != null && player.overdriveCharge != clamped) {
            dao.updatePlayer(player.copy(overdriveCharge = clamped))
        }
    }

    fun getOverchargeTier(uid: Long): Int = overchargeTierMap.getOrDefault(uid, 0)
    suspend fun setOverchargeTier(uid: Long, tier: Int) {
        val clamped = tier.coerceIn(0, 3)
        overchargeTierMap[uid] = clamped
        _overchargeTierFlow.value = clamped
        val player = dao.getPlayer(uid)
        if (player != null && player.overchargeTier != clamped) {
            dao.updatePlayer(player.copy(overchargeTier = clamped))
        }
    }

    suspend fun boostOvercharge(uid: Long): Int = dbMutex.withLock {
        val session = dao.getRaidSession(uid) ?: return@withLock 0
        val current = getOverchargeTier(uid)
        if (current >= io.eidos.zerolayer.domain.combat.CombatEngine.MAX_OVERCHARGE_TIER) {
            log(uid, "🔥 [ПРОТОКОЛ ПЕРЕГРУЗКИ]: Достигнут максимум (Уровень 3 / x2.5)!", "info")
            return@withLock current
        }
        val newTier = current + 1
        setOverchargeTier(uid, newTier)
        val mult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(newTier)
        log(uid, "🔥 [ПРОТОКОЛ ПЕРЕГРУЗКИ АКТИВИРОВАН]: Уровень $newTier/3! Множитель наград x$mult (+${newTier * 50}%), атака монстров +${newTier * 20}%!", "loot")
        return@withLock newTier
    }

    suspend fun handleLevelUpRewards(uid: Long, oldLevel: Int, newLevel: Int) {
        if (newLevel <= oldLevel) return
        val bonusShards = (oldLevel + 1..newLevel).sumOf { lvl -> PlayerProgressManager.getLevelInfo(lvl).rewardShards }
        if (bonusShards > 0) {
            addInventory(uid, "eidos_shard", bonusShards)
            log(uid, "💎 [РУБЕЖ ЯДРА]: Получено +$bonusShards Осколков Эйдоса за достижение Level $newLevel!", "loot")
        }
    }

    suspend fun deductShards(uid: Long, cost: Int): Boolean = dbMutex.withLock {
        val items = dao.getInventoryFlow(uid).first().filter { it.item_id == "eidos_shard" }
        val total = items.sumOf { it.quantity }
        if (total < cost) return@withLock false
        var remaining = cost
        for (item in items) {
            if (remaining <= 0) break
            if (item.quantity <= remaining) {
                remaining -= item.quantity
                dao.deleteInventoryItem(item)
            } else {
                dao.updateInventoryItem(item.copy(quantity = item.quantity - remaining))
                remaining = 0
            }
        }
        return@withLock true
    }

    private suspend fun addInventory(uid: Long, itemId: String, amount: Int) = dbMutex.withLock {
        val inventory = dao.getInventoryFlow(uid).first()
        val meta = getItemMetadata(itemId)
        val isEquipment = ItemSlotUtils.getSlotForItem(itemId, meta) != null
        if (!isEquipment) {
            val existing = inventory.find { it.item_id == itemId && !it.is_equipped }
            if (existing != null) {
                dao.updateInventoryItem(existing.copy(quantity = existing.quantity + amount))
            } else {
                dao.insertInventoryItem(InventoryItem(uid = uid, item_id = itemId, quantity = amount, is_equipped = false))
            }
        } else {
            repeat(amount) {
                dao.insertInventoryItem(InventoryItem(uid = uid, item_id = itemId, quantity = 1, is_equipped = false))
            }
        }
    }

    private suspend fun removeInventory(uid: Long, itemId: String, amount: Int) = dbMutex.withLock {
        val inventory = dao.getInventoryFlow(uid).first()
        val item = inventory.find { it.item_id == itemId && !it.is_equipped } ?: inventory.find { it.item_id == itemId }
        if (item != null) {
            if (item.quantity > amount) {
                dao.updateInventoryItem(item.copy(quantity = item.quantity - amount))
            } else {
                dao.deleteInventoryItem(item)
            }
        }
    }


    private val json = Json { ignoreUnknownKeys = true }

    suspend fun seedIfNeeded() {
        val existingVillains = dao.getVillainsForLevel(100)
        if (existingVillains.isEmpty()) {
            // Seed Villains
            val villainsData = context.assets.open("villains.json").use { stream ->
                json.decodeFromStream<VillainsRoot>(stream).villains
            }
            dao.insertVillains(villainsData.map {
                VillainStatic(
                    name = it.name,
                    level = it.level,
                    hp = it.hp,
                    atk = it.atk,
                    def = it.def,
                    xp = it.xp.toInt(),
                    coin = it.coin.toInt(),
                    desc = it.desc,
                    image = it.image
                )
            })

            // Seed Content
            val contentMap = context.assets.open("content.json").use { stream ->
                json.decodeFromString<Map<String, List<ContentItem>>>(stream.bufferedReader().readText())
            }
            val contentList = mutableListOf<GameContent>()
            contentMap.forEach { (level, items) ->
                items.forEach { item ->
                    contentList.add(GameContent(
                        level = level,
                        type = item.type,
                        path = item.path,
                        text = item.text
                    ))
                }
            }
            dao.insertContent(contentList)
            log(getActiveUid(), "SYSTEM: Neural assets synchronized.", "info")
        }
    }

    data class ItemMetadata(
        val id: String,
        val name: String,
        val type: String, // weapon, armor, head, chip, consumable, material
        val rarity: String, // common, uncommon, rare, epic, legendary, relic, cursed
        val icon: String = "❓",
        val multiplier: Float = 1.0f,
        val bonusAttack: Int = 0,
        val bonusDefense: Int = 0,
        val bonusLuck: Int = 0,
        val hpRestore: Int = 0,
        val energyRestore: Int = 0,
        val price: Int = 100,
        val description: String = "",
        val reqLevel: Int = 1
        )

    
    @kotlinx.serialization.Serializable
    data class ItemJson(
        val name: String = "Предмет",
        val slot: String = "",
        val type: String = "",
        val atk: Int = 0,
        val def: Int = 0,
        val luck: Int = 0,
        val price: Int = 0,
        val desc: String = ""
    )

    private val itemsMetadata: List<ItemMetadata> by lazy {
        try {
            val itemsMap = context.assets.open("items.json").use { stream ->
                json.decodeFromString<Map<String, ItemJson>>(stream.bufferedReader().readText())
            }
            itemsMap.map { (id, jsonItem) ->
                val slotType = when {
                    jsonItem.slot.isNotEmpty() -> jsonItem.slot
                    jsonItem.type.isNotEmpty() -> jsonItem.type
                    else -> "misc"
                }
                val rarity = when {
                    jsonItem.name.contains("⚪️") -> "common"
                    jsonItem.name.contains("🔵") -> "uncommon"
                    jsonItem.name.contains("🟣") -> "rare"
                    jsonItem.name.contains("🟠") -> "epic"
                    jsonItem.name.contains("🔴") -> "legendary"
                    jsonItem.name.contains("👁") -> "relic"
                    jsonItem.name.contains("💀") || jsonItem.slot == "cursed" -> "cursed"
                    else -> "common"
                }
                val calculatedReqLevel = 1

                ItemMetadata(
                    id = id,
                    name = jsonItem.name,
                    type = slotType,
                    rarity = rarity,
                    icon = jsonItem.name.filter { it.isSurrogate() || it.code > 128 }.take(1).ifEmpty { "❓" },
                    multiplier = 1.0f,
                    bonusAttack = jsonItem.atk,
                    bonusDefense = jsonItem.def,
                    bonusLuck = jsonItem.luck,
                    hpRestore = if (jsonItem.desc.contains("Восстанавливает")) 50 else 0,
                    energyRestore = if (jsonItem.desc.contains("энергии")) 50 else 0,
                    price = jsonItem.price,
                    description = jsonItem.desc,
                    reqLevel = calculatedReqLevel
                )
            }
        } catch (e: Exception) {
            e.printStackTrace()
            emptyList()
        }
    }

    fun getAllItemsMetadata() = itemsMetadata

    fun getItemMetadata(id: String) = itemsMetadata.find { it.id == id }

    fun isRedLoot(meta: ItemMetadata?): Boolean {
        if (meta == null) return false
        return meta.rarity in listOf("cursed", "relic") ||
               meta.name.contains("🔴") ||
               meta.name.contains("💀") ||
               meta.name.contains("👁") ||
               meta.type == "cursed"
    }

    fun rollCursedChestLoot(): ItemMetadata? {
        val all = getAllItemsMetadata().filter { it.id != "biocoin" }
        val redList = all.filter { isRedLoot(it) }
        val legendaryList = all.filter { !isRedLoot(it) && (it.rarity == "legendary" || it.name.contains("🟠")) }
        val otherList = all.filter { !isRedLoot(it) && it.rarity != "legendary" && !it.name.contains("🟠") }

        val roll = (0..99).random()
        return when {
            roll < 10 -> redList.randomOrNull() ?: legendaryList.randomOrNull() ?: all.randomOrNull()
            roll < 75 -> legendaryList.randomOrNull() ?: otherList.randomOrNull() ?: all.randomOrNull()
            else -> otherList.randomOrNull() ?: all.randomOrNull()
        }
    }

    fun rollCursedOrLegendaryLoot(): ItemMetadata? {
        val all = getAllItemsMetadata().filter { it.id != "biocoin" }
        val cursedList = all.filter { isRedLoot(it) || it.rarity.equals("cursed", ignoreCase = true) }
        val legendaryList = all.filter { it.rarity.equals("legendary", ignoreCase = true) }

        val isCursedRoll = (0..1).random() == 0
        return if (isCursedRoll) {
            cursedList.randomOrNull() ?: legendaryList.randomOrNull() ?: all.randomOrNull()
        } else {
            legendaryList.randomOrNull() ?: cursedList.randomOrNull() ?: all.randomOrNull()
        }
    }

    fun rollNormalLoot(): ItemMetadata? {
        val normalList = getAllItemsMetadata().filter { it.id != "biocoin" && !isRedLoot(it) }
        return normalList.randomOrNull()
    }

    data class AnomalyEvent(
        val id: String,
        val text: String,
        val options: List<AnomalyOption>
    )

    data class AnomalyOption(
        val id: String,
        val text: String,
        val description: String
    )

        private val dynamicAnomalies = io.eidos.zerolayer.data.GameData.EVENTS.map { event ->
        val options = when (event.type) {
            "portal_3ways" -> listOf(
                AnomalyOption("portal_red", "🔴 КРАСНЫЙ ПОРТАЛ (Бездна)", "Прыгнуть на +50м в глубину! (Риск -20 HP или сорвать куш)"),
                AnomalyOption("portal_blue", "🔵 СИНИЙ ПОРТАЛ (Синхронизация)", "Заплатить 20 Энергии для восстановления +35 HP"),
                AnomalyOption("portal_green", "🟢 ЗЕЛЕНЫЙ ПОРТАЛ (Обход)", "Безопасный проход и сканирование секторов (+50 XP)")
            )
            "locked_chest" -> listOf(
                AnomalyOption("chest_master_key", "🔑 МАГНИТНАЯ ОТМЫЧКА (100% Успех)", "Открыть Магнитной Отмычкой (100% шанс, стандартный лут)"),
                AnomalyOption("chest_abyssal_key", "🗝 КЛЮЧ БЕЗДНЫ (100% + Гарантия Экипировки)", "Открыть Ключом Бездны (Гарантия экипировки высшего тира)"),
                AnomalyOption("chest_data_spike", "📌 ДАТА-ШИП (80% Взлом / 20% Сгорает)", "Попытка взлома Дата-шипом (80% шанс успеха)"),
                AnomalyOption("ignore", "🚶 ПРОЙТИ МИМО", "Оставить сундук запечатанным")
            )
            "cursed_chest" -> listOf(
                AnomalyOption("cursed_abyssal_key", "🗝 КЛЮЧ БЕЗДНЫ (100% Успех)", "Открыть Ключом Бездны (50% Проклятый / 50% Легендарка)"),
                AnomalyOption("cursed_data_spike", "📌 ДАТА-ШИП (50% Взлом / 50% Сгорает)", "Попытка взлома Дата-шипом (50% шанс успеха)"),
                AnomalyOption("ignore", "🚶 ПРОЙТИ МИМО", "Оставить Монолит Бездны нетронутым")
            )
            "maxwells_demon" -> listOf(
                AnomalyOption("maxwell_sort", "🔮 СОРТИРОВКА ЭНТРОПИИ", "Разделить частицы (Проверка Удачи -> +40 HP и Чип Максвелла)"),
                AnomalyOption("maxwell_tax", "📊 АКТИВИРОВАТЬ ДЕМОНА", "Получить чип Демона Максвелла (Защита от ловушек в обмен на 10% налог)"),
                AnomalyOption("maxwell_seal", "🛡 ЗАПЕЧАТАТЬ ТЕРМО-ШЛЮЗ", "Запечатать аномалию (+150 XP и тишина)"),
                AnomalyOption("ignore", "🚶 ИГНОРИРОВАТЬ", "Пройти мимо заслона")
            )
            "quantum_reactor" -> listOf(
                AnomalyOption("reactor_overclock", "⚡ ОВЕРКЛОК АВАТАРА", "Получить +100 BC и +150 XP (потерять -15 HP)"),
                AnomalyOption("reactor_drain", "🔋 ЗАРЯДИТЬ БАТАРЕИ", "Восстановить Энергию персонажа до 100%"),
                AnomalyOption("ignore", "🚶 ИГНОРИРОВАТЬ", "Пройти мимо")
            )
            "quantum_altar" -> listOf(
                AnomalyOption("altar_common", "🔥 ПОЖЕРТВОВАТЬ ПРЕДМЕТ", "Сжечь предмет из инвентаря ради +50% Урона на рейд & +1 Комбо"),
                AnomalyOption("altar_rare", "🎲 РИСКОВАННАЯ ТРАНСМУТАЦИЯ", "Сжечь предмет: 30% шанс получить КРАСНУЮ РЕЛИКВИЮ БЕЗДНЫ!"),
                AnomalyOption("altar_shard", "💎 ЖЕРТВА ОСКОЛКА ЭЙДОСА", "Сжечь 1 Осколок Эйдоса -> +50 HP и +100 Сигнала"),
                AnomalyOption("ignore", "🚶 ПРОЙТИ МИМО", "Оставить алтарь без внимания")
            )
            "trap" -> listOf(
                AnomalyOption("accept", "ПРИНЯТЬ УДАР", "Потерять ${event.value} Сигнала"),
                AnomalyOption("dodge", "БЕЖАТЬ / УКЛОНИТЬСЯ", "Попытка избежать повреждений")
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

    fun getAnomaly(id: String): AnomalyEvent? {
        val found = anomalies.find { it.id == id }
        if (found != null) return found
        val event = io.eidos.zerolayer.data.GameData.EVENTS.find { it.id.toString() == id }
        return if (event != null) {
            AnomalyEvent(event.id.toString(), event.text, listOf(
                AnomalyOption("accept", "ПРОДОЛЖИТЬ", "Пройти через аномалию"),
                AnomalyOption("ignore", "ОБХОД", "Обойти сектор")
            ))
        } else {
            AnomalyEvent(id, "НЕИЗВЕСТНАЯ АНОМАЛИЯ СЕКТОРА", listOf(
                AnomalyOption("accept", "ПРОДОЛЖИТЬ ПУТЬ", "Сбросить аномалию и двигаться дальше"),
                AnomalyOption("ignore", "СБРОС ДАННЫХ", "Игнорировать сбой")
            ))
        }
    }

    suspend fun handleAnomalyChoice(uid: Long, optionId: String) {
        val session = dao.getRaidSession(uid) ?: return
        val player = dao.getPlayer(uid) ?: return
        val anomalyId = session.current_anomaly_id ?: return
        val gameEvent = io.eidos.zerolayer.data.GameData.EVENTS.find { it.id.toString() == anomalyId }

        if (gameEvent == null || optionId == "ignore") {
            dao.insertRaidSession(session.copy(current_anomaly_id = null))
            log(uid, "ОБХОД: Аномалия нейтрализована или обойдена.", "info")
            return
        }

        val hasMaxwellsDemon = dao.getInventoryFlow(uid).first().any { it.item_id == "maxwells_demon" && it.is_equipped }

        when (gameEvent.type) {
            "portal_3ways" -> {
                when (optionId) {
                    "portal_red" -> {
                        val roll = (0..100).random()
                        val newDepth = session.depth + 50
                        if (roll < 60) {
                            val coins = (200..400).random().toLong()
                            val xp = (150..300).random().toLong()
                            dao.insertRaidSession(session.copy(
                                depth = newDepth,
                                buffer_coins = session.buffer_coins + coins,
                                buffer_xp = session.buffer_xp + xp,
                                current_anomaly_id = null
                            ))
                            log(uid, "🌀 [КРАСНЫЙ ПОРТАЛ]: УСПЕХ! Сдвиг реальности перенес вас на +50м вглубь Бездны (${newDepth}м)! Найдено: +$coins BC, +$xp XP!", "loot")
                        } else {
                            val damage = 20
                            val newSignal = maxOf(0, session.signal - damage)
                            dao.insertRaidSession(session.copy(
                                depth = newDepth,
                                signal = newSignal,
                                current_anomaly_id = null
                            ))
                            damageArmorHelmet(uid, damage)
                            log(uid, "💥 [КРАСНЫЙ ПОРТАЛ]: ПРАВАЛ! Переход вызвал отдачу Сигнала (-$damage HP). Выброс на глубине ${newDepth}м!", "error")
                            if (newSignal <= 0) {
                                checkDeath(uid)
                            }
                        }
                    }
                    "portal_blue" -> {
                        if (player.energy >= 20) {
                            dao.updatePlayer(player.copy(energy = player.energy - 20, hp = minOf(player.max_hp, player.hp + 35)))
                            dao.insertRaidSession(session.copy(
                                signal = minOf(100, session.signal + 35),
                                current_anomaly_id = null
                            ))
                            log(uid, "🔵 [СИНИЙ ПОРТАЛ]: Канал синхронизации сбросил ошибки интерфейса! -20 Энергии, +35 HP восстановлено!", "info")
                        } else {
                            log(uid, "❌ [ОШИБКА]: Недостаточно энергии для активации Синего Портала (требуется 20 Энергии)!", "error")
                            return
                        }
                    }
                    "portal_green" -> {
                        dao.insertRaidSession(session.copy(
                            buffer_xp = session.buffer_xp + 50,
                            current_anomaly_id = null
                        ))
                        log(uid, "🟢 [ЗЕЛЕНЫЙ ПОРТАЛ]: Обходной шлюз пройден. Сканирование сектора завершено (+50 XP).", "info")
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "locked_chest" -> {
                when (optionId) {
                    "chest_master_key" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val keyItem = inventory.find { it.item_id in listOf("master_key", "admin_key", "crowbar") && it.quantity > 0 }
                        if (keyItem != null) {
                            if (keyItem.item_id == "master_key") removeInventory(uid, keyItem.item_id, 1)
                            val keyName = getItemMetadata(keyItem.item_id)?.name ?: keyItem.item_id
                            
                            val coins = (250..600).random().toLong() + (session.depth * 2)
                            val xp = (200..400).random().toLong()
                            val lootMeta = rollNormalLoot()
                            val lootItem = lootMeta?.id ?: "quantum_tuner"
                            val lootName = lootMeta?.name ?: lootItem
                            val newBuffer = if (session.buffer_items.isEmpty()) lootItem else "${session.buffer_items},$lootItem"

                            dao.insertRaidSession(session.copy(
                                buffer_coins = session.buffer_coins + coins,
                                buffer_xp = session.buffer_xp + xp,
                                buffer_items = newBuffer,
                                current_anomaly_id = null
                            ))
                            log(uid, "🔑 [СЕЙФ ОТКРЫТ]: Вы применили [$keyName]! Извлечено: +$coins BC, +$xp XP и [$lootName]!", "loot")
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет Магнитной Отмычки (Master Key)! Попробуйте Дата-шип или Ключ Бездны.", "error")
                            return
                        }
                    }
                    "chest_abyssal_key" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val keyItem = inventory.find { it.item_id == "abyssal_key" && it.quantity > 0 }
                        if (keyItem != null) {
                            removeInventory(uid, "abyssal_key", 1)
                            val coins = (400..800).random().toLong() + (session.depth * 3)
                            val xp = (300..600).random().toLong()
                            // Guaranteed equipment item
                            val equipItems = itemsMetadata.filter { it.type in listOf("weapon", "armor", "head", "chip") && it.rarity in listOf("rare", "epic", "legendary") }
                            val lootMeta = equipItems.randomOrNull() ?: rollNormalLoot()
                            val lootItem = lootMeta?.id ?: "nano_armor"
                            val lootName = lootMeta?.name ?: lootItem
                            val newBuffer = if (session.buffer_items.isEmpty()) lootItem else "${session.buffer_items},$lootItem"

                            dao.insertRaidSession(session.copy(
                                buffer_coins = session.buffer_coins + coins,
                                buffer_xp = session.buffer_xp + xp,
                                buffer_items = newBuffer,
                                current_anomaly_id = null
                            ))
                            log(uid, "🗝 [КЛЮЧ БЕЗДНЫ]: Сейф взломан с гарантией снаряжения! Извлечено: +$coins BC, +$xp XP и ЭКИПИРОВКА [$lootName]!", "loot")
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет Ключа Бездны (Abyssal Key)!", "error")
                            return
                        }
                    }
                    "chest_data_spike" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val spikeItem = inventory.find { it.item_id == "data_spike" && it.quantity > 0 }
                        if (spikeItem != null) {
                            removeInventory(uid, "data_spike", 1)
                            val successChance = if (player.level >= 12) 90 else 80
                            val roll = (0..99).random()
                            if (roll < successChance) {
                                val coins = (200..500).random().toLong() + (session.depth * 2)
                                val xp = (150..350).random().toLong()
                                val lootMeta = rollNormalLoot()
                                val lootItem = lootMeta?.id ?: "quantum_tuner"
                                val lootName = lootMeta?.name ?: lootItem
                                val newBuffer = if (session.buffer_items.isEmpty()) lootItem else "${session.buffer_items},$lootItem"

                                dao.insertRaidSession(session.copy(
                                    buffer_coins = session.buffer_coins + coins,
                                    buffer_xp = session.buffer_xp + xp,
                                    buffer_items = newBuffer,
                                    current_anomaly_id = null
                                ))
                                log(uid, "📌 [ДАТА-ШИП]: УСПЕХ ВЗЛОМА ($successChance% шанс)! Извлечено: +$coins BC, +$xp XP и [$lootName]!", "loot")
                            } else {
                                dao.insertRaidSession(session.copy(current_anomaly_id = null))
                                log(uid, "📌 [ДАТА-ШИП]: СБОЙ! Дата-шип перегорел при попытке обойти протокол безопасности. Лут не получен.", "error")
                            }
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет Дата-шипа (Data Spike)!", "error")
                            return
                        }
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "cursed_chest" -> {
                when (optionId) {
                    "cursed_abyssal_key" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val keyItem = inventory.find { it.item_id == "abyssal_key" && it.quantity > 0 }
                        if (keyItem != null) {
                            removeInventory(uid, "abyssal_key", 1)
                            val lootMeta = rollCursedOrLegendaryLoot()
                            val lootItem = lootMeta?.id ?: "relic_vampire"
                            val lootName = lootMeta?.name ?: lootItem
                            val isCursed = lootMeta?.rarity?.equals("cursed", ignoreCase = true) == true

                            val newBuffer = if (session.buffer_items.isEmpty()) lootItem else "${session.buffer_items},$lootItem"
                            dao.insertRaidSession(session.copy(
                                buffer_items = newBuffer,
                                current_anomaly_id = null
                            ))
                            if (isCursed) {
                                log(uid, "💀 [МОНОЛИТ БЕЗДНЫ]: Взлом Ключом Бездны успешен! Получен ПРОКЛЯТЫЙ АРТЕФАКТ [$lootName]!", "loot")
                            } else {
                                log(uid, "✨ [МОНОЛИТ БЕЗДНЫ]: Взлом Ключом Бездны успешен! Получен ЛЕГЕНДАРНЫЙ ПРЕДМЕТ [$lootName]!", "loot")
                            }
                        } else {
                            log(uid, "❌ [ОШИБКА]: Для Монолита Бездны требуется Ключ Бездны (Abyssal Key) или Дата-шип! Обычные отмычки бесполезны.", "error")
                            return
                        }
                    }
                    "cursed_data_spike" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val spikeItem = inventory.find { it.item_id == "data_spike" && it.quantity > 0 }
                        if (spikeItem != null) {
                            removeInventory(uid, "data_spike", 1)
                            val successChance = if (player.level >= 12) 60 else 50
                            val roll = (0..99).random()
                            if (roll < successChance) {
                                val lootMeta = rollCursedOrLegendaryLoot()
                                val lootItem = lootMeta?.id ?: "relic_vampire"
                                val lootName = lootMeta?.name ?: lootItem
                                val isCursed = lootMeta?.rarity?.equals("cursed", ignoreCase = true) == true

                                val newBuffer = if (session.buffer_items.isEmpty()) lootItem else "${session.buffer_items},$lootItem"
                                dao.insertRaidSession(session.copy(
                                    buffer_items = newBuffer,
                                    current_anomaly_id = null
                                ))
                                if (isCursed) {
                                    log(uid, "💀 [ДАТА-ШИП]: УСПЕХ ВЗЛОМА БЕЗДНЫ ($successChance% шанс)! Извлечен ПРОКЛЯТЫЙ АРТЕФАКТ [$lootName]!", "loot")
                                } else {
                                    log(uid, "✨ [ДАТА-ШИП]: УСПЕХ ВЗЛОМА БЕЗДНЫ ($successChance% шанс)! Извлечен ЛЕГЕНДАРНЫЙ ПРЕДМЕТ [$lootName]!", "loot")
                                }
                            } else {
                                dao.insertRaidSession(session.copy(current_anomaly_id = null))
                                log(uid, "📌 [ДАТА-ШИП]: СБОЙ! Дата-шип расплавлен багровой скверной Бездны. Лут не получен.", "error")
                            }
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет Дата-шипа (Data Spike)!", "error")
                            return
                        }
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "maxwells_demon" -> {
                when (optionId) {
                    "maxwell_sort" -> {
                        val activeStats = getActiveStats(uid)
                        val chance = 40 + activeStats.luck * 2
                        val roll = (0..100).random()
                        if (roll < chance) {
                            val newSignal = minOf(100, session.signal + 40)
                            val newBuffer = if (session.buffer_items.isEmpty()) "maxwells_demon" else "${session.buffer_items},maxwells_demon"
                            dao.insertRaidSession(session.copy(
                                signal = newSignal,
                                buffer_items = newBuffer,
                                current_anomaly_id = null
                            ))
                            log(uid, "🔮 [ДЕМОН МАКСВЕЛЛА]: УСПЕХ! Термодинамическая сортировка выравняла температуру! +40 Сигнала, в буфер рейда добавлен чип 'Демон Максвелла'!", "info")
                        } else {
                            val damage = 25
                            val newSignal = maxOf(0, session.signal - damage)
                            dao.insertRaidSession(session.copy(
                                signal = newSignal,
                                current_anomaly_id = null
                            ))
                            damageArmorHelmet(uid, damage)
                            log(uid, "⚡ [ДЕМОН МАКСВЕЛЛА]: ВЗРЫВ ЭНТРОПИИ! Хил-заслон дестабилизирован (-$damage Сигнала)!", "error")
                            if (newSignal <= 0) {
                                checkDeath(uid)
                            }
                        }
                    }
                    "maxwell_tax" -> {
                        val newBuffer = if (session.buffer_items.isEmpty()) "maxwells_demon" else "${session.buffer_items},maxwells_demon"
                        dao.insertRaidSession(session.copy(buffer_items = newBuffer, current_anomaly_id = null))
                        log(uid, "📊 [ДЕМОН МАКСВЕЛЛА]: Чип 'Демон Максвелла' помещен в буфер рейда! Активирована пассивная защита от ловушек в обмен на 10% налог.", "info")
                    }
                    "maxwell_seal" -> {
                        dao.insertRaidSession(session.copy(
                            buffer_xp = session.buffer_xp + 150,
                            current_anomaly_id = null
                        ))
                        log(uid, "🛡 [ТЕРМО-ШЛЮЗ]: Термальная аномалия запечатана (+150 XP). Энергетический баланс Нулевого Слая восстановлен.", "info")
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "quantum_reactor" -> {
                when (optionId) {
                    "reactor_overclock" -> {
                        dao.updatePlayer(player.copy(hp = maxOf(1, player.hp - 15)))
                        dao.insertRaidSession(session.copy(
                            buffer_coins = session.buffer_coins + 100,
                            buffer_xp = session.buffer_xp + 150,
                            current_anomaly_id = null
                        ))
                        log(uid, "⚡ [КВАНТОВЫЙ ОВЕРКЛОК]: Сигнал перегружен! Получено +100 BC, +150 XP (потеряно -15 HP).", "loot")
                    }
                    "reactor_drain" -> {
                        dao.updatePlayer(player.copy(energy = player.max_energy))
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                        log(uid, "🔋 [ЗАРЯДКА]: Реактор заправлен! Энергия аватара полностью восстановлена до 100%!", "info")
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "quantum_altar" -> {
                when (optionId) {
                    "altar_common" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val unequipped = inventory.filter { !it.is_equipped && it.item_id != "biocoin" && it.item_id != "eidos_shard" }
                        if (unequipped.isNotEmpty()) {
                            val sacrificed = unequipped.random()
                            removeInventory(uid, sacrificed.item_id, 1)
                            val itemMeta = getItemMetadata(sacrificed.item_id)
                            val itemName = itemMeta?.name ?: sacrificed.item_id
                            val newCombo = session.combo_count + 1
                            val isOverdrive = newCombo >= 5
                            dao.insertRaidSession(session.copy(
                                raid_damage_buff = true,
                                combo_count = if (isOverdrive) 0 else newCombo,
                                overdrive_turns = if (isOverdrive) 3 else session.overdrive_turns,
                                current_anomaly_id = null
                            ))
                            log(uid, "🔮 [КВАНТОВЫЙ АЛТАРЬ]: Сожжен предмет [$itemName]! Получен БАФФ УРОНА (+50% к атаке на рейд) & +1 Комбо!", "loot")
                            if (isOverdrive) {
                                log(uid, "⚡ [РЕЖИМ ГИПЕР-СИНХРОНИЗАЦИИ]: OVERDRIVE АКТИВИРОВАН НА 3 ХОДА! 100% КРИТ, ДВОЙНОЙ ЛУТ И 0 РАСХОД ЭНЕРГИИ!", "loot")
                            }
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет неоснащенных предметов для жертвоприношения!", "error")
                            return
                        }
                    }
                    "altar_rare" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val unequipped = inventory.filter { !it.is_equipped && it.item_id != "biocoin" && it.item_id != "eidos_shard" }
                        if (unequipped.isNotEmpty()) {
                            val sacrificed = unequipped.random()
                            removeInventory(uid, sacrificed.item_id, 1)
                            val itemMeta = getItemMetadata(sacrificed.item_id)
                            val itemName = itemMeta?.name ?: sacrificed.item_id
                            val roll = (0..99).random()
                            if (roll < 30) {
                                val redLoot = rollCursedChestLoot()
                                val redId = redLoot?.id ?: "relic_vampire"
                                val redName = redLoot?.name ?: redId
                                val newBuffer = if (session.buffer_items.isEmpty()) redId else "${session.buffer_items},$redId"
                                val newCombo = session.combo_count + 1
                                val isOverdrive = newCombo >= 5
                                dao.insertRaidSession(session.copy(
                                    buffer_items = newBuffer,
                                    combo_count = if (isOverdrive) 0 else newCombo,
                                    overdrive_turns = if (isOverdrive) 3 else session.overdrive_turns,
                                    current_anomaly_id = null
                                ))
                                log(uid, "🔥 [ТРАНСМУТАЦИЯ УСПЕШНА!]: Алтарь принял [$itemName] и сгенерировал КРАСНЫЙ АРТЕФАКТ [$redName]!", "loot")
                                if (isOverdrive) {
                                    log(uid, "⚡ [РЕЖИМ ГИПЕР-СИНХРОНИЗАЦИИ]: OVERDRIVE АКТИВИРОВАН НА 3 ХОДА!", "loot")
                                }
                            } else {
                                dao.insertRaidSession(session.copy(
                                    buffer_coins = session.buffer_coins + 150,
                                    current_anomaly_id = null
                                ))
                                log(uid, "💨 [РАСЩЕПЛЕНИЕ]: Предмет [$itemName] распался в пыль! Получено +150 BC.", "info")
                            }
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет предметов для ритуала!", "error")
                            return
                        }
                    }
                    "altar_shard" -> {
                        val inventory = dao.getInventoryFlow(uid).first()
                        val shard = inventory.find { it.item_id == "eidos_shard" && it.quantity > 0 }
                        if (shard != null) {
                            removeInventory(uid, "eidos_shard", 1)
                            val newSignal = minOf(100, session.signal + 100)
                            dao.updatePlayer(player.copy(hp = minOf(player.max_hp, player.hp + 50)))
                            dao.insertRaidSession(session.copy(
                                signal = newSignal,
                                current_anomaly_id = null
                            ))
                            log(uid, "💎 [ЖЕРТВА ОСКОЛКА]: Алтарь зарядил системы! Восстановлено +50 HP и +100 Сигнала!", "info")
                        } else {
                            log(uid, "❌ [ОШИБКА]: У вас нет Осколков Эйдоса!", "error")
                            return
                        }
                    }
                    else -> {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    }
                }
            }
            "trap" -> {
                if (hasMaxwellsDemon) {
                    dao.insertRaidSession(session.copy(current_anomaly_id = null))
                    log(uid, "😈 [ДЕМОН МАКСВЕЛЛА]: Чип заблокировал урон от ловушки!", "info")
                } else if (optionId == "accept") {
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
                    val tax = if (hasMaxwellsDemon) (coins * 0.1).toLong() else 0L
                    val finalCoins = coins - tax
                    dao.insertRaidSession(session.copy(
                        buffer_coins = session.buffer_coins + finalCoins,
                        buffer_xp = session.buffer_xp + xp,
                        current_anomaly_id = null
                    ))
                    log(uid, "📦 НАЙДЕНО: +$finalCoins BC, +$xp XP.", "loot")
                    if (tax > 0) {
                        log(uid, "😈 [ДЕМОН МАКСВЕЛЛА]: Изъят налог 10% (-$tax BC).", "error")
                    }
                }
            }
            else -> {
                dao.insertRaidSession(session.copy(current_anomaly_id = null))
                log(uid, "💡 ИССЛЕДОВАНИЕ ПРОДОЛЖАЕТСЯ.", "info")
            }
        }
        checkDeath(uid)
    }

    private suspend fun damageArmorHelmet(uid: Long, damage: Int) {
        val inventory = dao.getInventoryFlow(uid).first()
        val armorItem = inventory.find { it.slot == "armor" && it.is_equipped }
        val headItem = inventory.find { it.slot == "head" && it.is_equipped }
        
        val loss = maxOf(1f, damage * 0.1f)
        if (armorItem != null) {
            val newArmDur = maxOf(0f, armorItem.durability - loss)
            dao.updateInventoryItem(armorItem.copy(durability = newArmDur))
            if (newArmDur <= 0f) log(uid, "🚨 [СИСТЕМНЫЙ СБОЙ: БРОНЯ ДЕАКТИВИРОВАНА]", "error")
        }
        if (headItem != null) {
            val newHeadDur = maxOf(0f, headItem.durability - loss)
            dao.updateInventoryItem(headItem.copy(durability = newHeadDur))
            if (newHeadDur <= 0f) log(uid, "🚨 [СИСТЕМНЫЙ СБОЙ: ШЛЕМ ДЕАКТИВИРОВАН]", "error")
        }
    }

    
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

        removeInventory(uid, itemId, 3)
        addInventory(uid, upgradedItem.id, 1)
        log(uid, "УСПЕШНЫЙ СИНТЕЗ! 3x ${meta.name} -> 1x ${upgradedItem.name}", "success")
    }

    suspend fun dismantleItem(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        val player = dao.getPlayer(uid)
        val shardCount = when (meta.rarity) {
            "common" -> 0
            "uncommon" -> 0
            "rare" -> 1
            "epic" -> 2
            "legendary" -> 4
            "relic", "cursed" -> 8
            else -> 0
        }
        val bcReward = maxOf(5L, (meta.price * 0.15f).toLong())
        
        dao.deleteInventoryItem(item)
        if (player != null) {
            dao.updatePlayer(player.copy(biocoin = player.biocoin + bcReward))
        }
        
        if (shardCount > 0) {
            val currentShards = dao.getInventoryFlow(uid).first().find { it.item_id == "eidos_shard" }
            if (currentShards != null) {
                dao.updateInventoryItem(currentShards.copy(quantity = currentShards.quantity + shardCount))
            } else {
                dao.insertInventoryItem(InventoryItem(uid = uid, item_id = "eidos_shard", quantity = shardCount))
            }
            log(uid, "♻️ [РАЗБОР]: ${meta.name} утилизирован -> +$shardCount 💎 Осколков & +$bcReward BC.", "loot")
        } else {
            log(uid, "♻️ [РАЗБОР]: ${meta.name} утилизирован -> +$bcReward BC.", "loot")
        }
    }

    data class ForgeRecipeDefinition(
        val targetId: String,
        val shardCost: Int,
        val creditCost: Long,
        val additionalIngredients: Map<String, Int> = emptyMap()
    )

    val forgeRecipes: List<ForgeRecipeDefinition> = listOf(
        ForgeRecipeDefinition("reality_silencer", shardCost = 10, creditCost = 2500L, additionalIngredients = mapOf("boss_core" to 1)),
        ForgeRecipeDefinition("death_mask", shardCost = 6, creditCost = 1500L, additionalIngredients = mapOf("data_spike" to 1)),
        ForgeRecipeDefinition("scavenger_mask", shardCost = 4, creditCost = 800L, additionalIngredients = mapOf("master_key" to 2)),
        ForgeRecipeDefinition("nomad_goggles", shardCost = 5, creditCost = 1000L, additionalIngredients = mapOf("compass" to 1)),
        ForgeRecipeDefinition("karma_inversion", shardCost = 8, creditCost = 2000L, additionalIngredients = mapOf("abyssal_key" to 1)),
        ForgeRecipeDefinition("holo_poverty", shardCost = 6, creditCost = 1200L, additionalIngredients = emptyMap()),
        ForgeRecipeDefinition("aegis", shardCost = 5, creditCost = 1000L, additionalIngredients = mapOf("battery" to 1)),
        ForgeRecipeDefinition("medkit_small", shardCost = 15, creditCost = 100L),
        ForgeRecipeDefinition("battery", shardCost = 15, creditCost = 100L),
        ForgeRecipeDefinition("rusty_knife", shardCost = 30, creditCost = 250L),
        ForgeRecipeDefinition("crowbar", shardCost = 50, creditCost = 500L),
        ForgeRecipeDefinition("hoodie", shardCost = 40, creditCost = 400L),
        ForgeRecipeDefinition("master_key", shardCost = 20, creditCost = 200L),
        ForgeRecipeDefinition("data_spike", shardCost = 25, creditCost = 300L),
        ForgeRecipeDefinition("compass", shardCost = 25, creditCost = 300L)
    )

    suspend fun craftItem(uid: Long, targetId: String) {
        val meta = getItemMetadata(targetId) ?: return
        val player = dao.getPlayer(uid) ?: return
        val recipe = forgeRecipes.find { it.targetId == targetId }
        
        val shardCost = recipe?.shardCost ?: ((meta.price / 10) + 10)
        val creditCost = recipe?.creditCost ?: (meta.price / 2L)
        val additionalIngredients = recipe?.additionalIngredients ?: emptyMap()
        
        val inventory = dao.getInventoryFlow(uid).first()
        val shards = inventory.find { it.item_id == "eidos_shard" }
        
        if (shards == null || shards.quantity < shardCost) {
            log(uid, "❌ [КУЗНИЦА]: Недостаточно Осколков Эйдоса. Нужно: $shardCost 💎.", "error")
            return
        }
        
        if (player.biocoin < creditCost) {
            log(uid, "❌ [КУЗНИЦА]: Недостаточно BioCoin. Нужно: $creditCost BC.", "error")
            return
        }

        // Verify additional ingredients in Room DB
        for ((ingId, requiredQty) in additionalIngredients) {
            val ingItem = inventory.find { it.item_id == ingId }
            val currentQty = ingItem?.quantity ?: 0
            if (currentQty < requiredQty) {
                val ingMeta = getItemMetadata(ingId)
                val ingName = ingMeta?.name ?: ingId.uppercase()
                log(uid, "❌ [КУЗНИЦА]: Не хватает материала: $ingName (нужно $requiredQty шт., есть $currentQty шт.)", "error")
                return
            }
        }
        
        // Deduct costs
        dao.updatePlayer(player.copy(biocoin = player.biocoin - creditCost))
        if (shards.quantity == shardCost) {
            dao.deleteInventoryItem(shards)
        } else {
            dao.updateInventoryItem(shards.copy(quantity = shards.quantity - shardCost))
        }

        // Deduct additional ingredients
        for ((ingId, requiredQty) in additionalIngredients) {
            removeInventory(uid, ingId, requiredQty)
        }
        
        // Add crafted item
        addInventory(uid, targetId, 1)
        log(uid, "✨ [СИНТЕЗ ЗАВЕРШЕН]: Создан предмет [${meta.name}]! Материалы списаны, нейро-матрица стабилизирована.", "loot")
    }

    
    suspend fun buyShadowBrokerItem(uid: Long, itemId: String, useBioCoins: Boolean = false) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(itemId) ?: return
        
        val xpCost = ShadowBrokerPrices.getXpPrice(meta)
        val bcCost = ShadowBrokerPrices.getBcPrice(meta)

        if (useBioCoins) {
            if (player.biocoin < bcCost) {
                log(uid, "❌ [ТЕНЕВОЙ БРОКЕР]: Недостаточно BioCoin для сделки! Требуется: $bcCost BC (У вас: ${player.biocoin} BC).", "error")
                return
            }
            dao.updatePlayer(player.copy(biocoin = player.biocoin - bcCost))
            addInventory(uid, itemId, 1)
            log(uid, "📦 [ТЕНЕВОЙ БРОКЕР]: Приобретен артефакт ${meta.name} за $bcCost BC!", "success")
        } else {
            if (player.xp < xpCost) {
                log(uid, "❌ [ТЕНЕВОЙ БРОКЕР]: Недостаточно XP для болезненной жертвы! Требуется $xpCost XP (У вас: ${player.xp} XP).", "error")
                return
            }
            val newXp = maxOf(0L, player.xp - xpCost)
            val newLevel = calculateLevelForXp(newXp)
            val levelLoss = maxOf(0, player.level - newLevel)
            val hpLoss = levelLoss * 20
            val atkLoss = levelLoss * 3
            val defLoss = levelLoss * 2
            val newMaxHp = maxOf(100, player.max_hp - hpLoss)
            val newHp = minOf(newMaxHp, player.hp)
            val newAtk = maxOf(10, player.attack - atkLoss)
            val newDef = maxOf(5, player.defense - defLoss)
            val updatedPlayer = player.copy(
                xp = newXp,
                level = newLevel,
                max_hp = newMaxHp,
                hp = newHp,
                attack = newAtk,
                defense = newDef
            )
            dao.updatePlayer(updatedPlayer)
            addInventory(uid, itemId, 1)
            log(uid, "👁 [ПОЖЕРТВОВАНИЕ ОПЫТА]: Вы пожертвовали -$xpCost XP за ${meta.name}! Нейро-память частично стерта. Уровень Ядра: Level $newLevel.", "loot")
        }
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
            addInventory(uid, wonItem.id, 1)
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
        val rewardCoins = 300L + (player.level * 30L)
        val rewardXp = 120L + (player.level * 15L)
        val tempPlayer = player.copy(
            biocoin = player.biocoin + rewardCoins,
            xp = player.xp + rewardXp,
            wins_pvp = player.wins_pvp + 1
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            handleLevelUpRewards(uid, player.level, updatedPlayer.level)
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
        }
        log(uid, "🏆 [СЕТЕВАЯ ПОБЕДА]: Узел узла взломан! Извлечено +$rewardCoins BC и +$rewardXp XP у оппонента.", "success")
    }

    suspend fun onPvpLose(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val damage = 15
        val lostCoins = minOf(player.biocoin, 150L + player.level * 15L)
        val updatedPlayer = player.copy(
            hp = maxOf(1, player.hp - damage),
            biocoin = player.biocoin - lostCoins,
            losses_pvp = player.losses_pvp + 1
        )
        dao.updatePlayer(updatedPlayer)
        log(uid, "☠️ [ПОРЕЖЕНИЕ В PVP]: Защита ICE отразила атаки! Потеряно -$lostCoins BC, нанесено -$damage HP урона.", "error")
    }

    suspend fun buyItem(uid: Long, itemId: String) {
        val meta = getItemMetadata(itemId) ?: return
        val player = dao.getPlayer(uid) ?: return
        
        if (player.biocoin < meta.price) {
            log(uid, "Недостаточно кредитов для покупки ${meta.name}.", "error")
            return
        }

        val sessionToken = authStore.getSession().accessToken
        if (!sessionToken.isNullOrBlank() && SupabaseClientManager.isConfigured()) {
            val rpcResp = SupabaseClientManager.blackMarketPurchaseRpc(
                accessToken = sessionToken,
                itemId = itemId,
                cost = meta.price.toLong(),
                quantity = 1
            )
            if (rpcResp != null && rpcResp.success) {
                log(uid, "🌐 [SUPABASE RPC]: Покупка верифицирована на сервере!", "info")
            }
        }
        
        dao.updatePlayer(player.copy(biocoin = player.biocoin - meta.price))
        val existing = dao.getInventoryFlow(uid).first().find { it.item_id == itemId }
        if (existing != null && (meta.type == "consumable" || meta.type == "material")) {
            dao.updateInventoryItem(existing.copy(quantity = existing.quantity + 1))
        } else {
            val defaultEq = PoECraftEngine.generateDefaultEquipment(meta.rarity)
            val serialized = PoECraftEngine.serializeEquipment(defaultEq)
            dao.insertInventoryItem(InventoryItem(uid = uid, item_id = itemId, quantity = 1, custom_data = serialized))
        }
        log(uid, "Куплено: ${meta.name} на Черном Рынке.", "info")
    }

    suspend fun sellItem(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        val player = dao.getPlayer(uid) ?: return
        
        val eq = PoECraftEngine.parseEquipment(item.custom_data)
        var bonusPrice = 0L
        if (eq != null) {
            bonusPrice += eq.maxSockets * 50L
            bonusPrice += eq.affixes.size * 30L
            if (eq.isCorrupted) bonusPrice += 200L
        }

        val sellPrice = (meta.price / 2) + bonusPrice
        
        dao.updatePlayer(player.copy(biocoin = player.biocoin + sellPrice))
        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1))
        } else {
            dao.deleteInventoryItem(item)
        }
        log(uid, "Продано: ${meta.name} за $sellPrice BC.", "info")
    }

    @kotlinx.serialization.Serializable
    data class ProfileData(
        val player: Player,
        val inventory: List<InventoryItem>
    )

    @kotlinx.serialization.Serializable
    data class SignedProfileData(
        val data: String,
        val hmac: String
    )

    private fun calculateHMAC(data: String, key: String = "EIDOS_ZERO_LAYER_SECRET_SALT_2026"): String {
        return try {
            val sha256HMAC = javax.crypto.Mac.getInstance("HmacSHA256")
            val secretKey = javax.crypto.spec.SecretKeySpec(key.toByteArray(Charsets.UTF_8), "HmacSHA256")
            sha256HMAC.init(secretKey)
            val bytes = sha256HMAC.doFinal(data.toByteArray(Charsets.UTF_8))
            bytes.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            ""
        }
    }

    suspend fun exportProfile(uid: Long): String {
        val player = dao.getPlayer(uid) ?: return ""
        val inventory = dao.getInventoryFlow(uid).first()
        val plainData = json.encodeToString(ProfileData(player, inventory))
        val hmacSignature = calculateHMAC(plainData)
        return json.encodeToString(SignedProfileData(plainData, hmacSignature))
    }

    suspend fun importProfile(uid: Long, jsonData: String) {
        try {
            val signedData = json.decodeFromString<SignedProfileData>(jsonData)
            val computedHmac = calculateHMAC(signedData.data)
            
            if (computedHmac != signedData.hmac) {
                log(uid, "❌ [УГРОЗА БЕЗОПАСНОСТИ]: Не совпадает HMAC подпись! Локальный слепок отвергнут системой.", "error")
                return
            }

            val data = json.decodeFromString<ProfileData>(signedData.data)
            dao.updatePlayer(data.player.copy(uid = uid))
            // Clear current inventory and replace
            val current = dao.getInventoryFlow(uid).first()
            current.forEach { dao.deleteInventoryItem(it) }
            data.inventory.forEach { dao.insertInventoryItem(it.copy(uid = uid)) }
            log(uid, "📦 [СИНХРОНИЗАЦИЯ]: Слепок оператора успешно верифицирован и развернут.", "info")
        } catch (e: Exception) {
            log(uid, "❌ [СИНХРОНИЗАЦИЯ]: Файл слепка поврежден или не поддерживается.", "error")
        }
    }

    suspend fun getAdvice(level: Int): String {
        val levelStr = if (level < 50) "1" else if (level < 150) "2" else "3"
        val items = dao.getContentForLevel(levelStr).filter { it.type == "advice" }
        return items.randomOrNull()?.text ?: "Сохраняйте синхронизацию, оператор."
    }

    suspend fun ensurePlayerExists(uid: Long) {
        val target = if (uid <= 0L) getActiveUid() else uid
        if (dao.getPlayer(target) == null) {
            val defaultUsername = "Оператор ${target.toString().takeLast(6)}"
            dao.insertPlayer(Player(uid = target, username = defaultUsername, first_name = defaultUsername, biocoin = 500L))
            addInventory(target, "cyber_katana", 1)
            addInventory(target, "kevlar_vest", 1)
            addInventory(target, "medkit_small", 2)
        }
    }

    private var activeDeviceUid: Long = run {
        val prefs = context.getSharedPreferences("eidos_device_prefs", Context.MODE_PRIVATE)
        val uuid = prefs.getString("device_uuid", null)
        if (!uuid.isNullOrBlank()) {
            Math.abs(uuid.hashCode().toLong()) + 100000L
        } else {
            100001L
        }
    }

    fun getActiveUid(): Long = if (activeDeviceUid > 0L) activeDeviceUid else 100001L

    suspend fun ensureDevicePlayerExists(uid: Long, deviceUuid: String, defaultUsername: String) {
        val target = if (uid <= 0L) (Math.abs(deviceUuid.hashCode().toLong()) + 100000L) else uid
        activeDeviceUid = target
        if (dao.getPlayer(target) == null) {
            dao.insertPlayer(Player(uid = target, username = defaultUsername, first_name = defaultUsername, biocoin = 500L))
        }
        val inv = dao.getInventorySync(target)
        if (inv.isEmpty()) {
            addInventory(target, "cyber_katana", 1)
            addInventory(target, "kevlar_vest", 1)
            addInventory(target, "aegis", 1)
            addInventory(target, "medkit_small", 5)
            addInventory(target, "cpu_booster", 2)
        }
    }

    suspend fun log(uid: Long, message: String, type: String = "info") {
        val targetUid = if (uid > 0L) uid else getActiveUid()
        try {
            ensurePlayerExists(targetUid)
            dbMutex.withLock {
                dao.insertLog(GameLog(uid = targetUid, message = message, type = type))
                if ((0..20).random() == 0) {
                    dao.trimOldLogs(targetUid)
                }
            }
            SupabaseClientManager.addRaidLog(targetUid.toString(), message)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun getLogs(uid: Long): Flow<List<GameLog>> = dao.getLogsFlow(uid)

    fun getPlayer(uid: Long): Flow<Player?> = dao.getPlayerFlow(uid)
    
    suspend fun getPlayerSync(uid: Long): Player? {
        val player = dao.getPlayer(uid)
        if (player != null) {
            if (!overdriveChargeMap.containsKey(uid)) {
                overdriveChargeMap[uid] = player.overdriveCharge
                _overdriveChargeFlow.value = player.overdriveCharge
            }
            if (!overchargeTierMap.containsKey(uid)) {
                overchargeTierMap[uid] = player.overchargeTier
                _overchargeTierFlow.value = player.overchargeTier
            }
        }
        return player
    }

    suspend fun savePlayer(player: Player) = dao.insertPlayer(player)

    fun getInventory(uid: Long): Flow<List<InventoryItem>> = dao.getInventoryFlow(uid)

    fun getRaidSession(uid: Long): Flow<RaidSession?> = dao.getRaidSessionFlow(uid)

    data class PlayerStats(
        val hp: Int,
        val maxHp: Int,
        val energy: Int,
        val maxEnergy: Int,
        val attack: Int,
        val defense: Int,
        val luck: Int
    )

    suspend fun getActiveStats(uid: Long): PlayerStats {
        val player = dao.getPlayer(uid) ?: return PlayerStats(100, 100, 100, 100, 10, 5, 5)
        val inventory = dao.getInventoryFlow(uid).first()
        val equipped = inventory.filter { it.is_equipped }

        var atkBonus = 0
        var defBonus = 0
        var luckBonus = 0

        equipped.forEach { item ->
            val meta = getItemMetadata(item.item_id)
            val penalty = when {
                item.durability > 50f -> 1.0f
                item.durability > 20f -> 0.75f
                else -> 0.50f
            }
            if (meta != null && item.durability > 0f) {
                atkBonus += (meta.bonusAttack * penalty).toInt()
                defBonus += (meta.bonusDefense * penalty).toInt()
                luckBonus += (meta.bonusLuck * penalty).toInt()
            }

            // Parse PoE Cyber Equipment Custom Stats & Chips
            val eq = PoECraftEngine.parseEquipment(item.custom_data)
            if (eq != null && item.durability > 0f) {
                val poeStats = PoECraftEngine.calculateTotalStats(eq)
                atkBonus += (poeStats.getOrDefault("ATK", 0) * penalty).toInt()
                defBonus += (poeStats.getOrDefault("DEF", 0) * penalty).toInt()
                luckBonus += (poeStats.getOrDefault("CRIT", 0) * penalty).toInt()

                // Check Vaal Corruption Implicit
                if (eq.implicitAffix != null) {
                    when {
                        eq.implicitAffix.contains("ОВЕРКЛОК") -> atkBonus += (30 * penalty).toInt()
                        eq.implicitAffix.contains("КРИТИЧЕСКИЙ") -> luckBonus += (25 * penalty).toInt()
                        eq.implicitAffix.contains("ЖИЗНЕСТОЙКОСТЬ") -> { /* added to maxHp Bonus below */ }
                    }
                }
            }
        }

        // Faction bonuses
        when (player.faction) {
            "РАЗУМ" -> defBonus += 10
            "ТЕХНО" -> luckBonus += 10
            "АРХИТЕКТОРЫ" -> {
                atkBonus += 25
                defBonus += 25
                luckBonus += 25
            }
        }

        // Martyr halo cursed check
        val headItem = equipped.find { it.slot == "head" }
        if (headItem?.item_id == "martyr_halo" && player.hp < 10) {
            luckBonus += 200
        }

        // Specialization skill tree bonuses
        if (player.skill_hacker_1 == 1) luckBonus += 10
        if (player.skill_berserk_1 == 1) {
            atkBonus += 15
            defBonus += 15
        }

        // Meta-Tree Permanent Upgrades
        atkBonus += player.meta_power_level * 5
        defBonus += player.meta_power_level * 5
        luckBonus += player.meta_luck_level * 5

        // Set Synergies
        val voidCount = equipped.count { getItemMetadata(it.item_id)?.name?.contains("Пустот") == true || it.item_id.contains("void") }
        if (voidCount >= 2) atkBonus += 20
        if (voidCount >= 3) { atkBonus += 20; luckBonus += 15 }

        val archCount = equipped.count { getItemMetadata(it.item_id)?.name?.contains("Архитектора") == true || it.item_id.contains("architect") }
        if (archCount >= 2) defBonus += 20
        if (archCount >= 3) defBonus += 20

        val vampCount = equipped.count { getItemMetadata(it.item_id)?.name?.contains("Кров") == true || getItemMetadata(it.item_id)?.name?.contains("Вампир") == true || it.item_id.contains("vampire") }
        if (vampCount >= 2) luckBonus += 15
        if (vampCount >= 3) { luckBonus += 15; atkBonus += 20 }

        // Raid session damage buff from Altar
        val raidSession = dao.getRaidSession(uid)
        if (raidSession?.raid_damage_buff == true) {
            atkBonus = (atkBonus * 1.5f).toInt()
        }

        var maxHpBonus = (if (player.skill_berserk_2 == 1) 50 else 0) + (player.meta_signal_level * 15)
        equipped.forEach { item ->
            val eq = PoECraftEngine.parseEquipment(item.custom_data)
            if (eq != null && item.durability > 0f) {
                val poeStats = PoECraftEngine.calculateTotalStats(eq)
                maxHpBonus += poeStats.getOrDefault("HP", 0)
                if (eq.implicitAffix?.contains("ЖИЗНЕСТОЙКОСТЬ") == true) {
                    maxHpBonus += 100
                }
            }
        }

        return PlayerStats(
            hp = player.hp,
            maxHp = player.max_hp + maxHpBonus,
            energy = player.energy,
            maxEnergy = player.max_energy,
            attack = player.attack + atkBonus,
            defense = player.defense + defBonus,
            luck = player.luck + luckBonus
        )
    }

    suspend fun capPlayerHp(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val stats = getActiveStats(uid)
        if (player.hp > stats.maxHp) {
            dao.updatePlayer(player.copy(hp = stats.maxHp))
        }
    }

    suspend fun equipItem(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(item.item_id)
        val targetSlot = ItemSlotUtils.getSlotForItem(item.item_id, meta)

        if (targetSlot == null) {
            log(uid, "❌ Предмет [${meta?.name ?: item.item_id}] не является экипировкой!", "error")
            return
        }

        val reqLevel = meta?.reqLevel ?: 1
        if (player.level < reqLevel) {
            log(uid, "❌ [ОШИБКА МОДЕРНИЗАЦИИ]: Недостаточный уровень Ядра! Требуется Level $reqLevel (Ваш уровень: Level ${player.level}).", "error")
            return
        }

        if (item.durability <= 0f) {
            log(uid, "❌ [СИСТЕМНЫЙ СБОЙ: ПРЕДМЕТ ДЕАКТИВИРОВАН]", "error")
            return
        }

        // Unequip current item(s) in targetSlot
        val inventory = dao.getInventoryFlow(uid).first()
        inventory.forEach { invItem ->
            if (invItem.is_equipped) {
                val invMeta = getItemMetadata(invItem.item_id)
                val invSlot = invItem.slot ?: ItemSlotUtils.getSlotForItem(invItem.item_id, invMeta)
                if (invSlot == targetSlot) {
                    dao.updateInventoryItem(invItem.copy(is_equipped = false, slot = null))
                }
            }
        }

        dao.updateInventoryItem(item.copy(is_equipped = true, slot = targetSlot))
        log(uid, "Надето: ${meta?.name ?: item.item_id} в слот $targetSlot (Lvl $reqLevel).", "info")
        capPlayerHp(uid)
    }

    suspend fun unequipItem(uid: Long, item: InventoryItem) {
        dao.updateInventoryItem(item.copy(is_equipped = false, slot = null))
        log(uid, "Предмет снят.", "info")
        capPlayerHp(uid)
    }

    suspend fun useConsumable(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        val player = dao.getPlayer(uid) ?: return
        val session = dao.getRaidSession(uid)

        // Check for Karma Inversion on medkits
        val equippedItems = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
        val hasKarmaInversion = equippedItems.any { it.item_id == "karma_inversion" }
        if (hasKarmaInversion && (item.item_id.startsWith("medkit") || item.item_id == "battery" || item.item_id == "neural_stimulator")) {
            val damageAmount = maxOf(5, (player.max_hp * 0.25f).toInt())
            val newHp = maxOf(1, player.hp - damageAmount)
            dao.updatePlayer(player.copy(hp = newHp))
            consumeOneItem(uid, item)
            log(uid, "☯️ [ИНВЕРСИЯ КАРМЫ]: Аптечка вызвала нейро-токсический шок! Нанесено -$damageAmount HP урона!", "error")
            return
        }

        when (item.item_id) {
            "battery" -> {
                val healAmount = (player.max_hp * 0.30f).toInt().coerceAtLeast(30)
                val newHp = minOf(player.max_hp, player.hp + healAmount)
                dao.updatePlayer(player.copy(hp = newHp))
                if (session != null) {
                    val newSignal = minOf(player.max_hp, session.signal + healAmount)
                    dao.insertRaidSession(session.copy(signal = newSignal))
                }
                consumeOneItem(uid, item)
                log(uid, "🔋 [ЭНЕРГО-ЯЧЕЙКА]: Восстановлено +30% Сигнала (+$healAmount HP)!", "heal")
            }
            "neural_stimulator" -> {
                val healAmount = (player.max_hp * 0.60f).toInt().coerceAtLeast(60)
                val newHp = minOf(player.max_hp, player.hp + healAmount)
                dao.updatePlayer(player.copy(hp = newHp))
                if (session != null) {
                    val newSignal = minOf(player.max_hp, session.signal + healAmount)
                    dao.insertRaidSession(session.copy(signal = newSignal))
                }
                consumeOneItem(uid, item)
                log(uid, "💉 [НЕЙРО-СТИМУЛЯТОР]: Нейросеть стабилизирована! Восстановлено +60% Сигнала (+$healAmount HP)!", "heal")
            }
            "emp_grenade" -> {
                if (session != null && session.current_enemy_hp > 0) {
                    val damage = 150
                    val newEnemyHp = maxOf(0, session.current_enemy_hp - damage)
                    consumeOneItem(uid, item)
                    if (newEnemyHp <= 0) {
                        dao.insertRaidSession(session.copy(current_enemy_hp = 0, current_enemy_id = null, kills = session.kills + 1))
                        log(uid, "💣 [ЭМИ-ГРАНАТА]: Врагу нанесено $damage ЧИСТОГО УРОНА! Противник полностью аннигилирован!", "combat")
                    } else {
                        dao.insertRaidSession(session.copy(current_enemy_hp = newEnemyHp))
                        log(uid, "💣 [ЭМИ-ГРАНАТА]: Врагу нанесено $damage ЧИСТОГО НЕБЛОКИРУЕМОГО УРОНА! Осталось HP: $newEnemyHp.", "combat")
                    }
                } else {
                    log(uid, "❌ [ОШИБКА]: ЭМИ-гранату можно применить только во время боя с противником в рейде!", "error")
                }
            }
            "stealth_spray" -> {
                if (session != null && session.current_enemy_id != null) {
                    consumeOneItem(uid, item)
                    dao.insertRaidSession(session.copy(current_enemy_id = null, current_enemy_hp = 0, combat_turn = 0))
                    log(uid, "🌫 [КРИПТО-ТУМАН]: Вы скрыли сигнатуру и успешно растворились в помехах Слоя! Побег 100% успешен.", "info")
                } else {
                    log(uid, "❌ [ОШИБКА]: Крипто-туман применяется для мгновенного побега из любого боя в рейде!", "error")
                }
            }
            "compass" -> {
                if (session != null) {
                    val currentDur = if (item.durability > 1f) item.durability - 1f else 0f
                    if (currentDur <= 0f) {
                        dao.deleteInventoryItem(item)
                    } else {
                        dao.updateInventoryItem(item.copy(durability = currentDur))
                    }
                    dao.insertRaidSession(session.copy(has_scanned_next_room = true))
                    val nextEvent = session.next_event_type ?: "Неизвестный узел"
                    log(uid, "🧭 [КОМПАС ПУСТОШИ]: Сканирование завершено! Следующий сектор: [$nextEvent]. (Зарядов: ${currentDur.toInt()}/10)", "info")
                } else {
                    log(uid, "❌ [ОШИБКА]: Компас Пустоши можно активировать только во время рейда в Нулевой Слой!", "error")
                }
            }
            "tactical_scanner" -> {
                if (session != null && session.current_enemy_id != null) {
                    val playerAtk = player.attack + (player.level * 3)
                    val enemyHp = session.current_enemy_hp
                    val estimatedWinrate = ((player.hp.toFloat() / (player.hp + enemyHp)) * 100f).toInt().coerceIn(15, 95)
                    
                    if ((0..9).random() == 0) { // 10% chance to consume charge
                        val currentDur = if (item.durability > 1f) item.durability - 1f else 0f
                        if (currentDur <= 0f) dao.deleteInventoryItem(item)
                        else dao.updateInventoryItem(item.copy(durability = currentDur))
                    }
                    log(uid, "📡 [ТАКТИЧЕСКИЙ СКАНЕР]: Расчет тактической матрицы: Текущий шанс на победу: $estimatedWinrate%!", "info")
                } else {
                    log(uid, "❌ [ОШИБКА]: Тактический сканер используется во время боя для расчета вероятности победы!", "error")
                }
            }
            "memory_wiper" -> {
                if (session != null) {
                    consumeOneItem(uid, item)
                    dao.insertRaidSession(session.copy(active_aggro = 0))
                    log(uid, "💽 [СТИРАТЕЛЬ ПАМЯТИ]: Накопленная агрессия монстров и следящие скрипты сброшены до 0!", "info")
                } else {
                    log(uid, "❌ [ОШИБКА]: Стиратель памяти активируется в рейде для сброса агро-модификатора!", "error")
                }
            }
            "cryo" -> {
                consumeOneItem(uid, item)
                log(uid, "❄️ [КРИО-КАПСУЛА]: Ежедневный стрик активности заморожен и защищен от пропуска дня!", "info")
            }
            "accel", "sync_accel" -> {
                val updatedPlayer = player.copy(
                    sync_accel_expiry = System.currentTimeMillis() + (24L * 3600 * 1000)
                )
                dao.updatePlayer(updatedPlayer)
                consumeOneItem(uid, item)
                log(uid, "⚡ [УСКОРИТЕЛЬ СИНХРОНИЗАЦИИ]: Кулдаун синхронизации снижен до 15 минут на 24 часа!", "info")
            }
            "decoder" -> {
                consumeOneItem(uid, item)
                log(uid, "🔓 [ДЕШИФРАТОР]: Алгоритм активирован! Время дешифрации кэшей сокращено в 2 раза.", "info")
            }
            "aegis" -> {
                log(uid, "🛡 [ЭГИДА БЕССМЕРТИЯ]: Пассивный защитный артефакт. Автоматически спасет вас от смерти в рейде при падении Сигнала до 0.", "info")
            }
            "master_key", "abyssal_key", "data_spike" -> {
                log(uid, "🗝 [КЛЮЧ/ОТМЫЧКА]: Применяется в рейдах для вскрытия Запертых и Проклятых сундуков.", "info")
            }
            "purification_sync" -> {
                val resetPlayer = player.copy(
                    level = 1,
                    xp = 0,
                    hp = 100,
                    max_hp = 100,
                    attack = 10,
                    defense = 5,
                    luck = 5,
                    biocoin = 100,
                    reputation = player.reputation + 50,
                    state_version = player.state_version + 1,
                    updated_at = System.currentTimeMillis()
                )
                dao.updatePlayer(resetPlayer)
                consumeOneItem(uid, item)
                // Clear ordinary inventory items, keep only eidos_shard
                val inv = dao.getInventoryFlow(uid).first()
                inv.forEach {
                    if (it.item_id != "eidos_shard" && it.id != item.id) {
                        dao.deleteInventoryItem(it)
                    }
                }
                log(uid, "🌀 [СИНХРОН ОЧИЩЕНИЯ]: Совершен Hard Reset (Престиж). Уровень и опыт сброшены до 1. Рекорд зафиксирован в Архиве!", "loot")
            }
            else -> {
                var hpHeal = meta.hpRestore
                var energyHeal = meta.energyRestore

                if (player.skill_medic_3 == 1 && hpHeal > 0) {
                    hpHeal *= 2
                }

                val updatedPlayer = player.copy(
                    hp = minOf(player.max_hp, player.hp + hpHeal),
                    energy = minOf(player.max_energy, player.energy + energyHeal)
                )
                dao.updatePlayer(updatedPlayer)
                consumeOneItem(uid, item)
                log(uid, "Использован предмет ${meta.name}. Восстановлено: HP +$hpHeal, Энергия +$energyHeal.", "info")
            }
        }
    }

    private suspend fun consumeOneItem(uid: Long, item: InventoryItem) {
        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1))
        } else {
            dao.deleteInventoryItem(item)
        }
    }

    suspend fun repairItemBC(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        val player = dao.getPlayer(uid) ?: return

        val cost = calculateItemRepairFee(item)
        if (cost <= 0 || item.durability >= 100f) {
            log(uid, "Предмет ${meta.name} уже имеет полную прочность.", "error")
            return
        }
        if (player.biocoin < cost) {
            log(uid, "Недостаточно BioCoin. Нужно $cost BC.", "error")
            return
        }

        dao.updatePlayer(player.copy(biocoin = player.biocoin - cost))
        dao.updateInventoryItem(item.copy(durability = 100f))
        log(uid, "Успешно отремонтировано ${meta.name} за $cost BC.", "info")
    }

    suspend fun repairItemShards(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        if (item.durability >= 100f) {
            log(uid, "Предмет ${meta.name} уже имеет полную прочность.", "error")
            return
        }

        val inventory = dao.getInventoryFlow(uid).first()
        val shards = inventory.find { it.item_id == "eidos_shard" }
        if (shards == null || shards.quantity < 3) {
            log(uid, "Недостаточно Осколков Эйдоса. Нужно 3.", "error")
            return
        }

        if (shards.quantity == 3) {
            dao.deleteInventoryItem(shards)
        } else {
            dao.updateInventoryItem(shards.copy(quantity = shards.quantity - 3))
        }

        val newDurability = minOf(100f, item.durability + 25f)
        dao.updateInventoryItem(item.copy(durability = newDurability))
        log(uid, "Успешно отремонтировано ${meta.name} за 3 Осколка Эйдоса (+25% прочности).", "info")
    }

    suspend fun rechargeEnergy(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()
        val nextChargeTime = player.last_recharge + (4 * 3600 * 1000)
        if (now < nextChargeTime) {
            val remainMin = ((nextChargeTime - now) / 60000).toInt()
            log(uid, "Зарядная станция перезаряжается. Подождите $remainMin минут.", "error")
            return
        }

        dao.updatePlayer(player.copy(
            energy = minOf(player.max_energy, player.energy + 50),
            last_recharge = now
        ))
        log(uid, "⚡ [ЗАРЯДНАЯ СТАНЦИЯ]: Батарея заряжена на +50 ед.", "info")
    }

    suspend fun claimDailySupplyDrop(uid: Long): List<InventoryItem>? {
        val player = dao.getPlayer(uid) ?: return null
        val now = System.currentTimeMillis()
        val nextDropTime = player.last_supply_drop + (24 * 3600 * 1000)
        if (now < nextDropTime) {
            val remainHours = ((nextDropTime - now) / 3600000).toInt()
            log(uid, "Следующие припасы через $remainHours часов.", "error")
            return null
        }

        val consumables = listOf("battery", "master_key", "neural_stimulator")
        val dropItem = consumables.random()

        dao.updatePlayer(player.copy(
            energy = minOf(player.max_energy, player.energy + 50),
            last_supply_drop = now
        ))

        val invItem = InventoryItem(uid = uid, item_id = dropItem, quantity = 1)
        val existing = dao.getInventoryFlow(uid).first().find { it.item_id == dropItem }
        if (existing != null) {
            dao.updateInventoryItem(existing.copy(quantity = existing.quantity + 1))
        } else {
            dao.insertInventoryItem(invItem)
        }

        log(uid, "📦 [СИНХРОНИЗАЦИЯ ДЕПО]: Получены суточные припасы! +50 Энергии, +1 ${dropItem.uppercase()}", "loot")
        return listOf(invItem)
    }

    suspend fun buyPremium(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        dao.updatePlayer(player.copy(is_premium = true))
        log(uid, "💎 [SaaS АКТИВАЦИЯ]: Премиум-статус успешно активирован!", "info")
    }

    suspend fun upgradeSkill(uid: Long, branch: String, skillIndex: Int) {
        val player = dao.getPlayer(uid) ?: return
        val cost = when (skillIndex) {
            1 -> 10
            2 -> 30
            3 -> 100
            else -> return
        }

        val inventory = dao.getInventoryFlow(uid).first()
        val shards = inventory.find { it.item_id == "eidos_shard" }
        if (shards == null || shards.quantity < cost) {
            log(uid, "Недостаточно Осколков Эйдоса. Нужно $cost.", "error")
            return
        }

        // Deduct shards
        if (shards.quantity == cost) {
            dao.deleteInventoryItem(shards)
        } else {
            dao.updateInventoryItem(shards.copy(quantity = shards.quantity - cost))
        }

        val updatedPlayer = when (branch) {
            "hacker" -> when (skillIndex) {
                1 -> player.copy(skill_hacker_1 = 1)
                2 -> if (player.skill_hacker_1 == 1) player.copy(skill_hacker_2 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                3 -> if (player.skill_hacker_2 == 1) player.copy(skill_hacker_3 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                else -> player
            }
            "berserk" -> when (skillIndex) {
                1 -> player.copy(skill_berserk_1 = 1)
                2 -> if (player.skill_berserk_1 == 1) player.copy(skill_berserk_2 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                3 -> if (player.skill_berserk_2 == 1) player.copy(skill_berserk_3 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                else -> player
            }
            "medic" -> when (skillIndex) {
                1 -> player.copy(skill_medic_1 = 1)
                2 -> if (player.skill_medic_1 == 1) player.copy(skill_medic_2 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                3 -> if (player.skill_medic_2 == 1) player.copy(skill_medic_3 = 1) else { log(uid, "Сначала разблокируйте предыдущий навык.", "error"); return }
                else -> player
            }
            else -> player
        }

        dao.updatePlayer(updatedPlayer)
        log(uid, "✨ Улучшен пассивный навык ветки ${branch.uppercase()} ($skillIndex/3)!", "info")
    }

    suspend fun respecSkills(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        if (player.biocoin < 500) {
            log(uid, "Сброс требует 500 BC. Недостаточно средств.", "error")
            return
        }

        var totalRefund = 0
        if (player.skill_hacker_1 == 1) totalRefund += 10
        if (player.skill_hacker_2 == 1) totalRefund += 30
        if (player.skill_hacker_3 == 1) totalRefund += 100
        if (player.skill_berserk_1 == 1) totalRefund += 10
        if (player.skill_berserk_2 == 1) totalRefund += 30
        if (player.skill_berserk_3 == 1) totalRefund += 100
        if (player.skill_medic_1 == 1) totalRefund += 10
        if (player.skill_medic_2 == 1) totalRefund += 30
        if (player.skill_medic_3 == 1) totalRefund += 100

        val updatedPlayer = player.copy(
            biocoin = player.biocoin - 500,
            skill_hacker_1 = 0,
            skill_hacker_2 = 0,
            skill_hacker_3 = 0,
            skill_berserk_1 = 0,
            skill_berserk_2 = 0,
            skill_berserk_3 = 0,
            skill_medic_1 = 0,
            skill_medic_2 = 0,
            skill_medic_3 = 0
        )

        dao.updatePlayer(updatedPlayer)

        if (totalRefund > 0) {
            val shards = dao.getInventoryFlow(uid).first().find { it.item_id == "eidos_shard" }
            if (shards != null) {
                dao.updateInventoryItem(shards.copy(quantity = shards.quantity + totalRefund))
            } else {
                dao.insertInventoryItem(InventoryItem(uid = uid, item_id = "eidos_shard", quantity = totalRefund))
            }
        }

        log(uid, "🔄 [РЕКУРСИВНЫЙ СБРОС]: Все пассивные навыки обнулены. Возвращено осколков: $totalRefund ед.", "info")
    }

    suspend fun buyMetaUpgrade(uid: Long, upgradeType: String) {
        val player = dao.getPlayer(uid) ?: return
        val currentLevel = when (upgradeType) {
            "signal" -> player.meta_signal_level
            "key" -> player.meta_key_level
            "luck" -> player.meta_luck_level
            "power" -> player.meta_power_level
            else -> 0
        }
        val cost = (currentLevel + 1) * 5
        val hasDeducted = deductShards(uid, cost)
        if (!hasDeducted) {
            log(uid, "❌ Недостаточно Осколков Эйдоса. Требуется $cost Осколков.", "error")
            return
        }

        val updatedPlayer = when (upgradeType) {
            "signal" -> player.copy(meta_signal_level = player.meta_signal_level + 1)
            "key" -> player.copy(meta_key_level = player.meta_key_level + 1)
            "luck" -> player.copy(meta_luck_level = player.meta_luck_level + 1)
            "power" -> player.copy(meta_power_level = player.meta_power_level + 1)
            else -> player
        }

        dao.updatePlayer(updatedPlayer)
        val name = when(upgradeType) {
            "signal" -> "Стартовый Сигнал (+15 HP)"
            "key" -> "Карманный Мастер-Ключ"
            "luck" -> "Аура Удачи Бездны (+5 Удача)"
            "power" -> "Закалка Аватара (+5 Атака/Защита)"
            else -> upgradeType
        }
        log(uid, "🏛️ [МЕТА-ПРОГРЕСС]: Улучшено [$name] до уровня ${currentLevel + 1}! Затрачено $cost Осколков.", "info")
    }

    suspend fun hitWorldBoss(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        if (player.energy < 10) {
            log(uid, "❌ [МИРОВОЙ БОСС: EIDOS-CORE]: Недостаточно энергии (требуется 10⚡). Восстановите силы в Хабе.", "error")
            return
        }

        val damage = (player.attack * 12) + (30..80).random()
        val rewardsCoin = (15..35).random()
        val rewardXp = (25..50).random()
        val newEnergy = maxOf(0, player.energy - 10)

        val updatedPlayer = player.copy(
            energy = newEnergy,
            biocoin = player.biocoin + rewardsCoin,
            xp = player.xp + rewardXp
        )
        dao.updatePlayer(updatedPlayer)

        val roll = (1..100).random()
        if (roll <= 15) {
            addInventory(uid, "data_fragment", 1)
            log(uid, "⚔ [МИРОВОЙ БОСС]: Нанесено $damage урона! Награда: +$rewardsCoin BC, +$rewardXp XP, 💾 Фрагмент Данных (-10⚡).", "loot")
        } else {
            log(uid, "⚔ [МИРОВОЙ БОСС]: Нанесено $damage урона! Награда: +$rewardsCoin BC, +$rewardXp XP (-10⚡).", "combat")
        }
    }

    suspend fun startRaid(uid: Long, startDepth: Int) {
        val player = dao.getPlayer(uid) ?: return
        val isFreeEntry = player.raids_done == 0
        val startCostCoins = if (isFreeEntry) 0L else 20L

        if (!isFreeEntry && player.biocoin < startCostCoins) {
            log(uid, "❌ Недостаточно BioCoins для спуска в Нулевой Слой (Требуется $startCostCoins BC). Выполните взлом или восстановите ресурсы.", "error")
            return
        }

        if (startCostCoins > 0) {
            dao.updatePlayer(player.copy(biocoin = maxOf(0L, player.biocoin - startCostCoins)))
        }

        setOverdriveCharge(uid, 0)
        setOverchargeTier(uid, 0)

        io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context).logRaidStarted(startDepth, 100)

        val session = RaidSession(
            uid = uid,
            depth = startDepth,
            signal = 100,
            next_event_type = "scan"
        )
        dao.insertRaidSession(session)
        val feeMsg = if (isFreeEntry) "Первый спуск — БЕСПЛАТНО" else "Списано -$startCostCoins BC"
        log(uid, "Нейро-связь установлена. Вход в Нулевой Слой на ${startDepth}м ($feeMsg).", "info")
    }

    suspend fun processStep(uid: Long) {
        val initialSession = dao.getRaidSession(uid) ?: return
        var session = initialSession
        val player = dao.getPlayer(uid) ?: return

        if (session.current_anomaly_id != null) {
            return
        }
        if (session.current_enemy_id != null) {
            handleCombatTurn(uid, session, player)
            return
        }

        val stepGainXp = 5L + (session.depth / 200)

        // Step durability loss (0.1%)
        val inventory = dao.getInventoryFlow(uid).first()
        val equippedItems = inventory.filter { it.is_equipped }
        equippedItems.forEach { item ->
            if (item.slot in listOf("weapon", "armor", "head")) {
                val newDurability = maxOf(0f, item.durability - 0.1f)
                if (newDurability != item.durability) {
                    dao.updateInventoryItem(item.copy(durability = newDurability))
                }
            }
        }

        // Blood miner chip check
        val hasBloodMiner = equippedItems.find { it.item_id == "blood_miner" } != null
        var workingPlayer = if (hasBloodMiner) {
            val bloodLoss = maxOf(1, (player.hp * 0.02).toInt())
            log(uid, "🩸 [Майнер на Крови]: Получено +50 BC, потеряно -$bloodLoss HP.", "error")
            player.copy(biocoin = player.biocoin + 50, hp = maxOf(1, player.hp - bloodLoss), xp = player.xp + stepGainXp)
        } else {
            player.copy(xp = player.xp + stepGainXp)
        }

        val equipmentFlags = io.eidos.zerolayer.domain.raid.RaidEventDispatcher.parseEquipmentFlags(equippedItems)

        // Micro-Glitch Roll (3% chance unless reality_silencer is equipped)
        val microGlitch = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.rollMicroGlitch(
            player = workingPlayer,
            hasRealitySilencer = equipmentFlags.hasRealitySilencer
        )
        if (microGlitch != null) {
            workingPlayer = workingPlayer.copy(
                isGlitched = true,
                anomalyBuffType = microGlitch.buffType,
                anomalyBuffExpiry = microGlitch.expiryTimestamp,
                glitchEncounterCounter = microGlitch.newGlitchCounter
            )
            log(uid, "🌀 ${microGlitch.title}: ${microGlitch.description}", "heal")
        }
        dao.updatePlayer(workingPlayer)

        val newDepth = session.depth + (5..15).random()
        val activeStats = getActiveStats(uid)
        val gravesList = dao.getAllGraves()

        // 5000+m Abyssal Singularity room affix handling
        var currentMutator = session.active_mutator
        if (newDepth >= 5000 && (currentMutator == null || (newDepth % 50 < 15))) {
            currentMutator = io.eidos.zerolayer.domain.combat.CombatEngine.rollSingularityAffix(newDepth)
            val affixName = io.eidos.zerolayer.domain.combat.CombatEngine.getAffixDisplayName(currentMutator)
            if (affixName.isNotBlank()) {
                log(uid, "🌌 [АБИССАЛЬНАЯ СИНГУЛЯРНОСТЬ 5000+М]: Активирован аффикс сектора: $affixName", "info")
            }
        }

        // Apply Code Radiation affix damage on step if active
        if (currentMutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_RADIATION) {
            val radDamage = 8
            val newHp = maxOf(1, workingPlayer.hp - radDamage)
            val newSig = maxOf(1, session.signal - radDamage)
            workingPlayer = workingPlayer.copy(hp = newHp)
            session = session.copy(signal = newSig)
            log(uid, "☢️ [РАДИАЦИЯ КОДА]: Излучение Сингулярности на ${newDepth}м отнимает -$radDamage Сигнала!", "error")
        }

        val dispatchResult = io.eidos.zerolayer.domain.raid.RaidEventDispatcher.dispatchNextEvent(
            depth = newDepth,
            player = workingPlayer,
            playerDefense = activeStats.defense,
            playerLuck = activeStats.luck,
            flags = equipmentFlags,
            gravesList = gravesList
        )

        when (dispatchResult) {
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.MaxwellDemon -> {
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "maxwells_demon",
                    is_scanned = false
                ))
                log(uid, dispatchResult.message, "error")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.StealthBypass -> {
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "scan",
                    is_scanned = false
                ))
                log(uid, dispatchResult.message, "info")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.GraveFound -> {
                val grave = dispatchResult.grave
                val newBufferItems = if (session.buffer_items.isEmpty()) grave.items else "${session.buffer_items},${grave.items}"
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    buffer_coins = session.buffer_coins + grave.coins,
                    buffer_items = newBufferItems,
                    next_event_type = "loot",
                    is_scanned = false
                ))
                dao.deleteGrave(grave)
                log(uid, dispatchResult.message, "loot")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.TrapTriggered -> {
                if (dispatchResult.healAmount > 0) {
                    val newHp = minOf(workingPlayer.max_hp, workingPlayer.hp + dispatchResult.healAmount)
                    val newSignal = minOf(100, session.signal + dispatchResult.healAmount)
                    dao.updatePlayer(workingPlayer.copy(hp = newHp))
                    dao.insertRaidSession(session.copy(depth = newDepth, active_mutator = currentMutator, signal = newSignal, next_event_type = "scan", is_scanned = false))
                } else {
                    val newHp = maxOf(0, workingPlayer.hp - dispatchResult.damage)
                    val newSignal = maxOf(0, session.signal - dispatchResult.damage)
                    dao.updatePlayer(workingPlayer.copy(hp = newHp))
                    dao.insertRaidSession(session.copy(depth = newDepth, active_mutator = currentMutator, signal = newSignal, next_event_type = "scan", is_scanned = false))
                }
                log(uid, dispatchResult.message, if (dispatchResult.healAmount > 0) "heal" else "error")
                checkDeath(uid)
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.LootFound -> {
                val isDoubleDrop = currentMutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_DOUBLE_DROP
                val coinReward = if (isDoubleDrop) dispatchResult.coins * 2 else dispatchResult.coins
                var newBufferItems = session.buffer_items
                dispatchResult.items.forEach { foundId ->
                    newBufferItems = if (newBufferItems.isEmpty()) foundId else "$newBufferItems,$foundId"
                }
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    buffer_coins = session.buffer_coins + coinReward,
                    buffer_items = newBufferItems,
                    next_event_type = "loot",
                    is_scanned = false
                ))
                if (isDoubleDrop) {
                    log(uid, "💎 [СИНГУЛЯРНЫЙ РЕЗОНАНС]: Дроп монет удвоен ($coinReward BC)!", "loot")
                }
                log(uid, dispatchResult.message, "loot")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.SafeZone -> {
                val newHp = minOf(workingPlayer.max_hp, workingPlayer.hp + dispatchResult.healAmount)
                val newSignal = minOf(100, session.signal + dispatchResult.healAmount)
                dao.updatePlayer(workingPlayer.copy(hp = newHp))
                dao.insertRaidSession(session.copy(depth = newDepth, active_mutator = currentMutator, signal = newSignal, next_event_type = "scan", is_scanned = false))
                log(uid, dispatchResult.message, "heal")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.RiddleEncounter -> {
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "riddle",
                    is_scanned = false
                ))
                log(uid, dispatchResult.message, "info")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.CombatEncounter -> {
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "combat",
                    current_enemy_id = dispatchResult.enemyName,
                    current_enemy_hp = dispatchResult.enemyHp,
                    combat_turn = 0,
                    damage_buffer = 0,
                    is_scanned = false
                ))
                recordEnemyEncounter(dispatchResult.enemyName)
                log(uid, dispatchResult.message, "combat")
            }
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.SectorScanned -> {
                // Nomad Goggles 5% chance conversion to loot cache
                if (equipmentFlags.hasNomadGoggles && (0..100).random() < 5) {
                    val bonusLoot = "encrypted_cache"
                    val newBufferItems = if (session.buffer_items.isEmpty()) bonusLoot else "${session.buffer_items},$bonusLoot"
                    dao.insertRaidSession(session.copy(depth = newDepth, active_mutator = currentMutator, buffer_items = newBufferItems, next_event_type = "loot", is_scanned = false))
                    log(uid, "🥽 [ОКУЛЯРЫ НОМАДА]: Оптический сканер вскрыл скрытый тайник [Зашифрованный Кэш]!", "loot")
                } else {
                    dao.insertRaidSession(session.copy(depth = newDepth, active_mutator = currentMutator, next_event_type = "scan", is_scanned = false))
                    log(uid, dispatchResult.message, "info")
                }
            }
        }
    }

    private suspend fun handleCombatTurn(uid: Long, session: RaidSession, player: Player) {
        val villainsStatic = io.eidos.zerolayer.data.GameData.VILLAINS
        val depthDiffMult = io.eidos.zerolayer.domain.combat.CombatEngine.getDepthDifficultyMultiplier(session.depth)
        val depthRewardMult = io.eidos.zerolayer.domain.combat.CombatEngine.getDepthRewardMultiplier(session.depth)
        val villain = villainsStatic.find { it.name == session.current_enemy_id } ?: io.eidos.zerolayer.data.GameVillainData(
            id = 9999,
            name = session.current_enemy_id ?: "Неизвестный Сбой",
            level = (session.depth / 50) + 1,
            hp = session.current_enemy_hp,
            atk = ((15 + (session.depth / 10)) * depthDiffMult).toInt(),
            def = (5 + (session.depth / 20)),
            xp = ((50 + (session.depth / 2)) * depthRewardMult).toLong(),
            coin = ((30 + (session.depth / 3)) * depthRewardMult).toLong(),
            description = "Искаженный фрагмент кода, затерянный в Слоях Нуля.",
            image = ""
        )
        val activeStats = getActiveStats(uid)

        val inventory = dao.getInventoryFlow(uid).first()
        val weaponItem = inventory.find { it.slot == "weapon" && it.is_equipped }
        val armorItem = inventory.find { it.slot == "armor" && it.is_equipped }
        val headItem = inventory.find { it.slot == "head" && it.is_equipped }

        val isCursedWeapon = weaponItem != null && getItemMetadata(weaponItem.item_id)?.rarity == "cursed"

        // --- Player Turn ---
        val weaponMultiplier = if (weaponItem != null && weaponItem.durability > 0f) {
            getItemMetadata(weaponItem.item_id)?.multiplier ?: 1.0f
        } else {
            1.0f
        }

        var baseDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateBasePlayerDamage(activeStats.attack, weaponMultiplier, villain.def)

        // Cursed weapon credit_slicer logic
        if (weaponItem?.item_id == "credit_slicer") {
            if (player.biocoin > 0) {
                val burned = maxOf(1, (player.biocoin * 0.01).toLong())
                dao.updatePlayer(player.copy(biocoin = player.biocoin - burned))
                baseDamage = (activeStats.attack + burned * 1.5).toInt()
                log(uid, "💸 [Кредитный Резак]: Сожжено -$burned BC для форсированного удара!", "combat")
            } else {
                baseDamage = 5
            }
        }

        // Cursed weapon empath_whip logic
        if (weaponItem?.item_id == "empath_whip") {
            baseDamage = (villain.atk * 1.5).toInt()
        }

        // Crit roll using CombatEngine
        val isWarpAffix = session.active_mutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_WARP
        val warpCritBonus = if (isWarpAffix) 30 else 0
        val finalCritChance = io.eidos.zerolayer.domain.combat.CombatEngine.calculateCritChance(
            baseLuck = activeStats.luck,
            hasBerserk1 = player.skill_berserk_1 == 1,
            hasOverclockCrown = headItem?.item_id == "overclock_crown"
        )
        val maxwellCritBonus = if (io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_OVERCLOCK)) 15 else 0
        val isCrit = (0..100).random() < (finalCritChance + maxwellCritBonus + warpCritBonus)

        var finalPlayerDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateFinalPlayerDamage(baseDamage, isCrit)

        // Gain Overdrive Charge on Player Attack
        val currentCharge = getOverdriveCharge(uid)
        val chargeGain = if (isCrit) io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_CRIT_HIT else io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_NORMAL_ATTACK
        setOverdriveCharge(uid, currentCharge + chargeGain)

        // Glitch Berserk Anomaly Buff: +25% player ATK damage
        if (io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_GLITCH_BERSERK)) {
            finalPlayerDamage = (finalPlayerDamage * 1.25f).toInt()
        }

        // Maxwell Blood Overclock Buff: +35% player ATK damage
        if (io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_OVERCLOCK)) {
            finalPlayerDamage = (finalPlayerDamage * 1.35f).toInt()
        }

        // Cursed weapon banhammer_shard logic
        if (weaponItem?.item_id == "banhammer_shard" && (0..100).random() < 1) {
            finalPlayerDamage = 999999
            log(uid, "🔨 [Осколок Бан-Хаммера]: Враг стерт из реестра реальности!", "combat")
        }

        val newEnemyHp = session.current_enemy_hp - finalPlayerDamage
        val critTag = if (isCrit) " [CRITICAL_HIT]" else ""
        log(uid, "НЕЙРО-ВСПЛЕСК: -$finalPlayerDamage Сигнала у ${villain.name}$critTag.", "combat")

        // Emit combat visual event for player hit
        _combatEventFlow.tryEmit(CombatVisualEvent(
            damage = finalPlayerDamage,
            isCrit = isCrit,
            isOverdrive = false,
            isDodge = false,
            isPlayerHit = false
        ))

        // Singularity Affix: Thorns / Quantum Damage Reflection (20%)
        if (session.active_mutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_THORNS && finalPlayerDamage in 1..50000) {
            val reflectedDmg = maxOf(1, (finalPlayerDamage * 0.20f).toInt())
            val newSigAfterReflect = maxOf(0, session.signal - reflectedDmg)
            val newHpAfterReflect = maxOf(0, player.hp - reflectedDmg)
            dao.updatePlayer(player.copy(hp = newHpAfterReflect))
            dao.insertRaidSession(session.copy(signal = newSigAfterReflect))
            log(uid, "🪞 [КВАНТОВОЕ ОТРАЖЕНИЕ]: Отражено -$reflectedDmg урона обратно в оператора!", "error")
            if (newSigAfterReflect <= 0 || newHpAfterReflect <= 0) {
                checkDeath(uid)
            }
        }

        // Overclock crown cost
        if (isCrit && headItem?.item_id == "overclock_crown") {
            val costHp = maxOf(1, (player.hp * 0.02).toInt())
            dao.updatePlayer(player.copy(hp = maxOf(1, player.hp - costHp)))
            log(uid, "⚡ [Венец Разгона]: Крит стоил -$costHp Сигнала.", "error")
        }

        // Weapon durability reduction
        if (weaponItem != null) {
            val loss = if (isCrit || isCursedWeapon) 1.0f else 0.5f
            val newDur = maxOf(0f, weaponItem.durability - loss)
            dao.updateInventoryItem(weaponItem.copy(durability = newDur))
            if (newDur <= 0f) {
                log(uid, "🚨 [КРИТИЧЕСКИЙ СБОЙ]: Ваше оружие ${getItemMetadata(weaponItem.item_id)?.name} сломано!", "error")
            }
        }

        // Vampirism / True Blood Crown
        if (headItem?.item_id == "relic_vampire") {
            val healSignal = maxOf(1, (session.signal * 0.02).toInt())
            val newSig = minOf(100, session.signal + healSignal)
            dao.insertRaidSession(session.copy(signal = newSig))
            log(uid, "👑 [Корона Истинной Крови]: Восстановлено +2% ($healSignal HP) Сигнала при ударе!", "info")
        }
        if (player.skill_berserk_3 == 1) {
            val heal = maxOf(1, (finalPlayerDamage * 0.05).toInt())
            dao.updatePlayer(player.copy(hp = minOf(player.max_hp, player.hp + heal)))
            log(uid, "🧛 [Вампиризм]: Восстановлено +$heal Сигнала.", "info")
        }

        val nextTurn = session.combat_turn + 1

        if (newEnemyHp <= 0) {
            log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована.", "loot")
            recordEnemyKill(villain.name)
            val equippedAll = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
            val hasMaxwellsDemon = equippedAll.any { it.item_id == "maxwells_demon" }
            val hasOblivionChip = equippedAll.any { it.item_id == "oblivion_chip" }
            val isDoubleDrop = session.active_mutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_DOUBLE_DROP
            val rawCoins = if (weaponItem?.item_id == "cache_wiper") 0L else villain.coin.toLong()
            val baseCoins = if (isDoubleDrop) rawCoins * 2 else rawCoins
            val tax = if (hasMaxwellsDemon) (baseCoins * 0.1).toLong() else 0L

            val activeOverchargeTier = getOverchargeTier(uid)
            val ocLootMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(activeOverchargeTier)
            val finalCoins = ((baseCoins - tax) * ocLootMult).toLong()

            val baseXpGain = if (weaponItem?.item_id == "cache_wiper") 0L else villain.xp
            val multXp = if (isDoubleDrop) baseXpGain * 2 else baseXpGain
            val baseFinalXp = if (hasOblivionChip) multXp * 2 else multXp
            val finalXpGain = (baseFinalXp * ocLootMult).toLong()

            var newBufferItems = session.buffer_items
            val bonusOverchargeItem = io.eidos.zerolayer.domain.combat.CombatEngine.rollOverchargeBonusItem(activeOverchargeTier, session.depth)
            if (bonusOverchargeItem != null) {
                newBufferItems = if (newBufferItems.isEmpty()) bonusOverchargeItem else "$newBufferItems,$bonusOverchargeItem"
                val bonusMeta = getItemMetadata(bonusOverchargeItem)
                log(uid, "🔥 [ПРОТОКОЛ ПЕРЕГРУЗКИ]: Перегрузка выбила редкий трофей: [${bonusMeta?.name ?: bonusOverchargeItem}]!", "loot")
            }

            val updatedSession = session.copy(
                current_enemy_id = null,
                current_enemy_hp = 0,
                buffer_xp = session.buffer_xp + finalXpGain,
                buffer_coins = session.buffer_coins + finalCoins,
                buffer_items = newBufferItems,
                kills = session.kills + 1,
                combat_turn = 0,
                damage_buffer = 0
            )
            dao.insertRaidSession(updatedSession)
            if (activeOverchargeTier > 0) {
                log(uid, "🔥 [ПРОТОКОЛ ПЕРЕГРУЗКИ x${ocLootMult}]: Модифицированная награда (+${finalCoins} BC, +${finalXpGain} XP)!", "loot")
            } else if (isDoubleDrop) {
                log(uid, "💎 [СИНГУЛЯРНЫЙ РЕЗОНАНС]: Удвоенная награда за победу (+${finalCoins} BC, +${finalXpGain} XP)!", "loot")
            }
            if (hasOblivionChip && finalXpGain > 0) {
                log(uid, "🔮 [Чип Забвения]: Получен удвоенный опыт (2.0x -> +$finalXpGain XP)!", "loot")
            }
            if (tax > 0) {
                log(uid, "😈 [ДЕМОН МАКСВЕЛЛА]: Изъят налог 10% с трофеев врага (-$tax BC).", "error")
            }
        } else {
            // --- Enemy Turn ---
            // Grandfather paradox logic
            val hasParadox = weaponItem?.item_id == "grandfather_paradox"
            val evasionChance = io.eidos.zerolayer.domain.combat.CombatEngine.calculateEvasionChance(
                playerDefense = activeStats.defense,
                hasTacticalHelmet = headItem?.item_id == "tactical_helmet"
            )
            val isEvaded = (0..100).random() < evasionChance

            if (isEvaded) {
                // Gain overdrive charge on successful dodge (+25%)
                val dodgeCharge = getOverdriveCharge(uid) + io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_DODGE
                setOverdriveCharge(uid, dodgeCharge)
                _combatEventFlow.tryEmit(CombatVisualEvent(isDodge = true))

                log(uid, "УКЛОНЕНИЕ: Сдвиг сигнала. Атака от ${villain.name} промахнулась (+25% Овердрайв).", "info")
                dao.insertRaidSession(session.copy(current_enemy_hp = newEnemyHp, combat_turn = nextTurn))
            } else {
                val playerPower = activeStats.attack + activeStats.defense + activeStats.luck
                val rawVillainAtk = io.eidos.zerolayer.domain.combat.CombatEngine.calculateScaledEnemyAtk(
                    villainAtk = villain.atk,
                    playerPower = playerPower,
                    depth = session.depth
                )
                val ocAtkMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeEnemyAtkMultiplier(getOverchargeTier(uid))
                val scaledVillainAtk = (rawVillainAtk * ocAtkMult).toInt()

                val baseEnemyDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateBaseEnemyDamage(
                    scaledEnemyAtk = scaledVillainAtk,
                    playerDefense = activeStats.defense
                )
                var enemyDamage = baseEnemyDamage

                // Maxwell Vulnerability: +25% damage taken from enemies
                if (io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_VULNERABILITY) ||
                    io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_FORTUNE)) {
                    enemyDamage = (enemyDamage * 1.25f).toInt()
                }

                // Judas shell cursed defense
                if (armorItem?.item_id == "judas_shell") {
                    enemyDamage = maxOf(1, scaledVillainAtk - 75)
                }

                if (hasParadox && nextTurn <= 3) {
                    val newDmgBuf = session.damage_buffer + enemyDamage
                    log(uid, "⏳ [Парадокс Деда]: Отражен входящий удар (-$enemyDamage) в буфер ($newDmgBuf/3 ходов).", "info")
                    dao.insertRaidSession(session.copy(current_enemy_hp = newEnemyHp, combat_turn = nextTurn, damage_buffer = newDmgBuf))
                } else {
                    var totalIncoming = enemyDamage
                    if (hasParadox && nextTurn == 4) {
                        totalIncoming += session.damage_buffer
                        log(uid, "💥 [Парадокс Деда]: Временной барьер лопнул! Накопленный урон ($totalIncoming) ударил по вам!", "error")
                    }

                    _combatEventFlow.tryEmit(CombatVisualEvent(isPlayerHit = true, incomingDamage = totalIncoming))

                    // Cursed Armor error_404_mirror logic
                    val mirrorRoll = (0..100).random()
                    if (armorItem?.item_id == "error_404_mirror" && mirrorRoll < 50) {
                        log(uid, "🪞 [Зеркало 404]: Входящий урон ($totalIncoming) отражен обратно во врага!", "combat")
                        dao.insertRaidSession(session.copy(
                            current_enemy_hp = newEnemyHp - totalIncoming,
                            combat_turn = nextTurn,
                            damage_buffer = 0
                        ))
                    } else {
                        val newSignal = session.signal - totalIncoming

                        // Cursed Armor thermonuclear_shroud logic
                        if (armorItem?.item_id == "thermonuclear_shroud" && newSignal <= 0) {
                            log(uid, "☢ [Термоядерный Саван]: Инициирован самоподрыв! Враг уничтожен. Буфер рейда сожжен.", "error")
                            dao.insertRaidSession(session.copy(
                                current_enemy_id = null,
                                current_enemy_hp = 0,
                                buffer_coins = 0,
                                buffer_items = "",
                                signal = 1,
                                combat_turn = 0,
                                damage_buffer = 0
                            ))
                        } else {
                            log(uid, "УРОН: ${villain.name} атакует! -$totalIncoming Сигнала/HP.", "combat")
                            dao.updatePlayer(player.copy(hp = maxOf(0, player.hp - totalIncoming)))
                            dao.insertRaidSession(session.copy(
                                current_enemy_hp = newEnemyHp,
                                signal = newSignal,
                                combat_turn = nextTurn,
                                damage_buffer = 0
                            ))

                            // Armor/helmet durability wear
                            val loss = maxOf(1f, totalIncoming * 0.1f)
                            if (armorItem != null) {
                                val newArmDur = maxOf(0f, armorItem.durability - loss)
                                dao.updateInventoryItem(armorItem.copy(durability = newArmDur))
                                if (newArmDur <= 0f) log(uid, "🚨 [СИСТЕМНЫЙ СБОЙ: БРОНЯ ДЕАКТИВИРОВАНА]", "error")
                            }
                            if (headItem != null) {
                                val newHeadDur = maxOf(0f, headItem.durability - loss)
                                dao.updateInventoryItem(headItem.copy(durability = newHeadDur))
                                if (newHeadDur <= 0f) log(uid, "🚨 [СИСТЕМНЫЙ СБОЙ: ШЛЕМ ДЕАКТИВИРОВАН]", "error")
                            }
                        }
                    }
                }
            }
            checkDeath(uid)
        }
    }

    suspend fun triggerOverdrive(uid: Long) = dbMutex.withLock {
        val session = dao.getRaidSession(uid) ?: return@withLock
        val player = dao.getPlayer(uid) ?: return@withLock
        val currentCharge = getOverdriveCharge(uid)
        if (currentCharge < io.eidos.zerolayer.domain.combat.CombatEngine.OVERDRIVE_MAX_CHARGE || session.current_enemy_id == null) {
            return@withLock
        }

        setOverdriveCharge(uid, 0)

        val activeStats = getActiveStats(uid)
        val inventory = dao.getInventoryFlow(uid).first()
        val weaponItem = inventory.find { it.slot == "weapon" && it.is_equipped }
        val weaponMultiplier = if (weaponItem != null && weaponItem.durability > 0f) {
            getItemMetadata(weaponItem.item_id)?.multiplier ?: 1.0f
        } else 1.0f

        val overdriveDmg = io.eidos.zerolayer.domain.combat.CombatEngine.calculateOverdriveDamage(activeStats.attack, weaponMultiplier)
        val villain = io.eidos.zerolayer.data.GameData.VILLAINS.find { it.name == session.current_enemy_id }
        val enemyHp = session.current_enemy_hp
        val newEnemyHp = maxOf(0, enemyHp - overdriveDmg)

        val restoredSig = minOf(100, session.signal + 15)
        val restoredHp = minOf(player.max_hp, player.hp + maxOf(1, (player.max_hp * 0.15).toInt()))
        dao.updatePlayer(player.copy(hp = restoredHp))

        log(uid, "⚡ [СБРОС ЯДРА // OVERDRIVE]: Чистый крит -$overdriveDmg урона в обход брони! Враг оглушен. Восстановлено +15% Сигнала!", "combat")

        _combatEventFlow.tryEmit(CombatVisualEvent(
            damage = overdriveDmg,
            isCrit = true,
            isOverdrive = true,
            isPlayerHit = false
        ))

        if (newEnemyHp <= 0) {
            log(uid, "УСПЕХ: Цель ${session.current_enemy_id} стерта детонацией Ядра.", "loot")
            recordEnemyKill(session.current_enemy_id ?: "")
            val rawCoins = villain?.coin?.toLong() ?: 50L
            val rawXp = villain?.xp ?: 100L
            val ocLootMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(getOverchargeTier(uid))
            val finalCoins = (rawCoins * ocLootMult).toLong()
            val finalXp = (rawXp * ocLootMult).toLong()

            dao.insertRaidSession(session.copy(
                current_enemy_id = null,
                current_enemy_hp = 0,
                signal = restoredSig,
                buffer_coins = session.buffer_coins + finalCoins,
                buffer_xp = session.buffer_xp + finalXp,
                kills = session.kills + 1,
                combat_turn = 0
            ))
        } else {
            // Enemy is stunned for 1 turn (no enemy attack)
            dao.insertRaidSession(session.copy(
                current_enemy_hp = newEnemyHp,
                signal = restoredSig
            ))
        }
    }

    private suspend fun checkDeath(uid: Long) {
        val session = dao.getRaidSession(uid) ?: return
        if (session.signal <= 0) {
            val inventory = dao.getInventoryFlow(uid).first()
            val aegisItem = inventory.find { it.item_id == "aegis" && it.quantity > 0 }
            if (aegisItem != null) {
                if (aegisItem.quantity > 1) {
                    dao.updateInventoryItem(aegisItem.copy(quantity = aegisItem.quantity - 1))
                } else {
                    dao.deleteInventoryItem(aegisItem)
                }
                val player = dao.getPlayer(uid)
                if (player != null) {
                    dao.updatePlayer(player.copy(hp = 1))
                }
                dao.insertRaidSession(session.copy(signal = 1))
                log(uid, "🛡 [ЭГИДА БЕССМЕРТИЯ]: Смертельный урон заблокирован! Артефакт рассыпался в прах, восстановив 1 HP Сигнала.", "info")
                return
            }

            io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context).logRaidFailedAtAnomaly(
                session.current_anomaly_id ?: "signal_collapse",
                session.depth
            )
            log(uid, "💀 КРИТИЧЕСКИЙ СБОЙ: Нейро-связь разорвана. Экстренная эвакуация.", "error")

            val player = dao.getPlayer(uid)
            if (player != null) {
                // Break equipped items (Weapon, Armor, Head) by 10%
                val inventory = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
                inventory.forEach {
                    if (it.slot in listOf("weapon", "armor", "head")) {
                        dao.updateInventoryItem(it.copy(durability = maxOf(0f, it.durability - 10f)))
                    }
                }

                // Chance to completely break an active equipped item (25% chance)
                val equippedCombatItems = inventory.filter { it.slot in listOf("weapon", "armor", "head") }
                if (equippedCombatItems.isNotEmpty() && (0..100).random() < 25) {
                    val brokenItem = equippedCombatItems.random()
                    dao.updateInventoryItem(brokenItem.copy(durability = 0f))
                    val brokenName = getItemMetadata(brokenItem.item_id)?.name ?: brokenItem.item_id.uppercase()
                    log(uid, "🚨 [СНАРЯЖЕНИЕ СЛОМАНО]: Ваша вещь $brokenName полностью сломалась при экстренной эвакуации!", "error")
                }

                val deathMask = dao.getInventoryFlow(uid).first().find { it.item_id == "death_mask" && it.is_equipped } != null
                if (deathMask) {
                    log(uid, "💀 [Маска Мертвеца]: Весь ваш инвентарь стерт безвозвратно!", "error")
                    val fullInventory = dao.getInventoryFlow(uid).first()
                    fullInventory.forEach { dao.deleteInventoryItem(it) }
                }

                // Create a Grave at the depth of death (deduplicate existing grave at this depth)
                if (session.buffer_coins > 0 || session.buffer_items.isNotEmpty()) {
                    val existingGraves = dao.getAllGraves().filter { it.uid == uid && it.depth == session.depth }
                    existingGraves.forEach { dao.deleteGrave(it) }
                    val cleanItems = session.buffer_items.split(",").map { it.trim() }.filter { it.isNotBlank() }.joinToString(",")
                    val grave = Grave(
                        uid = uid,
                        owner_name = player.username ?: player.first_name ?: "Неизвестный Оператор",
                        depth = session.depth,
                        coins = session.buffer_coins,
                        items = cleanItems
                    )
                    dao.insertGrave(grave)
                    log(uid, "🪦 [ЦЕЛОСТНОСТЬ УТРАЧЕНА]: На глубине ${session.depth}м образовалась ваша Могила с ${session.buffer_coins} BC и предметами: [$cleanItems]. Её могут найти другие игроки!", "error")
                }

                dao.updatePlayer(player.copy(
                    max_depth = maxOf(player.max_depth, session.depth),
                    hp = 10
                ))
            }
            dao.deleteRaidSession(uid)
        }
    }

    suspend fun endRaid(uid: Long) {
        val session = dao.getRaidSession(uid) ?: return
        val player = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()

        // 15% bot attack roll upon return IF NOT SHIELDED
        var currentBiocoin = player.biocoin
        val isShielded = player.pvp_shield_until > now
        val pvpRoll = (0..100).random()
        if (!isShielded && pvpRoll < 15) {
            val lostCoins = maxOf(0L, (currentBiocoin * 0.05).toLong())
            currentBiocoin = maxOf(0L, currentBiocoin - lostCoins)
            log(uid, "🚨 [ВЗЛОМ ИЗВНЕ]: Пока вы возвращались, на ваш Хаб напал бот-охотник! Похищено -$lostCoins BC.", "error")
        }

        val bonusXpMult = if (player.is_premium) 1.5f else 1.0f
        val calculatedXp = (session.buffer_xp * bonusXpMult).toLong()
        
        // Holo Poverty limit check (max 500 BC extracted)
        val equippedItems = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
        val hasHoloPoverty = equippedItems.any { it.item_id == "holo_poverty" }
        val finalCoins = if (hasHoloPoverty) minOf(500L, session.buffer_coins) else session.buffer_coins
        if (hasHoloPoverty && session.buffer_coins > 500L) {
            log(uid, "🥋 [ГОЛОГРАММА НИЩЕТЫ]: Вынос валюты ограничен лимитом в 500 BC.", "info")
        }

        val tempPlayer = player.copy(
            xp = player.xp + calculatedXp,
            biocoin = currentBiocoin + finalCoins,
            max_depth = maxOf(player.max_depth, session.depth),
            raids_done = player.raids_done + 1
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            handleLevelUpRewards(uid, player.level, updatedPlayer.level)
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
        }

        // Transfer buffer items to inventory using addInventory (ensures stacking and valid formatting)
        if (session.buffer_items.isNotEmpty()) {
            val items = session.buffer_items.split(",").map { it.trim() }.filter { it.isNotBlank() }
            items.forEach { itemId ->
                addInventory(uid, itemId, 1)
            }
        }

        dao.deleteRaidSession(uid)
        log(uid, "📡 Экспедиция завершена. Прибыли успешно выгружены в буфер Хаба.", "info")
    }

    suspend fun acceptMaxwellContract(uid: Long, contractId: String) {
        val session = dao.getRaidSession(uid) ?: return
        val player = dao.getPlayer(uid) ?: return
        val nowSec = System.currentTimeMillis() / 1000L

        when (contractId) {
            "blood_overclock" -> {
                // Reduces Max HP by 20% until end of raid, grants +35% ATK and +15% Crit
                val hpReduction = maxOf(10, (player.max_hp * 0.20f).toInt())
                val newMaxHp = maxOf(20, player.max_hp - hpReduction)
                val newHp = minOf(newMaxHp, player.hp)
                val newSignal = minOf(100, (newHp.toFloat() / newMaxHp * 100).toInt())
                dao.updatePlayer(player.copy(
                    max_hp = newMaxHp,
                    hp = newHp,
                    anomalyBuffType = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_OVERCLOCK,
                    anomalyBuffExpiry = nowSec + 3600L
                ))
                dao.insertRaidSession(session.copy(
                    signal = newSignal,
                    raid_damage_buff = true,
                    next_event_type = "scan"
                ))
                log(uid, "🩸 [ДЕМОН МАКСВЕЛЛА]: Контракт «Кровавый Оверклок» заключен! Max HP -$hpReduction, но урон +35% и крит +15%!", "combat")
            }
            "fortune_inversion" -> {
                // Incoming damage from enemies and traps +25%, drop rate x2
                dao.updatePlayer(player.copy(
                    anomalyBuffType = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_FORTUNE,
                    anomalyBuffExpiry = nowSec + 3600L
                ))
                dao.insertRaidSession(session.copy(next_event_type = "scan"))
                log(uid, "🎲 [ДЕМОН МАКСВЕЛЛА]: Контракт «Инверсия Фортуны» подписан! Урон +25%, шанс кэшей и реликвий удвоен!", "loot")
            }
            "socket_mutation" -> {
                // Deducts 1500 BC. 50% Rainbow socket, 50% Locked socket
                if (player.biocoin < 1500L && session.buffer_coins < 1500L) {
                    log(uid, "❌ [ДЕМОН МАКСВЕЛЛА]: Недостаточно BioCoins (требуется 1500 BC)!", "error")
                    return
                }
                if (player.biocoin >= 1500L) {
                    dao.updatePlayer(player.copy(biocoin = player.biocoin - 1500L))
                } else {
                    dao.insertRaidSession(session.copy(buffer_coins = session.buffer_coins - 1500L))
                }

                val equippedItems = dao.getInventoryFlow(uid).first()
                val weapon = equippedItems.firstOrNull { it.is_equipped && it.slot == "weapon" } 
                    ?: equippedItems.firstOrNull { it.slot == "weapon" }
                
                if (weapon != null) {
                    val eq = PoECraftEngine.getOrGenerateEquipment(weapon, "rare")
                    val isSuccess = (0..100).random() < 50
                    val sockets = eq.socketColors.toMutableList()
                    if (sockets.isEmpty()) {
                        sockets.add(if (isSuccess) ChipSocketColor.WHITE_RAINBOW else ChipSocketColor.LOCKED)
                    } else {
                        val targetIdx = sockets.indices.random()
                        sockets[targetIdx] = if (isSuccess) ChipSocketColor.WHITE_RAINBOW else ChipSocketColor.LOCKED
                    }
                    val updatedEq = eq.copy(
                        maxSockets = maxOf(eq.maxSockets, sockets.size),
                        socketColors = sockets
                    )
                    dao.updateInventoryItem(weapon.copy(custom_data = PoECraftEngine.serializeEquipment(updatedEq)))
                    if (isSuccess) {
                        log(uid, "🔮 [ДЕМОН МАКСВЕЛЛА]: Квантовая Мутация УСПЕШНА! Оружие получило Радужный сокет (+25% ко всем чипам)!", "loot")
                    } else {
                        log(uid, "💀 [ДЕМОН МАКСВЕЛЛА]: Квантовая Мутация дала сбой! Сокет оружия заблокирован энтропией!", "error")
                    }
                } else {
                    log(uid, "🔮 [ДЕМОН МАКСВЕЛЛА]: Энергия мутации рассеялась: оружие не найдено в слотах!", "info")
                }
                val currentSession = dao.getRaidSession(uid) ?: session
                dao.insertRaidSession(currentSession.copy(next_event_type = "scan"))
            }
            "memory_sacrifice" -> {
                // Deducts 250 XP, restores 100% energy, grants 1x abyssal_key
                val newXp = maxOf(0L, player.xp - 250L)
                dao.updatePlayer(player.copy(
                    xp = newXp,
                    energy = player.max_energy
                ))
                val newBuffer = if (session.buffer_items.isEmpty()) "abyssal_key" else "${session.buffer_items},abyssal_key"
                dao.insertRaidSession(session.copy(
                    buffer_items = newBuffer,
                    next_event_type = "scan"
                ))
                log(uid, "🧠 [ДЕМОН МАКСВЕЛЛА]: Жертва Памяти принята (-250 XP). Энергия восстановлена на 100%, получен [Ключ Бездны]!", "heal")
            }
            "entropy_shield" -> {
                // Glitch effect on UI for 30 mins, 100% immunity to traps in raid
                dao.updatePlayer(player.copy(
                    isGlitched = true,
                    lastHardGlitchTimestamp = System.currentTimeMillis(),
                    anomalyBuffType = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_MAXWELL_ENTROPY_SHIELD,
                    anomalyBuffExpiry = nowSec + 1800L
                ))
                dao.insertRaidSession(session.copy(next_event_type = "scan"))
                log(uid, "🛡️ [ДЕМОН МАКСВЕЛЛА]: Энтропийный Щит развернут! 100% иммунитет к ловушкам Слоя активирован на 30 мин.", "info")
            }
            else -> {
                dao.insertRaidSession(session.copy(next_event_type = "scan"))
            }
        }
    }

    suspend fun betMaxwellDemonHp(uid: Long) {
        acceptMaxwellContract(uid, "blood_overclock")
    }

    suspend fun betMaxwellDemonBuffer(uid: Long) {
        acceptMaxwellContract(uid, "fortune_inversion")
    }

    suspend fun ignoreMaxwellDemon(uid: Long) {
        val session = dao.getRaidSession(uid) ?: return
        dao.insertRaidSession(session.copy(next_event_type = "scan"))
        log(uid, "🚶 [ДЕМОН МАКСВЕЛЛА]: Вы проигнорировали опасную сделку и продолжили путь по Слою.", "info")
    }

    suspend fun getRadioMessagesFlow(uid: Long) = dao.getRadioMessagesFlow(uid)

    suspend fun getUnclaimedRadioMessagesCountFlow(uid: Long) = dao.getUnclaimedMessagesCountFlow(uid)

    suspend fun checkAndGenerateRadioMessages(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val existing = dao.getAllRadioMessages(uid)

        // 1. Shadow Broker trigger (raids_done >= 5)
        if (player.raids_done >= 5 && existing.none { it.sender == "Теневой Брокер" }) {
            dao.insertRadioMessage(
                RadioMessageEntity(
                    uid = uid,
                    sender = "Теневой Брокер",
                    title = "ПЕРЕХВАЧЕН ПАКЕТ ДАННЫХ",
                    body = "Перехвачен пакет данных с чертежом для модификации чипов. Забирай кредиты и не привлекай внимания Ищеек.",
                    rewardCoins = 150L,
                    rewardXp = 0L,
                    isClaimed = false
                )
            )
            log(uid, "📟 [ТЕРМИНАЛ СВЯЗИ]: Получено новое входящее сообщение от Теневого Брокера!", "info")
        }

        // 2. SOS Shard trigger (max_depth >= 100)
        if (player.max_depth >= 100 && existing.none { it.sender == "Неизвестный Осколок (SOS)" }) {
            dao.insertRadioMessage(
                RadioMessageEntity(
                    uid = uid,
                    sender = "Неизвестный Осколок (SOS)",
                    title = "ЗАПРОС ЭВАКУАЦИИ ПАМЯТИ",
                    body = "Мой сигнал угасает в глубинах Нулевого Слоя... Забери остатки моей памяти и нейро-опыт, чтобы продолжить путь.",
                    rewardCoins = 0L,
                    rewardXp = 100L,
                    isClaimed = false
                )
            )
            log(uid, "📟 [ТЕРМИНАЛ СВЯЗИ]: Перехвачен сигнал бедствия из глубины Нулевого Слоя!", "info")
        }

        // 3. EIDOS Core trigger (streak >= 3)
        if (player.streak >= 3 && existing.none { it.sender == "Ядро EIDOS" }) {
            dao.insertRadioMessage(
                RadioMessageEntity(
                    uid = uid,
                    sender = "Ядро EIDOS",
                    title = "СИНХРОНИЗАЦИЯ СЕТИ 3D+",
                    body = "Начислена системная премия за непрерывную квантовую синхронизацию терминала в течение трех циклов.",
                    rewardCoins = 300L,
                    rewardXp = 50L,
                    isClaimed = false
                )
            )
            log(uid, "📟 [ТЕРМИНАЛ СВЯЗИ]: Начислена награда от Центрального Ядра EIDOS!", "loot")
        }
    }

    suspend fun claimRadioMessageReward(uid: Long, messageId: Long) {
        val player = dao.getPlayer(uid) ?: return
        val messages = dao.getAllRadioMessages(uid)
        val target = messages.firstOrNull { it.id == messageId } ?: return
        if (target.isClaimed) return

        val updatedPlayer = player.copy(
            biocoin = player.biocoin + target.rewardCoins,
            xp = player.xp + target.rewardXp
        )
        val (finalPlayer, _) = updatedPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(finalPlayer)
        dao.updateRadioMessage(target.copy(isClaimed = true))
        log(uid, "🎁 [ТЕРМИНАЛ СВЯЗИ]: Получено вознаграждение: +${target.rewardCoins} BC, +${target.rewardXp} XP!", "loot")
    }

    suspend fun resolveHardGlitch(uid: Long, chosenIndex: Int, correctIndex: Int) {
        val player = dao.getPlayer(uid) ?: return
        if (chosenIndex == correctIndex) {
            val rewardCoins = 200L
            val updated = player.copy(
                biocoin = player.biocoin + rewardCoins,
                glitchEncounterCounter = 0,
                lastHardGlitchTimestamp = System.currentTimeMillis(),
                isGlitched = false
            )
            dao.updatePlayer(updated)
            log(uid, "⚡ [СТАБИЛИЗАЦИЯ ЯДРА]: Критический сбой успешно нейтрализован! Получено +$rewardCoins BC.", "heal")
        } else {
            val damageHp = maxOf(1, (player.hp * 0.15f).toInt())
            val updated = player.copy(
                hp = maxOf(1, player.hp - damageHp),
                anomalyBuffType = null,
                anomalyBuffExpiry = 0L,
                lastHardGlitchTimestamp = System.currentTimeMillis()
            )
            dao.updatePlayer(updated)
            log(uid, "💥 [СИСТЕМНЫЙ СБОЙ]: Неверный протокол стабилизации! Получено -$damageHp HP урона, баффы сброшены.", "error")
        }
    }

    suspend fun scanSector(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val session = dao.getRaidSession(uid) ?: return

        if (session.is_scanned) {
            log(uid, "🔍 [СКАНИРОВАНИЕ]: Сектор на глубине ${session.depth}м уже просканирован. Сделайте шаг вглубь Бездны для сканирования следующей локации.", "info")
            return
        }

        if (player.energy < 5) {
            log(uid, "❌ Недостаточно энергии для сканирования секторов Бездны. Требуется 5 энергии.", "error")
            return
        }

        // Deduct 5 energy
        val newEnergy = maxOf(0, player.energy - 5)
        dao.updatePlayer(player.copy(energy = newEnergy))
        if (newEnergy < player.max_energy) {
            val recoveryDelayMs = (player.max_energy - newEnergy).toLong() * 5 * 60 * 1000L
            io.eidos.zerolayer.ui.utils.EnergyRecoveryWorker.schedule(context, recoveryDelayMs)
        }

        val roll = (0..100).random()
        val allMetas = getAllItemsMetadata().filter { it.id != "biocoin" }

        when {
            roll < 35 -> { // Found a random item or material
                val lootMeta = if ((0..100).random() < 50) rollNormalLoot() else null
                val foundItemId = lootMeta?.id ?: listOf("battery", "energy_cell", "eidos_shard", "medkit", "master_key", "crowbar").random()
                val lootName = getItemMetadata(foundItemId)?.name ?: foundItemId
                val updatedItems = if (session.buffer_items.isEmpty()) foundItemId else "${session.buffer_items},$foundItemId"
                dao.insertRaidSession(session.copy(buffer_items = updatedItems, is_scanned = true))
                log(uid, "🔍 [ИМПУЛЬСНОЕ СКАНИРОВАНИЕ]: Сканер обнаружил скрытый контейнер! Извлечен предмет: [$lootName]. Сектор изучен.", "loot")
            }
            roll < 70 -> { // Found BioCoins or telemetry XP
                val bonusBc = (25..90).random().toLong()
                val bonusXp = (30..120).random().toLong()
                dao.insertRaidSession(session.copy(
                    buffer_coins = session.buffer_coins + bonusBc,
                    buffer_xp = session.buffer_xp + bonusXp,
                    is_scanned = true
                ))
                log(uid, "🔍 [ИМПУЛЬСНОЕ СКАНИРОВАНИЕ]: Перехвачен незашифрованный архив (+${bonusBc} BC, +${bonusXp} XP)! Сектор изучен.", "info")
            }
            else -> { // Nothing found
                dao.insertRaidSession(session.copy(is_scanned = true))
                log(uid, "🔍 [ИМПУЛЬСНОЕ СКАНИРОВАНИЕ]: Аномальных сигналов не обнаружено. Сектор чист.", "info")
            }
        }
    }

    suspend fun useActiveAbility(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val session = dao.getRaidSession(uid) ?: return
        val enemyId = session.current_enemy_id ?: return

        if (player.energy < 15) {
            log(uid, "❌ Недостаточно энергии для использования активной способности. Требуется 15 энергии.", "error")
            return
        }

        // Deduct 15 energy
        val newEnergy = maxOf(0, player.energy - 15)
        val updatedPlayer = player.copy(energy = newEnergy)
        dao.updatePlayer(updatedPlayer)
        if (newEnergy < player.max_energy) {
            val recoveryDelayMs = (player.max_energy - newEnergy).toLong() * 5 * 60 * 1000L
            io.eidos.zerolayer.ui.utils.EnergyRecoveryWorker.schedule(context, recoveryDelayMs)
        }

        val villain = GameData.VILLAINS.find { it.name == enemyId } ?: return

        // Calculate custom effect based on faction
        when (player.faction) {
            "МАТЕРИЯ" -> {
                val extraDamage = (player.attack * 1.5).toInt()
                val lootedCoins = (15..45).random()
                val newEnemyHp = maxOf(0, session.current_enemy_hp - extraDamage)
                val updatedSession = session.copy(
                    current_enemy_hp = newEnemyHp,
                    buffer_coins = session.buffer_coins + lootedCoins
                )
                dao.insertRaidSession(updatedSession)
                log(uid, "⚡ [АКТИВАЦИЯ СПОСОБНОСТИ: ЗОЛОТОЙ ИМПУЛЬС] Нанесено $extraDamage урона. Дренировано +$lootedCoins BC у цели!", "combat")
                
                if (newEnemyHp <= 0) {
                    log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована активной способностью.", "loot")
                    val updatedSessionDefeated = updatedSession.copy(
                        current_enemy_id = null,
                        current_enemy_hp = 0,
                        buffer_xp = updatedSession.buffer_xp + villain.xp,
                        kills = updatedSession.kills + 1,
                        combat_turn = 0,
                        damage_buffer = 0
                    )
                    dao.insertRaidSession(updatedSessionDefeated)
                }
            }
            "РАЗУМ" -> {
                val healAmount = 25
                val shieldDamage = (player.attack * 0.8).toInt()
                val newSignal = minOf(100, session.signal + healAmount)
                val newEnemyHp = maxOf(0, session.current_enemy_hp - shieldDamage)
                val updatedSession = session.copy(
                    signal = newSignal,
                    current_enemy_hp = newEnemyHp
                )
                dao.insertRaidSession(updatedSession)
                log(uid, "⚡ [АКТИВАЦИЯ СПОСОБНОСТИ: НЕЙРО-ЩИТ] Целостность сигнала восстановлена на +$healAmount%. Нанесено $shieldDamage урона врагу.", "combat")
                
                if (newEnemyHp <= 0) {
                    log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована активной способностью.", "loot")
                    val updatedSessionDefeated = updatedSession.copy(
                        current_enemy_id = null,
                        current_enemy_hp = 0,
                        buffer_xp = updatedSession.buffer_xp + villain.xp,
                        kills = updatedSession.kills + 1,
                        combat_turn = 0,
                        damage_buffer = 0
                    )
                    dao.insertRaidSession(updatedSessionDefeated)
                }
            }
            "ТЕХНО" -> {
                val criticalDamage = (player.attack * 2.8).toInt()
                val newEnemyHp = maxOf(0, session.current_enemy_hp - criticalDamage)
                val updatedSession = session.copy(current_enemy_hp = newEnemyHp)
                dao.insertRaidSession(updatedSession)
                log(uid, "⚡ [АКТИВАЦИЯ СПОСОБНОСТИ: КВАНТОВЫЙ ВЗРЫВ] Протоколы взлома перегружены! Критический удар: $criticalDamage урона!", "combat")
                
                if (newEnemyHp <= 0) {
                    log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована активной способностью.", "loot")
                    val updatedSessionDefeated = updatedSession.copy(
                        current_enemy_id = null,
                        current_enemy_hp = 0,
                        buffer_xp = updatedSession.buffer_xp + villain.xp,
                        kills = updatedSession.kills + 1,
                        combat_turn = 0,
                        damage_buffer = 0
                    )
                    dao.insertRaidSession(updatedSessionDefeated)
                }
            }
            else -> {
                val absoluteDamage = (player.attack * 3.5).toInt()
                val newEnemyHp = maxOf(0, session.current_enemy_hp - absoluteDamage)
                val updatedSession = session.copy(current_enemy_hp = newEnemyHp)
                dao.insertRaidSession(updatedSession)
                log(uid, "⚡ [ПРОТОКОЛ АРХИТЕКТОРОВ: УДАЛЕНИЕ ОБЪЕКТА] Стирание кода цели! Нанесено $absoluteDamage урона!", "combat")
                
                if (newEnemyHp <= 0) {
                    log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована активной способностью.", "loot")
                    val updatedSessionDefeated = updatedSession.copy(
                        current_enemy_id = null,
                        current_enemy_hp = 0,
                        buffer_xp = updatedSession.buffer_xp + villain.xp,
                        kills = updatedSession.kills + 1,
                        combat_turn = 0,
                        damage_buffer = 0
                    )
                    dao.insertRaidSession(updatedSessionDefeated)
                }
            }
        }
    }

    suspend fun startDecryption(uid: Long, item: InventoryItem) {
        if (item.item_id != "corrupted_data_cluster") return
        val player = dao.getPlayer(uid) ?: return
        val validation = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.validateAndSanitizeTimestamp(context)
        val now = validation.sanitizedCurrentTime

        var durationMs = 4 * 3600 * 1000L // Base 4 hours
        if (player.faction in listOf("Технократы", "Техно")) {
            durationMs = 2 * 3600 * 1000L // 2 hours for Techno faction
        }

        val inventory = dao.getInventoryFlow(uid).first()
        val hasDecryptor = inventory.any { 
            (it.item_id in listOf("data_slicer", "data_spike", "decryptor", "overclocker") || getItemMetadata(it.item_id)?.name?.contains("Дешифратор", ignoreCase = true) == true) && it.quantity > 0
        }
        if (hasDecryptor) {
            durationMs /= 2 // Decryptor item accelerates in 2x
        }

        val endTime = now + durationMs
        val updatedItem = item.copy(custom_data = "decrypt:$endTime")
        dao.updateInventoryItem(updatedItem)

        // Schedule background notification via WorkManager
        io.eidos.zerolayer.ui.utils.DecryptionWorker.schedule(context, "Зашифрованный Кэш", durationMs)

        val hours = durationMs / (3600 * 1000L)
        val mins = (durationMs % (3600 * 1000L)) / (60 * 1000L)
        val timeStr = if (hours > 0) "${hours}ч ${mins}мин" else "${mins}мин"
        log(uid, "🔓 [ДЕШИФРАТОР КЭШЕЙ]: Запущен подбор ключей Кластера. Время: $timeStr.", "info")
    }

    suspend fun instantDecrypt(uid: Long, item: InventoryItem) {
        if (item.item_id != "corrupted_data_cluster") return
        val player = dao.getPlayer(uid) ?: return
        val cost = 500L
        if (player.biocoin < cost) {
            log(uid, "Недостаточно BioCoin. Моментальный обход блокировки требует $cost BC.", "error")
            return
        }
        
        dao.updatePlayer(player.copy(biocoin = player.biocoin - cost))
        val updatedItem = item.copy(custom_data = "decrypt:0")
        dao.updateInventoryItem(updatedItem)
        log(uid, "⚡ [СКОРОСТНОЙ ХАКИНГ]: Алгоритмы форсированы за $cost BC. Блокировка снята!", "success")
        claimDecryptedCache(uid, updatedItem)
    }

    suspend fun claimDecryptedCache(uid: Long, item: InventoryItem): List<InventoryItem>? {
        if (item.item_id != "corrupted_data_cluster") return null
        val custom = item.custom_data ?: return null
        if (!custom.startsWith("decrypt:")) return null
        val endTime = custom.substringAfter("decrypt:").toLongOrNull() ?: return null
        
        val validation = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.validateAndSanitizeTimestamp(context)
        val now = validation.sanitizedCurrentTime

        if (validation.isSuspiciousForwardJump || validation.isTimeReversed) {
            validation.message?.let { log(uid, it, "error") }
        }

        if (endTime > 0L && now < endTime) {
            val remainMin = ((endTime - now) / 60000).toInt()
            val remainSec = (((endTime - now) % 60000) / 1000).toInt()
            log(uid, "Процесс дешифрования продолжается. Осталось: ${remainMin}м ${remainSec}с.", "error")
            return null
        }

        // Deduct the cache
        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1, custom_data = null))
        } else {
            dao.deleteInventoryItem(item)
        }

        val player = dao.getPlayer(uid) ?: return null
        val bonusXp = (1000..3000).random().toLong()
        val bonusBc = (2000..5000).random().toLong()

        val tempPlayer = player.copy(
            xp = player.xp + bonusXp,
            biocoin = player.biocoin + bonusBc
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            handleLevelUpRewards(uid, player.level, updatedPlayer.level)
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
        }

        val rewards = mutableListOf<InventoryItem>()
        repeat(2) {
            val lootMeta = rollNormalLoot()
            if (lootMeta != null) {
                val lootId = lootMeta.id
                addInventory(uid, lootId, 1)
                rewards.add(InventoryItem(uid = uid, item_id = lootId, quantity = 1))
            }
        }

        log(uid, "🔓 [КЭШ ВЗЛОМАН]: Получено +${bonusXp} XP, +${bonusBc} BC и артефакты!", "loot")
        return rewards
    }

    suspend fun restoreSignal(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()
        val nextTime = player.last_signal_restore + (5 * 60 * 1000)
        if (now < nextTime) {
            val remainSeconds = ((nextTime - now) / 1000).toInt()
            log(uid, "❌ [ОТКАЗ_ДОСТУПА]: Нейро-контур в стадии регенерации. Подождите $remainSeconds сек.", "error")
            return
        }
        val activeStats = getActiveStats(uid)
        val xpReward = player.level * 25L
        val tempPlayer = player.copy(
            hp = activeStats.maxHp,
            xp = player.xp + xpReward,
            last_signal_restore = now
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            handleLevelUpRewards(uid, player.level, updatedPlayer.level)
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
        }
        log(uid, "💚 [СИГНАЛ_ВОССТАНОВЛЕН]: Целостность 100% (${activeStats.maxHp} HP). Получено +$xpReward XP за стабилизацию.", "info")
    }

    suspend fun syncProtocol(uid: Long) {
        val currentPlayer = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()
        val isAccelActive = currentPlayer.sync_accel_expiry > now
        val cooldownMs = if (isAccelActive) 15L * 60 * 1000 else 30L * 60 * 1000
        val nextTime = currentPlayer.last_sync + cooldownMs
        if (now < nextTime) {
            val remainMin = ((nextTime - now) / 60000).toInt()
            val remainSec = (((nextTime - now) % 60000) / 1000).toInt()
            log(uid, "⏳ [НЕЙРО_ПЕРЕГРУЗКА]: Цикл синхронизации недоступен. Ожидание: $remainMin мин. $remainSec сек.", "error")
            return
        }

        // Fetch protocols
        val protocols = dao.getContentByType("protocol")
        val selectedProtocolText = if (protocols.isNotEmpty()) {
            protocols.random().text
        } else {
            "🧬 🧘 ПРОТОКОЛ: ОПТИМИЗАЦИЯ ТЕЛА\nЛОГИКА: Сигнал - это просто интерфейс.\nМЕХАНИКА: Дышите ровно.\nПРОГНОЗ: Стабильность 100%."
        }

        // XP Reward logic: 120 * level * (1 + streak * 0.1)
        val baseXp = 120L * currentPlayer.level
        val streakBonus = 1.0f + (currentPlayer.streak * 0.1f)
        val totalXp = (baseXp * streakBonus).toLong()

        val tempPlayer = currentPlayer.copy(
            xp = currentPlayer.xp + totalXp,
            last_sync = now
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
        }

        log(uid, "🧬 [СИНХРОНИЗАЦИЯ_УСПЕШНА]: Получен новый протокол:\n$selectedProtocolText", "info")
        log(uid, "✨ Загружено +$totalXp XP (Бонус серии: +${(currentPlayer.streak * 10)}%).", "loot")

        // Glitch chance (7%)
        if ((0..100).random() < 7) {
            val glitchRoll = (0..2).random()
            when (glitchRoll) {
                0 -> {
                    log(uid, "⚠️ [ГЛИТЧ-ОБНАРУЖЕНИЕ]: Входящий сигнал искажен... Найден скрытый лог Архитекторов: 'Проект ЭЙДОС запущен в 2029 году. Мы искали бессмертие, а нашли бесконечную петлю.'", "error")
                }
                1 -> {
                    val rareItem = "eidos_shard"
                    val existingItem = dao.getInventoryFlow(uid).first().find { it.item_id == rareItem }
                    if (existingItem != null) {
                        dao.updateInventoryItem(existingItem.copy(quantity = existingItem.quantity + 1))
                    } else {
                        dao.insertInventoryItem(InventoryItem(uid = uid, item_id = rareItem, quantity = 1))
                    }
                    log(uid, "🎁 [ГЛИТЧ-ТАЙНИК]: Системная ошибка материализовала [Осколок Эйдоса] в вашем инвентаре!", "loot")
                }
                2 -> {
                    val p = dao.getPlayer(uid)
                    if (p != null) {
                        log(uid, "🌀 [ВСПЛЕСК_АНОМАЛИИ]: Потоки данных искривились. Энергия восстановлена на +30 ед.!", "info")
                        dao.updatePlayer(p.copy(energy = minOf(p.max_energy, p.energy + 30)))
                    }
                }
            }
        }
    }

    suspend fun claimDailyStreak(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()
        val currentStreak = player.streak
        val coinReward = 150L * currentStreak
        val shardReward = if (currentStreak % 3 == 0) (currentStreak / 3) else 0

        val updatedPlayer = player.copy(
            streak = currentStreak + 1,
            biocoin = player.biocoin + coinReward,
            last_active = now,
            hp = player.max_hp
        )
        dao.updatePlayer(updatedPlayer)

        if (shardReward > 0) {
            addInventory(uid, "eidos_shard", shardReward)
        }

        io.eidos.zerolayer.ui.utils.DailyStreakWorker.schedule(context, 24 * 3600 * 1000L)

        log(uid, "🎁 [СИНХРОНИЗАЦИЯ СЕТИ]: Серия заходов: ${currentStreak + 1} дней! Награда: +$coinReward BC, +$shardReward Осколков Эйдоса.", "loot")
    }

    suspend fun joinFaction(uid: Long, factionName: String) {
        val player = dao.getPlayer(uid) ?: return
        if (player.level < 3 && factionName == "АРХИТЕКТОРЫ") {
            log(uid, "❌ Фракция 'АРХИТЕКТОРЫ' доступна только с 3 уровня Ядра.", "error")
            return
        }
        val updatedPlayer = player.copy(faction = factionName)
        dao.updatePlayer(updatedPlayer)
        log(uid, "🧬 [ПЕРЕХОД ФРАКЦИИ]: Вы присягнули фракции $factionName!", "info")
    }

    suspend fun recycleItem(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val (bcGain, shardGain) = when (rarity) {
            "common" -> Pair(100L, 0)
            "uncommon" -> Pair(250L, 0)
            "rare" -> Pair(500L, 1)
            "epic" -> Pair(1000L, 2)
            "legendary" -> Pair(2500L, 5)
            else -> Pair(50L, 0)
        }

        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1))
        } else {
            dao.deleteInventoryItem(item)
        }

        val player = dao.getPlayer(uid) ?: return
        dao.updatePlayer(player.copy(biocoin = player.biocoin + bcGain))
        if (shardGain > 0) {
            addInventory(uid, "eidos_shard", shardGain)
        }

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "♻ [РЕЦИКЛЕР]: Предмет $itemName утилизирован! Награда: +$bcGain BC, +$shardGain Осколков.", "loot")
    }

    suspend fun simulatedPvpDuel(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        if (player.energy < 10) {
            log(uid, "❌ Недостаточно энергии для Дуэли (требуется 10 ед.).", "error")
            return
        }

        dao.updatePlayer(player.copy(energy = player.energy - 10))

        val stats = getActiveStats(uid)
        val botNames = listOf("Phantom_X", "CyberNinja_99", "Matrix_Zero", "Ghost_Operator", "DarkNet_Lord")
        val botName = botNames.random()
        val botAtk = (15 + player.level * 3) + (-5..10).random()
        val botDef = (5 + player.level * 2) + (-2..5).random()

        val playerPower = stats.attack + stats.defense + stats.luck
        val botPower = botAtk + botDef + 10

        val win = (playerPower + (0..30).random()) > (botPower + (0..30).random())

        if (win) {
            val rewardCoins = (200..450).random().toLong()
            val rewardXp = (100..250).random().toLong()
            val tempPlayer = player.copy(
                biocoin = player.biocoin + rewardCoins,
                xp = player.xp + rewardXp,
                wins_pvp = player.wins_pvp + 1
            )
            val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
            dao.updatePlayer(updatedPlayer)
            if (leveledUp) {
                log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
            }
            log(uid, "⚔ [ДУЭЛЬ ПОБЕДА]: Вы победили аватара $botName! Награда: +$rewardCoins BC, +$rewardXp XP.", "loot")
        } else {
            val lostCoins = minOf(player.biocoin, (50..120).random().toLong())
            val updatedPlayer = player.copy(
                biocoin = player.biocoin - lostCoins,
                losses_pvp = player.losses_pvp + 1,
                hp = maxOf(1, player.hp - 15)
            )
            dao.updatePlayer(updatedPlayer)
            log(uid, "☠ [ДУЭЛЬ ПОРЕДЖЕНИЕ]: Оператор $botName перехватил инициативу! Потеряно -$lostCoins BC, -15 HP.", "error")
        }
    }

    suspend fun pvpDuelAgainstOpponent(uid: Long, opponentName: String, opponentLevel: Int, opponentAtk: Int, opponentDef: Int) {
        val player = dao.getPlayer(uid) ?: return
        if (player.energy < 10) {
            log(uid, "❌ Недостаточно энергии для Дуэли (требуется 10 ед.).", "error")
            return
        }

        dao.updatePlayer(player.copy(energy = player.energy - 10))

        val stats = getActiveStats(uid)
        val playerPower = stats.attack + stats.defense + stats.luck
        val botPower = opponentAtk + opponentDef + 10

        val win = (playerPower + (0..30).random()) > (botPower + (0..30).random())

        if (win) {
            val rewardCoins = (200..450).random().toLong()
            val rewardXp = (100..250).random().toLong()
            val tempPlayer = player.copy(
                biocoin = player.biocoin + rewardCoins,
                xp = player.xp + rewardXp,
                wins_pvp = player.wins_pvp + 1
            )
            val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
            dao.updatePlayer(updatedPlayer)
            if (leveledUp) {
                log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Ваш уровень Ядра вырос до Level ${updatedPlayer.level}!", "info")
            }
            log(uid, "⚔ [PVP ПОБЕДА]: Вы победили оператора $opponentName! Награда: +$rewardCoins BC, +$rewardXp XP.", "loot")
        } else {
            val lostCoins = minOf(player.biocoin, (50..120).random().toLong())
            val updatedPlayer = player.copy(
                biocoin = player.biocoin - lostCoins,
                losses_pvp = player.losses_pvp + 1,
                hp = maxOf(1, player.hp - 15)
            )
            dao.updatePlayer(updatedPlayer)
            log(uid, "☠ [PVP ПОРАЖЕНИЕ]: Оператор $opponentName перехватил инициативу! Потеряно -$lostCoins BC, -15 HP.", "error")
        }
    }

    // --- ZERO LAYER ECONOMY & CURRENCY SINKS ---
    fun calculateItemRepairFee(item: InventoryItem): Long {
        val meta = getItemMetadata(item.item_id)
        val missingDurability = (100f - item.durability).coerceAtLeast(0f)
        return ZeroLayerEconomy.calculateRepairFee(missingDurability, meta?.rarity ?: "common")
    }

    suspend fun repairEquipmentWithFee(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(item.item_id) ?: return
        if (item.durability >= 100f) {
            log(uid, "Предмет ${meta.name} имеет 100% прочность.", "error")
            return
        }

        val repairFee = calculateItemRepairFee(item)
        if (player.biocoin < repairFee) {
            log(uid, "❌ [ОШИБКА РЕМОНТА]: Недостаточно средств. Требуется: $repairFee BC.", "error")
            return
        }

        dao.updatePlayer(player.copy(biocoin = player.biocoin - repairFee))
        dao.updateInventoryItem(item.copy(durability = 100f))
        log(uid, "🔧 [МАСТЕРСКАЯ СТОКОВ]: Отремонтирован ${meta.name}! Списано плату за ремонт: $repairFee BC.", "info")
    }

    suspend fun endRaidWithSafeExtraction(uid: Long): Triple<List<InventoryItem>, Long, Boolean>? {
        val session = dao.getRaidSession(uid) ?: return null
        val player = dao.getPlayer(uid) ?: return null

        val rawCoins = session.buffer_coins
        val extractionTax = ZeroLayerEconomy.calculateExtractionTax(rawCoins)
        val finalCoins = maxOf(0L, rawCoins - extractionTax)

        val bonusXpMult = if (player.is_premium) 1.5f else 1.0f
        val calculatedXp = (session.buffer_xp * bonusXpMult).toLong()

        val sessionToken = authStore.getSession().accessToken
        if (!sessionToken.isNullOrBlank() && SupabaseClientManager.isConfigured()) {
            val rpcResp = SupabaseClientManager.processRaidRewardRpc(
                accessToken = sessionToken,
                exp = calculatedXp,
                biocoins = finalCoins,
                depth = session.depth
            )
            if (rpcResp != null && rpcResp.success) {
                log(uid, "🌐 [SUPABASE RPC]: Награда за рейд зачислена сервером!", "info")
            }
        }

        val tempPlayer = player.copy(
            xp = player.xp + calculatedXp,
            biocoin = player.biocoin + finalCoins,
            max_depth = maxOf(player.max_depth, session.depth),
            raids_done = player.raids_done + 1
        )
        val (updatedPlayer, leveledUp) = tempPlayer.checkAndApplyLevelUp()
        dao.updatePlayer(updatedPlayer)
        if (leveledUp) {
            handleLevelUpRewards(uid, player.level, updatedPlayer.level)
            log(uid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedPlayer.level}! Повышены HP (+20), Атака (+3) и Защита (+2).", "info")
        }

        val extractedItems = mutableListOf<InventoryItem>()
        // Transfer buffer items to inventory
        if (session.buffer_items.isNotEmpty()) {
            val items = session.buffer_items.split(",").map { it.trim() }.filter { it.isNotBlank() }
            items.forEach { itemId ->
                extractedItems.add(InventoryItem(uid = uid, item_id = itemId, quantity = 1))
                addInventory(uid, itemId, 1)
            }
        }

        dao.deleteRaidSession(uid)
        log(uid, "📡 [БЕЗОПАСНАЯ ЭВАКУАЦИЯ]: Комиссия шлюза (12%): -$extractionTax BC. Зачислено чистой выручки: +$finalCoins BC, +$calculatedXp XP.", "info")
        
        return Triple(extractedItems, finalCoins, leveledUp)
    }

    suspend fun rerollChipModifiers(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"

        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)
        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит калибровке!", "error")
            return
        }

        val (bcCost, shardCost) = ZeroLayerEconomy.calculateRerollCost(rarity)

        if (player.biocoin < bcCost) {
            log(uid, "❌ [РЕРОЛЛ ЧИПА]: Недостаточно BioCoins. Требуется: $bcCost BC.", "error")
            return
        }

        if (shardCost > 0) {
            val hasEnough = deductShards(uid, shardCost)
            if (!hasEnough) {
                log(uid, "❌ [РЕРОЛЛ ЧИПА]: Недостаточно Осколков Эйдоса. Требуется: $shardCost шт.", "error")
                return
            }
        }

        // Deduct biocoin fees
        dao.updatePlayer(player.copy(biocoin = player.biocoin - bcCost))

        // Update equipment stat affix while preserving all sockets and chips
        val newAtkBonus = (5..30).random()
        val existingAtkIndex = currentEq.affixes.indexOfFirst { it.statType == "ATK" }
        val updatedAffixes = currentEq.affixes.toMutableList()
        if (existingAtkIndex >= 0) {
            val existing = updatedAffixes[existingAtkIndex]
            updatedAffixes[existingAtkIndex] = existing.copy(
                minValue = minOf(existing.minValue, 5),
                maxValue = maxOf(existing.maxValue, 30),
                currentValue = maxOf(existing.currentValue, newAtkBonus)
            )
        } else {
            updatedAffixes.add(ItemAffix(statType = "ATK", minValue = 5, maxValue = 30, currentValue = newAtkBonus))
        }
        val updatedEq = currentEq.copy(affixes = updatedAffixes)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)
        dao.updateInventoryItem(item.copy(custom_data = serialized, durability = 100f))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "⚙ [КАЛИБРАТОР ЧИПОВ]: Переконфигурирован $itemName! Новый кастомный бонус: +$newAtkBonus ATK (-$bcCost BC, -$shardCost Осколков).", "loot")
    }

    // --- EIDOS CRAFTING BENCH MECHANICS ---
    suspend fun applyDataSlicer(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 250L
        if (player.biocoin < costBc) {
            log(uid, "❌ [СЛАЙСЕР ДАННЫХ]: Недостаточно BioCoins ($costBc BC).", "error")
            return
        }

        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит модификации!", "error")
            return
        }

        val updatedEq = PoECraftEngine.applyDataSlicer(currentEq, rarity)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updatePlayer(player.copy(biocoin = player.biocoin - costBc))
        dao.updateInventoryItem(item.copy(custom_data = serialized))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "🎲 [СЛАЙСЕР ДАННЫХ]: Предмет $itemName пересоздан с новыми аффиксами! (-$costBc BC)", "loot")
    }

    suspend fun applyQuantumTuner(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 500L
        val costShards = 1

        if (player.biocoin < costBc) {
            log(uid, "❌ [КВАНТОВЫЙ КАЛИБРАТОР]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = deductShards(uid, costShards)
        if (!hasShards) {
            log(uid, "❌ [КВАНТОВЫЙ КАЛИБРАТОР]: Требуется $costShards 💎 Осколок.", "error")
            return
        }

        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит модификации!", "error")
            return
        }

        val updatedEq = PoECraftEngine.applyQuantumTuner(currentEq)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updatePlayer(player.copy(biocoin = player.biocoin - costBc))
        dao.updateInventoryItem(item.copy(custom_data = serialized))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "⚖️ [КВАНТОВЫЙ КАЛИБРАТОР]: Аффиксы $itemName калиброваны к новым роллам! (-$costBc BC, -$costShards 💎)", "loot")
    }

    suspend fun applySocketPuncher(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 300L
        val costShards = 1

        if (player.biocoin < costBc) {
            log(uid, "❌ [ПРОБОЙНИК ГНЕЗД]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = deductShards(uid, costShards)
        if (!hasShards) {
            log(uid, "❌ [ПРОБОЙНИК ГНЕЗД]: Требуется $costShards 💎 Осколок.", "error")
            return
        }

        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит модификации!", "error")
            return
        }

        val updatedEq = PoECraftEngine.applySocketPuncher(currentEq, rarity)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updatePlayer(player.copy(biocoin = player.biocoin - costBc))
        dao.updateInventoryItem(item.copy(custom_data = serialized))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "🔌 [ПРОБОЙНИК ГНЕЗД]: В $itemName пробито ${updatedEq.maxSockets} сокетов! (-$costBc BC, -$costShards 💎)", "loot")
    }

    suspend fun applyChromaticInjector(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 150L

        if (player.biocoin < costBc) {
            log(uid, "❌ [СПЕКТРАЛЬНЫЙ ИНЖЕКТОР]: Требуется $costBc BC.", "error")
            return
        }

        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит модификации!", "error")
            return
        }

        val updatedEq = PoECraftEngine.applyChromaticInjector(currentEq)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updatePlayer(player.copy(biocoin = player.biocoin - costBc))
        dao.updateInventoryItem(item.copy(custom_data = serialized))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "🌈 [СПЕКТРАЛЬНЫЙ ИНЖЕКТОР]: Переконфигурированы цвета сокетов в $itemName! (-$costBc BC)", "info")
    }

    suspend fun applyVaalCorruption(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 1000L
        val costShards = 2

        if (player.biocoin < costBc) {
            log(uid, "❌ [СКВЕРНА НЕЙРОСЕТИ]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = deductShards(uid, costShards)
        if (!hasShards) {
            log(uid, "❌ [СКВЕРНА НЕЙРОСЕТИ]: Требуется $costShards 💎 Осколков Эйдоса.", "error")
            return
        }

        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет уже ЗАПЕЧАТАН (СКВЕРНА)!", "error")
            return
        }

        val updatedEq = PoECraftEngine.applyVaalCorruption(currentEq)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updatePlayer(player.copy(biocoin = player.biocoin - costBc))
        dao.updateInventoryItem(item.copy(custom_data = serialized))

        val itemName = meta?.name ?: item.item_id.uppercase()
        log(uid, "☣️ [СКВЕРНА НЕЙРОСЕТИ]: Предмет $itemName поражен Скверной Бездны! Наложен бонус '${updatedEq.implicitAffix}'. Запечатано навечно!", "loot")
    }

    suspend fun insertChipToEquipment(uid: Long, item: InventoryItem, socketIndex: Int, chip: DataChip) {
        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит калибровке сокетов!", "error")
            return
        }

        if (socketIndex !in 0 until currentEq.maxSockets) return

        val newInserted = currentEq.insertedChips.toMutableList()
        while (newInserted.size < currentEq.maxSockets) newInserted.add(null)
        val oldChip = newInserted[socketIndex]
        if (oldChip != null) {
            addInventory(uid, oldChip.id, 1)
        }
        removeInventory(uid, chip.id, 1)
        newInserted[socketIndex] = chip

        val updatedEq = currentEq.copy(insertedChips = newInserted)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updateInventoryItem(item.copy(custom_data = serialized))
        log(uid, "🧩 [ВСТАВКА ЧИПА]: В сокет #${socketIndex + 1} установлен чип '${chip.name}'!", "info")
    }

    suspend fun removeChipFromEquipment(uid: Long, item: InventoryItem, socketIndex: Int) {
        val meta = getItemMetadata(item.item_id)
        val rarity = meta?.rarity ?: "common"
        val currentEq = PoECraftEngine.getOrGenerateEquipment(item, rarity)

        if (currentEq.isCorrupted) {
            log(uid, "❌ [ОШИБКА]: Предмет ЗАПЕЧАТАН (СКВЕРНА) и не подлежит калибровке сокетов!", "error")
            return
        }

        if (socketIndex !in currentEq.insertedChips.indices) return

        val chipToRemove = currentEq.insertedChips.getOrNull(socketIndex) ?: return
        val newInserted = currentEq.insertedChips.toMutableList()
        newInserted[socketIndex] = null

        val updatedEq = currentEq.copy(insertedChips = newInserted)
        val serialized = PoECraftEngine.serializeEquipment(updatedEq)

        dao.updateInventoryItem(item.copy(custom_data = serialized))
        addInventory(uid, chipToRemove.id, 1)
        log(uid, "🧩 [ИЗВЛЕЧЕНИЕ ЧИПА]: Чип '${chipToRemove.name}' возвращен в инвентарь.", "info")
    }

    fun getBestiaryFlow(): Flow<List<BestiaryEntry>> = dao.getBestiaryFlow()

    suspend fun recordEnemyEncounter(enemyId: String) {
        if (enemyId.isBlank()) return
        val existing = dao.getBestiaryEntry(enemyId)
        if (existing == null) {
            dao.insertBestiaryEntry(BestiaryEntry(enemy_id = enemyId, encountered = true, killed_count = 0))
        }
    }

    suspend fun recordEnemyKill(enemyId: String) {
        if (enemyId.isBlank()) return
        val existing = dao.getBestiaryEntry(enemyId)
        val kills = (existing?.killed_count ?: 0) + 1
        dao.insertBestiaryEntry(BestiaryEntry(enemy_id = enemyId, encountered = true, killed_count = kills))
    }

    // --- GACHA & LOOTBOX SYSTEM ---
    suspend fun buyGachaRoll(uid: Long): GachaRollResult? {
        val player = dao.getPlayer(uid) ?: return null
        val cost = GachaSystem.GACHA_PRICE_BC
        if (player.biocoin < cost) {
            log(uid, "❌ [ОШИБКА]: Недостаточно BioCoin. Стоимость лутбокса: $cost BC.", "error")
            return null
        }
        dao.updatePlayer(player.copy(biocoin = player.biocoin - cost))
        val result = GachaSystem.rollGacha()
        
        val invItem = InventoryItem(
            uid = uid,
            item_id = result.item.id,
            quantity = 1,
            durability = 100f
        )
        dao.insertInventoryItem(invItem)
        log(uid, "🎁 [КОНТЕЙНЕР БЕЗДНЫ]: Открыт лутбокс! Получен [${result.item.name}] (${result.rarity.name})!", "loot")
        return result
    }

    suspend fun synthesizeFragments(uid: Long): ItemMetadata? {
        val inventory = dao.getInventoryFlow(uid).first()
        val fragments = inventory.find { it.item_id == "data_fragment" }
        if (fragments == null || fragments.quantity < 5) {
            log(uid, "❌ [СИНТЕЗАТОР]: Требуется 5 Фрагментов Данных для синтеза.", "error")
            return null
        }
        if (fragments.quantity == 5) {
            dao.deleteInventoryItem(fragments)
        } else {
            dao.updateInventoryItem(fragments.copy(quantity = fragments.quantity - 5))
        }
        val legendaries = GachaSystem.LEGENDARY_POOL
        val won = legendaries.random()
        val invItem = InventoryItem(
            uid = uid,
            item_id = won.id,
            quantity = 1,
            durability = 100f
        )
        dao.insertInventoryItem(invItem)
        log(uid, "⚡ [СИНТЕЗ ФРАГМЕНТОВ]: 5 Фрагментов объединены в ЛЕГЕНДАРНЫЙ предмет [${won.name}]!", "loot")
        return won
    }

    // --- PVP 2.0 ACTIONS ---
    suspend fun setupPvpDefense(uid: Long, p1: PvpProgram, p2: PvpProgram, p3: PvpProgram) {
        val player = dao.getPlayer(uid) ?: return
        dao.updatePlayer(player.copy(
            defense_program_1 = p1.name,
            defense_program_2 = p2.name,
            defense_program_3 = p3.name
        ))
        log(uid, "🛡 [ПРОТОКОЛЫ ЗАЩИТЫ]: Защитная матрица обновлена: [${p1.label}, ${p2.label}, ${p3.label}].", "info")
    }

    suspend fun buyPvpHardware(uid: Long, hardware: HardwareType): Boolean {
        val player = dao.getPlayer(uid) ?: return false
        if (player.biocoin < hardware.priceBc) {
            log(uid, "❌ [КИБЕР-ДЕКА]: Недостаточно BioCoin для покупки ${hardware.label}.", "error")
            return false
        }
        val currentHw = player.installed_hardware.split(",").filter { it.isNotBlank() }.toMutableSet()
        if (currentHw.contains(hardware.name)) {
            log(uid, "❌ [КИБЕР-ДЕКА]: Модуль ${hardware.label} уже установлен!", "error")
            return false
        }
        currentHw.add(hardware.name)
        dao.updatePlayer(player.copy(
            biocoin = player.biocoin - hardware.priceBc,
            installed_hardware = currentHw.joinToString(",")
        ))
        log(uid, "💾 [КИБЕР-ДЕКА]: Установлен модуль [${hardware.label}]! (-${hardware.priceBc} BC)", "info")
        return true
    }

    suspend fun activatePvpShield(uid: Long, hours: Int = 12, costBc: Long = 300L): Boolean {
        val player = dao.getPlayer(uid) ?: return false
        if (player.biocoin < costBc) {
            log(uid, "❌ [КИБЕР-ЩИТ]: Недостаточно BioCoin ($costBc BC).", "error")
            return false
        }
        val now = System.currentTimeMillis()
        val base = if (player.pvp_shield_until > now) player.pvp_shield_until else now
        val newShield = base + (hours * 3600 * 1000L)
        dao.updatePlayer(player.copy(
            biocoin = player.biocoin - costBc,
            pvp_shield_until = newShield
        ))
        log(uid, "🛡 [КИБЕР-ЩИТ АКТИВИРОВАН]: Защита от нападений на $hours часов!", "info")
        return true
    }

    suspend fun activatePvpProxy(uid: Long, hours: Int = 24, costBc: Long = 500L): Boolean {
        val player = dao.getPlayer(uid) ?: return false
        if (player.biocoin < costBc) {
            log(uid, "❌ [ПРОКСИ-ЦЕПЬ]: Недостаточно BioCoin ($costBc BC).", "error")
            return false
        }
        val now = System.currentTimeMillis()
        val base = if (player.pvp_proxy_until > now) player.pvp_proxy_until else now
        val newProxy = base + (hours * 3600 * 1000L)
        dao.updatePlayer(player.copy(
            biocoin = player.biocoin - costBc,
            pvp_proxy_until = newProxy
        ))
        log(uid, "🕶 [ПРОКСИ-НОДА]: Маскировка сетевого адреса включена на $hours часов!", "info")
        return true
    }

    suspend fun executePvpRaid(
        attackerUid: Long,
        targetPlayer: SupabasePlayer,
        attackerPrograms: List<PvpProgram>,
        isRevenge: Boolean = false
    ): PvpMatchResult {
        val attacker = dao.getPlayer(attackerUid) ?: throw IllegalStateException("Player not found")
        
        if (targetPlayer.pvp_proxy_until > System.currentTimeMillis()) {
            log(attackerUid, "🌐 [ПРОКСИ-СЕРВЕР]: Узел цели '${targetPlayer.username ?: "Аноним"}' защищен активным Прокси-Сервером!", "error")
            throw IllegalStateException("Узел цели защищен Прокси-Сервером (анонимность 24ч)!")
        }

        val targetP1 = PvpProgram.fromString(targetPlayer.defense_program_1)
        val targetP2 = PvpProgram.fromString(targetPlayer.defense_program_2)
        val targetP3 = PvpProgram.fromString(targetPlayer.defense_program_3)
        val defenderPrograms = listOf(targetP1, targetP2, targetP3)
        
        val attackerHardware = attacker.installed_hardware.split(",").filter { it.isNotBlank() }
            .mapNotNull { HardwareType.fromString(it) }

        val matchResult = PvpEngine.resolveMatch(
            attacker = attacker,
            defender = targetPlayer,
            attackerPrograms = attackerPrograms,
            defenderPrograms = defenderPrograms,
            attackerHardware = attackerHardware,
            isRevenge = isRevenge
        )

        var updatedHw = attacker.installed_hardware
        if (matchResult.firewallTriggered) {
            updatedHw = updatedHw.split(",")
                .filter { it.isNotBlank() && !it.equals("firewall", ignoreCase = true) }
                .joinToString(",")
            log(attackerUid, "🛡️ [ФАЙРВОЛ]: Военный файрвол заблокировал атаку и сгорел в ходе боя.", "info")
        }

        if (matchResult.isWin) {
            val tempAttacker = attacker.copy(
                biocoin = attacker.biocoin + matchResult.stolenCoins,
                xp = attacker.xp + matchResult.attackerXpGained,
                wins_pvp = attacker.wins_pvp + 1,
                installed_hardware = updatedHw
            )
            val (updatedAttacker, leveledUp) = tempAttacker.checkAndApplyLevelUp()
            dao.updatePlayer(updatedAttacker)
            if (leveledUp) {
                handleLevelUpRewards(attackerUid, attacker.level, updatedAttacker.level)
                log(attackerUid, "🎉 [УРОВЕНЬ ПОВЫШЕН!]: Поздравляем! Ваш уровень Ядра вырос до Level ${updatedAttacker.level}!", "info")
            }
            log(attackerUid, "🏆 [СЕТЕВОЙ ВЗЛОМ: ПОБЕДА]: Сервер ${targetPlayer.username ?: "Анонима"} взломан! Похищено: +${matchResult.stolenCoins} BC, +${matchResult.attackerXpGained} XP!", "combat")
        } else {
            val finalXp = maxOf(0L, attacker.xp - matchResult.xpBurnedByIceTrap)
            val updatedAttacker = attacker.copy(
                biocoin = maxOf(0, attacker.biocoin - matchResult.coinsLost),
                xp = finalXp,
                losses_pvp = attacker.losses_pvp + 1,
                installed_hardware = updatedHw
            )
            dao.updatePlayer(updatedAttacker)
            if (matchResult.iceTrapTriggered) {
                log(attackerUid, "❄️ [ICE-ЛОВУШКА]: Защитный лед узла выжег -${matchResult.xpBurnedByIceTrap} XP из вашей системы!", "error")
            }
            log(attackerUid, "☠️ [СЕТЕВОЙ ВЗЛОМ: ПРОВАЛ]: Защитный лед цели отразил атаку! Контрудар: -${matchResult.coinsLost} BC.", "error")
        }
        
        return matchResult
    }

    // --- SYNDICATE & REFERRALS ---
    suspend fun redeemReferralCode(uid: Long, code: String): Boolean {
        val player = dao.getPlayer(uid) ?: return false
        if (player.referred_by != null) {
            log(uid, "❌ [РЕФЕРАЛ]: Вы уже активировали реферальный код ранее!", "error")
            return false
        }
        if (code.trim().equals(player.uid.toString(), ignoreCase = true) || code.trim().equals(player.referral_code, ignoreCase = true)) {
            log(uid, "❌ [РЕФЕРАЛ]: Нельзя вводить собственный реферальный код!", "error")
            return false
        }
        
        val updated = player.copy(
            referred_by = code.trim(),
            xp = player.xp + 300L,
            biocoin = player.biocoin + 200L
        )
        dao.updatePlayer(updated)
        log(uid, "🤝 [РЕФЕРАЛЬНАЯ ПРОГРАММА]: Код [$code] успешно применен! Получено +300 XP и +200 BC!", "loot")
        return true
    }

    suspend fun sendSignalToOperator(senderUid: Long, targetUid: Long, targetName: String): Boolean {
        val sender = dao.getPlayer(senderUid) ?: return false
        val updatedSender = sender.copy(xp = sender.xp + 10)
        dao.updatePlayer(updatedSender)
        log(senderUid, "📡 [НЕЙРО-СИГНАЛ]: Вы отправили сигнал оператору $targetName! Получено +10 XP.", "info")
        return true
    }

    suspend fun sendSignalToOperator(senderUid: Long, target: String, message: String): Boolean {
        val sender = dao.getPlayer(senderUid) ?: return false
        val updatedSender = sender.copy(xp = sender.xp + 10)
        dao.updatePlayer(updatedSender)
        log(senderUid, "📡 [НЕЙРО-СИГНАЛ]: Отправлено сообщение для $target: \"$message\" (+10 XP)", "info")
        return true
    }

    val authStore: EidosAuthStore = EidosAuthStore.getInstance(context)

    fun getAuthSession(): AuthSession = authStore.getSession()

    suspend fun registerOperator(username: String, password: String, targetUid: Long = 0L): AuthResult {
        val clean = username.trim()
        if (clean.length < 3) return AuthResult.Error("Позывной должен содержать не менее 3 символов.")
        if (password.length < 4) return AuthResult.Error("Пароль должен содержать минимум 4 символов.")

        var res = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.signUpWithCredentials(clean, password)
        } else {
            AuthResult.Error("Offline")
        }

        if (res !is AuthResult.Success) {
            // Smooth offline registration fallback
            val offlineUserId = "local_${System.currentTimeMillis()}"
            res = AuthResult.Success(
                user = AuthUser(id = offlineUserId),
                accessToken = "local_token_$offlineUserId",
                refreshToken = null,
                username = clean,
                isNewAccount = true
            )
        }

        authStore.saveSession(res.username, res.user.id, res.accessToken, res.refreshToken)
        val target = if (targetUid > 0L) targetUid else getActiveUid()
        val p = dao.getPlayer(target)
        if (p != null) {
            val updated = p.copy(username = res.username, first_name = res.username)
            dao.updatePlayer(updated)
            if (SupabaseClientManager.isConfigured()) {
                pushPlayerToSupabase(p.uid, res.user.id, res.username)
            }
        }
        log(target, "🛡 [НЕЙРО-ПРОФИЛЬ]: Оператор ${res.username} успешно зарегистрирован в Сети Эйдос!", "info")
        return res
    }

    suspend fun loginOperator(username: String, password: String, targetUid: Long = 0L): AuthResult {
        val clean = username.trim()
        if (clean.isBlank()) return AuthResult.Error("Введите позывной оператора.")
        if (password.isBlank()) return AuthResult.Error("Введите пароль.")

        var res = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.signInWithCredentials(clean, password)
        } else {
            AuthResult.Error("Offline")
        }

        if (res !is AuthResult.Success) {
            // Smooth offline login fallback
            val offlineUserId = "local_${clean.hashCode()}"
            res = AuthResult.Success(
                user = AuthUser(id = offlineUserId),
                accessToken = "local_token_$offlineUserId",
                refreshToken = null,
                username = clean,
                isNewAccount = false
            )
        }

        authStore.saveSession(res.username, res.user.id, res.accessToken, res.refreshToken)

        // Try to restore or sync cloud player profile
        val cloudPlayer = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.fetchPlayerByDeviceId(res.user.id)
                ?: SupabaseClientManager.fetchPlayerByDeviceId(res.username)
        } else null

        val target = if (targetUid > 0L) targetUid else getActiveUid()
        val localPlayer = dao.getPlayer(target)
        if (cloudPlayer != null) {
            val restored = (localPlayer ?: Player(uid = target, username = res.username, first_name = res.username)).copy(
                username = cloudPlayer.username,
                first_name = cloudPlayer.username,
                level = cloudPlayer.level,
                xp = cloudPlayer.exp,
                biocoin = cloudPlayer.biocoins,
                hp = cloudPlayer.hp,
                energy = cloudPlayer.energy,
                max_depth = cloudPlayer.maxDepth,
                defense_program_1 = cloudPlayer.defense_program_1,
                defense_program_2 = cloudPlayer.defense_program_2,
                defense_program_3 = cloudPlayer.defense_program_3,
                updated_at = System.currentTimeMillis()
            )
            dao.insertPlayer(restored)
            log(target, "☁️ [НЕЙРО-СИНХРОНИЗАЦИЯ]: Профиль оператора ${cloudPlayer.username} (Уровень ${cloudPlayer.level}) загружен из облака!", "loot")
        } else if (localPlayer != null) {
            val updated = localPlayer.copy(username = res.username, first_name = res.username)
            dao.updatePlayer(updated)
            if (SupabaseClientManager.isConfigured()) {
                pushPlayerToSupabase(localPlayer.uid, res.user.id, res.username)
            }
            log(target, "🔓 [СЕТЕВОЙ ВХОД]: Нейро-сессия активирована. Профиль «${res.username}» готов к вылазкам.", "info")
        }
        return res
    }

    suspend fun logoutOperator(): Boolean {
        val session = authStore.getSession()
        if (!session.accessToken.isNullOrBlank()) {
            SupabaseClientManager.logoutSession(session.accessToken)
        }
        authStore.clearSession()
        log(getActiveUid(), "🔌 [ОТКЛЮЧЕНИЕ]: Выход из нейро-профиля выполнен. Переход в автономный режим.", "info")
        return true
    }

    suspend fun pushPlayerToSupabase(uid: Long, customDeviceId: String? = null, customUsername: String? = null): Boolean {
        val p = dao.getPlayer(uid) ?: return false
        val session = authStore.getSession()
        val deviceId = customDeviceId ?: session.userId ?: "device_$uid"
        val username = customUsername ?: session.username ?: p.username ?: "Operator_$uid"

        val sp = SupabasePlayer(
            deviceId = deviceId,
            username = username,
            level = p.level,
            exp = p.xp,
            biocoins = p.biocoin,
            hp = p.hp,
            energy = p.energy,
            rank = if (p.level > 10) "Элита" else "Оператор",
            maxDepth = p.max_depth,
            defense_program_1 = p.defense_program_1,
            defense_program_2 = p.defense_program_2,
            defense_program_3 = p.defense_program_3,
            stateVersion = p.state_version,
            updatedAt = System.currentTimeMillis()
        )
        val res = SupabaseClientManager.syncPlayer(sp)
        if (res != null) {
            authStore.updateLastSync()
            return true
        }
        return false
    }
}

// --- STRUCTURE FOR ZERO LAYER ECONOMY ---
object ZeroLayerEconomy {
    const val SAFE_EXTRACTION_TAX_PERCENT = 8 // 8% Extraction tax rate
    const val REPAIR_BASE_PER_DURABILITY = 2L  // 2 BC per 1% lost durability

    fun calculateRepairFee(missingDurability: Float, rarity: String): Long {
        if (missingDurability <= 0.05f) return 0L
        val rarityMultiplier = when (rarity.lowercase()) {
            "uncommon" -> 1.3f
            "rare" -> 1.8f
            "epic" -> 2.5f
            "legendary" -> 4.0f
            "cursed" -> 6.0f
            else -> 1.0f
        }
        return (missingDurability * REPAIR_BASE_PER_DURABILITY * rarityMultiplier).toLong().coerceAtLeast(1L)
    }

    fun calculateExtractionTax(bufferCoins: Long): Long {
        return (bufferCoins * (SAFE_EXTRACTION_TAX_PERCENT / 100.0)).toLong()
    }

    fun calculateRerollCost(rarity: String): Pair<Long, Int> {
        val bcCost = when (rarity.lowercase()) {
            "rare" -> 250L
            "epic" -> 500L
            "legendary" -> 1000L
            "cursed" -> 2000L
            else -> 100L
        }
        val shardCost = if (rarity.lowercase() in listOf("legendary", "cursed")) 2 else 1
        return Pair(bcCost, shardCost)
    }
}

