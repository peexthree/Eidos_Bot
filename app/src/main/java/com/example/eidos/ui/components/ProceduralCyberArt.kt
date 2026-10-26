package com.example.eidos.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.theme.ZzzDarkSurface
import com.example.eidos.ui.theme.ZzzElectricCyan
import com.example.eidos.ui.theme.ZzzHotMagenta
import kotlin.math.*

/**
 * 🎨 ADVANCED PROCEDURAL CYBERPUNK ARTWORK ENGINE (V2.0)
 * Provides high-fidelity, deterministic vector illustrations for:
 * 1. Evolution AI Reactor Cores (lvl_1 .. lvl_19)
 * 2. 19 Unique Iconic Cyberpunk Villains (Bioparasite, Sentry Drone, Logic Bomb, Hydra, Cyber Lich, Machine God, etc.)
 * 3. Granular Equipment Archetypes (Katanas, Railguns, Smart Pistols, Banhammers, Exoskeletons, Jackets, Shields, Visors, Stims, Batteries)
 * 4. Cyberpunk Multi-layered Neon Bloom (glow layers + hot core pass)
 */
@Composable
fun ProceduralCyberpunkArtwork(
    imageName: String,
    modifier: Modifier = Modifier,
    borderColor: Color = Color.Unspecified
) {
    val cleanName = remember(imageName) {
        imageName.lowercase()
            .removeSuffix(".jpg")
            .removeSuffix(".png")
            .removeSuffix(".webp")
            .replace(" ", "_")
            .trim()
    }
    val hash = remember(cleanName) { cleanName.hashCode() }

    when {
        cleanName.startsWith("lvl_") -> {
            val level = cleanName.removePrefix("lvl_").toIntOrNull() ?: 1
            ProceduralLevelCore(level = level, modifier = modifier)
        }
        cleanName.contains("anomaly") || cleanName.contains("аномалия") || cleanName == "raid_anomaly" -> {
            ProceduralAnomalyRift(name = cleanName, hash = hash, modifier = modifier)
        }
        cleanName.contains("chest") || cleanName.contains("тайник") || cleanName.contains("cache") || cleanName == "raid_chest" -> {
            ProceduralRaidChest(name = cleanName, hash = hash, modifier = modifier)
        }
        cleanName == "abyssal_key" || cleanName.contains("abyssal_key") -> {
            ProceduralAbyssalKey(modifier = modifier)
        }
        cleanName.startsWith("monster_") || cleanName.startsWith("villain_") || isMonsterName(cleanName) -> {
            val monsterIdx = extractMonsterIndex(cleanName)
            ProceduralMonsterMask(monsterIndex = monsterIdx, name = cleanName, modifier = modifier)
        }
        else -> {
            ProceduralEquipmentCard(name = cleanName, hash = hash, modifier = modifier, customBorder = borderColor)
        }
    }
}

private fun isMonsterName(cleanName: String): Boolean {
    return cleanName.startsWith("monster_") || cleanName.startsWith("villain_") ||
            cleanName.contains("паразит") || cleanName.contains("parazit") ||
            cleanName.contains("глитч") || cleanName.contains("glitch") || cleanName.contains("фантом") || cleanName.contains("phantom") ||
            cleanName.contains("дрон") || cleanName.contains("dron") || cleanName.contains("drone") ||
            cleanName.contains("бомба") || cleanName.contains("bomb") ||
            cleanName.contains("майнер") || cleanName.contains("miner") ||
            cleanName.contains("гидра") || cleanName.contains("hydra") ||
            cleanName.contains("сбой") || cleanName.contains("error") ||
            cleanName.contains("ассасин") || cleanName.contains("assassin") ||
            cleanName.contains("доминатор") || cleanName.contains("dominator") ||
            cleanName.contains("стиратель") || cleanName.contains("eraser") || cleanName.contains("stirat") ||
            cleanName.contains("призрак") || cleanName.contains("ghost") ||
            cleanName.contains("лич") || cleanName.contains("lich") ||
            cleanName.contains("архитектор") || cleanName.contains("architect") ||
            cleanName.contains("пожиратель") || cleanName.contains("devourer") ||
            cleanName.contains("страж") || cleanName.contains("guardian") || cleanName.contains("sentry") ||
            cleanName.contains("синтез") || cleanName.contains("synthesis") ||
            cleanName.contains("машина") || cleanName.contains("machine") || cleanName.contains("deus") ||
            cleanName.contains("странник") || cleanName.contains("nomad") ||
            cleanName.contains("энтропия") || cleanName.contains("entropy")
}

private fun extractMonsterIndex(cleanName: String): Int {
    if (cleanName.startsWith("monster_")) {
        return cleanName.removePrefix("monster_").toIntOrNull()?.coerceIn(1, 19) ?: 1
    }
    return when {
        cleanName.contains("паразит") || cleanName.contains("parazit") -> 1
        cleanName.contains("глитч") || cleanName.contains("glitch") -> 2
        cleanName.contains("дрон") || cleanName.contains("drone") || cleanName.contains("dron") -> 3
        cleanName.contains("бомба") || cleanName.contains("bomb") -> 4
        cleanName.contains("майнер") || cleanName.contains("miner") -> 5
        cleanName.contains("гидра") || cleanName.contains("hydra") -> 6
        cleanName.contains("сбой") || cleanName.contains("error") -> 7
        cleanName.contains("ассасин") || cleanName.contains("assassin") -> 8
        cleanName.contains("доминатор") || cleanName.contains("dominator") -> 9
        cleanName.contains("стиратель") || cleanName.contains("eraser") || cleanName.contains("stirat") -> 10
        cleanName.contains("нейро_призрак") || cleanName.contains("призрак") || cleanName.contains("phantom") || cleanName.contains("ghost") -> 11
        cleanName.contains("лич") || cleanName.contains("lich") -> 12
        cleanName.contains("архитектор") || cleanName.contains("architect") -> 13
        cleanName.contains("пожиратель") || cleanName.contains("devourer") -> 14
        cleanName.contains("страж") || cleanName.contains("guardian") -> 15
        cleanName.contains("синтез") || cleanName.contains("synthesis") -> 16
        cleanName.contains("машина") || cleanName.contains("machine") || cleanName.contains("deus") -> 17
        cleanName.contains("странник") || cleanName.contains("nomad") -> 18
        cleanName.contains("энтропия") || cleanName.contains("entropy") -> 19
        else -> abs(cleanName.hashCode() % 19) + 1
    }
}

// ==============================================================================
// 🌀 A. PROCEDURAL ANOMALY RIFT (REALITY COMPROMISED)
// ==============================================================================

@Composable
fun ProceduralAnomalyRift(
    name: String,
    hash: Int,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "anomaly_anim")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(tween(1200, easing = LinearEasing), RepeatMode.Reverse),
        label = "pulseAlpha"
    )
    val rotAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(10000, easing = LinearEasing), RepeatMode.Restart),
        label = "rotAngle"
    )

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF040209))
            .border(1.5.dp, Color(0xFFFFD700).copy(alpha = pulseAlpha), CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)
            val radius = minDim * 0.42f

            // 1. Quantum Glitch Distortion Grid
            val step = size.width / 8f
            for (i in 0..8) {
                val x = i * step
                val jitter = if ((i + hash) % 3 == 0) 3f else -2f
                drawLine(
                    color = Color(0xFF8A2BE2).copy(alpha = 0.15f),
                    start = Offset(x + jitter, 0f),
                    end = Offset(x - jitter, size.height),
                    strokeWidth = 1f
                )
            }

            // 2. Swirling Elliptical Event Horizons
            for (i in 0 until 4) {
                val ellipseRot = rotAngle + (i * 45f)
                val rad = Math.toRadians(ellipseRot.toDouble())
                val cosA = cos(rad).toFloat()
                val sinA = sin(rad).toFloat()

                val path = Path().apply {
                    val rx = radius * (0.9f - i * 0.15f)
                    val ry = radius * (0.45f - i * 0.08f)
                    for (deg in 0..360 step 20) {
                        val dRad = Math.toRadians(deg.toDouble())
                        val px = rx * cos(dRad).toFloat()
                        val py = ry * sin(dRad).toFloat()
                        val rxRot = px * cosA - py * sinA + center.x
                        val ryRot = px * sinA + py * cosA + center.y
                        if (deg == 0) moveTo(rxRot, ryRot) else lineTo(rxRot, ryRot)
                    }
                    close()
                }
                val col = if (i % 2 == 0) Color(0xFFFFD700) else Color(0xFFFF0055)
                drawPath(path, col.copy(alpha = 0.35f), style = Stroke(width = 1.5f))
            }

            // 3. Central Singularity Core
            drawCircle(Color.Black, radius = radius * 0.35f, center = center)
            drawCircle(Color(0xFFFF0055).copy(alpha = pulseAlpha), radius = radius * 0.35f, center = center, style = Stroke(width = 2.5f))
            drawCircle(Color(0xFFFFD700), radius = radius * 0.18f, center = center, style = Stroke(width = 2f))
            drawCircle(Color.White, radius = radius * 0.08f, center = center)

            // 4. Energetic Fracture Rays
            for (i in 0 until 8) {
                val rayAngle = Math.toRadians((i * 45.0) + (rotAngle * 0.5))
                val p1 = Offset(center.x + cos(rayAngle).toFloat() * (radius * 0.38f), center.y + sin(rayAngle).toFloat() * (radius * 0.38f))
                val p2 = Offset(center.x + cos(rayAngle).toFloat() * (radius * 0.95f), center.y + sin(rayAngle).toFloat() * (radius * 0.95f))
                drawLine(Color(0xFFFF0055).copy(alpha = 0.7f), p1, p2, strokeWidth = 1.5f)
            }
        }

        // Telemetry Labels
        Text(
            text = "ANOMALY // 0x${abs(hash % 256).toString(16).uppercase()}",
            color = Color(0xFFFFD700).copy(alpha = 0.85f),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.TopStart).padding(6.dp)
        )
        Text(
            text = "RIFT DETECTED",
            color = Color(0xFFFF0055),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Black,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomEnd).padding(6.dp)
        )
    }
}

// ==============================================================================
// 📦 B. PROCEDURAL RAID CHEST (ENCRYPTED DATA CONTAINER)
// ==============================================================================

