package io.eidos.zerolayer.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.theme.*

// ─── EIDOS PRIMARY BUTTON ────────────────────────────────────────────────────
@Composable
fun EidosButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    text: String,
    icon: String = "",
    variant: EidosButtonVariant = EidosButtonVariant.PRIMARY,
    enabled: Boolean = true,
    subtext: String = ""
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed && enabled) 0.95f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessHigh),
        label = "btn_scale"
    )
    val (containerColor, borderColor, textColor) = when (variant) {
        EidosButtonVariant.PRIMARY -> Triple(Color(0xFF0A1F2E), EidosCyan, EidosCyan)
        EidosButtonVariant.SECONDARY -> Triple(Color(0xFF0D1F0F), EidosNeon, EidosNeon)
        EidosButtonVariant.DANGER -> Triple(Color(0xFF2A0A12), EidosRed, EidosRed)
        EidosButtonVariant.GOLD -> Triple(Color(0xFF1F1600), EidosGold, EidosGold)
        EidosButtonVariant.GHOST -> Triple(Color.Transparent, Color(0x44FFFFFF), Color.White)
    }
    val alpha = if (enabled) 1f else 0.38f

    Box(
        modifier = modifier
            .graphicsLayer { scaleX = scale; scaleY = scale; this.alpha = alpha }
            .shadow(if (enabled) 6.dp else 0.dp, CutCornerShape(topStart = 6.dp, bottomEnd = 8.dp), ambientColor = borderColor, spotColor = borderColor)
            .clip(CutCornerShape(topStart = 6.dp, bottomEnd = 8.dp))
            .background(containerColor)
            .border(1.5.dp, if (enabled) borderColor else Color.DarkGray, CutCornerShape(topStart = 6.dp, bottomEnd = 8.dp))
            .clickable(interactionSource = interactionSource, indication = null, enabled = enabled) { onClick() }
            .padding(horizontal = 16.dp, vertical = if (subtext.isEmpty()) 14.dp else 8.dp)
            .heightIn(min = 48.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                if (icon.isNotEmpty()) Text(icon, fontSize = 14.sp)
                Text(
                    text = text,
                    color = textColor,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center
                )
            }
            if (subtext.isNotEmpty()) {
                Text(
                    subtext,
                    color = textColor.copy(alpha = 0.65f),
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

enum class EidosButtonVariant { PRIMARY, SECONDARY, DANGER, GOLD, GHOST }

// ─── EIDOS GLASS CARD ───────────────────────────────────────────────────────
@Composable
fun EidosGlassCard(
    modifier: Modifier = Modifier,
    glowColor: Color = EidosCyan,
    cornerTopStart: Dp = 8.dp,
    cornerBottomEnd: Dp = 12.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    val shape = CutCornerShape(topStart = cornerTopStart, bottomEnd = cornerBottomEnd)
    Column(
        modifier = modifier
            .shadow(8.dp, shape, ambientColor = glowColor.copy(alpha = 0.3f), spotColor = glowColor.copy(alpha = 0.2f))
            .clip(shape)
            .background(
                Brush.linearGradient(
                    colors = listOf(Color(0xFF0E1A2A), Color(0xFF07101A)),
                    start = Offset.Zero, end = Offset.Infinite
                )
            )
            .border(1.dp, glowColor.copy(alpha = 0.35f), shape)
            .padding(12.dp),
        content = content
    )
}

// ─── EIDOS STAT BAR ─────────────────────────────────────────────────────────
@Composable
fun EidosStatBar(
    label: String,
    value: Int,
    maxValue: Int,
    color: Color = EidosCyan,
    modifier: Modifier = Modifier,
    showNumbers: Boolean = true
) {
    val progress = (value.toFloat() / maxValue.toFloat()).coerceIn(0f, 1f)
    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        animationSpec = tween(500),
        label = "stat_progress"
    )
    val barColor = when {
        progress < 0.2f -> EidosRed
        progress < 0.4f -> EidosOrange
        else -> color
    }
    Column(modifier = modifier) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(label, color = Color(0xFF94A3B8), fontSize = 9.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
            if (showNumbers) {
                Text("$value / $maxValue", color = barColor, fontSize = 10.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
            }
        }
        Spacer(modifier = Modifier.height(3.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(Color(0xFF1A2533))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(animatedProgress)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(3.dp))
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(barColor.copy(alpha = 0.6f), barColor)
                        )
                    )
                    .shadow(4.dp, RoundedCornerShape(3.dp), ambientColor = barColor, spotColor = barColor)
            )
        }
    }
}

// ─── EIDOS STAT ROW ─────────────────────────────────────────────────────────
@Composable
fun EidosStatRow(
    label: String,
    value: String,
    accent: Color = EidosCyan,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth().padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label, color = Color(0xFF64748B), fontSize = 10.sp, fontFamily = FontFamily.Monospace)
        Text(value, color = accent, fontSize = 11.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
    }
}

// ─── EIDOS SECTION HEADER ───────────────────────────────────────────────────
@Composable
fun EidosSectionHeader(
    title: String,
    subtitle: String = "",
    accent: Color = EidosCyan,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.width(3.dp).height(16.dp).background(accent, RoundedCornerShape(2.dp)))
            Text(title, color = accent, fontSize = 13.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Black)
        }
        if (subtitle.isNotEmpty()) {
            Text(subtitle, color = Color(0xFF475569), fontSize = 9.sp, fontFamily = FontFamily.Monospace, modifier = Modifier.padding(start = 11.dp, top = 2.dp))
        }
        Spacer(modifier = Modifier.height(1.dp))
        Box(Modifier.fillMaxWidth().height(1.dp).background(Brush.horizontalGradient(listOf(accent.copy(0.5f), Color.Transparent))))
    }
}

// ─── EIDOS RARITY BADGE ─────────────────────────────────────────────────────
fun rarityColor(rarity: String): Color = when (rarity.lowercase()) {
    "legendary" -> Color(0xFFFFB800)
    "epic" -> Color(0xFFA855F7)
    "rare" -> Color(0xFF00F0FF)
    "uncommon" -> Color(0xFF00E676)
    else -> Color(0xFF94A3B8)
}

@Composable
fun EidosRarityBadge(rarity: String, modifier: Modifier = Modifier) {
    val color = rarityColor(rarity)
    val label = when (rarity.lowercase()) {
        "legendary" -> "⭐ ЛЕГЕНД"
        "epic" -> "💜 ЭПИК"
        "rare" -> "💎 РЕД"
        "uncommon" -> "🟢 НЕОБ"
        else -> "⬜ ОБЫЧ"
    }
    Box(
        modifier = modifier
            .clip(CutCornerShape(topStart = 3.dp, bottomEnd = 4.dp))
            .background(color.copy(alpha = 0.15f))
            .border(0.5.dp, color.copy(alpha = 0.6f), CutCornerShape(topStart = 3.dp, bottomEnd = 4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(label, color = color, fontSize = 7.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
    }
}
