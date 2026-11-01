package io.eidos.zerolayer.ui.components.zzz

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.theme.*
import kotlin.math.cos
import kotlin.math.sin

/**
 * ZzzCyberSonarRadar - Reference 4:
 * Centerpiece Cyber-Sonar Radar with rotating sweep beam, concentric range rings,
 * tactical alien/runic bezel, and interactive threat blips.
 */
@Composable
fun ZzzCyberSonarRadar(
    anomalyCount: Int = 1,
    hasEnemy: Boolean = false,
    enemyDistanceM: Int = 29,
    lootDistanceM: Int = 6,
    signalStability: Int = 94,
    depthM: Int = 1480,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "radar_sweep")
    val sweepAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(4000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "sweep_angle"
    )

    val blipPulse by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blip_pulse"
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // TOP RADAR TELEMETRY BAR
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(horizontalAlignment = Alignment.Start) {
                Text("ГЛУБИНА (М)", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text("▼ ${depthM} М", color = EidosNeon, fontSize = 14.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("СТАБИЛЬНОСТЬ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text("${signalStability}%", color = if (signalStability > 50) EidosNeon else EidosRed, fontSize = 14.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("РАДАР", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                Text("АКТИВЕН", color = EidosCyan, fontSize = 13.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
            }
        }

        Spacer(modifier = Modifier.height(6.dp))

        // CIRCULAR CYBER SONAR RADAR CANVAS
        Box(
            modifier = Modifier
                .size(260.dp)
                .clip(RoundedCornerShape(130.dp))
                .background(Color(0xFF030B07))
                .border(2.dp, Brush.sweepGradient(listOf(EidosNeon.copy(alpha = 0.8f), Color.DarkGray, EidosNeon.copy(alpha = 0.8f))), RoundedCornerShape(130.dp)),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val center = Offset(size.width / 2f, size.height / 2f)
                val maxRadius = size.width / 2f - 12f

                // Outer Runic / Cyber Bezel Markers
                drawCircle(
                    color = Color(0xFF0D2818),
                    radius = maxRadius,
                    center = center,
                    style = Stroke(width = 4f)
                )

                // Concentric Range Rings (10m, 20m, 30m)
                val ringRadii = listOf(0.3f, 0.6f, 0.88f)
                ringRadii.forEachIndexed { idx, frac ->
                    val r = maxRadius * frac
                    drawCircle(
                        color = Color(0xFF00FF66).copy(alpha = 0.25f),
                        radius = r,
                        center = center,
                        style = Stroke(
                            width = 1.5f,
                            pathEffect = PathEffect.dashPathEffect(floatArrayOf(8f, 6f), 0f)
                        )
                    )
                }

                // Crosshairs
                drawLine(
                    color = Color(0xFF00FF66).copy(alpha = 0.2f),
                    start = Offset(center.x, center.y - maxRadius),
                    end = Offset(center.x, center.y + maxRadius),
                    strokeWidth = 1f
                )
                drawLine(
                    color = Color(0xFF00FF66).copy(alpha = 0.2f),
                    start = Offset(center.x - maxRadius, center.y),
                    end = Offset(center.x + maxRadius, center.y),
                    strokeWidth = 1f
                )

                // Sweeping Radar Beam (Sweep Gradient Cone)
                rotate(sweepAngle, pivot = center) {
                    val sweepBrush = Brush.sweepGradient(
                        0.0f to Color(0xFF00FF66).copy(alpha = 0.0f),
                        0.75f to Color(0xFF00FF66).copy(alpha = 0.0f),
                        0.98f to Color(0xFF00FF66).copy(alpha = 0.35f),
                        1.0f to Color(0xFF00FF66).copy(alpha = 0.85f),
                        center = center
                    )
                    drawCircle(
                        brush = sweepBrush,
                        radius = maxRadius,
                        center = center
                    )
                    // Leading beam line
                    drawLine(
                        color = Color(0xFF00FF66),
                        start = center,
                        end = Offset(center.x + maxRadius, center.y),
                        strokeWidth = 2f
                    )
                }

                // Blip 1: Anomaly (top-right, ~18m)
                val anomalyAngle = Math.toRadians(45.0)
                val anomalyDist = maxRadius * 0.55f
                val anomalyPos = Offset(
                    (center.x + anomalyDist * cos(anomalyAngle)).toFloat(),
                    (center.y - anomalyDist * sin(anomalyAngle)).toFloat()
                )
                drawCircle(
                    color = Color(0xFFFFD700).copy(alpha = blipPulse * 0.4f),
                    radius = 12f * blipPulse,
                    center = anomalyPos
                )
                drawCircle(
                    color = Color(0xFFFFD700),
                    radius = 4.5f,
                    center = anomalyPos
                )

                // Blip 2: Enemy (mid-right, ~29m)
                if (hasEnemy) {
                    val enemyAngle = Math.toRadians(15.0)
                    val enemyDist = maxRadius * 0.82f
                    val enemyPos = Offset(
                        (center.x + enemyDist * cos(enemyAngle)).toFloat(),
                        (center.y - enemyDist * sin(enemyAngle)).toFloat()
                    )
                    drawCircle(
                        color = Color(0xFFFF2A55).copy(alpha = blipPulse * 0.5f),
                        radius = 14f * blipPulse,
                        center = enemyPos
                    )
                    drawCircle(
                        color = Color(0xFFFF2A55),
                        radius = 5f,
                        center = enemyPos
                    )
                }

                // Blip 3: Loot (bottom-right, ~6m)
                val lootAngle = Math.toRadians(310.0)
                val lootDist = maxRadius * 0.28f
                val lootPos = Offset(
                    (center.x + lootDist * cos(lootAngle)).toFloat(),
                    (center.y - lootDist * sin(lootAngle)).toFloat()
                )
                drawCircle(
                    color = Color(0xFF00F0FF),
                    radius = 4f,
                    center = lootPos
                )
            }

            // Central cross dot
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(RoundedCornerShape(3.dp))
                    .background(EidosNeon)
            )

            // Blip Legend Text Tags overlay
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(14.dp)
            ) {
                // Anomaly tag (top-right)
                Text(
                    "● Аномалия [18м]",
                    color = Color(0xFFFFD700),
                    fontSize = 8.5.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 28.dp, end = 12.dp)
                )

                // Enemy tag (mid-right)
                if (hasEnemy) {
                    Text(
                        "▲ Чужой [${enemyDistanceM}м]",
                        color = Color(0xFFFF2A55),
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier
                            .align(Alignment.CenterEnd)
                            .padding(end = 4.dp)
                    )
                }

                // Loot tag (bottom-right)
                Text(
                    "◆ Лут [${lootDistanceM}м]",
                    color = Color(0xFF00F0FF),
                    fontSize = 8.5.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(bottom = 36.dp, end = 24.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Status text bar
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
                .clip(CutCornerShape(4.dp))
                .background(Color(0xFF08150D))
                .border(1.dp, Color(0xFF00FF66).copy(alpha = 0.3f), CutCornerShape(4.dp))
                .padding(vertical = 4.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                "СТАТУС: ПОГРУЖЕНИЕ // ЦЕЛЬ: ИССЛЕДОВАТЬ СЕКТОР",
                color = Color(0xFF00FF66),
                fontSize = 9.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * ZzzCyberMannequinDeck - References 2 & 3:
 * Holographic wireframe humanoid cyber-body silhouette with interactive
 * equipment slot connectors (Head, Torso, Weapon, Cache Chips 1-4).
 */
@Composable
fun ZzzCyberMannequinDeck(
    equippedHead: String?,
    equippedTorso: String?,
    equippedWeapon: String?,
    equippedChips: List<String>,
    onSlotClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "wireframe_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1200), RepeatMode.Reverse),
        label = "pulse"
    )

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF060B11).copy(alpha = 0.9f))
            .border(1.dp, EidosCyan.copy(alpha = 0.4f), CutCornerShape(8.dp))
            .padding(10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        // LEFT SLOTS: Head & Weapon
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            ZzzMannequinSlotTile(
                slotLabel = "ШЛЕМ",
                itemTitle = equippedHead ?: "ПУСТО",
                color = EidosCyan,
                onClick = { onSlotClick("head") }
            )
            ZzzMannequinSlotTile(
                slotLabel = "ОРУЖИЕ",
                itemTitle = equippedWeapon ?: "ПУСТО",
                color = Color(0xFFFF9800),
                onClick = { onSlotClick("weapon") }
            )
            ZzzMannequinSlotTile(
                slotLabel = "БРОНЯ",
                itemTitle = equippedTorso ?: "ПУСТО",
                color = EidosPurple,
                onClick = { onSlotClick("torso") }
            )
        }

        // CENTER: HOLOGRAPHIC CYBER WIREFRAME MANNEQUIN
        Box(
            modifier = Modifier
                .weight(1.2f)
                .height(180.dp),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val cx = size.width / 2f
                val h = size.height

                // Cyber Grid background
                val gridStep = 20f
                var y = 0f
                while (y < h) {
                    drawLine(
                        color = Color(0xFF00F0FF).copy(alpha = 0.08f),
                        start = Offset(0f, y),
                        end = Offset(size.width, y),
                        strokeWidth = 1f
                    )
                    y += gridStep
                }

                // Neon Mannequin Silhouette wireframe
                // Head
                drawCircle(
                    color = Color(0xFF00F0FF).copy(alpha = pulseAlpha),
                    radius = 16f,
                    center = Offset(cx, 28f),
                    style = Stroke(width = 2.5f)
                )
                // Visor line
                drawLine(
                    color = Color(0xFFFF007F),
                    start = Offset(cx - 10f, 28f),
                    end = Offset(cx + 10f, 28f),
                    strokeWidth = 3f
                )
                // Torso / Spine
                drawLine(
                    color = Color(0xFF00F0FF).copy(alpha = pulseAlpha),
                    start = Offset(cx, 46f),
                    end = Offset(cx, 110f),
                    strokeWidth = 3f
                )
                // Chest armor outline
                val chestPath = Path().apply {
                    moveTo(cx - 24f, 54f)
                    lineTo(cx + 24f, 54f)
                    lineTo(cx + 16f, 88f)
                    lineTo(cx - 16f, 88f)
                    close()
                }
                drawPath(chestPath, Color(0xFF9C27B0).copy(alpha = 0.35f))
                drawPath(chestPath, Color(0xFF9C27B0).copy(alpha = pulseAlpha), style = Stroke(width = 2f))

                // Arms
                drawLine(Color(0xFF00F0FF).copy(alpha = pulseAlpha), Offset(cx - 24f, 54f), Offset(cx - 36f, 100f), 2f)
                drawLine(Color(0xFF00F0FF).copy(alpha = pulseAlpha), Offset(cx + 24f, 54f), Offset(cx + 36f, 100f), 2f)

                // Legs
                drawLine(Color(0xFF00F0FF).copy(alpha = pulseAlpha), Offset(cx - 14f, 110f), Offset(cx - 20f, 168f), 2.5f)
                drawLine(Color(0xFF00F0FF).copy(alpha = pulseAlpha), Offset(cx + 14f, 110f), Offset(cx + 20f, 168f), 2.5f)

                // Circuit Connector Lines to Left/Right
                // Line to Head
                drawLine(Color(0xFF00F0FF).copy(alpha = 0.5f), Offset(cx - 16f, 28f), Offset(10f, 28f), 1f)
                // Line to Weapon
                drawLine(Color(0xFFFF9800).copy(alpha = 0.5f), Offset(cx - 36f, 100f), Offset(10f, 85f), 1f)
                // Line to Torso
                drawLine(Color(0xFF9C27B0).copy(alpha = 0.5f), Offset(cx - 16f, 70f), Offset(10f, 145f), 1f)

                // Connector lines to right (Chips)
                drawLine(Color(0xFF00FF66).copy(alpha = 0.5f), Offset(cx + 16f, 65f), Offset(size.width - 10f, 30f), 1f)
                drawLine(Color(0xFF00FF66).copy(alpha = 0.5f), Offset(cx + 16f, 85f), Offset(size.width - 10f, 75f), 1f)
                drawLine(Color(0xFF00FF66).copy(alpha = 0.5f), Offset(cx + 14f, 120f), Offset(size.width - 10f, 120f), 1f)
                drawLine(Color(0xFF00FF66).copy(alpha = 0.5f), Offset(cx + 18f, 150f), Offset(size.width - 10f, 160f), 1f)
            }
        }

        // RIGHT SLOTS: Mod Chips 1..4
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            for (i in 0..3) {
                val chip = equippedChips.getOrNull(i)
                ZzzMannequinSlotTile(
                    slotLabel = "ЧИП ${i + 1}",
                    itemTitle = chip ?: "СЛОТ ${i + 1}",
                    color = if (chip != null) EidosNeon else Color.Gray,
                    onClick = { onSlotClick("chip_$i") }
                )
            }
        }
    }
}

