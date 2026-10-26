package io.eidos.zerolayer.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.ui.theme.*

/**
 * ZZZ Vibrant Urban Cyberpunk Screen Container wrapper.
 */
@Composable
fun ZzzScreenContainer(
    modifier: Modifier = Modifier,
    showCyberGrid: Boolean = true,
    content: @Composable BoxScope.() -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(ZzzObsidian)
    ) {
        if (showCyberGrid) {
            ZzzCyberGridCanvas(modifier = Modifier.fillMaxSize())
        }
        content()
    }
}

@Composable
fun ZzzCyberGridCanvas(modifier: Modifier = Modifier) {
    val infiniteTransition = rememberInfiniteTransition(label = "grid_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.12f,
        targetValue = 0.28f,
        animationSpec = infiniteRepeatable(
            animation = tween(3000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height

        // Radial dark gradient overlay
        drawRect(
            brush = Brush.radialGradient(
                colors = listOf(Color(0xFF141A24), ZzzObsidian),
                center = Offset(width * 0.5f, height * 0.35f),
                radius = width * 1.1f
            )
        )

        // Diagonal lines
        val step = 50f
        var x = -height
        while (x < width + height) {
            drawLine(
                color = ZzzElectricCyan.copy(alpha = pulseAlpha * 0.2f),
                start = Offset(x, 0f),
                end = Offset(x + height, height),
                strokeWidth = 1f
            )
            x += step
        }

        // Reverse slash accents
        var rx = -height
        while (rx < width + height) {
            drawLine(
                color = ZzzHotMagenta.copy(alpha = pulseAlpha * 0.12f),
                start = Offset(rx + height, 0f),
                end = Offset(rx, height),
                strokeWidth = 1f
            )
            rx += step * 3
        }
    }
}

/**
 * ZZZ Window Card with terminal top header, cut corners, neon border, and optional glassmorphic graphic texture.
 */
@Composable
fun ZzzWindowCard(
    modifier: Modifier = Modifier,
    title: String? = null,
    subTitle: String? = null,
    headerBadge: String? = null,
    borderColor: Color = ZzzElectricCyan,
    backgroundColor: Color = ZzzDarkSurface.copy(alpha = 0.95f),
    cornerSize: Dp = 12.dp,
    borderWidth: Dp = 2.dp,
    useGraphicBackground: Boolean = true,
    graphicDrawableRes: Int = R.drawable.panel_card_glass,
    headerRightContent: (@Composable RowScope.() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    val shape = CutCornerShape(topStart = cornerSize, bottomEnd = cornerSize, topEnd = 2.dp, bottomStart = 2.dp)

    Surface(
        color = backgroundColor,
        shape = shape,
        border = androidx.compose.foundation.BorderStroke(borderWidth, borderColor),
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
    ) {
        Box(modifier = Modifier.fillMaxWidth()) {
            if (useGraphicBackground) {
                Image(
                    painter = painterResource(id = graphicDrawableRes),
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier
                        .matchParentSize()
                        .alpha(0.85f)
                )
            }

            Column(modifier = Modifier.fillMaxWidth()) {
                // Header Terminal Bar
                if (title != null || headerBadge != null || headerRightContent != null) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(Color(0xFF161922).copy(alpha = 0.9f))
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            // Hazard accent box
                            Box(
                                modifier = Modifier
                                    .size(width = 4.dp, height = 14.dp)
                                    .background(borderColor)
                            )

                            if (headerBadge != null) {
                                Surface(
                                    color = borderColor,
                                    shape = CutCornerShape(topStart = 2.dp, bottomEnd = 4.dp)
                                ) {
                                    Text(
                                        text = " $headerBadge ",
                                        color = Color.Black,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        fontFamily = FontFamily.Monospace,
                                        modifier = Modifier.padding(vertical = 1.dp)
                                    )
                                }
                            }

                            if (title != null) {
                                Text(
                                    text = title.uppercase(),
                                    color = Color.White,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontFamily = FontFamily.SansSerif,
                                    letterSpacing = 1.sp
                                )
                            }

                            if (subTitle != null) {
                                Text(
                                    text = "// $subTitle",
                                    color = Color.Gray,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            headerRightContent?.invoke(this)

                            // Terminal Window Buttons mock [- □ ✕]
                            Text(
                                text = "─ □ ✕",
                                color = borderColor.copy(alpha = 0.7f),
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.padding(start = 4.dp)
                            )
                        }
                    }
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(1.dp)
                            .background(borderColor.copy(alpha = 0.4f))
                    )
                }

                // Card Body Content
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(10.dp)
                ) {
                    content()
                }
            }
        }
    }
}

