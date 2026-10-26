package io.eidos.zerolayer.ui.utils

import androidx.compose.runtime.*
import kotlinx.coroutines.delay

@Composable
fun ghostTyping(text: String, speed: Long = 30, onComplete: () -> Unit = {}): String {
    var currentIndex by remember(text) { mutableStateOf(0) }
    
    LaunchedEffect(text) {
        currentIndex = 0
        while (currentIndex < text.length) {
            delay(speed)
            currentIndex++
        }
        onComplete()
    }
    
    return remember(text, currentIndex) { text.take(currentIndex) }
}
