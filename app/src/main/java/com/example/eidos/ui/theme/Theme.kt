package com.example.eidos.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Core Cyberpunk Aesthetic Palette
val EidosVoid = Color(0xFF05080E)
val EidosBg = Color(0xFF070C14)
val EidosDarkSurface = Color(0xFF0C131D)
val EidosSurfaceElevated = Color(0xFF111C2A)
val EidosCardBg = Color(0xFF0E1622)

// Holographic Accent Colors
val EidosCyan = Color(0xFF00F0FF)
val EidosCyanDim = Color(0xFF00A3B4)
val EidosNeon = Color(0xFF00E676)
val EidosNeonDim = Color(0xFF00A854)
val EidosRed = Color(0xFFFF3366)
val EidosRedDim = Color(0xFFB31940)
val EidosPurple = Color(0xFFA855F7)
val EidosPurpleDim = Color(0xFF7E22CE)
val EidosGold = Color(0xFFFFB800)
val EidosOrange = Color(0xFFFF6B00)

// ZZZ Neon & Industrial Palette
val ZzzAcidYellow = Color(0xFFFAFE00)      // Кислотно-желтый
val ZzzElectricCyan = Color(0xFF00FFF6)    // Электрик бирюза
val ZzzHotMagenta = Color(0xFFFF007A)      // Неоновая фуксия/маджента
val ZzzToxicGreen = Color(0xFF00FF66)      // Зеленый глитч
val ZzzDarkSurface = Color(0xFF101116)     // Глубокий темный фон
val ZzzObsidian = Color(0xFF08090C)        // Базовый обсидиан
val ZzzWarningStripes = Color(0xFFFFB800)  // Предупреждающие шевроны
val ZzzTextPrimary = Color(0xFFFFFFFF)     // Чистый белый
val ZzzTextBody = Color(0xFFE2E8F0)        // Контрастный светло-серый для русского текста
val ZzzTextSecondary = Color(0xFF94A3B8)   // Вторичный серый для логов и подписей

// Glassmorphism & Borders
val EidosGlass = Color(0xE60A111A)
val EidosGlassLight = Color(0x66152232)
val EidosGlassBorder = Color(0x3300F0FF)
val EidosBorderSubtle = Color(0x1F00F0FF)
val EidosBorderFocus = Color(0x8000F0FF)

private val DarkColorScheme = darkColorScheme(
    primary = EidosCyan,
    secondary = EidosNeon,
    tertiary = EidosPurple,
    background = EidosVoid,
    surface = EidosDarkSurface,
    surfaceVariant = EidosSurfaceElevated,
    onPrimary = Color.Black,
    onSecondary = Color.Black,
    onTertiary = Color.White,
    onBackground = Color.White,
    onSurface = Color.White,
    onSurfaceVariant = Color(0xFFB0BEC5)
)

@Composable
fun EidosTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = Typography,
        content = content
    )
}

