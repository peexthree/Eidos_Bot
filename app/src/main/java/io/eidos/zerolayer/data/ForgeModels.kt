package io.eidos.zerolayer.data

typealias ForgeRecipeDefinition = GameRepository.ForgeRecipeDefinition

object ForgeRecipes {
    fun createRecipe(
        targetId: String,
        shardCost: Int,
        creditCost: Long,
        additionalIngredients: Map<String, Int> = emptyMap()
    ): ForgeRecipeDefinition {
        return GameRepository.ForgeRecipeDefinition(targetId, shardCost, creditCost, additionalIngredients)
    }
}
