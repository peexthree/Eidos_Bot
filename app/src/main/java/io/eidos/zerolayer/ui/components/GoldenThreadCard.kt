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
    modifier: Modifier = Modifier,
    onOpenTutorial: (() -> Unit)? = null,
    onHide: (() -> Unit)? = null
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val isNovice = (player?.raids_done ?: 0) == 0
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
        initialValue = if (isNovice) 0.35f else 0.5f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(if (isNovice) 900 else 1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glow_alpha"
    )

    val borderColor = if (isAllCompleted) {
        Color(0xFF00E676).copy(alpha = borderAlpha)
    } else {
        Color(0xFFFFD700).copy(alpha = borderAlpha)
    }

    val cardShape = CutCornerShape(topStart = 12.dp, bottomEnd = 12.dp, topEnd = 3.dp, bottomStart = 3.dp)
    val borderWidth = if (isNovice) 2.2.dp else 1.5.dp

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(cardShape)
            .background(
                Brush.verticalGradient(
                    listOf(
                        Color(0xF0121A2A),
                        Color(0xF50A101C),
                        Color(0xFA05070E)
                    )
                )
            )
            .border(borderWidth, borderColor, cardShape)
    ) {
        // Studio Glass Top Reflection Sheen
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.5.dp)
                .background(
                    Brush.horizontalGradient(
                        listOf(
                            Color.Transparent,
                            Color.White.copy(alpha = 0.4f),
                            borderColor,
                            Color.Transparent
                        )
                    )
                )
        )

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
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
                    // Pulsing Status Diode
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .clip(androidx.compose.foundation.shape.CircleShape)
                            .background(if (isAllCompleted) Color(0xFF00E676) else EidosCyan)
                    )
                    Text(
                        text = "// ЕВА-09 :: АКТИВНАЯ ДИРЕКТИВА",
                        color = EidosCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.2.sp
                    )
                    Text("🔊", fontSize = 11.sp)
                }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    if (onOpenTutorial != null) {
                        Surface(
                            color = Color(0xFF00394D),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.8f)),
                            modifier = Modifier.clickable { onOpenTutorial() }
                        ) {
                            Text(
                                text = " [ ? ] ",
                                color = EidosCyan,
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                            )
                        }
                    }
                    // Скрыть директиву (для опытных операторов): вернуть можно в Настройках
                    if (onHide != null) {
                        Text(
                            text = "✕",
                            color = Color.Gray,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .clickable { onHide() }
                                .padding(horizontal = 5.dp, vertical = 1.dp)
                        )
                    }
                    Surface(
                        color = borderColor.copy(alpha = 0.15f),
                        shape = CutCornerShape(topStart = 2.dp, bottomEnd = 4.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, borderColor.copy(alpha = 0.5f))
                    ) {
                        Text(
                            text = " ${completedCount}/${totalCount} ",
                            color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.ExtraBold,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                        )
                    }
                }
            }

            // Title with Icon
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(if (isAllCompleted) Color(0x3300E676) else Color(0x33FFD700))
                        .border(1.dp, if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700), CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (isAllCompleted) "✓" else "⚡",
                        fontSize = 13.sp,
                        color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                        fontWeight = FontWeight.Black
                    )
                }
                Text(
                    text = if (isAllCompleted) "ПРОТОКОЛ ЗАВЕРШЕН // СИНГУЛЯРНОСТЬ ДОСТИГНУТА" else activeDirective.title,
                    color = Color.White,
                    fontSize = 13.5.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.3.sp
                )
            }

            // Description / EVA advice
            Text(
                text = if (isAllCompleted) {
                    "Все базовые и сингулярные директивы выполнены. Оператор достиг абсолютного статуса Нулевого Слоя."
                } else {
                    activeDirective.description
                },
                color = Color(0xFFCBD5E1),
                fontSize = 11.5.sp,
                lineHeight = 16.sp,
                fontFamily = FontFamily.SansSerif
            )

            // Progress bar with high-tech track
            val progress = (completedCount.toFloat() / totalCount.toFloat()).coerceIn(0f, 1f)
            Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(CutCornerShape(3.dp)),
                    color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                    trackColor = Color(0xFF161F30)
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "${completedCount}/${totalCount} ВЫПОЛНЕНО",
                        color = Color(0xFF94A3B8),
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${(progress * 100).toInt()}% СИНХРОНИЗАЦИИ",
                        color = if (isAllCompleted) Color(0xFF00E676) else Color(0xFFFFD700),
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // CTA Button with AAA studio styling
            if (!isAllCompleted) {
                Button(
                    onClick = { onNavigate(activeDirective.targetScreen) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(44.dp),
                    shape = CutCornerShape(topStart = 4.dp, bottomEnd = 8.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFFFFD700),
                        contentColor = Color(0xFF0B0E14)
                    ),
                    elevation = ButtonDefaults.buttonElevation(defaultElevation = 4.dp)
                ) {
                    Text(
                        text = "▶  ${activeDirective.ctaLabel}",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 1.sp
                    )
                }
            }
        }
    }
}
