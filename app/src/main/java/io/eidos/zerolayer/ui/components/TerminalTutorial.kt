package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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

    Dialog(onDismissRequest = onDismiss) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.Black, CutCornerShape(10.dp))
                .border(2.dp, EidosCyan, CutCornerShape(10.dp))
                .padding(18.dp)
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "ГОЛОС EIDOS // ИНСТРУКТАЖ",
                        color = EidosCyan,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        "${currentStepIndex + 1} / ${TUTORIAL_STEPS.size}",
                        color = EidosNeon,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                LinearProgressIndicator(
                    progress = { (currentStepIndex + 1).toFloat() / TUTORIAL_STEPS.size },
                    modifier = Modifier.fillMaxWidth().height(4.dp),
                    color = EidosNeon,
                    trackColor = Color.DarkGray
                )

                // Step Icon & Title
                Card(
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.6f)),
                    shape = CutCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(step.icon, fontSize = 28.sp)
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                step.title,
                                color = EidosNeon,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                step.hint,
                                color = Color.Gray,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                // Step Text
                Surface(
                    color = Color(0xFF0C1017),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.DarkGray),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = step.text,
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 16.sp,
                        modifier = Modifier.padding(12.dp)
                    )
                }

                // Navigation Controls
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (currentStepIndex > 0) {
                        OutlinedButton(
                            onClick = {
                                audio.playSound(EidosAudioManager.SoundType.TUTORIAL_STEP)
                                currentStepIndex--
                            },
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = EidosCyan),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                            shape = CutCornerShape(4.dp),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("НАЗАД", fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
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
                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(
                            text = if (currentStepIndex < TUTORIAL_STEPS.size - 1) "ДАЛЕЕ ➔" else "ЗАВЕРШИТЬ ОБУЧЕНИЕ (+500 BC)",
                            color = Color.Black,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