/**
 * ZZZ Vibrant Action Button with Graphic Texture Support, Hazard Stripes, spring compression animation, and haptics.
 */
@Composable
fun ZzzMainButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    primaryColor: Color = ZzzAcidYellow,
    borderColor: Color = ZzzElectricCyan,
    textColor: Color = Color.Black,
    leadingIcon: (@Composable () -> Unit)? = null,
    trailingIcon: (@Composable () -> Unit)? = null,
    showHazardStripes: Boolean = true,
    useGraphicBackground: Boolean = true,
    graphicDrawableRes: Int = R.drawable.btn_action_primary,
    shape: androidx.compose.ui.graphics.Shape = CutCornerShape(topStart = 10.dp, bottomEnd = 10.dp, topEnd = 3.dp, bottomStart = 3.dp),
    height: Dp = 50.dp
) {
    val haptic = LocalHapticFeedback.current
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.93f else 1.0f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow),
        label = "zzz_button_scale"
    )

    Surface(
        onClick = {
            if (enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            }
        },
        enabled = enabled,
        interactionSource = interactionSource,
        color = Color.Transparent,
        shape = shape,
        modifier = modifier.scale(scale)
    ) {
        Box(
            modifier = Modifier
                .height(height)
                .then(
                    if (useGraphicBackground) {
                        Modifier.clip(shape)
                    } else {
                        Modifier
                            .background(
                                brush = if (enabled) {
                                    Brush.horizontalGradient(
                                        listOf(primaryColor, primaryColor.copy(alpha = 0.85f))
                                    )
                                } else {
                                    Brush.horizontalGradient(
                                        listOf(Color.DarkGray, Color.Gray)
                                    )
                                },
                                shape = shape
                            )
                            .border(
                                width = 2.dp,
                                color = if (enabled) borderColor else Color.Gray,
                                shape = shape
                            )
                    }
                )
                .padding(horizontal = 16.dp),
            contentAlignment = Alignment.Center
        ) {
            if (useGraphicBackground) {
                Image(
                    painter = painterResource(id = graphicDrawableRes),
                    contentDescription = null,
                    contentScale = ContentScale.FillBounds,
                    modifier = Modifier
                        .matchParentSize()
                        .alpha(if (enabled) 1.0f else 0.45f)
                )
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                if (showHazardStripes && enabled) {
                    Text(
                        text = "///",
                        color = (if (useGraphicBackground) Color.White else textColor).copy(alpha = 0.6f),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(end = 6.dp)
                    )
                }

                leadingIcon?.invoke()

                Text(
                    text = text.uppercase(),
                    color = if (!enabled) Color.LightGray else if (useGraphicBackground) Color.White else textColor,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.SansSerif,
                    letterSpacing = 1.sp
                )

                trailingIcon?.invoke()

                if (showHazardStripes && enabled) {
                    Text(
                        text = "///",
                        color = (if (useGraphicBackground) Color.White else textColor).copy(alpha = 0.6f),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(start = 6.dp)
                    )
                }
            }
        }
    }
}

/**
 * ZZZ Danger Action Button (Emergency Escape, Logout, Reset, Flee) with btn_action_danger.png skin.
 */
