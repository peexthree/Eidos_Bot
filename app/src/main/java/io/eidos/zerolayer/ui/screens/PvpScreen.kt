package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.activity.compose.BackHandler
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.*
import io.eidos.zerolayer.R
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.theme.ZzzGold
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.CyberSkeletonLoader
import io.eidos.zerolayer.ui.components.VideoBackground
import androidx.compose.ui.draw.alpha
import io.eidos.zerolayer.ui.components.CyberParticleOverlay
import io.eidos.zerolayer.ui.components.ParticlePreset
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PvpScreen(
    player: Player?,
    phantoms: List<SupabasePlayer> = emptyList(),
    onSetupDefense: (PvpProgram, PvpProgram, PvpProgram) -> Unit = { _, _, _ -> },
    onBuyHardware: (HardwareType) -> Unit = {},
    onActivateShield: (Int) -> Unit = {},
    onActivateProxy: (Int) -> Unit = {},
    onSearchTarget: () -> Unit = {},
    onExecuteRaid: (target: SupabasePlayer, programs: List<PvpProgram>, isRevenge: Boolean, onResult: (PvpMatchResult) -> Unit) -> Unit = { _, _, _, _ -> },
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }
    val scope = rememberCoroutineScope()

    var selectedTab by remember { mutableIntStateOf(0) } // 0: Raid, 1: Defense & Deck, 2: Vendetta
    var selectedTarget by remember { mutableStateOf<SupabasePlayer?>(null) }
    var isRevengeRaid by remember { mutableStateOf(false) }

    // Attack setup
    val selectedAttackPrograms = remember { mutableStateListOf<PvpProgram>() }
    var activeDuelResult by remember { mutableStateOf<PvpMatchResult?>(null) }
    var isExecutingRaid by remember { mutableStateOf(false) }
    var currentDuelRoundStep by remember { mutableIntStateOf(0) }

    // Duel presentation phases (pure visual, logic untouched): 0 none, 1 VS screen, 2 rounds reveal, 3 result
    var duelPhase by remember { mutableIntStateOf(0) }
    var revealedRounds by remember { mutableIntStateOf(0) }

    // Defense setup
    var def1 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_1)) }
    var def2 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_2)) }
    var def3 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_3)) }
    var showSearchConfirmDialog by remember { mutableStateOf(false) }

    val amberColor = ZzzGold
    val installedHw = player?.installed_hardware?.split(",")?.filter { it.isNotBlank() } ?: emptyList()

    // Targets list: real Supabase operators only (mock bots removed in favor of honest empty state)
    val validTargets = remember(phantoms, player) {
        val now = System.currentTimeMillis()
        phantoms.filter { it.deviceId != player?.uid?.toString() && it.pvp_proxy_until <= now }
    }

    // Tactical scan skeleton: show loading placeholders for ~1s on first compose
    var isTargetsLoading by remember { mutableStateOf(true) }
    LaunchedEffect(Unit) {
        delay(1000)
        isTargetsLoading = false
    }

    // Duel presentation driver: VS (600ms) -> sequential round reveal -> result (visual only)
    LaunchedEffect(duelPhase, activeDuelResult) {
        val res = activeDuelResult ?: return@LaunchedEffect
        when (duelPhase) {
            1 -> {
                delay(600) // VS screen holds
                duelPhase = 2
            }
            2 -> {
                val total = res.roundResults.size
                for (i in 1..total) {
                    revealedRounds = i
                    haptics.click()
                    delay(550)
                }
                delay(250)
                duelPhase = 3
            }
        }
    }

    BackHandler(enabled = activeDuelResult != null || selectedTarget != null) {
        if (activeDuelResult != null) {
            if (duelPhase < 3) {
                // Back during the presentation just skips ahead to the verdict
                duelPhase = 3
            } else {
                activeDuelResult = null
                duelPhase = 0
                revealedRounds = 0
                selectedTarget = null
                selectedAttackPrograms.clear()
            }
        } else if (selectedTarget != null) {
            selectedTarget = null
            selectedAttackPrograms.clear()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        // Layer 0: Hexagonal Cyber Grid Live Video & PNG Fallback
        VideoBackground(resName = "bg_pvp", modifier = Modifier.fillMaxSize())
        androidx.compose.foundation.Image(
            painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_pvp),
            contentDescription = null,
            modifier = Modifier.fillMaxSize().alpha(0.35f),
            contentScale = androidx.compose.ui.layout.ContentScale.Crop,
            alignment = Alignment.Center
        )
        // Semi-transparent Dark Glass Overlay
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.45f))
        )
        CyberGridOverlay(modifier = Modifier.fillMaxSize())
        CyberParticleOverlay(
            modifier = Modifier.fillMaxSize(),
            preset = if (activeDuelResult != null) ParticlePreset.FORGE_SPARKS else ParticlePreset.ABYSS_DUST
        )

        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text("СЕТЕВЫЕ ВОЙНЫ 2.0 // РЕЙДЫ НА УЗЛЫ", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 15.sp, fontFamily = FontFamily.Monospace)
                            Text("КИБЕР-ДЕКА • ПРОТОКОЛЫ • ВЕНДЕТТА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = {
                            if (selectedTarget != null && activeDuelResult == null) {
                                selectedTarget = null
                                selectedAttackPrograms.clear()
                            } else {
                                onBack()
                            }
                        }) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosRed)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
                )
            },
            containerColor = Color.Transparent
        ) { innerPadding ->
            Column(
                modifier = Modifier
                    .padding(innerPadding)
                    .fillMaxSize()
            ) {
                // Header Status Bar
                Surface(
                    color = EidosGlass,
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.3f)),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("СТАТУС СЕТИ:", color = Color.Gray, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            val shieldActive = (player?.pvp_shield_until ?: 0) > System.currentTimeMillis()
                            val proxyActive = (player?.pvp_proxy_until ?: 0) > System.currentTimeMillis()
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                                if (shieldActive) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_action_defense, size = 12.dp)
                                        Spacer(Modifier.width(3.dp))
                                        Text("ЩИТ АКТИВЕН", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    }
                                } else {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_danger, size = 12.dp)
                                        Spacer(Modifier.width(3.dp))
                                        Text("УЗЕЛ ОТКРЫТ", color = EidosRed, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                                if (proxyActive) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text("•", color = Color.Gray, fontSize = 11.sp)
                                        Spacer(Modifier.width(4.dp))
                                        ZzzIcon(R.drawable.ic_event_unknown, size = 12.dp)
                                        Spacer(Modifier.width(3.dp))
                                        Text("ПРОКСИ", color = EidosNeon, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("БАЛАНС / ПОБЕДЫ:", color = Color.Gray, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text("${player?.biocoin ?: 0} BC • ${player?.wins_pvp ?: 0}W / ${player?.losses_pvp ?: 0}L", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }

                // Tab Selector
                TabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = Color.Black.copy(alpha = 0.50f),
                    contentColor = EidosRed,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0; haptics.click() },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_action_attack, size = 12.dp)
                                Spacer(Modifier.width(4.dp))
                                Text("ВЗЛОМ СЕТИ", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        },
                        selectedContentColor = EidosRed,
                        unselectedContentColor = Color.Gray
                    )
                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1; haptics.click() },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_action_defense, size = 12.dp)
                                Spacer(Modifier.width(4.dp))
                                Text("ДЕКА & ЗАЩИТА", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        },
                        selectedContentColor = EidosCyan,
                        unselectedContentColor = Color.Gray
                    )
                    Tab(
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2; haptics.click() },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_action_blood_overdrive, size = 12.dp)
                                Spacer(Modifier.width(4.dp))
                                Text("ВЕНДЕТТА", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        },
                        selectedContentColor = amberColor,
                        unselectedContentColor = Color.Gray
                    )
                }

                when (selectedTab) {
                    0 -> {
                        // RAID TAB
                        if (selectedTarget == null) {
                            if (isTargetsLoading) {
                                // Skeleton placeholders while the tactical scan resolves
                                Column(
                                    modifier = Modifier.fillMaxSize().padding(12.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    repeat(4) {
                                        CyberSkeletonLoader(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .height(88.dp)
                                        )
                                    }
                                }
                            } else if (validTargets.isEmpty()) {
                                // Honest empty state: no reachable nodes in the network
                                Box(
                                    modifier = Modifier.fillMaxSize().padding(24.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    CyberCornerBracketBox(
                                        bracketSize = 14.dp,
                                        bracketColor = EidosRed.copy(alpha = 0.7f),
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Column(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .background(Color(0xFF0A0F17).copy(alpha = 0.75f))
                                                .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(8.dp))
                                                .padding(24.dp),
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            verticalArrangement = Arrangement.spacedBy(10.dp)
                                        ) {
                                            ZzzIcon(R.drawable.ic_event_unknown, size = 32.dp, tint = EidosRed.copy(alpha = 0.8f))
                                            Text(
                                                "ЦЕЛИ НЕ ОБНАРУЖЕНЫ // СИНХРОНИЗАЦИЯ...",
                                                color = EidosRed,
                                                fontWeight = FontWeight.Bold,
                                                fontSize = 13.sp,
                                                fontFamily = FontFamily.Monospace,
                                                textAlign = TextAlign.Center
                                            )
                                            Text(
                                                "В СЕТИ НЕТ ДОСТУПНЫХ УЗЛОВ ДЛЯ ВЗЛОМА.\nИСПОЛЬЗУЙ СКАНИРОВАНИЕ СЕТИ ИЛИ ВЕРНИСЬ ПОЗЖЕ.",
                                                color = Color.Gray,
                                                fontSize = 10.sp,
                                                lineHeight = 14.sp,
                                                fontFamily = FontFamily.Monospace,
                                                textAlign = TextAlign.Center
                                            )
                                        }
                                    }
                                }
                            } else {
                            // Target Selection
                            LazyColumn(
                                modifier = Modifier.fillMaxSize().padding(12.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                item {
                                    CyberCornerBracketBox(
                                        bracketSize = 14.dp,
                                        bracketColor = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                                    ) {
                                        Surface(
                                            color = Color(0xCC0C1420),
                                            shape = CutCornerShape(6.dp),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, io.eidos.zerolayer.ui.theme.ZzzHotMagenta.copy(alpha = 0.6f)),
                                            modifier = Modifier.fillMaxWidth()
                                        ) {
                                            Box(modifier = Modifier.fillMaxWidth()) {
                                                // Background Art: ui_replace_the_word_2026
                                                androidx.compose.foundation.Image(
                                                    painter = androidx.compose.ui.res.painterResource(id = R.drawable.ui_replace_the_word_2026),
                                                    contentDescription = "Сетевая Война",
                                                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                                                    modifier = Modifier.matchParentSize().alpha(0.35f)
                                                )
                                                Box(
                                                    modifier = Modifier
                                                        .matchParentSize()
                                                        .background(
                                                            androidx.compose.ui.graphics.Brush.verticalGradient(
                                                                listOf(
                                                                    Color.Black.copy(alpha = 0.85f),
                                                                    Color.Black.copy(alpha = 0.55f),
                                                                    Color.Black.copy(alpha = 0.90f)
                                                                )
                                                            )
                                                        )
                                                )

                                                Column(
                                                    modifier = Modifier.padding(12.dp),
                                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                                ) {
                                                    Row(
                                                        modifier = Modifier.fillMaxWidth(),
                                                        horizontalArrangement = Arrangement.SpaceBetween,
                                                        verticalAlignment = Alignment.CenterVertically
                                                    ) {
                                                        Text(
                                                            "СЕТЕВАЯ ВОЙНА // КИБЕР-УЗЛЫ",
                                                            color = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                                            fontWeight = FontWeight.Bold,
                                                            fontSize = 12.sp,
                                                            fontFamily = FontFamily.Monospace
                                                        )
                                                        io.eidos.zerolayer.ui.components.ZzzBadge(
                                                            text = "TACTICAL SCAN",
                                                            color = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                                            textColor = Color.White
                                                        )
                                                    }
                                                    Text(
                                                        "ТАКТИЧЕСКАЯ СЕТКА КИБЕР-УЗЛОВ: Выберите узел цели для неврального взлома. Награда: до 15% BioCoins цели и +100 XP.",
                                                        color = io.eidos.zerolayer.ui.theme.ZzzTextBody,
                                                        fontSize = 11.sp,
                                                        fontFamily = FontFamily.SansSerif
                                                    )
                                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                                        text = "СКАНИРОВАТЬ СЕТЬ (-50 BC)",
                                                        onClick = {
                                                            haptics.click()
                                                            showSearchConfirmDialog = true
                                                        },
                                                        primaryColor = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                                        borderColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                                        textColor = Color.Black,
                                                        modifier = Modifier.fillMaxWidth().height(38.dp)
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }

                                items(validTargets, key = { it.deviceId }) { target ->
                                    CyberCornerBracketBox(
                                        bracketSize = 14.dp,
                                        bracketColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                                    ) {
                                        Surface(
                                            color = Color(0xFF081524).copy(alpha = 0.38f),
                                            shape = CutCornerShape(6.dp),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan.copy(alpha = 0.55f)),
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .clickable {
                                                    selectedTarget = target
                                                    isRevengeRaid = false
                                                    selectedAttackPrograms.clear()
                                                    activeDuelResult = null
                                                    haptics.click()
                                                }
                                        ) {
                                            Column(modifier = Modifier.fillMaxWidth().padding(12.dp)) {
                                                Row(
                                                    modifier = Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.SpaceBetween,
                                                    verticalAlignment = Alignment.CenterVertically
                                                ) {
                                                    Text(
                                                        target.username ?: "Квантовый Узел",
                                                        color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                                        fontWeight = FontWeight.Bold,
                                                        fontSize = 12.sp,
                                                        fontFamily = FontFamily.Monospace
                                                    )
                                                    io.eidos.zerolayer.ui.components.ZzzBadge(
                                                        text = "LVL ${target.level}",
                                                        color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                                        textColor = Color.Black
                                                    )
                                                }

                                                Spacer(modifier = Modifier.height(8.dp))

                                                Row(
                                                    modifier = Modifier.fillMaxWidth(),
                                                    verticalAlignment = Alignment.CenterVertically,
                                                    horizontalArrangement = Arrangement.SpaceBetween
                                                ) {
                                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                                        Box(
                                                            modifier = Modifier
                                                                .size(38.dp)
                                                                .background(Color(0xFF161C2A), CutCornerShape(4.dp))
                                                                .border(1.5.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan, CutCornerShape(4.dp)),
                                                            contentAlignment = Alignment.Center
                                                        ) {
                                                            Icon(Icons.Default.Share, contentDescription = null, tint = io.eidos.zerolayer.ui.theme.ZzzElectricCyan, modifier = Modifier.size(18.dp))
                                                        }
                                                        Spacer(modifier = Modifier.width(10.dp))
                                                        Column {
                                                            Text(target.username ?: "Неизвестный сервер", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.5.sp)
                                                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                                                io.eidos.zerolayer.ui.components.ZzzBadge(
                                                                    text = target.rank.uppercase(),
                                                                    color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                                                    textColor = Color.Black
                                                                )
                                                                Text("DEF: 87%", color = io.eidos.zerolayer.ui.theme.ZzzToxicGreen, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                                            }
                                                        }
                                                    }
                                                    Column(horizontalAlignment = Alignment.End) {
                                                        Text("ХРАНИЛИЩЕ", color = Color.Gray, fontSize = 8.5.sp, fontFamily = FontFamily.Monospace)
                                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                                            Text("${target.biocoins} BC", color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow, fontWeight = FontWeight.ExtraBold, fontSize = 12.5.sp, fontFamily = FontFamily.Monospace)
                                                            Spacer(Modifier.width(3.dp))
                                                            ZzzIcon(R.drawable.ic_res_biocoin, size = 12.dp)
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            }
                        } else if (activeDuelResult == null) {
                            // Program selection for Attack
                            val target = selectedTarget!!
                            Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                                Text("ЦЕЛЬ: ${target.username} (LVL ${target.level})", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                                Text("Сформируйте боевой пакет из 3 программ для атаки:", color = Color.Gray, fontSize = 11.sp)
                                Spacer(modifier = Modifier.height(16.dp))

                                // Chosen programs display
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    for (i in 0..2) {
                                        val prog = selectedAttackPrograms.getOrNull(i)
                                        Box(
                                            modifier = Modifier
                                                .weight(1f)
                                                .height(70.dp)
                                                .background(if (prog != null) prog.color.copy(alpha = 0.2f) else EidosGlass)
                                                .border(1.dp, if (prog != null) prog.color else Color.DarkGray, CutCornerShape(4.dp)),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            if (prog != null) {
                                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                                    Text("РАУНД ${i + 1}", color = Color.Gray, fontSize = 9.sp)
                                                    Text(prog.label, color = prog.color, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                                                }
                                            } else {
                                                Text("СЛОТ ${i + 1}", color = Color.DarkGray, fontSize = 10.sp)
                                            }
                                        }
                                    }
                                }

                                Spacer(modifier = Modifier.height(20.dp))
                                Text("ДОСТУПНЫЕ ПРОГРАММЫ:", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                Spacer(modifier = Modifier.height(8.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    listOf(PvpProgram.BRUTEFORCE, PvpProgram.SHIELD, PvpProgram.STEALTH).forEach { prog ->
                                        Button(
                                            onClick = {
                                                if (selectedAttackPrograms.size < 3) {
                                                    selectedAttackPrograms.add(prog)
                                                    haptics.click()
                                                }
                                            },
                                            modifier = Modifier.weight(1f).height(65.dp),
                                            colors = ButtonDefaults.buttonColors(containerColor = prog.color.copy(alpha = 0.2f)),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, prog.color),
                                            shape = CutCornerShape(4.dp)
                                        ) {
                                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                                Text(prog.label, color = prog.color, fontWeight = FontWeight.Bold, fontSize = 10.sp)
                                                Text(
                                                    when (prog) {
                                                        PvpProgram.BRUTEFORCE -> "> Стелс"
                                                        PvpProgram.SHIELD -> "> Брутфорс"
                                                        PvpProgram.STEALTH -> "> Щит"
                                                    },
                                                    color = Color.LightGray,
                                                    fontSize = 8.sp
                                                )
                                            }
                                        }
                                    }
                                }

                                Spacer(modifier = Modifier.height(16.dp))
                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                    TextButton(onClick = { selectedAttackPrograms.clear(); haptics.click() }) {
                                        Text("СБРОСИТЬ ВЫБОР", color = Color.Gray, fontSize = 11.sp)
                                    }
                                }

                                Spacer(modifier = Modifier.weight(1f))

                                Button(
                                    onClick = {
                                        if (selectedAttackPrograms.size == 3 && !isExecutingRaid) {
                                            isExecutingRaid = true
                                            haptics.click()
                                            audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
                                            onExecuteRaid(target, selectedAttackPrograms.toList(), isRevengeRaid) { res ->
                                                activeDuelResult = res
                                                isExecutingRaid = false
                                                duelPhase = 1
                                                revealedRounds = 0
                                            }
                                        }
                                    },
                                    enabled = selectedAttackPrograms.size == 3 && !isExecutingRaid,
                                    modifier = Modifier.fillMaxWidth().height(52.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.3f), disabledContainerColor = Color.DarkGray.copy(alpha = 0.2f)),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, if (selectedAttackPrograms.size == 3) EidosRed else Color.Gray),
                                    shape = CutCornerShape(4.dp)
                                ) {
                                    Text(
                                        if (isExecutingRaid) "ВЫПОЛНЕНИЕ ВЗЛОМА..." else "ЗАПУСТИТЬ СЕТЕВОЙ ВЗЛОМ",
                                        color = if (selectedAttackPrograms.size == 3) EidosRed else Color.Gray,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 14.sp
                                    )
                                }
                            }
                        } else if (duelPhase == 3) {
                            // Active Duel Result UI (shown after the VS/rounds presentation resolves)
                            val res = activeDuelResult!!
                            Column(
                                modifier = Modifier.fillMaxSize().padding(16.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(
                                    if (res.isWin) "СЕРВЕР ВЗЛОМАН: ПОБЕДА!" else "АТАКА ОТРАЖЕНА: ПОРАЖЕНИЕ",
                                    color = if (res.isWin) EidosNeon else EidosRed,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 18.sp
                                )
                                Text("СЧЕТ: ${res.playerRoundsWon} - ${res.defenderRoundsWon}", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 24.sp)
                                Spacer(modifier = Modifier.height(16.dp))

                                // Rounds breakdown
                                res.roundResults.forEach { r ->
                                    Surface(
                                        color = EidosGlass,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if (r.winner == 1) EidosNeon else if (r.winner == 2) EidosRed else Color.Yellow),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                                    ) {
                                        Row(
                                            modifier = Modifier.padding(10.dp),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text("РАУНД ${r.round}", color = Color.Gray, fontSize = 11.sp)
                                            Text("${r.attackerProgram.label} VS ${r.defenderProgram.label}", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                            Text(
                                                if (r.winner == 1) "ВЫ" else if (r.winner == 2) "ВРАГ" else "НИЧЬЯ",
                                                color = if (r.winner == 1) EidosNeon else if (r.winner == 2) EidosRed else Color.Yellow,
                                                fontWeight = FontWeight.Bold,
                                                fontSize = 11.sp
                                            )
                                        }
                                    }
                                }

                                Spacer(modifier = Modifier.height(20.dp))
                                if (res.isWin) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_res_biocoin, size = 14.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("Похищено: +${res.stolenCoins} BC", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_res_energy, size = 14.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("Получено: +${res.attackerXpGained} XP", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                    }
                                } else {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_danger, size = 14.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("Контрудар: -${res.coinsLost} BC", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                    }
                                }

                                Spacer(modifier = Modifier.weight(1f))

                                Button(
                                    onClick = {
                                        selectedTarget = null
                                        selectedAttackPrograms.clear()
                                        activeDuelResult = null
                                        duelPhase = 0
                                        revealedRounds = 0
                                        haptics.click()
                                    },
                                    modifier = Modifier.fillMaxWidth().height(50.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                    shape = CutCornerShape(4.dp)
                                ) {
                                    Text("ВЕРНУТЬСЯ К СПИСКУ ЦЕЛЕЙ", color = EidosRed, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }

                    1 -> {
                        // DEFENSE & CYBER-DECK TAB
                        LazyColumn(
                            modifier = Modifier.fillMaxSize().padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            item {
                                Surface(
                                    color = EidosCyan.copy(alpha = 0.1f),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.3f)),
                                    shape = CutCornerShape(4.dp)
                                ) {
                                    Column(modifier = Modifier.padding(12.dp)) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            ZzzIcon(R.drawable.ic_action_defense, size = 14.dp)
                                            Spacer(Modifier.width(6.dp))
                                            Text("ПАССИВНАЯ ЗАЩИТНАЯ МАТРИЦА УЗЛА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                        }
                                        Text("Этот порядок программ автоматически срабатывает, когда на ваш сервер нападают другие игроки в оффлайне.", color = Color.Gray, fontSize = 10.sp)
                                        Spacer(modifier = Modifier.height(10.dp))

                                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                            Column(modifier = Modifier.weight(1f)) {
                                                Text("СЛОТ 1", color = Color.Gray, fontSize = 9.sp)
                                                Button(
                                                    onClick = {
                                                        def1 = when (def1) {
                                                            PvpProgram.BRUTEFORCE -> PvpProgram.SHIELD
                                                            PvpProgram.SHIELD -> PvpProgram.STEALTH
                                                            PvpProgram.STEALTH -> PvpProgram.BRUTEFORCE
                                                        }
                                                        onSetupDefense(def1, def2, def3)
                                                        haptics.click()
                                                    },
                                                    colors = ButtonDefaults.buttonColors(containerColor = def1.color.copy(alpha = 0.2f)),
                                                    border = androidx.compose.foundation.BorderStroke(1.dp, def1.color),
                                                    shape = CutCornerShape(4.dp),
                                                    modifier = Modifier.fillMaxWidth()
                                                ) {
                                                    Text(def1.label.take(6), color = def1.color, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                                }
                                            }
                                            Column(modifier = Modifier.weight(1f)) {
                                                Text("СЛОТ 2", color = Color.Gray, fontSize = 9.sp)
                                                Button(
                                                    onClick = {
                                                        def2 = when (def2) {
                                                            PvpProgram.BRUTEFORCE -> PvpProgram.SHIELD
                                                            PvpProgram.SHIELD -> PvpProgram.STEALTH
                                                            PvpProgram.STEALTH -> PvpProgram.BRUTEFORCE
                                                        }
                                                        onSetupDefense(def1, def2, def3)
                                                        haptics.click()
                                                    },
                                                    colors = ButtonDefaults.buttonColors(containerColor = def2.color.copy(alpha = 0.2f)),
                                                    border = androidx.compose.foundation.BorderStroke(1.dp, def2.color),
                                                    shape = CutCornerShape(4.dp),
                                                    modifier = Modifier.fillMaxWidth()
                                                ) {
                                                    Text(def2.label.take(6), color = def2.color, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                                }
                                            }
                                            Column(modifier = Modifier.weight(1f)) {
                                                Text("СЛОТ 3", color = Color.Gray, fontSize = 9.sp)
                                                Button(
                                                    onClick = {
                                                        def3 = when (def3) {
                                                            PvpProgram.BRUTEFORCE -> PvpProgram.SHIELD
                                                            PvpProgram.SHIELD -> PvpProgram.STEALTH
                                                            PvpProgram.STEALTH -> PvpProgram.BRUTEFORCE
                                                        }
                                                        onSetupDefense(def1, def2, def3)
                                                        haptics.click()
                                                    },
                                                    colors = ButtonDefaults.buttonColors(containerColor = def3.color.copy(alpha = 0.2f)),
                                                    border = androidx.compose.foundation.BorderStroke(1.dp, def3.color),
                                                    shape = CutCornerShape(4.dp),
                                                    modifier = Modifier.fillMaxWidth()
                                                ) {
                                                    Text(def3.label.take(6), color = def3.color, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            item {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_action_skill, size = 12.dp)
                                    Spacer(Modifier.width(4.dp))
                                    Text("ЖЕЛЕЗО КИБЕР-ДЕКИ (HARDWARE):", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }
                            }

                            items(HardwareType.values(), key = { it.name }) { hw ->
                                val isInstalled = installedHw.contains(hw.name)
                                Surface(
                                    color = if (isInstalled) EidosCyan.copy(alpha = 0.15f) else EidosGlass,
                                    border = androidx.compose.foundation.BorderStroke(1.dp, if (isInstalled) EidosCyan else Color.DarkGray),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Row(
                                        modifier = Modifier.padding(12.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(hw.label, color = if (isInstalled) EidosCyan else Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                            Text(hw.description, color = Color.Gray, fontSize = 10.sp)
                                        }
                                        if (isInstalled) {
                                            Text("УСТАНОВЛЕНО", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                                        } else {
                                            Button(
                                                onClick = { onBuyHardware(hw); haptics.click() },
                                                colors = ButtonDefaults.buttonColors(containerColor = amberColor.copy(alpha = 0.2f)),
                                                border = androidx.compose.foundation.BorderStroke(1.dp, amberColor),
                                                shape = CutCornerShape(4.dp)
                                            ) {
                                                Text("${hw.priceBc} BC", color = amberColor, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                            }
                                        }
                                    }
                                }
                            }

                            item {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_action_defense, size = 12.dp)
                                    Spacer(Modifier.width(4.dp))
                                    Text("КИБЕР-ЩИТ & МАСКИРОВКА:", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }
                            }

                            item {
                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = { onActivateShield(12); haptics.click() },
                                        modifier = Modifier.weight(1f).height(60.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                        shape = CutCornerShape(4.dp)
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Text("ЩИТ 12 ЧАСОВ", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 10.sp)
                                            Text("300 BC", color = amberColor, fontSize = 10.sp)
                                        }
                                    }
                                    Button(
                                        onClick = { onActivateProxy(24); haptics.click() },
                                        modifier = Modifier.weight(1f).height(60.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.2f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                        shape = CutCornerShape(4.dp)
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Text("ПРОКСИ 24 ЧАСА", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 10.sp)
                                            Text("500 BC", color = amberColor, fontSize = 10.sp)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    2 -> {
                        // VENDETTA TAB
                        LazyColumn(
                            modifier = Modifier.fillMaxSize().padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            item {
                                Surface(
                                    color = EidosRed.copy(alpha = 0.1f),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.3f)),
                                    shape = CutCornerShape(4.dp)
                                ) {
                                    Text(
                                        "ЛОГ ВЕНДЕТТЫ: Список операторов, атаковавших ваш узел. Нажмите КРОВАВАЯ ВЕНДЕТТА для контрудара с бонусом +20% к похищаемому луту!",
                                        color = Color.White,
                                        fontSize = 11.sp,
                                        modifier = Modifier.padding(10.dp)
                                    )
                                }
                            }

                            // Mock/Real vendetta entries
                            items(validTargets.take(3), key = { it.deviceId }) { target ->
                                Surface(
                                    color = EidosGlass,
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.4f)),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Row(
                                        modifier = Modifier.padding(12.dp),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Column {
                                            Text("НАПАДЕНИЕ: ${target.username}", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                            Text("Похищено: 250 BC • LVL ${target.level}", color = Color.Gray, fontSize = 10.sp)
                                        }
                                        Button(
                                            onClick = {
                                                selectedTarget = target
                                                isRevengeRaid = true
                                                selectedTab = 0
                                                selectedAttackPrograms.clear()
                                                activeDuelResult = null
                                                haptics.criticalHit()
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.3f)),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                            shape = CutCornerShape(4.dp)
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                ZzzIcon(R.drawable.ic_action_attack, size = 10.dp)
                                                Spacer(Modifier.width(3.dp))
                                                Text("ВЕНДЕТТА", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold)
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

        // ============ DUEL PRESENTATION OVERLAY (visual only) ============
        if (activeDuelResult != null && duelPhase in 1..2) {
            val res = activeDuelResult!!
            val attackerName = (player?.username ?: "ОПЕРАТОР").uppercase()
            val defenderName = (selectedTarget?.username ?: "НЕИЗВЕСТНЫЙ УЗЕЛ").uppercase()

            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
                    .clickable(enabled = false) { },
                contentAlignment = Alignment.Center
            ) {
                AnimatedContent(
                    targetState = duelPhase,
                    transitionSpec = {
                        (fadeIn(animationSpec = tween(250)) + scaleIn(initialScale = 0.92f, animationSpec = tween(250, easing = FastOutSlowInEasing)))
                            .togetherWith(fadeOut(animationSpec = tween(200)))
                    },
                    label = "duel_phase_transition"
                ) { phase ->
                    when (phase) {
                        1 -> {
                            // PHASE 1: VS SCREEN (attacker vs defender, 600ms)
                            val vsScale = remember { Animatable(0.5f) }
                            LaunchedEffect(Unit) {
                                vsScale.animateTo(1f, tween(300, easing = FastOutSlowInEasing))
                            }
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(16.dp),
                                modifier = Modifier.graphicsLayer {
                                    scaleX = vsScale.value
                                    scaleY = vsScale.value
                                }
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(14.dp)
                                ) {
                                    PvpDuelSideCard(attackerName, EidosCyan, "АТАКУЮЩИЙ")
                                    Text(
                                        "VS",
                                        color = EidosRed,
                                        fontSize = 42.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    PvpDuelSideCard(defenderName, EidosRed, "ЦЕЛЬ")
                                }
                                Text(
                                    "СЕТЕВОЙ ВЗЛОМ // ИНИЦИАЛИЗАЦИЯ ДУЭЛИ",
                                    color = Color.Gray,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace,
                                    letterSpacing = 2.sp,
                                    textAlign = TextAlign.Center
                                )
                            }
                        }
                        else -> {
                            // PHASE 2: ROUND REVEAL (WIN/LOSS/DRAW icons appear sequentially)
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(18.dp)
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                                ) {
                                    Text(attackerName, color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text("VS", color = EidosRed, fontSize = 13.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                                    Text(defenderName, color = EidosRed, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                    res.roundResults.forEachIndexed { index, r ->
                                        AnimatedVisibility(
                                            visible = index < revealedRounds,
                                            enter = scaleIn(initialScale = 0.2f, animationSpec = tween(220, easing = FastOutSlowInEasing)) + fadeIn()
                                        ) {
                                            PvpRoundBadge(winner = r.winner, round = r.round)
                                        }
                                    }
                                }
                                val atkScore = res.roundResults.take(revealedRounds).count { it.winner == 1 }
                                val defScore = res.roundResults.take(revealedRounds).count { it.winner == 2 }
                                Text(
                                    "СЧЁТ $atkScore - $defScore",
                                    color = Color.White,
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            }
        }

        // Verdict flash right after the duel animation resolves (visual only)
        if (activeDuelResult != null && duelPhase == 3) {
            val res = activeDuelResult!!
            val flash = remember { Animatable(0.55f) }
            LaunchedEffect(Unit) {
                flash.animateTo(0f, tween(400, easing = FastOutSlowInEasing))
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background((if (res.isWin) EidosNeon else EidosRed).copy(alpha = flash.value))
                    .clickable(enabled = false) { }
            )
        }
    }

    if (showSearchConfirmDialog) {
        CurrencySpendConfirmDialog(
            itemName = "Сканирование PvP-сети на поиск уязвимого узла",
            cost = 50L,
            currencyName = "BioCoins",
            currentBalance = player?.biocoin ?: 0L,
            onConfirm = {
                showSearchConfirmDialog = false
                onSearchTarget()
            },
            onDismiss = { showSearchConfirmDialog = false }
        )
    }
}

// ==================== DUEL PRESENTATION HELPERS (visual only) ====================

@Composable
private fun PvpDuelSideCard(name: String, accent: Color, tag: String) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .widthIn(max = 118.dp)
            .background(accent.copy(alpha = 0.12f))
            .border(1.5.dp, accent, CutCornerShape(6.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp)
    ) {
        Text(
            tag,
            color = accent.copy(alpha = 0.8f),
            fontSize = 8.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            name,
            color = Color.White,
            fontSize = 12.sp,
            fontWeight = FontWeight.ExtraBold,
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.Center,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
private fun PvpRoundBadge(winner: Int, round: Int) {
    val (label, color) = when (winner) {
        1 -> "WIN" to EidosNeon
        2 -> "LOSS" to EidosRed
        else -> "DRAW" to ZzzGold
    }
    Box(
        modifier = Modifier
            .size(width = 82.dp, height = 58.dp)
            .background(color.copy(alpha = 0.18f))
            .border(1.5.dp, color, CutCornerShape(6.dp)),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                "РАУНД $round",
                color = Color.Gray,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
            Text(
                label,
                color = color,
                fontSize = 14.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}
