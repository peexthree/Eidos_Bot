package com.example.eidos.data

import kotlinx.serialization.Serializable

@Serializable
data class Achievement(
    val title: String,
    val description: String,
    val xpReward: Long = 0,
    val coinReward: Long = 0,
    val icon: String = "🏆",
    val id: String = java.util.UUID.randomUUID().toString(),
    val category: String = "ДОСТИЖЕНИЕ",
    val achievementKey: String = ""
)

@Serializable
data class LootDrop(
    val items: List<InventoryItem>,
    val source: String = "СИСТЕМНЫЙ КЭШ",
    val id: String = java.util.UUID.randomUUID().toString()
)

data class CyberToast(
    val message: String,
    val type: CyberToastType = CyberToastType.INFO,
    val id: Long = System.currentTimeMillis()
)

enum class CyberToastType {
    INFO, SUCCESS, ALERT, DANGER
}
