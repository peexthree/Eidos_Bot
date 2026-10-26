package io.eidos.zerolayer.ui.components

import androidx.compose.animation.animateColor
import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
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
import io.eidos.zerolayer.domain.anomaly.AnomalyEngine
import io.eidos.zerolayer.domain.anomaly.ZalgoHelper
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager

@Composable
fun HardGlitchModal(
    question: AnomalyEngine.HardGlitchQuestion,
    onAnswerChosen: (Int) -> Unit,
    onTimeout: () -> Unit = {}
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    LaunchedEffect(Unit) {
        haptics.glitchPulse()
        audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
    }

    val infiniteTransition = rememberInfiniteTransition(label = "HardGlitchPulse")
    val glowColor by infiniteTransition.animateColor(
        initialValue = Color(0xFFFF0055),
        targetValue = Color(0xFF9900FF),
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "GlitchColor"
    )

    Dialog(onDismissRequest = { /* Modal must be answered */ }) {
        Surface(
            color = Color(0xFF0D0208),
            border = BorderStroke(2.dp, glowColor),
            shape = CutCornerShape(10.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Surface(
                    color = glowColor.copy(alpha = 0.2f),
                    border = BorderStroke(1.dp, glowColor),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.padding(bottom = 12.dp)
                ) {
                    Text(
                        text = ZalgoHelper.toZalgo("⚠️ КРИТИЧЕСКИЙ СБОЙ // HARD GLITCH", 1),
                        color = glowColor,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp)
                    )
                }

                Text(
                    text = "ЦЕЛОСТНОСТЬ ЯДРА НАРУШЕНА. НАКОПЛЕНЫ КРИТИЧЕСКИЕ АНОМАЛИИ СЛОЯ.",
                    color = Color(0xFFFF88AA),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )

                Spacer(Modifier.height(8.dp))

                Text(
                    text = question.question,
                    color = Color.LightGray,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 15.sp,
                    textAlign = TextAlign.Center
                )

                Spacer(Modifier.height(16.dp))

                question.options.forEachIndexed { index, optionText ->
                    Button(
                        onClick = {
                            haptics.click()
                            onAnswerChosen(index)
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFF200518)
                        ),
                        border = BorderStroke(1.dp, Color(0xFFFF0055).copy(alpha = 0.7f)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                    ) {
                        Text(
                            text = "[0x0$index] $optionText",
                            color = Color(0xFFFFCCE0),
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Start,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
        }
    }
}
