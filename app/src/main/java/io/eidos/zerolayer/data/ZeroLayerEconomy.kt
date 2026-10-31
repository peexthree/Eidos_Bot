package io.eidos.zerolayer.data

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
