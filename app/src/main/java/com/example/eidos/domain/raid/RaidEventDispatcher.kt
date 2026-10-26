package com.example.eidos.domain.raid

import com.example.eidos.data.Grave
import com.example.eidos.data.InventoryItem
import com.example.eidos.data.Player
import com.example.eidos.data.RaidSession
import com.example.eidos.domain.anomaly.AnomalyEngine
import kotlin.random.Random

object RaidEventDispatcher {

    sealed class DispatchResult {
        data class MaxwellDemon(
            val message: String
        ) : DispatchResult()

        data class StealthBypass(
            val message: String
        ) : DispatchResult()

        data class GraveFound(
            val grave: Grave,
            val message: String
        ) : DispatchResult()

        data class TrapTriggered(
            val damage: Int,
            val healAmount: Int, // if karma inversion is equipped
            val message: String
        ) : DispatchResult()

        data class LootFound(
            val coins: Long,
            val items: List<String>,
            val message: String
        ) : DispatchResult()

        data class SafeZone(
            val healAmount: Int,
            val message: String
        ) : DispatchResult()

        data class RiddleEncounter(
            val question: String,
            val options: List<String>,
            val correctIndex: Int,
            val rewardCoins: Long,
            val penaltyHp: Int,
            val message: String
        ) : DispatchResult()

        data class CombatEncounter(
            val enemyName: String,
            val enemyHp: Int,
            val enemyLevel: Int,
            val isGlitchPhantom: Boolean,
            val message: String
        ) : DispatchResult()

        data class SectorScanned(
            val message: String
        ) : DispatchResult()
    }

    data class EquipmentFlags(
        val hasRealitySilencer: Boolean = false,
        val hasDeathMask: Boolean = false,
        val hasScavengerMask: Boolean = false,
        val hasNomadGoggles: Boolean = false,
        val hasKarmaInversion: Boolean = false,
        val hasHoloPoverty: Boolean = false
    )

    fun parseEquipmentFlags(equippedItems: List<InventoryItem>): EquipmentFlags {
        return EquipmentFlags(
            hasRealitySilencer = equippedItems.any { it.item_id == "reality_silencer" },
            hasDeathMask = equippedItems.any { it.item_id == "death_mask" },
            hasScavengerMask = equippedItems.any { it.item_id == "scavenger_mask" },
            hasNomadGoggles = equippedItems.any { it.item_id == "nomad_goggles" },
            hasKarmaInversion = equippedItems.any { it.item_id == "karma_inversion" },
            hasHoloPoverty = equippedItems.any { it.item_id == "holo_poverty" }
        )
    }

    fun dispatchNextEvent(
        depth: Int,
        player: Player,
        playerDefense: Int,
        playerLuck: Int,
        flags: EquipmentFlags,
        gravesList: List<Grave>
    ): DispatchResult {
        // 1. Reality Silencer Check -> If active, Maxwell Demon & Anomalies are completely suppressed
        val canSpawnDemon = !flags.hasRealitySilencer && depth > 50

        // 2. Maxwell Demon Check (Depth > 50 with 5% chance)
        if (canSpawnDemon && Random.nextInt(100) < 5) {
            return DispatchResult.MaxwellDemon(
                message = "😈 [ДЕМОН МАКСВЕЛЛА]: Квантовая энтропия сфокусировалась в аватаре Демона на глубине ${depth}м!"
            )
        }

        // 3. Stealth Night Buff / Shadow bypass Check (30% chance to safely bypass danger)
        val hasStealthBuff = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_STEALTH_NIGHT)
        if (hasStealthBuff && Random.nextInt(100) < 30) {
            return DispatchResult.StealthBypass(
                message = "🌙 [НОЧНАЯ СКРЫТНОСТЬ]: Вы активировали маскировку сигнала и незаметно обошли опасный патруль без боя!"
            )
        }

        // 4. Player Graves Check (30% base, 80% if Death Mask is equipped)
        val graveChance = if (flags.hasDeathMask) 80 else 30
        if (gravesList.isNotEmpty() && Random.nextInt(100) < graveChance) {
            val grave = gravesList.random()
            return DispatchResult.GraveFound(
                grave = grave,
                message = "🪦 [МОГИЛА ПАВШЕГО]: Обнаружен терминальный слепок оператора ${grave.owner_name} на ${grave.depth}м!"
            )
        }

