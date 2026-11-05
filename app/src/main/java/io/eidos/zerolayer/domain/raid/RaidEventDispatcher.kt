package io.eidos.zerolayer.domain.raid

import io.eidos.zerolayer.data.Grave
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.RaidSession
import io.eidos.zerolayer.domain.anomaly.AnomalyEngine
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

        data class VoidStep(
            val xpGain: Long,
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
        gravesList: List<Grave>,
        activeMutatorId: String? = null
    ): DispatchResult {
        // 1. Reality Silencer Check -> If active, Maxwell Demon & Anomalies are completely suppressed
        val canSpawnDemon = !flags.hasRealitySilencer && depth > 50

        // 2. Maxwell Demon Check (Depth > 50 with 5% chance)
        if (canSpawnDemon && Random.nextInt(100) < 5) {
            return DispatchResult.MaxwellDemon(
                message = "😈 [ДЕМОН МАКСВЕЛЛА]: Квантовая энтропия сфокусировалась в аватаре Демона на глубине ${depth}м!"
            )
        }

        // 3. Player Graves Check (Guaranteed Corpse Run if grave is at this exact depth, else randomized)
        // GATEKEEPER: every 1000m a biome warden blocks the descent (drops the Biome Key)
        if (depth > 0 && depth % 1000 == 0) {
            val keeper = io.eidos.zerolayer.data.GameData.VILLAINS
                .filter { it.level <= maxMonsterLevelForDepth(depth) + 2 }
                .maxByOrNull { it.level }
                ?: io.eidos.zerolayer.data.GameData.VILLAINS.last()
            val keeperHp = maxOf(400, (keeper.hp * (1.0f + depth * 0.0075f) * 2.5f).toInt())
            return DispatchResult.CombatEncounter(
                enemyName = keeper.name,
                enemyHp = keeperHp,
                enemyLevel = keeper.level + 3,
                isGlitchPhantom = false,
                message = "🚪 [ХРАНИТЕЛЬ ВОРОТ]: ${keeper.name} [УР ${keeper.level + 3}] стережёт врата на ${depth}м! За его спиной - Ключ Биомы. Путь вниз запечатан (HP: $keeperHp)!"
            )
        }

        val exactGrave = gravesList.find { it.depth == depth }
        if (exactGrave != null) {
            return DispatchResult.GraveFound(
                grave = exactGrave,
                message = "🪦 [ВОЗВРАТ ЛУТА // CORPSE RUN]: Обнаружена Цифровая Могила оператора ${exactGrave.owner_name} на ${exactGrave.depth}м!"
            )
        }
        // ECHOES_PAST mutator: doubled grave/relic encounter chance (Abyss Resonance)
        val baseGraveChance = if (flags.hasDeathMask) 80 else 30
        val graveChance = if (activeMutatorId == "mutator_echoes_past") baseGraveChance * 2 else baseGraveChance
        if (gravesList.isNotEmpty() && Random.nextInt(100) < graveChance) {
            val grave = gravesList.random()
            return DispatchResult.GraveFound(
                grave = grave,
                message = "🪦 [МОГИЛА ПАВШЕГО]: Обнаружен терминальный слепок оператора ${grave.owner_name} на ${grave.depth}м!"
            )
        }

        val hasStealthBuff = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_STEALTH_NIGHT)

        // 4. Multi-tiered Event Pool Selection (Stealth Night 30% bypass triggers ONLY on Trap or Combat)
        val roll = Random.nextInt(100)
        return when {
            roll < 25 -> handleVoidStepEvent(depth, player)
            roll < 40 -> {
                if (hasStealthBuff && Random.nextInt(100) < 30) {
                    DispatchResult.StealthBypass(
                        message = "🌙 [НОЧНАЯ СКРЫТНОСТЬ]: Вы активировали маскировку сигнала и незаметно обошли ловушку без урона!"
                    )
                } else {
                    handleTrapEvent(depth, player, playerDefense, flags)
                }
            }
            roll < 60 -> handleLootEvent(depth, player, playerLuck, flags)
            roll < 72 -> handleSafeZoneEvent(depth, player, flags)
            roll < 82 -> handleRiddleEvent(depth)
            else -> {
                if (hasStealthBuff && Random.nextInt(100) < 30) {
                    DispatchResult.StealthBypass(
                        message = "🌙 [НОЧНАЯ СКРЫТНОСТЬ]: Вы активировали маскировку сигнала и незаметно обошли опасный патруль без боя!"
                    )
                } else {
                    handleCombatEvent(depth, flags)
                }
            }
        }
    }

    private fun handleVoidStepEvent(depth: Int, player: Player): DispatchResult {
        val xpGain = (5L..15L).random() + (depth / 50L)
        val message = RaidLoreEngine.generateCombinedLore(
            type = "empty",
            depth = depth,
            extraNote = "💠 [ИССЛЕДОВАНИЕ БЕЗДНЫ]: Слой исследован глубже (+${xpGain} XP)."
        )
        return DispatchResult.VoidStep(
            xpGain = xpGain,
            message = message
        )
    }

    private fun handleTrapEvent(
        depth: Int,
        player: Player,
        playerDefense: Int,
        flags: EquipmentFlags
    ): DispatchResult {
        val trapContent = RaidLoreEngine.getRandomContent("trap")
        val baseTrapVal = if (trapContent.value > 0) trapContent.value else 25

        // 1. Check Maxwell Entropy Shield (100% trap immunity)
        if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_ENTROPY_SHIELD)) {
            val message = RaidLoreEngine.generateCombinedLore(
                type = "trap",
                depth = depth,
                extraNote = "🛡️ [ЭНТРОПИЙНЫЙ ЩИТ]: Ловушка Нулевого Слоя полностью поглощена квантовым барьером!"
            )
            return DispatchResult.TrapTriggered(
                damage = 0,
                healAmount = 0,
                message = message
            )
        }

        if (flags.hasKarmaInversion) {
            // Karma Inversion heals +20% HP instead of damaging
            val healAmount = maxOf(5, (player.max_hp * 0.20f).toInt())
            val message = RaidLoreEngine.generateCombinedLore(
                type = "trap",
                depth = depth,
                extraNote = "☯️ [ИНВЕРСИЯ КАРМЫ]: Ловушка Нулевого Слоя инвертирована в регенеративный импульс! Восстановлено +${healAmount} HP!"
            )
            return DispatchResult.TrapTriggered(
                damage = 0,
                healAmount = healAmount,
                message = message
            )
        }

        val depthMultiplier = io.eidos.zerolayer.domain.combat.CombatEngine.getDepthDifficultyMultiplier(depth)
        val maskReduction = if (flags.hasScavengerMask) 5 else 0
        val baseDamage = ((baseTrapVal + (depth / 15)) * depthMultiplier).toInt()
        var finalDamage = maxOf(5, baseDamage - (playerDefense / 2) - maskReduction)

        // If Maxwell Vulnerability is active, increase trap damage by +25%
        if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_VULNERABILITY)) {
            finalDamage = (finalDamage * 1.25f).toInt()
        }

        // One-shot protection: If HP > 90%, damage leaves minimum 5% HP
        val ninetyPercentHp = (player.max_hp * 0.90f).toInt()
        val fivePercentHp = maxOf(1, (player.max_hp * 0.05f).toInt())
        if (player.hp >= ninetyPercentHp && (player.hp - finalDamage) < fivePercentHp) {
            finalDamage = maxOf(0, player.hp - fivePercentHp)
        }

        val maskNote = if (flags.hasScavengerMask) " (Защита Маски: -5 ед)" else ""
        val vulnNote = if (AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_VULNERABILITY)) " [⚠️ УЯЗВИМОСТЬ +25%]" else ""
        val message = RaidLoreEngine.generateCombinedLore(
            type = "trap",
            depth = depth,
            extraNote = "💥 [УРОН ЛОВУШКИ]: -$finalDamage HP$maskNote$vulnNote."
        )

        return DispatchResult.TrapTriggered(
            damage = finalDamage,
            healAmount = 0,
            message = message
        )
    }

    private fun handleLootEvent(
        depth: Int,
        player: Player,
        playerLuck: Int,
        flags: EquipmentFlags
    ): DispatchResult {
        val lootContent = RaidLoreEngine.getRandomContent("loot")
        val baseLootVal = if (lootContent.value > 0) lootContent.value.toLong() else (20L..60L).random()
        val isOverload = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_OVERLOAD)
        val hasFortune = AnomalyEngine.isBuffActive(player, AnomalyEngine.BUFF_MAXWELL_FORTUNE)
        val luckMultiplier = 1.0f + (playerLuck * 0.02f)
        val depthRewardMultiplier = io.eidos.zerolayer.domain.combat.CombatEngine.getDepthRewardMultiplier(depth)
        val rawCoins = ((baseLootVal + (depth / 10L)) * luckMultiplier * depthRewardMultiplier).toLong()
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

        val itemsNote = if (items.isNotEmpty()) " и предметы: [${items.joinToString(", ")}]" else ""
        val message = RaidLoreEngine.generateCombinedLore(
            type = "loot",
            depth = depth,
            extraNote = "💰 [ДОБЫЧА СЛОЯ]: Получено +$finalCoins BC$itemsNote!"
        )

        return DispatchResult.LootFound(
            coins = finalCoins,
            items = items,
            message = message
        )
    }

    private fun handleSafeZoneEvent(
        depth: Int,
        player: Player,
        flags: EquipmentFlags
    ): DispatchResult {
        val healContent = RaidLoreEngine.getRandomContent("heal")
        val baseHealVal = if (healContent.value > 0) healContent.value else 15
        val heal = maxOf(5, (player.max_hp * 0.05f).toInt() + baseHealVal)
        val message = RaidLoreEngine.generateCombinedLore(
            type = "heal",
            depth = depth,
            extraNote = "💚 [ОАЗИС СТАБИЛЬНОСТИ]: Сигнал и биологический аватар восстановлены на +$heal HP."
        )
        return DispatchResult.SafeZone(
            healAmount = heal,
            message = message
        )
    }

    private fun handleRiddleEvent(depth: Int): DispatchResult {
        val rewardMultiplier = io.eidos.zerolayer.domain.combat.CombatEngine.getDepthRewardMultiplier(depth)
        val riddle = RaidLoreEngine.getRandomRiddle()
        val hint = RaidLoreEngine.getRandomHint("lore")
        return DispatchResult.RiddleEncounter(
            question = "ТЕРМИНАЛ СФИНКСА: «${riddle.question}»",
            options = riddle.options,
            correctIndex = riddle.correctIndex,
            rewardCoins = (150L * rewardMultiplier).toLong(),
            penaltyHp = 15,
            message = "🧩 [СФИНКС НУЛЕВОГО СЛОЯ]: ${hint.text}\nВпереди материализовалась загадка: «${riddle.question}»"
        )
    }

    private fun maxMonsterLevelForDepth(depth: Int): Int = when {
        depth < 150 -> 1
        depth < 350 -> 2
        depth < 650 -> 3
        depth < 1000 -> 4
        depth < 1500 -> 5
        depth < 2000 -> 6
        depth < 2600 -> 7
        depth < 3300 -> 8
        depth < 4000 -> 9
        depth < 4800 -> 10
        depth < 5800 -> 12
        depth < 7000 -> 15
        depth < 8500 -> 20
        depth < 10000 -> 25
        else -> 30
    }

    private fun handleCombatEvent(depth: Int, flags: EquipmentFlags): DispatchResult {
        val maxMonsterLevel = maxMonsterLevelForDepth(depth)
        val isGlitch = !flags.hasRealitySilencer && Random.nextInt(100) < 5

        if (isGlitch) {
            val baseHp = 180 + (depth / 25)
            return DispatchResult.CombatEncounter(
                enemyName = "▲▓ СТИРАТЕЛЬ_ГЛИТЧЕЙ █░",
                enemyHp = baseHp,
                enemyLevel = maxMonsterLevel + 1,
                isGlitchPhantom = true,
                message = "☠ ░▒▓ ГЛИТЧ-ФАНТОМ ▓▒░ ☠: Нестабильная программа-фантом атаковала аватар!"
            )
        }

        val candidates = io.eidos.zerolayer.data.GameData.VILLAINS.filter { it.level <= maxMonsterLevel }
        val villain = if (candidates.isNotEmpty()) {
            candidates.takeLast(3).random()
        } else {
            io.eidos.zerolayer.data.GameData.VILLAINS.first()
        }
        // Scaled HP with depth so starter monsters aren't trivialized and one-shotted with early gear
        val depthScale = 1.0f + (depth * 0.0075f)
        val baseMinHp = 50 + (villain.level * 25) + (depth / 4)
        val scaledHp = maxOf(baseMinHp, (villain.hp * depthScale).toInt())

        return DispatchResult.CombatEncounter(
            enemyName = villain.name,
            enemyHp = scaledHp,
            enemyLevel = villain.level,
            isGlitchPhantom = false,
            message = "⚠️ ${villain.name} [УР ${villain.level}] (HP: $scaledHp) перехватил ваш сигнал!"
        )
    }
}
