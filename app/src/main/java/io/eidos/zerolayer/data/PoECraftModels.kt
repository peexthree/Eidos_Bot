package io.eidos.zerolayer.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString

enum class ChipSocketColor(val title: String, val hexColor: Long) {
    RED_MONOLITH("Сила / Монолит", 0xFFFF3366),
    GREEN_GHOST("Логика / Призрак", 0xFF00FFCC),
    BLUE_HACKER("Нейро / Взломщик", 0xFF3399FF),
    WHITE_RAINBOW("Квантовый / Радужный (+25%)", 0xFFFFFFFF),
    LOCKED("Заблокирован (Ремонт в Кузнице)", 0xFF444444)
}

@Serializable
data class DataChip(
    val id: String,
    val name: String,
    val color: ChipSocketColor,
    val statBonusType: String, // "ATK", "DEF", "CRIT", "HP", "ENERGY"
    val statBonusValue: Int
)

@Serializable
data class ItemAffix(
    val statType: String, // "ATK", "DEF", "CRIT", "HP"
    val minValue: Int,
    val maxValue: Int,
    var currentValue: Int
)

@Serializable
data class CyberEquipment(
    val affixes: List<ItemAffix> = emptyList(),
    val maxSockets: Int = 1,
    val socketColors: List<ChipSocketColor> = emptyList(),
    val insertedChips: List<DataChip?> = emptyList(),
    val isCorrupted: Boolean = false,
    val implicitAffix: String? = null
)

object PoECraftEngine {
    private val json = Json { ignoreUnknownKeys = true; prettyPrint = false }

    val ROLLABLE_SOCKET_COLORS = listOf(
        ChipSocketColor.RED_MONOLITH,
        ChipSocketColor.GREEN_GHOST,
        ChipSocketColor.BLUE_HACKER,
        ChipSocketColor.WHITE_RAINBOW
    )

    fun parseEquipment(customData: String?): CyberEquipment? {
        if (customData.isNullOrBlank()) return null
        return try {
            json.decodeFromString<CyberEquipment>(customData)
        } catch (e: Exception) {
            null
        }
    }

    fun serializeEquipment(equipment: CyberEquipment): String {
        return json.encodeToString(equipment)
    }

    fun getOrGenerateEquipment(item: InventoryItem, rarity: String): CyberEquipment {
        val existing = parseEquipment(item.custom_data)
        if (existing != null) return existing

        return generateDefaultEquipment(rarity)
    }

    fun generateDefaultEquipment(rarity: String): CyberEquipment {
        val rarityLower = rarity.lowercase()
        val (socketCount, maxAffixes) = when (rarityLower) {
            "uncommon" -> Pair(2, 2)
            "rare" -> Pair(3, 3)
            "epic" -> Pair(4, 3)
            "legendary" -> Pair(5, 4)
            "relic", "cursed" -> Pair(6, 4)
            else -> Pair(1, 1)
        }

        val colors = List(socketCount) {
            ROLLABLE_SOCKET_COLORS.random()
        }

        val possibleStats = listOf("ATK", "DEF", "CRIT", "HP")
        val selectedStats = possibleStats.shuffled().take(maxAffixes)

        val affixes = selectedStats.map { stat ->
            val (min, max) = when (rarityLower) {
                "legendary", "cursed" -> Pair(35, 60)
                "relic" -> Pair(60, 100)
                "rare", "epic" -> Pair(15, 35)
                else -> Pair(5, 15) // common, uncommon
            }
            val initialVal = (min..max).random()
            ItemAffix(statType = stat, minValue = min, maxValue = max, currentValue = initialVal)
        }

        return CyberEquipment(
            affixes = affixes,
            maxSockets = socketCount,
            socketColors = colors,
            insertedChips = List(socketCount) { null }
        )
    }

    // 🎲 Data Slicer (Chaos Orb): Rerolls all non-locked affixes using the proper rarity tiers
    fun applyDataSlicerWithLocking(
        current: CyberEquipment,
        lockedIndices: Set<Int>,
        rarity: String
    ): CyberEquipment {
        if (current.isCorrupted) return current
        val rarityLower = rarity.lowercase()

        val updatedAffixes = current.affixes.mapIndexed { index, affix ->
            if (lockedIndices.contains(index)) {
                // Keep locked affix exactly as is
                affix
            } else {
                // Reroll stat type and values within proper tier ranges
                val statPool = listOf("ATK", "DEF", "CRIT", "HP")
                val newStatType = if ((0..1).random() == 0) statPool.random() else affix.statType
                val (min, max) = when (rarityLower) {
                    "legendary", "cursed" -> Pair(35, 60)
                    "relic" -> Pair(60, 100)
                    "rare", "epic" -> Pair(15, 35)
                    else -> Pair(5, 15)
                }
                val roll = (min..max).random()
                ItemAffix(statType = newStatType, minValue = min, maxValue = max, currentValue = roll)
            }
        }

        return current.copy(affixes = updatedAffixes)
    }

