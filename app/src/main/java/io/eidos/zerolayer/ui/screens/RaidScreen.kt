package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
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
import io.eidos.zerolayer.data.Player

import io.eidos.zerolayer.data.GameLog
import io.eidos.zerolayer.ui.components.TerminalLog
import io.eidos.zerolayer.ui.utils.ghostTyping

import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.zzz.ZzzCyberSonarRadar
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
import io.eidos.zerolayer.ui.components.EidosStatBar
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.VideoBackground
import androidx.compose.ui.draw.alpha
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
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    onNextStep: () -> Unit,
    onAttack: () -> Unit = onNextStep,
    onAnomalyChoice: (String) -> Unit,
    onOpenInventory: () -> Unit,
    onExitRaid: () -> Unit,
    onBack: () -> Unit,
    onStartRaid: () -> Unit = {},
    onScanSector: () -> Unit = {},
    onDefend: () -> Unit = {},
    onUseAbility: () -> Unit = {},
    onTriggerOverdrive: () -> Unit = {},
    onBoostOvercharge: () -> Unit = {},
    onUseConsumable: (InventoryItem) -> Unit = {},
    onAcceptMaxwellContract: (String) -> Unit = {},
    onBetDemonHp: () -> Unit = {},
    onBetDemonBuffer: () -> Unit = {},
    onIgnoreDemon: () -> Unit = {},
    onResolveHardGlitch: (chosenIndex: Int, correctIndex: Int) -> Unit = { _, _ -> },
    onResolveRiddle: (Boolean) -> Unit = {},
    onFlee: () -> Unit = {},
    onSalvageBufferItem: (Int) -> Unit = {},
    deathReport: io.eidos.zerolayer.data.GameRepository.DeathReport? = null,
    onClearDeathReport: () -> Unit = {}
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
    var inspectVillain by remember { mutableStateOf<io.eidos.zerolayer.data.GameVillainData?>(null) }
    var showCombatLogModal by remember { mutableStateOf(false) }

    // Dopamine Loot Modal State
    var showDopamineModal by remember { mutableStateOf(false) }
    var dopamineCoins by remember { mutableLongStateOf(0L) }
    var dopamineXp by remember { mutableLongStateOf(0L) }
    var dopamineItems by remember { mutableStateOf<List<String>>(emptyList()) }

    var prevCoins by remember { mutableLongStateOf(session?.buffer_coins ?: 0L) }
    var prevXp by remember { mutableLongStateOf(session?.buffer_xp ?: 0L) }
    var prevItemsStr by remember { mutableStateOf(session?.buffer_items ?: "") }
    var prevKills by remember { mutableIntStateOf(session?.kills ?: 0) }
    var showVictoryCinematic by remember { mutableStateOf(false) }
    var showOverdriveCinematic by remember { mutableStateOf(false) }

    LaunchedEffect(session?.kills) {
        val currentKills = session?.kills ?: 0
        if (currentKills > prevKills && currentKills > 0) {
            showVictoryCinematic = true
        }
        prevKills = currentKills
    }

    // Visual Combat Juice: Card Shake, Screen Flash, Floating Damage
    val cardShakeX = remember { androidx.compose.animation.core.Animatable(0f) }
    val screenFlashAlpha = remember { androidx.compose.animation.core.Animatable(0f) }
    var floatingDamageText by remember { mutableStateOf<String?>(null) }
    var floatingDamageColor by remember { mutableStateOf(EidosCyan) }
    var floatingDamageScale by remember { mutableFloatStateOf(1f) }
    var activeProcs by remember { mutableStateOf<List<io.eidos.zerolayer.data.EquipmentProcEvent>>(emptyList()) }
    var latestProc by remember { mutableStateOf<io.eidos.zerolayer.data.EquipmentProcEvent?>(null) }

    LaunchedEffect(activeProcs) {
        if (activeProcs.isNotEmpty()) {
            kotlinx.coroutines.delay(2500)
            activeProcs = emptyList()
            latestProc = null
        }
    }

    LaunchedEffect(combatEventFlow) {
        combatEventFlow?.collect { event ->
            if (event.triggeredProcs.isNotEmpty()) {
                activeProcs = event.triggeredProcs
                latestProc = event.triggeredProcs.lastOrNull()
                haptics.glitchPulse()
            }
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
            VideoBackground(resName = "bg_abyss", modifier = Modifier.fillMaxSize())
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_null_layer),
                contentDescription = null,
                modifier = Modifier.fillMaxSize().alpha(0.35f),
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
                                    Text("${activeStats?.attack ?: player?.attack ?: 10}", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("ЗАЩИТА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                    Text("${activeStats?.defense ?: player?.defense ?: 5}", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp)
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
                        .padding(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    // Unified Cyber Telemetry Strip
                    val hasOblivionChip = remember(inventory) { inventory.any { it.is_equipped && it.item_id == "oblivion_chip" } }
                    val hasTacticalScanner = remember(inventory) { inventory.any { it.item_id == "tactical_scanner" } }
                    RaidHUD(
                        session = session,
                        player = player,
                        hasOblivionChip = hasOblivionChip,
                        hasTacticalScanner = hasTacticalScanner,
                        overchargeTier = overchargeTier,
                        onOpenBuffer = { showBufferModal = true }
                    )

                    Spacer(modifier = Modifier.height(4.dp))

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
                                equippedItems = inventory.filter { it.is_equipped },
                                activeProcs = activeProcs,
                                latestProc = latestProc,
                                onTriggerHack = { showMinigame = true },
                                onInspectVillain = { villain -> inspectVillain = villain }
                            )
                        }
                    }

                    val isCombat = session.current_enemy_id != null
                    if (isCombat) {
                        Spacer(modifier = Modifier.height(4.dp))
                        CombatTickerBar(
                            logs = logs,
                            onOpenFullLog = { showCombatLogModal = true }
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                    } else {
                        Spacer(modifier = Modifier.height(6.dp))
                        TerminalLog(logs)
                        Spacer(modifier = Modifier.height(6.dp))
                    }

                    // Controls
                    if (!isEvacuatingHold) {
                        RaidControls(
                            session = session,
                            player = player,
                            anomalyData = anomalyData,
                            inventory = inventory,
                            overdriveCharge = overdriveCharge,
                            overchargeTier = overchargeTier,
                            activeStats = activeStats,
                            onNextStep = onNextStep,
                            onAttack = onAttack,
                            onAnomalyChoice = onAnomalyChoice,
                            onOpenInventory = onOpenInventory,
                            onOpenBuffer = { showBufferModal = true },
                            onScanSector = onScanSector,
                            onDefend = onDefend,
                            onUseAbility = onUseAbility,
                            onTriggerOverdrive = {
                                showOverdriveCinematic = true
                                onTriggerOverdrive()
                            },
                            onBoostOvercharge = onBoostOvercharge,
                            onUseConsumable = { itemId ->
                                inventory.find { it.item_id == itemId }?.let { onUseConsumable(it) }
                            },
                            onFlee = onFlee
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
            onSalvageBufferItem = onSalvageBufferItem,
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

    // Riddle / Sphinx Encounter Modal
    if (session?.next_event_type == "riddle") {
        io.eidos.zerolayer.ui.components.LoreRiddleDialog(
            onDismiss = {
                onNextStep()
            },
            onCorrectAnswer = {
                onResolveRiddle(true)
            },
            onWrongAnswer = {
                onResolveRiddle(false)
            }
        )
    }

    // Maxwell's Demon Encounter Modal (Isolated strictly to RaidScreen at depth 50+)
    if (session?.next_event_type == "maxwells_demon") {
        val hasEquipInBuffer = session.buffer_items.split(",").any { it.isNotBlank() }
        io.eidos.zerolayer.ui.components.MaxwellDemonModal(
            currentHp = player?.hp ?: 100,
            bufferCoins = session.buffer_coins,
            playerCoins = player?.biocoin ?: 0L,
            playerXp = player?.xp ?: 0L,
            hasEquipInBuffer = hasEquipInBuffer,
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

    if (showVictoryCinematic) {
        LaunchedEffect(Unit) {
            kotlinx.coroutines.delay(2200)
            showVictoryCinematic = false
        }
        androidx.compose.ui.window.Dialog(
            onDismissRequest = { showVictoryCinematic = false },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black)
                    .clickable { showVictoryCinematic = false },
                contentAlignment = Alignment.Center
            ) {
                VideoBackground(resName = "combat_victory", modifier = Modifier.fillMaxSize())
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 56.dp)
                        .background(Color.Black.copy(alpha = 0.75f))
                        .border(1.dp, EidosNeon, CutCornerShape(4.dp))
                        .padding(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text(
                        "💥 ЦЕЛЬ НЕЙТРАЛИЗОВАНА // СИГНАЛ ВРАГА РАСТВОРЕН 💥",
                        color = EidosNeon,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }

    if (showOverdriveCinematic) {
        LaunchedEffect(Unit) {
            kotlinx.coroutines.delay(2200)
            showOverdriveCinematic = false
        }
        androidx.compose.ui.window.Dialog(
            onDismissRequest = { showOverdriveCinematic = false },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black)
                    .clickable { showOverdriveCinematic = false },
                contentAlignment = Alignment.Center
            ) {
                VideoBackground(resName = "overdrive_activation", modifier = Modifier.fillMaxSize())
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 56.dp)
                        .background(Color.Black.copy(alpha = 0.75f))
                        .border(1.dp, Color(0xFFFFD700), CutCornerShape(4.dp))
                        .padding(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text(
                        "⚡ ОВЕРДРАЙВ 100%: ВСПЛЕСК МОЩНОСТИ ЯДРА ⚡",
                        color = Color(0xFFFFD700),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }

    if (inspectVillain != null) {
        EnemyInspectModal(
            villain = inspectVillain!!,
            onDismiss = { inspectVillain = null }
        )
    }

    if (showCombatLogModal) {
        FullCombatLogModal(
            logs = logs,
            onDismiss = { showCombatLogModal = false }
        )
    }

    if (deathReport != null) {
        DeathScreenOverlay(
            report = deathReport,
            onDismiss = onClearDeathReport
        )
    }
}

@Composable
fun DeathScreenOverlay(
    report: io.eidos.zerolayer.data.GameRepository.DeathReport,
    onDismiss: () -> Unit
) {
    val itemsCount = report.lostItems.split(",").filter { it.isNotBlank() }.size
    val context = androidx.compose.ui.platform.LocalContext.current
    val haptics = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }
    val audio = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }

    LaunchedEffect(Unit) {
        audio.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.ERROR_GLITCH)
        haptics.glitchPulse()
    }

    val infiniteTransition = rememberInfiniteTransition(label = "crt_flicker")
    val crtFlicker by infiniteTransition.animateFloat(
        initialValue = 0.88f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(120, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "crt"
    )

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            color = Color(0xFF020304).copy(alpha = crtFlicker),
            modifier = Modifier.fillMaxSize()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .border(BorderStroke(3.dp, Color(0xFFFF0055).copy(alpha = 0.85f)))
                    .padding(20.dp)
            ) {
                // Neural Interface Critical Signal Failure Video
                VideoBackground(resName = "death_glitch", modifier = Modifier.fillMaxSize())
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.65f))
                )

                // CRT Scanlines Canvas Overlay
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val lineSpacing = 6.dp.toPx()
                    var y = 0f
                    while (y < size.height) {
                        drawLine(
                            color = Color(0xFFFF0055).copy(alpha = 0.04f),
                            start = androidx.compose.ui.geometry.Offset(0f, y),
                            end = androidx.compose.ui.geometry.Offset(size.width, y),
                            strokeWidth = 1.5f
                        )
                        y += lineSpacing
                    }
                }

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState()),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Spacer(modifier = Modifier.height(16.dp))

                        // Large Monospace Title
                        Text(
                            text = "[ 💀 СИГНАЛ ПОТЕРЯН // АВАРИЙНЫЙ СБРОС СОЗНАНИЯ ]",
                            color = Color(0xFFFF0055),
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Center,
                            lineHeight = 24.sp
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        // Subtitle EVA-09
                        Text(
                            text = "EVA-09: «Критическая десинхронизация. Аварийный сброс сознания в Хаб...»",
                            color = Color(0xFFFF5252).copy(alpha = 0.85f),
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(14.dp))

                        // Digital disintegration art
                        Box(
                            modifier = Modifier
                                .size(105.dp)
                                .clip(CutCornerShape(8.dp))
                                .background(Color(0xFF140207))
                                .border(1.5.dp, Color(0xFFFF0055), CutCornerShape(8.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            EidosImage(
                                resName = "raid_death",
                                fallbackIcon = Icons.Default.Warning,
                                borderColor = Color.Transparent,
                                contentScale = ContentScale.Crop,
                                modifier = Modifier.fillMaxSize()
                            )
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        // 4-STEP PENALTY REPORT
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            // 1. Buffer Incineration
                            Surface(
                                color = Color(0xFF130408),
                                border = BorderStroke(1.dp, Color(0xFFFF0055).copy(alpha = 0.5f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            "1. БУФЕР РЕЙДА:",
                                            color = Color.LightGray,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Box(
                                            modifier = Modifier
                                                .background(Color(0xFFFF0055).copy(alpha = 0.25f))
                                                .border(1.dp, Color(0xFFFF0055), CutCornerShape(2.dp))
                                                .padding(horizontal = 6.dp, vertical = 2.dp)
                                        ) {
                                            Text(
                                                "[ БУФЕР УНИЧТОЖЕН: -100% ]",
                                                color = Color(0xFFFF0055),
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = "🪙 -${report.lostCoins} BC   ⚡ -${report.lostXp} XP   🎒 -${itemsCount} предметов",
                                        color = Color.Gray,
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace,
                                        style = androidx.compose.ui.text.TextStyle(textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough)
                                    )
                                }
                            }

                            // 2. EMP Durability Strike
                            Surface(
                                color = Color(0xFF130408),
                                border = BorderStroke(1.dp, Color(0xFFFF0055).copy(alpha = 0.5f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Text(
                                            "2. ЭМИ-УДАР ПО СНАРЯЖЕНИЮ:",
                                            color = Color.LightGray,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            "-${report.durabilityPenaltyPercent}% ПРОЧНОСТИ",
                                            color = Color(0xFFFF0055),
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                    if (report.brokenItems.isNotEmpty()) {
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = "🚨 [CRITICAL ERROR: ${report.brokenItems.joinToString()} СЛОМАНО] — урон снижен до базовых 5 ATK!",
                                            color = Color(0xFFFF5252),
                                            fontSize = 9.5.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                            }

                            // 3. Grave creation
                            Surface(
                                color = Color(0xFF041218),
                                border = BorderStroke(1.dp, Color(0xFF00E5FF).copy(alpha = 0.4f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    Text(
                                        "3. МОГИЛА ОПЕРАТОРА (СЛОЙ ${report.depth}м):",
                                        color = Color(0xFF00E5FF),
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = if (report.graveCreated) {
                                            "Ваше цифровое тело осталось на глубине ${report.depth}м. Другие Операторы могут разграбить ваши останки."
                                        } else {
                                            "Останки рассеяны в информационном шуме Нулевого Слоя."
                                        },
                                        color = Color.LightGray,
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            // 4. Critical Rollback to Hub
                            Surface(
                                color = Color(0xFF130408),
                                border = BorderStroke(1.dp, Color(0xFFFF0055).copy(alpha = 0.5f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    Text(
                                        "4. АВАРИЙНЫЙ ОТКАТ В ХАБ:",
                                        color = Color.LightGray,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = "⚡ Сигнал восстановлен до 1%. Овердрайв сброшен до 0%.",
                                        color = Color.Gray,
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Full-width Return Button
                    Button(
                        onClick = onDismiss,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF0055)),
                        shape = CutCornerShape(6.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ) {
                        Text(
                            text = "[ ⚡ АВАРИЙНАЯ ПЕРЕЗАГРУЗКА В ХАБ ]",
                            color = Color.White,
                            fontWeight = FontWeight.Black,
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun RaidHUD(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player? = null,
    hasOblivionChip: Boolean = false,
    hasTacticalScanner: Boolean = false,
    overchargeTier: Int = 0,
    onOpenBuffer: () -> Unit = {}
) {
    val signal = session?.signal ?: 94
    val depth = session?.depth ?: 1480
    val overdriveTurns = session?.overdrive_turns ?: 0
    val lootCount = session?.buffer_items?.split(",")?.filter { it.isNotBlank() }?.size ?: 0
    val nowSec = System.currentTimeMillis() / 1000L

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        // Active Status Micro-Badges Row
        val hasOvercharge = overchargeTier > 0
        val hasOverdrive = overdriveTurns > 0
        val hasBuff = player != null && player.anomalyBuffType != null && nowSec < player.anomalyBuffExpiry
        val isCombat = session?.current_enemy_id != null
        val showScanner = hasTacticalScanner && isCombat

        if (hasOvercharge || hasOverdrive || hasBuff || showScanner) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (showScanner) {
                    val pHp = player?.hp ?: 100
                    val eHp = session?.current_enemy_hp ?: 50
                    val pAtk = player?.attack ?: 20
                    val eAtk = maxOf(10, ((session?.depth ?: 0) / 10))
                    val pTurns = kotlin.math.ceil(eHp.toDouble() / maxOf(1, pAtk)).toInt()
                    val eTurns = kotlin.math.ceil(pHp.toDouble() / maxOf(1, eAtk)).toInt()
                    val winRate = if (pTurns <= eTurns) {
                        ((1.0 - (pTurns.toDouble() / (eTurns + 2))) * 100).toInt().coerceIn(55, 99)
                    } else {
                        ((eTurns.toDouble() / (pTurns + 2)) * 100).toInt().coerceIn(5, 49)
                    }
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(EidosNeon.copy(alpha = 0.2f))
                            .border(1.dp, EidosNeon, CutCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            "📊 WIN: $winRate%",
                            color = EidosNeon,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
                if (hasOvercharge) {
                    val lootMult = io.eidos.zerolayer.domain.combat.CombatEngine.getOverchargeLootMultiplier(overchargeTier)
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(EidosOrange.copy(alpha = 0.2f))
                            .border(1.dp, EidosOrange, CutCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            "🔥 x$lootMult (+${overchargeTier * 50}% ЛУТ)",
                            color = EidosOrange,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
                if (hasOverdrive) {
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(Color.Yellow.copy(alpha = 0.2f))
                            .border(1.dp, Color.Yellow, CutCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            "⚡ OVERDRIVE: ${overdriveTurns}Х",
                            color = Color.Yellow,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
                if (hasBuff) {
                    val buffName = when (player?.anomalyBuffType) {
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_GLITCH_BERSERK -> "⚡ БЕРСЕРК +25%"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_OVERLOAD -> "💰 ПЕРЕГРУЗКА +50%"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_STEALTH_NIGHT -> "🌙 СКРЫТНОСТЬ 30%"
                        io.eidos.zerolayer.domain.anomaly.AnomalyEngine.BUFF_VISUAL_DISTORTION -> "🌀 ИСКАЖЕНИЕ"
                        else -> "⚡ БАФФ"
                    }
                    val timeLeftSec = ((player?.anomalyBuffExpiry ?: nowSec) - nowSec).coerceAtLeast(0)
                    Box(
                        modifier = Modifier
                            .clip(CutCornerShape(4.dp))
                            .background(Color(0xFF00FFCC).copy(alpha = 0.2f))
                            .border(1.dp, Color(0xFF00FFCC), CutCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            "$buffName (${timeLeftSec}с)",
                            color = Color(0xFF00FFCC),
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }

        // Consolidated Telemetry Bar (46dp)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(46.dp)
                .clip(CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp))
                .background(Color(0xFF070D12).copy(alpha = 0.95f))
                .border(1.dp, EidosCyan.copy(alpha = 0.35f), CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp))
        ) {
            Row(
                modifier = Modifier.fillMaxSize(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Compartment 1: Depth (Сектор)
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .padding(horizontal = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_stat_depth),
                        contentDescription = "Глубина",
                        modifier = Modifier.size(18.dp),
                        contentScale = ContentScale.Fit
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Column {
                        Text("ГЛУБИНА", color = Color(0xFF78909C), fontSize = 7.5.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                        Text("${depth}м", color = EidosCyan, fontSize = 11.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                    }
                }

                // Vertical Divider
                Box(modifier = Modifier.width(1.dp).height(24.dp).background(Color(0xFF1E2D3D)))

                // Compartment 2: Signal with integrated gauge
                val signalColor = when {
                    signal > 50 -> EidosNeon
                    signal > 25 -> EidosOrange
                    else -> EidosRed
                }
                Box(
                    modifier = Modifier
                        .weight(1.1f)
                        .fillMaxHeight()
                        .padding(horizontal = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Image(
                                painter = painterResource(id = R.drawable.ic_stat_hp),
                                contentDescription = "Сигнал",
                                modifier = Modifier.size(16.dp),
                                contentScale = ContentScale.Fit
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("СИГНАЛ", color = Color(0xFFB0BEC5), fontSize = 7.5.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                if (hasOblivionChip) "???%" else "${signal}%",
                                color = signalColor,
                                fontSize = 11.5.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Spacer(modifier = Modifier.height(3.dp))
                        // Built-in slim progress bar
                        Box(
                            modifier = Modifier
                                .fillMaxWidth(0.85f)
                                .height(3.dp)
                                .clip(CutCornerShape(1.dp))
                                .background(Color(0xFF1A1A24))
                        ) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth((if (hasOblivionChip) 1f else signal / 100f).coerceIn(0f, 1f))
                                    .fillMaxHeight()
                                    .background(signalColor)
                            )
                        }
                    }
                }

                // Vertical Divider
                Box(modifier = Modifier.width(1.dp).height(24.dp).background(Color(0xFF1E2D3D)))

                // Compartment 3: Loot Buffer (Clickable)
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .clickable { onOpenBuffer() }
                        .padding(horizontal = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_biocoin),
                        contentDescription = "Буфер",
                        modifier = Modifier.size(17.dp),
                        contentScale = ContentScale.Fit
                    )
                    Spacer(modifier = Modifier.width(5.dp))
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("БУФЕР", color = Color(0xFF78909C), fontSize = 7.5.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.width(2.dp))
                            Text("🔍", fontSize = 7.sp)
                        }
                        Text("$lootCount/100", color = Color(0xFFFF9800), fontSize = 11.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        }
    }
}

@Composable
fun CombatTickerBar(
    logs: List<GameLog>,
    onOpenFullLog: () -> Unit
) {
    val recentCombat = logs.lastOrNull { it.type == "combat" || it.type == "error" }
        ?: logs.lastOrNull()

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(34.dp)
            .clip(CutCornerShape(4.dp))
            .background(Color(0xFF0E0709).copy(alpha = 0.95f))
            .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(4.dp))
            .clickable { onOpenFullLog() }
            .padding(horizontal = 8.dp),
        contentAlignment = Alignment.CenterStart
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.weight(1f),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("⚔️", fontSize = 11.sp)
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = recentCombat?.message ?: "Инициализация тактического контакта...",
                    color = if (recentCombat?.type == "error") EidosRed else Color(0xFFE2E8F0),
                    fontSize = 9.5.sp,
                    fontFamily = FontFamily.Monospace,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
            Spacer(modifier = Modifier.width(6.dp))
            Box(
                modifier = Modifier
                    .clip(CutCornerShape(2.dp))
                    .background(Color(0xFF22080E))
                    .border(0.5.dp, EidosRed.copy(alpha = 0.7f), CutCornerShape(2.dp))
                    .padding(horizontal = 5.dp, vertical = 2.dp)
            ) {
                Text("📜 ЛОГ", color = EidosRed, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun CombatArenaCard(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    enemyId: String,
    equippedItems: List<InventoryItem> = emptyList(),
    activeProcs: List<io.eidos.zerolayer.data.EquipmentProcEvent> = emptyList(),
    latestProc: io.eidos.zerolayer.data.EquipmentProcEvent? = null,
    onInspectVillain: (io.eidos.zerolayer.data.GameVillainData) -> Unit
) {
    val enemyHp = session?.current_enemy_hp ?: 0
    val villain = remember(enemyId) {
        io.eidos.zerolayer.data.GameData.VILLAINS.find { it.name == enemyId }
            ?: io.eidos.zerolayer.data.GameData.VILLAINS.find {
                val clean1 = it.name.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                val clean2 = enemyId.replace(Regex("[^а-яА-Яa-zA-Z0-9]"), "").lowercase()
                clean1.isNotEmpty() && clean2.isNotEmpty() && (clean1.contains(clean2) || clean2.contains(clean1))
            }
            ?: io.eidos.zerolayer.data.GameVillainData(
                id = 9999,
                name = enemyId,
                level = ((session?.depth ?: 0) / 50) + 1,
                hp = maxOf(10, enemyHp),
                atk = 18,
                def = 5,
                xp = 50,
                coin = 30,
                description = "Искаженный фантом, затерянный в коде Нулевого Слоя.",
                image = "monster_1"
            )
    }

    var initialMaxHp by remember(enemyId) { mutableIntStateOf(maxOf(villain.hp, enemyHp)) }
    if (enemyHp > initialMaxHp) {
        initialMaxHp = enemyHp
    }
    val maxEnemyHp = maxOf(1, initialMaxHp)
    val currentEnemyHpClamped = enemyHp.coerceIn(0, maxEnemyHp)
    val hpPct = (currentEnemyHpClamped * 100 / maxEnemyHp)

    val enemyImageName = villain.image.takeIf { it.isNotBlank() } ?: remember(villain.name) {
        "villain_" + villain.name
            .replace("🦠", "").replace("👻", "").replace("🚁", "").replace("💣", "")
            .replace("⛏", "").replace("🐉", "").replace("❌", "").replace("🗡", "")
            .replace("🧠", "").replace("⬛", "").replace("💀", "").replace("🏗", "")
            .replace("🍽", "").replace("🛡", "").replace("⚛️", "").replace("🤖", "")
            .replace("🌌", "").replace("🌀", "").trim()
    }

    val passiveDefMap = remember {
        mapOf(
            "vampire_visor" to ("🩸 ВИЗОР ВАМПИРА" to Color(0xFF00FFCC)),
            "relic_vampire" to ("👑 КОРОНА КРОВИ" to Color(0xFF00FFCC)),
            "architect_mask" to ("🛡️ ЛИЦО АРХИТЕКТОРА" to Color(0xFF00E5FF)),
            "tactical_helmet" to ("⚡ ТАКТИЧЕСКИЙ ШЛЕМ" to Color(0xFF00E5FF)),
            "cyber_halo" to ("✨ КИБЕР-НИМБ" to Color(0xFFFFD700)),
            "aegis" to ("🛡️ ЭГИДА" to Color(0xFF00E5FF)),
            "overclock_crown" to ("⚡ ВЕНЕЦ РАЗГОНА" to Color(0xFFFF0055)),
            "credit_slicer" to ("💳 РЕЗАК КРЕДИТОВ" to Color(0xFFFFD700)),
            "grandfather_paradox" to ("⏳ ПАРАДОКС ДЕДА" to Color(0xFFFF0055)),
            "thermonuclear_shroud" to ("💥 ТЕРМОЯДЕРНЫЙ САВАН" to Color(0xFFFF0055))
        )
    }

    val activeEquippedPassives = remember(equippedItems) {
        equippedItems.mapNotNull { item ->
            passiveDefMap[item.item_id]?.let { (title, color) ->
                Triple(item.item_id, title, color)
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF0A0608).copy(alpha = 0.95f))
            .border(1.dp, EidosRed.copy(alpha = 0.5f), CutCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header: Threat Name & Level Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⚠ ${villain.name.uppercase()}",
                    color = EidosRed,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Box(
                    modifier = Modifier
                        .clip(CutCornerShape(4.dp))
                        .background(EidosRed.copy(alpha = 0.2f))
                        .border(1.dp, EidosRed, CutCornerShape(4.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(
                        "УР ${villain.level}",
                        color = EidosRed,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // --- 👾 TACTICAL ENEMY INTENT TELEGRAPH ---
            val enemyIntent = remember(villain.id, session?.combat_turn) {
                io.eidos.zerolayer.domain.combat.CombatEngine.predictEnemyIntent(villain.id, session?.combat_turn ?: 0)
            }
            val intentBorderColor = when (enemyIntent.type) {
                io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.POWER_CHARGE -> Color(0xFFFF9100)
                io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.SHIELD -> EidosCyan
                io.eidos.zerolayer.domain.combat.CombatEngine.EnemyIntentType.STUNNED -> EidosNeon
                else -> Color(0xFFFF5252)
            }
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 2.dp),
                shape = CutCornerShape(4.dp),
                color = intentBorderColor.copy(alpha = 0.15f),
                border = BorderStroke(1.dp, intentBorderColor)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(enemyIntent.icon, fontSize = 13.sp)
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "НАМЕРЕНИЕ: ${enemyIntent.title}",
                            color = intentBorderColor,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = enemyIntent.description,
                            color = Color.White.copy(alpha = 0.9f),
                            fontSize = 7.5.sp,
                            fontFamily = FontFamily.Monospace,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }

            // 22.dp Micro-Badges Row for Active Passives
            if (activeEquippedPassives.isNotEmpty()) {
                androidx.compose.foundation.lazy.LazyRow(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(22.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    items(activeEquippedPassives.size) { idx ->
                        val (itemId, title, color) = activeEquippedPassives[idx]
                        val isTriggered = activeProcs.any { it.itemName == itemId }
                        val infiniteTransition = rememberInfiniteTransition(label = "pulse_$itemId")
                        val glowAlpha by infiniteTransition.animateFloat(
                            initialValue = 0.35f,
                            targetValue = 1f,
                            animationSpec = infiniteRepeatable(
                                animation = tween(350, easing = LinearEasing),
                                repeatMode = RepeatMode.Reverse
                            ),
                            label = "alpha_$itemId"
                        )
                        val currentBorder = if (isTriggered) color.copy(alpha = glowAlpha) else color.copy(alpha = 0.35f)
                        val currentBg = if (isTriggered) color.copy(alpha = 0.25f * glowAlpha) else Color.Black.copy(alpha = 0.6f)

                        Box(
                            modifier = Modifier
                                .height(20.dp)
                                .padding(horizontal = 2.dp)
                                .clip(CutCornerShape(3.dp))
                                .background(currentBg)
                                .border(1.dp, currentBorder, CutCornerShape(3.dp))
                                .padding(horizontal = 6.dp, vertical = 2.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = title,
                                color = if (isTriggered) color else color.copy(alpha = 0.8f),
                                fontSize = 8.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }

            // Prominent Clickable Monster Art (Takes major center stage, scales to width without cropping)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 140.dp, max = 220.dp)
                    .clip(CutCornerShape(8.dp))
                    .background(Color(0xFF14080B))
                    .border(1.5.dp, EidosRed.copy(alpha = 0.8f), CutCornerShape(8.dp))
                    .clickable { onInspectVillain(villain) },
                contentAlignment = Alignment.Center
            ) {
                EidosImage(
                    resName = enemyImageName,
                    fallbackIcon = Icons.Default.Warning,
                    borderColor = Color.Transparent,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp, vertical = 6.dp)
                )

                // Pop-up animated banner for triggered perk
                androidx.compose.animation.AnimatedVisibility(
                    visible = latestProc != null,
                    enter = slideInVertically(initialOffsetY = { it }) + fadeIn(),
                    exit = slideOutVertically(targetOffsetY = { it }) + fadeOut(),
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 22.dp)
                        .fillMaxWidth()
                ) {
                    latestProc?.let { proc ->
                        val (bannerBg, bannerBorder) = when (proc.colorType) {
                            io.eidos.zerolayer.data.ProcColorType.HEAL_NEON -> Color(0xFF00382B) to Color(0xFF00FFCC)
                            io.eidos.zerolayer.data.ProcColorType.CURSED_RED -> Color(0xFF38000F) to Color(0xFFFF0055)
                            io.eidos.zerolayer.data.ProcColorType.SHIELD_CYAN -> Color(0xFF002B3D) to Color(0xFF00E5FF)
                            io.eidos.zerolayer.data.ProcColorType.GOLD_CRIT -> Color(0xFF3D3200) to Color(0xFFFFD700)
                        }
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(bannerBg.copy(alpha = 0.95f))
                                .border(1.dp, bannerBorder)
                                .padding(vertical = 4.dp, horizontal = 6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = proc.effectText,
                                color = bannerBorder,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                }

                // Bottom Holographic Badge: Tap to Inspect
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .background(Color.Black.copy(alpha = 0.8f))
                        .border(BorderStroke(1.dp, EidosRed.copy(alpha = 0.4f)))
                        .padding(vertical = 3.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "🔍 ДОСЬЕ И ХАРАКТЕРИСТИКИ",
                        color = Color.White.copy(alpha = 0.95f),
                        fontSize = 8.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // High Visibility Health Bar
            AnimatedCyberProgressBar(
                progress = (currentEnemyHpClamped.toFloat() / maxEnemyHp.toFloat()).coerceIn(0f, 1f),
                color = EidosRed,
                label = "ЖИВУЧЕСТЬ ЦЕЛИ // HP",
                valueText = "$currentEnemyHpClamped / $maxEnemyHp HP ($hpPct%)",
                modifier = Modifier.fillMaxWidth()
            )

            // Tactical Stat Comparison Chips
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Enemy stat chip
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0xFF22080E))
                        .border(1.dp, EidosRed.copy(alpha = 0.5f), CutCornerShape(4.dp))
                        .padding(vertical = 4.dp, horizontal = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "ВРАГ: ⚔️ ${villain.atk}  🛡️ ${villain.def}",
                        color = EidosRed,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Player stat chip
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0xFF071922))
                        .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(4.dp))
                        .padding(vertical = 4.dp, horizontal = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "ВЫ: ⚔️ ${player?.attack ?: 10}  🛡️ ${player?.defense ?: 5}",
                        color = EidosCyan,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
fun ExplorationEventCard(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent?,
    onTriggerHack: () -> Unit = {}
) {
    val eventType = session?.next_event_type ?: "INITIALIZING"
    val isAnomaly = session?.current_anomaly_id != null

    val title = when {
        isAnomaly -> "🌀 ОБНАРУЖЕНА АНОМАЛИЯ"
        eventType == "loot" -> "📦 ОБНАРУЖЕН ТАЙНИК"
        else -> "📡 СКАНИРОВАНИЕ СЛОЯ..."
    }

    val description = when {
        isAnomaly -> anomalyData?.text ?: "Сработал протокол безопасности. Целостность сигнала под угрозой."
        eventType == "loot" -> "Зашифрованный контейнер данных излучает слабый сигнал."
        else -> "Нейро-связь стабильна. Продолжение спуска."
    }

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

    val borderColor = if (isAnomaly) Color.Yellow else EidosCyan

    Box(
        modifier = Modifier
            .fillMaxSize()
            .offset(x = if (isAnomaly) glitchOffset.dp else 0.dp)
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF070B10).copy(alpha = 0.95f))
            .border(1.dp, borderColor.copy(alpha = 0.5f), CutCornerShape(8.dp))
            .padding(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                title,
                color = borderColor,
                fontSize = 14.sp,
                fontWeight = FontWeight.Black,
                textAlign = TextAlign.Center,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 1.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            if (eventType == "loot") {
                EidosImage(
                    resName = "raid_chest",
                    fallbackIcon = Icons.Default.Warning,
                    borderColor = EidosNeon,
                    modifier = Modifier
                        .size(80.dp)
                        .clip(CutCornerShape(8.dp))
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "ОБНАРУЖЕНЫ ЦИФРОВЫЕ ОСТАТКИ",
                    color = EidosNeon,
                    fontSize = 11.5.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = onTriggerHack,
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                    border = BorderStroke(1.dp, EidosCyan),
                    shape = CutCornerShape(6.dp)
                ) {
                    Text("⚡ ВЗЛОМАТЬ ТЕРМИНАЛ [ПРОТОКОЛ ПЕРЕХВАТА]", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            } else if (isAnomaly) {
                EidosImage(
                    resName = "raid_anomaly",
                    fallbackIcon = Icons.Default.Info,
                    borderColor = Color.Yellow,
                    modifier = Modifier.size(90.dp)
                )
            } else {
                ZzzCyberSonarRadar(
                    anomalyCount = 1,
                    hasEnemy = false,
                    enemyDistanceM = 29,
                    lootDistanceM = 6,
                    signalStability = session?.signal ?: 94,
                    depthM = session?.depth ?: 1480
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            val displayedDescription = ghostTyping(description, speed = 12L)
            Text(
                displayedDescription,
                color = Color.White.copy(alpha = 0.75f),
                fontSize = 11.5.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.heightIn(min = 36.dp),
                fontFamily = FontFamily.Monospace,
                lineHeight = 15.sp
            )
        }
    }
}

@Composable
fun EventCard(
    session: RaidSession?,
    player: io.eidos.zerolayer.data.Player?,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent?,
    logs: List<GameLog>,
    equippedItems: List<InventoryItem> = emptyList(),
    activeProcs: List<io.eidos.zerolayer.data.EquipmentProcEvent> = emptyList(),
    latestProc: io.eidos.zerolayer.data.EquipmentProcEvent? = null,
    onTriggerHack: () -> Unit = {},
    onInspectVillain: (io.eidos.zerolayer.data.GameVillainData) -> Unit = {}
) {
    val enemyId = session?.current_enemy_id
    if (enemyId != null) {
        CombatArenaCard(
            session = session,
            player = player,
            enemyId = enemyId,
            equippedItems = equippedItems,
            activeProcs = activeProcs,
            latestProc = latestProc,
            onInspectVillain = onInspectVillain
        )
    } else {
        ExplorationEventCard(
            session = session,
            player = player,
            anomalyData = anomalyData,
            onTriggerHack = onTriggerHack
        )
    }
}

@Composable
fun EnemyInspectModal(
    villain: io.eidos.zerolayer.data.GameVillainData,
    onDismiss: () -> Unit
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
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
                    .fillMaxWidth()
                    .wrapContentHeight()
                    .clickable(enabled = false) {}
                    .clip(CutCornerShape(8.dp))
                    .background(Color(0xFF0C0709))
                    .border(1.5.dp, EidosRed, CutCornerShape(8.dp))
                    .padding(16.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "⚡ ДОСЬЕ УГРОЗЫ // БЕЗДНА",
                                color = EidosRed,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                villain.name.uppercase(),
                                color = Color.White,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                        Box(
                            modifier = Modifier
                                .clip(CutCornerShape(4.dp))
                                .background(EidosRed.copy(alpha = 0.2f))
                                .border(1.dp, EidosRed, CutCornerShape(4.dp))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text("УР ${villain.level}", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Large high-res art (190dp)
                    val enemyImageName = villain.image.takeIf { it.isNotBlank() } ?: "monster_1"
                    Box(
                        modifier = Modifier
                            .size(190.dp)
                            .clip(CutCornerShape(8.dp))
                            .background(Color(0xFF14080B))
                            .border(1.5.dp, EidosRed, CutCornerShape(8.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        EidosImage(
                            resName = enemyImageName,
                            fallbackIcon = Icons.Default.Warning,
                            borderColor = Color.Transparent,
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Stats Grid
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .background(Color(0xFF180A0D))
                                .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(4.dp))
                                .padding(6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("ЗДОРОВЬЕ", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                Text("${villain.hp} HP", color = EidosNeon, fontSize = 11.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .background(Color(0xFF180A0D))
                                .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(4.dp))
                                .padding(6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("АТАКА", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                Text("${villain.atk} ATK", color = EidosRed, fontSize = 11.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .background(Color(0xFF180A0D))
                                .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(4.dp))
                                .padding(6.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("ЗАЩИТА", color = Color.Gray, fontSize = 7.5.sp, fontFamily = FontFamily.Monospace)
                                Text("${villain.def} DEF", color = EidosCyan, fontSize = 11.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    // Reward banner
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(Color(0xFF1C1304))
                            .border(1.dp, Color(0xFFFFB300).copy(alpha = 0.5f), CutCornerShape(4.dp))
                            .padding(vertical = 4.dp, horizontal = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("НАГРАДА ЗА УСТРАНЕНИЕ:", color = Color(0xFFFFB300), fontSize = 8.5.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                        Text("+${villain.xp} EXP // +${villain.coin} BIO", color = Color.White, fontSize = 9.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Black)
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Lore
                    Text(
                        villain.description,
                        color = Color(0xFFD0D7DE),
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 15.sp,
                        textAlign = TextAlign.Start,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    // Close Button
                    io.eidos.zerolayer.ui.components.ZzzDangerButton(
                        text = "ЗАКРЫТЬ ДОСЬЕ [X]",
                        onClick = onDismiss,
                        modifier = Modifier.fillMaxWidth(),
                        height = 42.dp
                    )
                }
            }
        }
    }
}

@Composable
fun FullCombatLogModal(
    logs: List<GameLog>,
    onDismiss: () -> Unit
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
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
                    .fillMaxWidth()
                    .height(420.dp)
                    .clickable(enabled = false) {}
                    .clip(CutCornerShape(8.dp))
                    .background(Color(0xFF090D12))
                    .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("ПОЛНЫЙ БОЕВОЙ ЛОГ // ТАКТИКА", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        IconButton(onClick = onDismiss, modifier = Modifier.size(24.dp)) {
                            Text("✕", color = Color.Gray, fontSize = 14.sp)
                        }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Box(modifier = Modifier.weight(1f)) {
                        TerminalLog(logs)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    io.eidos.zerolayer.ui.components.EidosButton(
                        text = "ВЕРНУТЬСЯ В БОЙ",
                        onClick = onDismiss,
                        modifier = Modifier.fillMaxWidth().height(40.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun RaidControls(
    session: RaidSession?,
    player: Player? = null,
    anomalyData: io.eidos.zerolayer.data.GameRepository.AnomalyEvent?,
    inventory: List<InventoryItem> = emptyList(),
    overdriveCharge: Int = 0,
    overchargeTier: Int = 0,
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    onNextStep: () -> Unit,
    onAttack: () -> Unit = onNextStep,
    onAnomalyChoice: (String) -> Unit,
    onOpenInventory: () -> Unit,
    onOpenBuffer: () -> Unit = {},
    onScanSector: () -> Unit = {},
    onDefend: () -> Unit = {},
    onUseAbility: () -> Unit = {},
    onTriggerOverdrive: () -> Unit = {},
    onBoostOvercharge: () -> Unit = {},
    onUseConsumable: (String) -> Unit = {},
    onFlee: () -> Unit = {}
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    val isCombat = session?.current_enemy_id != null
    val isAnomaly = session?.current_anomaly_id != null

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        if (isCombat) {
            // Operator Live Combat Telemetry
            val curHp = player?.hp ?: 100
            val maxHp = maxOf(1, player?.max_hp ?: 100)
            val curEnergy = player?.energy ?: 0
            val maxEnergy = maxOf(1, player?.max_energy ?: 100)

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(CutCornerShape(6.dp))
                    .background(Color(0xFF091219).copy(alpha = 0.9f))
                    .border(1.dp, EidosCyan.copy(alpha = 0.35f), CutCornerShape(6.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp),
                verticalArrangement = Arrangement.spacedBy(3.dp)
            ) {
                EidosStatBar(
                    label = "HP ОПЕРАТОРА",
                    value = curHp,
                    maxValue = maxHp,
                    color = if (curHp < maxHp * 0.3) EidosRed else EidosNeon
                )
                EidosStatBar(
                    label = "ЭНЕРГИЯ (EP)",
                    value = curEnergy,
                    maxValue = maxEnergy,
                    color = EidosCyan
                )
            }

            val isOverdriveReady = overdriveCharge >= 100
            if (isOverdriveReady) {
                Button(
                    onClick = {
                        haptics.criticalHit()
                        audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                        onTriggerOverdrive()
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4A0080)),
                    border = BorderStroke(2.dp, Color(0xFFFFD700)),
                    shape = CutCornerShape(6.dp)
                ) {
                    Text(
                        "⚡ СБРОС ЯДРА (OVERDRIVE) [250% КРИТ // СТАН]",
                        color = Color(0xFFFFE600),
                        fontWeight = FontWeight.Black,
                        fontSize = 11.5.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                AnimatedCyberProgressBar(
                    progress = (overdriveCharge / 100f).coerceIn(0f, 1f),
                    color = EidosCyan,
                    label = "ЗАРЯД ОВЕРДРАЙВА (ЯДРО)",
                    valueText = "$overdriveCharge%",
                    modifier = Modifier.fillMaxWidth()
                )
            }

            val playerEnergy = player?.energy ?: 0
            val hasAbilityEnergy = playerEnergy >= 10
            val factionAbilityTitle = when (player?.faction) {
                "МАТЕРИЯ" -> "ЗОЛОТОЙ ИМПУЛЬС"
                "РАЗУМ" -> "НЕЙРО-ЩИТ"
                "ТЕХНО", "Технократы" -> "КВАНТОВЫЙ ВЗРЫВ"
                "АРХИТЕКТОРЫ" -> "ПРОТОКОЛ УДАЛЕНИЯ"
                else -> "СПЕЦУДАР ЯДРА"
            }

            // QuickUseRow (32.dp) with Available Consumables
            val quickConsumables = listOf(
                Triple("battery", "⚡ БАТАРЕЯ", Color(0xFF00E5FF)),
                Triple("neural_stimulator", "💉 СТИМ", Color(0xFF00E676)),
                Triple("emp_grenade", "💣 ЭМИ", Color(0xFFFF9100)),
                Triple("stealth_spray", "🌫 ТУМАН", Color(0xFFB388FF))
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(32.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                quickConsumables.forEach { (itemId, label, accentColor) ->
                    val qty = inventory.find { it.item_id == itemId }?.quantity ?: 0
                    val isUsable = qty > 0
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                            .clickable(enabled = isUsable) {
                                haptics.click()
                                onUseConsumable(itemId)
                            },
                        shape = CutCornerShape(4.dp),
                        color = if (isUsable) accentColor.copy(alpha = 0.15f) else Color(0xFF101319),
                        border = BorderStroke(
                            1.dp,
                            if (isUsable) accentColor.copy(alpha = 0.6f) else Color.DarkGray.copy(alpha = 0.4f)
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(horizontal = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = label,
                                color = if (isUsable) accentColor else Color.Gray,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Box(
                                modifier = Modifier
                                    .clip(CutCornerShape(2.dp))
                                    .background(if (isUsable) accentColor.copy(alpha = 0.3f) else Color.Transparent)
                                    .padding(horizontal = 3.dp, vertical = 1.dp)
                            ) {
                                Text(
                                    text = "x$qty",
                                    color = if (isUsable) Color.White else Color.Gray,
                                    fontSize = 8.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            }

            // Tactical 2x2 Combat Matrix
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                // Row 1: Attack + Defend
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Button(
                        onClick = {
                            haptics.criticalHit()
                            audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                            onAttack()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF380C14)),
                        border = BorderStroke(1.5.dp, EidosRed),
                        shape = CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("⚔️ АТАКА", color = Color(0xFFFF5252), fontWeight = FontWeight.Black, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                            Text("УДАР (${activeStats?.attack ?: player?.attack ?: 10} ATK)", color = Color.White.copy(alpha = 0.9f), fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Button(
                        onClick = {
                            haptics.step()
                            audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                            onDefend()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D2818)),
                        border = BorderStroke(1.5.dp, EidosNeon),
                        shape = CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("🛡 ЗАЩИТА", color = EidosNeon, fontWeight = FontWeight.Black, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                            Text("БЛОК -60% // +8 EP", color = Color.White.copy(alpha = 0.9f), fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }

                // Row 2: Ability + Flee
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Button(
                        onClick = {
                            haptics.criticalHit()
                            audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                            onUseAbility()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (hasAbilityEnergy) Color(0xFF0A2B38) else Color(0xFF380C14)
                        ),
                        border = BorderStroke(
                            1.5.dp,
                            if (hasAbilityEnergy) EidosCyan else Color(0xFFFF5252)
                        ),
                        shape = CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                if (hasAbilityEnergy) "⚡ НАВЫК [-10 EP]" else "🩸 НАВЫК [-8% HP]",
                                color = if (hasAbilityEnergy) EidosCyan else Color(0xFFFF5252),
                                fontWeight = FontWeight.Black,
                                fontSize = 11.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                "$factionAbilityTitle // ПРОБИТИЕ",
                                color = Color.White.copy(alpha = 0.9f),
                                fontSize = 8.sp,
                                fontFamily = FontFamily.Monospace,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }

                    Button(
                        onClick = {
                            haptics.step()
                            audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                            onFlee()
                        },
                        modifier = Modifier
                            .weight(1f)
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF261906)),
                        border = BorderStroke(1.5.dp, EidosOrange),
                        shape = CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("🏃 ОТХОД", color = EidosOrange, fontWeight = FontWeight.Black, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                            Text("ШАНС 75%", color = Color.White.copy(alpha = 0.9f), fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }
            }
        } else if (isAnomaly && anomalyData != null) {
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
                    border = BorderStroke(1.dp, btnColor),
                    shape = CutCornerShape(4.dp)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(vertical = 4.dp)) {
                        Text(option.text, color = btnColor, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        Text(option.description, color = Color.LightGray, fontSize = 10.sp, textAlign = TextAlign.Center)
                    }
                }
            }
        } else {
            // Overcharge boost button
            if (overchargeTier < io.eidos.zerolayer.domain.combat.CombatEngine.MAX_OVERCHARGE_TIER) {
                Button(
                    onClick = {
                        haptics.glitchPulse()
                        audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
                        onBoostOvercharge()
                    },
                    modifier = Modifier.fillMaxWidth().height(36.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2A1000)),
                    border = BorderStroke(1.dp, EidosOrange),
                    shape = CutCornerShape(6.dp)
                ) {
                    Text(
                        "🔥 ФОРСИРОВАТЬ СИГНАЛ (+50% ЛУТ / +РИСК) [УР ${overchargeTier + 1}/3]",
                        color = EidosOrange,
                        fontWeight = FontWeight.Bold,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // Row 1: Step into Abyss + Scan Sector
            val curEnergy = player?.energy ?: 0
            val hasStepEnergy = curEnergy >= 5
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = {
                        haptics.step()
                        audio.playSound(EidosAudioManager.SoundType.RAID_STEP)
                        onNextStep()
                    },
                    modifier = Modifier.weight(1.3f).height(50.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (hasStepEnergy) Color(0xFF0D2818) else Color(0xFF380C14)
                    ),
                    border = BorderStroke(1.5.dp, if (hasStepEnergy) EidosNeon else Color(0xFFFF5252)),
                    shape = CutCornerShape(8.dp)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            if (hasStepEnergy) "🏃 ШАГ В БЕЗДНУ" else "🩸 КРОВАВЫЙ ШАГ",
                            color = if (hasStepEnergy) EidosNeon else Color(0xFFFF5252),
                            fontWeight = FontWeight.Black,
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            if (hasStepEnergy) "СЕКТОР (-5 EP)" else "ПЕРЕГРУЗКА (-8% HP)",
                            color = Color.LightGray,
                            fontSize = 8.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                Button(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onScanSector()
                    },
                    modifier = Modifier.weight(1f).height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0A2433)),
                    border = BorderStroke(1.dp, EidosCyan),
                    shape = CutCornerShape(8.dp)
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("📡 СКАН СЕКТОРА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        Text("-5 EP (РАЗВЕДКА)", color = Color.LightGray, fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }

            // Row 2: Loot Buffer + Full Inventory (No duplicates!)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onOpenBuffer()
                    },
                    modifier = Modifier.weight(1f).height(40.dp),
                    shape = CutCornerShape(6.dp),
                    colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFF1F1206)),
                    border = BorderStroke(1.dp, Color(0xFFFF9800))
                ) {
                    Text("🎒 БУФЕР ЛУТА", color = Color(0xFFFF9800), fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                }

                OutlinedButton(
                    onClick = {
                        haptics.click()
                        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                        onOpenInventory()
                    },
                    modifier = Modifier.weight(1f).height(40.dp),
                    shape = CutCornerShape(6.dp),
                    colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFF1F080C)),
                    border = BorderStroke(1.dp, EidosRed)
                ) {
                    Text("🛡️ ИНВЕНТАРЬ", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
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
    onSalvageBufferItem: (Int) -> Unit = {},
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
                        itemsList.forEachIndexed { idx, itemId ->
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

                                    Button(
                                        onClick = { onSalvageBufferItem(idx) },
                                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00382B)),
                                        border = BorderStroke(1.dp, EidosNeon),
                                        shape = CutCornerShape(4.dp),
                                        contentPadding = PaddingValues(horizontal = 6.dp, vertical = 2.dp),
                                        modifier = Modifier.height(26.dp)
                                    ) {
                                        Text(
                                            "⚡ +15 EP",
                                            color = EidosNeon,
                                            fontSize = 8.5.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
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
