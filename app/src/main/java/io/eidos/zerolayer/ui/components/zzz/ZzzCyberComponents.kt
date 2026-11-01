package io.eidos.zerolayer.ui.components.zzz

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.components.premiumCyberClickable
import io.eidos.zerolayer.ui.theme.ZzzDesignSystem

/**
 * ⚡ ZZZ TECHWEAR SECTION HEADER
 * Slanted kinetic title with technical classification decal.
 */
@Composable
fun ZzzHeaderBadge(
    title: String,
    codeTag: String = "SEC-01",
    accentColor: Color = ZzzDesignSystem.VoltYellow,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .width(4.dp)
                .height(18.dp)
                .background(accentColor, CutCornerShape(1.dp))
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = title.uppercase(),
            color = Color.White,
            fontSize = 13.sp,
            fontWeight = FontWeight.Black,
            fontFamily = FontFamily.SansSerif,
            letterSpacing = 1.sp
        )
        Spacer(modifier = Modifier.weight(1f))
        Box(
            modifier = Modifier
                .background(ZzzDesignSystem.TechGrey, ZzzDesignSystem.ShapeBadge)
                .border(0.5.dp, accentColor.copy(alpha = 0.5f), ZzzDesignSystem.ShapeBadge)
                .padding(horizontal = 6.dp, vertical = 2.dp)
        ) {
            Text(
                text = "[$codeTag // AUTH]",
                color = accentColor,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

/**
 * ⚡ ZZZ ACTION TILE
 * High-performance kinetic card button for Main Menu / Hub.
 */
@Composable
fun ZzzActionTile(
    title: String,
    subtitle: String = "",
    iconTag: String = "◈",
    accentColor: Color = ZzzDesignSystem.VoltYellow,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(ZzzDesignSystem.ShapeCard)
            .background(ZzzDesignSystem.CardSurface)
            .border(1.5.dp, accentColor.copy(alpha = 0.8f), ZzzDesignSystem.ShapeCard)
            .premiumCyberClickable(onClick = onClick)
            .padding(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(42.dp)
                    .background(Color(0xFF0F131A), CutCornerShape(4.dp))
                    .border(1.dp, accentColor, CutCornerShape(4.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = iconTag,
                    color = accentColor,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Black
                )
            }
            Spacer(modifier = Modifier.width(10.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title.uppercase(),
                    color = Color.White,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.SansSerif,
                    letterSpacing = 0.5.sp
                )
                if (subtitle.isNotBlank()) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = subtitle,
                        color = ZzzDesignSystem.TechGreyLight,
                        fontSize = 9.5.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
            Text(
                text = "▶",
                color = accentColor.copy(alpha = 0.7f),
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * ⚡ ZZZ SEGMENTED GAUGE
 * High-tech segmented progress bar for Energy, HP, Overdrive.
 */
@Composable
fun ZzzSegmentedGauge(
    current: Long,
    max: Long,
    segments: Int = 10,
    accentColor: Color = ZzzDesignSystem.VoltYellow,
    modifier: Modifier = Modifier
) {
    val fillRatio = if (max > 0) (current.toFloat() / max.toFloat()).coerceIn(0f, 1f) else 0f
    val filledSegments = (fillRatio * segments).toInt()

    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(8.dp),
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        for (i in 0 until segments) {
            val isFilled = i < filledSegments
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .background(
                        if (isFilled) accentColor else ZzzDesignSystem.TechGrey,
                        CutCornerShape(1.dp)
                    )
            )
        }
    }
}

/**
 * ⚡ ZZZ RARITY BADGE
 * Technical chamfered tag with color coding for item rarities.
 */
@Composable
fun ZzzRarityBadge(
    rarity: String,
    modifier: Modifier = Modifier
) {
    val r = rarity.lowercase()
    val (color, label) = when {
        r in listOf("relic", "earth relic") -> Pair(ZzzDesignSystem.QuantumPurple, "RELIC")
        r in listOf("cursed", "hazard") -> Pair(ZzzDesignSystem.CrimsonHazard, "CURSED")
        r == "legendary" -> Pair(ZzzDesignSystem.VoltYellow, "LEGENDARY")
        r == "epic" -> Pair(ZzzDesignSystem.SignalCyan, "EPIC")
        r == "rare" -> Pair(ZzzDesignSystem.ToxicGreen, "RARE")
        else -> Pair(ZzzDesignSystem.TechGreyLight, "COMMON")
    }

    Box(
        modifier = modifier
            .background(color.copy(alpha = 0.15f), ZzzDesignSystem.ShapeBadge)
            .border(1.dp, color, ZzzDesignSystem.ShapeBadge)
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            color = color,
            fontSize = 9.sp,
            fontWeight = FontWeight.Black,
            fontFamily = FontFamily.Monospace
        )
    }
}
