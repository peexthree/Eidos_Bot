package io.eidos.zerolayer.data

import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
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
import io.eidos.zerolayer.domain.raid.SectorMutator


@OptIn(kotlinx.serialization.ExperimentalSerializationApi::class)
class GameRepository(private val context: Context, private val originalDao: EidosDao) {

    private val dao = object : EidosDao by originalDao {
        override suspend fun insertPlayer(player: Player): Long {
            val updated = player.copy(
                state_version = player.state_version + 1,
                updated_at = System.currentTimeMillis()
            )
            return originalDao.insertPlayer(updated)
        }

        override suspend fun updatePlayer(player: Player) {
            val updated = player.copy(
                state_version = player.state_version + 1,
                updated_at = System.currentTimeMillis()
            )
            originalDao.updatePlayer(updated)
        }

        override suspend fun upsertPlayer(player: Player) {
            val updated = player.copy(
                state_version = player.state_version + 1,
                updated_at = System.currentTimeMillis()
            )
            originalDao.upsertPlayer(updated)
        }
    }

    private val dbMutex = Mutex()

    // Fire-and-forget scope for background work that must never extend a dbMutex
    // critical section (e.g. cloud log sync). SupervisorJob: one failure
    // doesn't cancel pending children.
    private val backgroundScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    // ⚡ IN-MEMORY OVERDRIVE & OVERCHARGE STATE (ZERO ROOM MIGRATION)
    private val overdriveChargeMap = ConcurrentHashMap<Long, Int>()
    private val overchargeTierMap = ConcurrentHashMap<Long, Int>()
    private val empUsedInCombat = ConcurrentHashMap<Long, Boolean>()
    private val matterStealUsedInCombat = ConcurrentHashMap<Long, Boolean>()
    private val stunnedEnemies = ConcurrentHashMap<Long, Boolean>()
    private val batteryOverclockTurns = ConcurrentHashMap<Long, Int>()
    private val shadowDanceGuaranteedCrit = ConcurrentHashMap<Long, Boolean>()
    private val pactResurrectionsUsed = ConcurrentHashMap<Long, Boolean>()

    fun isEnemyStunned(uid: Long): Boolean = stunnedEnemies[uid] == true
    fun setEnemyStunned(uid: Long, stunned: Boolean) { stunnedEnemies[uid] = stunned }

    suspend fun getEquippedChips(uid: Long): List<InventoryItem> {
        val inventory = dao.getInventoryFlow(uid).first()
        return inventory.filter { invItem ->
            invItem.is_equipped && (invItem.slot == "chip" || ItemSlotUtils.getSlotForItem(invItem.item_id, getItemMetadata(invItem.item_id)) == "chip")
        }
    }

    suspend fun getActiveChipSynergies(uid: Long): List<io.eidos.zerolayer.domain.combat.ActiveSynergy> {
        val inventory = dao.getInventoryFlow(uid).first()
        val equippedChips = inventory.filter { invItem ->
            invItem.is_equipped && (invItem.slot == "chip" || ItemSlotUtils.getSlotForItem(invItem.item_id, getItemMetadata(invItem.item_id)) == "chip")
        }
        val allEquipped = inventory.filter { it.is_equipped }
        return io.eidos.zerolayer.domain.combat.ChipMatrixSynergyEngine.evaluateSynergies(equippedChips, allEquipped)
    }