@Composable
fun ProceduralRaidChest(
    name: String,
    hash: Int,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "chest_anim")
    val scanY by infiniteTransition.animateFloat(
        initialValue = -1f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(2000, easing = LinearEasing), RepeatMode.Reverse),
        label = "scanY"
    )

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF060B0E))
            .border(1.5.dp, EidosNeon, CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)
            val halfW = minDim * 0.40f
            val halfH = minDim * 0.32f

            // 1. Armored Crate Body
            val cratePath = Path().apply {
                val cut = halfW * 0.25f
                moveTo(center.x - halfW + cut, center.y - halfH)
                lineTo(center.x + halfW - cut, center.y - halfH)
                lineTo(center.x + halfW, center.y - halfH + cut)
                lineTo(center.x + halfW, center.y + halfH - cut)
                lineTo(center.x + halfW - cut, center.y + halfH)
                lineTo(center.x - halfW + cut, center.y + halfH)
                lineTo(center.x - halfW, center.y + halfH - cut)
                lineTo(center.x - halfW, center.y - halfH + cut)
                close()
            }
            drawPath(cratePath, Color(0xFF0F1B22))
            drawPath(cratePath, EidosNeon, style = Stroke(width = 2.2f))

            // 2. Reinforced Corner Armor Brackets
            val bracketSize = halfW * 0.3f
            drawRect(EidosCyan.copy(alpha = 0.4f), topLeft = Offset(center.x - halfW, center.y - halfH), size = Size(bracketSize, bracketSize), style = Stroke(width = 1.5f))
            drawRect(EidosCyan.copy(alpha = 0.4f), topLeft = Offset(center.x + halfW - bracketSize, center.y - halfH), size = Size(bracketSize, bracketSize), style = Stroke(width = 1.5f))
            drawRect(EidosCyan.copy(alpha = 0.4f), topLeft = Offset(center.x - halfW, center.y + halfH - bracketSize), size = Size(bracketSize, bracketSize), style = Stroke(width = 1.5f))
            drawRect(EidosCyan.copy(alpha = 0.4f), topLeft = Offset(center.x + halfW - bracketSize, center.y + halfH - bracketSize), size = Size(bracketSize, bracketSize), style = Stroke(width = 1.5f))

            // 3. Central Cryptographic Biometric Lock
            drawCircle(Color.Black, radius = halfH * 0.45f, center = center)
            drawCircle(Color(0xFFFFD700), radius = halfH * 0.45f, center = center, style = Stroke(width = 2f))
            drawCircle(EidosCyan, radius = halfH * 0.22f, center = center)

            // Keyhole slot
            drawLine(Color.White, Offset(center.x, center.y - halfH * 0.15f), Offset(center.x, center.y + halfH * 0.18f), strokeWidth = 2f)

            // 4. Holographic Scan Laser Bar
            val currentLaserY = center.y + (scanY * halfH * 0.8f)
            drawLine(
                color = EidosNeon.copy(alpha = 0.85f),
                start = Offset(center.x - halfW * 0.9f, currentLaserY),
                end = Offset(center.x + halfW * 0.9f, currentLaserY),
                strokeWidth = 2f
            )

            // 5. LED Status Dots
            drawCircle(Color(0xFF00FF66), radius = 2.5f, center = Offset(center.x - halfW * 0.65f, center.y - halfH * 0.65f))
            drawCircle(Color(0xFF00E5FF), radius = 2.5f, center = Offset(center.x - halfW * 0.45f, center.y - halfH * 0.65f))
            drawCircle(Color(0xFFFF0055), radius = 2.5f, center = Offset(center.x - halfW * 0.25f, center.y - halfH * 0.65f))
        }

        // Telemetry Labels
        Text(
            text = "CONTAINER // DATA-VAULT",
            color = EidosNeon.copy(alpha = 0.85f),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.TopStart).padding(6.dp)
        )
        Text(
            text = "LOCKED // 256-BIT",
            color = Color(0xFFFFD700),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Black,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomEnd).padding(6.dp)
        )
    }
}

// ==============================================================================
// 👁️ C. PROCEDURAL ABYSSAL KEY (OCULAR OCCULT CYBER ARTIFACT)
// ==============================================================================

@Composable
fun ProceduralAbyssalKey(
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "key_anim")
    val pulseGlow by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1400, easing = LinearEasing), RepeatMode.Reverse),
        label = "pulseGlow"
    )

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF07000F))
            .border(1.5.dp, Color(0xFFB026FF).copy(alpha = pulseGlow), CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)
            val s = minDim * 0.42f

            // 1. Occult Cybernetic Eye (Key Head)
            val eyeCenter = Offset(center.x, center.y - s * 0.45f)
            val eyePath = Path().apply {
                moveTo(eyeCenter.x - s * 0.6f, eyeCenter.y)
                cubicTo(
                    eyeCenter.x - s * 0.3f, eyeCenter.y - s * 0.45f,
                    eyeCenter.x + s * 0.3f, eyeCenter.y - s * 0.45f,
                    eyeCenter.x + s * 0.6f, eyeCenter.y
                )
                cubicTo(
                    eyeCenter.x + s * 0.3f, eyeCenter.y + s * 0.45f,
                    eyeCenter.x - s * 0.3f, eyeCenter.y + s * 0.45f,
                    eyeCenter.x - s * 0.6f, eyeCenter.y
                )
                close()
            }
            drawPath(eyePath, Color(0xFF8A2BE2).copy(alpha = 0.35f))
            drawPath(eyePath, Color(0xFFFFD700), style = Stroke(width = 2.2f))

            // Iris & Pupil
            drawCircle(Color(0xFFB026FF), radius = s * 0.22f, center = eyeCenter)
            drawCircle(Color.Black, radius = s * 0.12f, center = eyeCenter)
            drawCircle(Color.White, radius = s * 0.05f, center = Offset(eyeCenter.x + 2f, eyeCenter.y - 2f))

            // 2. Crystalline Key Shaft
            val shaftTop = eyeCenter.y + s * 0.35f
            val shaftBottom = center.y + s * 0.95f
            drawLine(Color(0xFFFFD700), Offset(center.x - s * 0.08f, shaftTop), Offset(center.x - s * 0.08f, shaftBottom), strokeWidth = 2f)
            drawLine(Color(0xFFFFD700), Offset(center.x + s * 0.08f, shaftTop), Offset(center.x + s * 0.08f, shaftBottom), strokeWidth = 2f)
            drawLine(Color.White, Offset(center.x, shaftTop), Offset(center.x, shaftBottom), strokeWidth = 1.2f)

            // 3. Cryptographic Teeth
            val tW = s * 0.35f
            val tH = s * 0.12f
            drawRect(Color(0xFFB026FF).copy(alpha = 0.4f), topLeft = Offset(center.x + s * 0.08f, center.y + s * 0.35f), size = Size(tW, tH))
            drawRect(Color(0xFFFFD700), topLeft = Offset(center.x + s * 0.08f, center.y + s * 0.35f), size = Size(tW, tH), style = Stroke(width = 1.5f))

            drawRect(Color(0xFFB026FF).copy(alpha = 0.4f), topLeft = Offset(center.x + s * 0.08f, center.y + s * 0.65f), size = Size(tW * 0.75f, tH))
            drawRect(Color(0xFFFFD700), topLeft = Offset(center.x + s * 0.08f, center.y + s * 0.65f), size = Size(tW * 0.75f, tH), style = Stroke(width = 1.5f))

            // 4. Radiating Singularity Sparks
            for (i in 0 until 6) {
                val a = Math.toRadians(i * 60.0)
                val p1 = Offset(eyeCenter.x + cos(a).toFloat() * s * 0.65f, eyeCenter.y + sin(a).toFloat() * s * 0.65f)
                val p2 = Offset(eyeCenter.x + cos(a).toFloat() * s * 0.85f, eyeCenter.y + sin(a).toFloat() * s * 0.85f)
                drawLine(Color(0xFFFFD700).copy(alpha = pulseGlow), p1, p2, strokeWidth = 1.5f)
            }
        }

        // Telemetry Labels
        Text(
            text = "ARTIFACT // ABYSSAL KEY",
            color = Color(0xFFFFD700),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.TopStart).padding(6.dp)
        )
        Text(
            text = "RESONANCE: MAX",
            color = Color(0xFFB026FF),
            fontSize = 7.5.sp,
            fontWeight = FontWeight.Black,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomEnd).padding(6.dp)
        )
    }
}

// ==============================================================================
// 🌟 1. EVOLUTION AI CORE (LVL 1 .. 19)
// ==============================================================================

