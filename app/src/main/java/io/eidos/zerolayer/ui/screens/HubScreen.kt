package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.GameLog
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.GoldenThreadCard
import io.eidos.zerolayer.ui.components.VideoBackground
import io.eidos.zerolayer.ui.components.CyberdeckVisorOverlay
import io.eidos.zerolayer.ui.components.AnimatedCyberProgressBar
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.TerminalTutorialDialog
import io.eidos.zerolayer.ui.theme.ZzzDesignSystem
import io.eidos.zerolayer.ui.components.zzz.ZzzHeaderBadge
import io.eidos.zerolayer.ui.components.zzz.ZzzSegmentedGauge
import io.eidos.zerolayer.ui.components.ShadowBrokerCountdownBadge
import io.eidos.zerolayer.ui.components.premiumCyberClickable
import android.content.Context
import io.eidos.zerolayer.data.DailyQuest
import io.eidos.zerolayer.ui.components.CyberSkeletonLoader
import io.eidos.zerolayer.ui.components.ZzzWindowCard
import io.eidos.zerolayer.ui.components.cyberClickable
import io.eidos.zerolayer.ui.components.cyber3DTilt
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.components.cyberGlitchEffect
import io.eidos.zerolayer.ui.components.CyberGlitchOverlay
import io.eidos.zerolayer.ui.components.animatedResourceText
import io.eidos.zerolayer.ui.components.CyberParticleOverlay
import io.eidos.zerolayer.ui.components.ParticlePreset
import io.eidos.zerolayer.ui.theme.*
import io.eidos.zerolayer.ui.utils.BiometricHelper
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import io.eidos.zerolayer.ui.utils.EidosAmbientSynthesizer
import androidx.fragment.app.FragmentActivity
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import io.eidos.zerolayer.ui.MainViewModel
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.neonGlowPulse

