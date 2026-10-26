package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import io.eidos.zerolayer.R
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.theme.EidosNeon

import io.eidos.zerolayer.data.RaidSession

import io.eidos.zerolayer.data.GameLog
import io.eidos.zerolayer.ui.components.TerminalLog
import io.eidos.zerolayer.ui.utils.ghostTyping

import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.CyberCard
import io.eidos.zerolayer.ui.components.RadarScanView
import io.eidos.zerolayer.ui.components.HackingMinigameDialog
import io.eidos.zerolayer.ui.components.cyberHudBorder
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.GameRepository.ItemMetadata
import io.eidos.zerolayer.ui.components.cyberClickable
import io.eidos.zerolayer.ui.theme.EidosGold
import io.eidos.zerolayer.ui.theme.EidosPurple
import io.eidos.zerolayer.ui.theme.EidosOrange
import io.eidos.zerolayer.ui.components.AnimatedCyberProgressBar
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.CyberParticleOverlay
import io.eidos.zerolayer.ui.components.ParticlePreset
import io.eidos.zerolayer.ui.utils.AbyssSeedRng
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.text.style.TextOverflow

import androidx.compose.ui.platform.LocalContext
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RaidScreen(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    logs: List<GameLog>,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent? = null,
    inventory: List<InventoryItem> = emptyList(),
    allItemsMetadata: List<ItemMetadata> = emptyList(),
    overdriveCharge: Int = 0,
    overchargeTier: Int = 0,
    combatEventFlow: kotlinx.coroutines.flow.SharedFlow<io.eidos.zerolayer.data.CombatVisualEvent>? = null,
    onNextStep: () -> Unit,
    onAnomalyChoice: (String) -> Unit,
    onOpenInventory: () -> Unit,
    onExitRaid: () -> Unit,
    onBack: () -> Unit,
    onStartRaid: () -> Unit = {},
    onScanSector: () -> Unit = {},
    onUseAbility: () -> Unit = {},
    onTriggerOverdrive: () -> Unit = {},
    onBoostOvercharge: () -> Unit = {},
    onUseConsumable: (InventoryItem) -> Unit = {},
    onAcceptMaxwellContract: (String) -> Unit = {},
    onBetDemonHp: () -> Unit = {},
    onBetDemonBuffer: () -> Unit = {},
    onIgnoreDemon: () -> Unit = {},
    onResolveHardGlitch: (chosenIndex: Int, correctIndex: Int) -> Unit = { _, _ -> }
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    var showMinigame by remember { mutableStateOf(false) }
    var minigameResultMsg by remember { mutableStateOf<String?>(null) }
    var isEvacuatingHold by remember { mutableStateOf(false) }
    var evacTurnsLeft by remember { mutableIntStateOf(2) }
    var showEvacSummary by remember { mutableStateOf(false) }
    var showBufferModal by remember { mutableStateOf(false) }

    // Dopamine Loot Modal State
    var showDopamineModal by remember { mutableStateOf(false) }
    var dopamineCoins by remember { mutableLongStateOf(0L) }
    var dopamineXp by remember { mutableLongStateOf(0L) }
    var dopamineItems by remember { mutableStateOf<List<String>>(emptyList()) }

    var prevCoins by remember { mutableLongStateOf(session?.buffer_coins ?: 0L) }
    var prevXp by remember { mutableLongStateOf(session?.buffer_xp ?: 0L) }
    var prevItemsStr by remember { mutableStateOf(session?.buffer_items ?: "") }

    // Visual Combat Juice: Card Shake, Screen Flash, Floating Damage
    val cardShakeX = remember { androidx.compose.animation.core.Animatable(0f) }
    val screenFlashAlpha = remember { androidx.compose.animation.core.Animatable(0f) }
    var floatingDamageText by remember { mutableStateOf<String?>(null) }
    var floatingDamageColor by remember { mutableStateOf(EidosCyan) }
    var floatingDamageScale by remember { mutableFloatStateOf(1f) }

    LaunchedEffect(combatEventFlow) {
        combatEventFlow?.collect { event ->
            if (event.isPlayerHit) {
                screenFlashAlpha.snapTo(0.6f)
                screenFlashAlpha.animateTo(0f, tween(300))
                haptics.glitchPulse()
                floatingDamageText = "-${event.incomingDamage} HP"
                floatingDamageColor = EidosRed
                floatingDamageScale = 1.2f
            } else if (event.isDodge) {
                floatingDamageText = "DODGE //"
                floatingDamageColor = EidosCyan
                floatingDamageScale = 1.0f
            } else {
                cardShakeX.animateTo(12f, spring(stiffness = Spring.StiffnessHigh))
                cardShakeX.animateTo(-12f, spring(stiffness = Spring.StiffnessHigh))
                cardShakeX.animateTo(0f, spring(stiffness = Spring.StiffnessHigh))

                if (event.isOverdrive) {
                    screenFlashAlpha.snapTo(0.9f)
                    screenFlashAlpha.animateTo(0f, tween(400))
                    haptics.criticalHit()
                    audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                    floatingDamageText = "OVERDRIVE! // -${event.damage}"
                    floatingDamageColor = EidosPurple
                    floatingDamageScale = 1.8f
                } else if (event.isCrit) {
                    screenFlashAlpha.snapTo(0.7f)
                    screenFlashAlpha.animateTo(0f, tween(300))
                    haptics.criticalHit()
                    audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                    floatingDamageText = "CRIT! // -${event.damage}"
                    floatingDamageColor = EidosGold
                    floatingDamageScale = 1.5f
                } else {
                    floatingDamageText = "-${event.damage}"
                    floatingDamageColor = EidosCyan
                    floatingDamageScale = 1.1f
                }
            }
        }
    }

    // Sound / Haptic trigger when encountering an Anomaly
    LaunchedEffect(session?.current_anomaly_id) {
        if (session?.current_anomaly_id != null) {
            haptics.glitchPulse()
            audio.playSound(EidosAudioManager.SoundType.GLITCH_FOUND)
        }
    }

    // Monitor session buffer changes for Dopamine Loot Modal
    LaunchedEffect(session?.buffer_coins, session?.buffer_xp, session?.buffer_items) {
        val currCoins = session?.buffer_coins ?: 0L
        val currXp = session?.buffer_xp ?: 0L
        val currItemsStr = session?.buffer_items ?: ""

        val diffCoins = currCoins - prevCoins
        val diffXp = currXp - prevXp

        val oldList = if (prevItemsStr.isBlank()) emptyList() else prevItemsStr.split(",")
        val newList = if (currItemsStr.isBlank()) emptyList() else currItemsStr.split(",")
        val diffItems = if (newList.size > oldList.size) newList.subList(oldList.size, newList.size) else emptyList()

        if (diffCoins > 0 || diffXp > 0 || diffItems.isNotEmpty()) {
            dopamineCoins = diffCoins
            dopamineXp = diffXp
            dopamineItems = diffItems
            showDopamineModal = true
            haptics.criticalHit()
            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        }

        prevCoins = currCoins
        prevXp = currXp
        prevItemsStr = currItemsStr
    }

    val currentSeed = remember { AbyssSeedRng.generateRandomSeed() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("НУЛЕВОЙ СЛОЙ // БЕЗДНА", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        Text("СИД // $currentSeed", color = Color.Gray, fontSize = 9.sp, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosRed)
                    }
                },
                actions = {
                    if (session != null && session.current_enemy_id == null && session.current_anomaly_id == null && !isEvacuatingHold) {
                        io.eidos.zerolayer.ui.components.ZzzDangerButton(
                            text = "ЭВАКУАЦИЯ",
                            onClick = {
                                haptics.evacuationWarning()
                                audio.playSound(EidosAudioManager.SoundType.EVAC_WARNING)
                                isEvacuatingHold = true
                            },
                            height = 36.dp
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Black
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize()) {
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_null_layer),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = Alignment.Center
            )
            CyberGridOverlay(modifier = Modifier.fillMaxSize())
            CyberParticleOverlay(
                preset = if (isEvacuatingHold) ParticlePreset.EVACUATION_VORTEX else ParticlePreset.ABYSS_DUST
            )

            if (session == null) {
                // Gateway Ready State: Enter Abyss
                Column(
                    modifier = Modifier
                        .padding(innerPadding)
                        .fillMaxSize()
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    CyberCard(
                        modifier = Modifier.fillMaxWidth(),
                        borderColor = EidosRed,
                        headerText = "⚡ ШЛЮЗ НУЛЕВОГО СЛОЯ // ГОТОВНОСТЬ"
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "НЕЙРОННЫЙ КАНАЛ СТАБИЛИЗИРОВАН",
                                color = EidosRed,
                                fontWeight = FontWeight.Black,
                                fontSize = 14.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            Text(
                                text = "Вы находитесь на пороге Нулевого Слоя. Здесь реальность искажена, а программы-фантомы и вирусы охраняют квантовые данные. Подготовьте снаряжение и начните спуск.",
                                color = Color.LightGray,
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center,
                                lineHeight = 16.sp
                            )
                            Spacer(modifier = Modifier.height(16.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceEvenly
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("ЗДОРОВЬЕ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                    Text("${player?.hp ?: 100}/${player?.max_hp ?: 100}", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("АТАКА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                    Text("${player?.attack ?: 10}", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("ЗАЩИТА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                    Text("${player?.defense ?: 5}", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                            }

                            Spacer(modifier = Modifier.height(20.dp))

                            Button(
                                onClick = {
                                    haptics.criticalHit()
                                    audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                                    onStartRaid()
                                },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(54.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2A0808)),
                                border = androidx.compose.foundation.BorderStroke(2.dp, EidosRed),
                                shape = androidx.compose.foundation.shape.CutCornerShape(8.dp)
                            ) {
                                Text("🌐 НАЧАТЬ ПОГРУЖЕНИЕ В БЕЗДНУ", color = EidosRed, fontWeight = FontWeight.Black, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }
                }
            } else {
                Column(
                    modifier = Modifier
                        .padding(innerPadding)
                        .fillMaxSize()
                        .padding(16.dp)
                ) {
                    // EVA-09 Assistant Guidance Banner
                    io.eidos.zerolayer.ui.components.ZzzHazardBanner(
                        title = "🌐 ГОЛОС EIDOS // СЕКТОР БЕЗДНЫ",
                        message = "Обнаружен шлюз в Бездну! Нажимай «СДЕЛАЙТЕ ШАГ В БЕЗДНУ» для сканирования секторов, поиска контейнеров и уничтожения вирусов. Если твой Сигнал критически слаб — немедленно задействуй «ЭВАКУАЦИЮ», чтобы сохранить весь добытый код и лут!",
                        borderColor = EidosRed,
                        icon = "🚨",
                        modifier = Modifier.padding(bottom = 8.dp)
                    )

                    // HUD
                    RaidHUD(
                        session = session,
                        player = player,
                        onOpenBuffer = { showBufferModal = true }
                    )

                    Spacer(modifier = Modifier.height(10.dp))

                    if (isEvacuatingHold) {
                        // Unstable Evacuation View
                        CyberCard(
                            modifier = Modifier.weight(1f).fillMaxWidth(),
                            borderColor = EidosRed,
                            headerText = "⚠ НЕСТАБИЛЬНАЯ ЭВАКУАЦИЯ // ТЕЛЕПОРТ"
                        ) {
                            Column(
                                modifier = Modifier.fillMaxSize(),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center
                            ) {
                                Text(
                                    "УДЕРЖАНИЕ СИГНАЛА: ВОЛНА ПЕРЕХВАТА",
                                    color = EidosRed,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "Осталось ходов до эвакуации: $evacTurnsLeft",
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Box(modifier = Modifier.size(140.dp)) {
                                    RadarScanView(color = EidosRed)
                                }
                                Spacer(modifier = Modifier.height(12.dp))
                                io.eidos.zerolayer.ui.components.ZzzDangerButton(
                                    text = if (evacTurnsLeft > 1) "ОТБИТЬ ВОЛНУ ПЕРЕХВАТА ($evacTurnsLeft)" else "ОТКРЫТЬ ШЛЮЗ ЭВАКУАЦИИ ➔ СВОДКА ЛУТА",
                                    onClick = {
                                        if (evacTurnsLeft > 1) {
                                            evacTurnsLeft--
                                        } else {
                                            isEvacuatingHold = false
                                            showEvacSummary = true
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    height = 52.dp
                                )
                            }
                        }
                    } else {
                        // Event Display
                        Box(modifier = Modifier.weight(1f)) {
                            EventCard(
                                session = session,
                                player = player,
                                anomalyData = anomalyData,
                                logs = logs,
                                onTriggerHack = { showMinigame = true }
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Logs
                    TerminalLog(logs)

                    Spacer(modifier = Modifier.height(10.dp))

                    // Controls
                    if (!isEvacuatingHold) {
                        RaidControls(
                            session = session,
                            anomalyData = anomalyData,
                            onNextStep = onNextStep,
                            onAnomalyChoice = onAnomalyChoice,
                            onOpenInventory = onOpenInventory,
                            onOpenBuffer = { showBufferModal = true },
                            onScanSector = onScanSector,
                            onUseAbility = onUseAbility
                        )
                    }
                }
            }
        }
    }

    if (showBufferModal) {
        RaidBufferModal(
            session = session,
            player = player,
            inventory = inventory,
            allItemsMetadata = allItemsMetadata,
            onUseConsumable = onUseConsumable,
            onDismiss = { showBufferModal = false },
            onOpenFullInventory = {
                showBufferModal = false
                onOpenInventory()
            }
        )
    }

    if (showMinigame) {
        HackingMinigameDialog(
            depth = session?.depth ?: 1,
            onDismiss = { showMinigame = false },
            onSuccess = {
                minigameResultMsg = "ВЗЛОМ УСПЕШЕН: Извлечены дополнительные байты данных (+200 BC, +150 XP)!"
            },
            onFailure = {
                minigameResultMsg = "ОШИБКА ВЗЛОМА: Получен импульсный разряд (-15 Сигнала)!"
            }
        )
    }

    if (showDopamineModal) {
        DopamineLootDialog(
            coinsGained = dopamineCoins,
            xpGained = dopamineXp,
            itemsGained = dopamineItems,
            onDismiss = { showDopamineModal = false }
        )
    }

    if (showEvacSummary) {
        EvacuationSummaryDialog(
            session = session,
            onConfirmExit = {
                showEvacSummary = false
                onExitRaid()
            }
        )
    }

    // Maxwell's Demon Encounter Modal (Isolated strictly to RaidScreen at depth 50+)
    if (session?.next_event_type == "maxwells_demon") {
        io.eidos.zerolayer.ui.components.MaxwellDemonModal(
            currentHp = player?.hp ?: 100,
            bufferCoins = session.buffer_coins,
            playerCoins = player?.biocoin ?: 0L,
            playerXp = player?.xp ?: 0L,
            onAcceptContract = onAcceptMaxwellContract,
            onIgnore = onIgnoreDemon
        )
    }

    // Hard Glitch Neural Stabilization Modal
    var activeHardGlitchQuestion by remember { mutableStateOf<io.eidos.zerolayer.domain.anomaly.AnomalyEngine.HardGlitchQuestion?>(null) }
    val isHardGlitchDue = remember(player?.glitchEncounterCounter, player?.lastHardGlitchTimestamp) {
        player != null && io.eidos.zerolayer.domain.anomaly.AnomalyEngine.isHardGlitchReady(player, false)
    }

    LaunchedEffect(isHardGlitchDue) {
        if (isHardGlitchDue && activeHardGlitchQuestion == null) {
            activeHardGlitchQuestion = io.eidos.zerolayer.domain.anomaly.AnomalyEngine.getRandomHardGlitchQuestion()
        }
    }

    activeHardGlitchQuestion?.let { question ->
        io.eidos.zerolayer.ui.components.HardGlitchModal(
            question = question,
            onAnswerChosen = { chosenIndex ->
                onResolveHardGlitch(chosenIndex, question.correctIndex)
                activeHardGlitchQuestion = null
            },
            onTimeout = {
                onResolveHardGlitch(-1, question.correctIndex)
                activeHardGlitchQuestion = null
            }
        )
    }
}

@Composable
fun RaidHUD(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player? = null,
    hasOblivionChip: Boolean = false,
    overchargeTier: Int = 0,
    onOpenBuffer: () -> Unit = {}
) {
    val signal = session?.signal ?: 94
    val depth = session?.depth ?: 1480
    val overdriveTurns = session?.overdrive_turns ?: 0
    val comboCount = session?.combo_count ?: 0
    val mutator = session?.active_mutator ?: ""
    val lootCount = session?.buffer_items?.split(",")?.filter { it.isNotBlank() }?.size ?: 0

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // OVERCHARGE PROTOCOL BANNER
        if (overchargeTier > 0) {
            val lootMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(overchargeTier)
            Surface(
                color = EidosOrange.copy(alpha = 0.25f),
                border = androidx.compose.foundation.BorderStroke(1.5.dp, EidosOrange),
                modifier = Modifier.fillMaxWidth(),
                shape = androidx.compose.foundation.shape.RoundedCornerShape(6.dp)
            ) {
                Row(
                    modifier = Modifier.padding(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        "🔥 OVERCHARGE x$lootMult (+${overchargeTier * 50}% ЛУТ / +${overchargeTier * 20}% АТАКА ВРАГОВ)",
                        color = EidosOrange,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
        // Active Anomaly Buff Pill
        val nowSec = System.currentTimeMillis() / 1000L
        if (player != null && player.anomalyBuffType != null && nowSec < player.anomalyBuffExpiry) {
            Surface(
                color = Color(0xFF00FFCC).copy(alpha = 0.15f),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF00FFCC)),
                modifier = Modifier.fillMaxWidth(),
                shape = CutCornerShape(4.dp)
            ) {
                Row(
                    modifier = Modifier.padding(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    val buffName = when (player.anomalyBuffType) {
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_GLITCH_BERSERK -> "⚡ [ГЛИТЧ-БЕРСЕРК: +25% ATK]"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_OVERLOAD -> "💰 [ПЕРЕГРУЗКА ЯДРА: +50% BC]"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_STEALTH_NIGHT -> "🌙 [НОЧНАЯ СКРЫТНОСТЬ: 30% ОБХОД]"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_VISUAL_DISTORTION -> "🌀 [ИСКАЖЕНИЕ РЕАЛЬНОСТИ]"
                        else -> "⚡ [АКТИВНАЯ АНОМАЛИЯ]"
                    }
                    val timeLeftSec = (player.anomalyBuffExpiry - nowSec).coerceAtLeast(0)
                    Text(
                        "$buffName (${timeLeftSec}с)",
                        color = Color(0xFF00FFCC),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
        // OVERDRIVE BANNER
        if (overdriveTurns > 0) {
            Surface(
                color = Color.Yellow.copy(alpha = 0.2f),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow),
                modifier = Modifier.fillMaxWidth(),
                shape = androidx.compose.foundation.shape.RoundedCornerShape(6.dp)
            ) {
                Row(
                    modifier = Modifier.padding(6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        "⚡ HYPER-SYNC OVERDRIVE: ОСТАЛОСЬ $overdriveTurns ХОДА!",
                        color = Color.Yellow,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }

        // 3 Key Info Cards Bar (Matching Cyber HUD)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Card 1: ГЛУБИНА (М)
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .background(Color(0xFF09161B).copy(alpha = 0.95f))
                    .border(1.dp, EidosCyan.copy(alpha = 0.5f), androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .cyberHudBorder(color = EidosCyan, cornerLength = 8.dp, strokeWidth = 1.dp)
                    .padding(8.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_stat_depth),
                        contentDescription = "Глубина",
                        modifier = Modifier.size(24.dp),
                        contentScale = ContentScale.Fit
                    )
                    Column {
                        Text("ГЛУБИНА", color = Color(0xFF78909C), fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                        Text("${depth} м", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                    }
                }
            }

            // Card 2: СИГНАЛ (%)
            Box(
                modifier = Modifier
                    .weight(1.2f)
                    .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .background(Color(0xFF1B090E).copy(alpha = 0.95f))
                    .border(1.dp, EidosRed.copy(alpha = 0.7f), androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .cyberHudBorder(color = EidosRed, cornerLength = 8.dp, strokeWidth = 1.dp)
                    .padding(8.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_stat_hp),
                        contentDescription = "Сигнал HP",
                        modifier = Modifier.size(24.dp),
                        contentScale = ContentScale.Fit
                    )
                    Column {
                        Text("СИГНАЛ", color = Color(0xFFB0BEC5), fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                        Text(if (hasOblivionChip) "???%" else "${signal}%", color = EidosRed, fontSize = 12.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                    }
                }
            }

            // Card 3: БУФЕР ЛУТА (Clickable to open buffer modal)
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .background(Color(0xFF1B1309).copy(alpha = 0.95f))
                    .border(1.dp, Color(0xFFFF9800).copy(alpha = 0.6f), androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                    .cyberHudBorder(color = Color(0xFFFF9800), cornerLength = 8.dp, strokeWidth = 1.dp)
                    .cyberClickable { onOpenBuffer() }
                    .padding(8.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_biocoin),
                        contentDescription = "Буфер Лута",
                        modifier = Modifier.size(22.dp),
                        contentScale = ContentScale.Fit
                    )
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("БУФЕР", color = Color(0xFF78909C), fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.width(2.dp))
                            Text("🔍", fontSize = 7.sp)
                        }
                        Text("$lootCount/100", color = Color(0xFFFF9800), fontSize = 12.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }

        // Signal Progress Bar
        AnimatedCyberProgressBar(
            progress = if (hasOblivionChip) 1f else signal / 100f,
            color = if (overdriveTurns > 0) Color.Yellow else EidosRed,
            label = "СТАБИЛЬНОСТЬ ПОДКЛЮЧЕНИЯ СИГНАЛА",
            valueText = if (hasOblivionChip) "???%" else "${signal}%",
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
fun EventCard(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent?,
    logs: List<GameLog>,
    onTriggerHack: () -> Unit = {}
) {
    val eventType = session?.next_event_type ?: "INITIALIZING"
    val enemyId = session?.current_enemy_id
    val enemyHp = session?.current_enemy_hp ?: 0
    val villain = io.eidos.zerolayer.data.GameData.VILLAINS.find { it.name == enemyId }

    val isAnomaly = session?.current_anomaly_id != null

    val title = when {
        enemyId != null -> "⚠ ${villain?.name?.uppercase() ?: "ВРАГ"}"
        isAnomaly -> "🌀 ОБНАРУЖЕНА АНОМАЛИЯ"
        eventType == "loot" -> "📦 ОБНАРУЖЕН ТАЙНИК"
        else -> "📡 СКАНИРОВАНИЕ СЛОЯ..."
    }

    val description = when {
        enemyId != null -> villain?.description ?: "Вражеская единица обнаружена."
        isAnomaly -> anomalyData?.text ?: "Сработал протокол безопасности. Целостность сигнала под угрозой."
        eventType == "loot" -> "Зашифрованный контейнер данных излучает слабый сигнал."
        else -> "Нейро-связь стабильна. Продолжение спуска."
    }

    // Glitch animation for anomalies
    val infiniteTransition = rememberInfiniteTransition(label = "glitch")
    val glitchOffset by infiniteTransition.animateFloat(
        initialValue = -2f,
        targetValue = 2f,
        animationSpec = infiniteRepeatable(
            animation = tween(100, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "offset"
    )

    val borderColor = if (enemyId != null) EidosRed else if (isAnomaly) Color.Yellow else EidosCyan

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .offset(x = if (isAnomaly) glitchOffset.dp else 0.dp)
            .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
            .background(Color(0xFF070B10).copy(alpha = 0.95f))
            .border(1.dp, borderColor.copy(alpha = 0.5f), androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
            .cyberHudBorder(color = borderColor, cornerLength = 10.dp, strokeWidth = 1.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                title,
                color = borderColor,
                fontSize = 15.sp,
                fontWeight = FontWeight.Black,
                textAlign = TextAlign.Center,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp
            )

            if (enemyId != null && villain != null) {
                Spacer(modifier = Modifier.height(10.dp))

                // Enemy Visual Card
                val enemyImageName = villain.image.takeIf { it.isNotBlank() } ?: remember(villain.name) {
                    "villain_" + villain.name
                        .replace("🦠", "").replace("👻", "").replace("🚁", "").replace("💣", "")
                        .replace("⛏", "").replace("🐉", "").replace("❌", "").replace("🗡", "")
                        .replace("🧠", "").replace("⬛", "").replace("💀", "").replace("🏗", "")
                        .replace("🍽", "").replace("🛡", "").replace("⚛️", "").replace("🤖", "")
                        .replace("🌌", "").replace("🌀", "").trim()
                }

                EidosImage(
                    resName = enemyImageName,
                    fallbackIcon = Icons.Default.Warning,
                    borderColor = EidosRed,
                    modifier = Modifier
                        .size(96.dp)
                        .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Enemy Stats Chips
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
                            .background(Color(0xFF1F080C))
                            .border(1.dp, EidosRed.copy(alpha = 0.4f), androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
                            .padding(vertical = 4.dp, horizontal = 6.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ЦЕЛЬ", color = EidosRed, fontSize = 8.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                            Text("ATK: ${villain.atk} | DEF: ${villain.def}", color = Color.White, fontSize = 9.5.sp, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
                            .background(Color(0xFF09161B))
                            .border(1.dp, EidosCyan.copy(alpha = 0.4f), androidx.compose.foundation.shape.RoundedCornerShape(4.dp))
                            .padding(vertical = 4.dp, horizontal = 6.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ОПЕРАТОР", color = EidosCyan, fontSize = 8.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                            Text("ATK: ${player?.attack ?: 0} | DEF: ${player?.defense ?: 0}", color = Color.White, fontSize = 9.5.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                AnimatedCyberProgressBar(
                    progress = (enemyHp.toFloat() / villain.hp.toFloat()).coerceIn(0f, 1f),
                    color = EidosRed,
                    label = "СИГНАЛ ВРАГА",
                    valueText = "$enemyHp / ${villain.hp}",
                    modifier = Modifier.fillMaxWidth()
                )

                // Combat Feedback Banner
                val combatLogs = logs.filter { it.type == "combat" || it.type == "error" }.takeLast(2)
                if (combatLogs.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(androidx.compose.foundation.shape.RoundedCornerShape(6.dp))
                            .background(Color.Black.copy(alpha = 0.6f))
                            .border(1.dp, EidosRed.copy(alpha = 0.3f), androidx.compose.foundation.shape.RoundedCornerShape(6.dp))
                            .padding(8.dp)
                    ) {
                        Column {
                            combatLogs.forEach { log ->
                                Text(
                                    log.message,
                                    color = if (log.type == "error") EidosRed else EidosNeon,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace,
                                    lineHeight = 12.sp
                                )
                            }
                        }
                    }
                }
            } else if (eventType == "loot") {
                Spacer(modifier = Modifier.height(12.dp))
                EidosImage(
                    resName = "raid_chest",
                    fallbackIcon = Icons.Default.Warning,
                    borderColor = EidosNeon,
                    modifier = Modifier
                        .size(80.dp)
                        .clip(androidx.compose.foundation.shape.RoundedCornerShape(8.dp))
                )
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    "ОБНАРУЖЕНЫ ЦИФРОВЫЕ ОСТАТКИ",
                    color = EidosNeon,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )

                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = onTriggerHack,
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(6.dp)
                ) {
                    Text("⚡ ВЗЛОМАТЬ ТЕРМИНАЛ [ПРОТОКОЛ ПЕРЕХВАТА]", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }


                // Show items if available in buffer (for visual interest)
                val items = session?.buffer_items?.split(",")?.filter { it.isNotBlank() } ?: emptyList()
                if (items.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        items.take(5).forEach { itemCode ->
                            EidosImage(
                                resName = itemCode,
                                fallbackIcon = Icons.Default.Info,
                                borderColor = EidosNeon,
                                modifier = Modifier.size(36.dp)
                            )
                        }
                    }
                }
            } else if (isAnomaly) {
                Spacer(modifier = Modifier.height(16.dp))
                EidosImage(
                    resName = "raid_anomaly",
                    fallbackIcon = Icons.Default.Info,
                    borderColor = Color.Yellow,
                    modifier = Modifier.size(90.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            val displayedDescription = ghostTyping(description, speed = if (enemyId != null) 5L else 15L)
            Text(
                displayedDescription,
                color = Color.White.copy(alpha = 0.7f),
                fontSize = 13.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.heightIn(min = 60.dp),
                fontFamily = FontFamily.Monospace,
                lineHeight = 18.sp
            )
        }
    }
}

@Composable
fun RaidControls(
    session: RaidSession?,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent?,
    overdriveCharge: Int = 0,
    overchargeTier: Int = 0,
    onNextStep: () -> Unit,
    onAnomalyChoice: (String) -> Unit,
    onOpenInventory: () -> Unit,
    onOpenBuffer: () -> Unit = {},
    onScanSector: () -> Unit = {},
    onUseAbility: () -> Unit = {},
    onTriggerOverdrive: () -> Unit = {},
    onBoostOvercharge: () -> Unit = {}
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    val isCombat = session?.current_enemy_id != null
    val isAnomaly = session?.current_anomaly_id != null
    val primaryButtonText = if (isCombat) "АТАКА [НЕЙРО_ИМПУЛЬС]" else if (isAnomaly) "ОЖИДАНИЕ ВВОДА..." else "СЛЕДУЮЩИЙ ШАГ [ЭНЕРГИЯ]"

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // OVERDRIVE COMBAT ULTIMATE BUTTON
        if (isCombat) {
            val isOverdriveReady = overdriveCharge >= 100
            AnimatedCyberProgressBar(
                progress = (overdriveCharge / 100f).coerceIn(0f, 1f),
                color = if (isOverdriveReady) EidosPurple else EidosCyan,
                label = if (isOverdriveReady) "⚡ ЯДРО ЗАРЯЖЕНО НА 100%" else "ЗАРЯД ОВЕРДРАЙВА",
                valueText = "$overdriveCharge%",
                modifier = Modifier.fillMaxWidth()
            )

            if (isOverdriveReady) {
                val infiniteTransition = rememberInfiniteTransition(label = "overdrive_pulse")
                val pulseScale by infiniteTransition.animateFloat(
                    initialValue = 0.98f,
                    targetValue = 1.03f,
                    animationSpec = infiniteRepeatable(tween(500), RepeatMode.Reverse),
                    label = "pulse"
                )

                Button(
                    onClick = {
                        haptics.criticalHit()
                        audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                        onTriggerOverdrive()
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3B0066)),
                    border = androidx.compose.foundation.BorderStroke(2.dp, EidosPurple),
                    shape = androidx.compose.foundation.shape.CutCornerShape(8.dp)
                ) {
                    Text(
                        "⚡ СБРОС ЯДРА (OVERDRIVE) [250% КРИТ // СТАН]",
                        color = Color.Yellow,
                        fontWeight = FontWeight.Black,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }

        // OVERCHARGE RISK PROTOCOL BUTTON (Non-combat raid boost)
        if (!isCombat && !isAnomaly && overchargeTier < io.eidos.zerolayer.domain.combat.CombatEngine.MAX_OVERCHARGE_TIER) {
            Button(
                onClick = {
                    haptics.glitchPulse()
                    audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
                    onBoostOvercharge()
                },
                modifier = Modifier.fillMaxWidth().height(40.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2A1000)),
                border = androidx.compose.foundation.BorderStroke(1.dp, EidosOrange),
                shape = androidx.compose.foundation.shape.CutCornerShape(6.dp)
            ) {
                Text(
                    "🔥 ФОРСИРОВАТЬ СИГНАЛ (+50% ЛУТ / +РИСК) [УР ${overchargeTier + 1}/3]",
                    color = EidosOrange,
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        if (isAnomaly && anomalyData != null) {
            Text("ВЫБОР ДЕЙСТВИЯ В НУЛЕВОМ СЛОЕ:", color = Color.Yellow, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
            anomalyData.options.forEach { option ->
                val btnColor = when {
                    option.id.contains("red") || option.id.contains("brute") -> EidosRed
                    option.id.contains("blue") || option.id.contains("key") -> EidosCyan
                    option.id.contains("green") || option.id.contains("seal") || option.id.contains("drain") -> EidosNeon
                    option.id.contains("sort") || option.id.contains("hack") || option.id.contains("overclock") -> Color.Yellow
                    else -> Color.Yellow
                }
                Button(
                    onClick = {
                        haptics.glitchPulse()
                        audio.playSound(EidosAudioManager.SoundType.GLITCH_FOUND)
                        onAnomalyChoice(option.id)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = btnColor.copy(alpha = 0.15f)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, btnColor),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(vertical = 4.dp)) {
                        Text(option.text, color = btnColor, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        Text(option.description, color = Color.LightGray, fontSize = 10.sp, textAlign = TextAlign.Center)
                    }
                }
            }
        } else {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Primary Action: Step into Abyss
                Button(
                    onClick = {
                        if (isCombat) {
                            haptics.criticalHit()
                            audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                        } else {
                            haptics.step()
                            audio.playSound(EidosAudioManager.SoundType.RAID_STEP)
                        }
                        onNextStep()
                    },
                    modifier = Modifier.weight(1.2f).height(50.dp),
                    enabled = !isAnomaly,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D2818)),
                    border = androidx.compose.foundation.BorderStroke(1.5.dp, EidosNeon),
                    shape = androidx.compose.foundation.shape.CutCornerShape(8.dp)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("🏃 [ ШАГ В БЕЗДНУ ]", color = EidosNeon, fontWeight = FontWeight.Black, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        Text(primaryButtonText, color = Color.LightGray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                    }
                }

                // Secondary Action: Evacuate / Open Inventory Buffer
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onOpenBuffer()
                    },
                    modifier = Modifier.weight(0.8f).height(50.dp),
                    shape = androidx.compose.foundation.shape.CutCornerShape(8.dp),
                    colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFF1F080C)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("🎒 ИНВЕНТАРЬ", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        Text("БУФЕР ЛУТА", color = Color.Gray, fontSize = 8.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (isCombat) {
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onOpenBuffer()
                    },
                    modifier = Modifier.weight(1f),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = EidosCyan)
                ) {
                    Text("ИНВЕНТАРЬ", fontSize = 12.sp)
                }
                OutlinedButton(
                    onClick = {
                        haptics.criticalHit()
                        audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                        onUseAbility()
                    },
                    modifier = Modifier.weight(1f),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.Yellow)
                ) {
                    Text("СПОСОБНОСТЬ", fontSize = 12.sp)
                }
            } else {
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onScanSector()
                    },
                    modifier = Modifier.weight(1f),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp)
                ) {
                    Text("СКАН [5 ЭНЕРГИИ]", fontSize = 12.sp)
                }
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onOpenBuffer()
                    },
                    modifier = Modifier.weight(1f),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp)
                ) {
                    Text("ИНВЕНТАРЬ", fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun DopamineLootDialog(
    coinsGained: Long,
    xpGained: Long,
    itemsGained: List<String>,
    onDismiss: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alphaPulse by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(800), RepeatMode.Reverse),
        label = "alpha"
    )

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF0D1B2A),
        shape = CutCornerShape(8.dp),
        modifier = Modifier.border(2.dp, EidosNeon.copy(alpha = alphaPulse), CutCornerShape(8.dp)),
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("💎 ", fontSize = 22.sp)
                Text(
                    "НАГРАДА ИЗВЛЕЧЕНА!",
                    color = EidosNeon,
                    fontWeight = FontWeight.Black,
                    fontSize = 16.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    "Успешно получены новые байты данных и трофеи в буфер:",
                    color = Color.LightGray,
                    fontSize = 11.sp
                )

                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    if (coinsGained > 0) {
                        Surface(
                            color = Color(0xFF1E3A8A),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan)
                        ) {
                            Text(
                                "+$coinsGained BC 💰",
                                color = EidosCyan,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                            )
                        }
                    }
                    if (xpGained > 0) {
                        Surface(
                            color = Color(0xFF14532D),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon)
                        ) {
                            Text(
                                "+$xpGained XP ⭐",
                                color = EidosNeon,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                            )
                        }
                    }
                }

                if (itemsGained.isNotEmpty()) {
                    Text(
                        "ОБНАРУЖЕНЫ НОВЫЕ ПРЕДМЕТЫ:",
                        color = Color.Yellow,
                        fontWeight = FontWeight.Bold,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    itemsGained.forEach { rawId ->
                        val cleanId = rawId.trim()
                        val name = getItemNameReadable(cleanId)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("📦 ", fontSize = 14.sp)
                            Text(
                                name,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                shape = CutCornerShape(4.dp)
            ) {
                Text("ЗАБРАТЬ В БУФЕР", color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }
    )
}

@Composable
fun EvacuationSummaryDialog(
    session: RaidSession?,
    onConfirmExit: () -> Unit
) {
    val coins = session?.buffer_coins ?: 0L
    val xp = session?.buffer_xp ?: 0L
    val depth = session?.depth ?: 0
    val itemsStr = session?.buffer_items ?: ""
    val itemsList = if (itemsStr.isBlank()) emptyList() else itemsStr.split(",")

    AlertDialog(
        onDismissRequest = onConfirmExit,
        containerColor = io.eidos.zerolayer.ui.theme.ZzzDarkSurface,
        shape = CutCornerShape(topStart = 14.dp, bottomEnd = 14.dp),
        modifier = Modifier.border(2.dp, io.eidos.zerolayer.ui.theme.ZzzAcidYellow, CutCornerShape(topStart = 14.dp, bottomEnd = 14.dp)),
        title = {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "🛸 RAID SESSION SUMMARY",
                        color = Color.White,
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 14.sp,
                        fontFamily = FontFamily.SansSerif,
                        letterSpacing = 1.sp
                    )
                    Text("─ □ ✕", color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                }

                Spacer(modifier = Modifier.height(6.dp))

                // [ S ] RANK Glowing Banner
                Surface(
                    color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                    shape = CutCornerShape(topStart = 4.dp, bottomEnd = 6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            "ЭВАКУАЦИЯ УСПЕШНА",
                            color = Color.Black,
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 13.sp,
                            fontFamily = FontFamily.SansSerif,
                            letterSpacing = 1.sp
                        )
                        Surface(
                            color = Color.Black,
                            shape = CutCornerShape(2.dp)
                        ) {
                            Text(
                                " [ S ] RANK ",
                                color = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }
        },
        text = {
            Column(
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.verticalScroll(rememberScrollState())
            ) {
                // Key Stats Grid
                Surface(
                    color = Color(0xFF0C0E14),
                    border = androidx.compose.foundation.BorderStroke(1.5.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan.copy(alpha = 0.7f)),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Text("📍 ГЛУБИНА:", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text("${depth}м 🏢", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp)
                        }
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Text("💰 BIOCOINS:", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text("+$coins 🪙", color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp)
                        }
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Text("⭐ ОПЫТ (XP):", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text("+$xp ▲", color = io.eidos.zerolayer.ui.theme.ZzzToxicGreen, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp)
                        }
                    }
                }

                Text(
                    "📦 ДОБЫТЫЕ АРТЕФАКТЫ (${itemsList.size} ШТ):",
                    color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                    fontWeight = FontWeight.ExtraBold,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )

                if (itemsList.isEmpty()) {
                    Text("Буфер пуст. Никаких предметов не найдено.", color = Color.Gray, fontSize = 10.sp)
                } else {
                    // Loot items in neon glowing frames grid
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        itemsList.forEachIndexed { index, rawId ->
                            val cleanId = rawId.trim()
                            val name = getItemNameReadable(cleanId)
                            val neonBorderColor = when(index % 3) {
                                0 -> io.eidos.zerolayer.ui.theme.ZzzElectricCyan
                                1 -> io.eidos.zerolayer.ui.theme.ZzzHotMagenta
                                else -> io.eidos.zerolayer.ui.theme.ZzzAcidYellow
                            }

                            Surface(
                                color = Color(0xFF141824),
                                shape = CutCornerShape(topStart = 4.dp, bottomEnd = 4.dp),
                                border = androidx.compose.foundation.BorderStroke(1.dp, neonBorderColor),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text("💠 ", fontSize = 12.sp)
                                        Text(
                                            name.uppercase(),
                                            color = Color.White,
                                            fontSize = 11.sp,
                                            fontFamily = FontFamily.SansSerif,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                    io.eidos.zerolayer.ui.components.ZzzBadge(
                                        text = "SAVED",
                                        color = neonBorderColor,
                                        textColor = Color.Black
                                    )
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            io.eidos.zerolayer.ui.components.ZzzMainButton(
                text = "ВЕРНУТЬСЯ В ХАБ С ЛУТОМ ➔",
                onClick = onConfirmExit,
                primaryColor = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                borderColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                textColor = Color.Black,
                modifier = Modifier.fillMaxWidth()
            )
        }
    )
}

fun getItemNameReadable(itemId: String): String {
    return when(itemId) {
        "rusty_knife" -> "Ржавый Нож"
        "crowbar" -> "Ломик"
        "data_bat" -> "Бита Данных"
        "shock_baton" -> "Шокер-Дубинка"
        "cyber_katana" -> "Кибер-Катана"
        "laser_pistol" -> "Лазерный Пистолет"
        "plasma_rifle" -> "Плазменная Винтовка"
        "nano_blade" -> "Нано-Клинок"
        "void_cannon" -> "Пушка Бездны"
        "singularity_sword" -> "Меч Сингулярности"
        "hoodie" -> "Худи Скитальца"
        "leather_jacket" -> "Кожаная Куртка"
        "kevlar_vest" -> "Кевларовый Жилет"
        "tactical_suit" -> "Тактический Костюм"
        "exo_skeleton" -> "Экзоскелет"
        "nano_suit" -> "Нано-Костюм"
        "phantom_cloak" -> "Плащ Фантома"
        "nomad_goggles" -> "Очки Номада"
        "scavenger_mask" -> "Маска Мусорщика"
        "tactical_helmet" -> "Тактический Шлем"
        "medkit" -> "Нано-Аптечка"
        "energy_cell" -> "Энергоячейка"
        "master_key" -> "Ключ-Дешифратор"
        "abyssal_key" -> "Ключ Бездны"
        "eidos_shard" -> "Осколок Эйдоса"
        "ram_chip" -> "RAM Модификатор"
        "cpu_booster" -> "CPU Акселератор"
        "glitch_filter" -> "Фильтр Аномалий"
        "ai_core" -> "Ядро ИИ-Компаньона"
        "overclocker" -> "Оверклокер (Смертник)"
        "backup_drive" -> "Резервный Накопитель"
        "neural_link" -> "Нейро-Шлюз"
        "chronometer" -> "Хронос-Имплант"
        "logic_gate" -> "Абсолютная Логика"
        "god_mode_chip" -> "God-Протокол"
        "corrupted_data_cluster" -> "Поврежденный Кластер Данных"
        else -> itemId.replace("_", " ").uppercase()
    }
}

@Composable
fun RaidBufferModal(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<ItemMetadata>,
    onUseConsumable: (InventoryItem) -> Unit,
    onDismiss: () -> Unit,
    onOpenFullInventory: () -> Unit
) {
    val rawItemsStr = session?.buffer_items ?: ""
    val itemsList = if (rawItemsStr.isBlank()) emptyList() else rawItemsStr.split(",").filter { it.isNotBlank() }
    val bufferCoins = session?.buffer_coins ?: 0L
    val bufferXp = session?.buffer_xp ?: 0L
    val signal = session?.signal ?: 100
    val depth = session?.depth ?: 0

    // Consumables in player backpack
    val consumables = inventory.filter { item ->
        val meta = allItemsMetadata.find { it.id == item.item_id }
        item.slot == "consumable" || (meta != null && meta.type == "consumable") ||
                item.item_id.contains("medkit") || item.item_id.contains("stim") || item.item_id.contains("cell") || item.item_id.contains("repair")
    }

    var selectedTab by remember { mutableStateOf("loot") } // "loot" or "supplies"

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFF090E17),
        shape = CutCornerShape(12.dp),
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
            .border(1.5.dp, Color(0xFFFF9800), CutCornerShape(12.dp)),
        title = {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("🎒", fontSize = 18.sp)
                        Column {
                            Text(
                                "БУФЕР НУЛЕВОГО СЛОЯ",
                                color = Color(0xFFFF9800),
                                fontWeight = FontWeight.Black,
                                fontSize = 13.sp,
                                fontFamily = FontFamily.Monospace,
                                letterSpacing = 1.sp
                            )
                            Text(
                                "ГЛУБИНА: ${depth}м | СИГНАЛ: ${signal}%",
                                color = Color(0xFF90A4AE),
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Text("✕", color = Color.Gray, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Stats overview banner
                Surface(
                    color = Color(0xFF141923),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF263238)),
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("BIOCOINS", color = Color(0xFF78909C), fontSize = 8.sp, fontFamily = FontFamily.Monospace)
                            Text("+$bufferCoins 🪙", color = EidosGold, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ОПЫТ БЕЗДНЫ", color = Color(0xFF78909C), fontSize = 8.sp, fontFamily = FontFamily.Monospace)
                            Text("+$bufferXp XP 🧠", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ПРЕДМЕТЫ", color = Color(0xFF78909C), fontSize = 8.sp, fontFamily = FontFamily.Monospace)
                            Text("${itemsList.size}/100 📦", color = Color(0xFFFF9800), fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Tab Switcher: [НАЙДЕННЫЙ ЛУТ] | [ПОЛЕВЫЕ ПРИПАСЫ (N)]
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    val isLootSelected = selectedTab == "loot"
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(28.dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(if (isLootSelected) Color(0xFFFF9800).copy(alpha = 0.25f) else Color(0xFF141923))
                            .border(1.dp, if (isLootSelected) Color(0xFFFF9800) else Color(0xFF263238), RoundedCornerShape(4.dp))
                            .cyberClickable { selectedTab = "loot" },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "ЛУТ В БУФЕРЕ (${itemsList.size})",
                            color = if (isLootSelected) Color(0xFFFF9800) else Color.Gray,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    val isSuppliesSelected = selectedTab == "supplies"
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(28.dp)
                            .clip(RoundedCornerShape(4.dp))
                            .background(if (isSuppliesSelected) EidosNeon.copy(alpha = 0.25f) else Color(0xFF141923))
                            .border(1.dp, if (isSuppliesSelected) EidosNeon else Color(0xFF263238), RoundedCornerShape(4.dp))
                            .cyberClickable { selectedTab = "supplies" },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "ПРИПАСЫ (${consumables.size})",
                            color = if (isSuppliesSelected) EidosNeon else Color.Gray,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 160.dp, max = 320.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                if (selectedTab == "loot") {
                    if (itemsList.isEmpty()) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("📦", fontSize = 28.sp)
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "БУФЕР ЛУТА ПУСТ",
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    "Исследуйте Бездну, побеждайте вирусы и находите квантовые тайники.",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace,
                                    textAlign = TextAlign.Center,
                                    modifier = Modifier.padding(top = 4.dp, start = 12.dp, end = 12.dp)
                                )
                            }
                        }
                    } else {
                        itemsList.forEach { itemId ->
                            val meta = allItemsMetadata.find { it.id == itemId }
                            val itemName = meta?.name ?: getItemNameReadable(itemId)
                            val rarity = meta?.rarity ?: "common"
                            val rarityColor = when (rarity) {
                                "legendary" -> EidosGold
                                "epic" -> EidosPurple
                                "rare" -> EidosCyan
                                "uncommon" -> EidosNeon
                                else -> Color(0xFF90A4AE)
                            }
                            val slotName = when (meta?.type) {
                                "weapon" -> "Оружие"
                                "armor" -> "Броня"
                                "chip" -> "Квант-Чип"
                                "consumable" -> "Припас"
                                else -> "Модуль"
                            }

                            Surface(
                                color = Color(0xFF0F1520),
                                border = androidx.compose.foundation.BorderStroke(1.dp, rarityColor.copy(alpha = 0.6f)),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    modifier = Modifier.padding(8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(36.dp)
                                            .clip(RoundedCornerShape(4.dp))
                                            .background(Color(0xFF05080C))
                                            .border(1.dp, rarityColor, RoundedCornerShape(4.dp)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        EidosImage(
                                            resName = itemId,
                                            contentDescription = itemName,
                                            modifier = Modifier.size(28.dp),
                                            contentScale = ContentScale.Fit
                                        )
                                    }

                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = itemName,
                                            color = rarityColor,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis
                                        )
                                        Row(
                                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                slotName.uppercase(),
                                                color = Color.Gray,
                                                fontSize = 8.sp,
                                                fontFamily = FontFamily.Monospace
                                            )
                                            Text("•", color = Color.DarkGray, fontSize = 8.sp)
                                            Text(
                                                rarity.uppercase(),
                                                color = rarityColor.copy(alpha = 0.8f),
                                                fontSize = 8.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                    }

                                    Surface(
                                        color = Color(0xFFFF9800).copy(alpha = 0.15f),
                                        shape = RoundedCornerShape(3.dp),
                                        border = androidx.compose.foundation.BorderStroke(0.5.dp, Color(0xFFFF9800))
                                    ) {
                                        Text(
                                            "БУФЕР",
                                            color = Color(0xFFFF9800),
                                            fontSize = 8.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                } else {
                    // Supplies tab
                    if (consumables.isEmpty()) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("🧪", fontSize = 28.sp)
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "НЕТ ПРИПАСОВ В РЮКЗАКЕ",
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    "Купите аптечки и энергоячейки в Кибер-Магазине перед спуском в Бездну.",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace,
                                    textAlign = TextAlign.Center,
                                    modifier = Modifier.padding(top = 4.dp, start = 12.dp, end = 12.dp)
                                )
                            }
                        }
                    } else {
                        consumables.forEach { item ->
                            val meta = allItemsMetadata.find { it.id == item.item_id }
                            val itemName = meta?.name ?: getItemNameReadable(item.item_id)
                            Surface(
                                color = Color(0xFF0F1520),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon.copy(alpha = 0.5f)),
                                shape = RoundedCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    modifier = Modifier.padding(8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(36.dp)
                                            .clip(RoundedCornerShape(4.dp))
                                            .background(Color(0xFF05080C))
                                            .border(1.dp, EidosNeon, RoundedCornerShape(4.dp)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        EidosImage(
                                            resName = item.item_id,
                                            contentDescription = itemName,
                                            modifier = Modifier.size(28.dp),
                                            contentScale = ContentScale.Fit
                                        )
                                    }

                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            itemName,
                                            color = Color.White,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            "Количество: ${item.quantity}",
                                            color = EidosNeon,
                                            fontSize = 9.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }

                                    Button(
                                        onClick = {
                                            onUseConsumable(item)
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                                        shape = CutCornerShape(4.dp),
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
                                        modifier = Modifier.height(30.dp)
                                    ) {
                                        Text(
                                            "ПРИМЕНИТЬ",
                                            color = Color.Black,
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1B263B)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth().height(42.dp)
                ) {
                    Text(
                        "➔ ВЕРНУТЬСЯ К РЕЙДУ В БЕЗДНЕ",
                        color = EidosCyan,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                OutlinedButton(
                    onClick = onOpenFullInventory,
                    colors = ButtonDefaults.outlinedButtonColors(containerColor = Color.Transparent),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF37474F)),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth().height(36.dp)
                ) {
                    Text(
                        "⚙ ОТКРЫТЬ ПОЛНЫЙ ИНВЕНТАРЬ DECK_OS",
                        color = Color.LightGray,
                        fontSize = 9.5.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    )
}