    // 🎲 Original applyDataSlicer kept for backward compatibility
    fun applyDataSlicer(current: CyberEquipment, rarity: String): CyberEquipment {
        return applyDataSlicerWithLocking(current, emptySet(), rarity)
    }

    // ⚖️ Quantum Tuner (Divine Orb): Preserves affixes, rerolls roll value in [minValue..maxValue]
    fun applyQuantumTuner(current: CyberEquipment): CyberEquipment {
        if (current.isCorrupted) return current
        val newAffixes = current.affixes.map { affix ->
            val minV = minOf(affix.minValue, affix.maxValue)
            val maxV = maxOf(affix.minValue, affix.maxValue)
            val roll = (minV..maxV).random()
            affix.copy(minValue = minV, maxValue = maxV, currentValue = roll)
        }
        return current.copy(affixes = newAffixes)
    }

    // 🔌 Socket Puncher (Jeweller's Orb): Rerolls sockets count & colors
    fun applySocketPuncher(current: CyberEquipment, rarity: String): CyberEquipment {
        if (current.isCorrupted) return current
        val maxAllowedSockets = when (rarity.lowercase()) {
            "uncommon" -> 2
            "rare" -> 3
            "epic" -> 4
            "legendary" -> 6
            "cursed" -> 6
            else -> 1
        }
        val newCount = (1..maxAllowedSockets).random()
        val newColors = List(newCount) { ROLLABLE_SOCKET_COLORS.random() }
        
        val newInserted = List(newCount) { index ->
            if (index < current.insertedChips.size) current.insertedChips[index] else null
        }

        return current.copy(
            maxSockets = newCount,
            socketColors = newColors,
            insertedChips = newInserted
        )
    }

    // 🌈 Chromatic Injector (Chromatic Orb): Rerolls colors of all existing sockets
    fun applyChromaticInjector(current: CyberEquipment): CyberEquipment {
        if (current.isCorrupted) return current
        val newColors = List(current.maxSockets) { ROLLABLE_SOCKET_COLORS.random() }
        return current.copy(socketColors = newColors)
    }

    // ☣️ Cyber Vaal Glitch (Vaal Orb): Corrupts item, locks crafting, grants super implicit stat
    fun applyVaalCorruption(current: CyberEquipment): CyberEquipment {
        if (current.isCorrupted) return current
        val implicits = listOf(
            "☣️ [ЭЙДОС СКВЕРНА] +30 АТАКА ОВЕРКЛОК",
            "☣️ [ЭЙДОС СКВЕРНА] +20% ВАМПИРИЗМ И ЩИТ",
            "☣️ [ЭЙДОС СКВЕРНА] +25% ГЛОБАЛЬНЫЙ КРИТИЧЕСКИЙ УРОН",
            "☣️ [ЭЙДОС СКВЕРНА] +100 HP КИБЕР-ЖИЗНЕСТОЙКОСТЬ"
        )
        val selectedImplicit = implicits.random()
        return current.copy(
            isCorrupted = true,
            implicitAffix = selectedImplicit
        )
    }

    // Stat Synergy calculation
    fun calculateTotalStats(equipment: CyberEquipment): Map<String, Int> {
        val stats = mutableMapOf("ATK" to 0, "DEF" to 0, "CRIT" to 0, "HP" to 0, "ENERGY" to 0)

        // 1. Item affixes
        equipment.affixes.forEach { affix ->
            val curr = stats.getOrDefault(affix.statType, 0)
            stats[affix.statType] = curr + affix.currentValue
        }

        // 2. Inserted Chips & Socket Color Matching Synergy
        equipment.insertedChips.forEachIndexed { index, chip ->
            if (chip != null) {
                val socketColor = equipment.socketColors.getOrNull(index)
                val colorMatchMultiplier = when (socketColor) {
                    ChipSocketColor.LOCKED -> 0.0f
                    ChipSocketColor.WHITE_RAINBOW -> 1.25f
                    chip.color -> 1.25f
                    else -> 1.0f
                }
                val effectiveBonus = (chip.statBonusValue * colorMatchMultiplier).toInt()
                val curr = stats.getOrDefault(chip.statBonusType, 0)
                stats[chip.statBonusType] = curr + effectiveBonus
            }
        }

        return stats
    }

    // Preset available Data Chips to insert
    val AVAILABLE_DATA_CHIPS = listOf(
        DataChip("chip_red_atk", "Чип Ядра (Монолит)", ChipSocketColor.RED_MONOLITH, "ATK", 15),
        DataChip("chip_red_hp", "Нейро-Броня (Монолит)", ChipSocketColor.RED_MONOLITH, "HP", 30),
        DataChip("chip_green_crit", "Калибратор Крита (Призрак)", ChipSocketColor.GREEN_GHOST, "CRIT", 12),
        DataChip("chip_blue_energy", "Потоковый Конденсатор (Взлом)", ChipSocketColor.BLUE_HACKER, "ENERGY", 20)
    )
}