@Composable
fun ProceduralLevelCore(
    level: Int,
    modifier: Modifier = Modifier
) {
    val tierColor = when {
        level >= 16 -> ZzzHotMagenta          // Tier 4: Singularity Plasma
        level >= 11 -> Color(0xFFFFB300)      // Tier 3: Overclock Amber Gold
        level >= 6 -> Color(0xFF00FF66)       // Tier 2: Acid Neural Green
        else -> ZzzElectricCyan               // Tier 1: Cold Pure Cyan
    }

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF06090E))
            .border(1.5.dp, tierColor, CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)
            val maxRadius = minDim * 0.44f

            // Cyber PCB Grid
            val gridStep = minDim * 0.12f
            var gx = 0f
            while (gx < size.width) {
                drawLine(
                    color = tierColor.copy(alpha = 0.07f),
                    start = Offset(gx, 0f),
                    end = Offset(gx, size.height),
                    strokeWidth = 1f
                )
                gx += gridStep
            }
            var gy = 0f
            while (gy < size.height) {
                drawLine(
                    color = tierColor.copy(alpha = 0.07f),
                    start = Offset(0f, gy),
                    end = Offset(size.width, gy),
                    strokeWidth = 1f
                )
                gy += gridStep
            }

            // Concentric Telemetry Rings with Neon Glow
            val ringCount = 2 + (level / 4)
            for (i in 1..ringCount) {
                val r = (maxRadius / ringCount) * i
                val isDashed = i % 2 == 1
                val effect = if (isDashed) PathEffect.dashPathEffect(floatArrayOf(14f, 8f), 0f) else null

                // Outer Glow
                drawCircle(
                    color = tierColor.copy(alpha = 0.12f),
                    radius = r,
                    center = center,
                    style = Stroke(width = 4.5f, pathEffect = effect)
                )
                // Solid Neon Ring
                drawCircle(
                    color = tierColor.copy(alpha = 0.5f + (i * 0.12f).coerceAtMost(0.45f)),
                    radius = r,
                    center = center,
                    style = Stroke(width = 1.6f, pathEffect = effect)
                )
            }

            // Radial Energy Rays & Data Terminals
            val rayCount = 4 + (level * 2)
            val angleStep = (2 * PI / rayCount)
            for (i in 0 until rayCount) {
                val angle = i * angleStep + (level * 0.12f)
                val startR = maxRadius * 0.35f
                val endR = maxRadius * (0.85f + 0.15f * (i % 2))
                val p1 = Offset(center.x + cos(angle).toFloat() * startR, center.y + sin(angle).toFloat() * startR)
                val p2 = Offset(center.x + cos(angle).toFloat() * endR, center.y + sin(angle).toFloat() * endR)

                drawLine(
                    color = tierColor.copy(alpha = if (i % 2 == 0) 0.65f else 0.3f),
                    start = p1,
                    end = p2,
                    strokeWidth = if (i % 2 == 0) 1.8f else 1f
                )
                drawCircle(
                    color = Color.White,
                    radius = if (i % 2 == 0) 2.2f else 1.5f,
                    center = p2
                )
            }

            // Central Sacred Cyber-Mandala Polygon
            val sides = when {
                level >= 15 -> 8
                level >= 10 -> 6
                level >= 5 -> 4
                else -> 3
            }
            val polyRadius = maxRadius * 0.36f
            val polyPath = Path()
            for (s in 0 until sides) {
                val pAngle = s * (2 * PI / sides) - (PI / 2)
                val px = center.x + cos(pAngle).toFloat() * polyRadius
                val py = center.y + sin(pAngle).toFloat() * polyRadius
                if (s == 0) polyPath.moveTo(px, py) else polyPath.lineTo(px, py)
            }
            polyPath.close()

            // Glow Pass
            drawPath(polyPath, tierColor.copy(alpha = 0.20f))
            drawPath(polyPath, tierColor.copy(alpha = 0.35f), style = Stroke(width = 5f))
            drawPath(polyPath, tierColor, style = Stroke(width = 2.2f))
            drawPath(polyPath, Color.White.copy(alpha = 0.8f), style = Stroke(width = 1f))

            // Pulsing Core Singularity
            drawCircle(
                color = tierColor.copy(alpha = 0.25f),
                radius = polyRadius * 0.65f,
                center = center
            )
            drawCircle(
                color = Color.White,
                radius = polyRadius * 0.25f,
                center = center
            )
        }

        // Telemetry Badge
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(6.dp).align(Alignment.BottomCenter)
        ) {
            Box(
                modifier = Modifier
                    .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                    .border(1.dp, tierColor.copy(alpha = 0.8f), CutCornerShape(4.dp))
                    .padding(horizontal = 8.dp, vertical = 2.dp)
            ) {
                Text(
                    text = "REACTOR // LVL $level",
                    color = tierColor,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

// ==============================================================================
// 👾 2. DISTINCTIVE CYBERPUNK MONSTER MASKS (19 UNIQUE BEASTS)
// ==============================================================================

@Composable
fun ProceduralMonsterMask(
    monsterIndex: Int,
    name: String,
    modifier: Modifier = Modifier
) {
    val threatColor = when {
        monsterIndex >= 15 -> EidosRed            // Singularity Apex Boss
        monsterIndex >= 8 -> ZzzHotMagenta        // Elite Nightmares
        else -> Color(0xFF00E5FF)                // Deep Network Glitches
    }

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF07090E))
            .border(1.5.dp, threatColor, CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)

            // 1. Digital Scanlines
            var sy = 0f
            while (sy < size.height) {
                drawLine(
                    color = Color.Black.copy(alpha = 0.35f),
                    start = Offset(0f, sy),
                    end = Offset(size.width, sy),
                    strokeWidth = 2f
                )
                sy += 8f
            }

            // 2. Tactical Reticle Brackets
            val reticleR = minDim * 0.42f
            drawCircle(
                color = threatColor.copy(alpha = 0.20f),
                radius = reticleR,
                center = center,
                style = Stroke(width = 1f, pathEffect = PathEffect.dashPathEffect(floatArrayOf(12f, 12f), 0f))
            )

            // 3. Draw Unique Iconic Archetype Silhouette
            when (monsterIndex) {
                1 -> drawParasiteSilhuette(threatColor, center, minDim * 0.36f)
                2 -> drawGlitchGhostSilhuette(threatColor, center, minDim * 0.36f)
                3 -> drawSentryDroneSilhuette(threatColor, center, minDim * 0.36f)
                4 -> drawLogicBombSilhuette(threatColor, center, minDim * 0.36f)
                5 -> drawCryptoMinerSilhuette(threatColor, center, minDim * 0.36f)
                6 -> drawSpamHydraSilhuette(threatColor, center, minDim * 0.36f)
                7 -> drawFatalGlitchSilhuette(threatColor, center, minDim * 0.36f)
                8 -> drawDarknetAssassinSilhuette(threatColor, center, minDim * 0.36f)
                9 -> drawAiDominatorSilhuette(threatColor, center, minDim * 0.36f)
                10 -> drawEraserSilhuette(threatColor, center, minDim * 0.36f)
                11 -> drawNeuralPhantomSilhuette(threatColor, center, minDim * 0.36f)
                12 -> drawCyberLichSilhuette(threatColor, center, minDim * 0.36f)
                13 -> drawArchitectSilhuette(threatColor, center, minDim * 0.36f)
                14 -> drawCodeDevourerSilhuette(threatColor, center, minDim * 0.36f)
                15 -> drawCoreSentinelSilhuette(threatColor, center, minDim * 0.36f)
                16 -> drawOmniSynthesisSilhuette(threatColor, center, minDim * 0.36f)
                17 -> drawMachineGodSilhuette(threatColor, center, minDim * 0.36f)
                18 -> drawVoidNomadSilhuette(threatColor, center, minDim * 0.36f)
                else -> drawEntropySingularitySilhuette(threatColor, center, minDim * 0.36f)
            }

            // Corner Brackets
            val bSize = minDim * 0.1f
            val bPad = minDim * 0.08f
            drawLine(threatColor, Offset(bPad, bPad), Offset(bPad + bSize, bPad), 2f)
            drawLine(threatColor, Offset(bPad, bPad), Offset(bPad, bPad + bSize), 2f)
            drawLine(threatColor, Offset(size.width - bPad, bPad), Offset(size.width - bPad - bSize, bPad), 2f)
            drawLine(threatColor, Offset(size.width - bPad, bPad), Offset(size.width - bPad, bPad + bSize), 2f)
            drawLine(threatColor, Offset(bPad, size.height - bPad), Offset(bPad + bSize, size.height - bPad), 2f)
            drawLine(threatColor, Offset(bPad, size.height - bPad), Offset(bPad, size.height - bPad - bSize), 2f)
            drawLine(threatColor, Offset(size.width - bPad, size.height - bPad), Offset(size.width - bPad - bSize, size.height - bPad), 2f)
            drawLine(threatColor, Offset(size.width - bPad, size.height - bPad), Offset(size.width - bPad, size.height - bPad - bSize), 2f)
        }

        // Threat Tier Badge
        Box(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 6.dp)
                .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                .border(1.dp, threatColor.copy(alpha = 0.8f), CutCornerShape(4.dp))
                .padding(horizontal = 6.dp, vertical = 2.dp)
        ) {
            val tierLabel = when {
                monsterIndex >= 17 -> "DEUS APEX"
                monsterIndex >= 14 -> "SINGULARITY"
                monsterIndex >= 8 -> "ELITE HOSTILE"
                else -> "VIRAL ENTITY"
            }
            Text(
                text = "THREAT #$monsterIndex // $tierLabel",
                color = threatColor,
                fontSize = 9.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

// ==============================================================================
// ⚔️ 3. PROCEDURAL EQUIPMENT CARDS WITH GRANULAR ARCHETYPES
// ==============================================================================

@Composable
fun ProceduralEquipmentCard(
    name: String,
    hash: Int,
    modifier: Modifier = Modifier,
    customBorder: Color = Color.Unspecified
) {
    val subType = remember(name) {
        when {
            // Weapons
            name.contains("rifle") || name.contains("railgun") || name.contains("снайпер") || name.contains("винтовка") -> "weapon_rifle"
            name.contains("pistol") || name.contains("пистолет") || name.contains("револьвер") -> "weapon_pistol"
            name.contains("hammer") || name.contains("молот") || name.contains("дубинка") || name.contains("baton") -> "weapon_hammer"
            name.contains("whip") || name.contains("хлыст") || name.contains("monowire") -> "weapon_whip"
            name.contains("blade") || name.contains("sword") || name.contains("knife") || name.contains("katana") ||
            name.contains("slicer") || name.contains("клинок") || name.contains("меч") || name.contains("нож") ||
            name.contains("катана") || name.contains("оружие") -> "weapon_blade"

            // Armors
            name.contains("jacket") || name.contains("hoodie") || name.contains("cloak") || name.contains("куртка") || name.contains("плащ") -> "armor_jacket"
            name.contains("shield") || name.contains("aegis") || name.contains("щит") -> "armor_shield"
            name.contains("armor") || name.contains("suit") || name.contains("titan") || name.contains("exoskeleton") || name.contains("броня") || name.contains("жилет") -> "armor_heavy"

            // Helmets & Heads
            name.contains("crown") || name.contains("диадема") || name.contains("корона") -> "helmet_crown"
            name.contains("goggles") || name.contains("visor") || name.contains("очки") || name.contains("визор") -> "helmet_goggles"
            name.contains("head") || name.contains("helmet") || name.contains("mask") || name.contains("шлем") || name.contains("маска") -> "helmet_full"

            // Relics & Artifacts
            name.contains("vampire") || name.contains("blood") || name.contains("кров") -> "relic_vampire"
            name.contains("demon") || name.contains("максвелл") || name.contains("демон") -> "relic_demon"
            name.contains("shard") || name.contains("осколок") || name.contains("эйдос") -> "relic_shard"

            // Chips
            name.contains("chip") || name.contains("core") || name.contains("ram") || name.contains("link") ||
            name.contains("gate") || name.contains("booster") || name.contains("чип") || name.contains("модуль") -> "chip"

            // Consumables & Tools
            name.contains("compass") || name.contains("компас") || name.contains("навигатор") -> "tool_compass"
            name.contains("battery") || name.contains("cell") || name.contains("батарея") || name.contains("аккумулятор") -> "consumable_battery"
            name.contains("cryo") || name.contains("крио") || name.contains("capsule") || name.contains("капсула") -> "consumable_cryo"
            name.contains("emp") || name.contains("grenade") || name.contains("граната") -> "consumable_emp"
            name.contains("disk") || name.contains("drive") || name.contains("wiper") || name.contains("чистка") || name.contains("диск") -> "consumable_disk"
            name.contains("key") || name.contains("crowbar") || name.contains("scanner") || name.contains("ключ") -> "tool_key"
            else -> "consumable_stim"
        }
    }

    // Determine rarity color
    val rarityColor = remember(name, customBorder) {
        if (customBorder != Color.Unspecified && customBorder != Color.Transparent) {
            customBorder
        } else {
            when {
                name.contains("glitch") || name.contains("abyssal") || name.contains("void") || name.contains("скверн") -> Color(0xFFFF0055)
                name.contains("god") || name.contains("legendary") || name.contains("banhammer") || name.contains("золот") -> Color(0xFFFFD700)
                name.contains("epic") || name.contains("hyper") || name.contains("quantum") -> Color(0xFFB026FF)
                name.contains("rare") || name.contains("proto") -> Color(0xFF00E5FF)
                name.contains("uncommon") -> Color(0xFF00FF66)
                subType.startsWith("weapon") -> Color(0xFFFF3366)
                subType.startsWith("armor") -> Color(0xFF00E5FF)
                subType.startsWith("helmet") -> Color(0xFFFFB300)
                subType.startsWith("relic") -> Color(0xFFFF0055)
                subType == "chip" -> Color(0xFF9933FF)
                subType == "tool_compass" -> Color(0xFF00E5FF)
                else -> Color(0xFF00FFCC)
            }
        }
    }

    Box(
        modifier = modifier
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF070B10))
            .border(1.5.dp, rarityColor, CutCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val minDim = minOf(size.width, size.height)

            // PCB Circuit Traces
            drawPcbTraces(rarityColor.copy(alpha = 0.22f), size, hash)

            // Granular Vector Silhouette
            when (subType) {
                "weapon_blade" -> drawVectorBlade(rarityColor, center, minDim * 0.38f)
                "weapon_rifle" -> drawVectorRifle(rarityColor, center, minDim * 0.38f)
                "weapon_pistol" -> drawVectorPistol(rarityColor, center, minDim * 0.38f)
                "weapon_hammer" -> drawVectorHammer(rarityColor, center, minDim * 0.38f)
                "weapon_whip" -> drawVectorWhip(rarityColor, center, minDim * 0.38f)

                "armor_jacket" -> drawVectorJacket(rarityColor, center, minDim * 0.38f)
                "armor_heavy" -> drawVectorExoskeleton(rarityColor, center, minDim * 0.38f)
                "armor_shield" -> drawVectorShield(rarityColor, center, minDim * 0.38f)

                "helmet_crown" -> drawVectorCrown(rarityColor, center, minDim * 0.38f)
                "helmet_goggles" -> drawVectorGoggles(rarityColor, center, minDim * 0.38f)
                "helmet_full" -> drawVectorFullHelmet(rarityColor, center, minDim * 0.38f)

                "relic_vampire" -> drawVectorBloodCrown(rarityColor, center, minDim * 0.38f)
                "relic_demon" -> drawVectorDemonHead(rarityColor, center, minDim * 0.38f)
                "relic_shard" -> drawVectorShard(rarityColor, center, minDim * 0.38f)

                "chip" -> drawVectorChip(rarityColor, center, minDim * 0.38f)
                "tool_compass" -> drawVectorCompass(rarityColor, center, minDim * 0.38f)
                "consumable_battery" -> drawVectorEnergyCell(rarityColor, center, minDim * 0.38f)
                "consumable_cryo" -> drawVectorCryoCapsule(rarityColor, center, minDim * 0.38f)
                "consumable_emp" -> drawVectorEmpSphere(rarityColor, center, minDim * 0.38f)
                "consumable_disk" -> drawVectorDatadisk(rarityColor, center, minDim * 0.38f)
                "tool_key" -> drawVectorKey(rarityColor, center, minDim * 0.38f)
                else -> drawVectorStim(rarityColor, center, minDim * 0.38f)
            }
        }

        // Telemetry Labels
        Text(
            text = "SYS // 0x${abs(hash % 256).toString(16).uppercase().padStart(2, '0')}",
            color = rarityColor.copy(alpha = 0.7f),
            fontSize = 8.sp,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.TopStart).padding(6.dp)
        )

        val archetypeLabel = when {
            subType.startsWith("weapon") -> "WEAPON"
            subType.startsWith("armor") -> "ARMOR"
            subType.startsWith("helmet") -> "OPTICS"
            subType.startsWith("relic") -> "RELIC"
            subType == "chip" -> "CHIP"
            subType == "tool_compass" -> "NAV-RADAR"
            subType == "tool_key" -> "KEY"
            subType == "consumable_battery" -> "ENERGY"
            subType == "consumable_cryo" -> "CRYO"
            subType == "consumable_emp" -> "EMP"
            else -> "MED/SUPPLY"
        }
        Text(
            text = archetypeLabel,
            color = rarityColor,
            fontSize = 8.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.align(Alignment.BottomEnd).padding(6.dp)
        )
    }
}

