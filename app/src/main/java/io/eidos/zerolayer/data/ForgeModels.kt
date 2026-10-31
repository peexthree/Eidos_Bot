package io.eidos.zerolayer.data

data class ForgeRecipeDefinition(
    val targetId: String,
    val shardCost: Int,
    val creditCost: Long,
    val additionalIngredients: Map<String, Int> = emptyMap()
)

object ForgeRecipes {
    val DEFAULT_RECIPES: List<ForgeRecipeDefinition> = listOf(
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
}
