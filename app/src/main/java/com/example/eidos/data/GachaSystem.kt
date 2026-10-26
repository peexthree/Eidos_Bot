package com.example.eidos.data

import kotlin.random.Random

enum class GachaRarity(val label: String) {
    CURSED("ПРОКЛЯТЫЙ"),
    LEGENDARY("ЛЕГЕНДАРНЫЙ"),
    EPIC("ЭПИЧЕСКИЙ"),
    RARE("РЕДКИЙ"),
    COMMON("ОБЫЧНЫЙ")
}

data class GachaRollResult(
    val item: GameRepository.ItemMetadata,
    val rarity: GachaRarity
)

sealed class GachaResult {
    data class ItemReward(val item: InventoryItem, val metadata: GameRepository.ItemMetadata, val rarityName: String) : GachaResult()
    data class FragmentReward(val count: Int, val totalFragments: Int) : GachaResult()
    data class JunkCodeReward(val xpGained: Long) : GachaResult()
    data class Error(val message: String) : GachaResult()
}

object GachaSystem {
    const val GACHA_COST_BC = 1000L
    const val GACHA_PRICE_BC = 1000L
    const val FRAGMENTS_FOR_SYNTHESIS = 5

    val CURSED_ITEM_IDS = listOf(
        "credit_cutter",
        "banhammer_shard",
        "blood_miner",
        "cursed_ring",
        "void_relic",
        "death_processor",
        "black_hole_generator",
        "entropy_relic",
        "relic_vampire"
    )

    val LEGENDARY_ITEM_IDS = listOf(
        "quantum_blade",
        "eidos_crown",
        "tachyon_core",
        "plasma_rifle",
        "void_armor",
        "hyper_cube",
        "singularity_core",
        "genesis_protocol",
        "overclock_chip",
        "cyber_deck"
    )

    val RARE_CONSUMABLES = listOf(
        "neural_stimulator",
        "emp_grenade",
        "stealth_spray",
        "abyssal_key"
    )

    val BASIC_CONSUMABLES = listOf(
        "battery",
        "compass",
        "master_key",
        "data_spike"
    )

    val LEGENDARY_POOL = listOf(
        GameRepository.ItemMetadata(id = "quantum_blade", name = "Квантовый Клинок", type = "weapon", rarity = "legendary", icon = "⚔️", bonusAttack = 35, bonusLuck = 5, price = 1500, description = "Сверхпрочный клинок из когерентного света", reqLevel = 3),
        GameRepository.ItemMetadata(id = "eidos_crown", name = "Корона Эйдоса", type = "head", rarity = "legendary", icon = "👑", bonusAttack = 15, bonusDefense = 25, bonusLuck = 10, hpRestore = 50, price = 2000, description = "Нейрошлем демиурга системы", reqLevel = 3),
        GameRepository.ItemMetadata(id = "tachyon_core", name = "Тахионный Реактор", type = "chip", rarity = "legendary", icon = "💠", bonusAttack = 20, bonusDefense = 20, bonusLuck = 15, hpRestore = 40, price = 1800, description = "Ядро искривления временных потоков", reqLevel = 2),
        GameRepository.ItemMetadata(id = "plasma_rifle", name = "Плазменная Винтовка", type = "weapon", rarity = "legendary", icon = "🔫", bonusAttack = 40, price = 1600, description = "Тяжелое орудие подавления протоколов", reqLevel = 3),
        GameRepository.ItemMetadata(id = "void_armor", name = "Броня Бездны", type = "armor", rarity = "legendary", icon = "🛡️", bonusDefense = 40, bonusLuck = 5, hpRestore = 60, price = 1700, description = "Нано-костюм из поглощающей материи", reqLevel = 3)
    )

    fun rollGacha(): GachaRollResult {
        val roll = Random.nextInt(100)
        return when {
            roll < 1 -> {
                // 1% Cursed
                val meta = GameRepository.ItemMetadata(id = "relic_vampire", name = "Око Бездны (Вампиризм)", type = "chip", rarity = "cursed", icon = "👁", bonusAttack = 25, bonusDefense = 10, bonusLuck = 15, hpRestore = 30, price = 2500, description = "Проклятый артефакт Бездны. Крадет здоровье врага.", reqLevel = 2)
                GachaRollResult(meta, GachaRarity.CURSED)
            }
            roll < 5 -> {
                // 4% Legendary
                val meta = LEGENDARY_POOL.random()
                GachaRollResult(meta, GachaRarity.LEGENDARY)
            }
            roll < 20 -> {
                // 15% Epic
                val meta = GameRepository.ItemMetadata(id = "nano_armor", name = "Нано-Броня Экзо-Уровня", type = "armor", rarity = "epic", icon = "🦺", bonusDefense = 25, hpRestore = 40, price = 800, description = "Тяжелый композитный защитный экзоскелет", reqLevel = 2)
                GachaRollResult(meta, GachaRarity.EPIC)
            }
            roll < 50 -> {
                // 30% Rare
                val meta = GameRepository.ItemMetadata(id = "abyssal_key", name = "Ключ от Бездны", type = "consumable", rarity = "rare", icon = "🗝", price = 500, description = "100% открывает любой контейнер Бездны")
                GachaRollResult(meta, GachaRarity.RARE)
            }
            else -> {
                // 50% Common / Data fragments
                val meta = GameRepository.ItemMetadata(id = "data_fragment", name = "Фрагмент Данных", type = "material", rarity = "common", icon = "💾", price = 100, description = "Часть исходного кода. 5 штук синтезируются в Легенду.")
                GachaRollResult(meta, GachaRarity.COMMON)
            }
        }
    }
}
