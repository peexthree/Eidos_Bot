package io.eidos.zerolayer.data

data class ForgeRecipeDefinition(
    val targetId: String,
    val shardCost: Int,
    val creditCost: Long,
    val additionalIngredients: Map<String, Int> = emptyMap()
)

object ForgeRecipes {
    fun createRecipe(
        targetId: String,
        shardCost: Int,
        creditCost: Long,
        additionalIngredients: Map<String, Int> = emptyMap()
    ): ForgeRecipeDefinition {
        return ForgeRecipeDefinition(targetId, shardCost, creditCost, additionalIngredients)
    }
}
