package io.eidos.zerolayer.data

typealias ForgeRecipeDefinition = GameRepository.ForgeRecipeDefinition

object ForgeRecipes {
    val DEFAULT_RECIPES: List<ForgeRecipeDefinition> = listOf(
        GameRepository.ForgeRecipeDefinition("reality_silencer", shardCost = 10, creditCost = 2500L, additionalIngredients = mapOf("boss_core" to 1)),
        GameRepository.ForgeRecipeDefinition("death_mask", shardCost = 6, creditCost = 1500L, additionalIngredients = mapOf("data_spike" to 1)),
        GameRepository.ForgeRecipeDefinition("scavenger_mask", shardCost = 4, creditCost = 800L, additionalIngredients = mapOf("master_key" to 2)),
        GameRepository.ForgeRecipeDefinition("nomad_goggles", shardCost = 5, creditCost = 1000L, additionalIngredients = mapOf("compass" to 1)),
        GameRepository.ForgeRecipeDefinition("karma_inversion", shardCost = 8, creditCost = 2000L, additionalIngredients = mapOf("abyssal_key" to 1)),
        GameRepository.ForgeRecipeDefinition("holo_poverty", shardCost = 6, creditCost = 1200L, additionalIngredients = emptyMap()),
        GameRepository.ForgeRecipeDefinition("aegis", shardCost = 5, creditCost = 1000L, additionalIngredients = mapOf("battery" to 1)),
        GameRepository.ForgeRecipeDefinition("medkit_small", shardCost = 15, creditCost = 100L),
        GameRepository.ForgeRecipeDefinition("battery", shardCost = 15, creditCost = 100L),
        GameRepository.ForgeRecipeDefinition("rusty_knife", shardCost = 30, creditCost = 250L),
        GameRepository.ForgeRecipeDefinition("crowbar", shardCost = 50, creditCost = 500L),
        GameRepository.ForgeRecipeDefinition("hoodie", shardCost = 40, creditCost = 400L),
        GameRepository.ForgeRecipeDefinition("master_key", shardCost = 20, creditCost = 200L),
        GameRepository.ForgeRecipeDefinition("data_spike", shardCost = 25, creditCost = 300L),
        GameRepository.ForgeRecipeDefinition("compass", shardCost = 25, creditCost = 300L)
    )
}
