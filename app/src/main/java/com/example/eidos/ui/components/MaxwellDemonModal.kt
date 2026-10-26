package com.example.eidos.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.example.eidos.domain.anomaly.MaxwellContractsEngine
import com.example.eidos.domain.anomaly.MaxwellContractInfo
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.utils.EidosAudioManager
import com.example.eidos.ui.utils.HapticFeedbackManager

@Composable
fun MaxwellDemonModal(
    currentHp: Int,
    bufferCoins: Long,
    playerCoins: Long = 0L,
    playerXp: Long = 0L,
    onAcceptContract: (String) -> Unit,
    onIgnore: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    LaunchedEffect(Unit) {
        haptics.glitchPulse()
        audio.playSound(EidosAudioManager.SoundType.DANGER)
    }

    val infiniteTransition = rememberInfiniteTransition(label = "DemonGlow")
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "GlowAlpha"
    )

    Dialog(onDismissRequest = onIgnore) {
        Surface(
            color = Color(0xFF0A0204),
            border = BorderStroke(1.5.dp, Color(0xFFFF003C).copy(alpha = glowAlpha)),
            shape = CutCornerShape(10.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header badge
                Surface(
                    color = Color(0xFFFF003C).copy(alpha = 0.15f),
                    border = BorderStroke(1.dp, Color(0xFFFF003C)),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.padding(bottom = 8.dp)
                ) {
                    Text(
                        text = "⚠️ АНОМАЛИЯ // КОНТРАКТЫ ДЕМОНА МАКСВЕЛЛА",
                        color = Color(0xFFFF003C),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                    )
                }

                Text(
                    text = "«Я сортирую энтропию Нулевого Слоя. Выбери пакт: пожертвуй ресурсом или стабильностью ради аномального преимущества.»",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    textAlign = TextAlign.Center,
                    lineHeight = 14.sp,
                    fontFamily = FontFamily.Monospace
                )

                Spacer(Modifier.height(12.dp))

                // Render 5 Contracts
                MaxwellContractsEngine.ALL_CONTRACTS.forEach { contract ->
                    val isAvailable = when (contract.id) {
                        "socket_mutation" -> (playerCoins + bufferCoins) >= 1500L
                        "memory_sacrifice" -> playerXp >= 250L
                        "blood_overclock" -> currentHp > 20
                        else -> true
                    }

                    Surface(
                        color = if (isAvailable) Color(0xFF140508) else Color(0xFF0D0D0D),
                        border = BorderStroke(
                            1.dp,
                            if (isAvailable) Color(0xFFFF003C).copy(alpha = 0.6f) else Color.DarkGray
                        ),
                        shape = CutCornerShape(6.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(10.dp)
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(contract.icon, fontSize = 16.sp, modifier = Modifier.padding(end = 8.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = contract.title,
                                        color = if (isAvailable) Color(0xFFFF6B6B) else Color.Gray,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        text = "УСЛОВИЕ: ${contract.conditionText}",
                                        color = if (isAvailable) Color(0xFFFFB3B3) else Color.DarkGray,
                                        fontSize = 9.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        text = "НАГРАДА: ${contract.rewardText}",
                                        color = if (isAvailable) EidosNeon else Color.DarkGray,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(6.dp))

                            Button(
                                onClick = {
                                    haptics.criticalHit()
                                    onAcceptContract(contract.id)
                                },
                                enabled = isAvailable,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(0xFF4A000B),
                                    disabledContainerColor = Color(0xFF1F1F1F)
                                ),
                                border = BorderStroke(1.dp, if (isAvailable) Color(0xFFFF003C) else Color.DarkGray),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = if (isAvailable) "ПОДПИСАТЬ ПАКТ" else "НЕДОСТУПНО (НЕТ РЕСУРСА)",
                                    color = if (isAvailable) Color.White else Color.Gray,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }

                Spacer(Modifier.height(10.dp))

                // Ignore Button
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        onIgnore()
                    },
                    border = BorderStroke(1.dp, Color.Gray.copy(alpha = 0.5f)),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("🚶 ОТКЛОНИТЬ СДЕЛКУ И ПРОЙТИ МИМО", color = Color.LightGray, fontSize = 10.sp)
                }
            }
        }
    }
}
