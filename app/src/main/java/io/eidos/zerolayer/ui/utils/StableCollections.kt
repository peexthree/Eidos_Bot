package io.eidos.zerolayer.ui.utils

import androidx.compose.runtime.Immutable

@Immutable
data class ImmutableListWrapper<T>(
    val items: List<T> = emptyList()
) {
    val size: Int get() = items.size
    operator fun get(index: Int): T = items[index]
    fun isEmpty(): Boolean = items.isEmpty()
    fun isNotEmpty(): Boolean = items.isNotEmpty()
}

fun <T> List<T>.toImmutableWrapper(): ImmutableListWrapper<T> = ImmutableListWrapper(this)
