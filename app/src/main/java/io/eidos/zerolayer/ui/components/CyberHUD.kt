package io.eidos.zerolayer.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.theme.*
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun Modifier.cyberClickable(
    enabled: Boolean = true,
    onClick: () -> Unit
): Modifier {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.96f else 1.0f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessLow),
        label = "cyberClickScale"
    )

    return this
        .graphicsLayer {
            scaleX = scale
            scaleY = scale
        }
        .clickable(
            interactionSource = interactionSource,
            indication = null,
            enabled = enabled,
            onClick = onClick
        )
}

fun Modifier.cyberHudBorder(
    color: Color = EidosCyan,
    cornerLength: Dp = 10.dp,
    strokeWidth: Dp = 1.5.dp
) = this.drawWithCache {
    val cornerPx = cornerLength.toPx()
    val strokePx = strokeWidth.toPx()
    val width = size.width
    val height = size.height

    onDrawWithContent {
        drawContent()

        // Sleek cyber corner brackets
        // Top-Left
        drawLine(color, Offset(0f, 0f), Offset(cornerPx, 0f), strokePx)
        drawLine(color, Offset(0f, 0f), Offset(0f, cornerPx), strokePx)

        // Top-Right
        drawLine(color, Offset(width - cornerPx, 0f), Offset(width, 0f), strokePx)
        drawLine(color, Offset(width, 0f), Offset(width, cornerPx), strokePx)

        // Bottom-Left
        drawLine(color, Offset(0f, height), Offset(cornerPx, height), strokePx)
        drawLine(color, Offset(0f, height - cornerPx), Offset(0f, height), strokePx)

        // Bottom-Right
        drawLine(color, Offset(width - cornerPx, height), Offset(width, height), strokePx)
        drawLine(color, Offset(width, height - cornerPx), Offset(width, height), strokePx)
    }
}

@Composable
fun CyberCard(
    modifier: Modifier = Modifier,
    borderColor: Color = EidosCyan,
    backgroundColor: Color = EidosGlass,
    headerText: String? = null,
    headerIcon: ImageVector? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        backgroundColor.copy(alpha = 0.95f),
                        Color(0xFF070B12).copy(alpha = 0.98f)
                    )
                ),
                RoundedCornerShape(10.dp)
            )
            .border(1.dp, borderColor.copy(alpha = 0.35f), RoundedCornerShape(10.dp))
            .cyberHudBorder(color = borderColor.copy(alpha = 0.7f), cornerLength = 8.dp, strokeWidth = 1.5.dp)
            .padding(14.dp)
    ) {
        Column {
            if (headerText != null) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        if (headerIcon != null) {
                            Icon(
                                imageVector = headerIcon,
                                contentDescription = null,
                                tint = borderColor,
                                modifier = Modifier.size(14.dp)
                            )
                        }
                        Text(
                            text = headerText.uppercase(),
                            color = borderColor,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 0.8.sp
                        )
                    }
                    Box(
                        modifier = Modifier
                            .size(5.dp)
                            .clip(CircleShape)
                            .background(borderColor)
                    )
                }
            }
            content()
        }
    }
}

@Composable
fun AnimatedCyberProgressBar(
    progress: Float,
    modifier: Modifier = Modifier,
    color: Color = EidosNeon,
    trackColor: Color = Color(0xFF0E1724),
    height: Dp = 6.dp,
    label: String? = null,
    valueText: String? = null,
    icon: ImageVector? = null
) {
    val animatedProgress by animateFloatAsState(
        targetValue = progress.coerceIn(0f, 1f),
        animationSpec = spring(stiffness = Spring.StiffnessLow),
        label = "cyberProgress"
    )

    Column(modifier = modifier) {
        if (label != null || valueText != null) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    if (icon != null) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = color.copy(alpha = 0.8f),
                            modifier = Modifier.size(12.dp)
                        )
                    }
                    if (label != null) {
                        Text(
                            text = label,
                            color = Color(0xFF90A4AE),
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
                if (valueText != null) {
                    Text(
                        text = valueText,
                        color = color,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(height)
                .clip(RoundedCornerShape(3.dp))
                .background(trackColor)
                .border(0.5.dp, color.copy(alpha = 0.25f), RoundedCornerShape(3.dp))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth(animatedProgress)
                    .clip(RoundedCornerShape(3.dp))
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(
                                color.copy(alpha = 0.6f),
                                color
                            )
                        )
                    )
            )
        }
    }
}

