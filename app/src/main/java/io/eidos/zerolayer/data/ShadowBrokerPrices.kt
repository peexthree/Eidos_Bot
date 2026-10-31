package io.eidos.zerolayer.data

object ShadowBrokerPrices {
    fun getXpPrice(meta: ItemMetadata): Long {
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

    fun getBcPrice(meta: ItemMetadata): Long {
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
