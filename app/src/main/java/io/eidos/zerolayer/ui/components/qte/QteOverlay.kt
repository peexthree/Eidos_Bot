package io.eidos.zerolayer.ui.components.qte

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.domain.qte.ActiveQte
import io.eidos.zerolayer.domain.qte.QteEngine
import io.eidos.zerolayer.domain.qte.QteType
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.ZzzDangerRed
import io.eidos.zerolayer.ui.theme.ZzzGold
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import kotlin.math.abs
import kotlin.random.Random
import kotlinx.coroutines.delay

/**
 * QTE-вставка спуска: полноэкранный оверлей с окном реакции.
 * Жесты: тап-тайминг (СТАБИЛИЗАЦИЯ), свайп по стрелке (УКЛОНЕНИЕ),
 * тап по маркерам (ГЛИТЧ-СРЫВ). Результат уходит в MainViewModel ->
 * GameRepository.applyQteResult (UI экономику не трогает).
 */
@Composable
fun QteOverlay(
    qte: ActiveQte,
    onResolve: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val haptics = remember { HapticFeedbackManager.getInstance(context) }

    // 0 = активна, 1 = успех, -1 = провал
    var phase by remember(qte.id) { mutableStateOf(0) }

    fun finish(success: Boolean) {
        if (phase != 0) return
        phase = if (success) 1 else -1
        if (success) {
            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
            haptics.criticalHit()
        } else {
            audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
            haptics.glitchPulse()
        }
    }

    // Автопровал по таймауту
    LaunchedEffect(qte.id) {
        delay(qte.timeoutMs)
        finish(false)
    }
    // Вспышка результата, затем колбэк (ViewModel гасит оверлей)
    LaunchedEffect(phase) {
        if (phase != 0) {
            delay(QteEngine.RESULT_FLASH_MS)
            onResolve(phase > 0)
        }
    }

    // Таймер-бар: 1f -> 0f за окно реакции
    val timeLeft = remember(qte.id) { Animatable(1f) }
    LaunchedEffect(qte.id) {
        timeLeft.animateTo(0f, tween(qte.timeoutMs.toInt(), easing = LinearEasing))
    }

    val pulseAlpha by rememberInfiniteTransition(label = "qtePulse").animateFloat(
        initialValue = 0.55f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(420), RepeatMode.Reverse),
        label = "qtePulseAlpha"
    )
    val borderColor = when {
        phase > 0 -> EidosNeon
        phase < 0 -> ZzzDangerRed
        else -> EidosCyan.copy(alpha = pulseAlpha)
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = if (phase == 0) 0.72f else 0.86f))
            .pointerInput(qte.id) { detectTapGestures { } } // абсорбер касаний к нижнему UI
    ) {
        Column(
            modifier = Modifier
                .align(Alignment.Center)
                .width(320.dp)
                .clip(CutCornerShape(10.dp))
                .background(Color(0xF20A121D))
                .border(1.6.dp, borderColor, CutCornerShape(10.dp))
                .padding(14.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                "[ПЕРЕХВАТ // QTE]",
                color = ZzzGold,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp
            )
            Spacer(Modifier.height(3.dp))
            Text(
                qte.type.title,
                color = Color.White,
                fontSize = 13.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Text(
                "ГЛУБИНА ${qte.depth}М",
                color = Color.Gray,
                fontSize = 8.sp,
                fontFamily = FontFamily.Monospace
            )
            Spacer(Modifier.height(10.dp))

            Box(modifier = Modifier.fillMaxWidth().height(130.dp)) {
                when (qte.type) {
                    QteType.STABILIZE -> StabilizeWidget(
                        qte = qte,
                        active = phase == 0,
                        onResult = { finish(it) }
                    )
                    QteType.DODGE -> DodgeWidget(
                        qte = qte,
                        active = phase == 0,
                        onResult = { finish(it) }
                    )
                    QteType.GLITCH_PURGE -> GlitchPurgeWidget(
                        qte = qte,
                        active = phase == 0,
                        onResult = { finish(it) }
                    )
                }
            }

            Spacer(Modifier.height(10.dp))
            Text(
                qte.type.instruction,
                color = Color(0xFF9FB3C8),
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                textAlign = TextAlign.Center
            )
            Spacer(Modifier.height(8.dp))

            // Окно реакции
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(CutCornerShape(3.dp))
                    .background(Color(0xFF1E2A3A))
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxHeight()
                        .fillMaxWidth(timeLeft.value.coerceIn(0f, 1f))
                        .clip(CutCornerShape(3.dp))
                        .background(if (timeLeft.value > 0.3f) EidosCyan else ZzzDangerRed)
                )
            }
        }

        // Вспышка результата
        if (phase != 0) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = if (phase > 0) "ПЕРЕХВАЧЕНО" else "СРЫВ",
                    color = if (phase > 0) EidosNeon else ZzzDangerRed,
                    fontSize = 30.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}

// --- СТАБИЛИЗАЦИЯ: тап, когда бегущий маркер в целевой зоне ---