    data class DeathReport(
        val depth: Int,
        val lostCoins: Long,
        val lostXp: Long = 0L,
        val lostItems: String = "",
        val graveCreated: Boolean = false,
        val brokenItems: List<String> = emptyList(),
        val durabilityPenaltyPercent: Int = 10,
        val kills: Int = 0,
        val riddlesSolved: Int = 0,
        val durationSeconds: Long = 0L,
        val activeMutator: String? = null
    )
    val deathReportFlow = MutableStateFlow<DeathReport?>(null)
    fun clearDeathReport() { deathReportFlow.value = null }

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
        internalUnsafeDeductShards(uid, cost)
    }

    private suspend fun internalUnsafeDeductShards(uid: Long, cost: Int): Boolean {
        val items = dao.getInventoryFlow(uid).first().filter { it.item_id == "eidos_shard" }
        val total = items.sumOf { it.quantity }
        if (total < cost) return false
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
        return true
    }

    private suspend fun internalUnsafeAddInventory(uid: Long, itemId: String, amount: Int) {
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

    private suspend fun addInventory(uid: Long, itemId: String, amount: Int) {
        internalUnsafeAddInventory(uid, itemId, amount)
    }

    private suspend fun internalUnsafeRemoveInventory(uid: Long, itemId: String, amount: Int) {
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

    private suspend fun removeInventory(uid: Long, itemId: String, amount: Int) {
        internalUnsafeRemoveInventory(uid, itemId, amount)
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
                val calculatedReqLevel = when (rarity) {
                    "common" -> 1
                    "uncommon" -> 2
                    "rare" -> 4
                    "epic" -> 8
                    "legendary" -> 15
                    "relic" -> 20
                    "cursed" -> 25
                    else -> 1
                }
                val finalPrice = if (jsonItem.price > 0) jsonItem.price else when (rarity) {
                    "common" -> 100
                    "uncommon" -> 350
                    "rare" -> 1200
                    "epic" -> 3500
                    "legendary" -> 10000
                    "relic" -> 25000
                    "cursed" -> 50000
                    else -> 150
                }

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
                    price = finalPrice,
                    description = jsonItem.desc
                        .replace(Regex("\\[(МЕХАНИКА|ЛОР|механика|лор)\\]:?\\s*", RegexOption.IGNORE_CASE), "")
                        .trim(),
                    reqLevel = calculatedReqLevel
                )
            }
        } catch (e: Exception) {
            android.util.Log.e("GameRepository", "loadItemsMetadata failed, shop/inventory metadata is empty: ${e.message}")
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

    fun rollNormalLoot(legendaryBoost: Boolean = false): ItemMetadata? {
        val normalList = getAllItemsMetadata().filter { it.id != "biocoin" && !isRedLoot(it) }
        // GLITCH_STORM mutator: +40% chance to force a legendary drop
        if (legendaryBoost && (0..100).random() < 40) {
            normalList.filter { it.rarity == "legendary" }.randomOrNull()?.let { return it }
        }
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
        val isGlitchStorm = session.active_mutator == SectorMutator.GLITCH_STORM.id
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
                            val lootMeta = rollNormalLoot(legendaryBoost = isGlitchStorm)
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
                            val lootMeta = equipItems.randomOrNull() ?: rollNormalLoot(legendaryBoost = isGlitchStorm)
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
                                val lootMeta = rollNormalLoot(legendaryBoost = isGlitchStorm)
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
                    val preSignal = session.signal
                    if (preSignal > 90 && preSignal - damage <= 0) {
                        val protectedSignal = maxOf(1, (100 * 0.05f).toInt())
                        dao.insertRaidSession(session.copy(signal = protectedSignal, current_anomaly_id = null))
                        damageArmorHelmet(uid, damage)
                        log(uid, "🛡️ [ONE-SHOT PROTECTION]: Фатальный импульс ловушки отражен системным предохранителем! Сигнал стабилизирован на 5% без траты предметов.", "heal")
                    } else {
                        dao.insertRaidSession(session.copy(signal = maxOf(0, preSignal - damage), current_anomaly_id = null))
                        damageArmorHelmet(uid, damage)
                        log(uid, "⚡ ПРЯМОЙ УДАР: -${damage} Сигнала.", "error")
                    }
                } else if (optionId == "dodge") {
                    val roll = (0..100).random()
                    val activeStats = getActiveStats(uid)
                    val dodgeChance = 30 + activeStats.luck
                    if (roll < dodgeChance) {
                        dao.insertRaidSession(session.copy(current_anomaly_id = null))
                        log(uid, "✨ УСПЕХ: Вы уклонились от ловушки!", "info")
                    } else {
                        val damage = (gameEvent.value * 1.5).toInt()
                        val preSignal = session.signal
                        if (preSignal > 90 && preSignal - damage <= 0) {
                            val protectedSignal = maxOf(1, (100 * 0.05f).toInt())
                            dao.insertRaidSession(session.copy(signal = protectedSignal, current_anomaly_id = null))
                            damageArmorHelmet(uid, damage)
                            log(uid, "🛡️ [ONE-SHOT PROTECTION]: Фатальный урон ловушки отражен предохранителем! Сигнал стабилизирован на 5%.", "heal")
                        } else {
                            dao.insertRaidSession(session.copy(signal = maxOf(0, preSignal - damage), current_anomaly_id = null))
                            damageArmorHelmet(uid, damage)
                            log(uid, "💥 ПРОВАЛ: Уклонение не удалось! -${damage} Сигнала.", "error")
                        }
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
        val matchingUnequipped = inventory.filter { it.item_id == itemId && !it.is_equipped }
        val totalCount = matchingUnequipped.sumOf { it.quantity.coerceAtLeast(1) }

        if (totalCount < 3) {
            log(uid, "❌ [СИНТЕЗ]: Для синтеза требуется 3 неэкипированных шт. ${meta.name} (В наличии: $totalCount).", "error")
            return
        }

        val allItems = getAllItemsMetadata()
        val currentRarity = meta.rarity.lowercase()
        val nextRarity = when (currentRarity) {
            "common" -> "uncommon"
            "uncommon" -> "rare"
            "rare" -> "epic"
            "epic" -> "legendary"
            "legendary" -> "relic"
            "cursed" -> "relic"
            "relic" -> "legendary"
            else -> "rare"
        }

        val possibleUpgrades = allItems.filter { it.rarity.equals(nextRarity, ignoreCase = true) && it.id != itemId }
            .ifEmpty { allItems.filter { it.rarity.equals(nextRarity, ignoreCase = true) } }

        if (possibleUpgrades.isEmpty()) {
            log(uid, "❌ [СИНТЕЗ]: База данных EIDOS не нашла прототипов ранга ${nextRarity.uppercase()} для слияния.", "error")
            return
        }

        // Prefer same type if available, otherwise random of next rarity
        val sameTypeUpgrades = possibleUpgrades.filter { it.type == meta.type }
        val upgradedItem = if (sameTypeUpgrades.isNotEmpty()) sameTypeUpgrades.random() else possibleUpgrades.random()

        // Consume 3 items from unequipped stack/rows
        var neededToRemove = 3
        for (invItem in matchingUnequipped) {
            if (neededToRemove <= 0) break
            if (invItem.quantity > neededToRemove) {
                dao.updateInventoryItem(invItem.copy(quantity = invItem.quantity - neededToRemove))
                neededToRemove = 0
            } else {
                neededToRemove -= invItem.quantity
                dao.deleteInventoryItem(invItem)
            }
        }

        // Grant upgraded item
        internalUnsafeAddInventory(uid, upgradedItem.id, 1)
        log(
            uid,
            "🧬 [КВАНТОВЫЙ СИНТЕЗ]: 3x [${meta.name}] расплавлены в Ядре! Получен артефакт ранга [${nextRarity.uppercase()}]: ${upgradedItem.name}!",
            "success"
        )
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
        val targetUuid = SupabaseClientManager.cachedPlayerUuid
        if (targetUuid != null) {
            SupabaseClientManager.deleteInventoryItem(targetUuid, item.item_id)
        }
        if (player != null) {
            dao.updatePlayer(player.copy(
                biocoin = player.biocoin + bcReward,
                state_version = player.state_version + 1
            ))
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
        ForgeRecipeDefinition("rusty_knife", shardCost = 30, creditCost = 250L),
        ForgeRecipeDefinition("crowbar", shardCost = 50, creditCost = 500L),
        ForgeRecipeDefinition("hoodie", shardCost = 40, creditCost = 400L)
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

    
    suspend fun buyShadowBrokerItem(uid: Long, itemId: String, useBioCoins: Boolean = true) {
        val player = dao.getPlayer(uid) ?: return
        val meta = getItemMetadata(itemId) ?: return
        
        val bcCost = ShadowBrokerPrices.getBcPrice(meta)
        if (player.biocoin < bcCost) {
            log(uid, "❌ [ТЕНЕВОЙ БРОКЕР]: Недостаточно BioCoin для сделки! Требуется: $bcCost BC (У вас: ${player.biocoin} BC).", "error")
            return
        }
        dao.updatePlayer(player.copy(biocoin = player.biocoin - bcCost, state_version = player.state_version + 1))
        addInventory(uid, itemId, 1)
        log(uid, "📦 [ТЕНЕВОЙ БРОКЕР]: Приобретен артефакт ${meta.name} за $bcCost BC!", "success")
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
            log(uid, "Недостаточно кредитов для покупки ${meta.name}. Требуется: ${meta.price} BC.", "error")
            return
        }
        if (player.level < meta.reqLevel) {
            log(uid, "Требуется уровень Ядра ${meta.reqLevel} для приобретения ${meta.name} (Ваш уровень: ${player.level}).", "error")
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
        
        dao.updatePlayer(player.copy(biocoin = player.biocoin - meta.price, state_version = player.state_version + 1))
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
        
        dao.updatePlayer(player.copy(
            biocoin = player.biocoin + sellPrice,
            state_version = player.state_version + 1
        ))
        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1))
        } else {
            dao.deleteInventoryItem(item)
            val targetUuid = SupabaseClientManager.cachedPlayerUuid
            if (targetUuid != null) {
                SupabaseClientManager.deleteInventoryItem(targetUuid, item.item_id)
            }
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

    suspend fun ensureDevicePlayerExists(uid: Long, deviceUuid: String, defaultUsername: String) = dbMutex.withLock {
        internalUnsafeEnsureDevicePlayerExists(uid, deviceUuid, defaultUsername)
    }

    private suspend fun internalUnsafeEnsureDevicePlayerExists(uid: Long, deviceUuid: String, defaultUsername: String) {
        val target = if (uid <= 0L) (Math.abs(deviceUuid.hashCode().toLong()) + 100000L) else uid
        activeDeviceUid = target
        val legacyHashUid = Math.abs(deviceUuid.hashCode().toLong()) + 100000L
        if (dao.getPlayer(target) == null) {
            val legacyPlayer = if (target != legacyHashUid) dao.getPlayer(legacyHashUid) else null
            if (legacyPlayer != null) {
                dao.insertPlayer(legacyPlayer.copy(uid = target))
            } else {
                dao.insertPlayer(Player(uid = target, username = defaultUsername, first_name = defaultUsername, biocoin = 500L))
            }
        }
        // Seamless migration: transfer items from legacy hash UID if target inventory is empty
        if (target != legacyHashUid) {
            val legacyItems = dao.getInventorySync(legacyHashUid)
            if (legacyItems.isNotEmpty()) {
                val currentTargetItems = dao.getInventorySync(target)
                if (currentTargetItems.isEmpty()) {
                    legacyItems.forEach { oldItem ->
                        dao.insertInventoryItem(oldItem.copy(id = 0, uid = target))
                    }
                }
            }
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
            dao.insertLog(GameLog(uid = targetUid, message = message, type = type))
            if ((0..20).random() == 0) {
                dao.trimOldLogs(targetUid)
            }
            // Cloud mirror runs detached: log() is frequently called inside
            // dbMutex.withLock, and a blocking OkHttp call there would hold the
            // mutex for the whole network round-trip (deadlock-prone pattern).
            backgroundScope.launch {
                runCatching { SupabaseClientManager.addRaidLog(targetUid.toString(), message) }
            }
        } catch (e: Exception) {
            android.util.Log.e("GameRepository", "log failed: ${e.message}")
        }
    }

    fun getLogs(uid: Long): Flow<List<GameLog>> = dao.getLogsFlow(uid)

    fun getPlayer(uid: Long): Flow<Player?> = dao.getPlayerFlow(uid)
    
    suspend fun getPlayerSync(uid: Long): Player? {
        val player = dao.getPlayer(uid)
        if (player != null) {
            // Auto-heal / sync kills count from bestiary if kills counter is zero
            var effectivePlayer = player
            if (player.kills == 0) {
                val totalBestiaryKills = runCatching {
                    dao.getBestiaryFlow().first().sumOf { it.killed_count }
                }.getOrDefault(0)
                if (totalBestiaryKills > 0) {
                    effectivePlayer = player.copy(kills = totalBestiaryKills)
                    dao.updatePlayer(effectivePlayer)
                }
            }

            loadEquipment(uid)
            if (!overdriveChargeMap.containsKey(uid)) {
                overdriveChargeMap[uid] = effectivePlayer.overdriveCharge
                _overdriveChargeFlow.value = effectivePlayer.overdriveCharge
            }
            if (!overchargeTierMap.containsKey(uid)) {
                overchargeTierMap[uid] = effectivePlayer.overchargeTier
                _overchargeTierFlow.value = effectivePlayer.overchargeTier
            }
            return effectivePlayer
        }
        return null
    }

    suspend fun savePlayer(player: Player) = dbMutex.withLock {
        val existing = originalDao.getPlayer(player.uid)
        if (existing != null) {
            dao.updatePlayer(player)
        } else {
            dao.insertPlayer(player)
        }
    }

    data class EnergyRegenReport(
        val validationMessage: String?,
        val gained: Int = 0,
        val newEnergy: Int = 0,
        val reachedMax: Boolean = false
    ) {
        val regenerated: Boolean get() = gained > 0
    }

    /**
     * Atomic read-modify-write energy regeneration under dbMutex.
     *
     * Used by both the offline catch-up path and the periodic in-app ticker;
     * previously these were two duplicated blocks in MainViewModel whose
     * read -> copy -> savePlayer sequences could interleave with other
     * player writes (lost updates). The whole cycle now runs inside one
     * critical section.
     *
     * @param resetIdleTimestamp when true, timestamps are refreshed even if
     * no energy could be regenerated (offline path keeps last_active fresh);
     * the periodic ticker passes false and leaves idle rows untouched.
     */
    suspend fun regenerateEnergy(
        uid: Long,
        regenIntervalMs: Long = 5 * 60 * 1000L, // 5 minutes
        resetIdleTimestamp: Boolean
    ): EnergyRegenReport? = dbMutex.withLock {
        val p = dao.getPlayer(uid) ?: return@withLock null
        val validation = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.validateAndSanitizeTimestamp(context)
        val safeNow = validation.sanitizedCurrentTime

        if (p.energy >= p.max_energy) {
            if (resetIdleTimestamp) {
                dao.updatePlayer(p.copy(last_active = safeNow))
            }
            return@withLock EnergyRegenReport(validationMessage = validation.message)
        }

        val diffMs = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.calculateSafeOfflineDurationMs(
            lastActiveTimestamp = p.last_active,
            currentValidatedTimestamp = safeNow
        )
        if (diffMs < regenIntervalMs) {
            if (resetIdleTimestamp) {
                dao.updatePlayer(p.copy(last_active = safeNow))
            }
            return@withLock EnergyRegenReport(validationMessage = validation.message)
        }

        val gained = (diffMs / regenIntervalMs).toInt()
        if (gained <= 0) {
            return@withLock EnergyRegenReport(validationMessage = validation.message)
        }

        val newEnergy = minOf(p.max_energy, p.energy + gained)
        // state_version is bumped by the dao wrapper on updatePlayer
        dao.updatePlayer(p.copy(
            energy = newEnergy,
            last_active = safeNow - (diffMs % regenIntervalMs),
            updated_at = safeNow
        ))
        EnergyRegenReport(
            validationMessage = validation.message,
            gained = gained,
            newEnergy = newEnergy,
            reachedMax = newEnergy >= p.max_energy
        )
    }

    suspend fun addInventoryDirect(
        uid: Long,
        itemId: String,
        quantity: Int,
        isEquipped: Boolean = false,
        slot: String? = null
    ) = dbMutex.withLock {
        val meta = getItemMetadata(itemId)
        val defaultEq = if (meta != null) PoECraftEngine.generateDefaultEquipment(meta.rarity) else null
        val serialized = if (defaultEq != null) PoECraftEngine.serializeEquipment(defaultEq) else null
        val effectiveSlot = slot ?: ItemSlotUtils.getSlotForItem(itemId, meta)
        dao.insertInventoryItem(
            InventoryItem(
                uid = uid,
                item_id = itemId,
                quantity = quantity,
                durability = 100f,
                is_equipped = isEquipped,
                slot = effectiveSlot,
                custom_data = serialized
            )
        )
    }

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
        val head = inventory.find { it.is_equipped && (it.slot == "head" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "head") }
        val armor = inventory.find { it.is_equipped && (it.slot == "armor" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "armor") }
        val weapon = inventory.find { it.is_equipped && (it.slot == "weapon" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "weapon") }
        val chips = inventory.filter { it.is_equipped && (it.slot == "chip" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "chip") }
            .distinctBy { it.item_id }
            .take(4)
        val shard = inventory.find { it.is_equipped && (it.slot == "eidos_shard" || it.item_id == "eidos_shard") }
        val equipped = listOfNotNull(head, armor, weapon, shard) + chips

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

        val hasKamikaze = equipped.any { it.item_id == "kamikaze_protocol" && it.durability > 0f }
        val rawTotalAtk = player.attack + atkBonus
        val finalAttack = if (hasKamikaze) (rawTotalAtk * 1.35f).toInt() else rawTotalAtk

        return PlayerStats(
            hp = player.hp,
            maxHp = player.max_hp + maxHpBonus,
            energy = player.energy,
            maxEnergy = player.max_energy,
            attack = finalAttack,
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

    suspend fun syncUserEquipmentToDb(uid: Long) {
        val inventory = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
        val head = inventory.find { it.slot == "head" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "head" }?.item_id
        val armor = inventory.find { it.slot == "armor" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "armor" }?.item_id
        val weapon = inventory.find { it.slot == "weapon" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "weapon" }?.item_id
        val chips = inventory.filter { it.slot == "chip" || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == "chip" }
            .distinctBy { it.item_id }
            .take(4)
        val chipStr = if (chips.isNotEmpty()) chips.joinToString(",") { it.item_id } else null
        val shard = inventory.find { it.slot == "eidos_shard" || it.item_id == "eidos_shard" }?.item_id

        val equipment = UserEquipment(
            player_uid = uid,
            head = head,
            armor = armor,
            weapon = weapon,
            chip = chipStr,
            eidos_shard = shard
        )
        dao.saveUserEquipment(equipment)
    }

    suspend fun loadEquipment(uid: Long): UserEquipment? {
        val userEq = dao.getUserEquipment(uid)
        if (userEq != null) {
            val inventory = dao.getInventoryFlow(uid).first()
            val chipList = userEq.chip?.split(",")?.map { it.trim() }?.filter { it.isNotBlank() }?.distinct()?.take(4) ?: emptyList()
            val equippedChipIds = mutableSetOf<String>()
            var headEquipped = false
            var armorEquipped = false
            var weaponEquipped = false
            var shardEquipped = false

            inventory.forEach { invItem ->
                val isHead = !headEquipped && invItem.item_id == userEq.head
                val isArmor = !armorEquipped && invItem.item_id == userEq.armor
                val isWeapon = !weaponEquipped && invItem.item_id == userEq.weapon
                val isShard = !shardEquipped && invItem.item_id == userEq.eidos_shard
                val isChip = chipList.contains(invItem.item_id) && !equippedChipIds.contains(invItem.item_id) && equippedChipIds.size < 4

                if (isHead) headEquipped = true
                if (isArmor) armorEquipped = true
                if (isWeapon) weaponEquipped = true
                if (isShard) shardEquipped = true
                if (isChip) equippedChipIds.add(invItem.item_id)

                val shouldBeEquipped = isHead || isArmor || isWeapon || isShard || isChip
                if (invItem.is_equipped != shouldBeEquipped) {
                    val targetSlot = when {
                        isHead -> "head"
                        isArmor -> "armor"
                        isWeapon -> "weapon"
                        isShard -> "eidos_shard"
                        isChip -> "chip"
                        else -> null
                    }
                    dao.updateInventoryItem(invItem.copy(is_equipped = shouldBeEquipped, slot = if (shouldBeEquipped) targetSlot else null))
                }
            }
        }
        return userEq
    }

    suspend fun unequipSlot(uid: Long, slot: String) {
        val inventory = dao.getInventoryFlow(uid).first()
        val itemsInSlot = inventory.filter {
            it.is_equipped && (it.slot == slot || ItemSlotUtils.getSlotForItem(it.item_id, getItemMetadata(it.item_id)) == slot)
        }
        val player = dao.getPlayer(uid)
        itemsInSlot.forEach { item ->
            dao.updateInventoryItem(item.copy(is_equipped = false, slot = null))
            SupabaseClientManager.updateInventoryItemEquipped(uid.toString(), item.item_id, false)
        }
        syncUserEquipmentToDb(uid)
        if (player != null) dao.updatePlayer(player.copy(state_version = player.state_version + 1))
        log(uid, "Слот $slot очищен.", "info")
        capPlayerHp(uid)
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

        // Unequip current item(s) in targetSlot (allow up to 4 chips without unequipping others)
        val inventory = dao.getInventoryFlow(uid).first()
        if (targetSlot == "chip") {
            val equippedChips = inventory.filter { invItem ->
                invItem.is_equipped && (invItem.slot == "chip" || ItemSlotUtils.getSlotForItem(invItem.item_id, getItemMetadata(invItem.item_id)) == "chip")
            }
            val isDuplicate = equippedChips.any { it.item_id == item.item_id }
            if (isDuplicate) {
                log(uid, "❌ [ПРОТОКОЛ ЧИПОВ]: Чип [${meta?.name ?: item.item_id}] уже установлен! Нельзя экипировать одинаковые чипы.", "error")
                return
            }
            if (equippedChips.size >= 4) {
                val chipToReplace = equippedChips.last()
                dao.updateInventoryItem(chipToReplace.copy(is_equipped = false, slot = null))
                SupabaseClientManager.updateInventoryItemEquipped(uid.toString(), chipToReplace.item_id, false)
                log(uid, "⚠️ Все 4 слота чипов заняты: чип [${getItemMetadata(chipToReplace.item_id)?.name ?: chipToReplace.item_id}] в слоте 4 заменен и возвращен в инвентарь.", "warn")
            }
        } else {
            inventory.forEach { invItem ->
                if (invItem.is_equipped) {
                    val invMeta = getItemMetadata(invItem.item_id)
                    val invSlot = invItem.slot ?: ItemSlotUtils.getSlotForItem(invItem.item_id, invMeta)
                    if (invSlot == targetSlot) {
                        dao.updateInventoryItem(invItem.copy(is_equipped = false, slot = null))
                        SupabaseClientManager.updateInventoryItemEquipped(uid.toString(), invItem.item_id, false)
                    }
                }
            }
        }

        dao.updateInventoryItem(item.copy(is_equipped = true, slot = targetSlot))
        syncUserEquipmentToDb(uid)
        SupabaseClientManager.updateInventoryItemEquipped(uid.toString(), item.item_id, true)
        dao.updatePlayer(player.copy(state_version = player.state_version + 1))
        log(uid, "Надето: ${meta?.name ?: item.item_id} в слот $targetSlot (Lvl $reqLevel).", "info")
        capPlayerHp(uid)
    }

    suspend fun unequipItem(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid)
        dao.updateInventoryItem(item.copy(is_equipped = false, slot = null))
        syncUserEquipmentToDb(uid)
        SupabaseClientManager.updateInventoryItemEquipped(uid.toString(), item.item_id, false)
        if (player != null) dao.updatePlayer(player.copy(state_version = player.state_version + 1))
        log(uid, "Предмет снят.", "info")
        capPlayerHp(uid)
    }

    suspend fun useConsumable(uid: Long, item: InventoryItem) {
        val meta = getItemMetadata(item.item_id) ?: return
        val player = dao.getPlayer(uid) ?: return
        val session = dao.getRaidSession(uid)

        // ANTIGRAVITY mutator: healing medkits are blocked by the gravity field
        if (session?.active_mutator == SectorMutator.ANTIGRAVITY.id &&
            item.item_id in listOf("medkit_small", "medkit_large", "neural_stimulator")
        ) {
            log(uid, "🪐 [АНТИГРАВИТАЦИЯ]: Мед-модули подавлены гравитационным полем! Восстановление HP заблокировано.", "error")
            return
        }

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
                val synergies = getActiveChipSynergies(uid)
                val hasDuoRedBlue = synergies.any { it.id == "syn_duo_red_blue" }
                val hasBlue4 = synergies.any { it.id == "syn_blue_4" }

                val excessEnergy = maxOf(0, (player.energy + 50) - player.max_energy)
                val newEnergy = minOf(player.max_energy, player.energy + 50)
                dao.updatePlayer(player.copy(energy = newEnergy))
                batteryOverclockTurns[uid] = 2
                consumeOneItem(uid, item)
                log(uid, "⚡ [ЭНЕРГО-БАТАРЕЯ]: Восстановлено +50 EP! Перегрузка сервоприводов (+15% ATK на 2 хода)!", "heal")

                if (hasDuoRedBlue && session != null && session.current_enemy_id != null) {
                    val pulseDmg = 35
                    val newEnemyHp = maxOf(0, session.current_enemy_hp - pulseDmg)
                    dao.insertRaidSession(session.copy(current_enemy_hp = newEnemyHp))
                    log(uid, "💥 [РЕАКТОР ВОЗМЕЗДИЯ]: Детонация энерго-ячейки нанесла -$pulseDmg урона врагу!", "combat")
                    _combatEventFlow.tryEmit(CombatVisualEvent(damage = pulseDmg, textPopup = "💥 РЕАКТОР -$pulseDmg", popupColor = "0xFFFF00FF"))
                }
                if (hasBlue4 && excessEnergy > 0) {
                    val shieldBonus = excessEnergy
                    val newHp = minOf(player.max_hp + 50, player.hp + shieldBonus)
                    dao.updatePlayer(player.copy(hp = newHp))
                    log(uid, "🌀 [СИНГУЛЯРНОСТЬ]: Избыточные +$excessEnergy EP преобразованы в Энерго-Щит!", "info")
                }
            }
            "neural_stimulator", "medkit_small", "medkit_large" -> {
                val healAmount = maxOf(1, (player.max_hp * 0.50f).toInt())
                val newHp = minOf(player.max_hp, player.hp + healAmount)
                dao.updatePlayer(player.copy(hp = newHp))
                if (session != null) {
                    dao.insertRaidSession(session.copy(signal = newHp))
                }
                consumeOneItem(uid, item)
                log(uid, "💉 [МЕД-МОДУЛЬ]: Целостность Сигнала восстановлена на +50% (+$healAmount HP)!", "heal")
            }
            "emp_grenade" -> {
                if (session != null && session.current_enemy_hp > 0) {
                    if (empUsedInCombat[uid] == true) {
                        log(uid, "❌ [ЭМИ-ГРАНАТА]: Разрешено не более 1 использования за бой!", "error")
                        return
                    }
                    val stats = getActiveStats(uid)
                    val damage = io.eidos.zerolayer.domain.combat.CombatMath.calculateEmpDamage(session.current_enemy_hp, stats.attack)
                    empUsedInCombat[uid] = true
                    stunnedEnemies[uid] = true // Сбивает силовой заряд и оглушает врага!
                    consumeOneItem(uid, item)
                    val newEnemyHp = maxOf(0, session.current_enemy_hp - damage)
                    if (newEnemyHp <= 0) {
                        empUsedInCombat[uid] = false
                        matterStealUsedInCombat[uid] = false
                        dao.insertRaidSession(session.copy(current_enemy_hp = 0, current_enemy_id = null, kills = session.kills + 1))
                        log(uid, "💣 [ЭМИ-ГРАНАТА]: Врагу нанесено $damage ЧИСТОГО УРОНА! Противник полностью аннигилирован!", "combat")
                    } else {
                        dao.insertRaidSession(session.copy(current_enemy_hp = newEnemyHp))
                        log(uid, "💣 [ЭМИ-ГРАНАТА]: Силовой контур врага сорван! Нанесено $damage чистых повреждений, цель ОГЛУШЕНА на 1 ход!", "combat")
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
        val player = dao.getPlayer(uid)
        if (item.quantity > 1) {
            dao.updateInventoryItem(item.copy(quantity = item.quantity - 1))
        } else {
            dao.deleteInventoryItem(item)
            val targetUuid = SupabaseClientManager.cachedPlayerUuid
            if (targetUuid != null) {
                SupabaseClientManager.deleteInventoryItem(targetUuid, item.item_id)
            }
        }
        if (player != null) {
            dao.updatePlayer(player.copy(state_version = player.state_version + 1))
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

        val requiredShards = ZeroLayerEconomy.calculateShardRepairCost(meta.rarity)
        val inventory = dao.getInventoryFlow(uid).first()
        val shards = inventory.find { it.item_id == "eidos_shard" }
        if (shards == null || shards.quantity < requiredShards) {
            log(uid, "Недостаточно Осколков Эйдоса. Нужно $requiredShards💎 (У вас: ${shards?.quantity ?: 0}💎).", "error")
            return
        }

        if (shards.quantity == requiredShards) {
            dao.deleteInventoryItem(shards)
        } else {
            dao.updateInventoryItem(shards.copy(quantity = shards.quantity - requiredShards))
        }

        val newDurability = minOf(100f, item.durability + 25f)
        dao.updateInventoryItem(item.copy(durability = newDurability))
        log(uid, "Успешно отремонтировано ${meta.name} за $requiredShards Осколков Эйдоса (+25% прочности).", "info")
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

    suspend fun buyMetaUpgrade(uid: Long, upgradeType: String) = dbMutex.withLock {
        internalUnsafeBuyMetaUpgrade(uid, upgradeType)
    }

    private suspend fun internalUnsafeBuyMetaUpgrade(uid: Long, upgradeType: String) {
        val player = dao.getPlayer(uid) ?: return
        val currentLevel = when (upgradeType) {
            "signal" -> player.meta_signal_level
            "key" -> player.meta_key_level
            "luck" -> player.meta_luck_level
            "power" -> player.meta_power_level
            else -> 0
        }
        val cost = (currentLevel + 1) * 5
        val hasDeducted = internalUnsafeDeductShards(uid, cost)
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

    // --- World Boss (persistent shared pool, monthly cycle) ---

    fun getWorldBossMonthKey(): String {
        val cal = java.util.Calendar.getInstance()
        return "%04d-%02d".format(cal.get(java.util.Calendar.YEAR), cal.get(java.util.Calendar.MONTH) + 1)
    }

    suspend fun getWorldBossState(): WorldBossState {
        var state = dao.getWorldBossState() ?: WorldBossState()
        // Monthly reset: fresh pool every calendar month, cycle keeps growing
        if (state.last_reset_month != getWorldBossMonthKey()) {
            state = WorldBossState(
                id = 1,
                boss_hp = state.boss_max_hp,
                boss_max_hp = state.boss_max_hp,
                cycle = state.cycle,
                last_reset_month = getWorldBossMonthKey()
            )
            dao.insertWorldBossState(state)
        }
        return state
    }

    suspend fun getTopWorldBossContributors(): List<BossContributor> =
        dao.getTopWorldBossContributors(5)

    // --- Singularity Terminal (endgame finale + NG+ prestige) ---

    suspend fun isSingularityTerminalReady(uid: Long): Boolean {
        val p = dao.getPlayer(uid) ?: return false
        // The Core gate at 1000m must have been breached at least once
        return p.max_depth >= 1000
    }

    /**
     * Chapter VI finale: three endings, each a different NG+ meta-loop.
     * great_reset  - prestige: level reset, +10% rewards per cycle (prestige_count);
     * ascension    - OMNI path: shard hoard + archivist bounty;
     * abyss        - abyss pact: keys + deep reserves.
     */
    suspend fun completeSingularityEnding(uid: Long, endingId: String) = dbMutex.withLock {
        val player = dao.getPlayer(uid) ?: return@withLock
        when (endingId) {
            "great_reset" -> {
                dao.updatePlayer(player.copy(
                    level = 1,
                    xp = 0,
                    prestige_count = player.prestige_count + 1,
                    hp = player.max_hp,
                    energy = player.max_energy
                ))
                log(uid, "♾ [ВЕЛИКИЙ СБРОС]: Ядро EIDOS-CORE перезаписано. Матрица уровня обнулена - Нейро-Ядро перерождается с Level 1, " +
                    "но резонанс прошлых циклов навсегда даёт +${(player.prestige_count + 1) * 10}% ко всем наградам рейдов. Цикл ${player.prestige_count + 1} начался.", "loot")
            }
            "ascension" -> {
                addInventory(uid, "eidos_shard", 25)
                dao.updatePlayer(player.copy(biocoin = player.biocoin + 25000L))
                log(uid, "🌐 [ЦИФРОВОЕ ВОЗНЕСЕНИЕ]: Код оператора влит в OMNI-слой Архитекторов. Получено: +25 💎 Осколков, +25000 BC. " +
                    "Твоя сигнатура теперь часть фундамента Эйдоса.", "loot")
            }
            "abyss" -> {
                addInventory(uid, "eidos_shard", 10)
                addInventory(uid, "abyssal_key", 5)
                dao.updatePlayer(player.copy(biocoin = player.biocoin + 15000L))
                log(uid, "🕳 [СИНГУЛЯРНОСТЬ БЕЗДНЫ]: Ты отринул и Сброс, и Вознесение. Бездна приняла дар: +10 💎 Осколков, +5 🗝 Ключей Бездны, +15000 BC. " +
                    "Глубина ждёт.", "loot")
            }
            else -> log(uid, "❌ [ТЕРМИНАЛ]: Неизвестная директива Сингулярности.", "error")
        }
    }


    suspend fun hitWorldBoss(uid: Long) = dbMutex.withLock {
        internalUnsafeHitWorldBoss(uid)
    }

    private suspend fun internalUnsafeHitWorldBoss(uid: Long) {
        val player = dao.getPlayer(uid) ?: return
        if (player.energy < 10) {
            log(uid, "❌ [МИРОВОЙ БОСС: EIDOS-CORE]: Недостаточно энергии (требуется 10⚡). Восстановите силы в Хабе.", "error")
            return
        }

        val state = getWorldBossState()
        if (state.boss_hp <= 0) {
            log(uid, "💠 [МИРОВОЙ БОСС]: EIDOS-CORE уже пал в этом цикле. Ожидается перезапуск пула.", "info")
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

        val newHp = maxOf(0L, state.boss_hp - damage)
        dao.insertWorldBossState(state.copy(boss_hp = newHp))
        dao.addWorldBossDamage(uid, damage.toLong())

        // Stage milestones: global progress checkpoints at 75/50/25% pool HP
        val oldPct = state.boss_hp * 100 / state.boss_max_hp
        val newPct = newHp * 100 / state.boss_max_hp
        listOf(75L, 50L, 25L).forEach { stage ->
            if (oldPct > stage && newPct <= stage) {
                log(uid, "💠 [МИРОВОЙ БОСС]: Пул EIDOS-CORE пробит до $stage%! Операторы близки к следующему рубежу!", "loot")
            }
        }

        if (newHp <= 0L) {
            // Pool defeated: big one-time reward to the killer + next cycle (+50% HP, richer loot)
            addInventory(uid, "eidos_shard", 3)
            dao.updatePlayer(dao.getPlayer(uid)?.copy(biocoin = player.biocoin + rewardsCoin + 5000, xp = player.xp + rewardXp + 2000) ?: updatedPlayer)
            val nextState = WorldBossState(
                id = 1,
                boss_hp = (state.boss_max_hp * 15 / 10),
                boss_max_hp = (state.boss_max_hp * 15 / 10),
                cycle = state.cycle + 1,
                last_reset_month = state.last_reset_month
            )
            dao.insertWorldBossState(nextState)
            log(uid, "🎉 [ЯДРО ПАЛО]: EIDOS-CORE уничтожен (цикл ${state.cycle})! Ты нанёс финальный удар: +5000 BC, +2000 XP, +3 💎 Осколка. Начинается цикл ${nextState.cycle}: ядро перезапущено (+50% прочности)!", "loot")
            return
        }

        val cycleBonus = if (state.cycle > 1) ", цикл ${state.cycle} (x${"%.1f".format(state.boss_max_hp / 984_124_510f)})" else ""
        val roll = (1..100).random()
        if (roll <= 15) {
            addInventory(uid, "data_fragment", 1)
            log(uid, "⚔ [МИРОВОЙ БОСС]: Нанесено $damage урона! Пул: ${"%,d".format(newHp)} HP$cycleBonus. Награда: +$rewardsCoin BC, +$rewardXp XP, 💾 Фрагмент Данных (-10⚡).", "loot")
        } else {
            log(uid, "⚔ [МИРОВОЙ БОСС]: Нанесено $damage урона! Пул: ${"%,d".format(newHp)} HP$cycleBonus. Награда: +$rewardsCoin BC, +$rewardXp XP (-10⚡).", "combat")
        }
    }

    suspend fun startRaid(uid: Long, startDepth: Int) = dbMutex.withLock {
        internalUnsafeStartRaid(uid, startDepth)
    }

    private suspend fun internalUnsafeStartRaid(uid: Long, startDepth: Int) {
        val player = dao.getPlayer(uid) ?: return
        val isFreeEntry = player.raids_done == 0
        val startCostCoins = if (isFreeEntry) 0L else 20L

        val isEmergencyGrace = !isFreeEntry && player.biocoin < startCostCoins
        val feeCoins = if (isEmergencyGrace) {
            log(uid, "⚡ [ПРОТОКОЛ ЕВЫ-09]: Нулевой баланс. Предоставлен экстренный допуск в Слой без списания BC!", "info")
            player.biocoin
        } else if (startCostCoins > 0) {
            maxOf(0L, player.biocoin - startCostCoins)
        } else {
            player.biocoin
        }

        dao.updatePlayer(player.copy(
            biocoin = feeCoins,
            hp = player.max_hp,
            energy = player.max_energy
        ))

        setOverdriveCharge(uid, 0)
        setOverchargeTier(uid, 0)
        shadowDanceGuaranteedCrit[uid] = false
        pactResurrectionsUsed[uid] = false

        io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context).logRaidStarted(startDepth, 100)

        var session = RaidSession(
            uid = uid,
            depth = startDepth,
            signal = player.max_hp,
            next_event_type = "scan"
        )

        // Meta upgrade "Карманный Мастер-Ключ": each level guarantees one
        // master_key in the raid buffer (previously the upgrade gave nothing)
        val keyBonus = player.meta_key_level
        if (keyBonus > 0) {
            val keys = List(keyBonus) { "master_key" }.joinToString(",")
            val items = if (session.buffer_items.isEmpty()) keys else "${session.buffer_items},$keys"
            session = session.copy(buffer_items = items)
            log(uid, "🔑 [КАРМАННЫЙ МАСТЕР-КЛЮЧ]: Уровень $keyBonus - на склад рейда доставлено $keyBonus отмычек!", "info")
        }

        dao.insertRaidSession(session)
        val feeMsg = if (isFreeEntry) "Первый спуск — БЕСПЛАТНО" else "Списано -$startCostCoins BC"
        log(uid, "Нейро-связь установлена. Вход в Нулевой Слой на ${startDepth}м ($feeMsg).", "info")
    }

    suspend fun processStep(uid: Long, chosenMutatorId: String? = null, costEnergyOverride: Int? = null) {
        val initialSession = dao.getRaidSession(uid) ?: return
        var session = initialSession
        val player = dao.getPlayer(uid) ?: return

        if (session.current_enemy_id != null) {
            val cleanSession = if (session.current_anomaly_id != null) {
                val updated = session.copy(current_anomaly_id = null)
                dao.insertRaidSession(updated)
                updated
            } else session
            handleCombatTurn(uid, cleanSession, player, isGuarding = false)
            return
        }
        if (session.current_anomaly_id != null) {
            return
        }

        val stepGainXp = 5L + (session.depth / 200)

        // Dynamic Energy step cost: 5 EP (10 EP with architect_eye)
        val inventory = dao.getInventoryFlow(uid).first()
        val equippedItems = inventory.filter { it.is_equipped }
        val hasArchitectEye = equippedItems.any { it.item_id == "architect_eye" }
        
        // Chip synergies check: Ghost synergy (-2 EP step cost)
        val activeSynergies = getActiveChipSynergies(uid)
        val hasGhostSynergy = activeSynergies.any { it.id == "syn_duo_green_blue" }

        val rawStepCost = costEnergyOverride ?: (if (hasArchitectEye) 10 else 5)
        val stepEnergyCost = if (hasGhostSynergy) maxOf(1, rawStepCost - 2) else rawStepCost

        var remainingEnergy = player.energy
        var currentHp = player.hp

        if (player.energy < stepEnergyCost) {
            // Механика «Кровавый Овердрайв» при нехватке EP: шаг ценой 8% HP без блокировок
            val bloodCost = maxOf(1, (player.max_hp * 0.08f).toInt())
            currentHp = maxOf(0, player.hp - bloodCost)
            remainingEnergy = 0
            log(uid, "🩸 [КРОВАВЫЙ ШАГ]: Энергия исчерпана! Шаг вглубь ценой -$bloodCost HP (8%).", "error")
        } else {
            remainingEnergy = player.energy - stepEnergyCost
        }

        // Step durability loss (0.1%)
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
            val bloodLoss = maxOf(1, (currentHp * 0.02).toInt())
            log(uid, "🩸 [Майнер на Крови]: Получено +50 BC, потеряно -$bloodLoss HP.", "error")
            player.copy(biocoin = player.biocoin + 50, hp = maxOf(0, currentHp - bloodLoss), xp = player.xp + stepGainXp, energy = remainingEnergy)
        } else {
            player.copy(hp = currentHp, xp = player.xp + stepGainXp, energy = remainingEnergy)
        }

        // Handle Vault / Rift instant events
        if (chosenMutatorId == SectorMutator.LASER_VAULT.id) {
            val vaultCoins = (120..260).random() * (1 + session.depth / 250)
            session = session.copy(buffer_coins = session.buffer_coins + vaultCoins)
            log(uid, "🔓 [ЗАПЕЧАТАННЫЙ БУНКЕР]: Лазерная сеть пройдена сквозь помехи (-$stepEnergyCost EP)! Вскрыт защищенный терминал: +$vaultCoins BC!", "loot")
        } else if (chosenMutatorId == SectorMutator.MAXWELL_RIFT.id) {
            val isShardDrop = (0..100).random() < 40
            if (isShardDrop) {
                val newBuffer = if (session.buffer_items.isEmpty()) "eidos_shard" else "${session.buffer_items},eidos_shard"
                session = session.copy(buffer_items = newBuffer)
                log(uid, "🌀 [РАЗЛОМ МАКСВЕЛЛА]: Квантовая флуктуация сконденсировала +1 Осколок Эйдоса!", "loot")
            } else {
                log(uid, "🌀 [РАЗЛОМ МАКСВЕЛЛА]: Пространственный туннель искривляет метрики Бездны!", "info")
            }
        }

        // Синхронизация единого Здоровья (Сигнала)
        session = session.copy(signal = workingPlayer.hp)
        dao.insertRaidSession(session)

        if (workingPlayer.hp <= 0) {
            dao.updatePlayer(workingPlayer)
            checkDeath(uid)
            return
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

        // 5000+m Abyssal Singularity room affix handling or chosen sector mutator
        var currentMutator = chosenMutatorId ?: session.active_mutator
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
            gravesList = gravesList,
            activeMutatorId = session.active_mutator
        )

        when (dispatchResult) {
            is io.eidos.zerolayer.domain.raid.RaidEventDispatcher.DispatchResult.VoidStep -> {
                val updatedPlayer = workingPlayer.copy(xp = workingPlayer.xp + dispatchResult.xpGain)
                dao.updatePlayer(updatedPlayer)
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "scan",
                    is_scanned = false
                ))
                log(uid, dispatchResult.message, "info")
            }
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
                val isCursed = newDepth >= 1500 && (currentMutator?.contains("cursed") == true || newDepth % 4 == 0)
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = if (isCursed) "cursed_loot" else "loot",
                    is_scanned = false
                ))
                val chestName = if (isCursed) "ПРОКЛЯТЫЙ ТАЙНИК БЕЗДНЫ (Нужен Ключ Бездны)" else "ЗАШИФРОВАННЫЙ ТАЙНИК (Нужен Дата-шип)"
                log(uid, "📦 [ОБНАРУЖЕН ТАЙНИК]: $chestName", "info")
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
                val enemyStartingHp = if (currentMutator == SectorMutator.FRAGILE_CORE.id) {
                    maxOf(1, (dispatchResult.enemyHp * 0.5f).toInt())
                } else {
                    dispatchResult.enemyHp
                }
                // Gatekeeper reward: at every 1000m the warden carries the Biome Key
                var bufferForGate = session.buffer_items
                if (newDepth > 0 && newDepth % 1000 == 0) {
                    bufferForGate = if (bufferForGate.isEmpty()) "abyssal_key" else "$bufferForGate,abyssal_key"
                }
                dao.insertRaidSession(session.copy(
                    depth = newDepth,
                    active_mutator = currentMutator,
                    next_event_type = "combat",
                    current_enemy_id = dispatchResult.enemyName,
                    current_enemy_hp = enemyStartingHp,
                    current_anomaly_id = null,
                    combat_turn = 0,
                    damage_buffer = 0,
                    buffer_items = bufferForGate,
                    is_scanned = false
                ))
                recordEnemyEncounter(dispatchResult.enemyName)
                log(uid, dispatchResult.message, "combat")
                if (newDepth > 0 && newDepth % 1000 == 0) {
                    log(uid, "🗝 [ТРОФЕЙ ХРАНИТЕЛЯ]: Ключ Биомы упадёт в буфер после победы над стражем врат ${newDepth}м!", "loot")
                }
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

    suspend fun resolveRiddle(uid: Long, isCorrect: Boolean) = dbMutex.withLock {
        val session = dao.getRaidSession(uid) ?: return@withLock
        val player = dao.getPlayer(uid) ?: return@withLock
        if (isCorrect) {
            val rewardCoins = 150L + (session.depth / 10L)
            val rewardXp = 100L + (session.depth / 20L)
            dao.insertRaidSession(session.copy(
                riddles_solved = session.riddles_solved + 1,
                buffer_coins = session.buffer_coins + rewardCoins,
                buffer_xp = session.buffer_xp + rewardXp,
                next_event_type = "scan"
            ))
            dao.updatePlayer(player.copy(xp = player.xp + rewardXp))
            log(uid, "🧩 [СФИНКС]: Загадка решена верно! Получено +$rewardCoins BC, +$rewardXp XP.", "loot")
        } else {
            val penaltyDmg = 15
            val newSignal = maxOf(1, session.signal - penaltyDmg)
            val newHp = maxOf(1, player.hp - penaltyDmg)
            dao.insertRaidSession(session.copy(
                signal = newSignal,
                next_event_type = "scan"
            ))
            dao.updatePlayer(player.copy(hp = newHp))
            log(uid, "🧩 [СФИНКС]: Ошибка в логике! Разряд искажения нанес -$penaltyDmg урона.", "error")
        }
    }

    suspend fun attackCombat(uid: Long) = dbMutex.withLock {
        internalUnsafeAttackCombat(uid)
    }

    private suspend fun internalUnsafeAttackCombat(uid: Long) {
        val session = dao.getRaidSession(uid)
        if (session == null) {
            android.util.Log.e("COMBAT", "Combat state or raidSession is NULL for uid=$uid!")
            return
        }
        val player = dao.getPlayer(uid)
        if (player == null) {
            android.util.Log.e("COMBAT", "Player is NULL for uid=$uid!")
            return
        }
        if (session.current_enemy_id != null) {
            val cleanSession = if (session.current_anomaly_id != null) {
                val updated = session.copy(current_anomaly_id = null)
                dao.insertRaidSession(updated)
                updated
            } else session
            handleCombatTurn(uid, cleanSession, player, isGuarding = false)
        } else {
            android.util.Log.e("COMBAT", "Combat state or villain is NULL! current_enemy_id is null in attackCombat, performing emergency step recovery.")
            processStep(uid)
        }
    }

    suspend fun defendCombat(uid: Long) = dbMutex.withLock {
        internalUnsafeDefendCombat(uid)
    }

    private suspend fun internalUnsafeDefendCombat(uid: Long) {
        val session = dao.getRaidSession(uid)
        if (session == null || session.current_enemy_id == null) {
            android.util.Log.e("COMBAT", "defendCombat: Combat state or villain is NULL!")
            return
        }
        val player = dao.getPlayer(uid)
        if (player == null) {
            android.util.Log.e("COMBAT", "defendCombat: Player is NULL!")
            return
        }

        // Gain +25% Overdrive charge on guard
        val curCharge = getOverdriveCharge(uid)
        setOverdriveCharge(uid, curCharge + io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_GUARD)

        // Restore +8 EP
        val newEnergy = minOf(player.max_energy, player.energy + 8)
        dao.updatePlayer(player.copy(energy = newEnergy))

        log(uid, "🛡 [ЗАЩИТНАЯ СТОЙКА]: Нейро-барьер активен! Входящий урон снижен на 60% (+25% Овердрайв, +8 EP).", "info")
        _combatEventFlow.tryEmit(CombatVisualEvent(isDodge = false))

        handleCombatTurn(uid, session, player, isGuarding = true)
    }

    private suspend fun handleCombatTurn(uid: Long, session: RaidSession, player: Player, isGuarding: Boolean = false) {
        var currentSession = session
        val enemyId = session.current_enemy_id
        if (enemyId.isNullOrBlank()) {
            android.util.Log.e("COMBAT", "Combat state or villain is NULL! Performing emergency recovery.")
            val clean = session.copy(current_enemy_id = null, current_enemy_hp = 0, combat_turn = 0)
            dao.insertRaidSession(clean)
            return
        }

        val villainsStatic = io.eidos.zerolayer.data.GameData.VILLAINS
        var villain = villainsStatic.find { it.name == enemyId }
            ?: villainsStatic.find {
                val clean1 = it.name.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                val clean2 = enemyId.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                clean1.isNotEmpty() && clean2.isNotEmpty() && (clean1.contains(clean2) || clean2.contains(clean1))
            }
        
        if (villain == null) {
            android.util.Log.e("COMBAT", "Combat state or villain is NULL! Emergency fallback for enemyId='$enemyId'")
            villain = io.eidos.zerolayer.data.GameVillainData(
                id = 9999,
                name = enemyId,
                level = ((session.depth / 50) + 1).coerceAtLeast(1),
                hp = maxOf(25, session.current_enemy_hp),
                atk = 15,
                def = 5,
                xp = 50L,
                coin = 30L,
                description = "Искаженный фрагмент кода, затерянный в Слоях Нуля.",
                image = "monster_1"
            )
        }

        // If enemy HP in session is corrupted (<= 0) when entering turn, restore from villain max hp
        if (currentSession.current_enemy_hp <= 0) {
            android.util.Log.w("COMBAT", "Enemy HP in session was <= 0, initializing to ${villain.hp}")
            currentSession = currentSession.copy(current_enemy_hp = villain.hp)
            dao.insertRaidSession(currentSession)
        }

        val activeStats = getActiveStats(uid)

        val inventory = dao.getInventoryFlow(uid).first()
        val weaponItem = inventory.find { it.slot == "weapon" && it.is_equipped }
        val armorItem = inventory.find { it.slot == "armor" && it.is_equipped }
        val headItem = inventory.find { it.slot == "head" && it.is_equipped }

        val isCursedWeapon = weaponItem != null && getItemMetadata(weaponItem.item_id)?.rarity == "cursed"

        val activeSynergies = getActiveChipSynergies(uid)
        val hasRed2 = activeSynergies.any { it.id == "syn_red_2" }
        val hasRed4 = activeSynergies.any { it.id == "syn_red_4" }
        val hasGreen2 = activeSynergies.any { it.id == "syn_green_2" }
        val hasGreen4 = activeSynergies.any { it.id == "syn_green_4" }
        val hasBlue2 = activeSynergies.any { it.id == "syn_blue_2" }
        val hasBlue4 = activeSynergies.any { it.id == "syn_blue_4" }
        val hasDuoRedGreen = activeSynergies.any { it.id == "syn_duo_red_green" }
        val hasDuoRedBlue = activeSynergies.any { it.id == "syn_duo_red_blue" }
        val hasDuoGreenBlue = activeSynergies.any { it.id == "syn_duo_green_blue" }
        val hasCursedPact = activeSynergies.any { it.id == "syn_cursed_pact" }

        // Mutator Cyber-Vampirism: Guard posture costs 5 EP
        if (isGuarding && session.active_mutator == SectorMutator.CYBER_VAMPIRISM.id) {
            val costE = maxOf(0, player.energy - 5)
            dao.updatePlayer(player.copy(energy = costE))
            log(uid, "🩸 [КИБЕР-ВАМПИРИЗМ]: Защитная стойка потребовала -5 EP!", "info")
        }

        val nextTurn = session.combat_turn + 1
        val turnProcs = mutableListOf<EquipmentProcEvent>()

        val aiAction = runCatching {
            io.eidos.zerolayer.domain.combat.CombatEngine.evaluateMonsterAi(
                villainId = villain.id,
                combatTurn = nextTurn,
                villainAtk = villain.atk,
                villainCurrentHp = currentSession.current_enemy_hp
            )
        }.getOrElse { err ->
            android.util.Log.e("COMBAT", "evaluateMonsterAi failed, using fallback MonsterAiAction", err)
            io.eidos.zerolayer.domain.combat.CombatEngine.MonsterAiAction()
        }

        val syn = CombatSynergyFlags(
            hasRed2, hasRed4, hasGreen2, hasGreen4, hasBlue2, hasBlue4,
            hasDuoRedGreen, hasDuoRedBlue, hasDuoGreenBlue, hasCursedPact
        )
        val enemyIntent = runCatching {
            io.eidos.zerolayer.domain.combat.CombatEngine.predictEnemyIntent(
                villainId = villain.id,
                combatTurn = nextTurn,
                isStunned = stunnedEnemies[uid] == true
            )
        }.getOrElse { err ->
            android.util.Log.e("COMBAT", "predictEnemyIntent failed, using fallback ATTACK", err)
            io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntent(
                type = io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.ATTACK,
                title = "ОБЫЧНАЯ АТАКА",
                description = "Стандартная атака врага.",
                iconRes = io.eidos.zerolayer.R.drawable.ic_action_attack,
                damageMultiplier = 1.0f
            )
        }

        val st = CombatTurnState(currentSession, currentSession.current_enemy_hp)

        // --- Player Turn (Only if not in defensive guard posture) ---
        if (!isGuarding) {
            performPlayerAttackTurn(st, uid, session, player, villain, activeStats, weaponItem, headItem, aiAction, enemyIntent, syn, isCursedWeapon)
        }

        if (st.newEnemyHp <= 0) {
            resolveEnemyDefeat(st, uid, session, player, villain, weaponItem, headItem, syn)
        } else {
            performEnemyTurn(st, uid, session, player, villain, activeStats, weaponItem, armorItem, headItem, aiAction, enemyIntent, syn, nextTurn, isGuarding)
        }
    }

    suspend fun triggerOverdrive(uid: Long) = dbMutex.withLock {
        internalUnsafeTriggerOverdrive(uid)
    }

    private suspend fun internalUnsafeTriggerOverdrive(uid: Long) {
        val session = dao.getRaidSession(uid)
        if (session == null) {
            android.util.Log.e("COMBAT", "triggerOverdrive: RaidSession is NULL!")
            return
        }
        val player = dao.getPlayer(uid)
        if (player == null) {
            android.util.Log.e("COMBAT", "triggerOverdrive: Player is NULL!")
            return
        }
        val currentCharge = getOverdriveCharge(uid)
        if (currentCharge < io.eidos.zerolayer.domain.combat.CombatEngine.OVERDRIVE_MAX_CHARGE || session.current_enemy_id == null) {
            android.util.Log.w("COMBAT", "triggerOverdrive: Charge insufficient ($currentCharge/100) or no enemy (${session.current_enemy_id})")
            return
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
            isPlayerHit = false,
            textPopup = "💥 ОВЕРДРАЙВ -$overdriveDmg!",
            popupColor = "0xFFFF0055"
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
            dao.updatePlayer(player.copy(kills = player.kills + 1))
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
        val player = dao.getPlayer(uid)
        if (session.signal <= 0 || (player != null && player.hp <= 0)) {
            val inventory = dao.getInventoryFlow(uid).first()
            val aegisItem = inventory.find { it.item_id == "aegis" && it.quantity > 0 }
            if (aegisItem != null) {
                if (aegisItem.quantity > 1) {
                    dao.updateInventoryItem(aegisItem.copy(quantity = aegisItem.quantity - 1))
                } else {
                    dao.deleteInventoryItem(aegisItem)
                }
                if (player != null) {
                    dao.updatePlayer(player.copy(hp = 1))
                }
                dao.insertRaidSession(session.copy(signal = 1))
                log(uid, "🛡 [ЭГИДА БЕССМЕРТИЯ]: Смертельный урон заблокирован! Артефакт рассыпался в прах, восстановив 1 HP Сигнала.", "info")
                return
            }

            val headItem = inventory.find { it.slot == "head" && it.is_equipped }
            if (headItem?.item_id == "cyber_halo" && (0..100).random() < 20) {
                if (player != null) {
                    dao.updatePlayer(player.copy(hp = 1))
                }
                dao.insertRaidSession(session.copy(signal = 1))
                log(uid, "✨ [ГОЛОГРАФИЧЕСКИЙ НИМБ]: Священный протокол восстановил 1% Сигнала, предотвратив гибель!", "info")
                return
            }

            io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context).logRaidFailedAtAnomaly(
                session.current_anomaly_id ?: "signal_collapse",
                session.depth
            )
            log(uid, "💀 КРИТИЧЕСКИЙ СБОЙ: Нейро-связь разорвана. Экстренная эвакуация.", "error")

            val player = dao.getPlayer(uid)
            if (player != null) {
                // Break equipped items (Weapon, Armor, Head) by 10% EMP strike
                val equippedCombatItems = inventory.filter { it.is_equipped && it.slot in listOf("weapon", "armor", "head") }
                val brokenList = mutableListOf<String>()
                equippedCombatItems.forEach { eqItem ->
                    val newDur = maxOf(0f, eqItem.durability - 10f)
                    dao.updateInventoryItem(eqItem.copy(durability = newDur))
                    if (newDur <= 0f) {
                        val brokenName = getItemMetadata(eqItem.item_id)?.name ?: eqItem.item_id.uppercase()
                        brokenList.add(brokenName)
                        log(uid, "🚨 [CRITICAL ERROR: $brokenName СЛОМАН(О)]!", "error")
                    }
                }
                syncUserEquipmentToDb(uid)

                val deathMask = dao.getInventoryFlow(uid).first().find { it.item_id == "death_mask" && it.is_equipped } != null
                if (deathMask) {
                    log(uid, "💀 [Маска Мертвеца]: Получен критический урон! Проклятие маски поглотило остатки сигнала.", "error")
                }

                // Create a Grave at the depth of death (deduplicate existing grave at this depth)
                val hasGrave = session.buffer_coins > 0 || session.buffer_items.isNotEmpty()
                if (hasGrave) {
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
                    val owner = player.username ?: player.first_name ?: "Оператор"
                    log(uid, "[ЦЕЛОСТНОСТЬ УТРАЧЕНА]: Ваше цифровое тело осталось на глубине ${session.depth}м с ${session.buffer_coins} BC и предметами: [$cleanItems]. Дойдите до ${session.depth}м в следующем рейде, чтобы вернуть лут!", "error")
                    val alertMsg = RadioMessageEntity(
                        uid = uid,
                        sender = "СЕТЬ НУЛЕВОГО СЛОЯ",
                        title = "ПАДЕНИЕ ОПЕРАТОРА",
                        body = "Оператор $owner пал на глубине ${session.depth}м! Цифровая Могила зафиксирована в Бездне.",
                        timestamp = System.currentTimeMillis()
                    )
                    dao.insertRadioMessage(alertMsg)
                }

                // Reset overdrive
                setOverdriveCharge(uid, 0)

                dao.updatePlayer(player.copy(
                    max_depth = maxOf(player.max_depth, session.depth),
                    hp = player.max_hp,
                    energy = player.max_energy,
                    overdriveCharge = 0,
                    kills = maxOf(player.kills, player.kills + session.kills)
                ))

                val durationSec = ((System.currentTimeMillis() - session.start_time).coerceAtLeast(0L)) / 1000L
                deathReportFlow.value = DeathReport(
                    depth = session.depth,
                    lostCoins = session.buffer_coins,
                    lostXp = session.buffer_xp,
                    lostItems = session.buffer_items,
                    graveCreated = hasGrave,
                    brokenItems = brokenList,
                    durabilityPenaltyPercent = 10,
                    kills = session.kills,
                    riddlesSolved = session.riddles_solved,
                    durationSeconds = durationSec,
                    activeMutator = session.active_mutator
                )
            }
            dao.deleteRaidSession(uid)
        }
    }

    suspend fun endRaid(uid: Long) {
        val session = dao.getRaidSession(uid) ?: return
        val player = dao.getPlayer(uid) ?: return
        val now = System.currentTimeMillis()

        // Kamikaze protocol durability penalty if leaving before step 10
        val stepsTaken = session.depth / 50
        val equippedItems = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
        val hasKamikaze = equippedItems.any { it.item_id == "kamikaze_protocol" }
        if (hasKamikaze && stepsTaken < 10) {
            equippedItems.forEach { eqItem ->
                if (eqItem.slot in listOf("weapon", "armor", "head")) {
                    dao.updateInventoryItem(eqItem.copy(durability = maxOf(0f, eqItem.durability - 20f)))
                }
            }
            log(uid, "💥 [ПРОТОКОЛ КАМИКАДЗЕ]: Экстренный выход до 10-го шага вызвал перегрузку (-20% прочности экипировки)!", "error")
        }

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
        // NG+ prestige: each Singularity cycle grants +10% to all raid rewards
        val prestigeMult = 1.0f + (player.prestige_count * 0.10f)
        val calculatedXp = (session.buffer_xp * bonusXpMult * prestigeMult).toLong()

        // Holo Poverty limit check (max 500 BC extracted)
        val hasHoloPoverty = equippedItems.any { it.item_id == "holo_poverty" }
        var finalCoins = if (hasHoloPoverty) minOf(500L, session.buffer_coins) else session.buffer_coins
        if (hasHoloPoverty && session.buffer_coins > 500L) {
            log(uid, "🥋 [ГОЛОГРАММА НИЩЕТЫ]: Вынос валюты ограничен лимитом в 500 BC.", "info")
        }
        if (player.prestige_count > 0) {
            finalCoins = (finalCoins * prestigeMult).toLong()
        }

        val isPerfectRaid = session.signal >= player.max_hp && session.depth >= 10
        val newPerfectRaids = if (isPerfectRaid) player.perfect_raids + 1 else player.perfect_raids
        if (isPerfectRaid) {
            log(uid, "⚔️ [БЕЗУПРЕЧНЫЙ РЕЙД]: Экспедиция завершена без потери Сигнала! (+1 в зачет)", "heal")
        }

        val tempPlayer = player.copy(
            xp = player.xp + calculatedXp,
            biocoin = currentBiocoin + finalCoins,
            max_depth = maxOf(player.max_depth, session.depth),
            raids_done = player.raids_done + 1,
            perfect_raids = newPerfectRaids,
            hp = player.max_hp,
            energy = player.max_energy,
            state_version = player.state_version + 1
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
                // Deducts 250 BC, restores 100% energy, grants 1x abyssal_key. XP is strictly non-deductible!
                val costBc = minOf(250L, player.biocoin)
                dao.updatePlayer(player.copy(
                    biocoin = player.biocoin - costBc,
                    energy = player.max_energy
                ))
                val newBuffer = if (session.buffer_items.isEmpty()) "abyssal_key" else "${session.buffer_items},abyssal_key"
                dao.insertRaidSession(session.copy(
                    buffer_items = newBuffer,
                    next_event_type = "scan"
                ))
                log(uid, "🧠 [ДЕМОН МАКСВЕЛЛА]: Жертва принята (-$costBc BC). Энергия восстановлена на 100%, получен [Ключ Бездны]!", "heal")
            }
            "loot_gamble" -> {
                val hasEquip = session.buffer_items.split(",").any { it.isNotBlank() }
                if (session.buffer_coins < 250L && !hasEquip) {
                    log(uid, "❌ [ДЕМОН МАКСВЕЛЛА]: Требуется накопить минимум 250 BC или предмет лута в буфере!", "error")
                    return
                }
                val isWin = kotlin.random.Random.nextBoolean()
                if (isWin) {
                    val doubledCoins = session.buffer_coins * 2L
                    val doubledItems = if (session.buffer_items.isNotBlank()) {
                        "${session.buffer_items},${session.buffer_items}"
                    } else session.buffer_items
                    dao.insertRaidSession(session.copy(
                        buffer_coins = doubledCoins,
                        buffer_items = doubledItems,
                        next_event_type = "scan"
                    ))
                    log(uid, "🎰 [ДЕМОН МАКСВЕЛЛА: ПОБЕДА!]: Энтропия на вашей стороне! Лут и монеты буфера УДВОЕНЫ (+${session.buffer_coins} BC)!", "loot")
                } else {
                    val coinsToDeduct = kotlin.math.ceil(session.buffer_coins / 2.0).toLong()
                    val remainingCoins = maxOf(0L, session.buffer_coins - coinsToDeduct)
                    val itemsList = session.buffer_items.split(",").filter { it.isNotBlank() }
                    val itemsToDrop = kotlin.math.ceil(itemsList.size / 2.0).toInt()
                    val remainingItems = itemsList.drop(itemsToDrop).joinToString(",")
                    dao.insertRaidSession(session.copy(
                        buffer_coins = remainingCoins,
                        buffer_items = remainingItems,
                        next_event_type = "scan"
                    ))
                    log(uid, "💀 [ДЕМОН МАКСВЕЛЛА: ПРОИГРЫШ!]: Демон забрал 50% вынесенного: -$coinsToDeduct BC и -$itemsToDrop предметов!", "error")
                }
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
            log(uid, "[ТЕРМИНАЛ СВЯЗИ]: Получено новое входящее сообщение от Теневого Брокера!", "info")
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
            log(uid, "[ТЕРМИНАЛ СВЯЗИ]: Перехвачен сигнал бедствия из глубины Нулевого Слоя!", "info")
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
            log(uid, "[ТЕРМИНАЛ СВЯЗИ]: Начислена награда от Центрального Ядра EIDOS!", "loot")
        }

        // 4. Episodic series "Кассандра // Сигнатура 7-7-3": a continuing story
        // of a trapped operator, unlocked by depth milestones (was: 3 messages
        // per account lifetime, no episodic lore delivery)
        val cassandraSender = "Кассандра // Сигнатура 7-7-3"
        val cassandraEpisodes = listOf(
            Triple(200, "КАССАНДРА // EP.01 - ЗОНД", "Я слышу тебя через шум. Я - оператор Кассандра, застрявшая между Слоями с Первого Сброса. Мой аватар распадается, но сигнатура жива. Если дойдёшь до 400м - я передам первую часть архива Архитекторов."),
            Triple(400, "КАССАНДРА // EP.02 - АРХИВ", "Архив 1/3: Эйдос не симуляция. Это перенос сознания, который пошёл не туда. Тела спящих на поверхности - контейнеры. Архитекторы знали о Глитче ДО запуска. 600м - следующая передача."),
            Triple(600, "КАССАНДРА // EP.03 - ЭНТРОПИЯ", "Архив 2/3: Энтропия - не баг. Это протокол очистки контейнеров, чей разум сопротивлялся переносу. Скверна - их крик. Не слушай её, если встретишь. На 800м я покажу лазейку мимо Ищеек."),
            Triple(800, "КАССАНДРА // EP.04 - ЛАЗЕЙКА", "Лазейка передана: слепые зоны между волнами Ищеек. Используй Ключи Бездны на вратах - Хранители видят меньше, чем думает Ядро. Дальше 1200м начинается чужая территория. Будь осторожен."),
            Triple(1200, "КАССАНДРА // EP.05 - БРОКЕР", "Осторожно: Теневой Брокер торгуется шкурами операторов. Его 'пакеты данных' прошиты трекерами. Я видела, кем он был до Сброса. Это был один из Архитекторов. Продолжение на 1600м."),
            Triple(1600, "КАССАНДРА // EP.06 - ДЕМОН", "Архив 3/3: Демон Максвелла - не сущность. Это экзекьютор протокола Энтропии, и он выполняет команду, отданную в 2029 году. Кем-то из нас. Кассандра больше не уверена, что она - исключение. Ищи Терминал."),
            Triple(2000, "КАССАНДРА // EP.07 - ТЕРМИНАЛ", "Терминал Сингулярности реален. Я была у него. Я не смогла выбрать. Сброс стирает всё, Вознесение растворяет всё. Но есть третий путь - Бездна сама предложит свою цену. Решай сама. На 3000м - последняя передача."),
            Triple(3000, "КАССАНДРА // EP.08 - МОЛЧАНИЕ", "Это моя последняя передача. Сигнатура 7-7-3 рассеивается. Если найдёшь Терминал - помни: любой финал лучше, чем застрять между Слоями, как я. Извлеки меня хотя бы из истории. Конец связи... и спасибо.")
        )
        cassandraEpisodes.forEach { (depthReq, title, body) ->
            if (player.max_depth >= depthReq && existing.none { it.title == title }) {
                dao.insertRadioMessage(
                    RadioMessageEntity(
                        uid = uid,
                        sender = cassandraSender,
                        title = title,
                        body = body,
                        rewardCoins = 250L,
                        rewardXp = 120L,
                        isClaimed = false
                    )
                )
                log(uid, "[ТЕРМИНАЛ СВЯЗИ]: Перехвачена эпизодическая передача: «$title»!", "info")
            }
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

    suspend fun claimChestLoot(uid: Long, isCursed: Boolean): Triple<Long, Long, List<String>> = dbMutex.withLock {
        val session = dao.getRaidSession(uid) ?: return Triple(0L, 0L, emptyList())
        val depth = session.depth
        val isDoubleDrop = session.active_mutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_DOUBLE_DROP
        val baseCoins = if (isCursed) (500L..1200L).random() + (depth * 2L) else (150L..350L).random() + (depth / 4L)
        val overchargeTier = _overchargeTierFlow.value
        val overchargeMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(overchargeTier)
        var coinReward = (baseCoins * overchargeMult.toDouble()).toLong()
        if (isDoubleDrop) coinReward *= 2

        val xpReward = if (isCursed) (300L..600L).random() else (100L..200L).random()
        val items = mutableListOf<String>()
        if (isCursed) {
            val cursedPool = listOf("relic_vampire", "death_mask", "karma_inversion", "quantum_blade", "oblivion_chip")
            items.add(cursedPool.random())
        } else {
            if (kotlin.random.Random.nextInt(100) < 50) {
                val lootPool = listOf("encrypted_cache", "battery", "eidos_shard", "data_spike")
                items.add(lootPool.random())
            }
        }

        var newBufferItems = session.buffer_items
        items.forEach { foundId ->
            newBufferItems = if (newBufferItems.isEmpty()) foundId else "$newBufferItems,$foundId"
        }

        dao.insertRaidSession(session.copy(
            buffer_coins = session.buffer_coins + coinReward,
            buffer_xp = session.buffer_xp + xpReward,
            buffer_items = newBufferItems
        ))

        val itemsNote = if (items.isNotEmpty()) " и предметы: [${items.joinToString(", ")}]" else ""
        val prefix = if (isCursed) "👁️ [ПРОКЛЯТЫЙ ТАЙНИК ВСКРЫТ]" else "🔓 [ТАЙНИК ВЗЛОМАН]"
        log(uid, "$prefix: Получено +$coinReward BC, +$xpReward XP$itemsNote!", "loot")

        Triple(coinReward, xpReward, items)
    }

    suspend fun scanSector(uid: Long) = dbMutex.withLock {
        internalUnsafeScanSector(uid)
    }

    private suspend fun internalUnsafeScanSector(uid: Long) {
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
                val lootMeta = if ((0..100).random() < 50) rollNormalLoot(legendaryBoost = session.active_mutator == SectorMutator.GLITCH_STORM.id) else null
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

    suspend fun useActiveAbility(uid: Long) = dbMutex.withLock {
        internalUnsafeUseActiveAbility(uid)
    }

    private suspend fun internalUnsafeUseActiveAbility(uid: Long) {
        val player = dao.getPlayer(uid)
        if (player == null) {
            android.util.Log.e("COMBAT", "useActiveAbility: Player is NULL for uid=$uid!")
            return
        }
        val session = dao.getRaidSession(uid)
        if (session == null) {
            android.util.Log.e("COMBAT", "useActiveAbility: RaidSession is NULL for uid=$uid!")
            return
        }
        val enemyId = session.current_enemy_id
        if (enemyId.isNullOrBlank()) {
            android.util.Log.e("COMBAT", "useActiveAbility: Combat state or enemyId is NULL!")
            return
        }

        // Tactical ability energy cost: 10 EP (or 8% HP emergency overload if low EP)
        // ANTIGRAVITY mutator: skills and Overdrive cost 0 EP
        val isAntigravity = session.active_mutator == SectorMutator.ANTIGRAVITY.id
        val abilityCost = if (isAntigravity) 0 else 10
        var workingPlayer = player
        if (isAntigravity) {
            log(uid, "🪐 [АНТИГРАВИТАЦИЯ]: Навык активирован в нулевой гравитации - бесплатно (0 EP)!", "info")
        } else if (player.energy >= abilityCost) {
            val newEnergy = player.energy - abilityCost
            workingPlayer = player.copy(energy = newEnergy)
            dao.updatePlayer(workingPlayer)
        } else {
            // Emergency overload: drains 8% Max HP when energy is exhausted
            val bloodCost = maxOf(1, (player.max_hp * 0.08f).toInt())
            val newHp = maxOf(0, player.hp - bloodCost)
            workingPlayer = player.copy(hp = newHp, energy = 0)
            dao.updatePlayer(workingPlayer)
            dao.insertRaidSession(session.copy(signal = newHp))
            log(uid, "🩸 [КРОВАВЫЙ НАВЫК]: Энергия исчерпана! Списано -$bloodCost HP (8%) для форсированного удара!", "error")
            if (newHp <= 0) {
                checkDeath(uid)
                return
            }
        }

        val villainsStatic = GameData.VILLAINS
        val villain = villainsStatic.find { it.name == enemyId }
            ?: villainsStatic.find {
                val clean1 = it.name.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                val clean2 = enemyId.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                clean1.isNotEmpty() && clean2.isNotEmpty() && (clean1.contains(clean2) || clean2.contains(clean1))
            }
            ?: GameVillainData(
                id = 9999,
                name = enemyId,
                level = (session.depth / 50) + 1,
                hp = maxOf(10, session.current_enemy_hp),
                atk = 20,
                def = 5,
                xp = 60L + session.depth,
                coin = 40L + (session.depth / 2),
                description = "Враг Нулевого Слоя",
                image = "monster_1"
            )

        val activeStats = getActiveStats(uid)
        val baseAtk = maxOf(12, activeStats.attack)

        var extraDamage = 0
        var lootedCoins = 0
        var healSignal = 0
        var abilityLog = ""

        when (player.faction) {
            "МАТЕРИЯ" -> {
                extraDamage = (baseAtk * 2.2f).toInt()
                if (matterStealUsedInCombat[uid] != true) {
                    lootedCoins = (20..55).random()
                    matterStealUsedInCombat[uid] = true
                    abilityLog = "⚡ [ЗОЛОТОЙ ИМПУЛЬС // МАТЕРИЯ]: Нанесено $extraDamage урона! Дренировано +$lootedCoins BC из ядра цели!"
                } else {
                    lootedCoins = 0
                    abilityLog = "⚡ [ЗОЛОТОЙ ИМПУЛЬС // МАТЕРИЯ]: Нанесено $extraDamage урона! (Ядро противника уже опустошено)"
                }
            }
            "РАЗУМ" -> {
                extraDamage = (baseAtk * 1.6f).toInt()
                healSignal = 25
                abilityLog = "⚡ [НЕЙРО-ЩИТ // РАЗУМ]: Нанесено $extraDamage урона! Целостность Сигнала восстановлена на +$healSignal%!"
            }
            "ТЕХНО", "Технократы" -> {
                extraDamage = (baseAtk * 2.8f).toInt()
                abilityLog = "⚡ [КВАНТОВЫЙ ВЗРЫВ // ТЕХНО]: Критический импульс взлома шины! Нанесено $extraDamage урона цели!"
            }
            "АРХИТЕКТОРЫ" -> {
                extraDamage = (baseAtk * 3.2f).toInt()
                abilityLog = "⚡ [ПРОТОКОЛ АРХИТЕКТОРОВ]: Удаление структуры цели из реестра! Нанесено $extraDamage урона!"
            }
            else -> {
                extraDamage = (baseAtk * 2.0f).toInt()
                abilityLog = "⚡ [ТАКТИЧЕСКИЙ СПЕЦУДАР]: Прорыв защиты цели на $extraDamage урона!"
            }
        }

        val enemyIntent = io.eidos.zerolayer.domain.combat.CombatEngine.predictEnemyIntent(villain.id, session.combat_turn, isStunned = stunnedEnemies[uid] == true)
        if (enemyIntent.type == io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.SHIELD) {
            extraDamage = (extraDamage * 1.5f).toInt()
            log(uid, "💥 [ПРОБИТИЕ БАРЬЕРА]: Квантовый щит цели сокрушен тактическим навыком (+50% DMG)!", "combat")
        }

        // Trigger visual hit event
        _combatEventFlow.tryEmit(CombatVisualEvent(
            damage = extraDamage,
            isCrit = true,
            isOverdrive = false,
            isDodge = false,
            isPlayerHit = false
        ))

        // Gain overdrive charge
        val curCharge = getOverdriveCharge(uid)
        setOverdriveCharge(uid, curCharge + 35)

        val newEnemyHp = maxOf(0, session.current_enemy_hp - extraDamage)
        val newSig = minOf(workingPlayer.max_hp, session.signal + healSignal)
        workingPlayer = workingPlayer.copy(hp = newSig)
        dao.updatePlayer(workingPlayer)
        log(uid, abilityLog, "combat")

        if (newEnemyHp <= 0) {
            log(uid, "🏆 [ЦЕЛЬ УНИЧТОЖЕНА]: ${villain.name} стерт тактической способностью!", "loot")
            recordEnemyKill(villain.name)
            val updatedEnergy = minOf(workingPlayer.max_energy, workingPlayer.energy + 5)
            dao.updatePlayer(workingPlayer.copy(energy = updatedEnergy))
            log(uid, "⚡ [ТАКТИЧЕСКИЙ РЕЗОНАНС]: Уничтожение врага вернуло +5 EP!", "info")
            val updatedSessionDefeated = session.copy(
                current_enemy_id = null,
                current_enemy_hp = 0,
                signal = newSig,
                buffer_xp = session.buffer_xp + villain.xp,
                buffer_coins = session.buffer_coins + villain.coin + lootedCoins,
                kills = session.kills + 1,
                combat_turn = 0,
                damage_buffer = 0
            )
            dao.insertRaidSession(updatedSessionDefeated)
        } else {
            val updatedSession = session.copy(
                current_enemy_hp = newEnemyHp,
                signal = newSig,
                buffer_coins = session.buffer_coins + lootedCoins,
                combat_turn = session.combat_turn + 1
            )
            dao.insertRaidSession(updatedSession)
        }
    }

    suspend fun salvageBufferItemForEnergy(uid: Long, itemIndex: Int) = dbMutex.withLock {
        val session = dao.getRaidSession(uid) ?: return@withLock
        val player = dao.getPlayer(uid) ?: return@withLock
        val items = session.buffer_items.split(",").map { it.trim() }.filter { it.isNotBlank() }.toMutableList()
        if (itemIndex in items.indices) {
            val removed = items.removeAt(itemIndex)
            val newItemsStr = items.joinToString(",")
            val newEnergy = minOf(player.max_energy, player.energy + 15)
            dao.updatePlayer(player.copy(energy = newEnergy))
            dao.insertRaidSession(session.copy(buffer_items = newItemsStr))
            val meta = getItemMetadata(removed)
            val name = meta?.name ?: removed.uppercase()
            log(uid, "⚡ [МОЛЕКУЛЯРНОЕ РАСЩЕПЛЕНИЕ]: Предмет [$name] расщеплен на +15 EP!", "info")
        }
    }

    suspend fun fleeCombat(uid: Long) = dbMutex.withLock {
        internalUnsafeFleeCombat(uid)
    }

    private suspend fun internalUnsafeFleeCombat(uid: Long) {
        val session = dao.getRaidSession(uid)
        if (session == null) {
            android.util.Log.e("COMBAT", "fleeCombat: RaidSession is NULL!")
            return
        }
        val player = dao.getPlayer(uid)
        if (player == null) {
            android.util.Log.e("COMBAT", "fleeCombat: Player is NULL!")
            return
        }
        val enemyName = session.current_enemy_id
        if (enemyName == null) {
            android.util.Log.e("COMBAT", "fleeCombat: Combat state or enemyName is NULL!")
            return
        }

        // 75% escape probability, 100% with tactical fog
        val roll = (1..100).random()
        if (roll <= 75) {
            val updatedSession = session.copy(
                current_enemy_id = null,
                current_enemy_hp = 0,
                active_aggro = maxOf(0, session.active_aggro - 1)
            )
            dao.insertRaidSession(updatedSession)
            log(uid, "🏃 [ТАКТИЧЕСКИЙ ОТХОД]: Вы успешно оторвались от преследования $enemyName и отступили в защищенный сектор!", "info")
        } else {
            val villain = GameData.VILLAINS.find { it.name == enemyName }
            val enemyAtk = villain?.atk ?: 25
            val playerDef = player.defense + (player.level * 2)
            val dmg = maxOf(6, enemyAtk - (playerDef / 3))
            val newSignal = maxOf(0, session.signal - dmg)
            val newHp = maxOf(0, player.hp - dmg)

            val updatedPlayer = player.copy(hp = newHp)
            val updatedSession = session.copy(signal = newSignal)
            dao.updatePlayer(updatedPlayer)
            dao.insertRaidSession(updatedSession)
            log(uid, "⚠️ [НЕУДАЧНЫЙ ПОБЕГ]: $enemyName перехватил вектор отхода и нанес -$dmg урона в спину!", "error")

            if (newSignal <= 0 || newHp <= 0) {
                checkDeath(uid)
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
            // Out-of-raid decryption: no session mutator applies here
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

        log(
            uid,
            "🧬 [СИНХРОНИЗАЦИЯ_УСПЕШНА]: Извлечён фрагмент АРХИВА АРХИТЕКТОРОВ (записи о Биоэпохе, до 2029):\n$selectedProtocolText\n" +
                "— Расшифровка ЕВА-09: это исследовательские заметки Архитекторов о носителях из плоти. Их доподлинная психология была ключом к помехоустойчивости сигнала.",
            "info"
        )
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
        // Discipline bonus: +5% BC on top for a clean extraction (safe path has
        // no outside-bot risk, the normal endRaid keeps that risk but no tax)
        val disciplineBonus = (rawCoins * 0.05).toLong()
        val rawFinalCoins = maxOf(0L, rawCoins - extractionTax + disciplineBonus)
        // NG+ prestige: +10% per Singularity cycle
        val prestigeMultSafe = 1.0f + (player.prestige_count * 0.10f)
        val finalCoins = (rawFinalCoins * prestigeMultSafe).toLong()

        val bonusXpMult = if (player.is_premium) 1.5f else 1.0f
        // NG+ prestige: each Singularity cycle grants +10% to all raid rewards
        val prestigeMult = 1.0f + (player.prestige_count * 0.10f)
        val calculatedXp = (session.buffer_xp * bonusXpMult * prestigeMult).toLong()

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

        val isPerfectRaid = session.signal >= player.max_hp && session.depth >= 10
        val newPerfectRaids = if (isPerfectRaid) player.perfect_raids + 1 else player.perfect_raids
        if (isPerfectRaid) {
            log(uid, "⚔️ [БЕЗУПРЕЧНЫЙ РЕЙД]: Экспедиция завершена без потери Сигнала! (+1 в зачет)", "heal")
        }

        val tempPlayer = player.copy(
            xp = player.xp + calculatedXp,
            biocoin = player.biocoin + finalCoins,
            max_depth = maxOf(player.max_depth, session.depth),
            raids_done = player.raids_done + 1,
            perfect_raids = newPerfectRaids,
            hp = player.max_hp,
            energy = player.max_energy,
            kills = maxOf(player.kills, player.kills + session.kills),
            state_version = player.state_version + 1
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
        log(
            uid,
            "📡 [БЕЗОПАСНАЯ ЭВАКУАЦИЯ]: Комиссия шлюза (${ZeroLayerEconomy.SAFE_EXTRACTION_TAX_PERCENT}%): -$extractionTax BC. " +
                "Надбавка за дисциплину: +$disciplineBonus BC. Зачислено чистой выручки: +$finalCoins BC, +$calculatedXp XP.",
            "info"
        )
        
        return Triple(extractedItems, finalCoins, leveledUp)
    }

    suspend fun rerollChipModifiers(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeRerollChipModifiers(uid, item)
    }

    private suspend fun internalUnsafeRerollChipModifiers(uid: Long, item: InventoryItem) {
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
            val hasEnough = internalUnsafeDeductShards(uid, shardCost)
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
    suspend fun applyDataSlicer(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeApplyDataSlicer(uid, item)
    }

    private suspend fun internalUnsafeApplyDataSlicer(uid: Long, item: InventoryItem) {
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

    suspend fun applyQuantumTuner(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeApplyQuantumTuner(uid, item)
    }

    private suspend fun internalUnsafeApplyQuantumTuner(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 500L
        val costShards = 1

        if (player.biocoin < costBc) {
            log(uid, "❌ [КВАНТОВЫЙ КАЛИБРАТОР]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = internalUnsafeDeductShards(uid, costShards)
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

    suspend fun applySocketPuncher(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeApplySocketPuncher(uid, item)
    }

    private suspend fun internalUnsafeApplySocketPuncher(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 300L
        val costShards = 1

        if (player.biocoin < costBc) {
            log(uid, "❌ [ПРОБОЙНИК ГНЕЗД]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = internalUnsafeDeductShards(uid, costShards)
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

    suspend fun applyChromaticInjector(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeApplyChromaticInjector(uid, item)
    }

    private suspend fun internalUnsafeApplyChromaticInjector(uid: Long, item: InventoryItem) {
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

    suspend fun applyVaalCorruption(uid: Long, item: InventoryItem) = dbMutex.withLock {
        internalUnsafeApplyVaalCorruption(uid, item)
    }

    private suspend fun internalUnsafeApplyVaalCorruption(uid: Long, item: InventoryItem) {
        val player = dao.getPlayer(uid) ?: return
        val costBc = 1000L
        val costShards = 2

        if (player.biocoin < costBc) {
            log(uid, "❌ [СКВЕРНА НЕЙРОСЕТИ]: Требуется $costBc BC.", "error")
            return
        }
        val hasShards = internalUnsafeDeductShards(uid, costShards)
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

    suspend fun insertChipToEquipment(uid: Long, item: InventoryItem, socketIndex: Int, chip: DataChip) = dbMutex.withLock {
        internalUnsafeInsertChipToEquipment(uid, item, socketIndex, chip)
    }

    private suspend fun internalUnsafeInsertChipToEquipment(uid: Long, item: InventoryItem, socketIndex: Int, chip: DataChip) {
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

    suspend fun removeChipFromEquipment(uid: Long, item: InventoryItem, socketIndex: Int) = dbMutex.withLock {
        internalUnsafeRemoveChipFromEquipment(uid, item, socketIndex)
    }

    private suspend fun internalUnsafeRemoveChipFromEquipment(uid: Long, item: InventoryItem, socketIndex: Int) {
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

    suspend fun searchPvpTarget(uid: Long): Boolean {
        val player = dao.getPlayer(uid) ?: return false
        if (player.level < PvpEngine.MIN_PVP_LEVEL) {
            log(uid, "🔒 [СЕТЕВАЯ ВОЙНА]: Доступ запрещен! Требуется 4 уровень Ядра.", "error")
            return false
        }
        if (player.biocoin < 50L) {
            log(uid, "❌ [СКАНИРОВАНИЕ СЕТИ]: Недостаточно BioCoin (требуется 50 BC)!", "error")
            return false
        }
        dao.updatePlayer(player.copy(biocoin = player.biocoin - 50L))
        log(uid, "📡 [СКАНИРОВАНИЕ СЕТИ]: Списано 50 BC. Обнаружены новые уязвимые узлы!", "info")
        return true
    }

    suspend fun executePvpRaid(
        attackerUid: Long,
        targetPlayer: SupabasePlayer,
        attackerPrograms: List<PvpProgram>,
        isRevenge: Boolean = false
    ): PvpMatchResult {
        val attacker = dao.getPlayer(attackerUid) ?: throw IllegalStateException("Player not found")
        
        if (attacker.level < PvpEngine.MIN_PVP_LEVEL) {
            log(attackerUid, "🔒 [СЕТЕВАЯ ВОЙНА]: Доступ запрещен! Требуется 4 уровень Ядра.", "error")
            throw IllegalStateException("Сетевая Война доступна строго с 4 уровня!")
        }

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
            val updatedAttacker = attacker.copy(
                biocoin = maxOf(0, attacker.biocoin - matchResult.coinsLost),
                losses_pvp = attacker.losses_pvp + 1,
                installed_hardware = updatedHw
            )
            dao.updatePlayer(updatedAttacker)
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

    // Аутентификация вынесена в AuthRepository. Передаём ту же обёртку dao
    // (автоинкремент state_version при записи Player) и ТОТ ЖЕ экземпляр
    // dbMutex. ВАЖНО: Kotlin Mutex нереентерабельный, поэтому AuthRepository
    // никогда не должен вызывать публичные методы GameRepository, берущие
    // dbMutex. Ссылки на getActiveUid() и log() безопасны: они мьютекс
    // не захватывают.
    val authRepository = AuthRepository(
        context = context,
        dao = dao,
        dbMutex = dbMutex,
        authStore = authStore,
        activeUidProvider = { getActiveUid() },
        logProvider = { uid, message, type -> log(uid, message, type) }
    )

    fun getAuthSession(): AuthSession = authRepository.getAuthSession()

    fun isInventoryInitialized(uid: Long): Boolean = authRepository.isInventoryInitialized(uid)
    fun setInventoryInitialized(uid: Long, initialized: Boolean = true) = authRepository.setInventoryInitialized(uid, initialized)

    suspend fun registerOperator(username: String, password: String, targetUid: Long = 0L): AuthResult =
        authRepository.registerOperator(username, password, targetUid)

    suspend fun loginOperator(username: String, password: String, targetUid: Long = 0L): AuthResult =
        authRepository.loginOperator(username, password, targetUid)

    suspend fun logoutOperator(): Boolean = authRepository.logoutOperator()

    suspend fun pushPlayerToSupabase(uid: Long, customDeviceId: String? = null, customUsername: String? = null): Boolean =
        authRepository.pushPlayerToSupabase(uid, customDeviceId, customUsername)

// Shared mutable state for one combat turn, split across helper functions
// (the original single method exceeded the JVM 64KB method limit).
private class CombatTurnState(
    var currentSession: RaidSession,
    var newEnemyHp: Int,
    val turnProcs: MutableList<EquipmentProcEvent> = mutableListOf()
)

private data class CombatSynergyFlags(
    val hasRed2: Boolean,
    val hasRed4: Boolean,
    val hasGreen2: Boolean,
    val hasGreen4: Boolean,
    val hasBlue2: Boolean,
    val hasBlue4: Boolean,
    val hasDuoRedGreen: Boolean,
    val hasDuoRedBlue: Boolean,
    val hasDuoGreenBlue: Boolean,
    val hasCursedPact: Boolean
)

    /**
     * Player attack portion of a combat turn (extracted from handleCombatTurn:
     * the original single method exceeded the JVM 64KB method limit).
     * Mechanical move, no logic changes.
     */
    private suspend fun performPlayerAttackTurn(
        st: CombatTurnState,
        uid: Long,
        session: RaidSession,
        player: Player,
        villain: GameVillainData,
        activeStats: PlayerStats,
        weaponItem: InventoryItem?,
        headItem: InventoryItem?,
        aiAction: io.eidos.zerolayer.domain.combat.CombatEngine.MonsterAiAction,
        enemyIntent: io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntent,
        syn: CombatSynergyFlags,
        isCursedWeapon: Boolean
    ) {
        if (aiAction.isPhaseEvading) {
            log(uid, aiAction.logMessage ?: "Враг уклонился от физического удара!", "info")
            _combatEventFlow.tryEmit(CombatVisualEvent(isDodge = true, textPopup = "💨 УКЛОНЕНИЕ!", popupColor = "0xFF00FFCC", triggeredProcs = st.turnProcs.toList()))
        } else {
            val isWeaponBroken = weaponItem != null && weaponItem.durability <= 0f
            val weaponMultiplier = if (weaponItem != null && weaponItem.durability > 0f) {
                getItemMetadata(weaponItem.item_id)?.multiplier ?: 1.0f
            } else {
                1.0f
            }

            val effectiveEnemyDef = villain.def + aiAction.selfDefBonus
            var baseDamage = if (isWeaponBroken) {
                log(uid, "🚨 [CRITICAL ERROR: ОРУЖИЕ СЛОМАНО]: Урон снижен до базовых 5 ATK!", "error")
                5
            } else {
                io.eidos.zerolayer.domain.combat.CombatEngine.calculateBasePlayerDamage(activeStats.attack, weaponMultiplier, effectiveEnemyDef)
            }

            // Synergy 4 Red: Titan's Rage (damage scales up to +100% on low HP)
            if (syn.hasRed4) {
                val missingHpRatio = (1.0f - (player.hp.toFloat() / maxOf(1, player.max_hp))).coerceIn(0f, 1f)
                baseDamage = (baseDamage * (1.0f + missingHpRatio)).toInt()
                st.turnProcs.add(EquipmentProcEvent("syn_red_4", "🔥 ЯРОСТЬ ТИТАНА: +${(missingHpRatio * 100).toInt()}% DMG", ProcColorType.CURSED_RED))
            }

            // Cursed weapon credit_slicer logic
            if (weaponItem?.item_id == "credit_slicer") {
                if (player.biocoin > 0) {
                    val burned = minOf(250L, maxOf(1L, (player.biocoin * 0.01).toLong()))
                    dao.updatePlayer(player.copy(biocoin = player.biocoin - burned))
                    val bonusAtk = (burned * 1.5).toInt()
                    baseDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateBasePlayerDamage(activeStats.attack + bonusAtk, weaponMultiplier, effectiveEnemyDef)
                    log(uid, "💸 [Кредитный Резак]: Сожжено -$burned BC для форсированного удара (+$bonusAtk ATK)!", "combat")
                    st.turnProcs.add(EquipmentProcEvent("credit_slicer", "💳 РЕЗАК КРЕДИТОВ: -$burned BC [+$bonusAtk ATK]", ProcColorType.GOLD_CRIT))
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
            
            // Synergy 4 Green: Shadow Dance guaranteed crit check
            val isGuaranteedCrit = syn.hasGreen4 && shadowDanceGuaranteedCrit[uid] == true
            if (isGuaranteedCrit) {
                shadowDanceGuaranteedCrit[uid] = false
                st.turnProcs.add(EquipmentProcEvent("syn_green_4", "🥷 ТАНЕЦ ТЕНЕЙ: 100% КРИТ!", ProcColorType.GOLD_CRIT))
            }
            val isCrit = isGuaranteedCrit || ((0..100).random() < (finalCritChance + maxwellCritBonus + warpCritBonus))

            val hasGlitchBerserk = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isBuffActive(player, io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_GLITCH_BERSERK)
            var finalPlayerDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateFinalPlayerDamage(baseDamage, isCrit, hasGlitchBerserk)

            // Synergy 2 Blue: Superconductor ignores shield
            if (enemyIntent.type == io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.SHIELD) {
                if (syn.hasBlue2) {
                    log(uid, "⚡ [СВЕРХПРОВОДНИК]: Энерго-щит противника пробит без потери урона!", "combat")
                    st.turnProcs.add(EquipmentProcEvent("syn_blue_2", "⚡ СВЕРХПРОВОДНИК: ПРОБИТИЕ ЩИТА!", ProcColorType.SHIELD_CYAN))
                } else {
                    finalPlayerDamage = maxOf(1, (finalPlayerDamage * 0.20f).toInt())
                    log(uid, "🛡 [КВАНТОВЫЙ ЩИТ]: Энерго-щит врага поглотил 80% физ. урона (-$finalPlayerDamage)!", "combat")
                }
            }
            if ((batteryOverclockTurns[uid] ?: 0) > 0) {
                finalPlayerDamage = (finalPlayerDamage * 1.15f).toInt()
                batteryOverclockTurns[uid] = (batteryOverclockTurns[uid] ?: 1) - 1
                log(uid, "⚡ [ПЕРЕГРУЗКА БАТАРЕИ]: +15% урона от энерго-ячейки!", "info")
            }

            // Gain Overdrive Charge on Player Attack (Neuro Overload doubles it)
            val currentCharge = getOverdriveCharge(uid)
            val baseChargeGain = if (isCrit) io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_CRIT_HIT else io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_NORMAL_ATTACK
            val chargeGain = if (session.active_mutator == SectorMutator.NEURO_OVERLOAD.id) baseChargeGain * 2 else baseChargeGain
            val nextCharge = currentCharge + chargeGain
            setOverdriveCharge(uid, nextCharge)

            // Blue 2: Superconductor stuns on 100% overdrive
            if (syn.hasBlue2 && nextCharge >= 100) {
                stunnedEnemies[uid] = true
                log(uid, "⚡ [СВЕРХПРОВОДНИК]: 100% Овердрайв вызывает ЭМ-импульс! Враг оглушен на 1 ход!", "combat")
                st.turnProcs.add(EquipmentProcEvent("syn_blue_2", "⚡ СВЕРХПРОВОДНИК: ЭМ-ОГЛУШЕНИЕ!", ProcColorType.SHIELD_CYAN))
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

            st.newEnemyHp = maxOf(0, session.current_enemy_hp - finalPlayerDamage)
            val critTag = if (isCrit) " [CRITICAL_HIT]" else ""
            log(uid, "НЕЙРО-ВСПЛЕСК: -$finalPlayerDamage Сигнала у ${villain.name}$critTag.", "combat")

            // Core Guardian reflection
            if (villain.id == 398 && finalPlayerDamage > 0) {
                val reflected = maxOf(1, (finalPlayerDamage * 0.15f).toInt())
                val curSig = maxOf(0, session.signal - reflected)
                dao.insertRaidSession(session.copy(signal = curSig))
                log(uid, "🛡 [Страж Ядра]: Отражено -$reflected урона в оператора!", "error")
            }

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
                st.turnProcs.add(EquipmentProcEvent("overclock_crown", "⚡ ВЕНЕЦ РАЗГОНА: x2 КРИТ [-2% HP]", ProcColorType.CURSED_RED))
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
                st.turnProcs.add(EquipmentProcEvent("relic_vampire", "🩸 КОРОНА КРОВИ: +2% (+$healSignal HP) СИГНАЛА", ProcColorType.HEAL_NEON))
            }
            if (player.skill_berserk_3 == 1) {
                val heal = maxOf(1, (finalPlayerDamage * 0.05).toInt())
                dao.updatePlayer(player.copy(hp = minOf(player.max_hp, player.hp + heal)))
                log(uid, "🧛 [Вампиризм]: Восстановлено +$heal Сигнала.", "info")
            }

            // Duo Red+Green (Кровавый Оверклок): 15% vampirism on crits
            if (syn.hasDuoRedGreen && isCrit) {
                val vampHeal = maxOf(1, (finalPlayerDamage * 0.15f).toInt())
                val curP = dao.getPlayer(uid) ?: player
                dao.updatePlayer(curP.copy(hp = minOf(curP.max_hp, curP.hp + vampHeal)))
                log(uid, "🩸 [КРОВАВЫЙ ОВЕРКЛОК]: Крит восстановил +$vampHeal HP (15%)!", "heal")
                st.turnProcs.add(EquipmentProcEvent("syn_duo_red_green", "🩸 КРОВАВЫЙ ОВЕРКЛОК: +$vampHeal HP", ProcColorType.HEAL_NEON))
            }

            // Mutator Cyber-Vampirism (+25% damage healed)
            if (session.active_mutator == SectorMutator.CYBER_VAMPIRISM.id) {
                val vamp = maxOf(1, (finalPlayerDamage * 0.25f).toInt())
                val curP = dao.getPlayer(uid) ?: player
                dao.updatePlayer(curP.copy(hp = minOf(curP.max_hp, curP.hp + vamp)))
                log(uid, "🩸 [КИБЕР-ВАМПИРИЗМ]: Поглощено +$vamp HP!", "heal")
            }

            // Mutator Gold Rush (+20..40 BC per hit)
            if (session.active_mutator == SectorMutator.GOLD_RUSH.id) {
                val rushGold = (20..40).random()
                st.currentSession = st.currentSession.copy(buffer_coins = st.currentSession.buffer_coins + rushGold)
                log(uid, "🪙 [ЗОЛОТАЯ ЛИХОРАДКА]: Удар выбил +$rushGold BC!", "loot")
            }

            // Emit combat visual event for player hit
            val playerPopupText = if (isCrit) "⚡ КРИТ -$finalPlayerDamage!" else "-$finalPlayerDamage"
            val playerPopupColor = if (isCrit) "0xFFFFD700" else "0xFFFFEEEE"
            _combatEventFlow.tryEmit(CombatVisualEvent(
                damage = finalPlayerDamage,
                isCrit = isCrit,
                isOverdrive = false,
                isDodge = false,
                isPlayerHit = false,
                textPopup = playerPopupText,
                popupColor = playerPopupColor,
                triggeredProcs = st.turnProcs.toList()
            ))

            // Synergy 2 Green: Double Impulse (35% echo attack 50% dmg + 3 EP)
            if (syn.hasGreen2 && (0..100).random() < 35 && st.newEnemyHp > 0) {
                val echoDmg = maxOf(1, (finalPlayerDamage * 0.50f).toInt())
                st.newEnemyHp = maxOf(0, st.newEnemyHp - echoDmg)
                val curP = dao.getPlayer(uid) ?: player
                val newE = minOf(curP.max_energy, curP.energy + 3)
                dao.updatePlayer(curP.copy(energy = newE))
                log(uid, "⚡ [ДВОЙНОЙ ИМПУЛЬС]: Эхо-атака нанесла -$echoDmg урона и восполнила +3 EP!", "combat")
                st.turnProcs.add(EquipmentProcEvent("syn_green_2", "⚡ ЭХО-УДАР: -$echoDmg [+3 EP]", ProcColorType.SHIELD_CYAN))
                _combatEventFlow.tryEmit(CombatVisualEvent(
                    damage = echoDmg,
                    isEchoAttack = true,
                    textPopup = "⚡ ЭХО -$echoDmg",
                    popupColor = "0xFF00FFCC",
                    triggeredProcs = st.turnProcs.toList()
                ))
            }
        }
    }

    /**
     * Kill/loot resolution of a combat turn (extracted from handleCombatTurn).
     * Mechanical move, no logic changes.
     */
    private suspend fun resolveEnemyDefeat(
        st: CombatTurnState,
        uid: Long,
        session: RaidSession,
        player: Player,
        villain: GameVillainData,
        weaponItem: InventoryItem?,
        headItem: InventoryItem?,
        syn: CombatSynergyFlags
    ) {
        log(uid, "УСПЕХ: Цель ${villain.name} нейтрализована.", "loot")
        recordEnemyKill(villain.name)
        val updatedEnergy = minOf(player.max_energy, player.energy + 5)
        dao.updatePlayer(player.copy(energy = updatedEnergy))
        log(uid, "⚡ [ТАКТИЧЕСКИЙ РЕЗОНАНС]: Уничтожение врага вернуло +5 EP!", "info")

        // Synergy 4 Red: Titan's Rage explosion restores 15% max HP
        if (syn.hasRed4) {
            val titanHeal = maxOf(1, (player.max_hp * 0.15f).toInt())
            val curP = dao.getPlayer(uid) ?: player
            dao.updatePlayer(curP.copy(hp = minOf(curP.max_hp, curP.hp + titanHeal)))
            log(uid, "💥 [ЯРОСТЬ ТИТАНА]: Взрыв поверженного врага восстановил +$titanHeal HP (15%)!", "heal")
        }

        val equippedAll = dao.getInventoryFlow(uid).first().filter { it.is_equipped }
        val hasMaxwellsDemon = equippedAll.any { it.item_id == "maxwells_demon" }
        val hasOblivionChip = equippedAll.any { it.item_id == "oblivion_chip" }
        val isDoubleDrop = session.active_mutator == io.eidos.zerolayer.domain.combat.CombatEngine.AFFIX_DOUBLE_DROP
        val rawCoins = if (weaponItem?.item_id == "cache_wiper") 0L else villain.coin
        var baseCoins = if (isDoubleDrop) rawCoins * 2 else rawCoins
        
        // Fragile core mutator: 2x BC
        if (session.active_mutator == SectorMutator.FRAGILE_CORE.id) {
            baseCoins *= 2
        }
        val tax = if (hasMaxwellsDemon) (baseCoins * 0.1).toLong() else 0L

        if (headItem?.item_id == "vampire_visor") {
            val healVisor = maxOf(1, (session.signal * 0.05).toInt())
            val newSig = minOf(100, session.signal + healVisor)
            dao.insertRaidSession(session.copy(signal = newSig))
            log(uid, "🩸 [Визор Вампира]: Уничтожение врага восстановило +5% ($healVisor HP) Сигнала!", "info")
            st.turnProcs.add(EquipmentProcEvent("vampire_visor", "🩸 ВИЗОР ВАМПИРА: +5% СИГНАЛА [KILL]", ProcColorType.HEAL_NEON))
        }

        val activeOverchargeTier = getOverchargeTier(uid)
        val ocLootMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(activeOverchargeTier)
        var finalCoins = ((baseCoins - tax) * ocLootMult).toLong()

        // Synergy Cursed Pact: +25% BC
        if (syn.hasCursedPact) {
            finalCoins = (finalCoins * 1.25f).toLong()
            log(uid, "🟣 [ПАКТ БЕЗДНЫ]: Темный контракт увеличил добычу (+25% BC)!", "loot")
        }

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
        dao.updatePlayer(player.copy(kills = player.kills + 1))
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
    }

    /**
     * Enemy retaliation portion of a combat turn (extracted from handleCombatTurn).
     * Mechanical move, no logic changes.
     */
    private suspend fun performEnemyTurn(
        st: CombatTurnState,
        uid: Long,
        session: RaidSession,
        player: Player,
        villain: GameVillainData,
        activeStats: PlayerStats,
        weaponItem: InventoryItem?,
        armorItem: InventoryItem?,
        headItem: InventoryItem?,
        aiAction: io.eidos.zerolayer.domain.combat.CombatEngine.MonsterAiAction,
        enemyIntent: io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntent,
        syn: CombatSynergyFlags,
        nextTurn: Int,
        isGuarding: Boolean
    ) {
        // --- Enemy Turn with Tactical AI ---
        if (aiAction.logMessage != null && !aiAction.isPhaseEvading) {
            log(uid, aiAction.logMessage, "combat")
        }
        if (aiAction.selfHeal > 0) {
            st.newEnemyHp = minOf(villain.hp, st.newEnemyHp + aiAction.selfHeal)
        }
        var workingCoins = session.buffer_coins
        if (aiAction.drainBioCoins > 0 && workingCoins > 0) {
            val drained = minOf(workingCoins, aiAction.drainBioCoins.toLong())
            workingCoins -= drained
        }
        if (aiAction.drainEnergy > 0 && player.energy > 0) {
            val newE = maxOf(0, player.energy - aiAction.drainEnergy)
            dao.updatePlayer(player.copy(energy = newE))
        }
        if (aiAction.isDetonating) {
            st.newEnemyHp = 0
        }

        val hasParadox = weaponItem?.item_id == "grandfather_paradox"
        val baseEvasion = io.eidos.zerolayer.domain.combat.CombatEngine.calculateEvasionChance(
            playerDefense = activeStats.defense,
            hasTacticalHelmet = headItem?.item_id == "tactical_helmet"
        )
        val evasionChance = if (syn.hasDuoGreenBlue) minOf(85f, baseEvasion + 20f) else baseEvasion
        val isEvaded = !isGuarding && ((0..100).random() < evasionChance)

        if (isEvaded) {
            val dodgeCharge = getOverdriveCharge(uid) + io.eidos.zerolayer.domain.combat.CombatEngine.CHARGE_DODGE
            setOverdriveCharge(uid, dodgeCharge)
            
            // Synergy 4 Green: Shadow Dance (+50% Overdrive and next hit 100% crit)
            if (syn.hasGreen4) {
                shadowDanceGuaranteedCrit[uid] = true
                setOverdriveCharge(uid, getOverdriveCharge(uid) + 50)
                log(uid, "🥷 [ТАНЕЦ ТЕНЕЙ]: Уворот разогнал Овердрайв (+50%)! Следующий удар гарантированно КРИТИЧЕСКИЙ!", "info")
            }
            // Synergy Duo Green+Blue: Quantum Ghost (+4 EP on dodge)
            if (syn.hasDuoGreenBlue) {
                val p = dao.getPlayer(uid) ?: player
                dao.updatePlayer(p.copy(energy = minOf(p.max_energy, p.energy + 4)))
                log(uid, "👻 [КВАНТОВЫЙ ПРИЗРАК]: Сдвиг фазы вернул +4 EP!", "info")
            }

            if (headItem?.item_id == "tactical_helmet") {
                st.turnProcs.add(EquipmentProcEvent("tactical_helmet", "⚡ ТАКТИЧЕСКИЙ ШЛЕМ: УКЛОНЕНИЕ!", ProcColorType.SHIELD_CYAN))
            }
            _combatEventFlow.tryEmit(CombatVisualEvent(
                isDodge = true,
                textPopup = "💨 УКЛОНЕНИЕ!",
                popupColor = "0xFF00FFCC",
                triggeredProcs = st.turnProcs.toList()
            ))

            log(uid, "УКЛОНЕНИЕ: Сдвиг сигнала. Атака от ${villain.name} промахнулась (+25% Овердрайв).", "info")
            dao.insertRaidSession(session.copy(
                current_enemy_hp = st.newEnemyHp,
                buffer_coins = workingCoins,
                combat_turn = nextTurn
            ))
        } else {
            val playerPower = activeStats.attack + activeStats.defense + activeStats.luck
            var rawVillainAtk = io.eidos.zerolayer.domain.combat.CombatEngine.calculateScaledEnemyAtk(
                villainAtk = villain.atk,
                playerPower = playerPower,
                depth = session.depth
            ) + aiAction.extraDamage

            // Mutator enemy attack scaling
            if (session.active_mutator == SectorMutator.FRAGILE_CORE.id) {
                rawVillainAtk = (rawVillainAtk * 1.30f).toInt()
            }
            if (session.active_mutator == SectorMutator.NEURO_OVERLOAD.id) {
                rawVillainAtk = (rawVillainAtk * 1.20f).toInt()
            }

            val ocAtkMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeEnemyAtkMultiplier(getOverchargeTier(uid))
            val scaledVillainAtk = (rawVillainAtk * aiAction.damageMultiplier * ocAtkMult).toInt()

            val effectivePlayerDef = (activeStats.defense * (1.0f - aiAction.bypassArmorPercent)).toInt()
            val baseEnemyDamage = io.eidos.zerolayer.domain.combat.CombatEngine.calculateBaseEnemyDamage(
                scaledEnemyAtk = scaledVillainAtk,
                playerDefense = effectivePlayerDef
            )
            var enemyDamage = baseEnemyDamage

            if (stunnedEnemies[uid] == true) {
                stunnedEnemies[uid] = false
                enemyDamage = 0
                log(uid, "💫 [ДЕЗОРИЕНТАЦИЯ]: Враг оглушен и пропускает ход!", "info")
            } else if (enemyIntent.type == io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.POWER_CHARGE) {
                if (isGuarding) {
                    enemyDamage = (baseEnemyDamage * 2.5f * 0.40f).toInt()
                    log(uid, "🛡 [ИДЕАЛЬНЫЙ БЛОК]: Силовой заряд противника заблокирован нейро-щитом (-60% урона)!", "combat")
                } else {
                    enemyDamage = (baseEnemyDamage * 2.5f).toInt()
                    log(uid, "⚠️ [СИЛОВОЙ ВСПЛЕСК]: Враг провел сокрушительный удар на x2.5 урона!", "error")
                }
            } else if (isGuarding) {
                enemyDamage = (baseEnemyDamage * 0.40f).toInt()
            }

            // Synergy 2 Red: Spiked Armor (reflect 100% blocked damage back to enemy)
            val blockedDmg = baseEnemyDamage - enemyDamage
            if (syn.hasRed2 && isGuarding && blockedDmg > 0) {
                st.newEnemyHp = maxOf(0, st.newEnemyHp - blockedDmg)
                log(uid, "🛡️ [ШИПОВАННАЯ БРОНЯ]: Отражено -$blockedDmg заблокированного урона обратно атакующему!", "combat")
                st.turnProcs.add(EquipmentProcEvent("syn_red_2", "🛡️ ШИПЫ: -$blockedDmg DMG", ProcColorType.CURSED_RED))
                _combatEventFlow.tryEmit(CombatVisualEvent(
                    damage = blockedDmg,
                    isReflectBlock = true,
                    textPopup = "🛡️ ШИПЫ -$blockedDmg",
                    popupColor = "0xFFFF0055"
                ))
            }

            if (aiAction.strikesTwice && enemyDamage > 0) {
                enemyDamage = (enemyDamage * 1.7f).toInt()
            }

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
                st.turnProcs.add(EquipmentProcEvent("grandfather_paradox", "⏳ ПАРАДОКС ДЕДА: БУФЕР $newDmgBuf DMG [$nextTurn/3]", ProcColorType.CURSED_RED))
                dao.insertRaidSession(session.copy(
                    current_enemy_hp = st.newEnemyHp,
                    buffer_coins = workingCoins,
                    combat_turn = nextTurn,
                    damage_buffer = newDmgBuf
                ))
                _combatEventFlow.tryEmit(CombatVisualEvent(triggeredProcs = st.turnProcs.toList()))
            } else {
                var totalIncoming = enemyDamage
                if (hasParadox && nextTurn == 4) {
                    totalIncoming += session.damage_buffer
                    log(uid, "💥 [Парадокс Деда]: Временной барьер лопнул! Накопленный урон ($totalIncoming) ударил по вам!", "error")
                }

                // Architect mask reflection (30%)
                if (headItem?.item_id == "architect_mask" && totalIncoming > 0) {
                    val reflected = maxOf(1, (totalIncoming * 0.30f).toInt())
                    st.newEnemyHp = maxOf(0, st.newEnemyHp - reflected)
                    log(uid, "🛡 [Лицо Архитектора]: Отражено -$reflected урона обратно во врага!", "combat")
                    st.turnProcs.add(EquipmentProcEvent("architect_mask", "🛡 ЛИЦО АРХИТЕКТОРА: ОТРАЖЕНО $reflected УРОНА", ProcColorType.SHIELD_CYAN))
                }

                // Cursed Armor error_404_mirror logic
                val mirrorRoll = (0..100).random()
                if (armorItem?.item_id == "error_404_mirror" && mirrorRoll < 50) {
                    log(uid, "🪞 [Зеркало 404]: Входящий урон ($totalIncoming) отражен обратно во врага!", "combat")
                    st.turnProcs.add(EquipmentProcEvent("error_404_mirror", "🪞 ЗЕРКАЛО 404: ОТРАЖЕНО $totalIncoming УРОНА", ProcColorType.SHIELD_CYAN))
                    dao.insertRaidSession(session.copy(
                        current_enemy_hp = st.newEnemyHp - totalIncoming,
                        buffer_coins = workingCoins,
                        combat_turn = nextTurn,
                        damage_buffer = 0
                    ))
                } else {
                    val newSignal = session.signal - totalIncoming

                    // Cursed Armor thermonuclear_shroud logic
                    if (armorItem?.item_id == "thermonuclear_shroud" && newSignal <= 0) {
                        log(uid, "☢ [Термоядерный Саван]: Инициирован самоподрыв! Враг уничтожен. Буфер рейда сожжен.", "error")
                        st.turnProcs.add(EquipmentProcEvent("thermonuclear_shroud", "💥 ТЕРМОЯДЕРНЫЙ САВАН: ВЗРЫВ 999,999 DMG!", ProcColorType.CURSED_RED))
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
                        val livePlayer = dao.getPlayer(uid) ?: player
                        
                        // Synergy Cursed Pact: Fatal blow resurrection + explosion
                        if (livePlayer.hp - totalIncoming <= 0 && syn.hasCursedPact && pactResurrectionsUsed[uid] != true) {
                            pactResurrectionsUsed[uid] = true
                            val reviveHp = maxOf(1, (livePlayer.max_hp * 0.25f).toInt())
                            val boomDmg = 150
                            st.newEnemyHp = maxOf(0, st.newEnemyHp - boomDmg)
                            dao.updatePlayer(livePlayer.copy(hp = reviveHp))
                            dao.insertRaidSession(session.copy(
                                current_enemy_hp = st.newEnemyHp,
                                buffer_coins = workingCoins,
                                signal = reviveHp,
                                combat_turn = nextTurn,
                                damage_buffer = 0
                            ))
                            log(uid, "🟣 [ПАКТ БЕЗДНЫ]: Смертельный удар разорвал темную материю! Взрыв -$boomDmg DMG по врагу, оператор воскрес с $reviveHp HP (25%)!", "loot")
                            st.turnProcs.add(EquipmentProcEvent("syn_cursed_pact", "🟣 ПАКТ БЕЗДНЫ: ВОСКРЕШЕНИЕ [$reviveHp HP]!", ProcColorType.CURSED_RED))
                            _combatEventFlow.tryEmit(CombatVisualEvent(
                                isPlayerHit = true,
                                textPopup = "🟣 ВОСКРЕШЕНИЕ!",
                                popupColor = "0xFFE040FB",
                                triggeredProcs = st.turnProcs.toList()
                            ))
                        } else {
                            val guardSuffix = if (isGuarding) " [ЗАЩИТА -50%]" else ""
                            log(uid, "УРОН: ${villain.name} атакует! -$totalIncoming Сигнала/HP$guardSuffix.", "combat")
                            dao.updatePlayer(livePlayer.copy(hp = maxOf(0, livePlayer.hp - totalIncoming)))
                            dao.insertRaidSession(session.copy(
                                current_enemy_hp = st.newEnemyHp,
                                buffer_coins = workingCoins,
                                signal = newSignal,
                                combat_turn = nextTurn,
                                damage_buffer = 0
                            ))
                            _combatEventFlow.tryEmit(CombatVisualEvent(
                                isPlayerHit = true,
                                incomingDamage = totalIncoming,
                                textPopup = "-$totalIncoming HP",
                                popupColor = "0xFFFF1744",
                                triggeredProcs = st.turnProcs.toList()
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
        }
        checkDeath(uid)
    }

}
