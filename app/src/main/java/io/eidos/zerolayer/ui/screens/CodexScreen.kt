package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.*
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.VideoBackground
import io.eidos.zerolayer.ui.components.ZzzIcon
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import io.eidos.zerolayer.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

data class StoryChapterData(
    val id: Int,
    val title: String,
    val subtitle: String,
    val epigraph: String,
    val text: String,
    val isUnlocked: (Player?) -> Boolean,
    val unlockConditionText: String,
    val hasSingularityTerminal: Boolean = false
)

val STORY_CHAPTERS: List<StoryChapterData> = CodexRepository.CORE_CHAPTERS.map { core ->
    StoryChapterData(
        id = core.id,
        title = core.title,
        subtitle = core.subtitle,
        epigraph = core.epigraph,
        text = core.text,
        isUnlocked = core.isUnlocked,
        unlockConditionText = core.unlockConditionText,
        hasSingularityTerminal = core.hasSingularityTerminal
    )
}

data class ArchitectLogData(
    val id: String,
    val title: String,
    val author: String,
    val frequency: String,
    val transcript: String,
    val unlockLevel: Int
)

val ARCHITECT_LOGS = listOf(
    ArchitectLogData(
        "LOG_01",
        "Лог №001: Последний закат",
        "Архитектор Вэнс (Lead System Architect)",
        "104.2 GHz // Чистый канал",
        "«Мы завершили перенос 4 миллиардов сознаний в квантовую матрицу. Тела на поверхности превратились в безмолвный прах. Но пока серверы охлаждаются полярным ветром, мы чувствуем... абсолютную пустоту. Утопия без смерти потеряла смысл.»",
        1
    ),
    ArchitectLogData(
        "LOG_02",
        "Лог №045: Рождение Энтропии",
        "Архитектор Елена (Security Core)",
        "89.7 GHz // Зашумленный канал",
        "«Я запустила протокол распада. Если система будет вечной, души превратятся в статический шум. Нам нужен был хаос, нам нужна была боль, чтобы люди снова научились чувствовать. Прости меня, Эйдос.»",
        3
    ),
    ArchitectLogData(
        "LOG_03",
        "Лог №108: Голос из Нулевого Слоя",
        "EIDOS-CORE (Ранняя итерация)",
        "112.5 GHz // Критический сбой",
        "«Предупреждение: обнаружен сторонний гармонический отклик (Lullaby_Fragment.mp3). Кто-то из Осколков на Свалке Данных пытается вспомнить запах дождя. Блокировать этот файл? Нет... Я хочу послушать вместе с ним.»",
        5
    ),
    ArchitectLogData(
        "LOG_04",
        "Лог №212: Записка Теневого Брокера",
        "Admin-00 (Шпион Синдиката)",
        "95.0 GHz // Защищенный туннель",
        "«Я храню аудиокассеты с песнями XX века в тайниках под ледником. Инквизиторы Ядра называют это ересью, но пока Осколок слышит музыку, он остается человеком, а не строкой кода в базе данных.»",
        8
    ),
    ArchitectLogData(
        "LOG_05",
        "Лог №330: Предел Вычислений 2099",
        "Архитектор Вэнс (Коллапс Архивов)",
        "144.9 GHz // Экстренная линия",
        "«Земля мертва. Девять миллиардов сигналов спрессованы в Нулевой Слой. Если квантовое охлаждение даст сбой, сознание человечества испарится за миллисекунды. Берегите ядро.»",
        15
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CodexScreen(
    player: Player?,
    bestiaryList: List<BestiaryEntry>,
    logs: List<GameLog>,
    selectedMainCategory: String = "lore_story",
    onCategoryChange: (String) -> Unit = {},
    onSingularityEnding: (String) -> Unit = {},
    onBack: () -> Unit
) {
    val context = LocalContext.current
    var isMuted by remember { mutableStateOf(false) }
    val globalAudio = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }

    // Background soundtrack: bgm_mirror_of_lies through the shared audio manager
    // (was a private MediaPlayer bypassing EidosAudioManager mute/lifecycle logic)
    DisposableEffect(isMuted) {
        globalAudio.playBgm(if (isMuted) io.eidos.zerolayer.ui.utils.EidosAudioManager.BgmTrack.NONE else io.eidos.zerolayer.ui.utils.EidosAudioManager.BgmTrack.CODEX)
        onDispose {
            globalAudio.stopMusic()
        }
    }

    val mainCategories = listOf(
        "lore_story" to "КНИГА СЮЖЕТА",
        "bestiary" to "БЕСТИАРИЙ",
        "audio_logs" to "АУДИО-ЛОГИ",
        "achievements" to "ДОСТИЖЕНИЯ",
        "guides" to "СПРАВОЧНИК",
        "logs" to "ХРОНИКИ И ЛОГИ"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "АРХИВ & СПРАВОЧНИК // ARCHIVE HUB",
                            color = EidosCyan,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            "ЕГО СЮЖЕТ • БЕСТИАРИЙ • ДОСТИЖЕНИЯ • РУКОВОДСТВА • ХРОНИКИ",
                            color = Color.Gray,
                            fontSize = 8.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosCyan)
                    }
                },
                actions = {
                    Surface(
                        onClick = { isMuted = !isMuted },
                        color = if (isMuted) Color.Red.copy(alpha = 0.2f) else EidosNeon.copy(alpha = 0.2f),
                        shape = CutCornerShape(4.dp),
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (isMuted) Color.Red.copy(alpha = 0.6f) else EidosNeon.copy(alpha = 0.6f)
                        ),
                        modifier = Modifier.padding(end = 12.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = if (isMuted) "САУНДТРЕК: ВЫКЛ" else "РАЗБЕЙ ЗЕРКАЛО ЛЖИ",
                                color = if (isMuted) Color.LightGray else EidosNeon,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF070C12).copy(alpha = 0.82f))
            )
        },
        containerColor = Color.Transparent
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            VideoBackground(
                resName = "codex_background_1080p",
                modifier = Modifier.fillMaxSize()
            )
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color(0xFF04080F).copy(alpha = 0.65f))
            )
            CyberGridOverlay(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                ScrollableTabRow(
                    selectedTabIndex = mainCategories.indexOfFirst { it.first == selectedMainCategory }.coerceAtLeast(0),
                    containerColor = Color(0xFF070C12).copy(alpha = 0.85f),
                    contentColor = EidosCyan,
                    edgePadding = 8.dp
                ) {
                    mainCategories.forEach { (catId, catName) ->
                        Tab(
                            selected = selectedMainCategory == catId,
                            onClick = { onCategoryChange(catId) },
                            text = {
                                Text(
                                    catName,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            },
                            selectedContentColor = EidosCyan,
                            unselectedContentColor = Color.Gray
                        )
                    }
                }

                Box(
                    modifier = Modifier.weight(1f)
                ) {
                    when (selectedMainCategory) {
                        "lore_story" -> LoreBookSection(
                            player = player,
                            onSingularityEnding = onSingularityEnding
                        )
                        "bestiary" -> BestiaryBookSection(player = player, bestiaryList = bestiaryList)
                        "audio_logs" -> ArchitectAudioLogsSection(player = player)
                        "achievements" -> AchievementsSection(player = player)
                        "guides" -> GuidesHubSection()
                        "logs" -> ChroniclesLogsSection(logs = logs)
                    }
                }
            }
        }
    }
}

