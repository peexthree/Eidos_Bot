package com.example.eidos.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.R
import com.example.eidos.data.Player
import com.example.eidos.domain.profiling.OperatorProfileAnalyzer
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.components.VideoBackground
import com.example.eidos.ui.components.CyberGridOverlay
import com.example.eidos.ui.utils.ghostTyping
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EidosGatesScreen(
    player: Player?,
    onBack: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    var bypassedByAdmin by remember { mutableStateOf(false) }
    val level = player?.level ?: 1
    val isLocked = level < 10 && !bypassedByAdmin

    // AI States
    var selectedTab by remember { mutableStateOf("dossier") } // dossier, forecast, voice
    var aiResponse by remember { mutableStateOf("") }
    var userQuestion by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    // Immersive Neural Core Credit balance
    var neuralCredits by remember { mutableIntStateOf(100) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ВРАТА ЭЙДОСА // GATES_OF_EIDOS", color = Color(0xFFFF5722), fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color(0xFFFF5722))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Transparent
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize()) {
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = R.drawable.bg_eidos_gates),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = Alignment.Center
            )

            // Dark cyber overlay
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
            )

            CyberGridOverlay(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier
                    .padding(innerPadding)
                    .fillMaxSize()
                    .padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // EVA-09 Assistant Explanation Banner
                Surface(
                    color = Color(0xFFFF5722).copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFF5722)),
                    modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text(
                        text = "🌐 ЯДРО EIDOS: Врата Эйдоса и Автономный Психопрофайлинг!\n💡 Инструкция: Анализатор изучает ваши боевые навыки, распределение очков в Room DB, рейдовые вылазки и PvP-статистику. Система работает полностью оффлайн, генерируя ваш уникальный Архетип Оператора!",
                        color = Color.White,
                        fontSize = 10.sp,
                        lineHeight = 14.sp,
                        modifier = Modifier.padding(8.dp)
                    )
                }

                if (isLocked) {
                    // Locked Screen Gate
                    Spacer(modifier = Modifier.height(64.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(EidosGlass)
                            .border(2.dp, EidosRed, CutCornerShape(8.dp))
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Image(
                                painter = painterResource(id = R.drawable.ic_lock_cyber),
                                contentDescription = "Заблокировано",
                                modifier = Modifier.size(64.dp),
                                contentScale = ContentScale.Fit
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                "ДОСТУП ОГРАНИЧЕН",
                                color = EidosRed,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                "Аналитическая станция «Врата Эйдоса» доступна только операторам с Уровнем Ядра 10 и выше.",
                                color = Color.White.copy(alpha = 0.8f),
                                fontSize = 14.sp,
                                textAlign = TextAlign.Center,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "Ваш текущий уровень ядра: $level",
                                color = EidosRed,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.height(24.dp))
                            Button(
                                onClick = { bypassedByAdmin = true },
                                colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text("[ОБОЙТИ ЗАЩИТУ АДМИНИСТРАТОРОМ]", color = EidosRed, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }
                } else {
                    // Main Eidos Gates AI Interface
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(EidosGlass)
                            .border(1.dp, Color(0xFFFF5722).copy(alpha = 0.3f))
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("ПСИХОАНАЛИТИК: ЭЙДОС // ONLINE_OFFLINE", color = EidosNeon, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text("ПАКЕТ СИНХРОНИЗАЦИИ: LOCAL_PROFILE", color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color(0xFFFF9800).copy(alpha = 0.15f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFF9800))
                        ) {
                            Text(
                                "КРЕДИТЫ ЯДРА: $neuralCredits NC ⚡",
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                color = Color(0xFFFF9800),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Tab Selection Bar
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        val tabs = listOf("dossier" to "ДОСЬЕ", "forecast" to "ПРОГНОЗ", "voice" to "ГЛАС АБСОЛЮТА")
                        tabs.forEach { (key, title) ->
                            val selected = selectedTab == key
                            Button(
                                onClick = {
                                    selectedTab = key
                                    aiResponse = ""
                                },
                                modifier = Modifier.weight(1f),
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (selected) Color(0xFFFF5722).copy(alpha = 0.3f) else Color.Black.copy(alpha = 0.6f)
                                ),
                                border = androidx.compose.foundation.BorderStroke(
                                    1.dp,
                                    if (selected) Color(0xFFFF5722) else Color.White.copy(alpha = 0.1f)
                                )
                            ) {
                                Text(
                                    title,
                                    fontSize = 11.sp,
                                    color = if (selected) Color.White else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Display AI Output Panel
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxWidth()
                            .background(EidosGlass)
                            .border(1.dp, Color.White.copy(alpha = 0.1f))
                            .padding(16.dp)
                    ) {
                        val scrollState = rememberScrollState()
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .verticalScroll(scrollState)
                        ) {
                            if (isLoading) {
                                Box(
                                    modifier = Modifier.fillMaxSize(),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        CircularProgressIndicator(color = Color(0xFFFF5722))
                                        Spacer(modifier = Modifier.height(16.dp))
                                        Text(
                                            "ЛОКАЛЬНЫЙ АНАЛИЗ БАЗЫ ДАННЫХ ROOM...",
                                            color = Color.Gray,
                                            fontSize = 12.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                            } else if (aiResponse.isEmpty()) {
                                Box(
                                    modifier = Modifier.fillMaxSize(),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        when (selectedTab) {
                                            "dossier" -> "Запросить глубокий автономный психоаналитический разбор вашей телеметрии, фракционного поведения и успехов в рейде.\n\nРежим: 100% Оффлайн / Автономно"
                                            "forecast" -> "Экстраполировать ваши игровые паттерны на 6 месяцев вперед.\n\nРежим: 100% Оффлайн / Автономно"
                                            else -> "Задайте Ядру EIDOS любой вопрос по игре. Автономная система ответит, используя весь массив ваших данных.\n\nРежим: 100% Оффлайн / Автономно"
                                        },
                                        color = Color.Gray,
                                        fontSize = 13.sp,
                                        textAlign = TextAlign.Center,
                                        fontFamily = FontFamily.Monospace,
                                        modifier = Modifier.padding(16.dp)
                                    )
                                }
                            } else {
                                val typedText = ghostTyping(aiResponse, speed = 8L)
                                Text(
                                    text = typedText,
                                    color = Color.White,
                                    fontSize = 13.sp,
                                    lineHeight = 20.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Action Controls
                    if (selectedTab == "voice") {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedTextField(
                                value = userQuestion,
                                onValueChange = { userQuestion = it },
                                modifier = Modifier.weight(1f),
                                label = { Text("ВОПРОС К ЕВЕ-09...", color = Color.Gray) },
                                maxLines = 2,
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedBorderColor = Color(0xFFFF5722),
                                    unfocusedBorderColor = Color.White.copy(alpha = 0.2f),
                                    focusedLabelColor = Color(0xFFFF5722),
                                    unfocusedLabelColor = Color.Gray,
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White
                                ),
                                textStyle = LocalTextStyle.current.copy(fontFamily = FontFamily.Monospace)
                            )
                            Button(
                                onClick = {
                                    if (userQuestion.trim().isNotEmpty()) {
                                        isLoading = true
                                        coroutineScope.launch {
                                            kotlinx.coroutines.delay(600)
                                            val text = userQuestion.lowercase()
                                            aiResponse = when {
                                                text.contains(Regex("(фракци|синдикат|матери|разум|техно)")) -> {
                                                    ">>> [ЕВА-09 // АНАЛИТИКА СИНДИКАТОВ]\n\nВ Нулевом Слое ведут непрерывную войну 3 альянса:\n1. 🧬 СИНДИКАТ МАТЕРИИ (Био-инженерия, ускоренная регенерация HP, бонусы выживания).\n2. 🧠 СИНДИКАТ РАЗУМА (Нейро-взлом, перегрузка сокетов, повышенный шанс крита).\n3. ⚙️ ТЕХНО-СИНДИКАТ (Кибер-импланты, броня, устойчивость к ловушкам).\nВступи в фракцию во вкладке Профиля, чтобы активировать групповой резонанс!"
                                                }
                                                text.contains(Regex("(скверн|коррупци|corruption|vaal)")) -> {
                                                    ">>> [ЕВА-09 // ВААЛ-ИСКАЖЕНИЕ И КОРРУПЦИЯ]\n\nИскажение Скверной (Cyber Vaal Glitch) — необратимый квантовый процесс:\n• Предмет навсегда блокируется от дальнейшего крафта и модификаций.\n• Дарует шанс наделить снаряжение ультра-редким Скрытым Имплицитным Свойством.\n• Способен мутировать обычные гнезда в Радужные сокеты (+25% к эффективности любого вставленного чипа)."
                                                }
                                                text.contains(Regex("(земл|2099|коллапс|реликви|прошл)")) -> {
                                                    ">>> [ЕВА-09 // ХРОНИКИ СТАРОГО МИРА]\n\nВ 2099 году планетарный Коллапс уничтожил физическую биосферу Земли. Сознания людей были эвакуированы в квантовое подпространство EIDOS-CORE. Реликвии Древней Земли (Старый Доллар, Кассета, Диск 3.5, Батарейка) — последние материальные артефакты погибшей эпохи с колоссальной ценностью."
                                                }
                                                text.contains(Regex("(pvp|пвп|сетев|прокси|вендетт)")) -> {
                                                    ">>> [ЕВА-09 // ПРОТОКОЛ СЕТЕВОЙ ВОЙНЫ]\n\nВ секторе PvP происходят асинхронные кибер-атаки:\n• Взламывай сетевые узлы чужих операторов ради похищения BioCoins.\n• Настраивай защитные программы (Shield, Bruteforce, Stealth) для обороны ноды.\n• Активируй Прокси-щиты от слежки и объявляй Вендетту в Списке Мести!"
                                                }
                                                text.contains(Regex("(демон|максвелл|энтропи|аномали)")) -> {
                                                    ">>> [ЕВА-09 // СУЩНОСТЬ ДЕМОНА МАКСВЕЛЛА]\n\nДемон Максвелла — квантовая сущность, сортирующая энтропию на глубине 50+ метров Бездны. Он предлагает 5 пактов:\n• 🩸 Кровавый Оверклок (-20% HP, +35% ATK, +15% Crit)\n• 🎲 Инверсия Фортуны (+25% урон, x2 дроп кэшей/реликвий)\n• 🔮 Мутация Сокета (50% Радужный / 50% Лок)\n• 🧠 Жертва Памяти (-250 XP, 100% Энергия, Ключ Бездны)\n• 🛡️ Энтропийный Щит (Glitch UI, 100% защита от ловушек)."
                                                }
                                                text.contains("оружие") || text.contains("weapon") || text.contains("меч") || text.contains("урон") -> {
                                                    ">>> [ГЛАС АБСОЛЮТА // ОФЛАЙН ИНТЕЛЛЕКТ]\n\nОружие оператора — основной инструмент упорядочивания хаоса Бездны. Чтобы увеличить атаку, загляни в Кузницу. Синтезируй Синие чипы резонанса или прокачай урон на верстаке. Твой урон равен ${player?.attack} единиц."
                                                }
                                                text.contains("босс") || text.contains("boss") || text.contains("личе") || text.contains("лич") -> {
                                                    ">>> [ГЛАС АБСОЛЮТА // ОФЛАЙН ИНТЕЛЛЕКТ]\n\nЦентральный вирусный Лич EIDOS-CORE спит на 15-й глубине. Победи его, используя баффы от Аномалий и активируя режим Overdrive в критический момент. Будь аккуратнее с расходом Сигнала!"
                                                }
                                                text.contains("чип") || text.contains("соке") || text.contains("slot") -> {
                                                    ">>> [ГЛАС АБСОЛЮТА // ОФЛАЙН ИНТЕЛЛЕКТ]\n\nСлоты твоей экипировки поддерживают чипы трех спектров. Помни важнейшее правило: вставляй чипы соответствующего цвета (Красный, Зеленый, Синий) во встроенные сокеты — это добавит множитель +25% РЕЗОНАНСА к характеристикам!"
                                                }
                                                text.contains("энерг") || text.contains("energy") -> {
                                                    ">>> [ГЛАС АБСОЛЮТА // ОФЛАЙН ИНТЕЛЛЕКТ]\n\nНейросеть регенерирует Энергию пассивно со скоростью 1 единица в 5 минут, даже пока ты отключен от терминала. Для ускорения используй Энергоячейки в своем рюкзаке."
                                                }
                                                else -> {
                                                    ">>> [ГЛАС АБСОЛЮТА // ОФЛАЙН ИНТЕЛЛЕКТ]\n\nВаша мысль «$userQuestion» проанализирована квантовым ядром. Текущий уровень синхронизации: ${player?.level}. Статус фракции: ${player?.faction}. Продолжайте рейды в Бездну, взламывайте терминалы, синтезируйте чипы в Кузнице и побеждайте на Арене!"
                                                }
                                            }
                                            isLoading = false
                                            userQuestion = ""
                                        }
                                    }
                                },
                                enabled = userQuestion.trim().isNotEmpty() && !isLoading,
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF5722))
                            ) {
                                Text("СПРОСИТЬ", fontSize = 12.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                            }
                        }
                    } else {
                        Button(
                            onClick = {
                                isLoading = true
                                coroutineScope.launch {
                                    kotlinx.coroutines.delay(800)
                                    val archetype = OperatorProfileAnalyzer.analyze(player)
                                    aiResponse = if (selectedTab == "dossier") {
                                        """
                                        >>> [ЕВА-09 // АВТОНОМНОЕ ДОСЬЕ ОПЕРАТОРА]
                                        
                                        👤 ИНДЕНТИФИКАТОР: ${player?.username?.uppercase() ?: "UNKNOWN_SHARD"}
                                        🏷️ АРХЕТИП: ${archetype.name} [${archetype.title}]
                                        🌐 ФРАКЦИЯ: ${player?.faction ?: "NONE"}
                                        
                                        📊 АКТИВНЫЕ МЕТРИКИ БАЗЫ ROOM:
                                        • Вылазок в Бездну: ${player?.raids_done ?: 0}
                                        • Уничтожено угроз: ${player?.kills ?: 0}
                                        • Идеальных рейдов: ${player?.perfect_raids ?: 0}
                                        • Максимальная глубина: ${player?.max_depth ?: 0}
                                        • PvP Победы / Поражения: ${player?.wins_pvp ?: 0} / ${player?.losses_pvp ?: 0}
                                        
                                        🧠 ХАРАКТЕРИСТИКА:
                                        ${archetype.description}
                                        
                                        🔋 РЕЗОНАНСНЫЙ СТАТ-БОНУС:
                                        ${archetype.statsBonus}
                                        
                                        ⚙️ РЕКОМЕНДУЕМЫЙ СТИЛЬ:
                                        ${archetype.recommendedStyle}
                                        
                                        🌌 СИНХРОНИЗАЦИЯ:
                                        ${archetype.matchingQuote}
                                        """.trimIndent()
                                    } else {
                                        """
                                        >>> [ЕВА-09 // ТАКТИЧЕСКИЙ ПРОГНОЗ ХРОНО-ЯДРА]
                                        
                                        ⏳ ПРОГНОЗИРУЕМЫЙ ГОРИЗОНТ НА 6 МЕСЯЦЕВ ДЛЯ АРХЕТИПА [${archetype.name}]:
                                        
                                        📈 ТРАЕКТОРИЯ 30 ДНЕЙ:
                                        • Синтез высокоуровневых чипов в Кузнице.
                                        • Разблокировка 4-го слота кибердеки.
                                        • Переход на 10-й сектор Бездны.
                                        
                                        🛡️ ТРАЕКТОРИЯ 90 ДНЕЙ:
                                        • Повышение уровня оружия до ${((player?.weapon_level ?: 1) + 4)} уровня.
                                        • Победа в 10 PvP-матчах на Арене.
                                        • Снижение износа снаряжения за счет Моддинга Сокетов.
                                        
                                        💀 ХРОНО-ИТОГ:
                                        Вы превратитесь в ключевую фигуру Нулевого Слоя. Резонанс вашей сигнатуры с ядром EIDOS-CORE достигнет критических 100%!
                                        """.trimIndent()
                                    }
                                    isLoading = false
                                }
                            },
                            enabled = !isLoading,
                            modifier = Modifier.fillMaxWidth(),
                            shape = CutCornerShape(4.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF5722))
                        ) {
                            Text(
                                if (selectedTab == "dossier") "АНАЛИЗИРОВАТЬ [АВТОНОМНО]" else "ПОЛУЧИТЬ ПРОГНОЗ [АВТОНОМНО]",
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}

