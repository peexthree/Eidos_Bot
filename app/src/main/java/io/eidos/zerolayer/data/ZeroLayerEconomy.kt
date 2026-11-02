package io.eidos.zerolayer.data

object ZeroLayerEconomy {
    const val SAFE_EXTRACTION_TAX_PERCENT = 8 // 8% Extraction tax rate

    /**
     * Repair fee per 1% lost durability in BioCoins:
     * Common = 1 BC, Uncommon = 2 BC, Rare = 3 BC, Epic = 8 BC, Legendary = 20 BC, Cursed/Relic = 40 BC.
     */
    fun calculateRepairFee(missingDurability: Float, rarity: String): Long {
        if (missingDurability <= 0.05f) return 0L
        val ratePerPercent = when (rarity.lowercase()) {
            "uncommon" -> 2L
            "rare" -> 3L
            "epic" -> 8L
            "legendary" -> 20L
            "cursed", "relic" -> 40L
            else -> 1L // Common
        }
        return (missingDurability * ratePerPercent).toLong().coerceAtLeast(1L)
    }

    /**
     * Repair cost in Eidos Shards for +25% durability:
     * Common/Uncommon = 1 shard, Rare = 2 shards, Epic = 3 shards, Legendary = 4 shards, Cursed/Relic = 5 shards.
     */
    fun calculateShardRepairCost(rarity: String): Int {
        return when (rarity.lowercase()) {
            "common", "uncommon" -> 1
            "rare" -> 2
            "epic" -> 3
            "legendary" -> 4
            "cursed", "relic" -> 5
            else -> 1
        }
    }

    fun calculateExtractionTax(bufferCoins: Long): Long {
        return (bufferCoins * (SAFE_EXTRACTION_TAX_PERCENT / 100.0)).toLong()
    }

    fun calculateRerollCost(rarity: String): Pair<Long, Int> {
        val bcCost = when (rarity.lowercase()) {
            "rare" -> 250L
            "epic" -> 500L
            "legendary" -> 1000L
            "cursed", "relic" -> 2000L
            else -> 100L
        }
        val shardCost = if (rarity.lowercase() in listOf("legendary", "cursed", "relic")) 2 else 1
        return Pair(bcCost, shardCost)
    }

    /**
     * Slicer lock surcharges:
     * 1 locked affix: +50% BC and 1 Eidos Shard
     * 2 locked affixes: +150% BC and 3 Eidos Shards
     */
    fun calculateSlicerLockCost(baseCost: Long, lockedCount: Int): Pair<Long, Int> {
        return when (lockedCount) {
            1 -> Pair((baseCost * 1.5).toLong(), 1)
            2 -> Pair((baseCost * 2.5).toLong(), 3)
            else -> Pair(baseCost, 0)
        }
    }
}
