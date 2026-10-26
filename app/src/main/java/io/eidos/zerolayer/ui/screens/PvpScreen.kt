package io.eidos.zerolayer.ui.screens

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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.*
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.components.CyberGridOverlay
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

    // Defense setup
    var def1 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_1)) }
    var def2 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_2)) }
    var def3 by remember(player) { mutableStateOf(PvpProgram.fromString(player?.defense_program_3)) }

    val amberColor = Color(0xFFFFB300)
    val installedHw = player?.installed_hardware?.split(",")?.filter { it.isNotBlank() } ?: emptyList()

    // Targets list
    val validTargets = remember(phantoms, player) {
        val list = phantoms.ifEmpty {
            listOf(
                SupabasePlayer(deviceId = "bot1", username = "Phantom_Spectre", level = (player?.level ?: 1) + 1, exp = 300, biocoins = 800, hp = 120, energy = 100, rank = "Ghost", stateVersion = 1, updatedAt = System.currentTimeMillis()),
                SupabasePlayer(deviceId = "bot2", username = "Neon_Viper", level = (player?.level ?: 1), exp = 150, biocoins = 550, hp = 100, energy = 100, rank = "Rogue", stateVersion = 1, updatedAt = System.currentTimeMillis()),
                SupabasePlayer(deviceId = "bot3", username = "NetRunner_Zero", level = (player?.level ?: 1) + 2, exp = 450, biocoins = 1200, hp = 150, energy = 100, rank = "Architect", stateVersion = 1, updatedAt = System.currentTimeMillis())
            )
        }
        val now = System.currentTimeMillis()
        list.filter { it.deviceId != player?.uid?.toString() && it.pvp_proxy_until <= now }
    }

    BackHandler(enabled = activeDuelResult != null || selectedTarget != null) {
        if (activeDuelResult != null) {
            activeDuelResult = null
            selectedTarget = null
            selectedAttackPrograms.clear()
        } else if (selectedTarget != null) {
            selectedTarget = null
            selectedAttackPrograms.clear()
        }
    }

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
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Black
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            // Layer 0: New PNG Background
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_pvp),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = Alignment.Center
            )
            // Dark Overlay
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.82f))
            )

            CyberGridOverlay(modifier = Modifier.fillMaxSize())
            CyberParticleOverlay(
                modifier = Modifier.fillMaxSize(),
                preset = if (activeDuelResult != null) ParticlePreset.FORGE_SPARKS else ParticlePreset.ABYSS_DUST
            )

            Column(modifier = Modifier.fillMaxSize()) {
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
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                if (shieldActive) {
                                    Text("🛡 ЩИТ АКТИВЕН", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                } else {
                                    Text("⚠️ УЗЕЛ ОТКРЫТ", color = EidosRed, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                                if (proxyActive) {
                                    Text("• 🕶 ПРОКСИ", color = EidosNeon, fontSize = 11.sp, fontWeight = FontWeight.Bold)
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
                    containerColor = Color.Black,
                    contentColor = EidosRed,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0; haptics.click() },
                        text = { Text("⚔️ ВЗЛОМ СЕТИ", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                        selectedContentColor = EidosRed,
                        unselectedContentColor = Color.Gray
                    )
                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1; haptics.click() },
                        text = { Text("🛡 ДЕКА & ЗАЩИТА", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                        selectedContentColor = EidosCyan,
                        unselectedContentColor = Color.Gray
                    )
                    Tab(
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2; haptics.click() },
                        text = { Text("🩸 ВЕНДЕТТА", fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                        selectedContentColor = amberColor,
                        unselectedContentColor = Color.Gray
                    )
                }

                when (selectedTab) {
                    0 -> {
                        // RAID TAB
                        if (selectedTarget == null) {
                            // Target Selection
                            LazyColumn(
                                modifier = Modifier.fillMaxSize().padding(12.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                item {
                                    io.eidos.zerolayer.ui.components.ZzzWindowCard(
                                        title = "СЕТЕВАЯ ВОЙНА // КИБЕР-УЗЛЫ",
                                        headerBadge = "TACTICAL SCAN",
                                        borderColor = io.eidos.zerolayer.ui.theme.ZzzHotMagenta,
                                        modifier = Modifier.padding(bottom = 8.dp)
                                    ) {
                                        Text(
                                            "📡 ТАКТИЧЕСКАЯ СЕТКА КИБЕР-УЗЛОВ: Выберите узел цели для неврального взлома. Награда: до 15% BioCoins цели и +100 XP.",
                                            color = io.eidos.zerolayer.ui.theme.ZzzTextBody,
                                            fontSize = 11.5.sp,
                                            fontFamily = FontFamily.SansSerif
                                        )
                                    }
                                }

                                items(validTargets) { target ->
                                    io.eidos.zerolayer.ui.components.ZzzWindowCard(
                                        title = target.username ?: "Квантовый Узел",
                                        headerBadge = "LVL ${target.level}",
                                        borderColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                        modifier = Modifier
                                            .padding(bottom = 8.dp)
                                            .clickable {
                                                selectedTarget = target
                                                isRevengeRaid = false
                                                selectedAttackPrograms.clear()
                                                activeDuelResult = null
                                                haptics.click()
                                            }
                                    ) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.SpaceBetween
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Box(
                                                    modifier = Modifier
                                                        .size(40.dp)
                                                        .background(Color(0xFF161C2A), CutCornerShape(4.dp))
                                                        .border(1.5.dp, io.eidos.zerolayer.ui.theme.ZzzElectricCyan, CutCornerShape(4.dp)),
                                                    contentAlignment = Alignment.Center
                                                ) {
                                                    Icon(Icons.Default.Share, contentDescription = null, tint = io.eidos.zerolayer.ui.theme.ZzzElectricCyan, modifier = Modifier.size(20.dp))
                                                }
                                                Spacer(modifier = Modifier.width(10.dp))
                                                Column {
                                                    Text(target.username ?: "Неизвестный сервер", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp)
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
                                                Text("ХРАНИЛИЩЕ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                                Text("${target.biocoins} BC 🪙", color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
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
                                            haptics.heavy()
                                            onExecuteRaid(target, selectedAttackPrograms.toList(), isRevengeRaid) { res ->
                                                activeDuelResult = res
                                                isExecutingRaid = false
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
                        } else {
                            // Active Duel Result UI
                            val res = activeDuelResult!!
                            Column(
                                modifier = Modifier.fillMaxSize().padding(16.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(
                                    if (res.isWin) "🏆 СЕРВЕР ВЗЛОМАН: ПОБЕДА!" else "☠️ АТАКА ОТРАЖЕНА: ПОРАЖЕНИЕ",
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
                                    Text("💰 Похищено: +${res.stolenCoins} BC", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                    Text("⚡ Получено: +${res.attackerXpGained} XP", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                } else {
                                    Text("💸 Контрудар: -${res.coinsLost} BC", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                }

                                Spacer(modifier = Modifier.weight(1f))

                                Button(
                                    onClick = {
                                        selectedTarget = null
                                        selectedAttackPrograms.clear()
                                        activeDuelResult = null
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
                                        Text("🛡 ПАССИВНАЯ ЗАЩИТНАЯ МАТРИЦА УЗЛА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp)
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
                                Text("💾 ЖЕЛЕЗО КИБЕР-ДЕКИ (HARDWARE):", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                            }

                            items(HardwareType.values()) { hw ->
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
                                Text("🛡 КИБЕР-ЩИТ & МАСКИРОВКА:", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
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
                                        "🩸 ЛОГ ВЕНДЕТТЫ: Список операторов, атаковавших ваш узел. Нажмите КРОВАВАЯ ВЕНДЕТТА для контрудара с бонусом +20% к похищаемому луту!",
                                        color = Color.White,
                                        fontSize = 11.sp,
                                        modifier = Modifier.padding(10.dp)
                                    )
                                }
                            }

                            // Mock/Real vendetta entries
                            items(validTargets.take(3)) { target ->
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
                                            Text("ВЕНДЕТТА ⚔️", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold)
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
}