@Composable
private fun StabilizeWidget(qte: ActiveQte, active: Boolean, onResult: (Boolean) -> Unit) {
    val rng = remember(qte.seed) { Random(qte.seed) }
    val zoneStart = remember(qte.seed) { 0.16f + rng.nextFloat() * 0.62f }
    val zoneSize = 0.18f
    val sweep = rememberInfiniteTransition(label = "qteSweep")
    val markerPos by sweep.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(820, easing = LinearEasing), RepeatMode.Reverse),
        label = "qteMarker"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(qte.id) {
                detectTapGestures {
                    if (active) onResult(markerPos in zoneStart..(zoneStart + zoneSize))
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxWidth().height(30.dp)) {
            val w = size.width
            val h = size.height
            // Базовая линия
            drawLine(
                color = Color(0xFF223146),
                start = Offset(0f, h / 2f),
                end = Offset(w, h / 2f),
                strokeWidth = 4f
            )
            // Целевая зона
            drawRoundRect(
                color = EidosNeon.copy(alpha = 0.28f),
                topLeft = Offset(w * zoneStart, 0f),
                size = Size(w * zoneSize, h),
                cornerRadius = CornerRadius(6f, 6f)
            )
            drawRoundRect(
                color = EidosNeon,
                topLeft = Offset(w * zoneStart, 0f),
                size = Size(w * zoneSize, h),
                cornerRadius = CornerRadius(6f, 6f),
                style = Stroke(width = 2f)
            )
            // Бегущий маркер
            drawLine(
                color = Color.White,
                start = Offset(w * markerPos, 0f),
                end = Offset(w * markerPos, h),
                strokeWidth = 5f
            )
        }
    }
}

// --- УКЛОНЕНИЕ: свайп в направлении показанной стрелки ---

private enum class DodgeDir(val icon: ImageVector, val label: String) {
    UP(Icons.Default.ArrowUpward, "ВВЕРХ"),
    DOWN(Icons.Default.ArrowDownward, "ВНИЗ"),
    LEFT(Icons.AutoMirrored.Filled.ArrowBack, "ВЛЕВО"),
    RIGHT(Icons.AutoMirrored.Filled.ArrowForward, "ВПРАВО")
}

@Composable
private fun DodgeWidget(qte: ActiveQte, active: Boolean, onResult: (Boolean) -> Unit) {
    val dir = remember(qte.seed) { DodgeDir.entries[Random(qte.seed).nextInt(DodgeDir.entries.size)] }
    var dragConsumed by remember(qte.id) { mutableStateOf(false) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(qte.id) {
                detectDragGestures { change, dragAmount ->
                    change.consume()
                    if (!active || dragConsumed) return@detectDragGestures
                    val threshold = 52.dp.toPx()
                    val dx = dragAmount.x
                    val dy = dragAmount.y
                    if (abs(dx) < threshold && abs(dy) < threshold) return@detectDragGestures
                    dragConsumed = true
                    val success = if (abs(dx) >= abs(dy)) {
                        (dir == DodgeDir.RIGHT && dx > 0) || (dir == DodgeDir.LEFT && dx < 0)
                    } else {
                        (dir == DodgeDir.DOWN && dy > 0) || (dir == DodgeDir.UP && dy < 0)
                    }
                    onResult(success)
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = dir.icon,
            contentDescription = dir.label,
            tint = EidosCyan,
            modifier = Modifier.size(62.dp)
        )
        Spacer(Modifier.height(0.dp))
        Text(
            dir.label,
            color = Color.White,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
    }
}

// --- ГЛИТЧ-СРЫВ: погасить 4 маркера до распада ---

@Composable
private fun GlitchPurgeWidget(qte: ActiveQte, active: Boolean, onResult: (Boolean) -> Unit) {
    val markers = remember(qte.seed) {
        val r = Random(qte.seed)
        List(4) {
            Pair(0.06f + r.nextFloat() * 0.76f, 0.06f + r.nextFloat() * 0.62f)
        }
    }
    val cleared = remember(qte.seed) { mutableStateListOf(false, false, false, false) }
    val pulseAlpha by rememberInfiniteTransition(label = "qteGlitch").animateFloat(
        initialValue = 0.45f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(tween(300), RepeatMode.Reverse),
        label = "qteGlitchAlpha"
    )

    BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
        markers.forEachIndexed { i, (fx, fy) ->
            if (!cleared[i]) {
                Box(
                    modifier = Modifier
                        .offset(x = maxWidth * fx, y = maxHeight * fy)
                        .size(46.dp)
                        .alpha(pulseAlpha)
                        .clip(CircleShape)
                        .background(ZzzDangerRed.copy(alpha = 0.22f))
                        .border(1.6.dp, ZzzDangerRed, CircleShape)
                        .clickable(enabled = active) {
                            cleared[i] = true
                            if (cleared.all { it }) onResult(true)
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Text("✖", color = ZzzDangerRed, fontSize = 16.sp, fontWeight = FontWeight.Black)
                }
            }
        }
        Text(
            "ЦЕЛИ: ${cleared.count { !it }}/4",
            color = Color.Gray,
            fontSize = 8.sp,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
    }
}