// ==============================================================================
// 📐 SILHOUETTE DRAWING HELPERS (NEON GLOW + VECTOR PATHS)
// ==============================================================================

private fun DrawScope.drawPcbTraces(color: Color, canvasSize: Size, hash: Int) {
    val rng = kotlin.random.Random(hash)
    val stroke = Stroke(width = 1.2f)

    for (i in 0 until 5) {
        val startX = (rng.nextFloat() * 0.8f + 0.1f) * canvasSize.width
        val startY = if (rng.nextBoolean()) 0f else canvasSize.height
        val midY = (rng.nextFloat() * 0.6f + 0.2f) * canvasSize.height
        val endX = (rng.nextFloat() * 0.8f + 0.1f) * canvasSize.width

        val path = Path().apply {
            moveTo(startX, startY)
            lineTo(startX, midY)
            lineTo(endX, midY)
            lineTo(endX, if (startY == 0f) canvasSize.height else 0f)
        }
        drawPath(path, color, style = stroke)
        drawCircle(color, radius = 2f, center = Offset(endX, midY))
    }
}

// --- WEAPONS ---

private fun DrawScope.drawVectorBlade(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Curved Cyber Katana
        moveTo(center.x + size * 0.1f, center.y - size * 0.95f)
        lineTo(center.x + size * 0.25f, center.y - size * 0.65f)
        lineTo(center.x + size * 0.16f, center.y + size * 0.35f)
        // Guard (Tsuba)
        lineTo(center.x + size * 0.40f, center.y + size * 0.40f)
        lineTo(center.x + size * 0.38f, center.y + size * 0.48f)
        lineTo(center.x + size * 0.10f, center.y + size * 0.48f)
        // Hilt
        lineTo(center.x + size * 0.08f, center.y + size * 0.95f)
        lineTo(center.x - size * 0.06f, center.y + size * 0.95f)
        lineTo(center.x - size * 0.08f, center.y + size * 0.48f)
        // Guard left
        lineTo(center.x - size * 0.38f, center.y + size * 0.48f)
        lineTo(center.x - size * 0.40f, center.y + size * 0.40f)
        // Back edge
        lineTo(center.x - size * 0.12f, center.y + size * 0.35f)
        lineTo(center.x - size * 0.05f, center.y - size * 0.65f)
        close()
    }
    // Glow & Fill
    drawPath(path, color.copy(alpha = 0.22f))
    drawPath(path, color.copy(alpha = 0.35f), style = Stroke(width = 5f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Hot Plasma Core Line
    drawLine(Color.White, Offset(center.x + size * 0.05f, center.y - size * 0.8f), Offset(center.x + size * 0.04f, center.y + size * 0.3f), 1.5f)
}

private fun DrawScope.drawVectorRifle(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // High-Tech Cyber Railgun / Sniper
        moveTo(center.x - size * 0.85f, center.y - size * 0.10f)
        lineTo(center.x + size * 0.85f, center.y - size * 0.10f) // Long Barrel
        lineTo(center.x + size * 0.85f, center.y + size * 0.08f) // Muzzle Brake
        lineTo(center.x + size * 0.30f, center.y + size * 0.08f)
        lineTo(center.x + size * 0.15f, center.y + size * 0.55f) // Magazine
        lineTo(center.x + size * 0.00f, center.y + size * 0.55f)
        lineTo(center.x + size * 0.08f, center.y + size * 0.12f)
        lineTo(center.x - size * 0.20f, center.y + size * 0.12f)
        lineTo(center.x - size * 0.30f, center.y + size * 0.55f) // Pistol Grip
        lineTo(center.x - size * 0.45f, center.y + size * 0.50f)
        lineTo(center.x - size * 0.38f, center.y + size * 0.10f)
        lineTo(center.x - size * 0.85f, center.y + size * 0.25f) // Stock
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Scope on top
    drawRect(color, topLeft = Offset(center.x - size * 0.25f, center.y - size * 0.32f), size = Size(size * 0.6f, size * 0.15f))
    drawLine(Color.White, Offset(center.x - size * 0.7f, center.y - size * 0.01f), Offset(center.x + size * 0.75f, center.y - size * 0.01f), 1.5f)
}

private fun DrawScope.drawVectorPistol(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Smart Handgun
        moveTo(center.x - size * 0.55f, center.y - size * 0.35f)
        lineTo(center.x + size * 0.60f, center.y - size * 0.35f) // Slide
        lineTo(center.x + size * 0.60f, center.y + size * 0.05f)
        lineTo(center.x + size * 0.05f, center.y + size * 0.05f)
        lineTo(center.x - size * 0.10f, center.y + size * 0.65f) // Grip
        lineTo(center.x - size * 0.38f, center.y + size * 0.60f)
        lineTo(center.x - size * 0.22f, center.y + size * 0.05f)
        lineTo(center.x - size * 0.55f, center.y + size * 0.05f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Laser Sight under barrel
    drawLine(Color.Red, Offset(center.x + size * 0.55f, center.y + size * 0.15f), Offset(center.x + size * 0.85f, center.y + size * 0.15f), 1.5f)
}

private fun DrawScope.drawVectorHammer(color: Color, center: Offset, size: Float) {
    // Banhammer / Kinetic Heavy Mallet
    val head = Rect(center.x - size * 0.55f, center.y - size * 0.75f, center.x + size * 0.55f, center.y - size * 0.20f)
    drawRect(color.copy(alpha = 0.30f), topLeft = head.topLeft, size = head.size)
    drawRect(color, topLeft = head.topLeft, size = head.size, style = Stroke(width = 2.5f))
    // Energy discharge in hammer head
    drawLine(Color.White, Offset(center.x - size * 0.4f, center.y - size * 0.48f), Offset(center.x + size * 0.4f, center.y - size * 0.48f), 2f)

    // Handle
    val shaft = Path().apply {
        moveTo(center.x - size * 0.08f, head.bottom)
        lineTo(center.x + size * 0.08f, head.bottom)
        lineTo(center.x + size * 0.08f, center.y + size * 0.85f)
        lineTo(center.x - size * 0.08f, center.y + size * 0.85f)
        close()
    }
    drawPath(shaft, color, style = Stroke(width = 2f))
}

private fun DrawScope.drawVectorWhip(color: Color, center: Offset, size: Float) {
    // Monowire / Energy Whip
    val path = Path().apply {
        moveTo(center.x - size * 0.5f, center.y + size * 0.7f)
        cubicTo(
            center.x - size * 0.7f, center.y - size * 0.2f,
            center.x + size * 0.6f, center.y - size * 0.6f,
            center.x + size * 0.1f, center.y + size * 0.2f
        )
        cubicTo(
            center.x - size * 0.2f, center.y + size * 0.6f,
            center.x + size * 0.5f, center.y + size * 0.5f,
            center.x + size * 0.6f, center.y - size * 0.1f
        )
    }
    drawPath(path, color.copy(alpha = 0.3f), style = Stroke(width = 5f))
    drawPath(path, color, style = Stroke(width = 2.5f))
    drawPath(path, Color.White, style = Stroke(width = 1f))
}

// --- ARMORS ---

private fun DrawScope.drawVectorJacket(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // High Collar Street Jacket
        moveTo(center.x - size * 0.25f, center.y - size * 0.75f)
        lineTo(center.x + size * 0.25f, center.y - size * 0.75f)
        lineTo(center.x + size * 0.75f, center.y - size * 0.40f) // Shoulders
        lineTo(center.x + size * 0.50f, center.y + size * 0.15f)
        lineTo(center.x + size * 0.42f, center.y + size * 0.75f) // Waist
        lineTo(center.x - size * 0.42f, center.y + size * 0.75f)
        lineTo(center.x - size * 0.50f, center.y + size * 0.15f)
        lineTo(center.x - size * 0.75f, center.y - size * 0.40f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Diagonal Cyber Zipper
    drawLine(Color.White, Offset(center.x - size * 0.12f, center.y - size * 0.65f), Offset(center.x + size * 0.05f, center.y + size * 0.65f), 1.8f)
}

private fun DrawScope.drawVectorExoskeleton(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Heavy Armored Carapace
        moveTo(center.x - size * 0.35f, center.y - size * 0.7f)
        lineTo(center.x + size * 0.35f, center.y - size * 0.7f)
        lineTo(center.x + size * 0.75f, center.y - size * 0.35f)
        lineTo(center.x + size * 0.55f, center.y + size * 0.25f)
        lineTo(center.x + size * 0.35f, center.y + size * 0.85f)
        lineTo(center.x, center.y + size * 0.95f)
        lineTo(center.x - size * 0.35f, center.y + size * 0.85f)
        lineTo(center.x - size * 0.55f, center.y + size * 0.25f)
        lineTo(center.x - size * 0.75f, center.y - size * 0.35f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.5f))
    // Core Reactor Node
    drawCircle(color, radius = size * 0.22f, center = Offset(center.x, center.y - size * 0.1f), style = Stroke(width = 2f))
    drawCircle(Color.White, radius = size * 0.09f, center = Offset(center.x, center.y - size * 0.1f))
}

private fun DrawScope.drawVectorShield(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Hexagonal Energy Barrier
        val r = size * 0.85f
        for (i in 0 until 6) {
            val angle = i * (PI / 3.0) - (PI / 2.0)
            val px = center.x + cos(angle).toFloat() * r
            val py = center.y + sin(angle).toFloat() * r
            if (i == 0) moveTo(px, py) else lineTo(px, py)
        }
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.5f))
    // Inner honeycomb cross
    drawCircle(Color.White, radius = size * 0.12f, center = center)
    drawLine(color, Offset(center.x - size * 0.4f, center.y), Offset(center.x + size * 0.4f, center.y), 1.5f)
    drawLine(color, Offset(center.x, center.y - size * 0.4f), Offset(center.x, center.y + size * 0.4f), 1.5f)
}

