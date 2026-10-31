package io.eidos.zerolayer.data

import kotlinx.serialization.Serializable

data class ItemMetadata(
    val id: String,
    val name: String,
    val type: String, // weapon, armor, head, chip, consumable, material
    val rarity: String, // common, uncommon, rare, epic, legendary, relic, cursed
    val icon: String = "❓",
    val multiplier: Float = 1.0f,
    val bonusAttack: Int = 0,
    val bonusDefense: Int = 0,
    val bonusLuck: Int = 0,
    val hpRestore: Int = 0,
    val energyRestore: Int = 0,
    val price: Int = 100,
    val description: String = "",
    val reqLevel: Int = 1
)

@Serializable
data class ItemJson(
    val name: String = "Предмет",
    val slot: String = "",
    val type: String = "",
    val atk: Int = 0,
    val def: Int = 0,
    val luck: Int = 0,
    val price: Int = 0,
    val desc: String = ""
)
