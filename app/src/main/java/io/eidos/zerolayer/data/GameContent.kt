package io.eidos.zerolayer.data

import kotlinx.serialization.Serializable

@Serializable
data class VillainData(
    val name: String = "",
    val level: Int = 1,
    val hp: Int = 10,
    val atk: Int = 1,
    val def: Int = 0,
    val xp: Long = 10L,
    val coin: Long = 5L,
    val desc: String = "",
    val image: String? = null
)

@Serializable
data class VillainsRoot(
    val villains: List<VillainData> = emptyList()
)

@Serializable
data class ContentItem(
    val type: String = "info",
    val path: String = "",
    val text: String = ""
)