@Composable
fun CyberGridOverlay(
    modifier: Modifier = Modifier,
    lineColor: Color = EidosCyan.copy(alpha = 0.04f)
) {
    val infiniteTransition = rememberInfiniteTransition(label = "scanline")
    val scanlineY by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(5000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "scanlineY"
    )

    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height
        val stepPx = 36.dp.toPx()

        // Subtle grid lines
        var x = 0f
        while (x <= width) {
            drawLine(
                color = lineColor,
                start = Offset(x, 0f),
                end = Offset(x, height),
                strokeWidth = 0.75f
            )
            x += stepPx
        }

        var y = 0f
        while (y <= height) {
            drawLine(
                color = lineColor,
                start = Offset(0f, y),
                end = Offset(width, y),
                strokeWidth = 0.75f
            )
            y += stepPx
        }

        // Soft laser scanline
        val currentScanY = height * scanlineY
        drawLine(
            brush = Brush.horizontalGradient(
                colors = listOf(
                    Color.Transparent,
                    EidosCyan.copy(alpha = 0.12f),
                    EidosCyan.copy(alpha = 0.25f),
                    EidosCyan.copy(alpha = 0.12f),
                    Color.Transparent
                )
            ),
            start = Offset(0f, currentScanY),
            end = Offset(width, currentScanY),
            strokeWidth = 2.dp.toPx()
        )
    }
}

@Composable
fun RadarScanView(
    modifier: Modifier = Modifier,
    color: Color = EidosRed
) {
    val infiniteTransition = rememberInfiniteTransition(label = "radar")
    val angle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2400, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "angle"
    )

    Canvas(modifier = modifier.fillMaxSize()) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val radius = minOf(size.width, size.height) / 2.2f

        drawCircle(color = color.copy(alpha = 0.2f), radius = radius, center = center, style = Stroke(width = 1.dp.toPx()))
        drawCircle(color = color.copy(alpha = 0.12f), radius = radius * 0.66f, center = center, style = Stroke(width = 1.dp.toPx()))
        drawCircle(color = color.copy(alpha = 0.08f), radius = radius * 0.33f, center = center, style = Stroke(width = 1.dp.toPx()))

        drawLine(color = color.copy(alpha = 0.15f), start = Offset(center.x - radius, center.y), end = Offset(center.x + radius, center.y))
        drawLine(color = color.copy(alpha = 0.15f), start = Offset(center.x, center.y - radius), end = Offset(center.x, center.y + radius))

        val rad = Math.toRadians(angle.toDouble())
        val sweepEnd = Offset(
            x = center.x + (radius * cos(rad)).toFloat(),
            y = center.y + (radius * sin(rad)).toFloat()
        )
        drawLine(color = color.copy(alpha = 0.8f), start = center, end = sweepEnd, strokeWidth = 2.dp.toPx())

        val blip1 = Offset(center.x + radius * 0.4f, center.y - radius * 0.3f)
        val blip2 = Offset(center.x - radius * 0.5f, center.y + radius * 0.4f)
        drawCircle(color = EidosNeon, radius = 3.5.dp.toPx(), center = blip1)
        drawCircle(color = EidosGold, radius = 4.dp.toPx(), center = blip2)
    }
}

@Composable
fun CyberGlassCard(
    modifier: Modifier = Modifier,
    borderColor: Color = EidosCyan,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF101926).copy(alpha = 0.92f),
                        Color(0xFF070B12).copy(alpha = 0.98f)
                    )
                ),
                RoundedCornerShape(12.dp)
            )
            .border(1.dp, borderColor.copy(alpha = 0.35f), RoundedCornerShape(12.dp))
            .cyberHudBorder(color = borderColor.copy(alpha = 0.6f), cornerLength = 10.dp, strokeWidth = 1.5.dp)
            .padding(14.dp)
    ) {
        Column(content = content)
    }
}