@Composable
fun ZzzDangerButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    shape: androidx.compose.ui.graphics.Shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp, topEnd = 3.dp, bottomStart = 3.dp),
    leadingIcon: (@Composable () -> Unit)? = null,
    trailingIcon: (@Composable () -> Unit)? = null,
    showHazardStripes: Boolean = true,
    height: Dp = 48.dp
) {
    ZzzMainButton(
        text = text,
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        primaryColor = ZzzHotMagenta,
        textColor = Color.White,
        borderColor = ZzzHotMagenta,
        shape = shape,
        leadingIcon = leadingIcon,
        trailingIcon = trailingIcon,
        showHazardStripes = showHazardStripes,
        useGraphicBackground = true,
        graphicDrawableRes = R.drawable.btn_action_danger,
        height = height
    )
}

/**
 * ZZZ Neon Status Badge.
 */
@Composable
fun ZzzBadge(
    text: String,
    modifier: Modifier = Modifier,
    color: Color = ZzzElectricCyan,
    textColor: Color = Color.Black,
    borderOnly: Boolean = false
) {
    if (borderOnly) {
        Surface(
            color = Color.Transparent,
            shape = CutCornerShape(topStart = 3.dp, bottomEnd = 3.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, color),
            modifier = modifier
        ) {
            Text(
                text = text,
                color = color,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
    } else {
        Surface(
            color = color,
            shape = CutCornerShape(topStart = 3.dp, bottomEnd = 3.dp),
            modifier = modifier
        ) {
            Text(
                text = text,
                color = textColor,
                fontSize = 10.sp,
                fontWeight = FontWeight.ExtraBold,
                fontFamily = FontFamily.Monospace,
                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
    }
}

/**
 * ZZZ Segmented Progress Bar.
 */
@Composable
fun ZzzProgressBar(
    progress: Float, // 0.0f to 1.0f
    modifier: Modifier = Modifier,
    totalSegments: Int = 10,
    activeColor: Color = ZzzToxicGreen,
    inactiveColor: Color = Color(0xFF1E2330),
    borderColor: Color = ZzzElectricCyan
) {
    Surface(
        color = ZzzDarkSurface,
        shape = CutCornerShape(4.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, borderColor.copy(alpha = 0.5f)),
        modifier = modifier
            .fillMaxWidth()
            .height(14.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(2.dp),
            horizontalArrangement = Arrangement.spacedBy(2.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val filledSegments = (progress * totalSegments).toInt().coerceIn(0, totalSegments)
            for (i in 0 until totalSegments) {
                val isFilled = i < filledSegments
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .background(
                            color = if (isFilled) activeColor else inactiveColor,
                            shape = CutCornerShape(topStart = 2.dp, bottomEnd = 2.dp)
                        )
                )
            }
        }
    }
}

/**
 * ZZZ Resource / Stat Graphic Badge with PNG icons (BioCoin, StarEnergy, NeuralExp, HP, Shield, Depth).
 */
@Composable
fun ZzzResourceBadge(
    iconRes: Int,
    value: String,
    label: String? = null,
    borderColor: Color = ZzzElectricCyan,
    textColor: Color = Color.White,
    modifier: Modifier = Modifier,
    iconSize: Dp = 18.dp,
    onClick: (() -> Unit)? = null
) {
    val shape = CutCornerShape(topStart = 4.dp, bottomEnd = 4.dp, topEnd = 2.dp, bottomStart = 2.dp)

    Surface(
        onClick = { onClick?.invoke() },
        enabled = onClick != null,
        color = Color(0xFF161922).copy(alpha = 0.95f),
        shape = shape,
        border = androidx.compose.foundation.BorderStroke(1.dp, borderColor.copy(alpha = 0.8f)),
        modifier = modifier
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 7.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(5.dp)
        ) {
            Image(
                painter = painterResource(id = iconRes),
                contentDescription = label ?: value,
                modifier = Modifier.size(iconSize),
                contentScale = ContentScale.Fit
            )

            if (label != null) {
                Text(
                    text = label.uppercase(),
                    color = Color.Gray,
                    fontSize = 8.5.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }

            Text(
                text = value,
                color = textColor,
                fontSize = 11.sp,
                fontWeight = FontWeight.ExtraBold,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

/**
 * Top Header Status Bar for Screens (BioCoins, XP, Energy, Signal).
 */
@Composable
fun ZzzHeaderBar(
    bioCoins: Long,
    energy: Int,
    maxEnergy: Int = 100,
    signalPercent: Int = 85,
    xp: Int = 0,
    level: Int = 1,
    onOpenSettings: (() -> Unit)? = null
) {
    Surface(
        color = ZzzDarkSurface,
        shape = CutCornerShape(bottomStart = 10.dp, bottomEnd = 10.dp),
        border = androidx.compose.foundation.BorderStroke(1.5.dp, ZzzElectricCyan),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 7.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // BioCoins Badge
            ZzzResourceBadge(
                iconRes = R.drawable.ic_biocoin,
                value = "$bioCoins",
                borderColor = ZzzAcidYellow,
                textColor = ZzzAcidYellow
            )

            // Energy Badge
            ZzzResourceBadge(
                iconRes = R.drawable.ic_star_energy,
                value = "$energy/$maxEnergy",
                borderColor = ZzzElectricCyan,
                textColor = ZzzElectricCyan
            )

            // Level / XP Badge
            ZzzResourceBadge(
                iconRes = R.drawable.ic_neural_exp,
                value = "LVL $level",
                borderColor = ZzzHotMagenta,
                textColor = ZzzHotMagenta
            )

            if (onOpenSettings != null) {
                Surface(
                    onClick = onOpenSettings,
                    color = Color(0xFF202534),
                    shape = CircleShape,
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.Gray)
                ) {
                    Text("⚙️", fontSize = 12.sp, modifier = Modifier.padding(5.dp))
                }
            }
        }
    }
}

/**
 * ZZZ Hazard Stripe Ribbon Divider (Texture-based).
 */
@Composable
fun ZzzHazardStripeDivider(
    modifier: Modifier = Modifier,
    height: Dp = 8.dp,
    alpha: Float = 0.85f
) {
    Image(
        painter = painterResource(id = R.drawable.banner_hazard_stripes),
        contentDescription = null,
        contentScale = ContentScale.FillBounds,
        modifier = modifier
            .fillMaxWidth()
            .height(height)
            .alpha(alpha)
    )
}

/**
 * ZZZ Warning / Guidance Banner with Hazard Header and Cyber Text.
 */
@Composable
fun ZzzHazardBanner(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    borderColor: Color = ZzzHotMagenta,
    backgroundColor: Color = ZzzDarkSurface.copy(alpha = 0.95f),
    icon: String? = null,
    iconRes: Int = R.drawable.ic_hazard_warning
) {
    val shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp, topEnd = 3.dp, bottomStart = 3.dp)

    Surface(
        color = backgroundColor,
        shape = shape,
        border = androidx.compose.foundation.BorderStroke(1.5.dp, borderColor),
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            // Hazard Stripes Top Accent Bar
            Image(
                painter = painterResource(id = R.drawable.banner_hazard_stripes),
                contentDescription = null,
                contentScale = ContentScale.FillBounds,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    if (icon != null) {
                        Text(text = icon, fontSize = 12.sp)
                    } else {
                        Image(
                            painter = painterResource(id = iconRes),
                            contentDescription = "Предупреждение",
                            modifier = Modifier.size(16.dp),
                            contentScale = ContentScale.Fit
                        )
                    }
                    Text(
                        text = title.uppercase(),
                        color = borderColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = message,
                    color = Color.White.copy(alpha = 0.9f),
                    fontSize = 10.5.sp,
                    lineHeight = 14.sp,
                    fontFamily = FontFamily.SansSerif
                )
            }
        }
    }
}