data class EvaLockInfo(
    val title: String,
    val requirement: String,
    val message: String,
    val ctaText: String = "К РЕЙДУ",
    val onCta: () -> Unit
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HubScreen(
    player: Player?,
    onClaimSupplyDrop: () -> Unit,
    onAttackWorldBoss: () -> Unit,
    logs: List<GameLog>,
    onRestoreSignal: () -> Unit,
    onSyncProtocol: () -> Unit,
    onNavigateToInventory: () -> Unit,
    onNavigateToRaid: () -> Unit,
    onNavigateToProfile: () -> Unit,
    onNavigateToForge: () -> Unit,
    onNavigateToShop: () -> Unit,
    onNavigateToPvp: () -> Unit,
    onNavigateToShadowBroker: () -> Unit,
    onNavigateToEidosGates: () -> Unit,
    onNavigateToCodex: () -> Unit = {},
    onBuyMetaUpgrade: (String) -> Unit = {}
) {
    var showSupplyDropDialog by remember { mutableStateOf(false) }
    var showRatingDialog by remember { mutableStateOf(false) }
    var showBossDialog by remember { mutableStateOf(false) }
    var showGuideDialog by remember { mutableStateOf(false) }
    var showShadowShopDialog by remember { mutableStateOf(false) }
    var showBrokerOfflineDialog by remember { mutableStateOf(false) }
    var showMetaTreeDialog by remember { mutableStateOf(false) }
    var showTerminalTutorialDialog by remember { mutableStateOf(false) }
    var evaLockDialogInfo by remember { mutableStateOf<EvaLockInfo?>(null) }

    var currentTimeMs by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        while (true) {
            currentTimeMs = System.currentTimeMillis()
            kotlinx.coroutines.delay(1000L)
        }
    }
    val lastDrop = player?.last_supply_drop ?: 0L
    val cooldownRemainingMs = (lastDrop + 24 * 3600 * 1000L - currentTimeMs).coerceAtLeast(0L)
    val isDepotReady = cooldownRemainingMs == 0L

    val depotCountdownText = remember(cooldownRemainingMs) {
        if (cooldownRemainingMs <= 0L) {
            "ГОТОВО"
        } else {
            val totalSeconds = cooldownRemainingMs / 1000
            val hours = totalSeconds / 3600
            val minutes = (totalSeconds % 3600) / 60
            val seconds = totalSeconds % 60
            if (hours > 0) {
                String.format(java.util.Locale.US, "%02d:%02d:%02d", hours, minutes, seconds)
            } else {
                String.format(java.util.Locale.US, "%02d:%02d", minutes, seconds)
            }
        }
    }

    var isBrokerActive by remember {
        mutableStateOf(ShadowBrokerManager.isBrokerActive(System.currentTimeMillis()) || (player?.is_admin == true))
    }
    LaunchedEffect(player?.is_admin) {
        while (true) {
            isBrokerActive = ShadowBrokerManager.isBrokerActive(System.currentTimeMillis()) || (player?.is_admin == true)
            kotlinx.coroutines.delay(30000)
        }
    }

    val context = LocalContext.current
    val achievementStorage = remember(context) { io.eidos.zerolayer.data.AchievementStorage(context) }
    val unclaimedAchievements = remember(player) { achievementStorage.getUnclaimedCount(player) }
    val haptics = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }
    val activity = context as? FragmentActivity
    val ambientSynth = remember { EidosAmbientSynthesizer.getInstance() }
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            when (event) {
                androidx.lifecycle.Lifecycle.Event.ON_STOP -> ambientSynth.stopAmbientSynth()
                androidx.lifecycle.Lifecycle.Event.ON_START, androidx.lifecycle.Lifecycle.Event.ON_RESUME -> ambientSynth.startAmbientSynth()
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            ambientSynth.stopAmbientSynth()
        }
    }

    // isBrokerActive is updated every 30s to avoid full-screen 1000ms recompositions

    // World Boss and Daily Quests: live state via MainViewModel
    val mainViewModel: MainViewModel = viewModel()
    val worldBossState by mainViewModel.worldBossState.collectAsState()
    val bossTop by mainViewModel.bossTop.collectAsState()
    val dailyQuests by mainViewModel.dailyQuests.collectAsState()
    val unreadRadio by mainViewModel.unreadRadio.collectAsState()
    val audio = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }
    LaunchedEffect(Unit) {
        mainViewModel.refreshWorldBoss()
        mainViewModel.refreshDailyQuests()
        mainViewModel.refreshUnreadRadio()
    }

    // EVA Welcome Back voice greeting (at most once every 10 min)
    LaunchedEffect(Unit) {
        val narrativePrefs = context.getSharedPreferences("eidos_narrative_prefs", Context.MODE_PRIVATE)
        val lastWelcome = narrativePrefs.getLong("last_eva_welcome", 0L)
        val now = System.currentTimeMillis()
        if (now - lastWelcome > 10 * 60 * 1000L) {
            narrativePrefs.edit().putLong("last_eva_welcome", now).apply()
            audio.playEvaHubVoice(io.eidos.zerolayer.ui.utils.EidosAudioManager.EvaHubVoiceType.WELCOME_BACK)
        }
    }

    // Terminal Tutorial is available on-demand via the [ ? ] button on GoldenThreadCard
    val bossHp = worldBossState?.boss_hp ?: 984124510L
    val bossMaxHp = worldBossState?.boss_max_hp ?: 984124510L
    val bossCycle = worldBossState?.cycle ?: 1
    val bossHpPercent = if (bossMaxHp > 0) (bossHp * 100 / bossMaxHp).coerceIn(0L, 100L) else 0L
    val personalDamage = bossTop.firstOrNull { it.username == (player?.username ?: "") }?.total_damage ?: 0L

    CyberdeckVisorOverlay(
        showGrid = true,
        showScanlines = false
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black)
        ) {
        // Layer 0: Cyberpunk gradient / Safe WebP background
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(Color(0xFF0A0B10), Color(0xFF020304))
                    )
                )
        ) {
            VideoBackground(resName = "bg_hub", modifier = Modifier.fillMaxSize())

            // bg_main exists in drawable - painterResource is safe to call directly
            // (Kotlin 2.3 forbids runCatching/try around @Composable invocations)
            val bgPainter = androidx.compose.ui.res.painterResource(id = R.drawable.bg_main)

            if (bgPainter != null) {
                androidx.compose.foundation.Image(
                    painter = bgPainter,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize().alpha(0.25f),
                    contentScale = ContentScale.Crop,
                    alignment = Alignment.Center
                )
            }
        }

        // Layer 1: Darkened Cybernetic Tint Overlay
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(
                            Color.Black.copy(alpha = 0.85f),
                            Color.Black.copy(alpha = 0.60f),
                            Color.Black.copy(alpha = 0.90f)
                        )
                    )
                )
        )

        // Cybernetic Grid & Scanline Background
        CyberGridOverlay()

        // 60/120 FPS Ambient Code Particle Dust Overlay
        CyberParticleOverlay(preset = ParticlePreset.ABYSS_DUST)

        // Layer 2: Main Responsive Content Layout
        Scaffold(
            containerColor = Color.Transparent
        ) { innerPadding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .statusBarsPadding()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // 1. TOP OPERATOR HEADER (Avatar with Orbital Rings + Live Gauges & Resource Pills)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 2.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Left: Holographic Avatar with Orbit Rings + Online status & Faction
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.width(96.dp)
                    ) {
                        Box {
                            HolographicOrbitalAvatar(
                                level = player?.level ?: 1,
                                onClick = onNavigateToProfile
                            )
                            // А4 UX: бейдж непрочитанных радио-передач и несобранных наград
                            val totalPendingBadges = unreadRadio + unclaimedAchievements
                            if (totalPendingBadges > 0) {
                                Box(
                                    modifier = Modifier
                                        .align(Alignment.TopEnd)
                                        .background(if (unclaimedAchievements > 0) io.eidos.zerolayer.ui.theme.ZzzAcidYellow else Color(0xFFE53935), androidx.compose.foundation.shape.CircleShape)
                                        .border(1.dp, Color.Black, androidx.compose.foundation.shape.CircleShape)
                                        .padding(horizontal = 5.dp, vertical = 1.dp)
                                ) {
                                    Text(
                                        text = totalPendingBadges.toString(),
                                        color = Color.Black,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Black
                                    )
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Text(
                                text = player?.username ?: "p1x3",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .clip(CircleShape)
                                    .background(ZzzNeonGreen)
                            )
                            Spacer(modifier = Modifier.width(2.dp))
                            Text(
                                text = "ONLINE",
                                color = Color(0xFF00FFF6),
                                fontSize = 8.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Spacer(modifier = Modifier.height(2.dp))
                        val factionText = if (player?.faction.isNullOrBlank() || player?.faction == "NONE") {
                            "РАНГ: НЕОФИТ // АВТОНОМНЫЙ"
                        } else {
                            "ФРАКЦИЯ: ${player?.faction} // СИНХРОНИЗИРОВАН"
                        }
                        Text(
                            text = factionText,
                            color = Color(0xFF7DE6F5),
                            fontSize = 7.5.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.SemiBold,
                            textAlign = TextAlign.Center,
                            lineHeight = 9.sp
                        )
                    }

                    // Right: Sci-Fi Gauges and Resource Pills
                    Column(
                        modifier = Modifier.weight(1f),
                        verticalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        // Signal Stability Bar (Magenta/Pink neon with exact HP)
                        CyberTopGaugeBar(
                            label = "СИГНАЛ // [${player?.hp ?: 100} / ${player?.max_hp ?: 100} HP]",
                            current = player?.hp ?: 100,
                            max = player?.max_hp ?: 100,
                            barColor = Color(0xFFFF007F),
                            bgColor = Color(0xFF280718)
                        )

                        // Energy Gauge Bar (Green neon with exact EP)
                        CyberTopGaugeBar(
                            label = "ЭНЕРГИЯ ЯДРА // [${player?.energy ?: 100} / ${player?.max_energy ?: 100} EP]",
                            current = player?.energy ?: 100,
                            max = player?.max_energy ?: 100,
                            barColor = ZzzNeonGreen,
                            bgColor = Color(0xFF082218)
                        )

                        Spacer(modifier = Modifier.height(2.dp))

                        // 3 Resource Pills Row: BioCoins, Rank/Level, Quick Inventory button
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            CyberResourcePill(
                                iconText = "🪙",
                                valueText = "${player?.biocoin ?: 0} BC",
                                accentColor = ZzzGold,
                                modifier = Modifier.weight(1.2f)
                            )
                            CyberResourcePill(
                                iconText = "💠",
                                valueText = if ((player?.level ?: 1) > 1) "LVL ${player?.level}" else "НЕОФИТ",
                                accentColor = ZzzCyanBright,
                                modifier = Modifier.weight(1f)
                            )
                            CyberResourcePill(
                                iconText = "🎒",
                                valueText = "РЮКЗАК",
                                accentColor = Color(0xFFFF2A85),
                                onClick = onNavigateToInventory,
                                modifier = Modifier.weight(1.1f)
                            )
                        }
                    }
                }

                // 2. CENTRAL SCI-FI TITLE WITH ACCENT SLASHES
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "EIDOS: CHRONICLES",
                        color = ZzzCyanBright,
                        fontSize = 11.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 2.5.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "///",
                            color = ZzzCyanBright,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "CYBER HUB",
                            color = ZzzGold,
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.SansSerif,
                            letterSpacing = 2.sp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "///",
                            color = ZzzCyanBright,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                // 3. DEPOT SYNCHRONIZATION CARD (Daily Supply Drop)
                CyberDepotSyncBanner(
                    isDepotReady = isDepotReady,
                    depotCountdownText = depotCountdownText,
                    onClick = {
                        if (isDepotReady) {
                            audio.playEvaHubVoice(io.eidos.zerolayer.ui.utils.EidosAudioManager.EvaHubVoiceType.DEPOT_READY)
                        }
                        showSupplyDropDialog = true
                    }
                )

                // GOLDEN THREAD DIRECTIVE
                GoldenThreadCard(
                    player = player,
                    onNavigate = { screen ->
                        when (screen) {
                            "raid" -> onNavigateToRaid()
                            "forge" -> onNavigateToForge()
                            "codex" -> onNavigateToCodex()
                            "shop" -> onNavigateToShop()
                            "pvp" -> onNavigateToPvp()
                            "broker" -> onNavigateToShadowBroker()
                            "gates" -> onNavigateToEidosGates()
                            "inventory" -> onNavigateToInventory()
                        }
                    },
                    onOpenTutorial = { showTerminalTutorialDialog = true }
                )

                // 4. MAIN CENTRAL CTA BUTTON: RAID ENTRY WITH HAZARD STRIPES
                val isFirstRaid = (player?.raids_done ?: 0) == 0
                CyberHazardRaidButton(
                    onClick = onNavigateToRaid,
                    text = if (isFirstRaid) "/// >>> НАЧАТЬ ПЕРВЫЙ РЕЙД (ЦЕЛЬ: 100м) >>> ///" else "/// >>> СПУСК В НУЛЕВОЙ СЛОЙ >>> ///",
                    isHighlighted = isFirstRaid
                )

                // 5. TACTICAL OPERATIONS 2X2 GRID
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .width(3.dp)
                                .height(14.dp)
                                .background(ZzzGold)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "ТАКТИЧЕСКИЕ ОПЕРАЦИИ",
                            color = Color.White,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 0.5.sp
                        )
                    }
                    Text(
                        text = "[GRID-OPS // AUTH]",
                        color = ZzzGold,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    val isForgeUnlocked = (player?.max_depth ?: 0) >= 100 || (player?.raids_done ?: 0) >= 1
                    val isShopUnlocked = (player?.level ?: 1) >= 2
                    val isBrokerUnlocked = (player?.max_depth ?: 0) >= 500 || (player?.is_admin == true)
                    val isGatesUnlocked = (player?.max_depth ?: 0) >= 4000 || (player?.is_admin == true)

                    // Row 1: Forge & Black Market
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        CyberTacticalOpsCard(
                            title = "КУЗНИЦА И СИНТЕЗ",
                            subtitle = if (isForgeUnlocked) "МОДЫ И СИНТЕЗ" else "ДОСТУП: 1-Й РЕЙД (100м)",
                            iconRes = if (isForgeUnlocked) R.drawable.ic_menu_forge else R.drawable.ic_ui_locked,
                            accentColor = if (isForgeUnlocked) Color(0xFFFF2A85) else Color.Gray,
                            onClick = {
                                if (isForgeUnlocked) {
                                    onNavigateToForge()
                                } else {
                                    haptics.click()
                                    evaLockDialogInfo = EvaLockInfo(
                                        title = "КУЗНИЦА И СИНТЕЗ",
                                        requirement = "ДОСТУП: 1-Й РЕЙД (ИЛИ 100м)",
                                        message = "Модуль Кузницы заблокирован протоколами безопасности. Для запуска термо-горна требуются первые трофеи из Бездны. Совершите вылазку в Нулевой Слой на глубину 100м.",
                                        ctaText = "ВХОД В РЕЙД",
                                        onCta = onNavigateToRaid
                                    )
                                }
                            },
                            modifier = Modifier.weight(1f)
                        )
                        CyberTacticalOpsCard(
                            title = "ЧЕРНЫЙ РЫНОК",
                            subtitle = if (isShopUnlocked) "КОНТРАБАНДА" else "ТРЕБУЕТСЯ: УРОВЕНЬ 2",
                            iconRes = if (isShopUnlocked) R.drawable.ic_menu_market else R.drawable.ic_ui_locked,
                            accentColor = if (isShopUnlocked) Color(0xFFA855F7) else Color.Gray,
                            onClick = {
                                if (isShopUnlocked) {
                                    onNavigateToShop()
                                } else {
                                    haptics.click()
                                    evaLockDialogInfo = EvaLockInfo(
                                        title = "ЧЕРНЫЙ РЫНОК",
                                        requirement = "ТРЕБУЕТСЯ: УРОВЕНЬ 2",
                                        message = "Контрабандный терминал требует репутацию проверенного оператора. Достигните 2-го уровня Ядра для открытия защищенных каналов сбыта.",
                                        ctaText = "К РЕЙДУ (ДЛЯ ОПЫТА)",
                                        onCta = onNavigateToRaid
                                    )
                                }
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    // Row 2: PvP Cyber War & Codex
                    val isPvpAvailable = (player?.level ?: 1) >= 4
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        CyberTacticalOpsCard(
                            title = "СЕТЕВАЯ ВОЙНА",
                            subtitle = if (isPvpAvailable) "РЕЙТИНГОВЫЕ БОИ" else "ДОСТУП: РАНГ 4",
                            iconRes = if (isPvpAvailable) R.drawable.ic_action_attack else R.drawable.ic_ui_locked,
                            accentColor = if (isPvpAvailable) ZzzCyanBright else Color.Gray,
                            onClick = {
                                if (isPvpAvailable) {
                                    onNavigateToPvp()
                                } else {
                                    haptics.click()
                                    evaLockDialogInfo = EvaLockInfo(
                                        title = "СЕТЕВАЯ ВОЙНА",
                                        requirement = "ДОСТУП: РАНГ 4",
                                        message = "Сетевые дуэли операторов открываются на 4-м уровне Ядра. Ваша нейро-матрица пока недостаточно стабилизирована для отражения внешних атак.",
                                        ctaText = "ПОВЫСИТЬ РАНГ В РЕЙДЕ",
                                        onCta = onNavigateToRaid
                                    )
                                }
                            },
                            modifier = Modifier.weight(1f)
                        )
                        CyberTacticalOpsCard(
                            title = "КОДЕКС",
                            subtitle = "АРХИВ ЗНАНИЙ",
                            iconRes = R.drawable.ic_menu_codex,
                            accentColor = ZzzGold,
                            onClick = onNavigateToCodex,
                            modifier = Modifier.weight(1f)
                        )
                    }

                    // Optional Broker Row if active
                    if (isBrokerActive) {
                        CyberTacticalOpsCard(
                            title = "ТЕНЕВОЙ БРОКЕР",
                            subtitle = if (isBrokerUnlocked) "РЕДКИЕ ЧИПЫ [ONLINE]" else "СЕКТОР: С 500м",
                            iconRes = if (isBrokerUnlocked) R.drawable.ic_action_scan else R.drawable.ic_ui_locked,
                            accentColor = if (isBrokerUnlocked) ZzzNeonGreen else Color.Gray,
                            onClick = {
                                if (!isBrokerUnlocked) {
                                    haptics.click()
                                    evaLockDialogInfo = EvaLockInfo(
                                        title = "ТЕНЕВОЙ БРОКЕР",
                                        requirement = "СЕКТОР: С 500м",
                                        message = "Теневой Брокер скрывается в глубоких подсетях Нулевого Слоя. Достигните глубины 500м для обнаружения его зашифрованного маяка.",
                                        ctaText = "СПУСК В СЛОЙ",
                                        onCta = onNavigateToRaid
                                    )
                                } else if (activity != null && BiometricHelper.isBiometricAvailable(context)) {
                                    BiometricHelper.authenticateOperator(
                                        activity = activity,
                                        title = "EIDOS // НЕЙРО-ИДЕНТИФИКАЦИЯ",
                                        subtitle = "Подтвердите биометрический профиль для доступа к Теневому Брокеру",
                                        onSuccess = { onNavigateToShadowBroker() },
                                        onError = { onNavigateToShadowBroker() }
                                    )
                                } else {
                                    onNavigateToShadowBroker()
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    // Eidos Gates Row (if unlocked or admin)
                    if (isGatesUnlocked) {
                        CyberTacticalOpsCard(
                            title = "ВРАТА ЭЙДОСА",
                            subtitle = "СИНГУЛЯРНОСТЬ [ОПАСНО]",
                            iconRes = R.drawable.ic_menu_codex,
                            accentColor = Color(0xFFFF4444),
                            onClick = onNavigateToEidosGates,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }

                // 6. DEDICATED WORLD BOSS BANNER
                CyberWorldBossBanner(
                    bossHp = bossHp,
                    bossMaxHp = bossMaxHp,
                    bossCycle = bossCycle,
                    playerDamage = personalDamage,
                    playerLevel = player?.level ?: 1,
                    onClick = { showBossDialog = true }
                )

                // 7. ЕЖЕДНЕВНЫЕ ДИРЕКТИВЫ
                CyberDailyDirectivesCard(
                    dailyQuests = dailyQuests,
                    onClaimQuest = { questId ->
                        haptics.click()
                        audio.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.ITEM_LOOT)
                        mainViewModel.claimDailyQuest(questId)
                    }
                )
            }
        }

        // Layer 3: One-shot glitch flash when the screen first composes (Juice Phase 1)
        val hubGlitchFlash = remember { Animatable(0.85f) }
        LaunchedEffect(Unit) {
            kotlinx.coroutines.delay(120)
            hubGlitchFlash.animateTo(0f, tween(650, easing = FastOutSlowInEasing))
        }
        if (hubGlitchFlash.value > 0.02f) {
            CyberGlitchOverlay(
                intensity = hubGlitchFlash.value,
                modifier = Modifier.fillMaxSize()
            )
        }
    }

    // --- Dialogs ---

    if (showMetaTreeDialog) {
        MetaTreeDialog(
            player = player,
            onDismiss = { showMetaTreeDialog = false },
            onUpgrade = { upgradeType ->
                onBuyMetaUpgrade(upgradeType)
            }
        )
    }

    // 1. Daily Supply Drop Dialog with bg_mind.jpg art header & Live Status
    if (showSupplyDropDialog) {
        androidx.compose.ui.window.Dialog(
            onDismissRequest = { showSupplyDropDialog = false },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
                    .padding(20.dp),
                contentAlignment = Alignment.Center
            ) {
                CyberCornerBracketBox(
                    bracketSize = 18.dp,
                    bracketColor = if (isDepotReady) EidosNeon else EidosCyan,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(CutCornerShape(8.dp))
                            .background(Color(0xFF070B12))
                            .border(1.dp, if (isDepotReady) EidosNeon else EidosCyan.copy(alpha = 0.6f), CutCornerShape(8.dp))
                            .padding(16.dp)
                    ) {
                        // Art Header
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(100.dp)
                                .clip(CutCornerShape(6.dp))
                        ) {
                            androidx.compose.foundation.Image(
                                painter = painterResource(id = R.drawable.bg_mind),
                                contentDescription = "Supply Drop Mind Art",
                                contentScale = ContentScale.Crop,
                                modifier = Modifier.fillMaxSize()
                            )
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(
                                        Brush.verticalGradient(
                                            colors = listOf(Color.Transparent, Color(0xFF070B12))
                                        )
                                    )
                            )
                            Row(
                                modifier = Modifier
                                    .align(Alignment.BottomStart)
                                    .padding(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                ZzzIcon(iconRes = R.drawable.ic_event_chest, size = 16.dp, tint = EidosCyan)
                                Spacer(Modifier.width(6.dp))
                                Text(
                                    "СИНХРОНИЗАЦИЯ ДЕПО // SUPPLY DROP",
                                    color = Color.White,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Black,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        Text(
                            text = "Каждые 24 часа вы можете синхронизировать депо вашего нейро-ядра, чтобы получить припасы из Центрального Хранилища.",
                            color = Color.LightGray,
                            fontSize = 10.5.sp,
                            lineHeight = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        Text(
                            text = "ТЕКУЩИЙ СТАТУС ОПЕРАТОРА:\n" +
                                    "• Оператор: ${player?.username ?: "GUEST"}\n" +
                                    "• Энергия: ${player?.energy ?: 0}/${player?.max_energy ?: 100} EP\n" +
                                    "• Баланс: ${player?.biocoin ?: 0} BC",
                            color = Color.Gray,
                            fontSize = 10.sp,
                            lineHeight = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        Text(
                            text = "СУТОЧНАЯ ПОСТАВКА:\n" +
                                    "• +50 Единиц Энергии Ядра (EP)\n" +
                                    "• 1х Случайный Расходник / Ресурс",
                            color = EidosNeon,
                            fontSize = 10.5.sp,
                            fontWeight = FontWeight.Bold,
                            lineHeight = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )

                        Spacer(modifier = Modifier.height(14.dp))

                        // Status Countdown
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(CutCornerShape(4.dp))
                                .background(Color(0xFF0C141F))
                                .border(0.8.dp, if (isDepotReady) EidosNeon else Color.Gray, CutCornerShape(4.dp))
                                .padding(8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("ТАЙМЕР ДОСТУПНОСТИ:", color = Color.Gray, fontSize = 9.5.sp, fontFamily = FontFamily.Monospace)
                            Text(depotCountdownText, color = if (isDepotReady) EidosNeon else ZzzGold, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedButton(
                                onClick = { showSupplyDropDialog = false },
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("ОТМЕНА", color = Color.Gray, fontSize = 10.5.sp, fontFamily = FontFamily.Monospace)
                            }
                            Button(
                                onClick = {
                                    if (isDepotReady) {
                                        onClaimSupplyDrop()
                                        onRestoreSignal()
                                        onSyncProtocol()
                                    }
                                    showSupplyDropDialog = false
                                },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (isDepotReady) EidosNeon else Color.DarkGray
                                ),
                                shape = CutCornerShape(4.dp),
                                enabled = isDepotReady,
                                modifier = Modifier.weight(1.5f)
                            ) {
                                Text(
                                    if (isDepotReady) "СИНХРОНИЗИРОВАТЬ" else "ПЕРЕЗАРЯДКА...",
                                    color = if (isDepotReady) Color.Black else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    // 2. Season Rating Dialog ("РЕЙТИНГ ОПЕРАТОРОВ")
    if (showRatingDialog) {
        AlertDialog(
            onDismissRequest = { showRatingDialog = false },
            title = {
                Text(
                    "РЕЙТИНГ НЕЙРО-ЛИГИ // СЕЗОН 30 ДНЕЙ",
                    color = EidosCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )
            },
            text = {
                Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                    Text(
                        text = "Длительность сезона - 30 дней. По завершении сезона Топ-10 Операторов рейтинга получают реликвию Красного тира (relic_vampire / relic_speed) и эксклюзивную неоновую статус-ауру профиля!",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "ТАБЛИЦА ЛИДЕРОВ (ТОП-10 ОПЕРАТОРОВ):",
                        color = EidosNeon,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    val leaderboard = listOf(
                        Triple("1. NIGHT_CHASER", "15,400 PTS", "АУРА [RED_FIRE] // RELIC_VAMPIRE"),
                        Triple("2. NULL_POINTER", "14,210 PTS", "АУРА [RED_FIRE] // RELIC_SPEED"),
                        Triple("3. LOGIC_BOMB", "13,990 PTS", "АУРА [CYAN_SPARK] // RELIC_VAMPIRE"),
                        Triple("4. GHOST_IN_SHELL", "12,850 PTS", "АУРА [CYAN_SPARK] // RELIC_SPEED"),
                        Triple("5. VOID_WALKER", "12,400 PTS", "АУРА [CYAN_SPARK]"),
                        Triple("6. CODE_RUNNER", "11,950 PTS", "ТОП-10 НАГРАДА"),
                        Triple("7. NEO_OP", "11,500 PTS", "ТОП-10 НАГРАДА"),
                        Triple("8. BUFFER_OVERFLOW", "10,800 PTS", "ТОП-10 НАГРАДА"),
                        Triple("9. DEEP_MIND", "10,200 PTS", "ТОП-10 НАГРАДА"),
                        Triple("10. EIDOS_DEV", "9,900 PTS", "ТОП-10 НАГРАДА")
                    )
                    leaderboard.forEach { (name, pts, reward) ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 3.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(name, color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                Text(reward, color = EidosRed, fontSize = 8.sp, fontFamily = FontFamily.Monospace)
                            }
                            Text(pts, color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "ВАШ ТЕКУЩИЙ СТАТУС:\n" +
                                "• Оператор: ${player?.username ?: "GUEST"}\n" +
                                "• Фракция: ${player?.faction ?: "НЕТ"}\n" +
                                "• Ранг: Оператор Нейросети\n" +
                                "• Позиция: #154 (2,450 PTS)",
                        color = Color.Gray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { showRatingDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ЗАКРЫТЬ Терминал", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF07070F),
            modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(8.dp))
        )
    }

    // 3. World Boss Dialog ("МИРОВОЙ БОСС: EIDOS-CORE")
    if (showBossDialog) {
        AlertDialog(
            onDismissRequest = { showBossDialog = false },
            title = {
                Text(
                    "МИРОВОЙ БОСС: EIDOS-CORE [LIVE-EVENT]",
                    color = EidosRed,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )
            },
            text = {
                Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                    Text(
                        text = "В секторе Zero Void обнаружен гигантский поврежденный суперкомпьютер EIDOS-CORE. Атакуйте его совместно с другими операторами, чтобы заработать BioCoins!",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // HP Bar
                    Text(
                        text = "ЗДОРОВЬЕ EIDOS-CORE: ${String.format(java.util.Locale.US, "%,d", bossHp)} / ${String.format(java.util.Locale.US, "%,d", bossMaxHp)} HP ($bossHpPercent%)",
                        color = EidosRed,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = { if (bossMaxHp > 0) bossHp.toFloat() / bossMaxHp.toFloat() else 0f },
                        color = EidosRed,
                        trackColor = Color.DarkGray,
                        modifier = Modifier.fillMaxWidth().height(8.dp)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "ЦИКЛ ПУЛА: #$bossCycle",
                        color = ZzzGold,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = "ВАША СТАТИСТИКА:\n" +
                                "• Базовый урон (АТK): ${player?.attack ?: 5}\n" +
                                "• Нанесено урона: ${String.format(java.util.Locale.US, "%,d", personalDamage)} HP damage\n" +
                                "• Стоимость атаки: 10 EP",
                        color = Color.Gray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = "ТОП ОПЕРАТОРОВ ПО УРОНУ БОССУ:",
                        color = EidosCyan,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    if (bossTop.isEmpty()) {
                        Text(
                            text = "ВКЛАД ОПЕРАТОРОВ: ПУСТО // БУДЬ ПЕРВЫМ",
                            color = Color.Gray,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    } else {
                        bossTop.forEachIndexed { index, contributor ->
                            val name = contributor.username ?: "UNKNOWN_OP"
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    "${index + 1}. $name",
                                    color = Color.White,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    "${String.format(java.util.Locale.US, "%,d", contributor.total_damage)} HP",
                                    color = EidosRed,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if ((player?.energy ?: 0) >= 10) {
                            onAttackWorldBoss()
                            showBossDialog = false
                        }
                    },
                    enabled = (player?.energy ?: 0) >= 10,
                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed),
                    shape = CutCornerShape(4.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_action_attack, size = 13.dp)
                        Spacer(Modifier.width(4.dp))
                        Text("НАНЕСТИ УДАР (-10 EP)", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { showBossDialog = false }) {
                    Text("ЗАКРЫТЬ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF0F0707),
            modifier = Modifier.border(1.dp, EidosRed.copy(alpha = 0.5f), CutCornerShape(8.dp))
        )
    }

    // 4. Detailed Novice Guide Dialog ("ПОЛНОЕ РУКОВОДСТВО ОПЕРАТОРA")
    if (showGuideDialog) {
        AlertDialog(
            onDismissRequest = { showGuideDialog = false },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.Info, contentDescription = null, tint = EidosCyan)
                    Text(
                        "СПРАВОЧНИК ОПЕРАТОРA // NOVICE PROTOCOL",
                        color = EidosCyan,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .verticalScroll(rememberScrollState())
                        .padding(vertical = 4.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(
                        text = "Добро пожаловать в кибернетическую сеть «ЭЙДОС». Это подробное руководство объясняет все механизмы выживания и развития:",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )

                    // Section 1: Raids & Signal
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F1520)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(4.dp))
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text("1. РЕЙДЫ В НУЛЕВОЙ СЛОЙ (РЕЖИМ ИССЛЕДОВАНИЯ)", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "• Каждый шаг погружает вас глубже в бездну и расходует 15 ед. Энергии.\n" +
                                       "• Во время рейда вы встречаете Врагов, Тайники с лутом и Нейро-Аномалии.\n" +
                                       "• При нулевом Сигнале (HP) ваша нейро-связь рвется, трофеи падают в Могилу, а снаряжение теряет прочность.\n" +
                                       "• Всегда вовремя прожимайте 'Завершить Рейд', чтобы унести добычу в Хаб!",
                                color = Color.LightGray,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    // Section 2: Currency & Items
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F1520)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(4.dp))
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text("2. ЭКОНОМИКА: BIOPCOINS И ОСКОЛКИ ЭЙДОСА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "• BioCoins (BC): Базовая крипто-валюта. Используется для покупки чипов, ремонта и мгновенного взлома.\n" +
                                       "• Осколки Эйдоса: Главный ресурс для улучшения навыков, точечного ремонта и синтеза легендарного экипа.\n" +
                                       "• Добывайте Осколки при дешифровке кластеров, победе над мировым боссом и рециклинге лута.",
                                color = Color.LightGray,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    // Section 3: Forge & Durability
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F1520)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(4.dp))
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text("3. КУЗНЯ И ПРОЧНОСТЬ ЭКИПИРОВКИ", color = Color(0xFFFFCC00), fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "• При боях оружие и броня изнашиваются (-0.5% за удар).\n" +
                                       "• При 0% прочности вещь деактивируется и теряет все боевые статы!\n" +
                                       "• Заходите в Мастерскую (Кузню) для чинки за BioCoins или объединения одинаковых предметов.",
                                color = Color.LightGray,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    // Section 4: Factions & Skills
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F1520)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(4.dp))
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text("4. ФРАКЦИИ И ВЕТКИ НАВЫКОВ", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "• Хакер: Повышает шансы крита, лута и уклонения.\n" +
                                       "• Берсерк: Значительно увеличивает урон, максимальное HP и вампиризм.\n" +
                                       "• Медик: Уменьшает расход энергии в рейдах и удваивает хил аптечек.\n" +
                                       "• Выбирайте фракцию в Профиле для мощных пассивных аур!",
                                color = Color.LightGray,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = { showGuideDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ПРИНЯТЬ И ПРОДОЛЖИТЬ", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF07070F),
            modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(8.dp))
        )
    }

    // 5. Shadow Broker Offline Dialog
    if (showBrokerOfflineDialog) {
        AlertDialog(
            onDismissRequest = { showBrokerOfflineDialog = false },
            containerColor = Color(0xFF0D0814),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.border(2.dp, Color(0xFF9C27B0), CutCornerShape(8.dp)),
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_event_danger, size = 16.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "СИГНАЛ БРОКЕРА ПОТЕРЯН",
                        color = Color(0xFF9C27B0),
                        fontWeight = FontWeight.Black,
                        fontSize = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "ЯДРО EIDOS: Теневой Брокер скрывается в теневых шлюзах от ищейщиков Корпорации!",
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Он подключается к Сети случайно в течение дня ровно на 1 час. До следующего стабильного сеанса связи осталось:",
                        color = Color.Gray,
                        fontSize = 11.sp
                    )
                    ShadowBrokerCountdownBadge(
                        isAdmin = player?.is_admin == true,
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                    )
                    Text(
                        "В момент подключения у него будет 5 редчайших секретных предметов (реликвии, проклятый шмот, чипы), недоступных в обычном магазине!",
                        color = Color.LightGray,
                        fontSize = 10.sp
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { showBrokerOfflineDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF9C27B0)),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ПОНЯТНО", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            }
        )
    }

    // 6. Interactive Terminal Tutorial Dialog
    if (showTerminalTutorialDialog) {
        TerminalTutorialDialog(
            onDismiss = {
                val tutorialPrefs = context.getSharedPreferences("eidos_tutorial_prefs", Context.MODE_PRIVATE)
                tutorialPrefs.edit().putBoolean("tutorial_shown_hub", true).apply()
                showTerminalTutorialDialog = false
            },
            onCompleteTutorial = {
                val tutorialPrefs = context.getSharedPreferences("eidos_tutorial_prefs", Context.MODE_PRIVATE)
                tutorialPrefs.edit().putBoolean("tutorial_shown_hub", true).apply()
                showTerminalTutorialDialog = false
                onClaimSupplyDrop() // Grants bonus supply rewards
            }
        )
    }

    // 7. Tactical Operations EVA Lock Information Dialog
    evaLockDialogInfo?.let { lockInfo ->
        androidx.compose.ui.window.Dialog(
            onDismissRequest = { evaLockDialogInfo = null },
            properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
                    .padding(20.dp),
                contentAlignment = Alignment.Center
            ) {
                io.eidos.zerolayer.ui.components.ZzzWindowCard(
                    title = "// ЕВА-09 :: ДОСТУП ОГРАНИЧЕН",
                    borderColor = Color(0xFFFFB300),
                    modifier = Modifier.fillMaxWidth(0.92f)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Surface(
                            color = Color(0x33FFB300),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFB300))
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 8.dp, vertical = 6.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = lockInfo.title.uppercase(),
                                    color = Color.White,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = lockInfo.requirement,
                                    color = Color(0xFFFFD54F),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Text(
                            text = lockInfo.message,
                            color = Color(0xFFE2E8F0),
                            fontSize = 11.5.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 16.sp
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedButton(
                                onClick = { evaLockDialogInfo = null },
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("ЗАКРЫТЬ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            }
                            Button(
                                onClick = {
                                    evaLockDialogInfo = null
                                    lockInfo.onCta()
                                },
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = ZzzCyanBright),
                                modifier = Modifier.weight(1.4f)
                            ) {
                                Text(
                                    lockInfo.ctaText,
                                    color = Color.Black,
                                    fontSize = 11.sp,
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

@Composable
fun ModuleButton(
    title: String,
    subtitle: String,
    icon: ImageVector,
    color: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val haptics = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }
    val audio = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }

    val isPrimary = title == "ВХОД В БЕЗДНУ" || title == "СЕТЕВАЯ ВОЙНА"

    Card(
        modifier = modifier
            .height(72.dp)
            .then(
                if (isPrimary) {
                    Modifier.neonGlowPulse(
                        glowColor = color,
                        shape = CutCornerShape(6.dp)
                    )
                } else {
                    Modifier.border(1.dp, color.copy(alpha = 0.25f), CutCornerShape(6.dp))
                }
            )
            .clickable {
                haptics.click()
                audio.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.CLICK_CYBER)
                onClick()
            },
        colors = CardDefaults.cardColors(containerColor = EidosGlass),
        shape = CutCornerShape(6.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .background(color.copy(alpha = 0.1f), RoundedCornerShape(4.dp))
                    .border(1.dp, color.copy(alpha = 0.3f), RoundedCornerShape(4.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = color,
                    modifier = Modifier.size(20.dp)
                )
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    color = Color.White,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = subtitle,
                    color = Color.Gray,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Composable
fun ServiceMiniButton(
    title: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    color: Color = EidosCyan
) {
    Card(
        modifier = modifier
            .height(56.dp)
            .border(1.dp, color.copy(alpha = 0.2f), CutCornerShape(4.dp))
            .clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = EidosGlass),
        shape = CutCornerShape(4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color.copy(alpha = 0.8f),
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = title,
                color = Color.White,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                textAlign = TextAlign.Center,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
fun MetaTreeDialog(
    player: Player?,
    onDismiss: () -> Unit,
    onUpgrade: (String) -> Unit
) {
    val signalLvl = player?.meta_signal_level ?: 0
    val keyLvl = player?.meta_key_level ?: 0
    val luckLvl = player?.meta_luck_level ?: 0
    val powerLvl = player?.meta_power_level ?: 0

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Color.Black,
        shape = CutCornerShape(8.dp),
        title = {
            Text(
                "ДЕРЕВО МЕТА-ПРОГРЕССИИ ХАБА",
                color = Color.Yellow,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    "Постоянные нейро-модификации, которые сохраняются между всеми рейдами. Покупаются за Осколки Эйдоса.",
                    color = Color.LightGray,
                    fontSize = 10.sp
                )

                // 1. Signal Level
                MetaUpgradeRow(
                    title = "СИГНАЛ ЯДРА (HP)",
                    desc = "Стартовое HP в рейде: +${signalLvl * 15} HP",
                    level = signalLvl,
                    cost = (signalLvl + 1) * 5,
                    onUpgrade = { onUpgrade("signal") }
                )

                // 2. Key Level
                MetaUpgradeRow(
                    title = "КАРМАННЫЙ КЛЮЧ",
                    desc = if (keyLvl > 0) "Старт рейда с Мастер-Ключом!" else "Старт без ключа",
                    level = keyLvl,
                    cost = (keyLvl + 1) * 5,
                    onUpgrade = { onUpgrade("key") }
                )

                // 3. Luck Level
                MetaUpgradeRow(
                    title = "АУРА УДАЧИ БЕЗДНЫ",
                    desc = "Бонус к Удаче: +${luckLvl * 5}",
                    level = luckLvl,
                    cost = (luckLvl + 1) * 5,
                    onUpgrade = { onUpgrade("luck") }
                )

                // 4. Power Level
                MetaUpgradeRow(
                    title = "ЗАКАЛКА АВАТАРА",
                    desc = "Бонус к Атаке и Защите: +${powerLvl * 5}",
                    level = powerLvl,
                    cost = (powerLvl + 1) * 5,
                    onUpgrade = { onUpgrade("power") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = Color.Yellow),
                shape = CutCornerShape(4.dp)
            ) {
                Text("ЗАКРЫТЬ", color = Color.Black, fontWeight = FontWeight.Bold)
            }
        }
    )
}

@Composable
fun MetaUpgradeRow(
    title: String,
    desc: String,
    level: Int,
    cost: Int,
    onUpgrade: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color.Gray.copy(alpha = 0.3f), CutCornerShape(4.dp)),
        colors = CardDefaults.cardColors(containerColor = EidosGlass),
        shape = CutCornerShape(4.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                Text(desc, color = EidosCyan, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                Text("Уровень: $level", color = Color.Yellow, fontSize = 9.sp)
            }
            Button(
                onClick = onUpgrade,
                colors = ButtonDefaults.buttonColors(containerColor = Color.Yellow.copy(alpha = 0.2f)),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow),
                shape = CutCornerShape(4.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_res_eidos_shard, size = 11.dp)
                    Spacer(Modifier.width(2.dp))
                    Text("+$cost", color = Color.Yellow, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun CyberHubHeader(
    player: io.eidos.zerolayer.data.Player?,
    onProfileClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 10.dp, vertical = 6.dp),
        color = Color(0xFF070D14).copy(alpha = 0.95f),
        shape = CutCornerShape(topStart = 8.dp, bottomEnd = 10.dp),
        border = androidx.compose.foundation.BorderStroke(1.2.dp, EidosCyan.copy(alpha = 0.45f))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 1. УРОВЕНЬ & АВАТАР ПРОФИЛЯ
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.clickable { onProfileClick() }
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .background(Color(0xFF0F2B26), CutCornerShape(6.dp))
                        .border(1.5.dp, EidosCyan, CutCornerShape(6.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${player?.level ?: 1}",
                        color = EidosCyan,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = player?.username ?: "ОПЕРАТОР",
                            color = Color.White,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            maxLines = 1
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Image(
                                painter = painterResource(id = R.drawable.ic_hud_signal_ping),
                                contentDescription = null,
                                modifier = Modifier.size(11.dp)
                            )
                            Spacer(modifier = Modifier.width(3.dp))
                            Text(
                                text = "NET // ONLINE",
                                color = Color(0xFF00FFF6),
                                fontSize = 8.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                    Text(
                        text = "УР ${player?.level ?: 1} // ${player?.faction ?: "НЕОФИТ"}",
                        color = Color(0xFF64748B),
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 2. СИГНАЛ (HP)
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "СИГНАЛ",
                    color = Color(0xFF64748B),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_res_signal_hp, size = 11.dp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.hp ?: 100}",
                        color = if ((player?.hp ?: 100) < 30) EidosRed else Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 3. ЭНЕРГИЯ (EP)
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "ЭНЕРГИЯ",
                    color = Color(0xFF64748B),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_res_energy, size = 11.dp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.energy ?: 100}",
                        color = EidosCyan,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 4. БИОКОИНЫ
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "БАЛАНС",
                    color = Color(0xFF64748B),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_res_biocoin, size = 11.dp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.biocoin ?: 0}",
                        color = EidosGold,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 5. СТРИК
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "СЕРИЯ",
                    color = Color(0xFF64748B),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_res_overdrive, size = 11.dp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.streak ?: 1}Д",
                        color = EidosOrange,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

// ==============================================================================
// 🌟 NEW SCI-FI CYBER HUB COMPONENTS (2026 REDESIGN)
// ==============================================================================

@Composable
fun HolographicOrbitalAvatar(
    level: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "avatarOrbits")
    val rotationAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(14000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "orbitRotation"
    )
    val counterRotationAngle by infiniteTransition.animateFloat(
        initialValue = 360f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(18000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "counterOrbitRotation"
    )

    Box(
        modifier = modifier
            .size(86.dp)
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val center = Offset(size.width / 2f, size.height / 2f)
            val ringRadiusX = size.width * 0.46f
            val ringRadiusY = size.height * 0.22f

            // Orbit Ring 1 (Tilted ~30 deg + rotation)
            rotate(30f + rotationAngle * 0.15f, pivot = center) {
                drawOval(
                    color = Color(0xFF00FFF6).copy(alpha = 0.75f),
                    topLeft = Offset(center.x - ringRadiusX, center.y - ringRadiusY),
                    size = Size(ringRadiusX * 2, ringRadiusY * 2),
                    style = Stroke(width = 1.6f.dp.toPx())
                )
                // Small beacon dot
                drawCircle(
                    color = Color(0xFF00FFF6),
                    radius = 2.5f.dp.toPx(),
                    center = Offset(center.x + ringRadiusX, center.y)
                )
            }

            // Orbit Ring 2 (Tilted -40 deg + counter rotation)
            rotate(-40f + counterRotationAngle * 0.2f, pivot = center) {
                drawOval(
                    color = Color(0xFF00D2FF).copy(alpha = 0.60f),
                    topLeft = Offset(center.x - ringRadiusX * 0.95f, center.y - ringRadiusY * 0.95f),
                    size = Size(ringRadiusX * 1.9f, ringRadiusY * 1.9f),
                    style = Stroke(width = 1.4f.dp.toPx())
                )
                drawCircle(
                    color = Color(0xFF80E5FF),
                    radius = 2.dp.toPx(),
                    center = Offset(center.x - ringRadiusX * 0.95f, center.y)
                )
            }

            // Outer subtle boundary ring
            drawCircle(
                color = Color(0xFF00FFF6).copy(alpha = 0.18f),
                radius = size.width * 0.38f,
                style = Stroke(width = 1.dp.toPx())
            )
        }

        // Inner Avatar Box
        Box(
            modifier = Modifier
                .size(52.dp)
                .clip(CircleShape)
                .background(Color(0xFF0A1520))
                .border(2.dp, Color(0xFF00FFF6), CircleShape),
            contentAlignment = Alignment.Center
        ) {
            EidosImage(
                resName = "lvl_${level.coerceIn(1, 31)}",
                borderColor = Color.Transparent,
                borderWidth = 0.dp,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}

@Composable
fun CyberTopGaugeBar(
    label: String,
    current: Int,
    max: Int,
    barColor: Color,
    bgColor: Color,
    modifier: Modifier = Modifier
) {
    val progress = (current.toFloat() / max.coerceAtLeast(1).toFloat()).coerceIn(0f, 1f)
    val animatedProgress by animateFloatAsState(
        targetValue = progress,
        animationSpec = tween(600, easing = FastOutSlowInEasing),
        label = "gaugeAnim"
    )

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = label,
                color = Color(0xFFB0C4DE),
                fontSize = 8.5.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 0.5.sp
            )
            Text(
                text = "$current/$max",
                color = barColor,
                fontSize = 10.5.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
        }
        Spacer(modifier = Modifier.height(3.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(CutCornerShape(topEnd = 4.dp, bottomEnd = 4.dp))
                .background(bgColor)
                .border(0.6.dp, barColor.copy(alpha = 0.4f), CutCornerShape(topEnd = 4.dp, bottomEnd = 4.dp))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth(animatedProgress)
                    .clip(CutCornerShape(topEnd = 4.dp, bottomEnd = 4.dp))
                    .background(
                        Brush.horizontalGradient(
                            listOf(barColor.copy(alpha = 0.7f), barColor)
                        )
                    )
            )
        }
    }
}

@Composable
fun CyberResourcePill(
    iconText: String,
    valueText: String,
    accentColor: Color,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null
) {
    // Juice Phase 1: animated counter (tween 600ms) + one-shot glitch pulse when the value changes
    val animatedValueText = animatedResourceText(valueText)

    val glitchFlash = remember { Animatable(0f) }
    var lastSeenValue by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(valueText) {
        if (lastSeenValue != null && valueText != lastSeenValue) {
            glitchFlash.snapTo(0.8f)
            glitchFlash.animateTo(0f, tween(500, easing = FastOutSlowInEasing))
        }
        lastSeenValue = valueText
    }

    val pillModifier = if (onClick != null) {
        modifier
            .height(26.dp)
            .clickable { onClick() }
    } else {
        modifier.height(26.dp)
    }

    Surface(
        color = Color(0xF00A131C),
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, accentColor.copy(alpha = 0.85f)),
        modifier = pillModifier
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            accentColor.copy(alpha = 0.15f),
                            Color(0xF5060C14)
                        )
                    )
                )
        ) {
            // Glass top specular line
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(
                        Brush.horizontalGradient(
                            listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.35f),
                                Color.Transparent
                            )
                        )
                    )
            )

            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                Text(
                    text = iconText,
                    fontSize = 10.sp
                )
                Spacer(modifier = Modifier.width(3.dp))
                Text(
                    text = animatedValueText,
                    color = Color(0xFFF1F5F9),
                    fontSize = 9.5.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace
                )
            }

            if (glitchFlash.value > 0.02f) {
                CyberGlitchOverlay(
                    intensity = glitchFlash.value,
                    modifier = Modifier.fillMaxSize()
                )
            }
        }
    }
}

@Composable
fun CyberDepotSyncBanner(
    isDepotReady: Boolean,
    depotCountdownText: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "syncPulse")
    val spinnerAngle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2400, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "syncSpinner"
    )

    val depotBorderColor = if (isDepotReady) ZzzNeonGreen else ZzzCyanBright
    Surface(
        color = Color(0xF2081622),
        shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp, topEnd = 2.dp, bottomStart = 2.dp),
        border = androidx.compose.foundation.BorderStroke(
            1.4.dp,
            depotBorderColor.copy(alpha = 0.85f)
        ),
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            depotBorderColor.copy(alpha = 0.12f),
                            Color(0xFA050E18)
                        )
                    )
                )
        ) {
            // Glass top specular highlight
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.2.dp)
                    .background(
                        Brush.horizontalGradient(
                            listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.35f),
                                depotBorderColor,
                                Color.Transparent
                            )
                        )
                    )
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(Color(0xFF0A2433))
                        .border(1.dp, ZzzCyanBright.copy(alpha = 0.5f), RoundedCornerShape(6.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Canvas(modifier = Modifier.size(20.dp)) {
                        rotate(spinnerAngle) {
                            drawArc(
                                color = if (isDepotReady) ZzzNeonGreen else ZzzCyanBright,
                                startAngle = 0f,
                                sweepAngle = 260f,
                                useCenter = false,
                                style = Stroke(width = 2.5f.dp.toPx())
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.width(10.dp))
                Column {
                    Text(
                        text = "СИНХРОНИЗАЦИЯ ДЕПО",
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = if (isDepotReady) "ПРИПАСЫ ХРАНИЛИЩА ГОТОВЫ" else "ПЕРЕЗАРЯДКА ШЛЮЗА ДЕПО",
                        color = if (isDepotReady) ZzzNeonGreen else Color(0xFF7090A8),
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 0.5.sp
                    )
                }
            }

            Surface(
                color = Color(0xF0050B10),
                shape = RoundedCornerShape(4.dp),
                border = androidx.compose.foundation.BorderStroke(
                    0.8.dp,
                    if (isDepotReady) ZzzNeonGreen else Color(0xFF334A5E)
                )
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (isDepotReady) "ГОТОВО" else "⏱ $depotCountdownText",
                        color = if (isDepotReady) ZzzNeonGreen else ZzzGold,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
        }
    }
}

@Composable
fun CyberHazardRaidButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    text: String = "/// >>> СПУСК В НУЛЕВОЙ СЛОЙ >>> ///",
    isHighlighted: Boolean = false
) {
    val infiniteTransition = rememberInfiniteTransition(label = "hazardBorder")
    val borderAlpha by infiniteTransition.animateFloat(
        initialValue = if (isHighlighted) 0.5f else 0.85f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(if (isHighlighted) 800 else 1800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "hazardBorderAlpha"
    )
    val borderColor = if (isHighlighted) ZzzAcidYellow.copy(alpha = borderAlpha) else ZzzCyanBright
    Surface(
        color = Color(0xEB04121C),
        shape = CutCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(if (isHighlighted) 2.5.dp else 2.dp, borderColor),
        modifier = modifier
            .fillMaxWidth()
            .height(56.dp)
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.fillMaxSize(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            HazardStripesCanvas(
                modifier = Modifier
                    .width(42.dp)
                    .fillMaxHeight()
            )

            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .background(
                        Brush.horizontalGradient(
                            listOf(Color(0xFF051C2A), Color(0xFF0A2B3E), Color(0xFF051C2A))
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = text,
                    color = Color.White,
                    fontSize = 11.5.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp,
                    textAlign = TextAlign.Center
                )
            }

            HazardStripesCanvas(
                modifier = Modifier
                    .width(42.dp)
                    .fillMaxHeight()
            )
        }
    }
}

@Composable
fun HazardStripesCanvas(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier) {
        val stripeWidth = 9.dp.toPx()
        val numStripes = ((size.width + size.height) / (stripeWidth * 2)).toInt() + 4
        drawRect(color = Color(0xFF050505))
        for (i in -4..numStripes) {
            val startX = i * stripeWidth * 2
            val path = Path().apply {
                moveTo(startX, 0f)
                lineTo(startX + stripeWidth, 0f)
                lineTo(startX + stripeWidth - size.height, size.height)
                lineTo(startX - size.height, size.height)
                close()
            }
            drawPath(path, color = ZzzGold)
        }
    }
}

@Composable
fun CyberTacticalOpsCard(
    title: String,
    @androidx.annotation.DrawableRes iconRes: Int,
    accentColor: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    subtitle: String? = null
) {
    val cardShape = CutCornerShape(topStart = 14.dp, bottomEnd = 14.dp, topEnd = 4.dp, bottomStart = 4.dp)
    Surface(
        color = Color(0xF00A101A),
        shape = cardShape,
        border = androidx.compose.foundation.BorderStroke(1.5.dp, accentColor.copy(alpha = 0.85f)),
        modifier = modifier
            .height(118.dp)
            .clickable { onClick() }
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            accentColor.copy(alpha = 0.16f),
                            Color(0xF5090F18),
                            Color(0xFA05080E)
                        )
                    )
                )
        ) {
            // Glass top specular highlight line
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.2.dp)
                    .background(
                        Brush.horizontalGradient(
                            listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.35f),
                                accentColor,
                                Color.Transparent
                            )
                        )
                    )
            )

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(vertical = 12.dp, horizontal = 8.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Box(
                    modifier = Modifier
                        .size(46.dp)
                        .clip(CutCornerShape(6.dp))
                        .background(
                            Brush.verticalGradient(
                                listOf(
                                    Color(0xFF162032),
                                    Color(0xFF0C1320)
                                )
                            )
                        )
                        .border(1.2.dp, accentColor.copy(alpha = 0.75f), CutCornerShape(6.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Image(
                        painter = painterResource(id = iconRes),
                        contentDescription = title,
                        modifier = Modifier.size(28.dp)
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = title.uppercase(),
                        color = Color(0xFFF1F5F9),
                        fontSize = 9.5.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center,
                        lineHeight = 11.5.sp,
                        letterSpacing = 0.5.sp,
                        maxLines = 1
                    )
                    if (subtitle != null) {
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = subtitle,
                            color = accentColor.copy(alpha = 0.95f),
                            fontSize = 7.5.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Center,
                            maxLines = 1
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun CyberWorldBossBanner(
    bossHp: Long,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    bossMaxHp: Long = 984124510L,
    bossCycle: Int = 1,
    playerDamage: Long = 0L,
    playerLevel: Int = 1
) {
    val bossHpPercent = if (bossMaxHp > 0) (bossHp * 100 / bossMaxHp).coerceIn(0L, 100L) else 0L
    Surface(
        color = Color(0xEB160508),
        shape = CutCornerShape(8.dp),
        border = androidx.compose.foundation.BorderStroke(1.6.dp, Color(0xFFFF003C)),
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(68.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color.Black)
                    .border(1.2.dp, Color(0xFFFF003C), RoundedCornerShape(6.dp)),
                contentAlignment = Alignment.Center
            ) {
                EidosImage(
                    resName = "monster_19",
                    borderColor = Color.Transparent,
                    borderWidth = 0.dp,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
                Image(
                    painter = painterResource(id = R.drawable.ic_event_danger),
                    contentDescription = "Danger",
                    modifier = Modifier
                        .size(20.dp)
                        .align(Alignment.TopEnd)
                        .padding(2.dp)
                )
            }

            Column(modifier = Modifier.weight(1f)) {
                // Collective Server Event Tag
                Text(
                    text = "[СЕРВЕРНОЕ СОБЫТИЕ // ОБЩИЙ РЕЙД СЕТИ]",
                    color = ZzzGold,
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "МИРОВОЙ БОСС: EIDOS-CORE",
                    color = Color(0xFFFF003C),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(2.dp))
                val formattedContribution = String.format(java.util.Locale.US, "%,d", playerDamage)
                Text(
                    text = "ВАШ ВКЛАД: $formattedContribution УРОНА | СЕТЬ: ОНЛАЙН",
                    color = Color(0xFFC0A0A0),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace
                )
                if (playerLevel < 3) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "ВНИМАНИЕ: РЕКОМЕНДОВАН 3+ УРОВЕНЬ ЯДРА ДЛЯ АТАК",
                        color = ZzzAcidYellow,
                        fontSize = 7.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(6.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(Color(0xFF28070B))
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxHeight()
                            .fillMaxWidth(
                                (if (bossMaxHp > 0) bossHp.toFloat() / bossMaxHp.toFloat() else 0f).coerceIn(0f, 1f)
                            )
                            .clip(RoundedCornerShape(3.dp))
                            .background(
                                Brush.horizontalGradient(
                                    listOf(Color(0xFFFF003C), ZzzDangerRed)
                                )
                            )
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "HP: ${String.format(java.util.Locale.US, "%,d", bossHp)} / ${String.format(java.util.Locale.US, "%,d", bossMaxHp)} ($bossHpPercent%) ///",
                        color = Color(0xFFFF003C),
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "ЦИКЛ #$bossCycle",
                        color = ZzzGold,
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "[АТАКОВАТЬ]",
                        color = ZzzGold,
                        fontSize = 9.5.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Black
                    )
                }
            }
        }
    }
}

@Composable
fun CyberGridMenuItem(
    title: String,
    @androidx.annotation.DrawableRes iconRes: Int,
    borderColor: Color = ZzzElectricCyan,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    CyberTacticalOpsCard(
        title = title,
        iconRes = iconRes,
        accentColor = borderColor,
        onClick = onClick,
        modifier = modifier
    )
}

@Composable
fun CyberHubBottomBar(
    selectedTab: String = "hub",
    isPvpUnlocked: Boolean = true,
    onTabSelected: (String) -> Unit
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .height(64.dp)
            .border(1.dp, Color(0xFF1E3A34), CutCornerShape(topStart = 12.dp, topEnd = 12.dp)),
        colors = CardDefaults.cardColors(containerColor = Color(0xF2060B0D)),
        shape = CutCornerShape(topStart = 12.dp, topEnd = 12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 4.dp),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            BottomNavItem(
                iconRes = io.eidos.zerolayer.R.drawable.ic_nav_hub,
                label = "ХАБ",
                isSelected = selectedTab == "hub",
                onClick = { onTabSelected("hub") }
            )
            BottomNavItem(
                iconRes = io.eidos.zerolayer.R.drawable.ic_nav_inventory,
                label = "ИНВЕНТАРЬ",
                isSelected = selectedTab == "inventory",
                onClick = { onTabSelected("inventory") }
            )
            BottomNavItem(
                iconRes = io.eidos.zerolayer.R.drawable.ic_nav_matrix,
                label = "БЕЗДНА",
                isSelected = selectedTab == "matrix",
                isHighlight = true,
                onClick = { onTabSelected("matrix") }
            )
            BottomNavItem(
                iconRes = io.eidos.zerolayer.R.drawable.ic_nav_pvp,
                label = if (isPvpUnlocked) "PVP СЕТЬ" else "PVP [УР 4]",
                isSelected = selectedTab == "pvp",
                onClick = {
                    if (isPvpUnlocked) {
                        onTabSelected("pvp")
                    } else {
                        android.widget.Toast.makeText(context, "Сетевая Война доступна строго с 4 уровня!", android.widget.Toast.LENGTH_SHORT).show()
                    }
                }
            )
            BottomNavItem(
                iconRes = io.eidos.zerolayer.R.drawable.ic_nav_settings,
                label = "ПРОФИЛЬ",
                isSelected = selectedTab == "settings",
                onClick = { onTabSelected("settings") }
            )
        }
    }
}

@Composable
private fun BottomNavItem(
    @androidx.annotation.DrawableRes iconRes: Int,
    label: String,
    isSelected: Boolean,
    isHighlight: Boolean = false,
    onClick: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "navPulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    Column(
        modifier = Modifier
            .clickable { onClick() }
            .padding(horizontal = 4.dp, vertical = 2.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .height(34.dp)
                .width(44.dp)
                .then(
                    if (isSelected) {
                        Modifier
                            .background(Color(0xFF00FFF6).copy(alpha = 0.22f), RoundedCornerShape(8.dp))
                            .border(1.2.dp, Color(0xFF00FFF6), RoundedCornerShape(8.dp))
                    } else Modifier
                )
        ) {
            Image(
                painter = painterResource(id = iconRes),
                contentDescription = label,
                modifier = Modifier.size(if (isHighlight) 26.dp else 22.dp),
                alpha = if (isSelected) pulseAlpha else 0.55f
            )
        }
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            color = if (isSelected) Color(0xFF00FFF6) else Color(0xFF708090),
            fontSize = 7.5.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            fontFamily = FontFamily.Monospace,
            maxLines = 1
        )
    }
}

// ============================================================================
// 7. ЕЖЕДНЕВНЫЕ ДИРЕКТИВЫ (DAILY QUESTS)
// ============================================================================

@Composable
fun CyberDailyDirectivesCard(
    dailyQuests: List<DailyQuest>,
    onClaimQuest: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val completedCount = dailyQuests.count { it.isClaimed }
    val totalCount = dailyQuests.size.coerceAtLeast(3)

    ZzzWindowCard(
        title = "ЕЖЕДНЕВНЫЕ ДИРЕКТИВЫ",
        subTitle = "СУТОЧНЫЙ ЦИКЛ // КВАНТОВЫЙ РЕЗОНАНС",
        headerBadge = "$completedCount/$totalCount ВЫПОЛНЕНО",
        borderColor = ZzzCyanBright,
        backgroundColor = Color(0xEB0A121D),
        cornerSize = 10.dp,
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (dailyQuests.isEmpty()) {
                repeat(3) {
                    CyberSkeletonLoader(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                    )
                }
            } else {
                dailyQuests.forEach { quest ->
                    DailyQuestRow(
                        quest = quest,
                        onClaim = { onClaimQuest(quest.id) }
                    )
                }
            }
        }
    }
}

@Composable
private fun DailyQuestRow(
    quest: DailyQuest,
    onClaim: () -> Unit
) {
    val iconRes = when (quest.type) {
        "KILLS" -> R.drawable.ic_action_attack
        "DEPTH" -> R.drawable.ic_event_evac
        "SYNC" -> R.drawable.ic_action_scan
        "SPEND" -> R.drawable.ic_res_biocoin
        "CHEST" -> R.drawable.ic_ui_locked
        else -> R.drawable.ic_event_unknown
    }
    val typeColor = when (quest.type) {
        "KILLS" -> ZzzDangerRed
        "DEPTH" -> ZzzCyanBright
        "SYNC" -> ZzzMint
        "SPEND" -> ZzzGold
        "CHEST" -> ZzzPurple
        else -> ZzzCyanBright
    }

    val progressFraction = if (quest.target > 0) (quest.progress.toFloat() / quest.target.toFloat()).coerceIn(0f, 1f) else 0f
    val isReadyToClaim = quest.progress >= quest.target && !quest.isClaimed

    Surface(
        color = Color(0xFF0F1722),
        shape = CutCornerShape(6.dp),
        border = androidx.compose.foundation.BorderStroke(
            1.dp,
            if (isReadyToClaim) ZzzDesignSystem.VoltYellow else Color(0xFF1E2A3A)
        ),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Icon box
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .clip(CutCornerShape(4.dp))
                    .background(Color.Black)
                    .border(1.dp, typeColor.copy(alpha = 0.8f), CutCornerShape(4.dp)),
                contentAlignment = Alignment.Center
            ) {
                ZzzIcon(iconRes = iconRes, size = 16.dp, tint = typeColor)
            }

            // Info column
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = quest.title,
                        color = if (quest.isClaimed) Color.Gray else Color.White,
                        fontSize = 10.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f, fill = false)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "+${quest.rewardCoins} BC / +${quest.rewardXp} XP",
                        color = if (quest.isClaimed) Color.DarkGray else ZzzGold,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(4.dp))

                // Progress bar row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(5.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(Color(0xFF0A0F15))
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxHeight()
                                .fillMaxWidth(progressFraction)
                                .background(
                                    if (quest.isClaimed) Color.Gray
                                    else if (isReadyToClaim) ZzzDesignSystem.VoltYellow
                                    else typeColor
                                )
                        )
                    }

                    Text(
                        text = "${quest.progress}/${quest.target}",
                        color = if (quest.isClaimed) Color.Gray else Color.LightGray,
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // Button / Status badge
            when {
                quest.isClaimed -> {
                    Surface(
                        color = Color(0xFF14241B),
                        shape = CutCornerShape(4.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF2E5E3D))
                    ) {
                        Text(
                            text = "ПОЛУЧЕНО",
                            color = Color(0xFF6ECB8B),
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 4.dp)
                        )
                    }
                }
                isReadyToClaim -> {
                    Button(
                        onClick = onClaim,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = ZzzDesignSystem.VoltYellow,
                            contentColor = Color.Black
                        ),
                        shape = CutCornerShape(4.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                        modifier = Modifier.height(28.dp)
                    ) {
                        Text(
                            text = "ЗАБРАТЬ",
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
                else -> {
                    Text(
                        text = "${(progressFraction * 100).toInt()}%",
                        color = Color.Gray,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 4.dp)
                    )
                }
            }
        }
    }
}
