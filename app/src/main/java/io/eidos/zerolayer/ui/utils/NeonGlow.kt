package io.eidos.zerolayer.ui.utils

import android.graphics.BlurMaskFilter
import android.os.Build
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

import androidx.compose.ui.graphics.Shape

@Composable
fun Modifier.neonGlowPulse(
    glowColor: Color = Color(0xFF00E5FF),
    baseWidth: Dp = 2.dp,
    shape: Shape = RoundedCornerShape(12.dp),
    durationMs: Int = 1200
): Modifier {
    val infiniteTransition = rememberInfiniteTransition(label = "NeonGlowPulse")
    val alphaPulse by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMs, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "AlphaPulse"
    )
    val widthPulse by infiniteTransition.animateFloat(
        initialValue = 1.5f,
        targetValue = 3.5f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMs, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "WidthPulse"
    )

    val activeGlowColor = glowColor.copy(alpha = alphaPulse)

    return this.border(
        width = widthPulse.dp,
        brush = Brush.sweepGradient(
            colors = listOf(
                activeGlowColor,
                activeGlowColor.copy(alpha = 0.2f),
                Color.White.copy(alpha = alphaPulse),
                activeGlowColor
            )
        ),
        shape = shape
    )
}

fun Modifier.cyberNeonBorder(
    color: Color,
    cornerRadius: Dp = 10.dp,
    glowRadius: Dp = 12.dp
): Modifier = this.drawWithCache {
    val paint = Paint().asFrameworkPaint().apply {
        isAntiAlias = true
        this.color = color.hashCode()
        maskFilter = BlurMaskFilter(glowRadius.toPx(), BlurMaskFilter.Blur.NORMAL)
    }

    onDrawWithContent {
        drawIntoCanvas { canvas ->
            canvas.drawRoundRect(
                left = 0f,
                top = 0f,
                right = size.width,
                bottom = size.height,
                radiusX = cornerRadius.toPx(),
                radiusY = cornerRadius.toPx(),
                paint = androidx.compose.ui.graphics.Paint().apply {
                    this.asFrameworkPaint().set(paint)
                }
            )
        }
        drawContent()
    }
}
