package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.EaseOutBack
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.RadioMessageEntity
import io.eidos.zerolayer.data.Achievement
import io.eidos.zerolayer.data.AchievementRegistry
import io.eidos.zerolayer.data.AchievementStorage
import io.eidos.zerolayer.data.AchievementItem
import io.eidos.zerolayer.data.PlayerProgressManager
import androidx.compose.foundation.horizontalScroll
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.components.VideoBackground
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.cyberHudBorder
import io.eidos.zerolayer.ui.components.AnimatedCyberProgressBar
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.cyberClickable
import io.eidos.zerolayer.ui.components.EidosTerminalDialog
import io.eidos.zerolayer.data.SupabaseClientManager
import io.eidos.zerolayer.data.SupabasePlayer
import kotlinx.coroutines.launch

data class AchievementData(
    val id: String,
    val title: String,
    val desc: String,
    val icon: String,
    val current: Int,
    val target: Int,
    val reward: String
)

data class SkillItem(val name: String, val desc: String, val cost: Int)

private fun getXpForLevel(level: Int): Long {
    return io.eidos.zerolayer.data.PlayerProgressManager.getLevelInfo(level).requiredXp
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    player: Player?,
    inventory: List<InventoryItem>,
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    radioMessages: List<RadioMessageEntity> = emptyList(),
    unclaimedRadioMessagesCount: Int = 0,
    onClaimRadioMessage: (Long) -> Unit = {},
    onUpgradeSkill: (String, Int) -> Unit,
    onRespecSkills: () -> Unit,
    onRedeemReferralCode: (String) -> Unit = {},
    onSendSignal: (String, String) -> Unit = { _, _ -> },
    onClaimAchievement: (Achievement) -> Unit = {},
    onTriggerTestLevelUp: () -> Unit = {},
    onBack: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    var activeTab by remember { mutableIntStateOf(0) } // 0: Stats, 1: Achievements, 2: Skill Tree, 3: Leaderboard, 4: Syndicate, 5: Radio/Mailbox
    var referralInput by remember { mutableStateOf("") }
    var signalRecipient by remember { mutableStateOf("") }
    var signalMessage by remember { mutableStateOf("") }
    var showTerminalDialog by remember { mutableStateOf(false) }
    var showAvatarInspector by remember { mutableStateOf(false) }
    var inspectedAvatarLvl by remember { mutableIntStateOf(1) }
    var topPlayers by remember { mutableStateOf<List<SupabasePlayer>>(emptyList()) }
    var isLeaderboardLoading by remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(activeTab) {
        if (activeTab == 3 && topPlayers.isEmpty()) {
            isLeaderboardLoading = true
            topPlayers = SupabaseClientManager.fetchTopPlayers()
            isLeaderboardLoading = false
        }
    }

    val context = LocalContext.current
    val audioManager = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }
    val hapticManager = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }
    val achievementStorage = remember { AchievementStorage(context) }

    val shardsCount = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0
    val actualLevel = player?.level ?: 1
    var currentDisplayLevel by remember { mutableIntStateOf(actualLevel) }
    var prevLevel by remember { mutableIntStateOf(actualLevel) }
    var isLevelUpAnimActive by remember { mutableStateOf(false) }

    val scanAnim = remember { Animatable(0f) }
    val flashAnim = remember { Animatable(0f) }

    fun triggerLevelUpAnimation(fromLvl: Int, toLvl: Int) {
        coroutineScope.launch {
            prevLevel = fromLvl
            currentDisplayLevel = toLvl
            isLevelUpAnimActive = true
            audioManager.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.HACK_SUCCESS)
            hapticManager.lootLegendary()

            launch {
                flashAnim.snapTo(0.85f)
                flashAnim.animateTo(0f, animationSpec = tween(900))
            }
            launch {
                scanAnim.snapTo(0f)
                scanAnim.animateTo(1f, animationSpec = tween(1400, easing = LinearEasing))
            }

            kotlinx.coroutines.delay(2600)
            isLevelUpAnimActive = false
        }
    }

    LaunchedEffect(actualLevel) {
        if (actualLevel > currentDisplayLevel) {
            triggerLevelUpAnimation(currentDisplayLevel, actualLevel)
        } else if (actualLevel != currentDisplayLevel) {
            currentDisplayLevel = actualLevel
        }
    }

    val currentXp = player?.xp ?: 0L
    val isMaxLevel = currentDisplayLevel >= 31
    val curLevelBaseXp = getXpForLevel(currentDisplayLevel)
    val nextLevelXp = getXpForLevel(currentDisplayLevel + 1)
    val xpInLevel = (currentXp - curLevelBaseXp).coerceAtLeast(0L)
    val xpNeededForLevel = (nextLevelXp - curLevelBaseXp).coerceAtLeast(1L)
    val xpProgress = if (isMaxLevel) 1f else (xpInLevel.toFloat() / xpNeededForLevel.toFloat()).coerceIn(0f, 1f)

    // Compute achievements from full registry (43 total achievements)
    val p = player ?: Player(uid = 0, username = null, first_name = null)
    val stats = remember(player, inventory) { achievementStorage.getStats() }
    val achievements: List<AchievementItem> = remember(player, stats, inventory) {
        AchievementRegistry.ALL_DEFINITIONS.map { def ->
            val isUnlocked = achievementStorage.isUnlocked(def.id) || def.isMet(p, stats)
            val isClaimed = achievementStorage.isClaimed(def.id)
            val curr = def.getProgress(p, stats)
            AchievementItem(
                id = def.id,
                category = def.category,
                icon = def.icon,
                title = def.title,
                description = def.description,
                xpReward = def.xpReward,
                coinReward = def.coinReward,
                target = def.target,
                current = curr,
                isUnlocked = isUnlocked,
                isClaimed = isClaimed
            )
        }
    }

    var selectedAchievementCategory by remember { mutableStateOf("ВСЕ") }
    val achievementCategories = remember(achievements) {
        listOf("ВСЕ") + achievements.map { it.category }.distinct()
    }
    val filteredAchievements = remember(achievements, selectedAchievementCategory) {
        if (selectedAchievementCategory == "ВСЕ") achievements
        else achievements.filter { it.category.equals(selectedAchievementCategory, ignoreCase = true) }
    }

    val unlockedAchCount = achievements.count { it.isUnlocked }
    val claimedAchCount = achievements.count { it.isClaimed }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("НЕЙРО-ПРОФИЛЬ // EIDOS", color = EidosCyan, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosCyan)
                    }
                },
                actions = {
                    IconButton(onClick = { showTerminalDialog = true }) {
                        ZzzIcon(iconRes = R.drawable.ic_menu_codex, size = 18.dp, tint = EidosCyan)
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings", tint = EidosCyan)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Transparent
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize()) {
            VideoBackground(resName = "doll", modifier = Modifier.fillMaxSize())
            CyberGridOverlay(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier
                    .padding(innerPadding)
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Identity Card with Full-Width Character Image
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(EidosGlass)
                        .border(1.dp, EidosCyan.copy(alpha = 0.6f), CutCornerShape(8.dp))
                        .cyberHudBorder(color = EidosCyan)
                ) {
                    Column(modifier = Modifier.fillMaxWidth()) {
                        // Full width Character Image Banner (1280x714 aspect ratio style)
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(220.dp)
                                .background(Color.Black)
                                .clickable {
                                    inspectedAvatarLvl = currentDisplayLevel
                                    showAvatarInspector = true
                                }
                        ) {
                            // Animated transition between character level images (lvl_x.png -> lvl_x+1.png)
                            AnimatedContent(
                                targetState = currentDisplayLevel,
                                transitionSpec = {
                                    (fadeIn(animationSpec = tween(700)) + scaleIn(initialScale = 0.82f, animationSpec = tween(700, easing = EaseOutBack)))
                                        .togetherWith(fadeOut(animationSpec = tween(400)) + scaleOut(targetScale = 1.18f, animationSpec = tween(400)))
                                },
                                label = "CharacterLevelTransition",
                                modifier = Modifier.fillMaxSize()
                            ) { targetLvl ->
                                EidosImage(
                                    resName = "lvl_${targetLvl.coerceIn(1, 31)}",
                                    borderColor = Color.Transparent,
                                    borderWidth = 0.dp,
                                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }

                            // Cybernetic gradient overlay at bottom of image for contrast
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(
                                        androidx.compose.ui.graphics.Brush.verticalGradient(
                                            colors = listOf(
                                                Color.Transparent,
                                                Color.Black.copy(alpha = 0.4f),
                                                Color.Black.copy(alpha = 0.95f)
                                            )
                                        )
                                    )
                            )

                            // Cyber Scanline Sweep overlay during level up animation
                            if (isLevelUpAnimActive) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .height(8.dp)
                                        .graphicsLayer {
                                            translationY = scanAnim.value * 220.dp.toPx()
                                        }
                                        .background(
                                            androidx.compose.ui.graphics.Brush.verticalGradient(
                                                colors = listOf(Color.Transparent, EidosNeon, EidosCyan, Color.Transparent)
                                            )
                                        )
                                )

                                // Neon Flash Overlay
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .background(EidosNeon.copy(alpha = flashAnim.value * 0.4f))
                                )
                            }

                            // Core Level Badge and Level-Up Simulation button on top-right of image
                            Row(
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .padding(12.dp),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                // Test Level Up button
                                Box(
                                    modifier = Modifier
                                        .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                        .border(1.dp, EidosCyan, CutCornerShape(4.dp))
                                        .clickable {
                                            onTriggerTestLevelUp()
                                            val nextLvl = if (currentDisplayLevel >= 31) 1 else currentDisplayLevel + 1
                                            triggerLevelUpAnimation(currentDisplayLevel, nextLvl)
                                        }
                                        .padding(horizontal = 8.dp, vertical = 6.dp)
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_res_energy, size = 10.dp)
                                        Spacer(Modifier.width(3.dp))
                                        Text(
                                            "ТЕСТ LEVEL UP",
                                            color = EidosCyan,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }

                                // Core Level Badge
                                Box(
                                    modifier = Modifier
                                        .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                        .border(1.dp, if (isLevelUpAnimActive) EidosNeon else EidosCyan, CutCornerShape(4.dp))
                                        .padding(horizontal = 10.dp, vertical = 6.dp)
                                ) {
                                    Text(
                                        "CORE LEVEL $currentDisplayLevel",
                                        color = if (isLevelUpAnimActive) EidosNeon else Color.White,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            // Level-Up Popup Overlay
                            if (isLevelUpAnimActive) {
                                Box(
                                    modifier = Modifier
                                        .align(Alignment.Center)
                                        .background(Color.Black.copy(alpha = 0.9f), CutCornerShape(8.dp))
                                        .border(1.5.dp, EidosNeon, CutCornerShape(8.dp))
                                        .padding(horizontal = 20.dp, vertical = 12.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            ZzzIcon(R.drawable.ic_res_overdrive, size = 14.dp)
                                            Spacer(Modifier.width(6.dp))
                                            Text(
                                                "LEVEL UP DETECTED",
                                                color = EidosNeon,
                                                fontSize = 13.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            "CORE UPGRADE: LVL $prevLevel > LVL $currentDisplayLevel",
                                            color = Color.White,
                                            fontSize = 14.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                            }

                            // Operator Info overlaid on bottom of image
                            Column(
                                modifier = Modifier
                                    .align(Alignment.BottomStart)
                                    .padding(12.dp)
                            ) {
                                Text("ЛИЧНОСТЬ ОПЕРАТОРА", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                                Text(player?.username ?: "ГОСТЬ", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Black)
                                Text("ФРАКЦИЯ: ${player?.faction ?: "НЕТ"}", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }

                            // Avatar Dossier Pill button on bottom-right of image
                            Box(
                                modifier = Modifier
                                    .align(Alignment.BottomEnd)
                                    .padding(12.dp)
                                    .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                    .border(1.dp, EidosCyan.copy(alpha = 0.7f), CutCornerShape(4.dp))
                                    .clickable {
                                        inspectedAvatarLvl = actualLevel.coerceIn(1, 31)
                                        showAvatarInspector = true
                                    }
                                    .padding(horizontal = 8.dp, vertical = 5.dp)
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    ZzzIcon(R.drawable.ic_event_anomaly, size = 10.dp)
                                    Text(
                                        "ДОСЬЕ ЭВОЛЮЦИИ",
                                        color = EidosCyan,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }

                        // Bottom section with XP Progress Bar
                        Column(modifier = Modifier.padding(12.dp)) {
                            AnimatedCyberProgressBar(
                                progress = xpProgress,
                                color = EidosNeon,
                                label = "ОПЫТ ДО УРОВНЯ ${currentDisplayLevel + 1}",
                                valueText = "$xpInLevel / $xpNeededForLevel XP [${(xpProgress * 100).toInt()}%]",
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Navigation Tabs
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(EidosGlass)
                        .border(1.dp, EidosCyan.copy(alpha = 0.3f))
                        .padding(4.dp),
                    horizontalArrangement = Arrangement.spacedBy(3.dp)
                ) {
                    TabButton(
                        text = "ИНФО",
                        selected = activeTab == 0,
                        onClick = { activeTab = 0 },
                        modifier = Modifier.weight(0.9f)
                    )
                    TabButton(
                        text = "АЧИВКИ",
                        selected = activeTab == 1,
                        onClick = { activeTab = 1 },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "НАВЫКИ",
                        selected = activeTab == 2,
                        onClick = { activeTab = 2 },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "ТОП",
                        selected = activeTab == 3,
                        onClick = { activeTab = 3 },
                        modifier = Modifier.weight(0.8f)
                    )
                    TabButton(
                        text = "АЛЬЯНС",
                        selected = activeTab == 4,
                        onClick = { activeTab = 4 },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = if (unclaimedRadioMessagesCount > 0) "РАДИО ($unclaimedRadioMessagesCount)" else "РАДИО",
                        selected = activeTab == 5,
                        onClick = { activeTab = 5 },
                        modifier = Modifier.weight(1.1f)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                when (activeTab) {
                    0 -> {
                        // TAB 0: Stats & Overview
                        val currentLevelInfo = io.eidos.zerolayer.data.PlayerProgressManager.getLevelInfo(currentDisplayLevel)

                        // Level Slogan & Rank Card
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 14.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF101017)),
                            shape = CutCornerShape(8.dp),
                            border = androidx.compose.foundation.BorderStroke(
                                1.5.dp,
                                Brush.horizontalGradient(listOf(Color(0xFFFFD700), Color(0xFFFF0055), EidosCyan))
                            )
                        ) {
                            Column(modifier = Modifier.padding(14.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_res_overdrive, size = 22.dp)
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Column {
                                            Text(
                                                "LVL ${currentLevelInfo.level}: ${currentLevelInfo.stageTitle}",
                                                color = Color(0xFFFFD700),
                                                fontSize = 14.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                            Text(
                                                "РАНГ: ${currentLevelInfo.rankTitle}",
                                                color = EidosCyan,
                                                fontSize = 11.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                    }

                                    Surface(
                                        color = Color(0xFFFFD700).copy(alpha = 0.15f),
                                        shape = CutCornerShape(4.dp),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700).copy(alpha = 0.5f))
                                    ) {
                                        Text(
                                            "СТАТУС АКТИВЕН",
                                            color = Color(0xFFFFD700),
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                Surface(
                                    color = Color.Black.copy(alpha = 0.6f),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        text = currentLevelInfo.sloganText,
                                        color = Color.LightGray,
                                        fontSize = 12.sp,
                                        lineHeight = 16.sp,
                                        modifier = Modifier.padding(10.dp)
                                    )
                                }

                                Spacer(modifier = Modifier.height(8.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    ZzzIcon(R.drawable.ic_ui_unlocked, size = 14.dp, tint = EidosCyan)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        "${currentLevelInfo.perkTitle}: ${currentLevelInfo.perkDescription}",
                                        color = EidosCyan,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.SemiBold
                                    )
                                }
                            }
                        }

                        Text(
                            "БОЕВЫЕ ХАРАКТЕРИСТИКИ ЯДРА:",
                            color = EidosCyan,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                        )

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            StatCard("HP (СИГНАЛ)", "${player?.hp}/${player?.max_hp}", EidosRed, Modifier.weight(1f))
                            StatCard("ЭНЕРГИЯ", "${player?.energy}/${player?.max_energy}", EidosNeon, Modifier.weight(1f))
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            StatCard("АТАКА", "${activeStats?.attack ?: player?.attack ?: 10}", Color.White, Modifier.weight(1f))
                            StatCard("ЗАЩИТА", "${activeStats?.defense ?: player?.defense ?: 5}", Color.White, Modifier.weight(1f))
                            StatCard("УДАЧА", "${activeStats?.luck ?: player?.luck ?: 5}", EidosCyan, Modifier.weight(1f))
                        }

                        Spacer(modifier = Modifier.height(20.dp))

                        Text(
                            "ПОКАЗАТЕЛИ ДЕЯТЕЛЬНОСТИ ОПЕРАТОРА:",
                            color = EidosCyan,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                        )

                        // Full Metrics Card
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = EidosGlass),
                            shape = CutCornerShape(6.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.15f))
                        ) {
                            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                MetricRow(drawableRes = R.drawable.ic_event_evac, label = "Рейдов Пройдено:", value = "${player?.raids_done ?: 0} рейдов")
                                MetricRow(drawableRes = R.drawable.ic_action_defense, label = "Идеальных Рейдов (без урона):", value = "${player?.perfect_raids ?: 0}")
                                MetricRow(drawableRes = R.drawable.ic_stat_depth, label = "Макс. Глубина Погружения:", value = "${player?.max_depth ?: 0} метров", valueColor = EidosCyan)
                                MetricRow(drawableRes = R.drawable.ic_event_danger, label = "Уничтожено Вирусов:", value = "${player?.kills ?: 0} сушностей")

                                HorizontalDivider(color = Color.White.copy(alpha = 0.1f))

                                val totalPvp = (player?.wins_pvp ?: 0) + (player?.losses_pvp ?: 0)
                                val winrate = if (totalPvp > 0) String.format(java.util.Locale.US, "%.1f%%", ((player?.wins_pvp ?: 0).toFloat() / totalPvp) * 100) else "0.0%"
                                MetricRow(drawableRes = R.drawable.ic_action_attack, label = "PvP Дуэли:", value = "${player?.wins_pvp ?: 0} W / ${player?.losses_pvp ?: 0} L")
                                MetricRow(drawableRes = R.drawable.ic_action_scan, label = "Процент Побед (Winrate):", value = winrate, valueColor = EidosNeon)

                                HorizontalDivider(color = Color.White.copy(alpha = 0.1f))

                                MetricRow(drawableRes = R.drawable.ic_res_overdrive, label = "Серия Входов (Стрик):", value = "${player?.streak ?: 1} дн.")
                                MetricRow(drawableRes = R.drawable.ic_res_eidos_shard, label = "Осколки Эйдоса:", value = "$shardsCount шт.", valueColor = EidosCyan)
                                MetricRow(drawableRes = R.drawable.ic_res_biocoin, label = "Крипто-Баланс:", value = "${player?.biocoin ?: 0} BC", valueColor = Color(0xFFFFB300))
                                MetricRow(drawableRes = R.drawable.ic_res_energy, label = "Накопленный Опыт:", value = "${player?.xp ?: 0} XP", valueColor = EidosNeon)
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        Surface(
                            color = if (unclaimedRadioMessagesCount > 0) Color(0xFF1B3A36) else EidosGlass,
                            border = androidx.compose.foundation.BorderStroke(1.dp, if (unclaimedRadioMessagesCount > 0) EidosCyan else Color.White.copy(alpha = 0.2f)),
                            shape = CutCornerShape(6.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { activeTab = 5 }
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                    ZzzIcon(R.drawable.ic_menu_codex, size = 20.dp, tint = EidosCyan)
                                    Spacer(Modifier.width(10.dp))
                                    Column {
                                        Text(
                                            "ТЕРМИНАЛ ПЕРЕХВАТА РАДИОЧАСТОТ",
                                            color = EidosCyan,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Text(
                                            if (unclaimedRadioMessagesCount > 0)
                                                "Обнаружено $unclaimedRadioMessagesCount невостребованных пакетов данных!"
                                            else
                                                "Входящие трансляции от Синдикатов и Ядра",
                                            color = if (unclaimedRadioMessagesCount > 0) EidosNeon else Color.LightGray,
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }
                                Text("ОТКРЫТЬ >", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }

                    1 -> {
                        // TAB 1: Achievements (43 items with categories, real progress, and Claim buttons)
                        Surface(
                            color = EidosCyan.copy(alpha = 0.12f),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.4f)),
                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp),
                            shape = CutCornerShape(6.dp)
                        ) {
                            Column(modifier = Modifier.padding(10.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_menu_codex, size = 14.dp)
                                    Spacer(Modifier.width(6.dp))
                                    Text(
                                        text = "НЕЙРО-ДОСТИЖЕНИЯ СЕТИ EIDOS",
                                        color = Color(0xFFFFD700),
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                Text(
                                    text = "Открыто: $unlockedAchCount/${achievements.size} • Забрано наград: $claimedAchCount/${achievements.size}",
                                    color = Color.White,
                                    fontSize = 10.sp,
                                    fontFamily = FontFamily.Monospace,
                                    modifier = Modifier.padding(top = 2.dp, bottom = 4.dp)
                                )
                                LinearProgressIndicator(
                                    progress = { if (achievements.isNotEmpty()) unlockedAchCount.toFloat() / achievements.size.toFloat() else 0f },
                                    modifier = Modifier.fillMaxWidth().height(6.dp).clip(CutCornerShape(3.dp)),
                                    color = Color(0xFFFFD700),
                                    trackColor = Color.DarkGray.copy(alpha = 0.5f)
                                )
                            }
                        }

                        // Category Filter Chips
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 12.dp)
                                .horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            achievementCategories.forEach { cat ->
                                val isSelected = cat == selectedAchievementCategory
                                val count = if (cat == "ВСЕ") achievements.size else achievements.count { it.category.equals(cat, ignoreCase = true) }
                                Surface(
                                    color = if (isSelected) Color(0xFFFF0055).copy(alpha = 0.3f) else EidosGlass,
                                    border = androidx.compose.foundation.BorderStroke(
                                        1.dp,
                                        if (isSelected) Color(0xFFFF0055) else Color.White.copy(alpha = 0.15f)
                                    ),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.clickable { selectedAchievementCategory = cat }
                                ) {
                                    Text(
                                        text = "$cat ($count)",
                                        color = if (isSelected) Color(0xFFFF0055) else Color.LightGray,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp)
                                    )
                                }
                            }
                        }

                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            filteredAchievements.forEach { ach ->
                                val isDone = ach.isUnlocked
                                val isClaimed = ach.isClaimed
                                val progressRatio = if (ach.target <= 0) (if (isDone) 1f else 0f) else (ach.current.toFloat() / ach.target.toFloat()).coerceIn(0f, 1f)

                                Card(
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                                    shape = CutCornerShape(6.dp),
                                    border = androidx.compose.foundation.BorderStroke(
                                        1.dp,
                                        when {
                                            isClaimed -> EidosNeon.copy(alpha = 0.6f)
                                            isDone -> Color(0xFFFFD700)
                                            else -> Color.White.copy(alpha = 0.15f)
                                        }
                                    )
                                ) {
                                    Column(modifier = Modifier.padding(12.dp)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                                ZzzIcon(R.drawable.ic_event_chest, size = 22.dp)
                                                Spacer(modifier = Modifier.width(10.dp))
                                                Column {
                                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                                        Text(
                                                            ach.title,
                                                            color = when {
                                                                isClaimed -> EidosNeon
                                                                isDone -> Color(0xFFFFD700)
                                                                else -> Color.White
                                                            },
                                                            fontWeight = FontWeight.Bold,
                                                            fontSize = 12.sp,
                                                            fontFamily = FontFamily.Monospace
                                                        )
                                                    }
                                                    Text(
                                                        ach.category,
                                                        color = Color(0xFF8A2BE2),
                                                        fontSize = 9.sp,
                                                        fontWeight = FontWeight.Bold,
                                                        fontFamily = FontFamily.Monospace
                                                    )
                                                    Text(ach.description, color = Color.Gray, fontSize = 10.sp, lineHeight = 13.sp)
                                                }
                                            }

                                            Spacer(modifier = Modifier.width(8.dp))

                                            Surface(
                                                color = when {
                                                    isClaimed -> EidosNeon.copy(alpha = 0.15f)
                                                    isDone -> Color(0xFFFFD700).copy(alpha = 0.2f)
                                                    else -> Color.DarkGray.copy(alpha = 0.3f)
                                                },
                                                border = androidx.compose.foundation.BorderStroke(
                                                    1.dp,
                                                    when {
                                                        isClaimed -> EidosNeon
                                                        isDone -> Color(0xFFFFD700)
                                                        else -> Color.Gray
                                                    }
                                                ),
                                                shape = CutCornerShape(3.dp)
                                            ) {
                                                Text(
                                                    when {
                                                        isClaimed -> "ПОЛУЧЕНО"
                                                        isDone -> "ВЫПОЛНЕНО"
                                                        else -> "${ach.current.coerceAtMost(ach.target)}/${ach.target}"
                                                    },
                                                    color = when {
                                                        isClaimed -> EidosNeon
                                                        isDone -> Color(0xFFFFD700)
                                                        else -> Color.LightGray
                                                    },
                                                    fontSize = 9.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                                    fontFamily = FontFamily.Monospace
                                                )
                                            }
                                        }

                                        Spacer(modifier = Modifier.height(8.dp))

                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            LinearProgressIndicator(
                                                progress = { progressRatio },
                                                modifier = Modifier.weight(1f).height(4.dp).clip(CutCornerShape(2.dp)),
                                                color = if (isDone) Color(0xFFFFD700) else EidosCyan,
                                                trackColor = Color.DarkGray.copy(alpha = 0.5f)
                                            )
                                            Spacer(modifier = Modifier.width(10.dp))
                                            Text(
                                                "НАГРАДА: +${ach.xpReward} XP",
                                                color = Color(0xFFFFB300),
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }

                                        if (isDone && !isClaimed) {
                                            Spacer(modifier = Modifier.height(8.dp))
                                            Button(
                                                onClick = {
                                                    onClaimAchievement(
                                                        Achievement(
                                                            title = ach.title,
                                                            description = ach.description,
                                                            xpReward = ach.xpReward,
                                                            coinReward = 0,
                                                            icon = ach.icon,
                                                            category = ach.category,
                                                            achievementKey = ach.id
                                                        )
                                                    )
                                                },
                                                modifier = Modifier.fillMaxWidth().height(36.dp),
                                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF0055)),
                                                shape = CutCornerShape(4.dp)
                                            ) {
                                                Row(verticalAlignment = Alignment.CenterVertically) {
                                                    ZzzIcon(R.drawable.ic_res_energy, size = 12.dp)
                                                    Spacer(Modifier.width(4.dp))
                                                    Text(
                                                        "ЗАБРАТЬ НАГРАДУ (+${ach.xpReward} XP)",
                                                        color = Color.White,
                                                        fontSize = 10.sp,
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

                    2 -> {
                        // TAB 2: Skill Tree
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(EidosGlass)
                                .border(1.dp, EidosCyan.copy(alpha = 0.3f))
                                .padding(12.dp)
                        ) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                Text("РЕЗЕРВНЫЙ ЗАПАС ОСКОЛКОВ:", color = Color.Gray, fontSize = 11.sp)
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text("$shardsCount", color = EidosCyan, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                                    Spacer(Modifier.width(4.dp))
                                    ZzzIcon(R.drawable.ic_res_eidos_shard, size = 14.dp)
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        // 1. Hacker Branch
                        SkillBranchHeader("ВЕТКА ВЗЛОМА [HACKER]", EidosCyan)
                        SkillNodeRow(
                            branchName = "hacker",
                            skillsUnlocked = listOf(player?.skill_hacker_1 ?: 0, player?.skill_hacker_2 ?: 0, player?.skill_hacker_3 ?: 0),
                            skillDescriptions = listOf(
                                SkillItem("Базовый Сканнер", "LUCK +10 во всех рейдах.", 10),
                                SkillItem("ИИ Дешифратор", "+20% BioCoins из контейнеров.", 30),
                                SkillItem("Пакет Взлома", "Магнитные отмычки не расходуются на сейфы.", 100)
                            ),
                            shardsCount = shardsCount,
                            onUpgrade = onUpgradeSkill
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        // 2. Berserk Branch
                        SkillBranchHeader("БОЕВАЯ ВЕТКА [BERSERK]", EidosRed)
                        SkillNodeRow(
                            branchName = "berserk",
                            skillsUnlocked = listOf(player?.skill_berserk_1 ?: 0, player?.skill_berserk_2 ?: 0, player?.skill_berserk_3 ?: 0),
                            skillDescriptions = listOf(
                                SkillItem("Боевой Стимулятор", "+10% к шансу критического удара.", 10),
                                SkillItem("Синергия Ядра", "+15 ATK и +15 DEF базово.", 30),
                                SkillItem("Протокол «Пиявка»", "Вампиризм: +5% урона лечит Сигнал.", 100)
                            ),
                            shardsCount = shardsCount,
                            onUpgrade = onUpgradeSkill
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        // 3. Medic Branch
                        SkillBranchHeader("ВЕТКА СИНХРОНИЗАЦИИ [MEDIC]", EidosNeon)
                        SkillNodeRow(
                            branchName = "medic",
                            skillsUnlocked = listOf(player?.skill_medic_1 ?: 0, player?.skill_medic_2 ?: 0, player?.skill_medic_3 ?: 0),
                            skillDescriptions = listOf(
                                SkillItem("Оптимизация Шага", "Расход энергии на шаг снижен на 1 ед.", 10),
                                SkillItem("Авто-Рекуператор", "Каждый шаг в рейде регенерирует +2 HP.", 30),
                                SkillItem("Нейро-Связь", "Эффективность лечения нано-аптечками +100%.", 100)
                            ),
                            shardsCount = shardsCount,
                            onUpgrade = onUpgradeSkill
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // Respec Button
                        Button(
                            onClick = onRespecSkills,
                            modifier = Modifier.fillMaxWidth(),
                            shape = CutCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed)
                        ) {
                            Text("РЕКУРСИВНЫЙ СБРОС НАВЫКОВ (Цена: 500 BC)", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        }
                    }
                    3 -> {
                        // TAB 3: Global Leaderboard
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
                            ZzzIcon(R.drawable.ic_event_unknown, size = 14.dp)
                            Spacer(Modifier.width(6.dp))
                            Text(
                                "ГЛОБАЛЬНЫЙ РЕЙТИНГ ОПЕРАТОРОВ [SUPABASE NETWORK]",
                                color = EidosCyan,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }

                        if (isLeaderboardLoading) {
                            Box(modifier = Modifier.fillMaxWidth().height(200.dp), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(color = EidosCyan)
                            }
                        } else if (topPlayers.isEmpty()) {
                            Surface(
                                color = EidosGlass,
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color.Gray.copy(alpha = 0.3f)),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_action_scan, size = 14.dp, tint = Color.Gray)
                                        Spacer(Modifier.width(6.dp))
                                        Text("СЕТЬ АВТОНОМНА", color = Color.Gray, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text("Глобальные данные загружаются. Проверьте подключение к базе Supabase.", color = Color.LightGray, fontSize = 10.sp, textAlign = TextAlign.Center)
                                }
                            }
                        } else {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                topPlayers.forEachIndexed { index, p ->
                                    val isMe = p.deviceId == (player?.uid?.toString() ?: "")
                                    Surface(
                                        color = if (isMe) EidosCyan.copy(alpha = 0.2f) else EidosGlass,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if (isMe) EidosCyan else Color.White.copy(alpha = 0.1f)),
                                        shape = CutCornerShape(6.dp),
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Row(
                                            modifier = Modifier.padding(12.dp),
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.SpaceBetween
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                                Text(
                                                    text = "#${index + 1}",
                                                    color = if (index < 3) Color.Yellow else Color.Gray,
                                                    fontSize = 14.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    modifier = Modifier.width(32.dp)
                                                )
                                                Column {
                                                    Text(
                                                        text = p.username + if (isMe) " (ВЫ)" else "",
                                                        color = if (isMe) EidosCyan else Color.White,
                                                        fontWeight = FontWeight.Bold,
                                                        fontSize = 13.sp
                                                    )
                                                    Text(
                                                        text = "ГЛУБИНА: ${if (isMe && (player?.max_depth ?: 0) > p.maxDepth) player?.max_depth else p.maxDepth}м",
                                                        color = Color.Gray,
                                                        fontSize = 10.sp,
                                                        fontFamily = FontFamily.Monospace
                                                    )
                                                }
                                            }
                                            Column(horizontalAlignment = Alignment.End) {
                                                Text("УР. ${p.level}", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                                Text("${p.exp} XP", color = Color.LightGray, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    4 -> {
                        // TAB 4: Syndicate & Referral Network
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(14.dp)
                        ) {
                            // My Referral Code Card
                            val myRefCode = player?.referral_code ?: "EIDOS-${(player?.username?.take(6) ?: player?.uid?.toString()?.take(6) ?: "NET001").uppercase()}"
                            Surface(
                                color = EidosGlass,
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon.copy(alpha = 0.5f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_action_skill, size = 12.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("ВАШ РЕФЕРАЛЬНЫЙ КОД ОПЕРАТОРА", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                                    }
                                    Text("Приглашайте союзников в EIDOS: каждый новый агент получает +250 BC, и вы получаете +250 BC за каждого рекрута!", color = Color.Gray, fontSize = 10.sp)
                                    Spacer(modifier = Modifier.height(8.dp))

                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(myRefCode, color = Color.White, fontWeight = FontWeight.Black, fontSize = 16.sp, fontFamily = FontFamily.Monospace)
                                        Button(
                                            onClick = {
                                                val clipboard = context.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as? android.content.ClipboardManager
                                                val clip = android.content.ClipData.newPlainText("EIDOS Code", myRefCode)
                                                clipboard?.setPrimaryClip(clip)
                                                hapticManager.click()
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.2f)),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                            shape = CutCornerShape(4.dp),
                                            modifier = Modifier.height(34.dp)
                                        ) {
                                            Text("КОПИРОВАТЬ", color = EidosNeon, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                        }
                                    }
                                }
                            }

                            // Redeem Referral Card
                            Surface(
                                color = EidosGlass,
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.4f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_chest, size = 12.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("АКТИВАЦИЯ КОДА СИНДИКАТА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                                    }
                                    Text("Введите реферальный или промо-код оператора для начисления бонусных BioCoins.", color = Color.Gray, fontSize = 10.sp)
                                    Spacer(modifier = Modifier.height(8.dp))

                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        OutlinedTextField(
                                            value = referralInput,
                                            onValueChange = { referralInput = it.uppercase() },
                                            placeholder = { Text("EIDOS-XXXXXX", color = Color.DarkGray, fontSize = 11.sp) },
                                            singleLine = true,
                                            modifier = Modifier.weight(1f),
                                            colors = OutlinedTextFieldDefaults.colors(
                                                focusedBorderColor = EidosCyan,
                                                unfocusedBorderColor = Color.DarkGray,
                                                focusedTextColor = Color.White,
                                                unfocusedTextColor = Color.White
                                            )
                                        )
                                        Button(
                                            onClick = {
                                                if (referralInput.isNotBlank()) {
                                                    onRedeemReferralCode(referralInput)
                                                    referralInput = ""
                                                    hapticManager.success()
                                                }
                                            },
                                            colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.3f)),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                            shape = CutCornerShape(4.dp),
                                            modifier = Modifier.height(52.dp)
                                        ) {
                                            Text("ВВЕСТИ", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                        }
                                    }
                                }
                            }

                            // Operator Encrypted Signal (SOS / Network transmission)
                            Surface(
                                color = EidosGlass,
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFB300).copy(alpha = 0.4f)),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_action_scan, size = 12.dp)
                                        Spacer(Modifier.width(4.dp))
                                        Text("СЕТЕВОЙ ПЕРЕДАТЧИК (SIGNAL RELAY)", color = Color(0xFFFFB300), fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                                    }
                                    Text("Отправка зашифрованного пакета данных другому оператору EIDOS.", color = Color.Gray, fontSize = 10.sp)
                                    Spacer(modifier = Modifier.height(8.dp))

                                    OutlinedTextField(
                                        value = signalRecipient,
                                        onValueChange = { signalRecipient = it },
                                        placeholder = { Text("Позывной или ID получателя...", color = Color.DarkGray, fontSize = 11.sp) },
                                        singleLine = true,
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = OutlinedTextFieldDefaults.colors(
                                            focusedBorderColor = Color(0xFFFFB300),
                                            unfocusedBorderColor = Color.DarkGray,
                                            focusedTextColor = Color.White,
                                            unfocusedTextColor = Color.White
                                        )
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    OutlinedTextField(
                                        value = signalMessage,
                                        onValueChange = { signalMessage = it },
                                        placeholder = { Text("Шифрограмма сообщения...", color = Color.DarkGray, fontSize = 11.sp) },
                                        singleLine = true,
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = OutlinedTextFieldDefaults.colors(
                                            focusedBorderColor = Color(0xFFFFB300),
                                            unfocusedBorderColor = Color.DarkGray,
                                            focusedTextColor = Color.White,
                                            unfocusedTextColor = Color.White
                                        )
                                    )
                                    Spacer(modifier = Modifier.height(10.dp))
                                    Button(
                                        onClick = {
                                            if (signalRecipient.isNotBlank() && signalMessage.isNotBlank()) {
                                                onSendSignal(signalRecipient, signalMessage)
                                                signalMessage = ""
                                                hapticManager.criticalHit()
                                            }
                                        },
                                        modifier = Modifier.fillMaxWidth().height(44.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFFB300).copy(alpha = 0.25f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFB300)),
                                        shape = CutCornerShape(4.dp)
                                    ) {
                                        Text("ОТПРАВИТЬ СИГНАЛ В СЕТЬ", color = Color(0xFFFFB300), fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                    }
                                }
                            }
                        }
                    }

                    5 -> {
                        // TAB 5: Radio / Mailbox Transmissions (ZZZ Terminal Inbox)
                        io.eidos.zerolayer.ui.components.ZzzWindowCard(
                            title = "ТЕРМИНАЛ СВЯЗИ // EIDOS-INBOX",
                            subTitle = "КВАНТОВЫЙ ТРАНСЛЯТОР ПАКЕТОВ",
                            headerBadge = if (unclaimedRadioMessagesCount > 0) "NEW: $unclaimedRadioMessagesCount" else "ONLINE",
                            borderColor = if (unclaimedRadioMessagesCount > 0) io.eidos.zerolayer.ui.theme.ZzzAcidYellow else io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                "Дешифрованные квантовые трансляции, сетевые награды за операции и радиосигналы из глубин Бездны Z-Layer.",
                                color = io.eidos.zerolayer.ui.theme.ZzzTextBody,
                                fontSize = 11.sp,
                                fontFamily = FontFamily.SansSerif,
                                modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)
                            )

                            if (radioMessages.isEmpty()) {
                                Surface(
                                    color = Color(0xFF10131D),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.15f)),
                                    shape = CutCornerShape(6.dp),
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                                ) {
                                    Column(
                                        modifier = Modifier.fillMaxWidth().padding(16.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        ZzzIcon(R.drawable.ic_event_unknown, size = 32.dp)
                                        Spacer(Modifier.height(8.dp))
                                        Text(
                                            "ВХОДЯЩИХ ТРАНСЛЯЦИЙ ПОКА НЕТ",
                                            color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.ExtraBold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Spacer(Modifier.height(6.dp))
                                        Text(
                                            "Условия перехвата пакетов данных:\n" +
                                            "• Теневой Брокер: совершить 5+ рейдов\n" +
                                            "• SOS Осколок: достичь глубины 100+ метров\n" +
                                            "• Центральное Ядро: серия синхронизации 3+ дня",
                                            color = Color.Gray,
                                            fontSize = 10.sp,
                                            lineHeight = 15.sp,
                                            fontFamily = FontFamily.Monospace,
                                            textAlign = TextAlign.Center
                                        )
                                    }
                                }
                            } else {
                                Column(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalArrangement = Arrangement.spacedBy(10.dp)
                                ) {
                                    radioMessages.forEach { msg ->
                                        val isClaimed = msg.isClaimed
                                        io.eidos.zerolayer.ui.components.ZzzWindowCard(
                                            title = msg.sender,
                                            headerBadge = if (isClaimed) "ПРОЧИТАНО" else "NEW SIGNAL",
                                            borderColor = if (!isClaimed) io.eidos.zerolayer.ui.theme.ZzzAcidYellow else Color.Gray,
                                            modifier = Modifier.fillMaxWidth()
                                        ) {
                                            Column(modifier = Modifier.fillMaxWidth()) {
                                                Text(msg.title, color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp, fontFamily = FontFamily.SansSerif)
                                                Spacer(modifier = Modifier.height(2.dp))
                                                Text(msg.body, color = io.eidos.zerolayer.ui.theme.ZzzTextBody, fontSize = 11.5.sp, lineHeight = 16.sp)
                                                if (msg.rewardCoins > 0L || msg.rewardXp > 0L) {
                                                    Spacer(modifier = Modifier.height(8.dp))
                                                    Row(
                                                        verticalAlignment = Alignment.CenterVertically,
                                                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                                                    ) {
                                                        if (msg.rewardCoins > 0L) {
                                                            io.eidos.zerolayer.ui.components.ZzzBadge(
                                                                text = "НАГРАДА: +${msg.rewardCoins} BC",
                                                                color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                                                textColor = Color.Black
                                                            )
                                                        }
                                                        if (msg.rewardXp > 0L) {
                                                            io.eidos.zerolayer.ui.components.ZzzBadge(
                                                                text = "+${msg.rewardXp} XP",
                                                                color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                                                textColor = Color.Black
                                                            )
                                                        }
                                                    }
                                                }
                                                if (!isClaimed) {
                                                    Spacer(modifier = Modifier.height(10.dp))
                                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                                        text = "ЗАБРАТЬ НАГРАДУ >",
                                                        onClick = { onClaimRadioMessage(msg.id) },
                                                        primaryColor = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                                        borderColor = Color.White,
                                                        textColor = Color.Black,
                                                        height = 38.dp,
                                                        modifier = Modifier.fillMaxWidth()
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
        }

        if (showTerminalDialog) {
            EidosTerminalDialog(
                player = player,
                onDismiss = { showTerminalDialog = false },
                onForceSync = {
                    if (player != null) {
                        SupabaseClientManager.syncPlayer(
                            SupabasePlayer(
                                deviceId = player.uid.toString(),
                                username = player.username ?: "Оператор",
                                level = player.level,
                                exp = player.xp,
                                biocoins = player.biocoin,
                                hp = player.hp,
                                energy = player.energy,
                                rank = player.faction
                            )
                        )
                    }
                }
            )
        }

        if (showAvatarInspector) {
            val isUnlocked = inspectedAvatarLvl <= actualLevel
            val isCurrent = inspectedAvatarLvl == actualLevel
            val stageInfo = io.eidos.zerolayer.data.PlayerProgressManager.getLevelInfo(inspectedAvatarLvl)

            Dialog(
                onDismissRequest = { showAvatarInspector = false },
                properties = DialogProperties(usePlatformDefaultWidth = false)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.92f))
                        .clickable { showAvatarInspector = false },
                    contentAlignment = Alignment.Center
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(0.94f)
                            .clip(CutCornerShape(12.dp))
                            .background(Color(0xFF090D1A))
                            .border(1.5.dp, if (isUnlocked) EidosCyan else Color(0xFFFF5252).copy(alpha = 0.7f), CutCornerShape(12.dp))
                            .clickable(enabled = false) {}
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
                                Column {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_anomaly, size = 16.dp)
                                        Spacer(Modifier.width(6.dp))
                                        Text(
                                            "ДОСЬЕ НЕЙРО-ЭВОЛЮЦИИ",
                                            color = if (isUnlocked) EidosCyan else Color(0xFFFF5252),
                                            fontSize = 14.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                    Text(
                                        "ХРОНИКА БИОМЕХАНИЧЕСКИХ ТРАНСФОРМАЦИЙ ОПЕРАТОРА",
                                        color = Color.Gray,
                                        fontSize = 9.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                Box(
                                    modifier = Modifier
                                        .size(30.dp)
                                        .background(Color.Black.copy(alpha = 0.6f), CutCornerShape(4.dp))
                                        .border(1.dp, EidosCyan.copy(alpha = 0.5f), CutCornerShape(4.dp))
                                        .clickable { showAvatarInspector = false },
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text("X", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                }
                            }

                            Spacer(modifier = Modifier.height(12.dp))

                            // Avatar Viewport (Revealed if unlocked, Classified & Hidden if not)
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(230.dp)
                                    .clip(CutCornerShape(8.dp))
                                    .border(
                                        1.5.dp,
                                        if (isCurrent) EidosNeon else if (isUnlocked) EidosCyan else Color(0xFFFF5252).copy(alpha = 0.6f),
                                        CutCornerShape(8.dp)
                                    )
                                    .background(Color.Black)
                            ) {
                                if (isUnlocked) {
                                    // Player has reached this level: Display the evolved artwork!
                                    EidosImage(
                                        resName = "lvl_$inspectedAvatarLvl",
                                        borderColor = Color.Transparent,
                                        borderWidth = 0.dp,
                                        contentScale = ContentScale.Crop,
                                        modifier = Modifier.fillMaxSize()
                                    )

                                    // Cyber scanline gradient
                                    Box(
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .background(
                                                Brush.verticalGradient(
                                                    colors = listOf(
                                                        Color.Transparent,
                                                        Color.Transparent,
                                                        Color.Black.copy(alpha = 0.85f)
                                                    )
                                                )
                                            )
                                    )
                                } else {
                                    // Future level: Player CANNOT see it yet! Redacted / Classified view.
                                    Box(
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .background(Color(0xFF070A12)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        CyberGridOverlay(modifier = Modifier.fillMaxSize())

                                        Column(
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            modifier = Modifier.padding(16.dp)
                                        ) {
                                            ZzzIcon(R.drawable.ic_ui_locked, size = 38.dp, tint = Color(0xFFFF5252))
                                            Spacer(modifier = Modifier.height(6.dp))
                                            Text(
                                                "СТАДИЯ НЕ ДОСТИГНУТА",
                                                color = Color(0xFFFF5252),
                                                fontSize = 13.sp,
                                                fontWeight = FontWeight.Black,
                                                fontFamily = FontFamily.Monospace
                                            )
                                            Spacer(modifier = Modifier.height(4.dp))
                                            Text(
                                                "Облик следующей формы эволюции засекречен.\nДостигните Уровня $inspectedAvatarLvl для дешифровки нейро-матрицы.",
                                                color = Color.LightGray,
                                                fontSize = 10.sp,
                                                fontFamily = FontFamily.Monospace,
                                                textAlign = TextAlign.Center
                                            )
                                        }
                                    }
                                }

                                // Stage badge (top-left)
                                Box(
                                    modifier = Modifier
                                        .align(Alignment.TopStart)
                                        .padding(10.dp)
                                        .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                        .border(1.dp, if (isUnlocked) EidosCyan else Color(0xFFFF5252), CutCornerShape(4.dp))
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        "СТАДИЯ $inspectedAvatarLvl / 31",
                                        color = if (isUnlocked) EidosCyan else Color(0xFFFF5252),
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }

                                // Status badge (top-right)
                                Box(
                                    modifier = Modifier
                                        .align(Alignment.TopEnd)
                                        .padding(10.dp)
                                        .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                        .border(
                                            1.dp,
                                            if (isCurrent) EidosNeon else if (isUnlocked) EidosCyan else Color(0xFFFF5252),
                                            CutCornerShape(4.dp)
                                        )
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        when {
                                            isCurrent -> "ТЕКУЩИЙ ОБЛИК"
                                            isUnlocked -> "ПРОЙДЕННАЯ СТАДИЯ"
                                            else -> "ЗАСЕКРЕЧЕНО"
                                        },
                                        color = when {
                                            isCurrent -> EidosNeon
                                            isUnlocked -> EidosCyan
                                            else -> Color(0xFFFF5252)
                                        },
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Dossier Details Card
                            Surface(
                                modifier = Modifier.fillMaxWidth(),
                                color = Color(0xFF0F1424),
                                shape = CutCornerShape(8.dp),
                                border = androidx.compose.foundation.BorderStroke(
                                    1.dp,
                                    if (isUnlocked) EidosCyan.copy(alpha = 0.4f) else Color(0xFFFF5252).copy(alpha = 0.3f)
                                )
                            ) {
                                Column(modifier = Modifier.padding(10.dp)) {
                                    if (isUnlocked) {
                                        Text(
                                            "${stageInfo.rankTitle} // ${stageInfo.stageTitle}",
                                            color = if (isCurrent) EidosNeon else Color.White,
                                            fontWeight = FontWeight.Black,
                                            fontSize = 13.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            stageInfo.sloganText,
                                            color = Color.LightGray,
                                            fontSize = 11.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Spacer(modifier = Modifier.height(6.dp))
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            ZzzIcon(R.drawable.ic_res_energy, size = 12.dp)
                                            Spacer(Modifier.width(4.dp))
                                            Text(
                                                "СПОСОБНОСТЬ: ${stageInfo.perkTitle} — ${stageInfo.perkDescription}",
                                                color = Color(0xFFFFB300),
                                                fontSize = 10.sp,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                        Spacer(modifier = Modifier.height(2.dp))
                                        Text(
                                            "БОНУСЫ ЯДРА: +${stageInfo.bonusHp} HP  •  +${stageInfo.bonusAtk} ATK  •  +${stageInfo.bonusDef} DEF",
                                            color = EidosCyan,
                                            fontSize = 9.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    } else {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            ZzzIcon(R.drawable.ic_ui_locked, size = 12.dp, tint = Color(0xFFFF5252))
                                            Spacer(Modifier.width(4.dp))
                                            Text(
                                                "СТАДИЯ $inspectedAvatarLvl // [ДАННЫЕ ЗАСЕКРЕЧЕНЫ]",
                                                color = Color(0xFFFF5252),
                                                fontWeight = FontWeight.Black,
                                                fontSize = 13.sp,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        }
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            "Биомеханическая форма еще не синтезирована. Каждая следующая фаза превосходит предыдущую по боевой мощи и кибер-адаптации.",
                                            color = Color.Gray,
                                            fontSize = 11.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        Spacer(modifier = Modifier.height(6.dp))
                                        Text(
                                            "ТРЕБУЕТСЯ ОПЫТА: ${stageInfo.requiredXp} XP (Осталось: ${(stageInfo.requiredXp - currentXp).coerceAtLeast(0)} XP)",
                                            color = Color(0xFFFFB300),
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Prev / Next Navigation Row
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .background(
                                            if (inspectedAvatarLvl > 1) EidosCyan.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                                            CutCornerShape(6.dp)
                                        )
                                        .border(
                                            1.dp,
                                            if (inspectedAvatarLvl > 1) EidosCyan else Color.DarkGray,
                                            CutCornerShape(6.dp)
                                        )
                                        .clickable(enabled = inspectedAvatarLvl > 1) {
                                            if (inspectedAvatarLvl > 1) inspectedAvatarLvl--
                                        }
                                        .padding(vertical = 8.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        "◀ СТАДИЯ ${inspectedAvatarLvl - 1}",
                                        color = if (inspectedAvatarLvl > 1) EidosCyan else Color.Gray,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }

                                Spacer(modifier = Modifier.width(10.dp))

                                Box(
                                    modifier = Modifier
                                        .weight(1f)
                                        .background(
                                            if (inspectedAvatarLvl < 31) EidosCyan.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                                            CutCornerShape(6.dp)
                                        )
                                        .border(
                                            1.dp,
                                            if (inspectedAvatarLvl < 31) EidosCyan else Color.DarkGray,
                                            CutCornerShape(6.dp)
                                        )
                                        .clickable(enabled = inspectedAvatarLvl < 31) {
                                            if (inspectedAvatarLvl < 31) inspectedAvatarLvl++
                                        }
                                        .padding(vertical = 8.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        "СТАДИЯ ${inspectedAvatarLvl + 1} ▶",
                                        color = if (inspectedAvatarLvl < 31) EidosCyan else Color.Gray,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Horizontal strip of all 31 stages
                            Text(
                                "ХРОНИКА ЭВОЛЮЦИИ (1 - 31):",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.fillMaxWidth(),
                                textAlign = TextAlign.Start
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(5.dp)
                            ) {
                                (1..31).forEach { lvl ->
                                    val isLvlInspected = lvl == inspectedAvatarLvl
                                    val isLvlUnlocked = lvl <= actualLevel
                                    val isLvlActive = lvl == actualLevel

                                    Box(
                                        modifier = Modifier
                                            .size(32.dp)
                                            .background(
                                                when {
                                                    isLvlInspected && isLvlUnlocked -> EidosCyan
                                                    isLvlInspected -> Color(0xFFFF5252).copy(alpha = 0.4f)
                                                    isLvlActive -> EidosNeon.copy(alpha = 0.35f)
                                                    isLvlUnlocked -> EidosCyan.copy(alpha = 0.15f)
                                                    else -> Color.Black.copy(alpha = 0.6f)
                                                },
                                                CutCornerShape(4.dp)
                                            )
                                            .border(
                                                1.dp,
                                                when {
                                                    isLvlInspected && isLvlUnlocked -> Color.White
                                                    isLvlInspected -> Color(0xFFFF5252)
                                                    isLvlActive -> EidosNeon
                                                    isLvlUnlocked -> EidosCyan.copy(alpha = 0.6f)
                                                    else -> Color.DarkGray.copy(alpha = 0.5f)
                                                },
                                                CutCornerShape(4.dp)
                                            )
                                            .clickable {
                                                inspectedAvatarLvl = lvl
                                            },
                                        contentAlignment = Alignment.Center
                                    ) {
                                        if (isLvlUnlocked) {
                                            Text(
                                                text = "$lvl",
                                                color = when {
                                                    isLvlInspected && isLvlUnlocked -> Color.Black
                                                    isLvlActive -> EidosNeon
                                                    isLvlUnlocked -> Color.White
                                                    else -> Color.Gray
                                                },
                                                fontSize = 11.sp,
                                                fontWeight = FontWeight.Bold,
                                                fontFamily = FontFamily.Monospace
                                            )
                                        } else {
                                            ZzzIcon(
                                                iconRes = R.drawable.ic_ui_locked,
                                                size = 10.dp,
                                                tint = Color.Gray
                                            )
                                        }
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            // Evolutionary rule notification (no downgrades / active avatar is immutable)
                            Text(
                                "Кибер-эволюция необратима: ваш активный аватар навсегда закреплен за наивысшей достигнутой ступенью (Уровень $actualLevel). Пройденные стадии сохранены в досье.",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center,
                                modifier = Modifier.padding(horizontal = 8.dp)
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            // Close button
                            Button(
                                onClick = {
                                    showAvatarInspector = false
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Color.White.copy(alpha = 0.1f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                shape = CutCornerShape(6.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    "ЗАКРЫТЬ ДОСЬЕ",
                                    color = EidosCyan,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
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

@Composable
fun StatCard(label: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .background(EidosGlass)
            .border(1.dp, color.copy(alpha = 0.3f))
            .padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(label, color = color, fontSize = 10.sp, fontWeight = FontWeight.Bold)
        Text(value, color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun SkillBranchHeader(title: String, color: Color) {
    Text(
        text = title,
        color = color,
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        textAlign = TextAlign.Start,
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
    )
}

@Composable
fun SkillNodeRow(
    branchName: String,
    skillsUnlocked: List<Int>,
    skillDescriptions: List<SkillItem>,
    shardsCount: Int,
    onUpgrade: (String, Int) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(EidosGlass)
            .border(1.dp, Color.White.copy(alpha = 0.1f))
            .padding(12.dp)
    ) {
        skillDescriptions.forEachIndexed { index, skill ->
            val step = index + 1
            val isUnlocked = skillsUnlocked.getOrElse(index) { 0 } == 1
            val canUnlock = !isUnlocked && (index == 0 || skillsUnlocked.getOrElse(index - 1) { 0 } == 1)

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            "${step}. ${skill.name}",
                            color = if (isUnlocked) EidosNeon else Color.White,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                        if (isUnlocked) {
                            Spacer(Modifier.width(4.dp))
                            ZzzIcon(R.drawable.ic_ui_unlocked, size = 10.dp, tint = EidosNeon)
                        }
                    }
                    Text(skill.desc, color = Color.Gray, fontSize = 10.sp)
                }

                if (isUnlocked) {
                    Text(
                        "РАЗБЛОКИРОВАН",
                        color = EidosNeon,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                } else {
                    Button(
                        onClick = { onUpgrade(branchName, step) },
                        enabled = canUnlock && shardsCount >= skill.cost,
                        shape = CutCornerShape(4.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = EidosCyan,
                            disabledContainerColor = Color.DarkGray
                        ),
                        modifier = Modifier.height(32.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "${skill.cost}",
                                color = if (canUnlock && shardsCount >= skill.cost) Color.Black else Color.Gray,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(Modifier.width(2.dp))
                            ZzzIcon(R.drawable.ic_res_eidos_shard, size = 10.dp)
                        }
                    }
                }
            }
            if (index < skillDescriptions.size - 1) {
                HorizontalDivider(color = Color.White.copy(alpha = 0.05f), modifier = Modifier.padding(vertical = 4.dp))
            }
        }
    }
}

@Composable
private fun TabButton(text: String, selected: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Surface(
        color = if (selected) EidosCyan.copy(alpha = 0.25f) else Color.Transparent,
        border = androidx.compose.foundation.BorderStroke(1.dp, if (selected) EidosCyan else Color.Transparent),
        shape = CutCornerShape(4.dp),
        modifier = modifier.clickable { onClick() }
    ) {
        Text(
            text = text,
            color = if (selected) EidosCyan else Color.Gray,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp)
        )
    }
}

@Composable
private fun MetricRow(
    icon: String? = null,
    drawableRes: Int? = null,
    label: String,
    value: String,
    valueColor: Color = Color.White
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (drawableRes != null) {
                Image(
                    painter = painterResource(id = drawableRes),
                    contentDescription = label,
                    modifier = Modifier
                        .size(16.dp)
                        .padding(end = 4.dp),
                    contentScale = ContentScale.Fit
                )
            } else if (icon != null) {
                Text(icon, fontSize = 14.sp, modifier = Modifier.padding(end = 6.dp))
            }
            Text(label, color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
        }
        Text(value, color = valueColor, fontSize = 12.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
    }
}
