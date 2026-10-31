package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.screens.ShadowBrokerManager
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosRed
import kotlinx.coroutines.delay

@Composable
fun ShadowBrokerCountdownBadge(
    modifier: Modifier = Modifier,
    isAdmin: Boolean = false,
    onStatusChanged: (isActive: Boolean) -> Unit = {}
) {
    var currentTime by remember { mutableLongStateOf(System.currentTimeMillis()) }

    LaunchedEffect(Unit) {
        while (true) {
            delay(1000)
            currentTime = System.currentTimeMillis()
        }
    }

    val isActive = remember(currentTime, isAdmin) {
        val active = ShadowBrokerManager.isBrokerActive(currentTime) || isAdmin
        onStatusChanged(active)
        active
    }

    val timeRemainingMs = remember(currentTime) {
        ShadowBrokerManager.getTimeRemainingMs(currentTime)
    }

    val formattedTime = remember(timeRemainingMs) {
        val totalSec = timeRemainingMs / 1000
        val m = totalSec / 60
        val s = totalSec % 60
        String.format("%02d:%02d", m, s)
    }

    val accentColor = if (isActive) EidosCyan else EidosRed

    Box(
        modifier = modifier
            .background(Color(0xFF0F131A), CutCornerShape(topStart = 4.dp, bottomEnd = 6.dp))
            .border(1.dp, accentColor, CutCornerShape(topStart = 4.dp, bottomEnd = 6.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(
            text = if (isActive) "СЕТЬ: $formattedTime" else "ОФФЛАЙН: $formattedTime",
            color = accentColor,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
    }
}