// --- HELMETS & HEAD ---

private fun DrawScope.drawVectorCrown(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Overclock Crown / Spired Neural Diadem
        moveTo(center.x - size * 0.6f, center.y + size * 0.3f)
        lineTo(center.x - size * 0.7f, center.y - size * 0.5f) // Spire left
        lineTo(center.x - size * 0.3f, center.y - size * 0.1f)
        lineTo(center.x, center.y - size * 0.85f)             // Tall Center Spire
        lineTo(center.x + size * 0.3f, center.y - size * 0.1f)
        lineTo(center.x + size * 0.7f, center.y - size * 0.5f) // Spire right
        lineTo(center.x + size * 0.6f, center.y + size * 0.3f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Glowing Crown Gems
    drawCircle(Color.White, radius = 3.5f, center = Offset(center.x, center.y - size * 0.75f))
    drawCircle(Color.White, radius = 2.5f, center = Offset(center.x - size * 0.6f, center.y - size * 0.42f))
    drawCircle(Color.White, radius = 2.5f, center = Offset(center.x + size * 0.6f, center.y - size * 0.42f))
}

private fun DrawScope.drawVectorGoggles(color: Color, center: Offset, size: Float) {
    // Cyber VR Goggles / Optics
    val leftLens = Rect(center.x - size * 0.65f, center.y - size * 0.25f, center.x - size * 0.1f, center.y + size * 0.25f)
    val rightLens = Rect(center.x + size * 0.1f, center.y - size * 0.25f, center.x + size * 0.65f, center.y + size * 0.25f)

    drawRect(color.copy(alpha = 0.3f), topLeft = leftLens.topLeft, size = leftLens.size)
    drawRect(color, topLeft = leftLens.topLeft, size = leftLens.size, style = Stroke(width = 2.2f))
    drawRect(color.copy(alpha = 0.3f), topLeft = rightLens.topLeft, size = rightLens.size)
    drawRect(color, topLeft = rightLens.topLeft, size = rightLens.size, style = Stroke(width = 2.2f))

    // Bridge & Straps
    drawLine(color, Offset(leftLens.right, center.y), Offset(rightLens.left, center.y), 2.5f)
    drawLine(color, Offset(leftLens.left, center.y), Offset(center.x - size * 0.85f, center.y), 1.5f)
    drawLine(color, Offset(rightLens.right, center.y), Offset(center.x + size * 0.85f, center.y), 1.5f)
}

private fun DrawScope.drawVectorFullHelmet(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        moveTo(center.x - size * 0.45f, center.y - size * 0.55f)
        lineTo(center.x, center.y - size * 0.85f)
        lineTo(center.x + size * 0.45f, center.y - size * 0.55f)
        lineTo(center.x + size * 0.60f, center.y + size * 0.10f)
        lineTo(center.x + size * 0.35f, center.y + size * 0.75f)
        lineTo(center.x - size * 0.35f, center.y + size * 0.75f)
        lineTo(center.x - size * 0.60f, center.y + size * 0.10f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Glowing Visor
    drawRect(Color.White.copy(alpha = 0.85f), topLeft = Offset(center.x - size * 0.35f, center.y - size * 0.05f), size = Size(size * 0.70f, size * 0.18f))
}

// --- CHIPS & SUPPLIES ---

private fun DrawScope.drawVectorChip(color: Color, center: Offset, size: Float) {
    val body = Rect(center.x - size * 0.55f, center.y - size * 0.55f, center.x + size * 0.55f, center.y + size * 0.55f)
    drawRect(color.copy(alpha = 0.30f), topLeft = body.topLeft, size = body.size)
    drawRect(color, topLeft = body.topLeft, size = body.size, style = Stroke(width = 2.5f))

    // 8 gold pins
    val pinLen = size * 0.2f
    for (i in -2..2) {
        val off = i * (size * 0.2f)
        drawLine(color, Offset(center.x + off, body.top), Offset(center.x + off, body.top - pinLen), 1.8f)
        drawLine(color, Offset(center.x + off, body.bottom), Offset(center.x + off, body.bottom + pinLen), 1.8f)
        drawLine(color, Offset(body.left, center.y + off), Offset(body.left - pinLen, center.y + off), 1.8f)
        drawLine(color, Offset(body.right, center.y + off), Offset(body.right + pinLen, center.y + off), 1.8f)
    }
    drawCircle(Color.White, radius = size * 0.18f, center = center)
}

private fun DrawScope.drawVectorBattery(color: Color, center: Offset, size: Float) {
    // Energy Cell / Heavy Capacitor
    val rect = Rect(center.x - size * 0.40f, center.y - size * 0.65f, center.x + size * 0.40f, center.y + size * 0.65f)
    drawRect(color.copy(alpha = 0.25f), topLeft = rect.topLeft, size = rect.size)
    drawRect(color, topLeft = rect.topLeft, size = rect.size, style = Stroke(width = 2.2f))

    // Top Terminal
    drawRect(color, topLeft = Offset(center.x - size * 0.15f, center.y - size * 0.82f), size = Size(size * 0.30f, size * 0.16f))

    // Charge Bars
    for (b in 0..2) {
        val by = center.y + size * 0.35f - (b * size * 0.35f)
        drawRect(Color.White.copy(alpha = 0.85f), topLeft = Offset(center.x - size * 0.25f, by), size = Size(size * 0.50f, size * 0.15f))
    }
}

private fun DrawScope.drawVectorDatadisk(color: Color, center: Offset, size: Float) {
    // Cyber Data Disk / Eraser Module
    drawCircle(color.copy(alpha = 0.25f), radius = size * 0.70f, center = center)
    drawCircle(color, radius = size * 0.70f, center = center, style = Stroke(width = 2.2f))
    drawCircle(color, radius = size * 0.35f, center = center, style = Stroke(width = 1.8f))
    drawCircle(Color.White, radius = size * 0.12f, center = center)
}

private fun DrawScope.drawVectorKey(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Quantum Data Spike Key
        moveTo(center.x - size * 0.12f, center.y - size * 0.75f)
        lineTo(center.x + size * 0.12f, center.y - size * 0.75f)
        lineTo(center.x + size * 0.12f, center.y + size * 0.15f)
        lineTo(center.x + size * 0.40f, center.y + size * 0.15f)
        lineTo(center.x + size * 0.40f, center.y + size * 0.30f)
        lineTo(center.x + size * 0.12f, center.y + size * 0.30f)
        lineTo(center.x + size * 0.30f, center.y + size * 0.48f)
        lineTo(center.x + size * 0.30f, center.y + size * 0.62f)
        lineTo(center.x + size * 0.12f, center.y + size * 0.62f)
        lineTo(center.x + size * 0.12f, center.y + size * 0.85f)
        lineTo(center.x - size * 0.12f, center.y + size * 0.85f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    drawCircle(color, radius = size * 0.32f, center = Offset(center.x, center.y - size * 0.55f), style = Stroke(width = 2.2f))
}

private fun DrawScope.drawVectorStim(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        // Pneumatic Hypospray Injector
        moveTo(center.x - size * 0.25f, center.y - size * 0.65f)
        lineTo(center.x + size * 0.25f, center.y - size * 0.65f)
        lineTo(center.x + size * 0.25f, center.y + size * 0.40f)
        lineTo(center.x, center.y + size * 0.85f) // Needle
        lineTo(center.x - size * 0.25f, center.y + size * 0.40f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.25f))
    drawPath(path, color, style = Stroke(width = 2.2f))
    // Glowing Med fluid
    drawRect(Color.White.copy(alpha = 0.65f), topLeft = Offset(center.x - size * 0.18f, center.y - size * 0.20f), size = Size(size * 0.36f, size * 0.45f))
}

private fun DrawScope.drawVectorCompass(color: Color, center: Offset, size: Float) {
    // Holographic Cyber-Compass & Navigational Radar
    val outerRadius = size * 0.75f
    drawCircle(color.copy(alpha = 0.15f), radius = outerRadius, center = center)
    drawCircle(color, radius = outerRadius, center = center, style = Stroke(width = 2.2f))
    drawCircle(color.copy(alpha = 0.5f), radius = outerRadius * 0.55f, center = center, style = Stroke(width = 1.2f))

    // 4 Cardinal Axis Ticks
    val tickLen = size * 0.18f
    drawLine(color, Offset(center.x, center.y - outerRadius), Offset(center.x, center.y - outerRadius + tickLen), 2.2f)
    drawLine(color, Offset(center.x, center.y + outerRadius), Offset(center.x, center.y + outerRadius - tickLen), 2.2f)
    drawLine(color, Offset(center.x - outerRadius, center.y), Offset(center.x - outerRadius + tickLen, center.y), 2.2f)
    drawLine(color, Offset(center.x + outerRadius, center.y), Offset(center.x + outerRadius - tickLen, center.y), 2.2f)

    // North Needle (Hot Red/Neon)
    val northNeedle = Path().apply {
        moveTo(center.x, center.y - outerRadius * 0.85f)
        lineTo(center.x + size * 0.14f, center.y)
        lineTo(center.x, center.y - size * 0.08f)
        lineTo(center.x - size * 0.14f, center.y)
        close()
    }
    drawPath(northNeedle, Color(0xFFFF2A6D))

    // South Needle (Dim/Steel)
    val southNeedle = Path().apply {
        moveTo(center.x, center.y + outerRadius * 0.85f)
        lineTo(center.x + size * 0.14f, center.y)
        lineTo(center.x, center.y + size * 0.08f)
        lineTo(center.x - size * 0.14f, center.y)
        close()
    }
    drawPath(southNeedle, color.copy(alpha = 0.45f))

    // Center Pivot Rivet
    drawCircle(Color.White, radius = size * 0.08f, center = center)
    drawCircle(Color(0xFF0D0D15), radius = size * 0.03f, center = center)
}

private fun DrawScope.drawVectorEnergyCell(color: Color, center: Offset, size: Float) {
    // High-Density Micro-Fusion Energy Cell
    val w = size * 0.65f
    val h = size * 1.05f
    val body = Rect(center.x - w / 2, center.y - h / 2, center.x + w / 2, center.y + h / 2)

    drawRect(color.copy(alpha = 0.20f), topLeft = body.topLeft, size = body.size)
    drawRect(color, topLeft = body.topLeft, size = body.size, style = Stroke(width = 2.2f))

    // Anode & Cathode Terminals
    val termW = w * 0.45f
    val termH = size * 0.12f
    drawRect(color, topLeft = Offset(center.x - termW / 2, body.top - termH), size = Size(termW, termH))
    drawRect(color, topLeft = Offset(center.x - termW / 2, body.bottom), size = Size(termW, termH * 0.6f))

    // 4 Neon Energy Fuel Bars
    for (i in 0 until 4) {
        val barY = body.top + (i * (h / 4.5f)) + size * 0.08f
        val barRect = Rect(center.x - w * 0.35f, barY, center.x + w * 0.35f, barY + size * 0.12f)
        drawRect(Color(0xFF00F0FF).copy(alpha = 0.85f), topLeft = barRect.topLeft, size = barRect.size)
        drawLine(Color.White, Offset(barRect.left + 3f, barRect.center.y), Offset(barRect.right - 3f, barRect.center.y), 1.5f)
    }

    // High Voltage Lightning Bolt Accent
    val bolt = Path().apply {
        moveTo(center.x + size * 0.05f, center.y - size * 0.25f)
        lineTo(center.x - size * 0.10f, center.y)
        lineTo(center.x + size * 0.02f, center.y)
        lineTo(center.x - size * 0.05f, center.y + size * 0.25f)
        lineTo(center.x + size * 0.10f, center.y - size * 0.02f)
        lineTo(center.x - size * 0.01f, center.y - size * 0.02f)
        close()
    }
    drawPath(bolt, Color(0xFFFFD700))
}

private fun DrawScope.drawVectorCryoCapsule(color: Color, center: Offset, size: Float) {
    // Sub-Zero Cryogenic Ampoule
    val capsuleWidth = size * 0.6f
    val capsuleHeight = size * 1.1f
    val top = center.y - capsuleHeight / 2
    val bottom = center.y + capsuleHeight / 2
    val left = center.x - capsuleWidth / 2
    val right = center.x + capsuleWidth / 2

    // Capsule Body (Rounded Pill)
    val pillPath = Path().apply {
        moveTo(left, top + capsuleWidth / 2)
        arcTo(Rect(left, top, right, top + capsuleWidth), 180f, 180f, false)
        lineTo(right, bottom - capsuleWidth / 2)
        arcTo(Rect(left, bottom - capsuleWidth, right, bottom), 0f, 180f, false)
        close()
    }
    drawPath(pillPath, Color(0xFF00E5FF).copy(alpha = 0.25f))
    drawPath(pillPath, Color(0xFF00E5FF), style = Stroke(width = 2.2f))

    // Metallic Restraint Rings
    drawRect(color, topLeft = Offset(left - 3f, center.y - size * 0.25f), size = Size(capsuleWidth + 6f, size * 0.10f))
    drawRect(color, topLeft = Offset(left - 3f, center.y + size * 0.15f), size = Size(capsuleWidth + 6f, size * 0.10f))

    // Hexagonal Nano-Snowflake in center
    val hexR = size * 0.18f
    for (i in 0 until 3) {
        val angle = i * (PI / 3.0)
        val p1 = Offset(center.x + cos(angle).toFloat() * hexR, center.y + sin(angle).toFloat() * hexR)
        val p2 = Offset(center.x - cos(angle).toFloat() * hexR, center.y - sin(angle).toFloat() * hexR)
        drawLine(Color.White, p1, p2, 1.8f)
    }
    drawCircle(Color.White, radius = 3f, center = center)
}

private fun DrawScope.drawVectorEmpSphere(color: Color, center: Offset, size: Float) {
    // Concentric Electromagnetic Pulse Grenade
    val r = size * 0.7f
    drawCircle(Color(0xFF7000FF).copy(alpha = 0.25f), radius = r, center = center)
    drawCircle(Color(0xFF00F0FF), radius = r, center = center, style = Stroke(width = 2.2f))
    drawCircle(color, radius = r * 0.65f, center = center, style = Stroke(width = 1.5f))

    // 4 Magnetic Discharger Nodes on rim
    for (i in 0 until 4) {
        val angle = i * (PI / 2.0) + (PI / 4.0)
        val nodeCenter = Offset(center.x + cos(angle).toFloat() * r, center.y + sin(angle).toFloat() * r)
        drawCircle(Color.White, radius = size * 0.10f, center = nodeCenter)
        drawCircle(Color(0xFFFF0055), radius = size * 0.05f, center = nodeCenter)
    }

    // High Voltage Arc Paths crossing core
    val arc1 = Path().apply {
        moveTo(center.x - r * 0.5f, center.y - r * 0.2f)
        lineTo(center.x - r * 0.1f, center.y + r * 0.1f)
        lineTo(center.x + r * 0.1f, center.y - r * 0.1f)
        lineTo(center.x + r * 0.5f, center.y + r * 0.2f)
    }
    drawPath(arc1, Color(0xFF00F0FF), style = Stroke(width = 2.2f))
    drawCircle(Color.White, radius = size * 0.12f, center = center)
}

private fun DrawScope.drawVectorBloodCrown(color: Color, center: Offset, size: Float) {
    // Sanguine Vampire Relic Crown with Dripping Vitality
    val bloodColor = Color(0xFFFF0044)
    val path = Path().apply {
        moveTo(center.x - size * 0.65f, center.y + size * 0.40f)
        lineTo(center.x - size * 0.75f, center.y - size * 0.35f) // Left Fang
        lineTo(center.x - size * 0.35f, center.y - size * 0.05f)
        lineTo(center.x, center.y - size * 0.80f)              // Central Blood Spire
        lineTo(center.x + size * 0.35f, center.y - size * 0.05f)
        lineTo(center.x + size * 0.75f, center.y - size * 0.35f) // Right Fang
        lineTo(center.x + size * 0.65f, center.y + size * 0.40f)
        close()
    }
    drawPath(path, bloodColor.copy(alpha = 0.30f))
    drawPath(path, bloodColor, style = Stroke(width = 2.4f))

    // Crimson Blood Drop falling from crown base
    val dropPath = Path().apply {
        moveTo(center.x, center.y + size * 0.25f)
        cubicTo(
            center.x + size * 0.15f, center.y + size * 0.55f,
            center.x + size * 0.15f, center.y + size * 0.85f,
            center.x, center.y + size * 0.85f
        )
        cubicTo(
            center.x - size * 0.15f, center.y + size * 0.85f,
            center.x - size * 0.15f, center.y + size * 0.55f,
            center.x, center.y + size * 0.25f
        )
        close()
    }
    drawPath(dropPath, bloodColor)
    drawCircle(Color.White, radius = 3f, center = Offset(center.x, center.y - size * 0.70f))
}

private fun DrawScope.drawVectorShard(color: Color, center: Offset, size: Float) {
    // Prismatic Eidos Singularity Shard
    val shardPath = Path().apply {
        moveTo(center.x, center.y - size * 0.90f)               // Top Apex
        lineTo(center.x + size * 0.45f, center.y - size * 0.15f) // Right Facet
        lineTo(center.x + size * 0.20f, center.y + size * 0.85f) // Bottom Right
        lineTo(center.x - size * 0.25f, center.y + size * 0.80f) // Bottom Left
        lineTo(center.x - size * 0.45f, center.y + size * 0.05f) // Left Facet
        close()
    }
    drawPath(shardPath, color.copy(alpha = 0.35f))
    drawPath(shardPath, color, style = Stroke(width = 2.4f))

    // Facet Cleave Lines
    drawLine(Color.White, Offset(center.x, center.y - size * 0.90f), center, 1.8f)
    drawLine(Color.White, Offset(center.x + size * 0.45f, center.y - size * 0.15f), center, 1.4f)
    drawLine(Color.White, Offset(center.x - size * 0.45f, center.y + size * 0.05f), center, 1.4f)
    drawLine(Color.White, Offset(center.x + size * 0.20f, center.y + size * 0.85f), center, 1.4f)
    drawLine(Color.White, Offset(center.x - size * 0.25f, center.y + size * 0.80f), center, 1.4f)

    // Inner Glowing Core
    drawCircle(Color.White, radius = size * 0.15f, center = center)
    drawCircle(Color(0xFF00F0FF), radius = size * 0.08f, center = center)
}

private fun DrawScope.drawVectorDemonHead(color: Color, center: Offset, size: Float) {
    // Maxwell's Demon Horned Cyber-Mask
    val demonColor = Color(0xFFFF2A6D)
    val headPath = Path().apply {
        // Left Horn
        moveTo(center.x - size * 0.25f, center.y - size * 0.20f)
        lineTo(center.x - size * 0.70f, center.y - size * 0.85f)
        lineTo(center.x - size * 0.45f, center.y - size * 0.15f)
        // Crown Top
        lineTo(center.x, center.y - size * 0.35f)
        // Right Horn
        lineTo(center.x + size * 0.45f, center.y - size * 0.15f)
        lineTo(center.x + size * 0.70f, center.y - size * 0.85f)
        lineTo(center.x + size * 0.25f, center.y - size * 0.20f)
        // Cheeks & Jaw
        lineTo(center.x + size * 0.45f, center.y + size * 0.25f)
        lineTo(center.x + size * 0.20f, center.y + size * 0.80f) // Chin Right
        lineTo(center.x - size * 0.20f, center.y + size * 0.80f) // Chin Left
        lineTo(center.x - size * 0.45f, center.y + size * 0.25f)
        close()
    }
    drawPath(headPath, demonColor.copy(alpha = 0.25f))
    drawPath(headPath, demonColor, style = Stroke(width = 2.4f))

    // Slanted Demon Eyes (Glowing Neon Yellow/Gold)
    val leftEye = Path().apply {
        moveTo(center.x - size * 0.32f, center.y)
        lineTo(center.x - size * 0.08f, center.y + size * 0.08f)
        lineTo(center.x - size * 0.10f, center.y + size * 0.14f)
        close()
    }
    val rightEye = Path().apply {
        moveTo(center.x + size * 0.32f, center.y)
        lineTo(center.x + size * 0.08f, center.y + size * 0.08f)
        lineTo(center.x + size * 0.10f, center.y + size * 0.14f)
        close()
    }
    drawPath(leftEye, Color(0xFFFFD700))
    drawPath(rightEye, Color(0xFFFFD700))

    // Cyber Respiration Grille on Chin
    drawLine(demonColor, Offset(center.x - size * 0.12f, center.y + size * 0.50f), Offset(center.x + size * 0.12f, center.y + size * 0.50f), 1.8f)
    drawLine(demonColor, Offset(center.x - size * 0.08f, center.y + size * 0.62f), Offset(center.x + size * 0.08f, center.y + size * 0.62f), 1.8f)
}

// ==============================================================================
// 👾 DETAILED ICONIC BEAST DRAWINGS (19 DISTINCT MONSTER ARCHETYPES)
// ==============================================================================

// 1: 🦠 Цифровой Паразит (Capsid + 4 Cyber Tentacles)
private fun DrawScope.drawParasiteSilhuette(color: Color, center: Offset, size: Float) {
    drawCircle(color.copy(alpha = 0.25f), radius = size * 0.45f, center = center)
    drawCircle(color, radius = size * 0.45f, center = center, style = Stroke(width = 2.2f))
    // 4 Curved Tentacles
    val t = size * 0.75f
    drawLine(color, Offset(center.x - size * 0.3f, center.y - size * 0.3f), Offset(center.x - t, center.y - t), 2f)
    drawLine(color, Offset(center.x + size * 0.3f, center.y - size * 0.3f), Offset(center.x + t, center.y - t), 2f)
    drawLine(color, Offset(center.x - size * 0.3f, center.y + size * 0.3f), Offset(center.x - t, center.y + t), 2f)
    drawLine(color, Offset(center.x + size * 0.3f, center.y + size * 0.3f), Offset(center.x + t, center.y + t), 2f)
    // Evil Red Eye Core
    drawCircle(Color.Red, radius = size * 0.15f, center = center)
}

// 2: 👻 Призрак Глитча (Fragmented Phantom)
private fun DrawScope.drawGlitchGhostSilhuette(color: Color, center: Offset, size: Float) {
    for (i in -3..3) {
        val y = center.y + (i * size * 0.22f)
        val shift = if (i % 2 == 0) size * 0.12f else -size * 0.12f
        val w = size * (0.8f - abs(i) * 0.12f)
        drawRect(color.copy(alpha = 0.35f), topLeft = Offset(center.x - w / 2 + shift, y), size = Size(w, size * 0.14f))
    }
    // Glitched Eye slits
    drawRect(Color.White, topLeft = Offset(center.x - size * 0.35f, center.y - size * 0.15f), size = Size(size * 0.2f, size * 0.08f))
    drawRect(Color.White, topLeft = Offset(center.x + size * 0.15f, center.y - size * 0.15f), size = Size(size * 0.2f, size * 0.08f))
}

// 3: 🚁 Дрон-Страж (Quad-rotor Chassis & Laser Optic)
private fun DrawScope.drawSentryDroneSilhuette(color: Color, center: Offset, size: Float) {
    // Body pod
    drawRect(color.copy(alpha = 0.3f), topLeft = Offset(center.x - size * 0.4f, center.y - size * 0.25f), size = Size(size * 0.8f, size * 0.5f))
    drawRect(color, topLeft = Offset(center.x - size * 0.4f, center.y - size * 0.25f), size = Size(size * 0.8f, size * 0.5f), style = Stroke(width = 2.2f))
    // Rotors left & right
    drawLine(color, Offset(center.x - size * 0.4f, center.y), Offset(center.x - size * 0.85f, center.y), 2f)
    drawLine(color, Offset(center.x + size * 0.4f, center.y), Offset(center.x + size * 0.85f, center.y), 2f)
    drawCircle(Color.White, radius = size * 0.18f, center = Offset(center.x - size * 0.85f, center.y), style = Stroke(width = 1.5f))
    drawCircle(Color.White, radius = size * 0.18f, center = Offset(center.x + size * 0.85f, center.y), style = Stroke(width = 1.5f))
    // Central Targeting Optic
    drawCircle(Color.Red, radius = size * 0.12f, center = center)
}

// 4: 💣 Логическая Бомба (Spherical Mine + Countdown)
private fun DrawScope.drawLogicBombSilhuette(color: Color, center: Offset, size: Float) {
    drawCircle(color.copy(alpha = 0.3f), radius = size * 0.65f, center = center)
    drawCircle(color, radius = size * 0.65f, center = center, style = Stroke(width = 2.5f))
    // Spikes
    for (i in 0 until 8) {
        val angle = i * (PI / 4.0)
        val p1 = Offset(center.x + cos(angle).toFloat() * size * 0.65f, center.y + sin(angle).toFloat() * size * 0.65f)
        val p2 = Offset(center.x + cos(angle).toFloat() * size * 0.95f, center.y + sin(angle).toFloat() * size * 0.95f)
        drawLine(color, p1, p2, 2f)
    }
    // Danger Core
    drawCircle(Color.Red, radius = size * 0.22f, center = center)
}

// 5: ⛏ Крипто-Майнер (Cyber Pickaxe & Hash Block)
private fun DrawScope.drawCryptoMinerSilhuette(color: Color, center: Offset, size: Float) {
    // Pickaxe head
    val pick = Path().apply {
        moveTo(center.x - size * 0.7f, center.y - size * 0.4f)
        lineTo(center.x, center.y - size * 0.7f)
        lineTo(center.x + size * 0.7f, center.y - size * 0.4f)
        lineTo(center.x + size * 0.5f, center.y - size * 0.25f)
        lineTo(center.x, center.y - size * 0.45f)
        lineTo(center.x - size * 0.5f, center.y - size * 0.25f)
        close()
    }
    drawPath(pick, color)
    drawLine(color, Offset(center.x, center.y - size * 0.45f), Offset(center.x, center.y + size * 0.85f), 3f)
    // Hash Cube at bottom
    drawRect(Color.White.copy(alpha = 0.6f), topLeft = Offset(center.x - size * 0.3f, center.y + size * 0.4f), size = Size(size * 0.6f, size * 0.35f), style = Stroke(width = 1.5f))
}

// 6: 🐉 Спам-Гидра (Three Cyber-Serpent Heads)
private fun DrawScope.drawSpamHydraSilhuette(color: Color, center: Offset, size: Float) {
    for (i in -1..1) {
        val hx = center.x + (i * size * 0.55f)
        val hy = center.y - size * 0.45f + (abs(i) * size * 0.25f)
        // Neck
        drawLine(color, Offset(center.x, center.y + size * 0.65f), Offset(hx, hy), 2f)
        // Serpent Head Triangle
        val head = Path().apply {
            moveTo(hx, hy - size * 0.25f)
            lineTo(hx + size * 0.22f, hy + size * 0.15f)
            lineTo(hx - size * 0.22f, hy + size * 0.15f)
            close()
        }
        drawPath(head, color)
        drawCircle(Color.White, radius = 2f, center = Offset(hx, hy))
    }
}

// 7: ❌ Фатальный Сбой (Huge Glowing Fatal X Error)
private fun DrawScope.drawFatalGlitchSilhuette(color: Color, center: Offset, size: Float) {
    val s = size * 0.75f
    // Glowing X
    drawLine(EidosRed, Offset(center.x - s, center.y - s), Offset(center.x + s, center.y + s), 6f)
    drawLine(EidosRed, Offset(center.x + s, center.y - s), Offset(center.x - s, center.y + s), 6f)
    drawLine(Color.White, Offset(center.x - s, center.y - s), Offset(center.x + s, center.y + s), 2f)
    drawLine(Color.White, Offset(center.x + s, center.y - s), Offset(center.x - s, center.y + s), 2f)
}

// 8: 🗡 Ассасин Даркнета (Hooded Visage & Crossed Daggers)
private fun DrawScope.drawDarknetAssassinSilhuette(color: Color, center: Offset, size: Float) {
    val hood = Path().apply {
        moveTo(center.x, center.y - size * 0.85f)
        lineTo(center.x + size * 0.65f, center.y + size * 0.25f)
        lineTo(center.x - size * 0.65f, center.y + size * 0.25f)
        close()
    }
    drawPath(hood, color.copy(alpha = 0.25f))
    drawPath(hood, color, style = Stroke(width = 2.2f))
    // Glowing slit eyes
    drawLine(Color.White, Offset(center.x - size * 0.35f, center.y - size * 0.05f), Offset(center.x - size * 0.1f, center.y - size * 0.05f), 2.5f)
    drawLine(Color.White, Offset(center.x + size * 0.1f, center.y - size * 0.05f), Offset(center.x + size * 0.35f, center.y - size * 0.05f), 2.5f)
}

// 9: 🧠 ИИ-Доминатор (Neural Cortex Synapse Sphere)
private fun DrawScope.drawAiDominatorSilhuette(color: Color, center: Offset, size: Float) {
    drawCircle(color.copy(alpha = 0.25f), radius = size * 0.65f, center = center)
    drawCircle(color, radius = size * 0.65f, center = center, style = Stroke(width = 2.2f))
    // Brain hemisphere divider
    drawLine(color, Offset(center.x, center.y - size * 0.65f), Offset(center.x, center.y + size * 0.65f), 2f)
    // Pulsing Core
    drawCircle(Color.White, radius = size * 0.25f, center = center)
    drawCircle(Color.Red, radius = size * 0.12f, center = center)
}

// 10: ⬛ Стиратель (The Void Monolith)
private fun DrawScope.drawEraserSilhuette(color: Color, center: Offset, size: Float) {
    val rect = Rect(center.x - size * 0.35f, center.y - size * 0.85f, center.x + size * 0.35f, center.y + size * 0.85f)
    drawRect(Color.Black, topLeft = rect.topLeft, size = rect.size)
    drawRect(color, topLeft = rect.topLeft, size = rect.size, style = Stroke(width = 2.5f))
    drawRect(Color.White.copy(alpha = 0.4f), topLeft = Offset(center.x - size * 0.2f, center.y - size * 0.7f), size = Size(size * 0.4f, size * 1.4f), style = Stroke(width = 1f))
}

// 11: 👻 Нейро-Призрак (Holographic Phantom Skull)
private fun DrawScope.drawNeuralPhantomSilhuette(color: Color, center: Offset, size: Float) {
    drawCircle(color.copy(alpha = 0.3f), radius = size * 0.55f, center = Offset(center.x, center.y - size * 0.15f))
    drawRect(color.copy(alpha = 0.3f), topLeft = Offset(center.x - size * 0.3f, center.y + size * 0.25f), size = Size(size * 0.6f, size * 0.35f))
    // Skull Eyes
    drawCircle(Color.Black, radius = size * 0.15f, center = Offset(center.x - size * 0.25f, center.y - size * 0.15f))
    drawCircle(Color.Black, radius = size * 0.15f, center = Offset(center.x + size * 0.25f, center.y - size * 0.15f))
    drawCircle(Color.White, radius = size * 0.06f, center = Offset(center.x - size * 0.25f, center.y - size * 0.15f))
    drawCircle(Color.White, radius = size * 0.06f, center = Offset(center.x + size * 0.25f, center.y - size * 0.15f))
}

// 12: 💀 Кибер-Лич (Horned Robotic Lich Skull)
private fun DrawScope.drawCyberLichSilhuette(color: Color, center: Offset, size: Float) {
    drawNeuralPhantomSilhuette(color, center, size)
    // Robotic Crown Horns
    drawLine(color, Offset(center.x - size * 0.4f, center.y - size * 0.5f), Offset(center.x - size * 0.8f, center.y - size * 0.95f), 3f)
    drawLine(color, Offset(center.x + size * 0.4f, center.y - size * 0.5f), Offset(center.x + size * 0.8f, center.y - size * 0.95f), 3f)
}

// 13: 🏗 Архитектор (Tesseract / Hypercube Labyrinth)
private fun DrawScope.drawArchitectSilhuette(color: Color, center: Offset, size: Float) {
    // Outer Box
    val outR = Rect(center.x - size * 0.65f, center.y - size * 0.65f, center.x + size * 0.65f, center.y + size * 0.65f)
    drawRect(color, topLeft = outR.topLeft, size = outR.size, style = Stroke(width = 2f))
    // Inner Box
    val inR = Rect(center.x - size * 0.3f, center.y - size * 0.3f, center.x + size * 0.3f, center.y + size * 0.3f)
    drawRect(Color.White, topLeft = inR.topLeft, size = inR.size, style = Stroke(width = 1.5f))
    // Connecting tesseract rays
    drawLine(color, outR.topLeft, inR.topLeft, 1.5f)
    drawLine(color, outR.topRight, inR.topRight, 1.5f)
    drawLine(color, outR.bottomLeft, inR.bottomLeft, 1.5f)
    drawLine(color, outR.bottomRight, inR.bottomRight, 1.5f)
}

// 14: 🍽 Пожиратель Кода (Maw Vortex)
private fun DrawScope.drawCodeDevourerSilhuette(color: Color, center: Offset, size: Float) {
    for (i in 1..4) {
        val r = (size * 0.7f / 4) * i
        drawCircle(color.copy(alpha = 0.25f * i), radius = r, center = center, style = Stroke(width = 2f))
    }
    // Jagged Teeth
    for (a in 0 until 6) {
        val angle = a * (PI / 3.0)
        val p1 = Offset(center.x + cos(angle).toFloat() * size * 0.7f, center.y + sin(angle).toFloat() * size * 0.7f)
        drawLine(Color.White, center, p1, 1.5f)
    }
}

// 15: 🛡 Страж Ядра (Fortress Mech Carapace)
private fun DrawScope.drawCoreSentinelSilhuette(color: Color, center: Offset, size: Float) {
    val path = Path().apply {
        moveTo(center.x - size * 0.6f, center.y - size * 0.65f)
        lineTo(center.x + size * 0.6f, center.y - size * 0.65f)
        lineTo(center.x + size * 0.8f, center.y + size * 0.25f)
        lineTo(center.x, center.y + size * 0.85f)
        lineTo(center.x - size * 0.8f, center.y + size * 0.25f)
        close()
    }
    drawPath(path, color.copy(alpha = 0.3f))
    drawPath(path, color, style = Stroke(width = 2.5f))
    // 3 Target Sensors
    drawCircle(Color.Red, radius = 4f, center = Offset(center.x - size * 0.25f, center.y - size * 0.1f))
    drawCircle(Color.Red, radius = 5f, center = Offset(center.x, center.y - size * 0.1f))
    drawCircle(Color.Red, radius = 4f, center = Offset(center.x + size * 0.25f, center.y - size * 0.1f))
}

// 16: ⚛️ Омни-Синтез (Quantum Collider Orbitals)
private fun DrawScope.drawOmniSynthesisSilhuette(color: Color, center: Offset, size: Float) {
    for (i in 0 until 3) {
        val angle = i * (PI / 3.0)
        val path = Path().apply {
            moveTo(center.x - cos(angle).toFloat() * size * 0.85f, center.y - sin(angle).toFloat() * size * 0.85f)
            cubicTo(
                center.x - sin(angle).toFloat() * size * 0.45f, center.y + cos(angle).toFloat() * size * 0.45f,
                center.x + sin(angle).toFloat() * size * 0.45f, center.y - cos(angle).toFloat() * size * 0.45f,
                center.x + cos(angle).toFloat() * size * 0.85f, center.y + sin(angle).toFloat() * size * 0.85f
            )
        }
        drawPath(path, color, style = Stroke(width = 2f))
    }
    drawCircle(Color.White, radius = size * 0.18f, center = center)
}

// 17: 🤖 Бог Машины (Deus Ex Machina Visage)
private fun DrawScope.drawMachineGodSilhuette(color: Color, center: Offset, size: Float) {
    // Massive Colossal Head
    val path = Path().apply {
        moveTo(center.x - size * 0.7f, center.y - size * 0.5f)
        lineTo(center.x, center.y - size * 0.95f)
        lineTo(center.x + size * 0.7f, center.y - size * 0.5f)
        lineTo(center.x + size * 0.55f, center.y + size * 0.7f)
        lineTo(center.x - size * 0.55f, center.y + size * 0.7f)
        close()
    }
    drawPath(path, Color(0xFFFFD700).copy(alpha = 0.25f))
    drawPath(path, Color(0xFFFFD700), style = Stroke(width = 2.5f))
    // Radiant Halo Rays
    for (i in 0 until 5) {
        val angle = -PI + (i * PI / 4.0)
        val p1 = Offset(center.x + cos(angle).toFloat() * size * 0.9f, center.y + sin(angle).toFloat() * size * 0.9f)
        val p2 = Offset(center.x + cos(angle).toFloat() * size * 1.25f, center.y + sin(angle).toFloat() * size * 1.25f)
        drawLine(Color(0xFFFFD700), p1, p2, 2f)
    }
    // All-seeing Golden Eye
    drawCircle(Color.White, radius = size * 0.14f, center = center)
}

// 18: 🌌 Пустотный Странник (Cosmic Rift Entity)
private fun DrawScope.drawVoidNomadSilhuette(color: Color, center: Offset, size: Float) {
    // Dimensional Tear
    val tear = Path().apply {
        moveTo(center.x, center.y - size * 0.95f)
        cubicTo(center.x + size * 0.7f, center.y - size * 0.2f, center.x - size * 0.7f, center.y + size * 0.2f, center.x, center.y + size * 0.95f)
        cubicTo(center.x - size * 0.7f, center.y + size * 0.2f, center.x + size * 0.7f, center.y - size * 0.2f, center.x, center.y - size * 0.95f)
        close()
    }
    drawPath(tear, Color(0xFF6200EA).copy(alpha = 0.4f))
    drawPath(tear, color, style = Stroke(width = 2.2f))
    drawCircle(Color.White, radius = size * 0.12f, center = center)
}

// 19: 🌀 Энтропия (Swirling Chaotic Singularity)
private fun DrawScope.drawEntropySingularitySilhuette(color: Color, center: Offset, size: Float) {
    // Spiral Event Horizon
    for (i in 0 until 12) {
        val a = i * (PI / 6.0)
        val r1 = size * 0.25f
        val r2 = size * 0.95f
        val p1 = Offset(center.x + cos(a).toFloat() * r1, center.y + sin(a).toFloat() * r1)
        val p2 = Offset(center.x + cos(a + 0.8f).toFloat() * r2, center.y + sin(a + 0.8f).toFloat() * r2)
        drawLine(color, p1, p2, 2f)
    }
    drawCircle(Color.Black, radius = size * 0.35f, center = center)
    drawCircle(EidosRed, radius = size * 0.35f, center = center, style = Stroke(width = 2.5f))
    drawCircle(Color.White, radius = size * 0.12f, center = center)
}
