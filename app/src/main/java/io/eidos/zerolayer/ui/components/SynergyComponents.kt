package io.eidos.zerolayer.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import io.eidos.zerolayer.domain.combat.ActiveSynergy
import io.eidos.zerolayer.domain.combat.ChipMatrixSynergyEngine
import io.eidos.zerolayer.domain.raid.QuantumSector
import io.eidos.zerolayer.domain.raid.SectorRiskLevel
import io.eidos.zerolayer.ui.theme.*

/**
 * Compact horizontal badge bar displaying currently active chip synergies.
 * Tapping opens the full TFT/Auto-Chess style Codex modal.
 */
@Composable
fun ActiveSynergiesBar(
    activeSynergies: List<ActiveSynergy>,
    onOpenCodex: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(6.dp))
            .background(Color(0xFF07121A).copy(alpha = 0.9f))
            .border(1.dp, EidosCyan.copy(alpha = 0.4f), CutCornerShape(6.dp))
            .clickable { onOpenCodex() }
            .padding(horizontal = 8.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            modifier = Modifier.weight(1f).horizontalScroll(rememberScrollState())
        ) {
            Text(
                "⚡ МАТРИЦА:",
                color = EidosCyan,
                fontSize = 9.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )

            if (activeSynergies.isEmpty()) {
                Text(
                    "Нет синергий (установите 2+ чипа одного цвета)",
                    color = Color.Gray,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    maxLines = 1
                )
            } else {
                activeSynergies.forEach { syn ->
                    Row(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(syn.color.copy(alpha = 0.2f))
                            .border(1.dp, syn.color, CutCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Text(syn.icon, fontSize = 9.sp)
                        Text(
                            "${syn.title} [${syn.tierLabel}]",
                            color = syn.color,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.width(6.dp))
        Text(
            "📖 ШПАРГАЛКА",
            color = EidosGold,
            fontSize = 8.5.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
    }
}

/**
 * TFT / Auto-Chess style modal cheat-sheet showing all potential chip synergies.
 */
@Composable
fun SynergyCodexModal(
    activeSynergies: List<ActiveSynergy>,
    onDismiss: () -> Unit
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.88f))
                .clickable { onDismiss() }
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.85f)
                    .clickable(enabled = false) {}
                    .clip(CutCornerShape(10.dp))
                    .background(Color(0xFF060B11))
                    .border(1.5.dp, EidosCyan, CutCornerShape(10.dp))
                    .padding(16.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    // Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                "⚡ РЕЗОНАНС МАТРИЦЫ ЧИПОВ",
                                color = EidosCyan,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                "Каталог синергий (2/4, 4/4, Duo & Cursed)",
                                color = Color.Gray,
                                fontSize = 9.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        IconButton(onClick = onDismiss) {
                            Text("✕", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    HorizontalDivider(color = EidosCyan.copy(alpha = 0.3f), thickness = 1.dp)
                    Spacer(modifier = Modifier.height(10.dp))

                    // Synergy List
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        ChipMatrixSynergyEngine.ALL_SYNERGIES_INFO.forEach { info ->
                            val isActive = activeSynergies.any { it.id == info.id }
                            val borderCol = if (isActive) info.color else Color.DarkGray
                            val bgCol = if (isActive) info.color.copy(alpha = 0.16f) else Color(0xFF0C131A)

                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(CutCornerShape(6.dp))
                                    .background(bgCol)
                                    .border(if (isActive) 1.5.dp else 0.8.dp, borderCol, CutCornerShape(6.dp))
                                    .padding(10.dp)
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.Top,
                                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                                ) {
                                    Text(
                                        info.icon,
                                        fontSize = 24.sp,
                                        modifier = Modifier.padding(top = 2.dp)
                                    )

                                    Column(modifier = Modifier.weight(1f)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                info.title,
                                                color = if (isActive) info.color else Color.LightGray,
                                                fontSize = 11.5.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                            Text(
                                                info.tierLabel,
                                                color = if (isActive) info.color else Color.Gray,
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }

                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            info.description,
                                            color = if (isActive) Color(0xFFE0E0E0) else Color(0xFF888888),
                                            fontSize = 9.sp,
                                            fontFamily = FontFamily.Monospace,
                                            lineHeight = 12.sp
                                        )

                                        if (isActive) {
                                            Spacer(modifier = Modifier.height(4.dp))
                                            Text(
                                                "✔ АКТИВНО В БОЮ",
                                                color = EidosNeon,
                                                fontSize = 8.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))
                    Button(
                        onClick = onDismiss,
                        modifier = Modifier.fillMaxWidth().height(44.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF003049)),
                        border = BorderStroke(1.dp, EidosCyan),
                        shape = CutCornerShape(6.dp)
                    ) {
                        Text("ЗАКРЫТЬ КАТАЛОГ", color = EidosCyan, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
    }
}

/**
 * 3 Asymmetric Quantum Sector Cards for exploration before taking a step.
 */
@Composable
fun QuantumSectorChoicesFork(
    sectors: List<QuantumSector>,
    currentEnergy: Int,
    onSelectSector: (QuantumSector) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "⚡ ВРАТА БЕЗДНЫ // ВЫБЕРИТЕ ВЕКТОР",
                color = EidosCyan,
                fontSize = 10.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Text(
                "РАСХОД ЭНЕРГИИ",
                color = Color.Gray,
                fontSize = 8.5.sp,
                fontFamily = FontFamily.Monospace
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            sectors.forEach { sector ->
                val hasEnergy = currentEnergy >= sector.costEnergy
                val riskColor = Color(sector.riskLevel.colorHex)
                val borderCol = if (sector.isEncrypted) Color(0xFF555555) else riskColor

                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(115.dp)
                        .clip(CutCornerShape(6.dp))
                        .background(
                            if (sector.isEncrypted) Color(0xFF080D11)
                            else if (hasEnergy) Color(0xFF09141D) else Color(0xFF220A10)
                        )
                        .border(1.2.dp, borderCol, CutCornerShape(6.dp))
                        .clickable { onSelectSector(sector) }
                        .padding(6.dp),
                    contentAlignment = Alignment.TopCenter
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.SpaceBetween
                    ) {
                        // Icon + Title
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(sector.icon, fontSize = 20.sp)
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = sector.title,
                                color = if (sector.isEncrypted) Color.LightGray else riskColor,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis
                            )
                        }

                        // Subtitle / Mutator
                        Text(
                            text = sector.subTitle,
                            color = if (sector.isEncrypted) Color(0xFFFFCC00) else Color.White,
                            fontSize = 7.5.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Center,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis
                        )

                        // Energy Cost tag
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(if (hasEnergy) Color(0xFF00241A) else Color(0xFF440E14))
                                .border(0.8.dp, if (hasEnergy) EidosNeon else Color(0xFFFF5252), CutCornerShape(4.dp))
                                .padding(horizontal = 4.dp, vertical = 1.dp)
                        ) {
                            Text(
                                text = if (hasEnergy) "-${sector.costEnergy} EP" else "🩸 -8% HP",
                                color = if (hasEnergy) EidosNeon else Color(0xFFFF5252),
                                fontSize = 7.5.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * Pulsing Low-HP Red Vignette overlay around the screen edges.
 */
@Composable
fun LowHpPulseVignette(
    isLowHp: Boolean,
    modifier: Modifier = Modifier
) {
    if (!isLowHp) return

    val infiniteTransition = rememberInfiniteTransition(label = "low_hp_pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.25f,
        targetValue = 0.65f,
        animationSpec = infiniteRepeatable(
            animation = tween(700, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "vignetteAlpha"
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .border(8.dp, Color(0xFFFF0033).copy(alpha = alpha))
    )
}