@Composable
fun OperatorRadialHUD(
    hpPercent: Float,
    energyPercent: Float,
    corruptionPercent: Float,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.size(110.dp),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val stroke = 5.dp.toPx()

            // Outer Corruption Ring
            drawArc(
                color = EidosRed.copy(alpha = 0.7f),
                startAngle = -90f,
                sweepAngle = 360f * corruptionPercent.coerceIn(0f, 1f),
                useCenter = false,
                style = Stroke(width = stroke, cap = StrokeCap.Round)
            )

            // Middle Energy Ring
            drawArc(
                color = EidosCyan.copy(alpha = 0.85f),
                startAngle = -90f,
                sweepAngle = 360f * energyPercent.coerceIn(0f, 1f),
                useCenter = false,
                style = Stroke(width = stroke - 1.dp.toPx(), cap = StrokeCap.Round)
            )

            // Inner HP Ring
            drawArc(
                color = EidosNeon,
                startAngle = -90f,
                sweepAngle = 360f * hpPercent.coerceIn(0f, 1f),
                useCenter = false,
                style = Stroke(width = stroke - 2.dp.toPx(), cap = StrokeCap.Round)
            )
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                "СТАТУС",
                color = EidosCyanDim,
                fontSize = 8.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold
            )
            Text(
                "${(hpPercent * 100).toInt()}%",
                color = EidosNeon,
                fontSize = 15.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Black
            )
            Text(
                "СКВ: ${(corruptionPercent * 100).toInt()}%",
                color = EidosRed,
                fontSize = 8.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

enum class BadgeType { SUCCESS, WARNING, DANGER, INFO }

@Composable
fun SemanticBadge(
    text: String,
    type: BadgeType,
    modifier: Modifier = Modifier
) {
    val color = when (type) {
        BadgeType.SUCCESS -> EidosNeon
        BadgeType.WARNING -> EidosGold
        BadgeType.DANGER -> EidosRed
        BadgeType.INFO -> EidosCyan
    }

    Box(
        modifier = modifier
            .background(color.copy(alpha = 0.12f), RoundedCornerShape(4.dp))
            .border(0.75.dp, color.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(
            text = text.uppercase(),
            color = color,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 0.5.sp
        )
    }
}

@Composable
fun CyberToastNotification(
    message: String,
    type: BadgeType = BadgeType.INFO,
    modifier: Modifier = Modifier
) {
    val color = when (type) {
        BadgeType.SUCCESS -> EidosNeon
        BadgeType.WARNING -> EidosGold
        BadgeType.DANGER -> EidosRed
        BadgeType.INFO -> EidosCyan
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFF0B111A).copy(alpha = 0.96f), RoundedCornerShape(8.dp))
            .border(1.dp, color.copy(alpha = 0.6f), RoundedCornerShape(8.dp))
            .padding(12.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .clip(CircleShape)
                    .background(color.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = when (type) {
                        BadgeType.SUCCESS -> "✓"
                        BadgeType.WARNING -> "!"
                        BadgeType.DANGER -> "✕"
                        BadgeType.INFO -> "i"
                    },
                    color = color,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Text(
                text = message,
                color = Color.White,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                lineHeight = 15.sp
            )
        }
    }
}

@Composable
fun CyberSkeletonLoader(
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "skeleton")
    val alphaAnim by infiniteTransition.animateFloat(
        initialValue = 0.2f,
        targetValue = 0.6f,
        animationSpec = infiniteRepeatable(
            animation = tween(900, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "skeletonAlpha"
    )

    Box(
        modifier = modifier
            .background(EidosCyan.copy(alpha = alphaAnim * 0.15f), RoundedCornerShape(8.dp))
            .border(1.dp, EidosCyan.copy(alpha = alphaAnim * 0.4f), RoundedCornerShape(8.dp))
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            "СИНХРОНИЗАЦИЯ С ЕЙДОСОМ...",
            color = EidosCyan.copy(alpha = alphaAnim + 0.3f),
            fontSize = 10.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold
        )
    }
}

