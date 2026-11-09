package io.eidos.zerolayer.ui.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.MainDirectiveEngine
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.ui.theme.EidosCyan

import androidx.compose.ui.platform.LocalContext
import io.eidos.zerolayer.ui.utils.EidosAudioManager

@Composable
fun GoldenThreadCard(
    player: Player?,
    onNavigate: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val activeDirective = remember(player?.raids_done, player?.max_depth, player?.wins_pvp, player?.prestige_count) {
        MainDirectiveEngine.getActiveDirective(player)
    }
    val completedCount = remember(player?.raids_done, player?.max_depth, player?.wins_pvp, player?.prestige_count) {
        MainDirectiveEngine.getCompletedCount(player)
    }
    val totalCount = MainDirectiveEngine.totalCount
    val isAllCompleted = completedCount >= totalCount

    val infiniteTransition = rememberInfiniteTransition(label = "golden_thread_glow")
    val borderAlpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glow_alpha"
    )

    val borderColor = if (isAllCompleted) {
        Color(0xFF00E676).copy(alpha = borderAlpha)
    } else {
        Color(0xFFFFD700).copy(alpha = borderAlpha)
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(topStart = 10.dp, bottomEnd = 10.dp))
            .background(Color(0xFF0A0D1A))
            .border(2.dp, borderColor, CutCornerShape(topStart = 10.dp, bottomEnd = 10.dp))
            .padding(14.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header: EVA-09 Status with Voice replay
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    modifier = Modifier
                        .clip(CutCornerShape(4.dp))
                        .clickable { audio.playEvaDirectiveVoice(activeDirective.id) }
                        .padding(vertical = 2.dp, horizontal = 4.dp)
                ) {
                    Text(
                        text = "// ЕВА-09 :: АКТИВНАЯ ДИРЕКТИВА",
                        color = EidosCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Text("🔊", fontSize = 11.sp)
                }
                Text(
                    text = "${completedCount}/${totalCount}",
                    color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.ExtraBold
                )
            }

            // Title with Icon
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = if (isAllCompleted) "✓" else "⚡",
                    fontSize = 16.sp,
                    color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700)
                )
                Text(
                    text = if (isAllCompleted) "ПРОТОКОЛ ЗАВЕРШЕН // СИНГУЛЯРНОСТЬ ДОСТИГНУТА" else activeDirective.title,
                    color = Color.White,
                    fontSize = 13.5.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }

            // Description / EVA advice
            Text(
                text = if (isAllCompleted) {
                    "Все базовые и сингулярные директивы выполнены. Оператор достиг абсолютного статуса Нулевого Слоя."
                } else {
                    activeDirective.description
                },
                color = Color.LightGray,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                fontFamily = FontFamily.SansSerif
            )

            // Progress bar
            val progress = (completedCount.toFloat() / totalCount.toFloat()).coerceIn(0f, 1f)
            Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(5.dp)
                        .clip(CutCornerShape(2.dp)),
                    color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                    trackColor = Color(0xFF1E2235)
                )
                Text(
                    text = "${completedCount}/${totalCount} ДИРЕКТИВ ВЫПОЛНЕНО",
                    color = Color.Gray,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            // CTA Button
            if (!isAllCompleted) {
                FilledTonalButton(
                    onClick = { onNavigate(activeDirective.targetScreen) },
                    modifier = Modifier.fillMaxWidth(),
                    shape = CutCornerShape(6.dp),
                    colors = ButtonDefaults.filledTonalButtonColors(
                        containerColor = Color(0xFFFFD700),
                        contentColor = Color.Black
                    )
                ) {
                    Text(
                        text = "▶ ${activeDirective.ctaLabel}",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 0.5.sp
                    )
                }
            }
        }
    }
}
