package io.eidos.zerolayer.data

import io.eidos.zerolayer.data.GameRepository.ItemMetadata

object ShadowBrokerPrices {
    // Dynamic price multipliers configurable at runtime or via remote config / Supabase
    @Volatile var xpMultiplier: Double = 1.0
    @Volatile var bcMultiplier: Double = 1.0

    fun updateMultipliers(xpMul: Double, bcMul: Double) {
        xpMultiplier = xpMul.coerceIn(0.1, 10.0)
        bcMultiplier = bcMul.coerceIn(0.1, 10.0)
    }

    fun getXpPrice(meta: ItemMetadata): Long {
        val r = meta.rarity.lowercase()
        val isCursedOrRelic = r in listOf("cursed", "relic") || meta.type == "cursed"
        val isLegendary = r == "legendary"
        val isEpicOrChip = r == "epic" || meta.type == "chip"

        val basePrice = when {
            isCursedOrRelic -> 50000L
            isLegendary -> 20000L
            isEpicOrChip -> 8000L
            else -> 3000L
        }
        return (basePrice * xpMultiplier).toLong()
    }

    fun getBcPrice(meta: ItemMetadata): Long {
        val r = meta.rarity.lowercase()
        val isCursedOrRelic = r in listOf("cursed", "relic") || meta.type == "cursed"
        val isLegendary = r == "legendary"
        val isEpicOrChip = r == "epic" || meta.type == "chip"

        val basePrice = when {
            isCursedOrRelic -> 25000L
            isLegendary -> 10000L
            isEpicOrChip -> 4000L
            else -> 1500L
        }
        return (basePrice * bcMultiplier).toLong()
    }
}
