package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.SupabaseClientManager
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.AbyssSeedRng
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.random.Random

@Composable
fun EidosTerminalDialog(
    player: Player?,
    onDismiss: () -> Unit,
    onForceSync: suspend () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val coroutineScope = rememberCoroutineScope()

    var commandInput by remember { mutableStateOf("") }
    var accentColor by remember { mutableStateOf(EidosNeon) }

    // State for interactive features
    var targetPin by remember { mutableIntStateOf(Random.nextInt(10, 100)) }
    var hackAttemptsLeft by remember { mutableIntStateOf(5) }
    var isHackingActive by remember { mutableStateOf(false) }

    val redeemedCodes = remember { mutableStateListOf<String>() }

    val logs = remember {
        mutableStateListOf(
            "EIDOS // NEURAL OS TERMINAL v4.2.0 [CYBER ENGINE]",
            "Система готова. Введите '/help' для меню из 10+ кибер-команд.",
            "────────────────────────────────────────────────────────────"
        )
    }

    fun log(text: String) {
        logs.add(text)
    }

    fun executeCommand(rawCmd: String) {
        val trimmed = rawCmd.trim()
        if (trimmed.isBlank()) return
        log("> $trimmed")

        val parts = trimmed.split("\\s+".toRegex())
        val cmd = parts[0].lowercase()
        val arg = if (parts.size > 1) parts.subList(1, parts.size).joinToString(" ") else ""

        when {
            // 1. HELP & UTILITIES
            cmd == "/help" -> {
                log("═════════════ ДОСТУПНЫЕ ТЕРМИНАЛЬНЫЕ КОМАНДЫ ═════════════")
                log("🎮 ИГРОВЫЕ И ИНТЕРАКТИВНЫЕ ФИШКИ:")
                log("  /hack [pin]   - Взлом сетевого узла EIDOS (подбор 2-значного PIN)")
                log("  /redeem <code>- Активация промокодов (EIDOS2026, MATRIX, EVA09)")
                log("  /mine         - Симулятор майнинга BioCoin в реальном времени")
                log("  /dice [bet]   - Кибер-рулетка на удачу (риск BioCoin)")
                log("  /eva [вопрос] - Диалог с ИИ-помощником EVA-09")
                log("  /bestiary     - База уязвимостей и тактик боссов Бездны")
                log("🎨 КАСТОМИЗАЦИЯ И СИСТЕМА:")
                log("  /color <color>- Цвет терминала (green, cyan, red, amber, purple)")
                log("  /matrix       - Запуск матричного потока кода")
                log("  /glitch       - Имитация критического сбоя системы и вибро-тест")
                log("  /ascii        - Отображение ASCII-артов системного ядра")
                log("🛠 СИСТЕМНЫЕ:")
                log("  /status | /scan | /seed | /sync | /clear")
            }

            // 2. FEATURE #1: /hack (Node Hacking Mini-Game)
            cmd == "/hack" -> {
                if (!isHackingActive) {
                    isHackingActive = true
                    targetPin = Random.nextInt(10, 100)
                    hackAttemptsLeft = 5
                    haptics.abilityActivate()
                    log("⚡ [ВЗЛОМ ЗАПУЩЕН] Узел EIDOS-NODE-99 заблокирован!")
                    log("🎯 Задача: Отгадайте 2-значный PIN (10-99). Попыток: 5.")
                    log("💡 Введите: /hack <число> (например: /hack 50)")
                } else {
                    val guess = arg.toIntOrNull()
                    if (guess == null) {
                        log("✕ ОШИБКА: Укажите 2-значное число (10-99). Пример: /hack 42")
                    } else {
                        hackAttemptsLeft--
                        when {
                            guess == targetPin -> {
                                haptics.lootLegendary()
                                log("✓ [УСПЕХ ВЗЛОМА!] PIN $targetPin ВЕРЕН! Система взломана!")
                                log("🎁 НАГРАДА: +150 BioCoins занесено на баланс!")
                                isHackingActive = false
                                if (player != null) {
                                    coroutineScope.launch {
                                        SupabaseClientManager.addRaidLog(
                                            playerId = player.uid.toString(),
                                            logText = "💻 ВЗЛОМ ТЕРМИНАЛА: Игрок подобрал PIN $targetPin и взломал узел EIDOS!"
                                        )
                                    }
                                }
                            }
                            hackAttemptsLeft <= 0 -> {
                                haptics.criticalHit()
                                log("✕ [ПРОВАЛ ВЗЛОМА] Попытки исчерпаны! Загаданный PIN был: $targetPin")
                                log("🔒 Безопасность блокирует узел. Введите /hack для повтора.")
                                isHackingActive = false
                            }
                            guess < targetPin -> {
                                haptics.click()
                                log("▲ Загаданный PIN БОЛЬШЕ чем $guess. Осталось попыток: $hackAttemptsLeft")
                            }
                            else -> {
                                haptics.click()
                                log("▼ Загаданный PIN МЕНЬШЕ чем $guess. Осталось попыток: $hackAttemptsLeft")
                            }
                        }
                    }
                }
            }

            // 3. FEATURE #2: /redeem <code> (Promo Codes)
            cmd == "/redeem" -> {
                val code = arg.trim().uppercase()
                if (code.isBlank()) {
                    log("✕ Укажите код. Пример: /redeem EIDOS2026")
                } else if (redeemedCodes.contains(code)) {
                    log("✕ ОШИБКА: Промокод '$code' уже активирован в этой сессии!")
                } else {
                    when (code) {
                        "EIDOS2026" -> {
                            redeemedCodes.add(code)
                            haptics.lootLegendary()
                            log("🎉 [ПРОМОКОД АКТИВИРОВАН] Бонус оператора: +100 BioCoins & +50 XP!")
                        }
                        "MATRIX" -> {
                            redeemedCodes.add(code)
                            accentColor = EidosNeon
                            haptics.abilityActivate()
                            log("🟢 [ПРОМОКОД АКТИВИРОВАН] Неоновый режим Матрицы включен!")
                        }
                        "EVA09" -> {
                            redeemedCodes.add(code)
                            haptics.click()
                            log("🤖 [EVA-09]: Приветствую, Оператор. Системы связи активны. Мои алгоритмы с вами.")
                        }
                        "ZERO_POINT" -> {
                            redeemedCodes.add(code)
                            haptics.lootLegendary()
                            log("🌌 [ПРОМОКОД АКТИВИРОВАН] Импульс Нулевой Точки: +300 EXP!")
                        }
                        "CYBER_GHOST" -> {
                            redeemedCodes.add(code)
                            haptics.abilityActivate()
                            log("👤 [ПРОМОКОД АКТИВИРОВАН] Статус 'Кибер-Призрак' присвоен!")
                        }
                        else -> {
                            haptics.criticalHit()
                            log("✕ ОШИБКА: Промокод '$code' недействителен или просрочен.")
                        }
                    }
                }
            }

            // 4. FEATURE #3: /matrix (Code Cascade Stream)
            cmd == "/matrix" -> {
                accentColor = EidosNeon
                haptics.abilityActivate()
                log("🟢 ЗАПУСК МАТРИЧНОГО ПОТОКА ДАННЫХ...")
                log("01000101 01001001 01000100 01001111 01010011")
                log("0x4A8F99 // 0xFF2A10 // 0x00E5FF // 0x76FF03")
                log(">> SYSTEM_MEM_ALLOC: 1024MB ... OK")
                log(">> ABYSS_SIGNAL_STRENGTH: 99.8% ... STABLE")
                log(">> NEURAL_SYNAPSE_LINK: CONNECTED")
            }

            // 5. FEATURE #4: /eva [вопрос] (AI Assistant)
            cmd == "/eva" -> {
                haptics.click()
                val query = arg.lowercase()
                val response = when {
                    query.contains("бездна") || query.contains("рейд") ->
                        "🤖 [EVA-09]: Бездна нестабильна. Рекомендую собирать Чипы Холода и Энергощиты перед глубокими секторами."
                    query.contains("босс") || query.contains("жнец") ->
                        "🤖 [EVA-09]: Кибер-Жнец использует фазовые атаки. Активируйте STEALTH в нужный момент!"
                    query.contains("богатство") || query.contains("деньги") ->
                        "🤖 [EVA-09]: Зачищайте аномалии и торгуйте с Теневым Брокером во время фазы таймера."
                    query.contains("кто ты") || query.contains("eva") ->
                        "🤖 [EVA-09]: Я нейронный ИИ-помощник комплекса EIDOS. Моя цель — выживание операторов."
                    else -> listOf(
                        "🤖 [EVA-09]: Анализирую нейроактивность... Все параметры в пределах нормы.",
                        "🤖 [EVA-09]: В секторах Бездны зафиксированы всплески кристаллической эссенции.",
                        "🤖 [EVA-09]: Совет: Не забудьте синхронизировать прогресс через команду /sync!"
                    ).random()
                }
                log(response)
            }

            // 6. FEATURE #5: /color <color> (Theme Customizer)
            cmd == "/color" -> {
                when (arg.lowercase()) {
                    "green", "зеленый" -> {
                        accentColor = EidosNeon
                        log("🎨 Цвет терминала изменен на [НЕОНОВЫЙ ЗЕЛЕНЫЙ]")
                    }
                    "cyan", "голубой" -> {
                        accentColor = EidosCyan
                        log("🎨 Цвет терминала изменен на [КИБЕР ГОЛУБОЙ]")
                    }
                    "red", "красный" -> {
                        accentColor = EidosRed
                        log("🎨 Цвет терминала изменен на [АВАРИЙНЫЙ КРАСНЫЙ]")
                    }
                    "amber", "янтарный" -> {
                        accentColor = Color(0xFFFFB300)
                        log("🎨 Цвет терминала изменен на [РЕТРО ЯНТАРНЫЙ]")
                    }
                    "purple", "фиолетовый" -> {
                        accentColor = Color(0xFFB388FF)
                        log("🎨 Цвет терминала изменен на [АБСОЛЮТНАЯ БЕЗДНА]")
                    }
                    else -> {
                        log("✕ Укажите цвет: green, cyan, red, amber, purple. Пример: /color cyan")
                    }
                }
            }

            // 7. FEATURE #6: /mine (Console Crypto Mining)
            cmd == "/mine" -> {
                haptics.abilityActivate()
                log("⛏️ [МАЙНИНГ] Запуск хеширования блока BioCoin...")
                coroutineScope.launch {
                    delay(300)
                    log("  [1/3] HASH: 0x8F2A... [ПРОВЕРКА НОДЫ]")
                    delay(300)
                    log("  [2/3] HASH: 0x4C01... [СЛОЖНОСТЬ: 12.8M]")
                    delay(400)
                    log("  [3/3] HASH: 0x0000... [БЛОК НАЙДЕН!]")
                    haptics.lootLegendary()
                    log("💰 [УСПЕХ] Вымайнен блок #9802! +15 BioCoins добавлены!")
                }
            }

            // 8. FEATURE #7: /dice [bet] (Gamble)
            cmd == "/dice" -> {
                val bet = arg.toIntOrNull() ?: 20
                haptics.abilityActivate()
                log("🎲 [РУЛЕТКА] Ставка: $bet BC. Бросок кубика d100...")
                val roll = Random.nextInt(1, 101)
                if (roll > 50) {
                    haptics.lootLegendary()
                    log("🎉 ВЫПАЛО: $roll / 100 [ПОБЕДА!]. Вы выиграли +${bet * 2} BC!")
                } else {
                    haptics.criticalHit()
                    log("💥 ВЫПАЛО: $roll / 100 [ПРОИГРЫШ]. Системная перегрузка. Утрачено $bet BC.")
                }
            }

            // 9. FEATURE #8: /glitch (Glitch Simulation & Haptics)
            cmd == "/glitch" -> {
                haptics.glitchPulse()
                accentColor = EidosRed
                log("⚠️ WARNING: CRITICAL SYSTEM GLITCH DETECTED ⚠️")
                log("E̷I̷D̷O̷S̷_̷C̷O̷R̷E̷_̷E̷R̷R̷O̷R̷:̷ ̷0̷x̷0̷0̷0̷F̷F̷F̷")
                log("▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")
                log("Восстановление нейтрального барьера... OK.")
            }

            // 10. FEATURE #9: /bestiary (Monster Tactics)
            cmd == "/bestiary" -> {
                log("══════════ БАЗА УЯЗВИМОСТЕЙ БОССОВ БЕЗДНЫ ══════════")
                log("💀 [01] КИБЕР-ЖНЕЦ: HP 500 | Atk 45 | Уязвимость: BRUTEFORCE")
                log("❄️ [02] ЦЕРБЕР-09: HP 1200 | Atk 85 | Уязвимость: CRYO CHIP")
                log("👁 [03] НУЛЕВОЙ СТРАЖ: HP 3000 | Atk 180 | Уязвимость: STEALTH")
            }

            // 11. FEATURE #10: /ascii (ASCII Art Visualizer)
            cmd == "/ascii" -> {
                log("   _______  _____ ______   ____  ____ ")
                log("  / ___/ / / / _ / ___/ /  / __ \\/ __/")
                log(" / /__/ /_/ / __/ /__/ /__/ /_/ /\\ \\  ")
                log(" \\___/\\____/_/  \\___/____/\\____/___/  ")
                log("   [NEURAL LINK SYSTEM // CORE 2026]  ")
            }

            // SYSTEM COMMANDS
            cmd == "/status" -> {
                if (player != null) {
                    log("ИМЯ: ${player.username}")
                    log("УРОВЕНЬ: ${player.level} | XP: ${player.xp}")
                    log("BIOCOINS: ${player.biocoin} BC")
                    log("РЕЙДОВ: ${player.raids_done} | МАКС.ГЛУБИНА: ${player.max_depth}м")
                } else {
                    log("ОШИБКА: Нейропрофиль не определен.")
                }
            }
            cmd == "/scan" -> {
                log("СКАНИРОВАНИЕ СИСТЕМЫ...")
                log("✓ SUPABASE CLOUD: ${if (SupabaseClientManager.isConfigured()) "ПОДКЛЮЧЕНО" else "АВТОНОМНЫЙ РЕЖИМ"}")
                log("✓ HAPTICS WAVEFORM: АКТИВНО (Android Vibe API)")
                log("✓ DSP AMBIENT SOUNDTRACK: АКТИВНО (AudioTrack PCM)")
                log("✓ AGSL SHADER ENGINE: ГОТОВ")
            }
            cmd == "/seed" -> {
                val seed = AbyssSeedRng.generateRandomSeed()
                log("СГЕНЕРИРОВАН СИД СЕКТОРА: $seed")
            }
            cmd == "/sync" -> {
                log("СИНХРОНИЗАЦИЯ С ОБЛАКОМ SUPABASE...")
                coroutineScope.launch {
                    try {
                        onForceSync()
                        log("✓ СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
                    } catch (e: Exception) {
                        log("✕ ОШИБКА СИНХРОНИЗАЦИИ: ${e.message}")
                    }
                }
            }
            cmd == "/clear" -> {
                logs.clear()
            }
            else -> {
                log("НЕИЗВЕСТНАЯ КОМАНДА: '$rawCmd'. Введите '/help' для списка.")
            }
        }
        commandInput = ""
    }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(460.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF040A0F)),
            border = androidx.compose.foundation.BorderStroke(1.dp, accentColor),
            shape = CutCornerShape(8.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(12.dp)
            ) {
                // Header Bar
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "💻 EIDOS // NEURAL TERMINAL",
                            color = accentColor,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    IconButton(onClick = onDismiss, modifier = Modifier.size(24.dp)) {
                        Text("✕", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))
                HorizontalDivider(color = accentColor.copy(alpha = 0.4f))
                Spacer(modifier = Modifier.height(6.dp))

                // Terminal Output Area
                LazyColumn(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                        .background(Color.Black.copy(alpha = 0.7f), CutCornerShape(4.dp))
                        .border(1.dp, accentColor.copy(alpha = 0.2f), CutCornerShape(4.dp))
                        .padding(8.dp),
                    reverseLayout = false
                ) {
                    items(logs) { logMsg ->
                        Text(
                            text = logMsg,
                            color = when {
                                logMsg.startsWith(">") -> EidosCyan
                                logMsg.startsWith("✓") || logMsg.startsWith("🎉") || logMsg.startsWith("🟢") -> EidosNeon
                                logMsg.startsWith("✕") || logMsg.startsWith("⚠️") || logMsg.startsWith("💥") -> EidosRed
                                logMsg.startsWith("🤖") -> Color(0xFFB388FF)
                                logMsg.startsWith("EIDOS") || logMsg.startsWith("═") -> Color.Yellow
                                else -> Color.LightGray
                            },
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 14.sp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Input Bar
                OutlinedTextField(
                    value = commandInput,
                    onValueChange = { commandInput = it },
                    placeholder = { Text("Введите команду (/help)...", color = Color.Gray, fontSize = 11.sp) },
                    leadingIcon = { Text(">", color = accentColor, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 8.dp)) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                    keyboardActions = KeyboardActions(onSend = { executeCommand(commandInput) }),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = accentColor,
                        unfocusedBorderColor = Color.Gray.copy(alpha = 0.5f),
                        cursorColor = accentColor
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}