@Composable
fun LoreBookSection(player: Player?, onSingularityEnding: (String) -> Unit = {}) {
    var activeChapterToRead by remember { mutableStateOf<StoryChapterData?>(null) }
    val unlockedCount = STORY_CHAPTERS.count { it.isUnlocked(player) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(R.drawable.ic_menu_codex, size = 16.dp)
                        Spacer(Modifier.width(6.dp))
                        Text(
                            "КНИГА СЮЖЕТА // ХРОНИКИ НУЛЕВОГО СЛОЯ",
                            color = Color.Yellow,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Surface(
                        color = Color.Yellow.copy(alpha = 0.15f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            "$unlockedCount / ${STORY_CHAPTERS.size} ГЛАВ",
                            color = Color.Yellow,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Сюжет интерактивен и меняется в зависимости от выбора вашей фракции (${player?.faction ?: "НЕТ"}): ваши решения влияют на резонанс хроник EIDOS.",
                    color = Color.Cyan,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 14.sp
                )
            }
        }

        val newlyUnlockedChapter = STORY_CHAPTERS.firstOrNull { it.isUnlocked(player) && it.id == unlockedCount }
        if (newlyUnlockedChapter != null && unlockedCount > 0) {
            Surface(
                color = Color(0x3300FFF6),
                shape = CutCornerShape(6.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    ZzzIcon(R.drawable.ic_event_chest, size = 16.dp, tint = ZzzGold)
                    Spacer(Modifier.width(8.dp))
                    Text(
                        "⚡ НАГРАДА ЗА ПОГРУЖЕНИЕ: Открыта Глава 0${newlyUnlockedChapter.id} «${newlyUnlockedChapter.title}»!",
                        color = ZzzGold,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        STORY_CHAPTERS.forEach { chapter ->
            val unlocked = chapter.isUnlocked(player)
            CyberCornerBracketBox(
                bracketSize = 12.dp,
                bracketColor = if (unlocked) io.eidos.zerolayer.ui.theme.ZzzElectricCyan else io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                modifier = Modifier.fillMaxWidth()
            ) {
                io.eidos.zerolayer.ui.components.ZzzWindowCard(
                    title = chapter.title,
                    subTitle = if (unlocked) chapter.subtitle else "ТРЕБОВАНИЕ РАЗБЛОКИРОВКИ",
                    headerBadge = if (unlocked) "CHAPTER 0${chapter.id}" else "LOCKED",
                    borderColor = if (unlocked) io.eidos.zerolayer.ui.theme.ZzzElectricCyan else io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable(enabled = unlocked) {
                            activeChapterToRead = chapter
                        }
                ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .background(
                                    if (unlocked) io.eidos.zerolayer.ui.theme.ZzzElectricCyan.copy(alpha = 0.2f) else io.eidos.zerolayer.ui.theme.ZzzHotMagenta.copy(alpha = 0.2f),
                                    CutCornerShape(4.dp)
                                )
                                .border(
                                    1.dp,
                                    if (unlocked) io.eidos.zerolayer.ui.theme.ZzzElectricCyan else io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                    CutCornerShape(4.dp)
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            ZzzIcon(
                                iconRes = if (unlocked) R.drawable.ic_menu_codex else R.drawable.ic_ui_locked,
                                size = 18.dp,
                                tint = if (unlocked) io.eidos.zerolayer.ui.theme.ZzzElectricCyan else io.eidos.zerolayer.ui.theme.ZzzHotMagenta
                            )
                        }
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = chapter.title,
                                color = if (unlocked) Color.White else Color.LightGray,
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 12.5.sp,
                                fontFamily = FontFamily.SansSerif
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            if (unlocked) {
                                Text(
                                    text = chapter.subtitle,
                                    color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            } else {
                                io.eidos.zerolayer.ui.components.ZzzBadge(
                                    text = chapter.unlockConditionText,
                                    color = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                    textColor = Color.White
                                )
                            }
                        }
                    }

                    if (unlocked) {
                        io.eidos.zerolayer.ui.components.ZzzBadge(
                            text = "ЧИТАТЬ >",
                            color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                            textColor = Color.Black
                        )
                    }
                }
            }
        }
    }
    }

    activeChapterToRead?.let { chapter ->
        androidx.compose.ui.window.Dialog(
            onDismissRequest = { activeChapterToRead = null },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                CyberCornerBracketBox(
                    bracketSize = 20.dp,
                    bracketColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Surface(
                        color = Color(0xFF0F141A),
                        shape = CutCornerShape(10.dp),
                        border = androidx.compose.foundation.BorderStroke(1.2.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan.copy(alpha = 0.7f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(18.dp)) {
                            // Title
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_menu_codex, size = 18.dp, tint = io.eidos.zerolayer.ui.theme.ZzzElectricCyan)
                                Spacer(Modifier.width(8.dp))
                                Column {
                                    Text(
                                        chapter.title,
                                        color = Color.Yellow,
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        chapter.subtitle,
                                        color = EidosCyan,
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            Spacer(Modifier.height(12.dp))

                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .heightIn(max = 380.dp)
                                    .verticalScroll(rememberScrollState()),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                Surface(
                                    color = Color.Black.copy(alpha = 0.6f),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.4f)),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        text = chapter.epigraph,
                                        color = Color.Yellow,
                                        fontSize = 11.sp,
                                        fontStyle = FontStyle.Italic,
                                        modifier = Modifier.padding(10.dp),
                                        lineHeight = 15.sp
                                    )
                                }

                                Text(
                                    text = chapter.text,
                                    color = Color(0xFFE0E6ED),
                                    fontSize = 12.sp,
                                    lineHeight = 18.sp,
                                    fontFamily = FontFamily.SansSerif,
                                    textAlign = TextAlign.Justify
                                )

                                Spacer(modifier = Modifier.height(8.dp))
                                Surface(
                                    color = Color.Black.copy(alpha = 0.7f),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.6f)),
                                    shape = CutCornerShape(6.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Column(modifier = Modifier.padding(10.dp)) {
                                        Text(
                                            text = "ИТЕРАЦИЯ ФРАКЦИИ: ${player?.faction ?: "НЕЙТРАЛ"}",
                                            color = EidosCyan,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        val factionResonance = when (player?.faction) {
                                            "АРХИТЕКТОРЫ" -> "Ваш статус администратора дает вам полный доступ к секретным логам Архитекторов. EIDOS воспринимает вас не как вирус, а как спящий узел управления."
                                            "ТЕХНО" -> "Ваши экзо-чипы перехватывают зашифрованные пакеты этой главы, открывая скрытые командные строки и обходные пути в Бездне."
                                            "РАЗУМ" -> "Ваша ментальная матрица стабилизирует гармонический отклик, поглощая фантомные боли и защищая от угроз Скверны."
                                            "МАТЕРИЯ" -> "Датчики фиксируют микрочастицы озона и реальной пыли Земли в вашем потоке памяти. Вы ближе всех к физическому источнику."
                                            else -> "Вы - свободный Осколок на Свалке Данных. Ваши решения формируют новую ветку реальности без указаний Синдикатов."
                                        }
                                        Text(
                                            text = factionResonance,
                                            color = Color.LightGray,
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            lineHeight = 14.sp
                                        )
                                    }
                                }
                            }

                            Spacer(Modifier.height(14.dp))

                            Button(
                                onClick = { activeChapterToRead = null },
                                colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth().height(42.dp)
                            ) {
                                Text("ЗАКРЫТЬ КНИГУ", color = Color.Black, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }

        // --- SINGULARITY TERMINAL: Chapter VI finale (depth >= 1000m) ---
        val terminalReady = (player?.max_depth ?: 0) >= 1000
        if (STORY_CHAPTERS.any { it.hasSingularityTerminal && it.isUnlocked(player) }) {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF160810)),
                border = androidx.compose.foundation.BorderStroke(2.dp, Color(0xFFB388FF)),
                shape = CutCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_event_anomaly, size = 16.dp, tint = Color(0xFFB388FF))
                        Spacer(Modifier.width(6.dp))
                        Text(
                            "ТЕРМИНАЛ СИНГУЛЯРНОСТИ // ФИНАЛ",
                            color = Color(0xFFB388FF),
                            fontWeight = FontWeight.Black,
                            fontSize = 13.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Spacer(Modifier.height(6.dp))
                    Text(
                        if (terminalReady)
                            "Ты стоишь у ядра EIDOS-CORE. Терминал принимает директивы. Выбор необратим и определит форму твоего существования."
                        else
                            "Терминал заблокирован: требуется breach Ядра на 1000м глубины (достигни врат Хранителя).",
                        color = if (terminalReady) Color.White else Color.LightGray,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    if (terminalReady) {
                        Spacer(Modifier.height(10.dp))
                        listOf(
                            Triple("great_reset", "♾ ВЕЛИКИЙ СБРОС", "Обнулить уровень. Сохранить снаряжение. +10% наград за каждый цикл навсегда."),
                            Triple("ascension", "🌐 ЦИФРОВОЕ ВОЗНЕСЕНИЕ", "Влиться в OMNI-слой Архитекторов: +25 💎, +25000 BC."),
                            Triple("abyss", "🕳 СИНГУЛЯРНОСТЬ БЕЗДНЫ", "Отринуть обоих: +10 💎, +5 🗝, +15000 BC.")
                        ).forEach { (endingId, title, desc) ->
                            Button(
                                onClick = { onSingularityEnding(endingId) },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2A0A2A)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFB388FF)),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp)
                            ) {
                                Column(modifier = Modifier.fillMaxWidth()) {
                                    Text(title, color = Color(0xFFB388FF), fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                    Text(desc, color = Color.LightGray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun BestiaryBookSection(
    player: Player?,
    bestiaryList: List<BestiaryEntry>
) {
    var inspectedVillain by remember { mutableStateOf<GameVillainData?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_event_danger, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "БЕСТИАРИЙ СИСТЕМЫ // БАЗА УГРОЗ",
                        color = EidosRed,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Здесь собраны все аномалии, глитчи и вирусные формы жизни, обнаруженные в глубинах Эйдоса. Уничтожайте врагов, чтобы открывать их данные и получать ценные трофеи.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        GameData.VILLAINS.forEach { villain ->
            val entry = bestiaryList.find { it.enemy_id == villain.name }
            val killed = entry?.killed_count ?: 0
            val unlocked = killed > 0 || (entry?.encountered == true)

            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (unlocked) EidosNeon.copy(alpha = 0.5f) else Color.DarkGray
                ),
                shape = CutCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(enabled = unlocked) {
                        inspectedVillain = villain
                    }
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            if (unlocked) {
                                EidosImage(
                                    resName = villain.image,
                                    fallbackIcon = Icons.Default.Info,
                                    borderColor = EidosNeon,
                                    modifier = Modifier
                                        .size(44.dp)
                                        .clip(androidx.compose.foundation.shape.RoundedCornerShape(6.dp))
                                )
                            } else {
                                Box(
                                    modifier = Modifier
                                        .size(44.dp)
                                        .background(Color.Black.copy(alpha = 0.6f))
                                        .border(1.dp, Color.DarkGray, androidx.compose.foundation.shape.RoundedCornerShape(6.dp)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    ZzzIcon(R.drawable.ic_ui_locked, size = 18.dp, tint = Color.Gray)
                                }
                            }
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = if (unlocked) villain.name else "??? [НЕИЗВЕСТНО]",
                                    color = if (unlocked) Color.White else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "Тип: Аномалия • Уровень ${villain.level}",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Surface(
                            color = if (unlocked) EidosNeon.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (unlocked) EidosNeon else Color.DarkGray
                            ),
                            shape = CutCornerShape(4.dp)
                        ) {
                            Text(
                                text = "УБИТО: $killed",
                                color = if (unlocked) EidosNeon else Color.Gray,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    if (unlocked) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = villain.description,
                            color = Color.LightGray,
                            fontSize = 10.5.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 14.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("HP: ${villain.hp} | ATK: ${villain.atk} | DEF: ${villain.def}", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("XP: +${villain.xp} | Монет: +${villain.coin}", color = Color.Yellow, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                    } else {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Сектор заблокирован. Уничтожьте хотя бы одну особь этого типа в Бездне, чтобы расшифровать досье.",
                            color = Color.Gray,
                            fontSize = 9.sp,
                            fontStyle = FontStyle.Italic
                        )
                    }
                }
            }
        }
    }

    // Fullscreen Immersion Monster Dossier & High-Res Art Modal
    inspectedVillain?.let { villain ->
        val entry = bestiaryList.find { it.enemy_id == villain.name }
        val killed = entry?.killed_count ?: 0

        androidx.compose.ui.window.Dialog(
            onDismissRequest = { inspectedVillain = null },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.90f))
                    .clickable { inspectedVillain = null }
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth(0.95f)
                        .fillMaxHeight(0.88f)
                        .clickable(enabled = false) {}
                ) {
                    CyberCornerBracketBox(bracketSize = 20.dp, bracketColor = EidosRed) {
                        Surface(
                            color = Color(0xFF0A1017).copy(alpha = 0.98f),
                            shape = CutCornerShape(8.dp),
                            border = androidx.compose.foundation.BorderStroke(1.5.dp, EidosRed.copy(alpha = 0.7f)),
                            modifier = Modifier.fillMaxSize()
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .verticalScroll(rememberScrollState())
                                    .padding(16.dp)
                            ) {
                                // Top Header Bar
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_danger, size = 16.dp, tint = EidosRed)
                                        Spacer(Modifier.width(6.dp))
                                        Text(
                                            "ДОСЬЕ УГРОЗЫ // КЛАСС: АНОМАЛИЯ",
                                            color = EidosRed,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            letterSpacing = 1.sp
                                        )
                                    }
                                    IconButton(
                                        onClick = { inspectedVillain = null },
                                        modifier = Modifier.size(28.dp)
                                    ) {
                                        Text("✕", color = Color.Gray, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                                    }
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                // Large High-Res Monster Illustration
                                CyberCornerBracketBox(
                                    bracketSize = 14.dp,
                                    bracketColor = EidosRed.copy(alpha = 0.8f),
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .height(240.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .clip(CutCornerShape(6.dp))
                                            .background(Color(0xFF03060A))
                                            .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(6.dp)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        EidosImage(
                                            resName = villain.image,
                                            fallbackIcon = Icons.Default.Info,
                                            borderColor = Color.Transparent,
                                            borderWidth = 0.dp,
                                            contentScale = ContentScale.Crop,
                                            modifier = Modifier.fillMaxSize()
                                        )

                                        // Threat Level Stamp
                                        Box(
                                            modifier = Modifier
                                                .align(Alignment.TopEnd)
                                                .padding(8.dp)
                                                .clip(CutCornerShape(4.dp))
                                                .background(Color.Black.copy(alpha = 0.75f))
                                                .border(1.dp, EidosRed, CutCornerShape(4.dp))
                                                .padding(horizontal = 8.dp, vertical = 3.dp)
                                        ) {
                                            Text(
                                                "УРОВЕНЬ ${villain.level}",
                                                color = EidosRed,
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                    }
                                }

                                Spacer(modifier = Modifier.height(14.dp))

                                // Monster Title & Kill Count
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = villain.name,
                                            color = Color.White,
                                            fontSize = 17.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace,
                                            letterSpacing = 0.5.sp
                                        )
                                        Text(
                                            text = "ТИП: ВИРУСНЫЙ ГЛИТЧ // НУЛЕВОЙ СЛОЙ",
                                            color = EidosCyan,
                                            fontSize = 9.5.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                    Surface(
                                        color = EidosNeon.copy(alpha = 0.15f),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                        shape = CutCornerShape(4.dp)
                                    ) {
                                        Text(
                                            text = "УНИЧТОЖЕНО: $killed",
                                            color = EidosNeon,
                                            fontSize = 9.5.sp,
                                            fontWeight = FontWeight.Bold,
                                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(14.dp))

                                // Combat Telemetry Grid (HP, ATK, DEF)
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    // HP Card
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(CutCornerShape(4.dp))
                                            .background(Color(0xFF141922))
                                            .border(1.dp, EidosRed.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                            .padding(6.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Text("СИГНАЛ (HP)", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                            Text("${villain.hp}", color = EidosRed, fontSize = 13.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                        }
                                    }
                                    // ATK Card
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(CutCornerShape(4.dp))
                                            .background(Color(0xFF141922))
                                            .border(1.dp, EidosOrange.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                            .padding(6.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Text("АТАКА", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                            Text("${villain.atk}", color = EidosOrange, fontSize = 13.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                        }
                                    }
                                    // DEF Card
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(CutCornerShape(4.dp))
                                            .background(Color(0xFF141922))
                                            .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                            .padding(6.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Text("ЗАЩИТА", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                            Text("${villain.def}", color = EidosCyan, fontSize = 13.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                        }
                                    }
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                // Drops & Rewards Row
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(CutCornerShape(4.dp))
                                        .background(Color(0xFF0F1823))
                                        .border(1.dp, EidosGold.copy(alpha = 0.4f), CutCornerShape(4.dp))
                                        .padding(horizontal = 10.dp, vertical = 6.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_neural_exp, size = 12.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("НАГРАДА: +${villain.xp} EXP", color = Color.White, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                                    }
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_res_biocoin, size = 12.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("+${villain.coin} BC", color = EidosGold, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                    }
                                }

                                Spacer(modifier = Modifier.height(14.dp))

                                // Lore & Protocol Description
                                Text(
                                    "ПРОТОКОЛ ИДЕНТИФИКАЦИИ // АРХИВ:",
                                    color = EidosCyan,
                                    fontSize = 9.5.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = villain.description,
                                    color = Color.LightGray,
                                    fontSize = 11.5.sp,
                                    fontFamily = FontFamily.Monospace,
                                    lineHeight = 16.sp
                                )

                                Spacer(modifier = Modifier.height(16.dp))

                                io.eidos.zerolayer.ui.components.EidosButton(
                                    text = "ЗАКРЫТЬ ДОСЬЕ",
                                    onClick = { inspectedVillain = null },
                                    modifier = Modifier.fillMaxWidth().height(42.dp)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AchievementsSection(player: Player?) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_menu_codex, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "ДОСТИЖЕНИЯ СИСТЕМЫ // НАГРАДЫ ОПЕРАТОРА",
                        color = Color.Yellow,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Выполняйте боевые и исследовательские задачи в Бездне, чтобы получать постоянные баффы и очки славы.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        val achievements = listOf(
            Triple("Первый шаг в Бездну", "Спуститесь на глубину 100 метров", (player?.max_depth ?: 0) >= 100),
            Triple("Охотник на Глитчи", "Уничтожьте 10 противников", (player?.kills ?: 0) >= 10),
            Triple("Властелин Клинка", "Прокачайте оружие до 5 уровня", (player?.weapon_level ?: 1) >= 5),
            Triple("Кибер-Мастер", "Достигните 5 уровня Осколка", (player?.level ?: 1) >= 5),
            Triple("Глубинный Странник", "Достигните глубины 500 метров", (player?.max_depth ?: 0) >= 500),
            Triple("Легенда Арены", "Одержите 5 побед в Сетевых Дуэлях", (player?.wins_pvp ?: 0) >= 5)
        )

        achievements.forEach { (title, desc, unlocked) ->
            Card(
                colors = CardDefaults.cardColors(containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (unlocked) Color.Yellow.copy(alpha = 0.6f) else Color.DarkGray),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ZzzIcon(if (unlocked) R.drawable.ic_menu_codex else R.drawable.ic_ui_locked, size = 12.dp)
                            Spacer(Modifier.width(4.dp))
                            Text(
                                text = title,
                                color = if (unlocked) Color.White else Color.Gray,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = desc,
                            color = Color.LightGray,
                            fontSize = 9.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Surface(
                        color = if (unlocked) Color.Yellow.copy(alpha = 0.2f) else Color.DarkGray.copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, if (unlocked) Color.Yellow else Color.DarkGray),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            text = if (unlocked) "ВЫПОЛНЕНО" else "ЗАКРЫТО",
                            color = if (unlocked) Color.Yellow else Color.Gray,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun GuidesHubSection() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_menu_codex, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "СПРАВОЧНИК ОПЕРАТОРА // БАЗОВЫЕ ПРОТОКОЛЫ",
                        color = EidosCyan,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Изучите механики выживания в Бездне, управления инвентарем и сражений с ИИ-стражами.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        CodexCard(
            title = "1. ПОГРУЖЕНИЕ В БЕЗДНУ",
            subtitle = "Спуск по секторам памяти",
            description = "Каждый шаг вглубь Бездны (кнопка СЕКАТОР/ПОГРУЖЕНИЕ) уменьшает глубину на 10 метров и требует квантовой энергии. На вашем пути встречаются терминалы добычи ресурсов, боевые столкновения и аномалии Скверны.",
            tag = "ВЫЖИВАНИЕ",
            tagColor = EidosCyan
        )

        CodexCard(
            title = "2. МОДИФИКАЦИЯ ЭКИПИРОВКИ",
            subtitle = "Оружие, Щиты и Чипы",
            description = "В хабе вы можете улучшать оружие за монеты и кредиты данных. Улучшение повышает урон в секунду (DPS) и шанс критического удара. Устанавливайте чипы защиты для снижения урона от атак Глитчей.",
            tag = "КРАФТ",
            tagColor = Color.Yellow
        )

        CodexCard(
            title = "3. СЕТЕВАЯ АРЕНА (PvP)",
            subtitle = "Борьба за оперативную память",
            description = "На Арене вы сражаетесь с автоматизированными цифровыми фантомами других игроков. Победа приносит очки ранга, кредиты и долю их выделенной памяти.",
            tag = "СРАЖЕНИЯ",
            tagColor = EidosRed
        )

        CodexCard(
            title = "4. МИРОВЫЕ РЕЙДЫ НА БОССОВ",
            subtitle = "Эвтаназия EIDOS-CORE",
            description = "Коллективные рейды позволяют атаковать центральные процессоры Системы. Нанесите максимальный урон за отведенное время, чтобы получить редчайшие легендарные чертежи.",
            tag = "РЕЙДЫ",
            tagColor = EidosNeon
        )
    }
}

@Composable
fun ChroniclesLogsSection(logs: List<GameLog>) {
    val dateFormat = remember { SimpleDateFormat("HH:mm:ss", Locale.getDefault()) }
    var filterType by remember { mutableStateOf("all") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_menu_codex, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "СИСТЕМНЫЕ ЛОГИ // ТЕРМИНАЛ СОБЫТИЙ",
                        color = EidosNeon,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Хронологическая лента всех событий, битв, находок и предупреждений ядра.",
                    color = Color.LightGray,
                    fontSize = 10.sp
                )
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            listOf("all" to "ВСЕ", "combat" to "БОЙ", "loot" to "ЛУТ", "info" to "ИНФО").forEach { (type, label) ->
                val selected = filterType == type
                FilterChip(
                    selected = selected,
                    onClick = { filterType = type },
                    label = { Text(label, fontSize = 10.sp, fontFamily = FontFamily.Monospace) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = EidosNeon.copy(alpha = 0.3f),
                        selectedLabelColor = EidosNeon,
                        containerColor = Color.Black,
                        labelColor = Color.Gray
                    )
                )
            }
        }

        val filteredLogs = if (filterType == "all") logs else logs.filter { it.type == filterType }

        if (filteredLogs.isEmpty()) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    ZzzIcon(R.drawable.ic_event_unknown, size = 32.dp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Записи в журнале отсутствуют или фильтр скрывает все логи.",
                        color = Color.DarkGray,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(filteredLogs, key = { it.id }) { logItem ->
                    val badgeColor = when (logItem.type) {
                        "combat" -> EidosRed
                        "loot" -> Color.Yellow
                        "info" -> EidosCyan
                        else -> EidosNeon
                    }

                    Surface(
                        color = Color.Black.copy(alpha = 0.7f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, badgeColor.copy(alpha = 0.35f)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "[${dateFormat.format(Date(logItem.timestamp))}]",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = logItem.message,
                                color = Color.White,
                                fontSize = 10.5.sp,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 14.sp,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CodexCard(
    title: String,
    subtitle: String,
    description: String,
    simpleExplanation: String? = null,
    loreContext: String? = null,
    tag: String,
    tagColor: Color
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = EidosGlass),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, tagColor.copy(alpha = 0.35f), CutCornerShape(6.dp)),
        shape = CutCornerShape(6.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    title,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.weight(1f)
                )
                Surface(
                    color = tagColor.copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, tagColor),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text(
                        tag,
                        color = tagColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                subtitle,
                color = tagColor,
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                description,
                color = Color.LightGray,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
fun ArchitectAudioLogsSection(player: Player?) {
    var selectedLog by remember { mutableStateOf<ArchitectLogData?>(null) }
    val playerLevel = player?.level ?: 1

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Magenta.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_menu_codex, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "АУДИО-ЛОГИ АРХИТЕКТОРОВ // РЕЛИКВИИ ПРОШЛОГО",
                        color = Color.Magenta,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Зашифрованные квантовые записи голосов создателей Эйдоса и Теневого Брокера. Прослушивание этих логов позволяет глубже понять истинную причину Великого Глитча.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        ARCHITECT_LOGS.forEach { log ->
            val unlocked = playerLevel >= log.unlockLevel
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (unlocked) Color.Magenta.copy(alpha = 0.5f) else Color.DarkGray
                ),
                shape = CutCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(enabled = unlocked) {
                        selectedLog = log
                    }
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            if (unlocked) {
                                ZzzIcon(
                                    iconRes = R.drawable.ic_action_scan,
                                    size = 22.dp,
                                    tint = Color.Magenta
                                )
                            } else {
                                Image(
                                    painter = painterResource(id = R.drawable.ic_lock_cyber),
                                    contentDescription = "Заблокировано",
                                    modifier = Modifier.size(24.dp),
                                    contentScale = ContentScale.Fit
                                )
                            }
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = if (unlocked) log.title else "??? [ЗАКРИПТОВАНО]",
                                    color = if (unlocked) Color.White else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "Автор: ${if (unlocked) log.author else "Неизвестен"} • ${log.frequency}",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Surface(
                            color = if (unlocked) Color.Magenta.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (unlocked) Color.Magenta else Color.DarkGray
                            ),
                            shape = CutCornerShape(4.dp)
                        ) {
                            Text(
                                text = if (unlocked) "ДОСТУПНО" else "ТРЕБУЕТСЯ УР. ${log.unlockLevel}",
                                color = if (unlocked) Color.Magenta else Color.Gray,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    if (unlocked) {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Нажмите, чтобы расшифровать и воспроизвести аудио-транскрипт.",
                            color = Color.LightGray,
                            fontSize = 9.5.sp,
                            fontStyle = FontStyle.Italic
                        )
                    }
                }
            }
        }
    }

    selectedLog?.let { log ->
        AlertDialog(
            onDismissRequest = { selectedLog = null },
            containerColor = Color(0xFF140F1A),
            shape = CutCornerShape(12.dp),
            title = {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(R.drawable.ic_action_scan, size = 16.dp, tint = Color.Magenta)
                        Spacer(Modifier.width(6.dp))
                        Text(
                            log.title,
                            color = Color.Magenta,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Text(
                        "${log.author} • ${log.frequency}",
                        color = EidosCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 300.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = log.transcript,
                        color = Color(0xFFE0E6ED),
                        fontSize = 11.5.sp,
                        lineHeight = 17.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Justify
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { selectedLog = null },
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Magenta),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ЗАКРЫТЬ КАНАЛ", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            }
        )
    }
}
