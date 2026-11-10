package io.eidos.zerolayer.data

/**
 * Единый реестр рецептов КОВКИ ШЕЙДЕРОВ: единственный источник истины
 * и для GameRepository.craftItem (валидация/списание), и для ForgeScreen (UI).
 * Раньше UI держал собственный список из 15 рецептов, а репозиторий - из 10,
 * и списки расходились (для 5 рецептов craftItem брал фолбэк-цены, не совпадающие
 * с показанными в интерфейсе).
 */

/** Категории рецептов для фильтров в UI КОВКИ. */
enum class ForgeRecipeCategory(val label: String) {
    GEAR("ЭКИПИРОВКА"),
    CONSUMABLE("РАСХОДНИКИ"),
    TOOL("ИНСТРУМЕНТЫ")
}

data class ForgeRecipeDefinition(
    val targetId: String,
    val shardCost: Int,
    val creditCost: Long,
    val additionalIngredients: Map<String, Int> = emptyMap(),
    /** Отображаемое имя; если пусто - берется из items.json. */
    val name: String = "",
    val description: String = "",
    val category: ForgeRecipeCategory = ForgeRecipeCategory.GEAR
)

object ForgeRecipeRegistry {

    val ALL: List<ForgeRecipeDefinition> = listOf(
        // === Экипировка ===
        ForgeRecipeDefinition(
            targetId = "reality_silencer", shardCost = 10, creditCost = 2500L,
            additionalIngredients = mapOf("boss_core" to 1),
            name = "Глушитель Реальности", description = "Подавляет искажения пространства"
        ),
        ForgeRecipeDefinition(
            targetId = "death_mask", shardCost = 6, creditCost = 1500L,
            additionalIngredients = mapOf("data_spike" to 1),
            name = "Маска Мертвеца", description = "Смертоносный артефакт Бездны"
        ),
        ForgeRecipeDefinition(
            targetId = "scavenger_mask", shardCost = 4, creditCost = 800L,
            additionalIngredients = mapOf("master_key" to 2),
            name = "Маска Мусорщика", description = "Повышает шанс ценного лута"
        ),
        ForgeRecipeDefinition(
            targetId = "nomad_goggles", shardCost = 5, creditCost = 1000L,
            additionalIngredients = mapOf("compass" to 1),
            name = "Очки Кочевника", description = "Облегчает навигацию по секторам"
        ),
        ForgeRecipeDefinition(
            targetId = "karma_inversion", shardCost = 8, creditCost = 2000L,
            additionalIngredients = mapOf("abyssal_key" to 1),
            name = "Инверсия Кармы", description = "Преобразует урон в щиты"
        ),
        ForgeRecipeDefinition(
            targetId = "holo_poverty", shardCost = 6, creditCost = 1200L,
            name = "Голографическая Нищета", description = "Маскировка от агрессивных программ"
        ),
        ForgeRecipeDefinition(
            targetId = "aegis", shardCost = 5, creditCost = 1000L,
            additionalIngredients = mapOf("battery" to 1),
            name = "Эгида Бессмертия", description = "Спасает от смертельного удара"
        ),
        ForgeRecipeDefinition(
            targetId = "rusty_knife", shardCost = 30, creditCost = 250L,
            name = "Ржавый Тесак", description = "Базовое оружие ближнего боя"
        ),
        ForgeRecipeDefinition(
            targetId = "crowbar", shardCost = 50, creditCost = 500L,
            name = "Монтировка Хакера", description = "Оружие и инструмент"
        ),
        ForgeRecipeDefinition(
            targetId = "hoodie", shardCost = 40, creditCost = 400L,
            name = "Балахон Сквиттера", description = "Легкая защита"
        ),

        // === Расходники ===
        ForgeRecipeDefinition(
            targetId = "medkit_small", shardCost = 15, creditCost = 100L,
            name = "Малая Аптечка", description = "Восстанавливает HP",
            category = ForgeRecipeCategory.CONSUMABLE
        ),
        ForgeRecipeDefinition(
            targetId = "battery", shardCost = 15, creditCost = 100L,
            name = "Энерго-Батарея", description = "Заряжает энергоячейки",
            category = ForgeRecipeCategory.CONSUMABLE
        ),

        // === Инструменты и ключи ===
        ForgeRecipeDefinition(
            targetId = "master_key", shardCost = 20, creditCost = 200L,
            name = "Магнитная Отмычка", description = "Взламывает защищенные контейнеры",
            category = ForgeRecipeCategory.TOOL
        ),
        ForgeRecipeDefinition(
            targetId = "data_spike", shardCost = 25, creditCost = 300L,
            name = "Дата-Шип", description = "Пробивает терминалы",
            category = ForgeRecipeCategory.TOOL
        ),
        ForgeRecipeDefinition(
            targetId = "compass", shardCost = 25, creditCost = 300L,
            name = "Компас Пустоши", description = "Указывает путь к аномалиям",
            category = ForgeRecipeCategory.TOOL
        )
    )

    fun byId(targetId: String): ForgeRecipeDefinition? = ALL.find { it.targetId == targetId }
}
