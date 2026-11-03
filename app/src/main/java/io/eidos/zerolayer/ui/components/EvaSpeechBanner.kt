package io.eidos.zerolayer.ui.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R

/**
 * Tactical voice module banner of EVA-09 AI Assistant.
 * Displays biometric avatar, transmitting REC diode, animated equalizer wave, and synthesized message.
 */
@Composable
fun EvaSpeechBanner(
    text: String,
    isSpeaking: Boolean,
    modifier: Modifier = Modifier,
    onReplayClick: () -> Unit = {}
) {
    val infiniteTransition = rememberInfiniteTransition(label = "eva_transmitting_blink")
    val diodeAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(600, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "diode_alpha"
    )

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onReplayClick),
        shape = CutCornerShape(topStart = 0.dp, bottomEnd = 12.dp, topEnd = 12.dp, bottomStart = 12.dp),
        border = BorderStroke(1.5.dp, Color(0xFF00FFF6)),
        color = Color(0xEB101116)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Левый блок: Аватар ЕВЫ-09 с диодом сеанса связи
            Box(
                modifier = Modifier
                    .size(46.dp)
                    .align(Alignment.Top)
            ) {
                Image(
                    painter = painterResource(id = R.drawable.ic_eva_avatar_ai),
                    contentDescription = "EVA-09 Avatar",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(44.dp)
                )
                Image(
                    painter = painterResource(id = R.drawable.ic_eva_transmitting),
                    contentDescription = "Transmission Active",
                    modifier = Modifier
                        .size(12.dp)
                        .align(Alignment.TopEnd)
                        .alpha(if (isSpeaking) diodeAlpha else 0.4f)
                )
            }

            Spacer(modifier = Modifier.width(10.dp))

            // Центральный блок: Заголовок, эквалайзер и текст
            Column(
                modifier = Modifier
                    .weight(1f)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "// ЕВА-09 [ИИ-АССИСТЕНТ]",
                        color = Color(0xFF00FFF6),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 0.5.sp
                    )

                    // Индикатор эквалайзера речи
                    if (isSpeaking) {
                        Image(
                            painter = painterResource(id = R.drawable.ic_eva_wave_active),
                            contentDescription = "Speaking Wave",
                            contentScale = ContentScale.Fit,
                            modifier = Modifier
                                .height(18.dp)
                                .fillMaxWidth(0.45f)
                        )
                    } else {
                        Image(
                            painter = painterResource(id = R.drawable.ic_eva_wave_idle),
                            contentDescription = "Idle Wave",
                            contentScale = ContentScale.Fit,
                            modifier = Modifier
                                .height(8.dp)
                                .fillMaxWidth(0.45f)
                                .alpha(0.5f)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = text,
                    color = Color.White,
                    fontSize = 12.5.sp,
                    lineHeight = 17.sp,
                    fontFamily = FontFamily.SansSerif
                )
            }
        }
    }
}