        // 5. Base Pool Selection
        val roll = Random.nextInt(100)
        return when {
            roll < 20 -> handleTrapEvent(depth, player, playerDefense, flags)
            roll < 45 -> handleLootEvent(depth, player, playerLuck, flags)
            roll < 60 -> handleSafeZoneEvent(depth, player, flags)
            roll < 75 -> handleRiddleEvent(depth)
            else -> handleCombatEvent(depth, flags)
        }
    }

    private fun handleTrapEvent(
        depth: Int,
        player: Player,
        playerDefense: Int,
        flags: EquipmentFlags
    ): DispatchResult {
        // 1. Check Maxwell Entropy Shield (100% trap immunity)
        if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_ENTROPY_SHIELD)) {
            return DispatchResult.TrapTriggered(
                damage = 0,
                healAmount = 0,
                message = "🛡️ [ЭНТРОПИЙНЫЙ ЩИТ]: Ловушка Нулевого Слоя полностью поглощена квантовым барьером!"
            )
        }

        if (flags.hasKarmaInversion) {
            // Karma Inversion heals +20% HP instead of damaging
            val healAmount = maxOf(5, (player.max_hp * 0.20f).toInt())
            return DispatchResult.TrapTriggered(
                damage = 0,
                healAmount = healAmount,
                message = "☯️ [ИНВЕРСИЯ КАРМЫ]: Ловушка Нулевого Слоя инвертирована в регенеративный импульс! Восстановлено +$healAmount HP!"
            )
        }

        val depthMultiplier = com.example.eidos.domain.combat.CombatEngine.getDepthDifficultyMultiplier(depth)
        val maskReduction = if (flags.hasScavengerMask) 5 else 0
        val baseDamage = ((15 + (depth / 10)) * depthMultiplier).toInt()
        var finalDamage = maxOf(5, baseDamage - (playerDefense / 2) - maskReduction)

        // If Maxwell Vulnerability is active, increase trap damage by +25%
        if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_VULNERABILITY)) {
            finalDamage = (finalDamage * 1.25f).toInt()
        }

        // One-shot protection: If HP > 90%, damage leaves minimum 5% HP
        val ninetyPercentHp = (player.max_hp * 0.90f).toInt()
        val fivePercentHp = maxOf(1, (player.max_hp * 0.05f).toInt())
        if (player.hp >= ninetyPercentHp && finalDamage >= player.hp) {
            finalDamage = maxOf(1, player.hp - fivePercentHp)
        }

        val maskNote = if (flags.hasScavengerMask) " (Защита Маски: -5 ед)" else ""
        val vulnNote = if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_VULNERABILITY)) " [⚠️ УЯЗВИМОСТЬ +25%]" else ""
        val scalingNote = if (depth > 1000) " [МАСШТАБ ГЛУБИНЫ x${String.format(java.util.Locale.US, "%.2f", depthMultiplier)}]" else ""
        return DispatchResult.TrapTriggered(
            damage = finalDamage,
            healAmount = 0,
            message = "⚠️ [ЛОВУШКА СЛОЯ]: Детонировал лазерный импульс! Нанесено -$finalDamage урона$maskNote$vulnNote$scalingNote."
        )
    }

    private fun handleLootEvent(
        depth: Int,
        player: Player,
        playerLuck: Int,
        flags: EquipmentFlags
    ): DispatchResult {
        val isOverload = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_OVERLOAD)
        val hasFortune = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_FORTUNE)
        val luckMultiplier = 1.0f + (playerLuck * 0.02f)
        val depthRewardMultiplier = com.example.eidos.domain.combat.CombatEngine.getDepthRewardMultiplier(depth)
        val baseCoins = (10..30).random() + (depth / 5)
        val rawCoins = (baseCoins * luckMultiplier * depthRewardMultiplier).toLong()
        val finalCoins = if (isOverload) (rawCoins * 1.5f).toLong() else rawCoins

        val items = mutableListOf<String>()
        // 5% base chance of encrypted cache (10% if Maxwell Fortune, increases with depth)
        val depthCacheBonus = (depth / 1000).coerceAtMost(15)
        val cacheChance = (if (hasFortune) 10 else 5) + depthCacheBonus
        if (Random.nextInt(100) < cacheChance) {
            items.add("encrypted_cache")
        }
        val shardChance = if (hasFortune) 30 else 15
        if (Random.nextInt(100) < shardChance) {
            items.add(listOf("eidos_shard", "battery", "master_key").random())
        }

        // Proportional drop chance for Relic and Cursed items with depth stepping
        val relicChance = (2 + (depth / 500)).coerceAtMost(25)
        if (Random.nextInt(100) < relicChance) {
            val relicPool = listOf("relic_vampire", "death_mask", "karma_inversion", "quantum_blade", "oblivion_chip")
            items.add(relicPool.random())
        }

        // Deep cursed artifacts on 1500m+
        if (depth >= 1500) {
            val cursedChance = (1 + (depth / 1000)).coerceAtMost(18)
            if (Random.nextInt(100) < cursedChance) {
                val cursedPool = listOf("credit_slicer", "banhammer_shard", "error_404_mirror", "thermonuclear_shroud", "grandfather_paradox")
                items.add(cursedPool.random())
            }
        }

        val overloadNote = if (isOverload) " ⚡ [ПЕРЕГРУЗКА +50%]" else ""
        val fortuneNote = if (hasFortune) " 🎲 [ИНВЕРСИЯ ФОРТУНЫ x2]" else ""
        val singularityNote = if (depth >= 5000) " 🌌 [СИНГУЛЯРНОСТЬ]" else ""
        val itemsNote = if (items.isNotEmpty()) " и предметы: [${items.joinToString(", ")}]" else ""
        return DispatchResult.LootFound(
            coins = finalCoins,
            items = items,
            message = "📦 [ТАЙНИК СЛОЯ]: Извлечено +$finalCoins BC$overloadNote$fortuneNote$singularityNote$itemsNote!"
        )
    }

    private fun handleSafeZoneEvent(
        depth: Int,
        player: Player,
        flags: EquipmentFlags
    ): DispatchResult {
        val heal = maxOf(5, (player.max_hp * 0.05f).toInt())
        return DispatchResult.SafeZone(
            healAmount = heal,
            message = "🏕 [БЕЗОПАСНАЯ ЗОНА]: Нейро-купол изоляции. Сигнал стабилизирован на +$heal HP."
        )
    }

    private fun handleRiddleEvent(depth: Int): DispatchResult {
        val rewardMultiplier = com.example.eidos.domain.combat.CombatEngine.getDepthRewardMultiplier(depth)
        val riddles = listOf(
            DispatchResult.RiddleEncounter(
                question = "ТЕРМИНАЛ: «Сколько бит в одном килобайте в архитектуре Нулевого Слоя?»",
                options = listOf("8192 бит", "1024 бит", "4096 бит"),
                correctIndex = 0,
                rewardCoins = (150L * rewardMultiplier).toLong(),
                penaltyHp = 10,
                message = "🧩 [ТЕРМИНАЛЬНАЯ ЗАГАДКА]: Взломайте проверочный хэш."
            ),
            DispatchResult.RiddleEncounter(
                question = "ТЕРМИНАЛ: «Какой протокол сбрасывает тепловую энтропию демона?»",
                options = listOf("MAXWELL_REVERSE", "ENTROPY_ZERO", "BIT_PARITY"),
                correctIndex = 0,
                rewardCoins = (200L * rewardMultiplier).toLong(),
                penaltyHp = 15,
                message = "🧩 [ТЕРМИНАЛЬНАЯ ЗАГАДКА]: Взломайте проверочный хэш."
            )
        )
        return riddles.random()
    }

    private fun handleCombatEvent(depth: Int, flags: EquipmentFlags): DispatchResult {
        val depthLevel = (depth / 50) + 1
        val depthMultiplier = com.example.eidos.domain.combat.CombatEngine.getDepthDifficultyMultiplier(depth)
        val isGlitch = !flags.hasRealitySilencer && Random.nextInt(100) < 5

        if (isGlitch) {
            val baseHp = (180..350).random() + (depth * 2)
            val hp = (baseHp * depthMultiplier).toInt()
            return DispatchResult.CombatEncounter(
                enemyName = "▲▓ СТИРАТЕЛЬ_ГЛИТЧЕЙ █░",
                enemyHp = hp,
                enemyLevel = depthLevel + 1,
                isGlitchPhantom = true,
                message = "☠ ░▒▓ ГЛИТЧ-ФАНТОМ ▓▒░ ☠: Нестабильная программа-фантом атаковала аватар!"
            )
        }

        val villains = com.example.eidos.data.GameData.VILLAINS.filter { it.level == depthLevel }
        val villain = villains.randomOrNull() ?: com.example.eidos.data.GameData.VILLAINS.first()
        val baseHp = villain.hp + (depth * 2)
        val hp = (baseHp * depthMultiplier).toInt()

        return DispatchResult.CombatEncounter(
            enemyName = villain.name,
            enemyHp = hp,
            enemyLevel = villain.level,
            isGlitchPhantom = false,
            message = "⚠️ ${villain.name} [УР ${villain.level}] (HP: $hp) перехватил ваш сигнал!"
        )
    }
}
