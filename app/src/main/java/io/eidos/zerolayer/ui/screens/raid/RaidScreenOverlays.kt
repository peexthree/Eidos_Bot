package io.eidos.zerolayer.ui.screens.raid

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.GameLog
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.TerminalLog
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGold
import io.eidos.zerolayer.ui.theme.ZzzElectricCyan

/**
 * Механически извлечено из RaidScreen.kt (декомпозиция без изменения поведения).
 * Модал системного журнала событий.
 */
@Composable
internal fun EventLogsDialog(
    logs: List<GameLog>,
    onDismiss: () -> Unit
) {
    androidx.compose.ui.window.Dialog(
        onDismissRequest = { onDismiss() },
        properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.85f))
                .clickable { onDismiss() }
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.95f)
                    .fillMaxHeight(0.72f)
                    .clickable(enabled = false) {}
            ) {
                CyberCornerBracketBox(bracketSize = 16.dp, bracketColor = EidosCyan) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(Color(0xFF090D12).copy(alpha = 0.95f))
                            .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(8.dp))
                            .padding(14.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(iconRes = R.drawable.ic_action_scan, size = 16.dp)
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    "ЛОГИ СОБЫТИЙ // СИСТЕМНЫЙ ЖУРНАЛ",
                                    color = EidosCyan,
                                    fontSize = 11.5.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            IconButton(onClick = { onDismiss() }, modifier = Modifier.size(24.dp)) {
                                Text("✕", color = Color.Gray, fontSize = 14.sp)
                            }
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                        Box(modifier = Modifier.weight(1f)) {
                            TerminalLog(logs)
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                        io.eidos.zerolayer.ui.components.EidosButton(
                            text = "ЗАКРЫТЬ",
                            onClick = { onDismiss() },
                            modifier = Modifier.fillMaxWidth().height(42.dp)
                        )
                    }
                }
            }
        }
    }
}

/**
 * Механически извлечено из RaidScreen.kt (декомпозиция без изменения поведения).
 * Диалог расшифрованного фрагмента памяти (глава кодекса).
 */
@Composable
internal fun StoryMilestoneChapterDialog(
    chapter: io.eidos.zerolayer.data.StoryChapter,
    haptics: io.eidos.zerolayer.ui.utils.HapticFeedbackManager,
    onDismiss: () -> Unit
) {
    androidx.compose.ui.window.Dialog(
        onDismissRequest = { onDismiss() },
        properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.85f))
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            CyberCornerBracketBox(
                bracketSize = 20.dp,
                bracketColor = ZzzElectricCyan,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(8.dp))
                        .background(Color(0xFF091018))
                        .border(1.5.dp, ZzzElectricCyan, CutCornerShape(8.dp))
                        .padding(18.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_menu_codex, size = 18.dp, tint = ZzzElectricCyan)
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "РАСШИФРОВАН ФРАГМЕНТ ПАМЯТИ // КОДЕКС",
                            color = ZzzElectricCyan,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = chapter.title,
                        color = Color.White,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Black,
                        textAlign = TextAlign.Center,
                        fontFamily = FontFamily.SansSerif
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = chapter.subtitle,
                        color = EidosGold,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center,
                        fontFamily = FontFamily.Monospace
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = chapter.epigraph,
                        color = Color.LightGray,
                        fontSize = 11.5.sp,
                        fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                        textAlign = TextAlign.Center,
                        lineHeight = 16.sp
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    Button(
                        onClick = {
                            onDismiss()
                            haptics.click()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = ZzzElectricCyan.copy(alpha = 0.25f)),
                        border = androidx.compose.foundation.BorderStroke(1.2.dp, ZzzElectricCyan),
                        shape = CutCornerShape(6.dp),
                        modifier = Modifier.fillMaxWidth().height(44.dp)
                    ) {
                        Text(
                            "СИНХРОНИЗИРОВАТЬ ДАННЫЕ В КОДЕКС",
                            color = ZzzElectricCyan,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
