package io.eidos.zerolayer.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class EconomyAndCraftTest {

    @Test
    fun testZeroLayerEconomyExtractionTax() {
        // Tax rate is 8%
        assertEquals(0L, ZeroLayerEconomy.calculateExtractionTax(0L))
        assertEquals(8L, ZeroLayerEconomy.calculateExtractionTax(100L))
        assertEquals(80L, ZeroLayerEconomy.calculateExtractionTax(1000L))
    }

    @Test
    fun testZeroLayerEconomyRepairFee() {
        // Negligible damage under 5% should be 0
        assertEquals(0L, ZeroLayerEconomy.calculateRepairFee(0.04f, "common"))

        // Common rarity: missing 50% = 50 * 2 * 1.0 = 100 BC
        assertEquals(100L, ZeroLayerEconomy.calculateRepairFee(50.0f, "common"))

        // Legendary rarity: missing 50% = 50 * 2 * 4.0 = 400 BC
        assertEquals(400L, ZeroLayerEconomy.calculateRepairFee(50.0f, "legendary"))

        // Cursed rarity: missing 10% = 10 * 2 * 6.0 = 120 BC
        assertEquals(120L, ZeroLayerEconomy.calculateRepairFee(10.0f, "cursed"))
    }

    @Test
    fun testZeroLayerEconomyRerollCost() {
        val (rareBc, rareShards) = ZeroLayerEconomy.calculateRerollCost("rare")
        assertEquals(250L, rareBc)
        assertEquals(1, rareShards)

        val (legBc, legShards) = ZeroLayerEconomy.calculateRerollCost("legendary")
        assertEquals(1000L, legBc)
        assertEquals(2, legShards)

        val (cursedBc, cursedShards) = ZeroLayerEconomy.calculateRerollCost("cursed")
        assertEquals(2000L, cursedBc)
        assertEquals(2, cursedShards)
    }

    @Test
    fun testShadowBrokerPricing() {
        val commonItem = ItemMetadata(id = "knife", name = "Нож", type = "weapon", rarity = "common")
        val epicChip = ItemMetadata(id = "chip_v1", name = "Чип", type = "chip", rarity = "epic")
        val legendaryGun = ItemMetadata(id = "plasma", name = "Плазма 🟠", type = "weapon", rarity = "legendary")
        val cursedRelic = ItemMetadata(id = "skull", name = "Череп 💀", type = "cursed", rarity = "cursed")

        // XP Prices
        assertEquals(3000L, ShadowBrokerPrices.getXpPrice(commonItem))
        assertEquals(8000L, ShadowBrokerPrices.getXpPrice(epicChip))
        assertEquals(20000L, ShadowBrokerPrices.getXpPrice(legendaryGun))
        assertEquals(50000L, ShadowBrokerPrices.getXpPrice(cursedRelic))

        // BioCoin Prices
        assertEquals(1500L, ShadowBrokerPrices.getBcPrice(commonItem))
        assertEquals(4000L, ShadowBrokerPrices.getBcPrice(epicChip))
        assertEquals(10000L, ShadowBrokerPrices.getBcPrice(legendaryGun))
        assertEquals(25000L, ShadowBrokerPrices.getBcPrice(cursedRelic))
    }

    @Test
    fun testForgeRecipesDefaultList() {
        val recipes = ForgeRecipes.DEFAULT_RECIPES
        assertTrue(recipes.isNotEmpty())

        val silencer = recipes.find { it.targetId == "reality_silencer" }
        assertNotNull(silencer)
        assertEquals(10, silencer?.shardCost)
        assertEquals(2500L, silencer?.creditCost)
        assertEquals(1, silencer?.additionalIngredients?.get("boss_core"))
    }
}
