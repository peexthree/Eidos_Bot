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
import io.eidos.zerolayer.R
import io.eidos.zerolayer.domain.combat.ActiveSynergy
import io.eidos.zerolayer.domain.combat.ChipMatrixSynergyEngine
import io.eidos.zerolayer.domain.raid.DescentScenario
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
    onOpenLogs: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(CutCornerShape(6.dp))
            .background(Color(0xFF07121A).copy(alpha = 0.9f))
            .border(1.dp, EidosCyan.copy(alpha = 0.4f), CutCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            modifier = Modifier
                .weight(1f)
                .clickable { onOpenCodex() }
                .horizontalScroll(rememberScrollState())
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ZzzIcon(iconRes = R.drawable.ic_res_energy, size = 13.dp)
                Spacer(Modifier.width(4.dp))
                Text(
                    "МАТРИЦА:",
                    color = EidosCyan,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }

            if (activeSynergies.isEmpty()) {
                Text(
                    "Нет синергий (2+ чипа цвета)",
                    color = Color.Gray,
                    fontSize = 8.5.sp,
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
                            .padding(horizontal = 5.dp, vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(3.dp)
                    ) {
                        ZzzIcon(iconRes = syn.iconRes, size = 12.dp)
                        Text(
                            "${syn.title} [${syn.tierLabel}]",
                            color = syn.color,
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.width(6.dp))

        // Action Buttons: ШПАРГАЛКА & ЛОГИ СОБЫТИЙ
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            // ШПАРГАЛКА
            Row(
                modifier = Modifier
                    .clip(CutCornerShape(4.dp))
                    .background(EidosGold.copy(alpha = 0.15f))
                    .border(0.8.dp, EidosGold.copy(alpha = 0.6f), CutCornerShape(4.dp))
                    .clickable { onOpenCodex() }
                    .padding(horizontal = 5.dp, vertical = 3.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                ZzzIcon(iconRes = R.drawable.ic_menu_codex, size = 11.dp)
                Spacer(Modifier.width(3.dp))
                Text(
                    "ШПАРГАЛКА",
                    color = EidosGold,
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }

            // ЛОГИ СОБЫТИЙ
            if (onOpenLogs != null) {
                Row(
                    modifier = Modifier
                        .clip(CutCornerShape(4.dp))
                        .background(EidosCyan.copy(alpha = 0.15f))
                        .border(0.8.dp, EidosCyan.copy(alpha = 0.6f), CutCornerShape(4.dp))
                        .clickable { onOpenLogs() }
                        .padding(horizontal = 5.dp, vertical = 3.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    ZzzIcon(iconRes = R.drawable.ic_action_scan, size = 11.dp)
                    Spacer(Modifier.width(3.dp))
                    Text(
                        "ЛОГИ СОБЫТИЙ",
                        color = EidosCyan,
                        fontSize = 8.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
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
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(iconRes = R.drawable.ic_res_energy, size = 16.dp)
                                Spacer(Modifier.width(6.dp))
                                Text(
                                    "РЕЗОНАНС МАТРИЦЫ ЧИПОВ",
                                    color = EidosCyan,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Black,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
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
                                    ZzzIcon(
                                        iconRes = info.iconRes,
                                        size = 24.dp,
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
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                ZzzIcon(iconRes = R.drawable.ic_ui_unlocked, size = 11.dp)
                                                Spacer(Modifier.width(4.dp))
                                                Text(
                                                    "АКТИВНО В БОЮ",
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
    modifier: Modifier = Modifier,
    scenario: DescentScenario? = null
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Narrative Scenario Lore Card (if scenario is present or sectors have narrative text)
        val scenarioTitle = scenario?.title ?: "РАЗВИЛКА СЕКТОРА // ВЫБОР МАРШРУТА"
        val scenarioLore = scenario?.loreDescription ?: "Сенсоры кибер-деки фиксируют пространственную нестабильность. Перед вами несколько векторов для продолжения спуска в глубины Нулевого Слоя..."

        CyberCornerBracketBox(
            modifier = Modifier.fillMaxWidth(),
            bracketSize = 14.dp,
            bracketAlpha = 0.9f
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(6.dp))
                    .background(Color(0xFF070E17).copy(alpha = 0.85f))
                    .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(6.dp))
                    .padding(10.dp)
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ZzzIcon(iconRes = R.drawable.ic_action_scan, size = 13.dp)
                            Spacer(Modifier.width(6.dp))
                            Text(
                                scenarioTitle,
                                color = EidosCyan,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                letterSpacing = 0.5.sp
                            )
                        }
                        Text(
                            "ВЕКТОРЫ СИТУАЦИИ",
                            color = Color(0xFF78909C),
                            fontSize = 8.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Spacer(Modifier.height(4.dp))
                    Text(
                        scenarioLore,
                        color = Color.LightGray.copy(alpha = 0.85f),
                        fontSize = 9.5.sp,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 13.5.sp
                    )
                }
            }
        }

        // 3 Narrative Action Option Cards
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            sectors.forEachIndexed { index, sector ->
                val hasEnergy = currentEnergy >= sector.costEnergy
                val riskColor = Color(sector.riskLevel.colorHex)
                val borderCol = if (sector.isEncrypted) Color(0xFF555555) else riskColor
                val actionTitle = if (sector.narrativeAction.isNotBlank()) sector.narrativeAction else sector.title
                val actionHint = if (sector.narrativeHint.isNotBlank()) sector.narrativeHint else sector.subTitle

                CyberCornerBracketBox(
                    modifier = Modifier.fillMaxWidth(),
                    bracketSize = 12.dp,
                    bracketAlpha = 0.8f
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(CutCornerShape(6.dp))
                            .background(
                                if (sector.isEncrypted) Color(0xFF080D11).copy(alpha = 0.85f)
                                else if (hasEnergy) Color(0xFF0A1520).copy(alpha = 0.88f)
                                else Color(0xFF220A10).copy(alpha = 0.88f)
                            )
                            .border(1.2.dp, borderCol.copy(alpha = 0.7f), CutCornerShape(6.dp))
                            .clickable { onSelectSector(sector) }
                            .padding(horizontal = 10.dp, vertical = 8.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            // Left: Index + Icon + Narrative Action Text
                            Row(
                                modifier = Modifier.weight(1f),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(26.dp)
                                        .clip(CutCornerShape(4.dp))
                                        .background(riskColor.copy(alpha = 0.15f))
                                        .border(1.dp, riskColor.copy(alpha = 0.6f), CutCornerShape(4.dp)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        "${index + 1}",
                                        color = riskColor,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                Spacer(Modifier.width(8.dp))
                                ZzzIcon(iconRes = sector.iconRes, size = 18.dp)
                                Spacer(Modifier.width(8.dp))
                                Column {
                                    Text(
                                        text = actionTitle,
                                        color = if (sector.isEncrypted) Color.LightGray else Color.White,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                    Text(
                                        text = actionHint,
                                        color = if (sector.isEncrypted) Color(0xFFFFCC00) else riskColor,
                                        fontSize = 8.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                            }

                            Spacer(Modifier.width(8.dp))

                            // Right: Mutator info + Energy Cost
                            Column(horizontalAlignment = Alignment.End) {
                                Box(
                                    modifier = Modifier
                                        .clip(CutCornerShape(4.dp))
                                        .background(if (hasEnergy) Color(0xFF00241A) else Color(0xFF440E14))
                                        .border(0.8.dp, if (hasEnergy) EidosNeon else ZzzDangerRed, CutCornerShape(4.dp))
                                        .padding(horizontal = 6.dp, vertical = 2.dp)
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        if (!hasEnergy) {
                                            ZzzIcon(iconRes = R.drawable.ic_action_blood_overdrive, size = 9.dp)
                                            Spacer(Modifier.width(2.dp))
                                        }
                                        Text(
                                            text = if (hasEnergy) "-${sector.costEnergy} EP" else "-8% HP",
                                            color = if (hasEnergy) EidosNeon else ZzzDangerRed,
                                            fontSize = 8.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                                Spacer(Modifier.height(2.dp))
                                Text(
                                    text = sector.mutator.title,
                                    color = Color.Gray,
                                    fontSize = 7.5.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
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
