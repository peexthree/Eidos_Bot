package com.example.eidos.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.platform.LocalContext
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.utils.EidosAudioManager
import kotlinx.coroutines.delay

// 1. ADVANCED PROGRESSIVE HACKING MINIGAME (Scales with Depth)
@Composable
fun HackingMinigameDialog(
    depth: Int = 1,
    onDismiss: () -> Unit,
    onSuccess: () -> Unit,
    onFailure: () -> Unit
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    // Scaling difficulty with depth
    val sequenceLength = when {
        depth >= 10 -> 4
        depth >= 5 -> 3
        else -> 2
    }
    val timeLimitSec = maxOf(10, 30 - (depth * 2)) // Gets tighter with depth

    val hexPool = remember { listOf("0xFA", "0x70", "0x99", "0x3C", "0xEE", "0x12", "0xBF", "0x4D", "0xFF", "0x00", "0xCA", "0xFE") }
    val targetSequence = remember { hexPool.shuffled().take(sequenceLength) }
    val gridSize = if (depth >= 5) 9 else 6
    val gridNodes = remember { (targetSequence + hexPool.shuffled().take(gridSize - targetSequence.size)).shuffled() }

    var userProgress = remember { mutableStateOf(emptyList<String>()) }
    var timeLeftSec = remember { mutableIntStateOf(timeLimitSec) }
    var isFinished = remember { mutableStateOf(false) }
    var gameResult = remember { mutableStateOf<Boolean?>(null) } // true = success, false = fail

    LaunchedEffect(isFinished.value) {
        if (!isFinished.value) {
            while (timeLeftSec.intValue > 0 && !isFinished.value) {
                delay(1000)
                timeLeftSec.intValue--
            }
            if (timeLeftSec.intValue <= 0 && !isFinished.value) {
                isFinished.value = true
                gameResult.value = false
                onFailure()
            }
        }
    }

    Dialog(onDismissRequest = {
        isFinished.value = true
        onDismiss()
    }) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.Black, CutCornerShape(8.dp))
                .border(2.dp, if (gameResult.value == true) EidosNeon else if (gameResult.value == false) EidosRed else EidosCyan, CutCornerShape(8.dp))
                .padding(20.dp)
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    "⚡ КВАНТОВЫЙ ВЗЛОМ // СЛОЙ $depth",
                    color = EidosCyan,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )
                Text(
                    "Соберите правильную последовательность байтов до истечения времени. Чем глубже Слой, тем выше сложность и короче таймер!",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "ТАЙМЕР: ${timeLeftSec.intValue}s",
                        color = if (timeLeftSec.intValue <= 5) EidosRed else EidosNeon,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        "ПРОГРЕСС: ${userProgress.value.size}/$sequenceLength",
                        color = EidosCyan,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                LinearProgressIndicator(
                    progress = { timeLeftSec.intValue.toFloat() / timeLimitSec.toFloat() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp),
                    color = if (timeLeftSec.intValue <= 5) EidosRed else EidosNeon,
                    trackColor = Color.DarkGray
                )

                // Target Sequence Display
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(EidosGlass)
                        .border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(4.dp))
                        .padding(10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        targetSequence.forEachIndexed { idx, code ->
                            val isMatched = idx < userProgress.value.size && userProgress.value[idx] == code
                            Text(
                                text = code,
                                color = if (isMatched) EidosNeon else if (idx == userProgress.value.size) EidosCyan else Color.Gray,
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                if (isFinished.value) {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = if (gameResult.value == true) "✔ ДОСТУП РАЗРЕШЕН: Квантовый узел взломан!" else "✖ ВЗЛОМ ПРОВАЛЕН: Сработал защитный скрипт!",
                        color = if (gameResult.value == true) EidosNeon else EidosRed,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Button(
                        onClick = onDismiss,
                        colors = ButtonDefaults.buttonColors(containerColor = if (gameResult.value == true) EidosNeon else EidosRed),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("ПРОДОЛЖИТЬ", color = Color.Black, fontWeight = FontWeight.Bold)
                    }
                } else {
                    // Grid Matrix (3x2 or 3x3)
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        gridNodes.chunked(3).forEach { rowNodes ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                rowNodes.forEach { node ->
                                    val expectedCode = targetSequence.getOrNull(userProgress.value.size)
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .aspectRatio(1.6f)
                                            .background(EidosGlass)
                                            .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                            .clickable {
                                                if (node == expectedCode) {
                                                    val nextProg = userProgress.value + node
                                                    userProgress.value = nextProg
                                                    if (nextProg.size == targetSequence.size) {
                                                        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                                                        isFinished.value = true
                                                        gameResult.value = true
                                                        onSuccess()
                                                    } else {
                                                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                                                    }
                                                } else {
                                                    audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                                                    isFinished.value = true
                                                    gameResult.value = false
                                                    onFailure()
                                                }
                                            },
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            node,
                                            color = Color.White,
                                            fontSize = 14.sp,
                                            fontWeight = FontWeight.Bold,
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
    }
}

// 2. LORE TRIVIA / RIDDLE EVENT DIALOG (Optional Encounter in Abyssal Raids)
data class LoreRiddle(
    val question: String,
    val options: List<String>,
    val correctIndex: Int,
    val explanation: String
)

val LORE_RIDDLES = listOf(
    LoreRiddle(
        question = "Кто разработал изначальную квантовую матрицу и систему EIDOS?",
        options = listOf("Инквизиторы Ядра", "Архитекторы", "Протоколы Хаоса"),
        correctIndex = 1,
        explanation = "Архитекторы перенесли сознания человечества в матрицу, создав идеальный цифровой мир."
    ),
    LoreRiddle(
        question = "Что стало истинной причиной Великого Глитча в системе?",
        options = listOf("Случайный скачок напряжения", "Протокол распада Энтропии", "Атака внешнего вируса из космоса"),
        correctIndex = 1,
        explanation = "Архитектор Елена запустила протокол распада, чтобы победить стагнацию вечной жизни."
    ),
    LoreRiddle(
        question = "Какой главный внутренний стимул ведет Осколок сквозь Нулевой Слой?",
        options = listOf("Жажда наживы и крипты", "Фрагмент памяти из прошлой жизни", "Приказ EIDOS-CORE"),
        correctIndex = 1,
        explanation = "Осколок ищет разгадку искаженного воспоминания, ради которого готов спускаться в самую глубь."
    ),
    LoreRiddle(
        question = "Кто является хранителем артефактов и аудиокассет забытой Земли?",
        options = listOf("Теневой Брокер (Admin-00)", "Голос EIDOS", "Гладиатор Арены"),
        correctIndex = 0,
        explanation = "Admin-00 тайно передает осколки человеческой истории тем, кто готов слушать."
    )
)

@Composable
fun LoreRiddleDialog(
    onDismiss: () -> Unit,
    onCorrectAnswer: () -> Unit,
    onWrongAnswer: () -> Unit
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val currentRiddle = remember { LORE_RIDDLES.random() }
    var selectedOption by remember { mutableStateOf<Int?>(null) }
    var isFinished by remember { mutableStateOf(false) }
    var isCorrect by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = { if (isFinished) onDismiss() }) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.Black, CutCornerShape(8.dp))
                .border(2.dp, Color.Yellow, CutCornerShape(8.dp))
                .padding(20.dp)
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    "🧠 ЗАГАДКА АНОМАЛИИ // ЛОР-СОБЫТИЕ",
                    color = Color.Yellow,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )

                Card(
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.5f)),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = currentRiddle.question,
                            color = Color.White,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 16.sp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                currentRiddle.options.forEachIndexed { index, option ->
                    val isSelected = selectedOption == index
                    val optionCorrect = index == currentRiddle.correctIndex
                    val btnColor = when {
                        isFinished && optionCorrect -> EidosNeon.copy(alpha = 0.3f)
                        isFinished && isSelected && !optionCorrect -> EidosRed.copy(alpha = 0.3f)
                        isSelected -> Color.Yellow.copy(alpha = 0.2f)
                        else -> EidosGlass
                    }

                    Surface(
                        color = btnColor,
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (isFinished && optionCorrect) EidosNeon else if (isSelected) Color.Yellow else Color.DarkGray
                        ),
                        shape = CutCornerShape(6.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable(enabled = !isFinished) {
                                selectedOption = index
                                isFinished = true
                                isCorrect = optionCorrect
                                if (optionCorrect) {
                                    audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                                    onCorrectAnswer()
                                } else {
                                    audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                                    onWrongAnswer()
                                }
                            }
                    ) {
                        Text(
                            text = "${index + 1}. $option",
                            color = Color.LightGray,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(10.dp)
                        )
                    }
                }

                if (isFinished) {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = if (isCorrect) "✔ ВЕРНО! +XP, +Лор-резонанс\n${currentRiddle.explanation}" else "✖ ОШИБКА! -Сигнал / урон\n${currentRiddle.explanation}",
                        color = if (isCorrect) EidosNeon else EidosRed,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Button(
                        onClick = onDismiss,
                        colors = ButtonDefaults.buttonColors(containerColor = if (isCorrect) EidosNeon else EidosRed),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("ПРОДОЛЖИТЬ РЕЙД", color = Color.Black, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}
