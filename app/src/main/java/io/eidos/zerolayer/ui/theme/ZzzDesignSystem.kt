package io.eidos.zerolayer.ui.theme

import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * ⚡ ZENLESS ZONE ZERO (ZZZ) HIGH-TECH DESIGN SYSTEM
 * Authentic GaaS urban cyberpunk palette, kinetic geometry and techwear decals.
 */
object ZzzDesignSystem {
    // 🎨 Core Color Palette
    val ObsidianDark = Color(0xFF0D0F14)       // Deep matte background
    val CardSurface = Color(0xFF161922)        // Technical panel surface
    val CardElevated = Color(0xFF1D2230)       // Raised HUD element
    val TechGrey = Color(0xFF262C3A)           // Border and inactive slots
    val TechGreyLight = Color(0xFF4A5568)      // Technical details and decals

    // ⚡ Vivid Kinetic Accents
    val VoltYellow = Color(0xFFFFE600)         // Signature ZZZ Volt Yellow (Actions, Highlights)
    val SignalCyan = Color(0xFF00F0FF)         // Holographic Electric Cyan (Data, Energy, Shields)
    val CrimsonHazard = Color(0xFFFF2A55)      // Critical Warning Red (Boss HP, Cursed, Danger)
    val ToxicGreen = Color(0xFF10FFA0)         // Overdrive & Synergies
    val QuantumPurple = Color(0xFFB537F2)      // Void, Relics, High-Tier Crafting

    // 📐 High-Tech Techwear Chamfered Shapes
    val ShapeCard = CutCornerShape(topStart = 8.dp, bottomEnd = 10.dp)
    val ShapeCardLarge = CutCornerShape(topStart = 12.dp, bottomEnd = 16.dp)
    val ShapeBadge = CutCornerShape(topStart = 4.dp, bottomEnd = 6.dp)
    val ShapeButton = CutCornerShape(topStart = 6.dp, bottomEnd = 8.dp)
    val ShapeSlot = CutCornerShape(4.dp)

    // 🌌 Gradients & Glows
    val GlowVoltYellow = Brush.verticalGradient(
        colors = listOf(VoltYellow.copy(alpha = 0.25f), Color.Transparent)
    )
    val GlowSignalCyan = Brush.verticalGradient(
        colors = listOf(SignalCyan.copy(alpha = 0.25f), Color.Transparent)
    )
    val GlowCrimson = Brush.verticalGradient(
        colors = listOf(CrimsonHazard.copy(alpha = 0.25f), Color.Transparent)
    )
    val CardGradient = Brush.linearGradient(
        colors = listOf(CardElevated, CardSurface)
    )
}

// 🥇 Consolidated Semantic Tokens (canonical source: collapse targets for legacy hardcodes)
// Top-level so they resolve via plain / star imports of the theme package.
val ZzzGold = Color(0xFFFFD700)            // Unified gold (collapse target: FFD700/FFB300/FFC107/FFD54F)
val ZzzAmber = Color(0xFFFFB800)           // Distinct amber (warning stripes, legacy EidosGold value)
val ZzzDangerRed = Color(0xFFFF5252)       // Unified danger red (damage, errors, alerts)
val ZzzWarningOrange = Color(0xFFFF9800)   // Unified warning orange (cooldowns, cautions)
val ZzzPurple = Color(0xFFA855F7)          // Standard accent purple (relics, rare loot)
val ZzzGlassBase = Color(0xE60A111A)       // Base glassmorphism surface (90% opacity)
