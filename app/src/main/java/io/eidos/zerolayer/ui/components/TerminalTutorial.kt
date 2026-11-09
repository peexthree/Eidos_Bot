package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.EidosAudioManager

data class TutorialStepData(
    val title: String,
    val text: String,
    val icon: String,
    val hint: String
)

val TUTORIAL_STEPS = listOf(
    TutorialStepData(
        title = "00 // ЗОЛОТАЯ НИТЬ",
        text = "Оператор, в центральной части Хаба ты всегда видишь свою АКТИВНУЮ ДИРЕКТИВУ. Это твоя цель прямо сейчас. Следуй ей - и не потеряешься в Нулевом Слое.",
        icon = "🧵",
        hint = "Директива автоматически обновляется, когда ты выполняешь условие."
    ),
    TutorialStepData(
        title = "01 // ПОДКЛЮЧЕНИЕ К ЕЙДОСУ",
        text = "Приветствую, Оператор. Вы успешно установили нейро-связь с Нулевым Слоем. EIDOS-CORE регистрирует ваш био-паспорт и присваивает начальный ранг. Здесь реальность сливается с кодом.",
        icon = "🌐",
        hint = "Ваш прогресс сохраняется в автономной квантовой матрице."
    ),
    TutorialStepData(
        title = "02 // КУЗНИЦА И СКВЕРНА",
        text = "Любая экипировка, найденная в Бездне, подвержена заражению Скверной. Скверна дает мощную атаку, но видоизменяет интерфейс и сжигает сигнал. Используйте Кузницу для заточки, перековки и очистки от вирусов.",
        icon = "⚙️",
        hint = "Регулярно затачивайте оружие в Кузнице за биокоины."
    ),
    TutorialStepData(
        title = "03 // РЕЙДЫ В БЕЗДНУ И ЭВАКУАЦИЯ",
        text = "Каждый шаг в Бездну погружает вас глубже в Нулевой Слой. Главное правило: если уровень Сигнала (HP) становится критическим - запускайте процедуру НЕСТАБИЛЬНОЙ ЭВАКУАЦИИ. Если вы погибете, часть неадаптированного кода будет утеряна!",
        icon = "⚡",
        hint = "Следите за полоской Сигнала и эвакуируйтесь вовремя."
    ),
    TutorialStepData(
        title = "04 // БОЕВЫЕ ПРОТОКОЛЫ И ВЗЛОМ",
        text = "Во время боя вам доступны активные навыки экзоскелета: Перегрузка Щита, Электромагнитный Импульс и Скрытый Протокол. При нахождении запертых узлов запускается квантовая мини-игра взлома байтовых последовательностей.",
        icon = "🛡️",
        hint = "Подбирайте правильные байты до истечения времени."
    ),
    TutorialStepData(
        title = "05 // СТОЙКА РЕЛИКВИЙ И КРАФТ",
        text = "В Бездне вы будете находить аудиокассеты и кварцевые артефакты забытой Земли. Размещайте их на Стойке Реликвий в Убежище, чтобы активировать постоянные пассивные баффы к опыту, защите и добыче крипты.",
        icon = "📼",
        hint = "Аудио-логи Архитекторов раскрывают истинную причину Глитча."
    )
)

@Composable
fun TerminalTutorialDialog(
    onDismiss: () -> Unit,
    onCompleteTutorial: () -> Unit
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    var currentStepIndex by remember { mutableIntStateOf(0) }
    val step = TUTORIAL_STEPS[currentStepIndex]

    val dialogShape = CutCornerShape(topStart = 12.dp, bottomEnd = 12.dp, topEnd = 3.dp, bottomStart = 3.dp)

    Dialog(onDismissRequest = onDismiss) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(dialogShape)
                .background(
                    androidx.compose.ui.graphics.Brush.verticalGradient(
                        listOf(
                            Color(0xF5121B2D),
                            Color(0xF80B111E),
                            Color(0xFE04060D)
                        )
                    )
                )
                .border(1.5.dp, EidosCyan.copy(alpha = 0.85f), dialogShape)
                .padding(18.dp)
        ) {
            // Studio Glass Top Reflection Sheen
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.5.dp)
                    .background(
                        androidx.compose.ui.graphics.Brush.horizontalGradient(
                            listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.4f),
                                EidosCyan,
                                Color.Transparent
                            )
                        )
                    )
            )

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // Header with live status diode
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(androidx.compose.foundation.shape.CircleShape)
                                .background(EidosCyan)
                        )
                        Text(
                            "ГОЛОС EIDOS // ИНСТРУКТАЖ",
                            color = EidosCyan,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                    }
                    Surface(
                        color = EidosCyan.copy(alpha = 0.15f),
                        shape = CutCornerShape(topStart = 2.dp, bottomEnd = 4.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.4f))
                    ) {
                        Text(
                            " ${currentStepIndex + 1} / ${TUTORIAL_STEPS.size} ",
                            color = EidosNeon,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                        )
                    }
                }

                LinearProgressIndicator(
                    progress = { (currentStepIndex + 1).toFloat() / TUTORIAL_STEPS.size },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(4.dp)
                        .clip(CutCornerShape(2.dp)),
                    color = EidosNeon,
                    trackColor = Color(0xFF162030)
                )

                // Step Icon & Title
                Surface(
                    color = Color(0x6610192A),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.45f)),
                    shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp, topEnd = 2.dp, bottomStart = 2.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(CutCornerShape(4.dp))
                                .background(Color(0x3300F0FF))
                                .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(4.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(step.icon, fontSize = 20.sp)
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                step.title,
                                color = EidosNeon,
                                fontSize = 12.5.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace,
                                letterSpacing = 0.5.sp
                            )
                            Text(
                                step.hint,
                                color = Color(0xFF94A3B8),
                                fontSize = 9.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                // Step Text
                Surface(
                    color = Color(0xEE090E17),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E293B)),
                    shape = CutCornerShape(topStart = 2.dp, bottomEnd = 6.dp, topEnd = 6.dp, bottomStart = 2.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = step.text,
                        color = Color(0xFFE2E8F0),
                        fontSize = 11.5.sp,
                        fontFamily = FontFamily.SansSerif,
                        lineHeight = 17.sp,
                        modifier = Modifier.padding(14.dp)
                    )
                }

                // Navigation Controls
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    if (currentStepIndex > 0) {
                        OutlinedButton(
                            onClick = {
                                audio.playSound(EidosAudioManager.SoundType.TUTORIAL_STEP)
                                currentStepIndex--
                            },
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = EidosCyan),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                            shape = CutCornerShape(topStart = 2.dp, bottomEnd = 6.dp),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("НАЗАД", fontSize = 10.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Button(
                        onClick = {
                            if (currentStepIndex < TUTORIAL_STEPS.size - 1) {
                                audio.playSound(EidosAudioManager.SoundType.TUTORIAL_STEP)
                                currentStepIndex++
                            } else {
                                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                                onCompleteTutorial()
                                onDismiss()
                            }
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (currentStepIndex < TUTORIAL_STEPS.size - 1) EidosCyan else EidosNeon,
                            contentColor = Color.Black
                        ),
                        shape = CutCornerShape(topStart = 2.dp, bottomEnd = 6.dp),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(
                            text = if (currentStepIndex < TUTORIAL_STEPS.size - 1) "ДАЛЕЕ ➔" else "ЗАВЕРШИТЬ (+500 BC)",
                            fontSize = 10.5.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
