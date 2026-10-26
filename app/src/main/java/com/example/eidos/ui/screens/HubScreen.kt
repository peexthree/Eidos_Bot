package com.example.eidos.ui.screens

import androidx.compose.animation.core.*
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
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.R
import com.example.eidos.data.Player
import com.example.eidos.data.GameLog
import com.example.eidos.ui.components.VideoBackground
import com.example.eidos.ui.components.AnimatedCyberProgressBar
import com.example.eidos.ui.components.CyberGridOverlay
import com.example.eidos.ui.components.EidosImage
import com.example.eidos.ui.components.TerminalTutorialDialog
import com.example.eidos.ui.components.RelicShowcaseDialog
import com.example.eidos.ui.components.EarthRelic
import com.example.eidos.ui.components.cyberClickable
import com.example.eidos.ui.components.cyber3DTilt
import com.example.eidos.ui.components.cyberGlitchEffect
import com.example.eidos.ui.components.CyberParticleOverlay
import com.example.eidos.ui.components.ParticlePreset
import com.example.eidos.ui.theme.*
import com.example.eidos.ui.utils.BiometricHelper
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import com.example.eidos.ui.utils.EidosAmbientSynthesizer
import androidx.fragment.app.FragmentActivity
import androidx.compose.ui.platform.LocalContext
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.utils.neonGlowPulse

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
    var showRelicShowcaseDialog by remember { mutableStateOf(false) }
    var activeRelic by remember { mutableStateOf<EarthRelic?>(null) }

    var currentTimeMillis by remember { mutableStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(1000)
            currentTimeMillis = System.currentTimeMillis()
        }
    }

    val context = LocalContext.current
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

    val isBrokerActive = ShadowBrokerManager.isBrokerActive(currentTimeMillis) || (player?.is_admin == true)
    val brokerTimeMs = ShadowBrokerManager.getTimeRemainingMs(currentTimeMillis)
    val brokerTimeStr = ShadowBrokerManager.formatTime(brokerTimeMs)

    // World Boss local state
    var bossHp by remember { mutableStateOf(984124510L) }
    var personalDamage by remember { mutableStateOf(1540200L) }

    // Dynamic scanning line effect
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0.8f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

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
            val bgPainter = runCatching { androidx.compose.ui.res.painterResource(id = R.drawable.bg_main) }.getOrNull()

            if (bgPainter != null) {
                androidx.compose.foundation.Image(
                    painter = bgPainter,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
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

        // ⚛️ 60/120 FPS Ambient Code Particle Dust Overlay
        CyberParticleOverlay(preset = ParticlePreset.ABYSS_DUST)

        // Layer 2: Main Responsive Content Layout
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                CyberHubHeader(
                    player = player,
                    onProfileClick = onNavigateToProfile
                )
            }
        ) { innerPadding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Story Campaign Banner
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, EidosNeon.copy(alpha = 0.6f), CutCornerShape(8.dp))
                        .clickable { onNavigateToCodex() },
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    shape = CutCornerShape(8.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("📚", fontSize = 28.sp, modifier = Modifier.padding(end = 10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "📚 АРХИВ & СПРАВОЧНИК // ARCHIVE HUB",
                                color = EidosNeon,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Книги сюжета, бестиарий монстров, достижения, справочник механик и хроники событий в одном месте!",
                                color = Color.LightGray,
                                fontSize = 10.sp,
                                lineHeight = 13.sp
                            )
                        }
                    }
                }

                // Interactive Onboarding & Relic Showcase Quick Action Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Card(
                        modifier = Modifier
                            .weight(1f)
                            .border(1.dp, EidosCyan, CutCornerShape(8.dp))
                            .clickable { showTerminalTutorialDialog = true },
                        colors = CardDefaults.cardColors(containerColor = EidosGlass),
                        shape = CutCornerShape(8.dp)
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("🌐", fontSize = 18.sp)
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    "ИНСТРУКТАЖ EIDOS",
                                    color = EidosCyan,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "Интерактивное обучение и базовые протоколы",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                lineHeight = 12.sp
                            )
                        }
                    }

                    Card(
                        modifier = Modifier
                            .weight(1f)
                            .border(1.dp, Color.Yellow, CutCornerShape(8.dp))
                            .clickable { showRelicShowcaseDialog = true },
                        colors = CardDefaults.cardColors(containerColor = EidosGlass),
                        shape = CutCornerShape(8.dp)
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("📼", fontSize = 18.sp)
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    "РЕЛИКВИИ ЗЕМЛИ",
                                    color = Color.Yellow,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                if (activeRelic != null) "Резонатор: ${activeRelic?.name}" else "Стойка резонаторов и баффов",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                lineHeight = 12.sp,
                                maxLines = 1
                            )
                        }
                    }
                }

                // Faction and Operator Status Card
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, EidosCyan.copy(alpha = 0.3f), CutCornerShape(8.dp)),
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    shape = CutCornerShape(8.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Circular Avatar Preview
                            Box(
                                modifier = Modifier
                                    .size(54.dp)
                                    .clip(CircleShape)
                                    .border(2.dp, EidosCyan, CircleShape)
                                    .clickable { onNavigateToProfile() },
                                contentAlignment = Alignment.Center
                            ) {
                                EidosImage(
                                    resName = "lvl_${(player?.level ?: 1).coerceIn(1, 30)}",
                                    borderColor = Color.Transparent,
                                    borderWidth = 0.dp,
                                    contentScale = ContentScale.Crop,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }

                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "ОПЕРАТОР: ${player?.username ?: "GUEST_OP"}",
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "ФРАКЦИЯ: ${player?.faction ?: "NONE"}",
                                    color = EidosCyan,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }
                            // Level Badge
                            Box(
                                modifier = Modifier
                                    .background(EidosCyan.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                                    .border(1.dp, EidosCyan, RoundedCornerShape(4.dp))
                                    .padding(horizontal = 8.dp, vertical = 4.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "LVL ${player?.level ?: 1}",
                                    color = EidosCyan,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Black,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        // Stats Grid (Energy & Health Bars)
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            AnimatedCyberProgressBar(
                                progress = (player?.energy ?: 0).toFloat() / (player?.max_energy ?: 100).toFloat(),
                                color = EidosNeon,
                                label = "ЭНЕРГИЯ ПОГРУЖЕНИЯ",
                                valueText = "${player?.energy ?: 0}/${player?.max_energy ?: 100}",
                                modifier = Modifier.weight(1f)
                            )

                            AnimatedCyberProgressBar(
                                progress = (player?.hp ?: 0).toFloat() / (player?.max_hp ?: 100).toFloat(),
                                color = EidosRed,
                                label = "СТАБИЛЬНОСТЬ СИГНАЛА",
                                valueText = "${player?.hp ?: 0}/${player?.max_hp ?: 100}",
                                modifier = Modifier.weight(1f)
                            )
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // Balance row
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "БАЛАНС НЕЙРОСЕТИ:",
                                color = Color.Gray,
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Image(
                                    painter = painterResource(id = R.drawable.ic_biocoin),
                                    contentDescription = "BioCoins",
                                    modifier = Modifier.size(18.dp),
                                    contentScale = ContentScale.Fit
                                )
                                Text(
                                    text = "${player?.biocoin ?: 0} BioCoins",
                                    color = EidosCyan,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Black,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = onSyncProtocol,
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text(
                                    "🧬 СИНХРОНИЗАЦИЯ",
                                    color = EidosNeon,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }

                            Button(
                                onClick = onRestoreSignal,
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text(
                                    "💚 СИГНАЛ",
                                    color = EidosRed,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }

                // Meta-Hub Tree Card
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, Color.Yellow.copy(alpha = 0.6f), CutCornerShape(8.dp))
                        .clickable { showMetaTreeDialog = true },
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    shape = CutCornerShape(8.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("🏛️", fontSize = 24.sp)
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text(
                                    text = "ДЕРЕВО МЕТА-УЛУЧШЕНИЙ ХАБА",
                                    color = Color.Yellow,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "Постоянные баффы за Осколки Эйдоса (Сигнал, Ключи, Удача, Сила)",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                        Icon(imageVector = Icons.Default.ArrowForward, contentDescription = "Open Meta Tree", tint = Color.Yellow)
                    }
                }

                // Primary Events (Daily Supply Drop & World Boss)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Daily Supply Card
                    Card(
                        modifier = Modifier
                            .weight(1f)
                            .height(100.dp)
                            .border(1.dp, EidosNeon.copy(alpha = 0.4f), CutCornerShape(8.dp))
                            .clickable { showSupplyDropDialog = true },
                        colors = CardDefaults.cardColors(containerColor = EidosGlass),
                        shape = CutCornerShape(8.dp)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(12.dp),
                            verticalArrangement = Arrangement.SpaceBetween,
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                imageVector = Icons.Default.Refresh,
                                contentDescription = "Supply Drop",
                                tint = EidosNeon,
                                modifier = Modifier.size(24.dp)
                            )
                            Text(
                                text = "СИНХРОНИЗАЦИЯ\nДЕПО",
                                color = EidosNeon,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                textAlign = TextAlign.Center,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 14.sp
                            )
                        }
                    }

                    // World Boss Card
                    Card(
                        modifier = Modifier
                            .weight(1f)
                            .height(100.dp)
                            .border(1.dp, EidosRed.copy(alpha = 0.4f), CutCornerShape(8.dp))
                            .clickable { showBossDialog = true },
                        colors = CardDefaults.cardColors(containerColor = EidosGlass),
                        shape = CutCornerShape(8.dp)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(12.dp),
                            verticalArrangement = Arrangement.SpaceBetween,
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                imageVector = Icons.Default.Warning,
                                contentDescription = "World Boss",
                                tint = EidosRed,
                                modifier = Modifier.size(24.dp)
                            )
                            Text(
                                text = "МИРОВОЙ БОСС\nEIDOS-CORE",
                                color = EidosRed,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                textAlign = TextAlign.Center,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 14.sp
                            )
                        }
                    }
                }

                // Core Modules Sector (Main Gameplay Entries)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "ОПЕРАЦИОННЫЕ МОДУЛИ // РЕЖИМЫ ИГРЫ",
                        color = Color.Gray,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                    Text(
                        text = "💡 Выберите действие",
                        color = EidosCyan,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Central Sci-Fi Title Block
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "EIDOS: CHRONICLES",
                        color = ZzzElectricCyan,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.SansSerif,
                        letterSpacing = 2.sp
                    )
                    Text(
                        text = "CYBER HUB",
                        color = ZzzAcidYellow,
                        fontSize = 26.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.SansSerif,
                        letterSpacing = 2.sp
                    )
                }

                // ZZZ MASSIVE CENTRAL BANNER "СПУСК В НУЛЕВОЙ СЛОЙ"
                com.example.eidos.ui.components.ZzzMainButton(
                    text = ">>> СПУСК В НУЛЕВОЙ СЛОЙ >>>",
                    onClick = onNavigateToRaid,
                    primaryColor = ZzzAcidYellow,
                    borderColor = ZzzElectricCyan,
                    textColor = Color.Black,
                    height = 52.dp,
                    modifier = Modifier.fillMaxWidth()
                )

                // 3x3 Grid Menu (9 Cyber Frame Buttons)
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    // Row 1
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        CyberGridMenuItem(
                            title = "ПОГРУЖЕНИЕВ РЕЙД",
                            emojiIcon = "🌀",
                            borderColor = ZzzElectricCyan,
                            onClick = onNavigateToRaid,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = "ИНВЕНТАРЬ И СНАРЯЖЕНИЕ",
                            emojiIcon = "🃏",
                            borderColor = ZzzAcidYellow,
                            onClick = onNavigateToInventory,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = "КУЗНИЦА И СИНТЕЗ",
                            emojiIcon = "⚒️",
                            borderColor = ZzzHotMagenta,
                            onClick = onNavigateToForge,
                            modifier = Modifier.weight(1f)
                        )
                    }

                    // Row 2
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        CyberGridMenuItem(
                            title = "СЕТЕВАЯ ВОЙНА",
                            emojiIcon = "💀",
                            borderColor = EidosRed,
                            onClick = onNavigateToPvp,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = "ЧЕРНЫЙ РЫНОК",
                            emojiIcon = "🥷",
                            borderColor = Color(0xFF9C27B0),
                            onClick = onNavigateToShop,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = if (isBrokerActive) "ТЕНЕВОЙ БРОКЕР" else "ТЕНЕВОЙ БРОКЕР 🔴",
                            emojiIcon = "💻",
                            borderColor = if (isBrokerActive) EidosNeon else Color.Gray,
                            onClick = {
                                if (isBrokerActive) {
                                    if (activity != null && BiometricHelper.isBiometricAvailable(context)) {
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
                                } else {
                                    showBrokerOfflineDialog = true
                                }
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    // Row 3
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        CyberGridMenuItem(
                            title = "ВРАТА ЭЙДОСА",
                            emojiIcon = "⛩️",
                            borderColor = EidosCyan,
                            onClick = onNavigateToEidosGates,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = "КОДЕКС И БЕСТИАРИЙ",
                            emojiIcon = "📖",
                            borderColor = Color(0xFFFFD700),
                            onClick = onNavigateToCodex,
                            modifier = Modifier.weight(1f)
                        )
                        CyberGridMenuItem(
                            title = "ПРОФИЛЬ И СИНДИКАТ",
                            emojiIcon = "👤",
                            borderColor = EidosNeon,
                            onClick = onNavigateToProfile,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }

                // Secondary System Actions
                Text(
                    text = "СИСТЕМНЫЕ СЕРВИСЫ // SERVICES",
                    color = Color.Gray,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(top = 4.dp)
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    ServiceMiniButton(
                        title = "РЕЙТИНГ",
                        icon = Icons.Default.Star,
                        onClick = { showRatingDialog = true },
                        modifier = Modifier.weight(1f)
                    )
                    ServiceMiniButton(
                        title = "СПРАВКА",
                        icon = Icons.Default.Info,
                        onClick = { showGuideDialog = true },
                        modifier = Modifier.weight(1f),
                        color = EidosCyan
                    )
                    ServiceMiniButton(
                        title = "ТЕНЕВОЙ РЫНОК",
                        icon = Icons.Default.Lock,
                        onClick = { showShadowShopDialog = true },
                        modifier = Modifier.weight(1.2f),
                        color = EidosRed
                    )
                }

                // Live Terminal logs Panel
                Spacer(modifier = Modifier.height(4.dp))
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(150.dp)
                        .border(1.dp, Color.Gray.copy(alpha = 0.2f), CutCornerShape(4.dp)),
                    colors = CardDefaults.cardColors(containerColor = Color.Black.copy(alpha = 0.85f)),
                    shape = CutCornerShape(4.dp)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "TERMINAL_MONITOR // LOGS",
                                color = Color.Gray,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                text = "SYS_LOGGER_ACTIVE",
                                color = EidosNeon.copy(alpha = 0.7f),
                                fontSize = 8.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Divider(
                            color = Color.Gray.copy(alpha = 0.2f),
                            modifier = Modifier.padding(vertical = 8.dp)
                        )
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            if (logs.isEmpty()) {
                                Text(
                                    text = ">> No terminal logs found. System ready.",
                                    color = Color.DarkGray,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            } else {
                                logs.takeLast(6).reversed().forEach { log ->
                                    val logColor = when (log.type) {
                                        "error" -> EidosRed
                                        "loot" -> EidosNeon
                                        "combat" -> Color(0xFFFFCC00)
                                        else -> EidosCyan
                                    }
                                    Text(
                                        text = ">> [${log.type.uppercase()}] ${log.message}",
                                        color = logColor.copy(alpha = 0.85f),
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace,
                                        lineHeight = 13.sp
                                    )
                                }
                            }
                        }
                    }
                }
            }
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

    // 1. Daily Supply Drop logic (triggering Juice UI instead of simple AlertDialog)
    if (showSupplyDropDialog) {
        AlertDialog(
            onDismissRequest = { showSupplyDropDialog = false },
            title = {
                Text(
                    "СИНХРОНИЗАЦИЯ ДЕПО // SUPPLY DROP",
                    color = EidosCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    fontFamily = FontFamily.Monospace
                )
            },
            text = {
                Column {
                    Text(
                        text = "Каждые 24 часа вы можете синхронизировать депо вашего нейро-ядра, чтобы получить припасы из Центрального Хранилища.",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "ТЕКУЩИЕ ПАРАМЕТРЫ ЯДРА:\n" +
                                "• Оператор: ${player?.username ?: "GUEST"}\n" +
                                "• Энергия: ${player?.energy ?: 0}/${player?.max_energy ?: 100} ед. ⚡\n" +
                                "• Баланс: ${player?.biocoin ?: 0} BC 🪙",
                        color = Color.Gray,
                        fontSize = 11.sp,
                        lineHeight = 16.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "ГРАНТИРОВАННАЯ СУТОЧНАЯ ПОСТАВКА:\n" +
                                "• +50 Единиц Энергии Ядра ⚡\n" +
                                "• 1х Случайный Расходник 📦",
                        color = EidosNeon,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        lineHeight = 16.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        onClaimSupplyDrop()
                        showSupplyDropDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("СИНХРОНИЗИРОВАТЬ ДЕПО", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            dismissButton = {
                TextButton(onClick = { showSupplyDropDialog = false }) {
                    Text("ОТМЕНА", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF07070F),
            modifier = Modifier.border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(8.dp))
        )
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
                        Triple("1. NIGHT_CHASER", "15,400 PTS", "🏆 АУРА [RED_FIRE] // RELIC_VAMPIRE"),
                        Triple("2. NULL_POINTER", "14,210 PTS", "🥈 АУРА [RED_FIRE] // RELIC_SPEED"),
                        Triple("3. LOGIC_BOMB", "13,990 PTS", "🥉 АУРА [CYAN_SPARK] // RELIC_VAMPIRE"),
                        Triple("4. GHOST_IN_SHELL", "12,850 PTS", "⚡ АУРА [CYAN_SPARK] // RELIC_SPEED"),
                        Triple("5. VOID_WALKER", "12,400 PTS", "⚡ АУРА [CYAN_SPARK]"),
                        Triple("6. CODE_RUNNER", "11,950 PTS", "🎖 ТОП-10 НАГРАДА"),
                        Triple("7. NEO_OP", "11,500 PTS", "🎖 ТОП-10 НАГРАДА"),
                        Triple("8. BUFFER_OVERFLOW", "10,800 PTS", "🎖 ТОП-10 НАГРАДА"),
                        Triple("9. DEEP_MIND", "10,200 PTS", "🎖 ТОП-10 НАГРАДА"),
                        Triple("10. EIDOS_DEV", "9,900 PTS", "🎖 ТОП-10 НАГРАДА")
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
                        text = "ЗДОРОВЬЕ EIDOS-CORE: $bossHp / 1,000,000,000 HP",
                        color = EidosRed,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = bossHp.toFloat() / 1000000000f,
                        color = EidosRed,
                        trackColor = Color.DarkGray,
                        modifier = Modifier.fillMaxWidth().height(8.dp)
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    Text(
                        text = "ВАША СТАТИСТИКА:\n" +
                                "• Базовый урон (АТK): ${player?.attack ?: 5}\n" +
                                "• Нанесено урона: $personalDamage HP damage\n" +
                                "• Стоимость атаки: 10 Энергии Ядра ⚡",
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
                    val bossLeaderboard = listOf(
                        Pair("1. VIRTUAL_GOD", "120,400,000 HP"),
                        Pair("2. ANON_OP", "98,540,000 HP"),
                        Pair("3. KERNEL_PANIC", "84,100,000 HP"),
                        Pair("4. STACK_OVERFLOW", "72,900,000 HP"),
                        Pair("5. ROOT_ADMIN", "63,220,000 HP")
                    )
                    bossLeaderboard.forEach { (name, dmg) ->
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(name, color = Color.White, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text(dmg, color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if ((player?.energy ?: 0) >= 10) {
                            onAttackWorldBoss()
                            bossHp -= ((player?.attack ?: 10) * 12 + (50..150).random())
                            personalDamage += ((player?.attack ?: 10) * 12 + (50..150).random())
                            showBossDialog = false
                        }
                    },
                    enabled = (player?.energy ?: 0) >= 10,
                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("НАНЕСТИ УДАР (-10 ⚡)", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
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
                    Text(
                        "🔴 СИГНАЛ БРОКЕРА ПОТЕРЯН",
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
                        "🌐 ЯДРО EIDOS: Теневой Брокер скрывается в теневых шлюзах от ищейщиков Корпорации!",
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Он подключается к Сети случайно в течение дня ровно на 1 час. До следующего стабильного сеанса связи осталось:",
                        color = Color.Gray,
                        fontSize = 11.sp
                    )
                    Surface(
                        color = Color(0xFF1F0F2E),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF9C27B0)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                    ) {
                        Text(
                            "⏳ ПРИБЫТИЕ ЧЕРЕЗ: $brokerTimeStr",
                            color = Color(0xFFE040FB),
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.padding(10.dp)
                        )
                    }
                    Text(
                        "💡 В момент подключения у него будет 5 редчайших секретных предметов (реликвии, проклятый шмот, чипы), недоступных в обычном магазине!",
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
            onDismiss = { showTerminalTutorialDialog = false },
            onCompleteTutorial = {
                onClaimSupplyDrop() // Grants bonus supply rewards
            }
        )
    }

    // 7. Earth Relic Showcase Dialog
    if (showRelicShowcaseDialog) {
        RelicShowcaseDialog(
            activeRelicId = activeRelic?.id,
            onSelectResonator = { relic ->
                activeRelic = relic
            },
            onDismiss = { showRelicShowcaseDialog = false }
        )
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
    val haptics = remember { com.example.eidos.ui.utils.HapticFeedbackManager.getInstance(context) }
    val audio = remember { com.example.eidos.ui.utils.EidosAudioManager.getInstance(context) }

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
                audio.playSound(com.example.eidos.ui.utils.EidosAudioManager.SoundType.CLICK_CYBER)
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
                "🏛️ ДЕРЕВО МЕТА-ПРОГРЕССИИ ХАБА",
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
                    title = "💚 СИГНАЛ ЯДРА (HP)",
                    desc = "Стартовое HP в рейде: +${signalLvl * 15} HP",
                    level = signalLvl,
                    cost = (signalLvl + 1) * 5,
                    onUpgrade = { onUpgrade("signal") }
                )

                // 2. Key Level
                MetaUpgradeRow(
                    title = "🔑 КАРМАННЫЙ КЛЮЧ",
                    desc = if (keyLvl > 0) "Старт рейда с Мастер-Ключом!" else "Старт без ключа",
                    level = keyLvl,
                    cost = (keyLvl + 1) * 5,
                    onUpgrade = { onUpgrade("key") }
                )

                // 3. Luck Level
                MetaUpgradeRow(
                    title = "🍀 АУРА УДАЧИ БЕЗДНЫ",
                    desc = "Бонус к Удаче: +${luckLvl * 5}",
                    level = luckLvl,
                    cost = (luckLvl + 1) * 5,
                    onUpgrade = { onUpgrade("luck") }
                )

                // 4. Power Level
                MetaUpgradeRow(
                    title = "⚡ ЗАКАЛКА АВАТАРА",
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
                Text("+$cost 💎", color = Color.Yellow, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun CyberHubHeader(
    player: com.example.eidos.data.Player?,
    onProfileClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 8.dp, vertical = 6.dp)
            .border(1.dp, Color(0xFF1E3A34), CutCornerShape(8.dp)),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0B1215).copy(alpha = 0.95f)),
        shape = CutCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 1. УРОВЕНЬ
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "УРОВЕНЬ",
                    color = Color.Gray,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .background(Color(0xFF0F2B26), CutCornerShape(6.dp))
                        .border(1.5.dp, EidosCyan, CutCornerShape(6.dp))
                        .clickable { onProfileClick() },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${player?.level ?: 48}",
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 2. СИГНАЛ (ОЗ)
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "СИГНАЛ (ОЗ)",
                    color = Color.Gray,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("❤️", fontSize = 11.sp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.hp ?: 1240}/${player?.max_hp ?: 1500}",
                        color = Color.White,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 3. ОПЫТ
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "ОПЫТ",
                    color = Color.Gray,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .background(EidosCyan, RoundedCornerShape(2.dp))
                            .padding(horizontal = 3.dp, vertical = 1.dp)
                    ) {
                        Text(
                            text = "XP",
                            color = Color.Black,
                            fontSize = 7.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.xp ?: 28600}/35k",
                        color = Color.White,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 4. БИОКОИНЫ
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "БИОКОИНЫ",
                    color = Color.Gray,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("🪙", fontSize = 11.sp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.biocoin ?: 18950}",
                        color = Color(0xFFFFD700),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            // 5. СЕРИЯ
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "СЕРИЯ",
                    color = Color.Gray,
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(2.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("🔥", fontSize = 11.sp)
                    Spacer(modifier = Modifier.width(3.dp))
                    Text(
                        text = "${player?.streak ?: 24} ДНЯ",
                        color = Color(0xFFFF5722),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
fun CyberGridMenuItem(
    title: String,
    emojiIcon: String,
    borderColor: Color = ZzzElectricCyan,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val haptic = LocalHapticFeedback.current
    Surface(
        onClick = {
            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
            onClick()
        },
        color = ZzzDarkSurface.copy(alpha = 0.95f),
        shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp),
        border = androidx.compose.foundation.BorderStroke(2.dp, borderColor),
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 10.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Color(0xFF161B26), CutCornerShape(4.dp))
                    .border(1.dp, borderColor.copy(alpha = 0.6f), CutCornerShape(4.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = emojiIcon,
                    fontSize = 20.sp
                )
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = title.uppercase(),
                color = Color.White,
                fontSize = 9.5.sp,
                fontWeight = FontWeight.ExtraBold,
                fontFamily = FontFamily.SansSerif,
                textAlign = TextAlign.Center,
                lineHeight = 12.sp
            )
        }
    }
}

@Composable
fun CyberHubBottomBar(
    selectedTab: String = "hub",
    onTabSelected: (String) -> Unit
) {
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
                iconRes = com.example.eidos.R.drawable.ic_nav_hub,
                fallbackEmoji = "🏠",
                label = "ТЕРМИНАЛ",
                isSelected = selectedTab == "hub",
                onClick = { onTabSelected("hub") }
            )
            BottomNavItem(
                iconRes = com.example.eidos.R.drawable.ic_nav_inventory,
                fallbackEmoji = "🎒",
                label = "ИНВЕНТАРЬ",
                isSelected = selectedTab == "inventory",
                onClick = { onTabSelected("inventory") }
            )
            BottomNavItem(
                iconRes = com.example.eidos.R.drawable.ic_nav_matrix,
                fallbackEmoji = "⚡",
                label = "БЕЗДНА",
                isSelected = selectedTab == "matrix",
                isHighlight = true,
                onClick = { onTabSelected("matrix") }
            )
            BottomNavItem(
                iconRes = com.example.eidos.R.drawable.ic_nav_pvp,
                fallbackEmoji = "⚔️",
                label = "PVP СЕТЬ",
                isSelected = selectedTab == "pvp",
                onClick = { onTabSelected("pvp") }
            )
            BottomNavItem(
                iconRes = com.example.eidos.R.drawable.ic_nav_settings,
                fallbackEmoji = "⚙️",
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
    fallbackEmoji: String,
    label: String,
    isSelected: Boolean,
    isHighlight: Boolean = false,
    onClick: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "navPulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.8f,
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
            .padding(horizontal = 6.dp, vertical = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier.size(28.dp)
        ) {
            Image(
                painter = painterResource(id = iconRes),
                contentDescription = label,
                modifier = Modifier
                    .size(if (isHighlight) 28.dp else 24.dp)
                    .then(
                        if (isSelected) {
                            Modifier.neonGlowPulse(
                                glowColor = if (isHighlight) EidosCyan else EidosNeon,
                                baseWidth = 2.dp,
                                shape = RoundedCornerShape(8.dp)
                            )
                        } else Modifier
                    ),
                alpha = if (isSelected) pulseAlpha else 0.6f
            )
        }
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            color = when {
                isSelected && isHighlight -> EidosCyan
                isSelected -> EidosNeon
                else -> Color.Gray
            },
            fontSize = 7.5.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            fontFamily = FontFamily.Monospace,
            maxLines = 1
        )
    }
}