@Composable
private fun ZzzMannequinSlotTile(
    slotLabel: String,
    itemTitle: String,
    color: Color,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(CutCornerShape(4.dp))
            .background(Color(0xFF0A131A))
            .border(1.dp, color.copy(alpha = 0.6f), CutCornerShape(4.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 6.dp, vertical = 4.dp)
    ) {
        Column {
            Text(
                slotLabel,
                color = color,
                fontSize = 8.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Text(
                itemTitle,
                color = Color.White,
                fontSize = 9.sp,
                fontFamily = FontFamily.Monospace,
                maxLines = 1
            )
        }
    }
}

/**
 * ZzzForgeHologramChamber - References 1 & 5:
 * Hologram blueprint weapon crafting chamber, mod slot buttons,
 * materials telemetry, and giant COMMENCE CRAFTING button.
 */
@Composable
fun ZzzForgeHologramChamber(
    weaponTitle: String = "APEX STARBURST [AS-VII]",
    weaponRarity: String = "LEGENDARY",
    dataSlicerLvl: Int = 5,
    quantumTunerLvl: Int = 3,
    isVaalCorrupted: Boolean = false,
    quantumCoils: Int = 18,
    maxQuantumCoils: Int = 20,
    voidCells: Int = 12,
    maxVoidCells: Int = 15,
    vaalEssence: Int = 3,
    maxVaalEssence: Int = 5,
    onDataSlicerClick: () -> Unit = {},
    onQuantumTunerClick: () -> Unit = {},
    onVaalCorruptionClick: () -> Unit = {},
    onCommenceCraft: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "forge_hologram")
    val reticleAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(10000, easing = LinearEasing), RepeatMode.Restart),
        label = "reticle_spin"
    )
    val glowPulse by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1000), RepeatMode.Reverse),
        label = "glow_pulse"
    )

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF090E14))
            .border(1.5.dp, Color(0xFFFF9800).copy(alpha = 0.7f), CutCornerShape(8.dp))
            .padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Top Chamber Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "BLUEPRINT // $weaponTitle",
                color = Color(0xFFFF9800),
                fontSize = 11.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Text(
                weaponRarity,
                color = Color(0xFFFFD700),
                fontSize = 10.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Center: Holographic Blueprint Projection Reticle
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(140.dp)
                .clip(CutCornerShape(6.dp))
                .background(Color(0xFF04070A))
                .border(1.dp, Color(0xFF00F0FF).copy(alpha = 0.3f), CutCornerShape(6.dp)),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val cx = size.width / 2f
                val cy = size.height / 2f

                // Rotating Dashed Reticle
                rotate(reticleAngle, pivot = Offset(cx, cy)) {
                    drawCircle(
                        color = Color(0xFF00F0FF).copy(alpha = 0.35f),
                        radius = 55.dp.toPx(),
                        center = Offset(cx, cy),
                        style = Stroke(
                            width = 2f,
                            pathEffect = PathEffect.dashPathEffect(floatArrayOf(15f, 10f), 0f)
                        )
                    )
                }

                // Inner steady ring
                drawCircle(
                    color = Color(0xFFFF9800).copy(alpha = 0.5f * glowPulse),
                    radius = 35.dp.toPx(),
                    center = Offset(cx, cy),
                    style = Stroke(width = 1.5f)
                )

                // Hologram blade silhouette
                val bladePath = Path().apply {
                    moveTo(cx, cy - 45f)
                    lineTo(cx + 12f, cy - 25f)
                    lineTo(cx + 8f, cy + 30f)
                    lineTo(cx, cy + 45f)
                    lineTo(cx - 8f, cy + 30f)
                    lineTo(cx - 12f, cy - 25f)
                    close()
                }
                drawPath(bladePath, Color(0xFFFF9800).copy(alpha = 0.4f * glowPulse))
                drawPath(bladePath, Color(0xFFFFD700), style = Stroke(width = 2f))
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    "MODEL: AS-VII // CLASS: PLASMA BLADE",
                    color = EidosCyan,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // MOD SLOTS (Reference 1 & 5)
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            // Mod Slot 1: DATA SLICER
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(4.dp))
                    .background(Color(0xFF051722))
                    .border(1.dp, EidosCyan, CutCornerShape(4.dp))
                    .clickable(onClick = onDataSlicerClick)
                    .padding(horizontal = 10.dp, vertical = 7.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("DATA SLICER", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        Text("MOD СЛОТ 1: АКТИВЕН", color = Color.LightGray, fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                    }
                    Text("[УРОВЕНЬ $dataSlicerLvl]", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                }
            }

            // Mod Slot 2: QUANTUM TUNER
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(4.dp))
                    .background(Color(0xFF1F1203))
                    .border(1.dp, Color(0xFFFF9800), CutCornerShape(4.dp))
                    .clickable(onClick = onQuantumTunerClick)
                    .padding(horizontal = 10.dp, vertical = 7.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("QUANTUM TUNER", color = Color(0xFFFF9800), fontSize = 11.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        Text("MOD СЛОТ 2: АКТИВЕН", color = Color.LightGray, fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                    }
                    Text("[УРОВЕНЬ $quantumTunerLvl]", color = Color(0xFFFF9800), fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                }
            }

            // Mod Slot 3: VAAL CORRUPTION (Hazard/Glitch risk)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(4.dp))
                    .background(Color(0xFF26050A))
                    .border(1.dp, EidosRed, CutCornerShape(4.dp))
                    .clickable(onClick = onVaalCorruptionClick)
                    .padding(horizontal = 10.dp, vertical = 7.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("⚠️ VAAL CORRUPTION", color = EidosRed, fontSize = 11.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        Text("СТАТУС: КРИТИЧЕСКИЙ РИСК", color = Color(0xFFFF8A80), fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                    }
                    Text(if (isVaalCorrupted) "[АКТИВНО]" else "[НЕСТАБИЛЬНО]", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // MATERIALS TELEMETRY ROW
        Text(
            "ТРЕБУЕМЫЕ МАТЕРИАЛЫ КРАФТА:",
            color = Color.LightGray,
            fontSize = 9.sp,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(4.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            ZzzMaterialChip(title = "Quantum Coils", value = "$quantumCoils/$maxQuantumCoils", color = EidosCyan, modifier = Modifier.weight(1f))
            ZzzMaterialChip(title = "Void Cells", value = "$voidCells/$maxVoidCells", color = EidosPurple, modifier = Modifier.weight(1f))
            ZzzMaterialChip(title = "Vaal Essence", value = "$vaalEssence/$maxVaalEssence", color = EidosRed, modifier = Modifier.weight(1f))
        }

        Spacer(modifier = Modifier.height(12.dp))

        // COMMENCE CRAFTING BUTTON (Giant tactile button from Ref 1 & 5)
        androidx.compose.material3.Button(
            onClick = onCommenceCraft,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = Color(0xFF2A1504)),
            border = androidx.compose.foundation.BorderStroke(2.dp, Color(0xFFFF9800)),
            shape = CutCornerShape(8.dp)
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    "🔨 СИНТЕЗИРОВАТЬ [COMMENCE CRAFTING]",
                    color = Color(0xFFFF9800),
                    fontWeight = FontWeight.Black,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    "ВРЕМЯ СИНТЕЗА: МГНОВЕННО // ЗАТРАТЫ: 250 BC",
                    color = Color.LightGray,
                    fontSize = 8.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}

@Composable
private fun ZzzMaterialChip(
    title: String,
    value: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(CutCornerShape(4.dp))
            .background(Color(0xFF060B11))
            .border(1.dp, color.copy(alpha = 0.5f), CutCornerShape(4.dp))
            .padding(4.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace, maxLines = 1)
            Text(value, color = color, fontSize = 9.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
        }
    }
}
