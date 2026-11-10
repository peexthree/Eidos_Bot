package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.ForgeRecipeCategory
import io.eidos.zerolayer.data.ForgeRecipeDefinition
import io.eidos.zerolayer.data.ForgeRecipeRegistry
import io.eidos.zerolayer.data.InventoryItem
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.ui.platform.LocalContext
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.theme.EidosOrange
import io.eidos.zerolayer.ui.theme.EidosPurple
import io.eidos.zerolayer.ui.theme.ZzzGold
import io.eidos.zerolayer.ui.theme.ZzzDangerRed
import io.eidos.zerolayer.ui.theme.ZzzWarningOrange
import io.eidos.zerolayer.ui.theme.ZzzToxicGreen
import io.eidos.zerolayer.ui.theme.ZzzAcidYellow
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import kotlinx.coroutines.delay
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.VideoBackground
import androidx.compose.ui.draw.alpha
import io.eidos.zerolayer.ui.components.CyberParticleOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.ParticlePreset
import io.eidos.zerolayer.ui.components.ZzzIcon

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ForgeScreen(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    preselectedItem: InventoryItem? = null,
    onDismantle: (InventoryItem) -> Unit,
    onMerge: (InventoryItem) -> Unit,
    onCraft: (String) -> Unit,
    onRepairBC: (InventoryItem) -> Unit,
    onRepairShards: (InventoryItem) -> Unit,
    onRerollChip: (InventoryItem) -> Unit = {},
    onDataSlicer: (InventoryItem) -> Unit = {},
    onQuantumTuner: (InventoryItem) -> Unit = {},
    onSocketPuncher: (InventoryItem) -> Unit = {},
    onChromaticInjector: (InventoryItem) -> Unit = {},
    onVaalCorruption: (InventoryItem) -> Unit = {},
    onInsertChip: (InventoryItem, Int, io.eidos.zerolayer.data.DataChip) -> Unit = { _, _, _ -> },
    onRemoveChip: (InventoryItem, Int) -> Unit = { _, _ -> },
    onApplyCustomMod: (InventoryItem, io.eidos.zerolayer.data.CyberEquipment, Long, String) -> Unit = { _, _, _, _ -> },
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    LaunchedEffect(Unit) {
        val tutorialPrefs = context.getSharedPreferences("eidos_tutorial_prefs", android.content.Context.MODE_PRIVATE)
        if (!tutorialPrefs.getBoolean("eva_tip_forge_played", false)) {
            tutorialPrefs.edit().putBoolean("eva_tip_forge_played", true).apply()
            audio.playEvaHubVoice(EidosAudioManager.EvaHubVoiceType.TIP_FORGE)
        }
    }

    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("СИНТЕЗ", "МОДДИНГ СОКЕТОВ", "КОРРУПЦИЯ")

    // State for interactive recalibration
    var showComparisonDialog by remember { mutableStateOf(false) }
    var currentModItem by remember { mutableStateOf<InventoryItem?>(null) }
    var originalEquipment by remember { mutableStateOf<io.eidos.zerolayer.data.CyberEquipment?>(null) }
    var prospectiveEquipment by remember { mutableStateOf<io.eidos.zerolayer.data.CyberEquipment?>(null) }
    var prospectiveRarity by remember { mutableStateOf("common") }
    var prospectiveCost by remember { mutableStateOf(250L) }

    // EE-4: Сервисный Терминал Архитекторов
    var showRootTerminalDialog by remember { mutableStateOf(false) }
    var rootInputCode by remember { mutableStateOf("") }
    var rootTerminalMessage by remember { mutableStateOf<String?>(null) }

    // A1 UX: предмет, переданный из Инвентаря (кнопка «🔧 ВЕРСТАК»), сразу в моддинг
    androidx.compose.runtime.LaunchedEffect(preselectedItem) {
        if (preselectedItem != null) {
            currentModItem = preselectedItem
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            buildAnnotatedString {
                                withStyle(SpanStyle(color = EidosCyan)) { append("КУЗНЯ ") }
                                withStyle(SpanStyle(color = ZzzAcidYellow)) { append("// МОДЕРНИЗАЦИЯ") }
                            },
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                        Text(
                            "СЫРЬЕ: ${inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0} ОСКОЛКОВ | ${player?.biocoin ?: 0} BC | УР. ${player?.level ?: 1}",
                            color = Color.Gray,
                            fontSize = 9.sp,
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
                    IconButton(onClick = { showRootTerminalDialog = true }) {
                        Text("📟", fontSize = 16.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
            )
        },
        containerColor = Color(0xFF060402)
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            // Background and VFX: Living Plasma Reactor
            VideoBackground(resName = "bg_forge", modifier = Modifier.fillMaxSize())
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_forge),
                contentDescription = null,
                modifier = Modifier.fillMaxSize().alpha(0.35f),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = Alignment.Center
            )
            CyberGridOverlay(modifier = Modifier.fillMaxSize())
            CyberParticleOverlay(preset = ParticlePreset.FORGE_SPARKS)

            Column(modifier = Modifier.fillMaxSize()) {
                io.eidos.zerolayer.ui.components.FirstTimeTooltip(
                    prefKey = "tooltip_shown_forge",
                    text = "Здесь усиливай предметы. Начни с Заточки, чтобы повысить характеристики снаряжения.",
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                )
                TabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = Color.Black,
                    contentColor = EidosCyan,
                    indicator = { tabPositions ->
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                            color = EidosCyan
                        )
                    }
                ) {
                    tabs.forEachIndexed { index, title ->
                        Tab(
                            selected = selectedTab == index,
                            onClick = {
                                haptics.click()
                                audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                                selectedTab = index
                            },
                            text = { Text(title, fontSize = 9.sp, fontWeight = FontWeight.Bold) }
                        )
                    }
                }

                // EVA-09 Assistant Explanation Banner
                Surface(
                    color = EidosCyan.copy(alpha = 0.12f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.3f)),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
                    shape = androidx.compose.foundation.shape.CutCornerShape(4.dp)
                ) {
                    val bannerText = when (selectedTab) {
                        0 -> "СИНТЕЗ: Слияние дубликатов 2-в-1 до высших рангов или крафт снаряжения из осколков Эйдоса."
                        1 -> "МОДДИНГ СОКЕТОВ: Настройка гнезд под чипы. Роллируйте статы с фиксацией замков (макс. 2 заморозки, +50% BC за замок)."
                        else -> "КОРРУПЦИЯ: Заражение предметов хаотическим глитч-кодом. Дает мощнейший скрытый бонус, но полностью блокирует модификацию."
                    }
                    Text(
                        text = bannerText,
                        color = Color.White,
                        fontSize = 9.sp,
                        lineHeight = 13.sp,
                        modifier = Modifier.padding(8.dp)
                    )
                }

                when (selectedTab) {
                    0 -> SynthesisTab(
                        player = player,
                        inventory = inventory,
                        allItemsMetadata = allItemsMetadata,
                        onDismantle = onDismantle,
                        onMerge = onMerge,
                        onCraft = onCraft
                    )
                    1 -> SocketModdingTab(
                        player = player,
                        inventory = inventory,
                        allItemsMetadata = allItemsMetadata,
                        onQuantumTuner = onQuantumTuner,
                        onSocketPuncher = onSocketPuncher,
                        onChromaticInjector = onChromaticInjector,
                        onInsertChip = onInsertChip,
                        onRemoveChip = onRemoveChip,
                        onTriggerSlicerReroll = { item, oldEq, prospectiveEq, finalCost, rarity ->
                            currentModItem = item
                            originalEquipment = oldEq
                            prospectiveEquipment = prospectiveEq
                            prospectiveRarity = rarity
                            prospectiveCost = finalCost
                            showComparisonDialog = true
                        }
                    )
                    2 -> DataCorruptionTab(
                        player = player,
                        inventory = inventory,
                        allItemsMetadata = allItemsMetadata,
                        onVaalCorruption = onVaalCorruption
                    )
                }
            }
        }
    }

    // Interactive Comparison Dialog (Before/After)
    if (showComparisonDialog && currentModItem != null && originalEquipment != null && prospectiveEquipment != null) {
        val itemMeta = allItemsMetadata.find { it.id == currentModItem!!.item_id }
        val itemName = itemMeta?.name ?: getItemName(currentModItem!!.item_id)

        AlertDialog(
            onDismissRequest = { showComparisonDialog = false },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_menu_forge, size = 16.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "[ПЕРЕКАЛИБРОВКА: СРАВНЕНИЕ СТАТОВ]",
                        color = EidosCyan,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            text = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        "Слайсер сгенерировал новый вариант. Выберите, сохранить ли новые значения или отклонить:",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 15.sp
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        // Left: Current stats
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color.White.copy(alpha = 0.05f)),
                            modifier = Modifier.weight(1f).border(1.dp, Color.Gray.copy(alpha = 0.3f), CutCornerShape(4.dp))
                        ) {
                            Column(modifier = Modifier.padding(8.dp)) {
                                Text("ТЕКУЩИЕ ПАРАМЕТРЫ", color = Color.Gray, fontWeight = FontWeight.Bold, fontSize = 9.sp)
                                Spacer(modifier = Modifier.height(6.dp))
                                originalEquipment!!.affixes.forEach { affix ->
                                    Text("${affix.statType}: +${affix.currentValue}", color = Color.LightGray, fontSize = 11.sp)
                                }
                            }
                        }

                        // Right: Prospective stats
                        Card(
                            colors = CardDefaults.cardColors(containerColor = EidosNeon.copy(alpha = 0.08f)),
                            modifier = Modifier.weight(1f).border(1.dp, EidosNeon.copy(alpha = 0.3f), CutCornerShape(4.dp))
                        ) {
                            Column(modifier = Modifier.padding(8.dp)) {
                                Text("НОВЫЕ ПАРАМЕТРЫ", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 9.sp)
                                Spacer(modifier = Modifier.height(6.dp))
                                prospectiveEquipment!!.affixes.forEach { affix ->
                                    Text("${affix.statType}: +${affix.currentValue}", color = EidosNeon, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        "Списание операции: ${prospectiveCost} BioCoins.",
                        color = Color.Yellow,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        onApplyCustomMod(
                            currentModItem!!,
                            prospectiveEquipment!!,
                            prospectiveCost,
                            "[СЛАЙСЕР]: Перекалибровка аффиксов в $itemName успешно завершена! Списано $prospectiveCost BC."
                        )
                        showComparisonDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ПРИНЯТЬ НОВЫЕ", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 10.sp)
                }
            },
            dismissButton = {
                Button(
                    onClick = { showComparisonDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = Color.DarkGray),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ОСТАВИТЬ СТАРЫЕ", color = Color.White, fontSize = 10.sp)
                }
            },
            containerColor = Color(0xFF0C0904),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.border(1.5.dp, EidosCyan, CutCornerShape(8.dp))
        )
    }

    // EE-4: Сервисный Терминал Архитекторов
    if (showRootTerminalDialog) {
        val narrativePrefs = remember { context.getSharedPreferences("eidos_narrative_prefs", android.content.Context.MODE_PRIVATE) }
        AlertDialog(
            onDismissRequest = {
                showRootTerminalDialog = false
                rootTerminalMessage = null
            },
            containerColor = Color(0xFF0F151F),
            shape = CutCornerShape(10.dp),
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("📟", fontSize = 18.sp)
                    Spacer(Modifier.width(8.dp))
                    Text("СЕРВИСНЫЙ ТЕРМИНАЛ // ROOT", color = EidosCyan, fontSize = 13.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "Ввод инженерных директив Архитекторов 2099 года для сервисной отладки секторов.",
                        color = Color.LightGray,
                        fontSize = 10.sp
                    )
                    OutlinedTextField(
                        value = rootInputCode,
                        onValueChange = { rootInputCode = it },
                        placeholder = { Text("Например: 2099-ADMIN-VANCE", color = Color.Gray, fontSize = 11.sp) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        textStyle = androidx.compose.ui.text.TextStyle(color = Color.White, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                    )
                    rootTerminalMessage?.let { msg ->
                        Text(
                            text = msg,
                            color = if (msg.startsWith("👑")) ZzzGold else ZzzDangerRed,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val clean = rootInputCode.trim().uppercase()
                        if (clean == "2099-ADMIN-VANCE" || clean == "ADMIN-VANCE") {
                            narrativePrefs.edit().putBoolean("architect_code_unlocked", true).apply()
                            onCraft("eidos_shard")
                            haptics.criticalHit()
                            audio.playSound(EidosAudioManager.SoundType.SECRET_FOUND)
                            audio.playEvaEggVoice("vance")
                            rootTerminalMessage = "👑 [ДОСТУП АРХИТЕКТОРА]: Код 2099-ADMIN-VANCE принят! Разблокирован статус АРХИТЕКТОР, Лог №000 в Кодексе и начислено снабжение!"
                        } else {
                            haptics.click()
                            audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                            rootTerminalMessage = "❌ [ОТКАЗ В ДОСТУПЕ]: Неверный сертификат авторизации."
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ВВОД", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                }
            },
            dismissButton = {
                OutlinedButton(
                    onClick = {
                        showRootTerminalDialog = false
                        rootTerminalMessage = null
                    },
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ЗАКРЫТЬ", color = Color.Gray, fontSize = 11.sp)
                }
            }
        )
    }
}

@Composable
fun SynthesisTab(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    onDismantle: (InventoryItem) -> Unit,
    onMerge: (InventoryItem) -> Unit,
    onCraft: (String) -> Unit
) {
    var subTab by remember { mutableIntStateOf(0) } // 0: РАЗБОР И СЛИЯНИЕ, 1: КОВКА РЕЦЕПТОВ
    var pendingCraftRecipe by remember { mutableStateOf<ForgeRecipeDefinition?>(null) }

    // Visual craft feedback: id of the card currently pulsing (pure presentation, logic untouched)
    var craftingId by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(craftingId) {
        if (craftingId != null) {
            delay(600)
            craftingId = null
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Sub-navigation pills
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = { subTab = 0 },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (subTab == 0) EidosCyan.copy(alpha = 0.2f) else Color.Transparent
                ),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (subTab == 0) EidosCyan else Color.DarkGray),
                shape = CutCornerShape(4.dp),
                modifier = Modifier.weight(1f),
                contentPadding = PaddingValues(2.dp)
            ) {
                Text("УТИЛИЗАЦИЯ / СЛИЯНИЕ", color = if (subTab == 0) EidosCyan else Color.Gray, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
            Button(
                onClick = { subTab = 1 },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (subTab == 1) EidosCyan.copy(alpha = 0.2f) else Color.Transparent
                ),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (subTab == 1) EidosCyan else Color.DarkGray),
                shape = CutCornerShape(4.dp),
                modifier = Modifier.weight(1f),
                contentPadding = PaddingValues(2.dp)
            ) {
                Text("КОВКА ШЕЙДЕРОВ", color = if (subTab == 1) EidosCyan else Color.Gray, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
        }

        if (subTab == 0) {
            val dismantleable = inventory.filter { it.item_id != "eidos_shard" && !it.is_equipped }
            if (dismantleable.isEmpty()) {
                ForgeEmptyWorkbench(hint = "НЕТ ПРЕДМЕТОВ ДЛЯ УТИЛИЗАЦИИ ИЛИ СИНТЕЗА")
            } else {
                val groupedItems = remember(dismantleable) {
                    dismantleable.groupBy { it.item_id }.values.map { items ->
                        val totalCount = items.sumOf { it.quantity.coerceAtLeast(1) }
                        val rep = items.first()
                        Triple(rep, totalCount, items)
                    }
                }
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(groupedItems, key = { it.first.item_id }) { (repItem, totalCount, stack) ->
                        val itemMeta = allItemsMetadata.find { it.id == repItem.item_id }
                        val name = itemMeta?.name ?: getItemName(repItem.item_id)
                        val rarity = itemMeta?.rarity ?: getItemRarity(repItem.item_id)
                        val rarityColor = when (rarity.lowercase()) {
                            "cursed", "relic" -> EidosRed
                            "legendary" -> EidosOrange
                            "epic" -> EidosPurple
                            "rare" -> EidosCyan
                            "uncommon" -> EidosNeon
                            else -> Color(0xFF78909C)
                        }

                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF080F17).copy(alpha = 0.85f))
                                .border(1.dp, rarityColor.copy(alpha = 0.45f), RoundedCornerShape(6.dp))
                                .padding(8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(44.dp)
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(Color(0xFF03060A))
                                    .border(1.dp, rarityColor.copy(alpha = 0.5f), RoundedCornerShape(4.dp)),
                                contentAlignment = Alignment.Center
                            ) {
                                EidosImage(
                                    resName = repItem.item_id,
                                    borderColor = Color.Transparent,
                                    borderWidth = 0.dp,
                                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }
                            Spacer(Modifier.width(8.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Text(rarity.uppercase(), color = rarityColor, fontSize = 9.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                    Text("• В наличии: $totalCount шт.", color = if (totalCount >= 3) EidosNeon else Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                if (totalCount >= 3 && repItem.item_id !in io.eidos.zerolayer.data.ItemSlotUtils.NON_MERGEABLE) {
                                    Button(
                                        onClick = { onMerge(repItem) },
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.25f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                        shape = CutCornerShape(4.dp),
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Text("СИНТЕЗ (3->1 РАНГ+)", color = EidosNeon, fontSize = 8.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                                    }
                                }
                                Button(
                                    onClick = { onDismantle(repItem) },
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                    shape = CutCornerShape(4.dp),
                                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text("РАЗОБРАТЬ", color = EidosRed, fontSize = 8.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }
                }
            }
        } else {
            val shards = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0

            // Единый реестр рецептов (ForgeRecipes.kt) + фильтр по категории; крафтабельные поднимаются вверх
            var recipeFilter by remember { mutableStateOf<ForgeRecipeCategory?>(null) }
            val filteredRecipes = run {
                val base = if (recipeFilter == null) ForgeRecipeRegistry.ALL
                    else ForgeRecipeRegistry.ALL.filter { it.category == recipeFilter }
                base.sortedWith(
                    compareByDescending { recipe: ForgeRecipeDefinition ->
                        shards >= recipe.shardCost && (player?.biocoin ?: 0L) >= recipe.creditCost &&
                            recipe.additionalIngredients.all { (ingId, qty) ->
                                (inventory.find { it.item_id == ingId }?.quantity ?: 0) >= qty
                            }
                    }
                )
            }

            Column(modifier = Modifier.fillMaxSize()) {
                // HIGH-TECH WEAPON CRAFTING CHAMBER (References 1 & 5)
                ForgeCraftPulse(
                    isCrafting = craftingId == "__hologram__",
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    io.eidos.zerolayer.ui.components.zzz.ZzzForgeHologramChamber(
                        weaponTitle = "APEX STARBURST [AS-VII]",
                        weaponRarity = "LEGENDARY",
                        dataSlicerLvl = 5,
                        quantumTunerLvl = 3,
                        isVaalCorrupted = false,
                        quantumCoils = 18,
                        maxQuantumCoils = 20,
                        voidCells = 12,
                        maxVoidCells = 15,
                        vaalEssence = 3,
                        maxVaalEssence = 5,
                        onCommenceCraft = {
                            craftingId = "__hologram__"
                            filteredRecipes.firstOrNull()?.let { onCraft(it.targetId) }
                        },
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 4.dp)
                        .background(EidosGlass)
                        .padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("КРЕДИТНЫЙ БАЛАНС СКОПЛЕНИЯ: $shards", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                    Spacer(Modifier.width(4.dp))
                    ZzzIcon(R.drawable.ic_res_eidos_shard, size = 12.dp)
                    Spacer(Modifier.width(2.dp))
                    Text("Осколков", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }

                // Фильтры по категориям рецептов
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 4.dp)
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    ForgeRecipeFilterPill(label = "ВСЕ", selected = recipeFilter == null) { recipeFilter = null }
                    ForgeRecipeCategory.entries.forEach { cat ->
                        ForgeRecipeFilterPill(label = cat.label, selected = recipeFilter == cat) { recipeFilter = cat }
                    }
                }

                LazyColumn(
                    // weight(1f), а не fillMaxSize: иначе список занимает весь рост колонки
                    // и нижние карточки уходят за край экрана без возможности доскроллить
                    modifier = Modifier.fillMaxWidth().weight(1f),
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(filteredRecipes, key = { it.targetId }) { recipe ->
                        val recipeDisplayName = resolveForgeRecipeName(recipe, allItemsMetadata)
                        val hasEnoughShards = shards >= recipe.shardCost
                        val hasEnoughBc = (player?.biocoin ?: 0L) >= recipe.creditCost
                        val canAffordRecipe = hasEnoughShards && hasEnoughBc
                        var hasAllIngredients = hasEnoughShards
                        val ingStatusList = mutableListOf<String>()

                        recipe.additionalIngredients.forEach { (ingId, qty) ->
                            val currentIng = inventory.find { it.item_id == ingId }?.quantity ?: 0
                            val ingMeta = allItemsMetadata.find { it.id == ingId }
                            val ingName = ingMeta?.name ?: getItemName(ingId)
                            val ok = currentIng >= qty
                            if (!ok) hasAllIngredients = false
                            ingStatusList.add("$ingName: $currentIng/$qty")
                        }

                        ForgeCraftPulse(
                            isCrafting = craftingId == recipe.targetId,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(EidosGlass)
                                .border(1.dp, if (hasAllIngredients) EidosCyan.copy(alpha = 0.4f) else Color.White.copy(alpha = 0.08f), CutCornerShape(4.dp))
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(44.dp)
                                    .clip(CutCornerShape(4.dp))
                                    .background(Color(0xFF03060A))
                                    .border(1.dp, if (hasAllIngredients) EidosCyan.copy(alpha = 0.5f) else Color.White.copy(alpha = 0.12f), CutCornerShape(4.dp)),
                                contentAlignment = Alignment.Center
                            ) {
                                EidosImage(
                                    resName = recipe.targetId,
                                    borderColor = Color.Transparent,
                                    borderWidth = 0.dp,
                                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }
                            Spacer(Modifier.width(8.dp))
                            Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    // Индикатор доступности: зеленая точка - хватает осколков и BC, красная - нет
                                    Box(
                                        modifier = Modifier
                                            .size(8.dp)
                                            .clip(CircleShape)
                                            .background(if (canAffordRecipe) ZzzToxicGreen else ZzzDangerRed)
                                    )
                                    Spacer(Modifier.width(6.dp))
                                    Text(recipeDisplayName, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                }
                                if (recipe.description.isNotEmpty()) {
                                    Text(recipe.description, color = Color.Gray, fontSize = 9.sp)
                                }
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text("Требуется: ${recipe.shardCost} ", color = if (hasEnoughShards) EidosNeon else EidosRed, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
                                    ZzzIcon(R.drawable.ic_res_eidos_shard, size = 10.dp)
                                    Text(" + ${recipe.creditCost} BC", color = if (hasEnoughShards) EidosNeon else EidosRed, fontSize = 10.sp, fontWeight = FontWeight.SemiBold)
                                }
                                if (ingStatusList.isNotEmpty()) {
                                    Text(
                                        "Материалы: " + ingStatusList.joinToString(", "),
                                        color = if (hasAllIngredients) EidosCyan else ZzzGold,
                                        fontSize = 9.sp
                                    )
                                }
                            }
                            Button(
                                onClick = { pendingCraftRecipe = recipe },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (hasAllIngredients) EidosCyan.copy(alpha = 0.25f) else Color.DarkGray.copy(alpha = 0.3f)
                                ),
                                border = androidx.compose.foundation.BorderStroke(
                                    1.dp,
                                    if (hasAllIngredients) EidosCyan else Color.Gray.copy(alpha = 0.5f)
                                ),
                                shape = CutCornerShape(4.dp),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    "КОВКА",
                                    color = if (hasAllIngredients) EidosCyan else Color.LightGray,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                        }
                    }
                }
            }
        }
    }

    val activeRecipeToCraft = pendingCraftRecipe
    if (activeRecipeToCraft != null) {
        val recipe = activeRecipeToCraft
        AlertDialog(
            onDismissRequest = { pendingCraftRecipe = null },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_event_danger, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text("ПОДТВЕРЖДЕНИЕ СИНТЕЗА", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                }
            },
            text = {
                Text(
                    "Вы действительно хотите синтезировать «${resolveForgeRecipeName(recipe, allItemsMetadata)}» и списать требуемые компоненты со склада?",
                    color = Color.LightGray,
                    fontSize = 11.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        craftingId = recipe.targetId
                        onCraft(recipe.targetId)
                        pendingCraftRecipe = null
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("СИНТЕЗИРОВАТЬ", color = Color.Black, fontWeight = FontWeight.Black, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingCraftRecipe = null }) {
                    Text("ОТМЕНА", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF090E14),
            shape = CutCornerShape(8.dp)
        )
    }
}

@Composable
fun SocketModdingTab(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    onQuantumTuner: (InventoryItem) -> Unit,
    onSocketPuncher: (InventoryItem) -> Unit,
    onChromaticInjector: (InventoryItem) -> Unit,
    onInsertChip: (InventoryItem, Int, io.eidos.zerolayer.data.DataChip) -> Unit,
    onRemoveChip: (InventoryItem, Int) -> Unit,
    onTriggerSlicerReroll: (InventoryItem, io.eidos.zerolayer.data.CyberEquipment, io.eidos.zerolayer.data.CyberEquipment, Long, String) -> Unit
) {
    // Строго экипировка: расходники/материалы не подлежат слайсерам и сокетам
    val equipmentItems = inventory.filter { io.eidos.zerolayer.data.PoECraftEngine.socketLimitFor(it.item_id) > 0 }
    val shardsCount = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0

    // Пикер чипа: вставлять можно только чипы, что есть в инвентаре
    // (раньше в пустой сокет вставлялся случайный чип бесплатно - халява из воздуха)
    var chipPickerFor by remember { mutableStateOf<Pair<InventoryItem, Int>?>(null) }
    chipPickerFor?.let { (targetItem, socketIdx) ->
        val ownedChips = inventory.associate { it.item_id to it.quantity }
        AlertDialog(
            onDismissRequest = { chipPickerFor = null },
            title = {
                Text("ВСТАВИТЬ ЧИП", color = EidosCyan, fontSize = 13.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
            },
            text = {
                Column {
                    Text(
                        "Чипы добываются из врагов на глубине 2000м+ и из тайников. Резонанс: цвет чипа = цвет сокета (+25%).",
                        color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace
                    )
                    Spacer(Modifier.height(8.dp))
                    io.eidos.zerolayer.data.PoECraftEngine.AVAILABLE_DATA_CHIPS.forEach { chip ->
                        val owned = ownedChips[chip.id] ?: 0
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(CutCornerShape(4.dp))
                                .background(if (owned > 0) Color(0xFF0F1A24) else Color(0xFF0C0F15))
                                .border(1.dp, if (owned > 0) EidosCyan.copy(alpha = 0.5f) else Color.DarkGray, CutCornerShape(4.dp))
                                .clickable(enabled = owned > 0) {
                                    onInsertChip(targetItem, socketIdx, chip)
                                    chipPickerFor = null
                                }
                                .padding(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(chip.name, color = if (owned > 0) Color.White else Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                Text(
                                    "${chip.statBonusType} +${chip.statBonusValue} | ${chip.color.name}",
                                    color = Color(0xFF9FB3C8), fontSize = 9.sp, fontFamily = FontFamily.Monospace
                                )
                            }
                            Text(
                                if (owned > 0) "x$owned" else "НЕТ",
                                color = if (owned > 0) EidosNeon else ZzzDangerRed,
                                fontSize = 11.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace
                            )
                        }
                        Spacer(Modifier.height(6.dp))
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { chipPickerFor = null }) {
                    Text("ОТМЕНА", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF090E14),
            shape = CutCornerShape(8.dp)
        )
    }

    if (equipmentItems.isEmpty()) {
        ForgeEmptyWorkbench(hint = "НЕТ СНАРЯЖЕНИЯ ДЛЯ РЕКАЛИБРОВКИ")
    } else {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            items(equipmentItems, key = { it.id }) { item ->
                val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                val rarity = itemMeta?.rarity ?: getItemRarity(item.item_id)
                val name = itemMeta?.name ?: getItemName(item.item_id)
                val eq = io.eidos.zerolayer.data.PoECraftEngine.getOrGenerateEquipment(item, rarity)
                val totalStats = io.eidos.zerolayer.data.PoECraftEngine.calculateTotalStats(eq)

                // Track locked affixes locally for this specific card
                var lockedIndices by remember { mutableStateOf(setOf<Int>()) }
                val baseCost = 250L
                val (slicerBcCost, slicerShardCost) = io.eidos.zerolayer.data.ZeroLayerEconomy.calculateSlicerLockCost(baseCost, lockedIndices.size)

                Card(
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(
                            1.dp,
                            if (eq.isCorrupted) ZzzDangerRed else Color.White.copy(alpha = 0.2f),
                            CutCornerShape(4.dp)
                        )
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        // Title
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                if (eq.isCorrupted) {
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(R.drawable.ic_event_danger, size = 10.dp)
                                        Spacer(Modifier.width(3.dp))
                                        Text("СКВЕРНА", color = ZzzDangerRed, fontWeight = FontWeight.Bold, fontSize = 9.sp)
                                    }
                                }
                            }
                            Text(
                                rarity.uppercase(),
                                color = when (rarity) {
                                    "legendary" -> ZzzWarningOrange
                                    "relic" -> Color(0xFFFF3366)
                                    "epic" -> Color(0xFF9C27B0)
                                    "rare" -> EidosCyan
                                    else -> EidosNeon
                                },
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        if (eq.implicitAffix != null) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Surface(
                                color = ZzzDangerRed.copy(alpha = 0.12f),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzDangerRed),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    eq.implicitAffix,
                                    color = ZzzDangerRed,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    modifier = Modifier.padding(6.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        // Total active bonuses summary (including color synergy)
                        val nonZeroStats = totalStats.filter { it.value > 0 }
                        if (nonZeroStats.isNotEmpty()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_res_energy, size = 10.dp)
                                Spacer(Modifier.width(4.dp))
                                Text(
                                    "ИТОГОВЫЙ БОНУС: " + nonZeroStats.entries.joinToString(" | ") { "+${it.value} ${it.key}" },
                                    color = EidosNeon,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                        }

                        // Affixes with locks
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ZzzIcon(R.drawable.ic_action_scan, size = 10.dp)
                            Spacer(Modifier.width(4.dp))
                            Text("АФФИКСЫ (ФИКСАЦИЯ ПАРАМЕТРА):", color = EidosCyan, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        }
                        Spacer(modifier = Modifier.height(4.dp))

                        eq.affixes.forEachIndexed { index, affix ->
                            val rangeSpan = (affix.maxValue - affix.minValue).coerceAtLeast(1)
                            val currentOffset = (affix.currentValue - affix.minValue).coerceAtLeast(0)
                            val pct = (currentOffset.toFloat() / rangeSpan.toFloat()).coerceIn(0f, 1f)
                            val isPerfect = affix.currentValue == affix.maxValue
                            val isLocked = lockedIndices.contains(index)

                            Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            "${affix.statType}: +${affix.currentValue}",
                                            color = if (isLocked) EidosCyan else if (isPerfect) EidosNeon else Color.White,
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            "[Диапазон: ${affix.minValue} - ${affix.maxValue}]",
                                            color = Color.Gray,
                                            fontSize = 9.sp
                                        )
                                    }

                                    if (!eq.isCorrupted) {
                                        Row(
                                            verticalAlignment = Alignment.CenterVertically,
                                            modifier = Modifier.clickable {
                                                if (isLocked) {
                                                    lockedIndices = lockedIndices - index
                                                } else if (lockedIndices.size < 2) {
                                                    lockedIndices = lockedIndices + index
                                                }
                                            }
                                        ) {
                                            ZzzIcon(
                                                iconRes = if (isLocked) R.drawable.ic_ui_locked else R.drawable.ic_ui_unlocked,
                                                size = 10.dp,
                                                tint = if (isLocked) EidosCyan else Color.Gray
                                            )
                                            Spacer(Modifier.width(4.dp))
                                            Text(
                                                if (isLocked) "ЗАПИСАН" else "СВОБОДЕН",
                                                color = if (isLocked) EidosCyan else Color.Gray,
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Bold
                                            )
                                        }
                                    }
                                }
                                LinearProgressIndicator(
                                    progress = { pct },
                                    color = if (isLocked) EidosCyan else if (isPerfect) EidosNeon else EidosCyan,
                                    trackColor = Color.DarkGray,
                                    modifier = Modifier.fillMaxWidth().height(4.dp).padding(top = 2.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        // Sockets & Chips (+25% synergy display ZZZ Style)
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_action_skill, size = 12.dp)
                                Spacer(Modifier.width(4.dp))
                                Text("СОКЕТЫ И ЧИПЫ:", color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, fontFamily = FontFamily.Monospace)
                            }
                            io.eidos.zerolayer.ui.components.ZzzBadge(
                                text = "+25% РЕЗОНАНС АКТИВЕН!",
                                color = io.eidos.zerolayer.ui.theme.ZzzToxicGreen,
                                textColor = Color.Black
                            )
                        }
                        Spacer(modifier = Modifier.height(6.dp))

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            eq.socketColors.forEachIndexed { index, socketColor ->
                                val chip = if (index < eq.insertedChips.size) eq.insertedChips[index] else null
                                val colorVal = Color(socketColor.hexColor)
                                val matchedSynergy = chip != null && socketColor == chip.color

                                Surface(
                                    color = Color(0xFF10131D),
                                    shape = CutCornerShape(8.dp),
                                    border = androidx.compose.foundation.BorderStroke(
                                        width = if (matchedSynergy) 2.5.dp else 1.5.dp,
                                        color = if (matchedSynergy) io.eidos.zerolayer.ui.theme.ZzzToxicGreen else colorVal
                                    ),
                                    modifier = Modifier
                                        .weight(1f)
                                        .clickable {
                                            if (eq.isCorrupted) return@clickable
                                            if (chip != null) {
                                                onRemoveChip(item, index)
                                            } else {
                                                // Чипы - предметы из инвентаря: открываем пикер своих чипов
                                                chipPickerFor = item to index
                                            }
                                        }
                                ) {
                                    Column(
                                        modifier = Modifier.padding(8.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        // Glowing Socket Circle Icon
                                        Box(
                                            modifier = Modifier
                                                .size(38.dp)
                                                .background(colorVal.copy(alpha = 0.25f), CircleShape)
                                                .border(
                                                    width = 2.dp,
                                                    color = if (matchedSynergy) io.eidos.zerolayer.ui.theme.ZzzToxicGreen else colorVal,
                                                    shape = CircleShape
                                                ),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            if (chip != null) {
                                                val chipIconRes = when (chip.color) {
                                                    io.eidos.zerolayer.data.ChipSocketColor.RED_MONOLITH -> R.drawable.ic_chip_red
                                                    io.eidos.zerolayer.data.ChipSocketColor.GREEN_GHOST -> R.drawable.ic_chip_green
                                                    io.eidos.zerolayer.data.ChipSocketColor.BLUE_HACKER -> R.drawable.ic_chip_blue
                                                    else -> R.drawable.ic_chip_blue
                                                }
                                                Image(
                                                    painter = painterResource(id = chipIconRes),
                                                    contentDescription = chip.name,
                                                    modifier = Modifier.size(26.dp),
                                                    contentScale = ContentScale.Fit
                                                )
                                            } else {
                                                Text(
                                                    text = "⨁",
                                                    fontSize = 16.sp,
                                                    color = colorVal
                                                )
                                            }
                                        }

                                        Spacer(modifier = Modifier.height(4.dp))

                                        Text(
                                            if (chip != null) chip.name else "СОКЕТ #${index + 1}",
                                            color = if (matchedSynergy) io.eidos.zerolayer.ui.theme.ZzzToxicGreen else colorVal,
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.SansSerif,
                                            maxLines = 1
                                        )

                                        if (chip != null) {
                                            if (matchedSynergy) {
                                                Row(verticalAlignment = Alignment.CenterVertically) {
                                                    ZzzIcon(R.drawable.ic_res_energy, size = 8.dp)
                                                    Spacer(Modifier.width(2.dp))
                                                    Text("+25%", color = io.eidos.zerolayer.ui.theme.ZzzToxicGreen, fontSize = 8.sp, fontWeight = FontWeight.ExtraBold)
                                                }
                                            } else {
                                                Text("Нет синергии", color = Color.Gray, fontSize = 7.sp)
                                            }
                                            Text("[TAP] ИЗВЛЕЧЬ", color = Color.Gray.copy(alpha = 0.7f), fontSize = 6.5.sp, fontFamily = FontFamily.Monospace)
                                        }
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // Controls Industrial Panel Buttons
                        if (!eq.isCorrupted) {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    // Data Slicer Button ZZZ
                                    val slicerLabel = if (slicerShardCost > 0) "СЛАЙСЕР ($slicerBcCost BC + ${slicerShardCost} Осколков)" else "СЛАЙСЕР ($slicerBcCost BC)"
                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                        text = slicerLabel,
                                        onClick = {
                                            val nextProspective = io.eidos.zerolayer.data.PoECraftEngine.applyDataSlicerWithLocking(
                                                eq,
                                                lockedIndices,
                                                rarity
                                            )
                                            onTriggerSlicerReroll(
                                                item,
                                                eq,
                                                nextProspective,
                                                slicerBcCost,
                                                rarity
                                            )
                                        },
                                        enabled = shardsCount >= slicerShardCost,
                                        primaryColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                        borderColor = Color.White,
                                        textColor = Color.Black,
                                        modifier = Modifier.weight(1f),
                                        height = 44.dp
                                    )

                                    // Quantum Tuner ZZZ
                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                        text = "ТЮНЕР (500 BC + 1 Осколок)",
                                        onClick = { onQuantumTuner(item) },
                                        enabled = shardsCount >= 1,
                                        primaryColor = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                        borderColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                        textColor = Color.Black,
                                        modifier = Modifier.weight(1f),
                                        height = 44.dp
                                    )
                                }

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    // Socket Puncher
                                    Button(
                                        onClick = { onSocketPuncher(item) },
                                        enabled = shardsCount >= 1,
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = ZzzWarningOrange.copy(alpha = 0.2f),
                                            disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                        ),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if (shardsCount >= 1) ZzzWarningOrange else Color.DarkGray),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.weight(1f),
                                        contentPadding = PaddingValues(2.dp)
                                    ) {
                                        Text("ГНЕЗДА\n(300 BC + 1 Осколок)", color = if (shardsCount >= 1) ZzzWarningOrange else Color.Gray, fontSize = 9.sp, fontWeight = FontWeight.Bold, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                                    }

                                    // Chromatic Injector
                                    Button(
                                        onClick = { onChromaticInjector(item) },
                                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF9C27B0).copy(alpha = 0.2f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF9C27B0)),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.weight(1f),
                                        contentPadding = PaddingValues(2.dp)
                                    ) {
                                        Text("СПЕКТР\n(150 BC)", color = Color(0xFFE040FB), fontSize = 9.sp, fontWeight = FontWeight.Bold, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                                    }
                                }
                            }
                        } else {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_ui_locked, size = 12.dp, tint = ZzzDangerRed)
                                Spacer(Modifier.width(4.dp))
                                Text(
                                    "ПРЕДМЕТ ЗАПЕЧАТАН (СКВЕРНА) - калибровка и сокеты заблокированы!",
                                    color = ZzzDangerRed,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Bold
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
fun DataCorruptionTab(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    onVaalCorruption: (InventoryItem) -> Unit
) {
    // Строго экипировка: расходники/материалы не оскверняются
    val uncorruptedEquipment = inventory.filter {
        io.eidos.zerolayer.data.PoECraftEngine.socketLimitFor(it.item_id) > 0
    }
    val shardsCount = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0

    // Обязательное окно предупреждения перед Ваал-осквернением
    var pendingVaalItem by remember { mutableStateOf<InventoryItem?>(null) }
    pendingVaalItem?.let { target ->
        val targetMeta = allItemsMetadata.find { it.id == target.item_id }
        AlertDialog(
            onDismissRequest = { pendingVaalItem = null },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_event_danger, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text("☣️ ОСКВЕРНИТЬ НАВЕЧНО?", color = ZzzDangerRed, fontWeight = FontWeight.Black, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                }
            },
            text = {
                Text(
                    "«${targetMeta?.name ?: target.item_id.uppercase()}» будет либо УНИЧТОЖЕН безвозвратно, либо получит случайный сверх-модификатор.\n\n" +
                        "После ритуала предмет ЗАПЕЧАТАН: сокеты, чипы, заточка и перековка заблокированы навсегда.\n\n" +
                        "Стоимость: 1000 BC + 2 💎. Продолжить?",
                    color = Color.LightGray, fontSize = 11.sp, fontFamily = FontFamily.Monospace
                )
            },
            confirmButton = {
                Button(
                    onClick = {
                        onVaalCorruption(target)
                        pendingVaalItem = null
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ZzzDangerRed.copy(alpha = 0.3f)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, ZzzDangerRed),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("РИСКНУТЬ", color = ZzzDangerRed, fontWeight = FontWeight.Black, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingVaalItem = null }) {
                    Text("ОТМЕНА", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            containerColor = Color(0xFF0A0508),
            shape = CutCornerShape(8.dp)
        )
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1F0C0D)),
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
                .border(1.dp, ZzzDangerRed, CutCornerShape(6.dp))
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(R.drawable.ic_event_danger, size = 14.dp)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "ОПАСНОСТЬ: ИНЪЕКЦИЯ КОДА СКВЕРНЫ",
                        color = ZzzDangerRed,
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Внедрение хаотического вируса в нейроструктуру предмета дает шанс наложить колоссальный СВЕРХ-БОНУС (напр. +30% вампиризма или критического урона).\n\n" +
                    "ОДНАКО предмет будет ЗАПЕЧАТАН НАВЕЧНО! Его сокеты, чипы и аффиксы больше никогда нельзя будет изменить.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("ТРЕБУЕТСЯ: 1000 BC + 2 ", color = Color.Yellow, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    ZzzIcon(R.drawable.ic_res_eidos_shard, size = 10.dp)
                    Text(" Осколка Эйдоса", color = Color.Yellow, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        if (uncorruptedEquipment.isEmpty()) {
            ForgeEmptyWorkbench(hint = "НЕТ СНАРЯЖЕНИЯ ДЛЯ ПРОВЕДЕНИЯ СКВЕРНЫ")
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(uncorruptedEquipment, key = { it.id }) { item ->
                    val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                    val rarity = itemMeta?.rarity ?: getItemRarity(item.item_id)
                    val name = itemMeta?.name ?: getItemName(item.item_id)
                    val eq = io.eidos.zerolayer.data.PoECraftEngine.getOrGenerateEquipment(item, rarity)

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(EidosGlass)
                            .border(
                                1.dp,
                                if (eq.isCorrupted) ZzzDangerRed else Color.White.copy(alpha = 0.1f),
                                CutCornerShape(4.dp)
                            )
                            .padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                            Text(
                                "Класс: ${rarity.uppercase()} | ${if (eq.isCorrupted) "ЗАПЕЧАТАН" else "ДОСТУПЕН ДЛЯ СКВЕРНЫ"}",
                                color = if (eq.isCorrupted) ZzzDangerRed else Color.Gray,
                                fontSize = 10.sp
                            )
                        }

                        if (!eq.isCorrupted) {
                            Button(
                                onClick = { pendingVaalItem = item },
                                enabled = (player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = ZzzDangerRed.copy(alpha = 0.2f),
                                    disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                ),
                                border = androidx.compose.foundation.BorderStroke(
                                    width = 1.dp,
                                    color = if ((player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2) ZzzDangerRed else Color.DarkGray
                                ),
                                shape = CutCornerShape(4.dp),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_event_danger, size = 10.dp)
                                    Spacer(Modifier.width(3.dp))
                                    Text("ИСКАЗИТЬ", color = if ((player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2) ZzzDangerRed else Color.Gray, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        } else {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(R.drawable.ic_ui_locked, size = 10.dp, tint = ZzzDangerRed)
                                Spacer(Modifier.width(3.dp))
                                Text("ЗАПЕЧАТАН", color = ZzzDangerRed, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * Pure visual wrapper for craft feedback: pulses content (scale 1.0 -> 1.06 -> 1.0, ~400ms total)
 * and overlays forge sparks while [isCrafting] is true. Does not touch any craft logic.
 */
@Composable
fun ForgeCraftPulse(
    isCrafting: Boolean,
    modifier: Modifier = Modifier,
    content: @Composable androidx.compose.foundation.layout.BoxScope.() -> Unit
) {
    val scale = remember { Animatable(1f) }
    LaunchedEffect(isCrafting) {
        if (isCrafting) {
            scale.animateTo(1.06f, tween(200))
            scale.animateTo(1f, tween(200))
        } else {
            scale.snapTo(1f)
        }
    }
    Box(
        modifier = modifier.graphicsLayer {
            scaleX = scale.value
            scaleY = scale.value
        }
    ) {
        content()
        if (isCrafting) {
            CyberParticleOverlay(
                preset = ParticlePreset.FORGE_SPARKS,
                modifier = Modifier.matchParentSize()
            )
        }
    }
}

/**
 * Empty forge state panel: "ВЕРСТАК ЖДЁТ" header with the original hint line preserved below.
 */
@Composable
fun ForgeEmptyWorkbench(hint: String) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        CyberCornerBracketBox(
            bracketSize = 14.dp,
            bracketColor = ZzzWarningOrange.copy(alpha = 0.7f),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFF0D0A06).copy(alpha = 0.8f))
                    .border(1.dp, ZzzWarningOrange.copy(alpha = 0.4f), CutCornerShape(8.dp))
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                ZzzIcon(R.drawable.ic_menu_forge, size = 32.dp, tint = ZzzWarningOrange.copy(alpha = 0.85f))
                Text(
                    "ВЕРСТАК ЖДЁТ // ВЫБЕРИ ПРЕДМЕТ ДЛЯ МОДИФИКАЦИИ",
                    color = ZzzWarningOrange,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )
                Text(
                    hint,
                    color = Color.Gray,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

fun getItemRarity(id: String): String {
    return when(id) {
        "rusty_knife", "crowbar", "nomad_goggles", "scavenger_mask", "hoodie", "leather_jacket", "medkit", "energy_cell", "battery", "ram_chip" -> "common"
        "data_bat", "shock_baton", "tactical_helmet", "vampire_visor", "kevlar_vest", "tactical_suit", "master_key", "neural_stimulator", "glitch_filter", "cpu_booster" -> "uncommon"
        "cyber_katana", "laser_pistol", "cyber_halo", "overclock_crown", "exo_skeleton", "nano_suit", "abyssal_key", "eidos_shard" -> "rare"
        "plasma_rifle", "nano_blade", "void_walker_hood", "phantom_cloak", "force_field", "aegis", "ai_core", "overclocker", "backup_drive", "neural_link" -> "epic"
        "void_cannon", "singularity_sword", "architect_mask", "reality_armor", "quantum_shield", "admin_key", "chronometer", "logic_gate", "god_mode_chip" -> "legendary"
        "relic_vampire", "relic_speed", "corrupted_data_cluster" -> "relic"
        else -> "common"
    }
}

fun getItemName(id: String): String {
    return when(id) {
        "rusty_knife" -> "Ржавый Тесак"
        "crowbar" -> "Монтировка Хакера"
        "data_bat" -> "Бита-носитель"
        "shock_baton" -> "Шоковая Дубинка"
        "cyber_katana" -> "Кибер-Катана"
        "laser_pistol" -> "Лазерный Излучатель"
        "plasma_rifle" -> "Плазменный Рельсотрон"
        "nano_blade" -> "Нано-Клинок"
        "void_cannon" -> "Пушка Пустоты"
        "singularity_sword" -> "Меч Сингулярности"
        "nomad_goggles" -> "Окуляры Кочевника"
        "scavenger_mask" -> "Респиратор Сталкера"
        "tactical_helmet" -> "Шлем Тактического Отклика"
        "vampire_visor" -> "Нейро-Визор «Пиявка»"
        "cyber_halo" -> "Голографический Нимб"
        "overclock_crown" -> "Венец Разгона"
        "void_walker_hood" -> "Капюшон Пустоты"
        "architect_mask" -> "Лицо Архитектора"
        "relic_vampire" -> "Корона Истинной Крови"
        "relic_speed" -> "Шлем Бога Скорости"
        "hoodie" -> "Балахон Сквиттера"
        "leather_jacket" -> "Куртка Синдиката"
        "kevlar_vest" -> "Бронежилет Охраны"
        "tactical_suit" -> "Тактический Комбинезон"
        "exo_skeleton" -> "Экзоскелет"
        "nano_suit" -> "Нано-Костюм"
        "phantom_cloak" -> "Плащ Фантома"
        "force_field" -> "Генератор Поля"
        "reality_armor" -> "Доспехи Реальности"
        "quantum_shield" -> "Квантовый Барьер"
        "medkit" -> "Нано-Аптечка"
        "energy_cell" -> "Энерго-Ячейка"
        "battery" -> "Энерго-Ячейка"
        "master_key" -> "Магнитная Отмычка"
        "abyssal_key" -> "Ключ от Бездны"
        "neural_stimulator" -> "Нейро-Стимулятор"
        "aegis" -> "Эгида Бессмертия"
        "admin_key" -> "Ключ Архитектора"
        "eidos_shard" -> "Осколок Эйдоса"
        "wasteland_compass" -> "Компас Пустоши"
        "compass" -> "Компас Пустоши"
        "emp_charge" -> "EMP-Заряд"
        "emp_grenade" -> "EMP-Заряд"
        "crypto_fog" -> "Крипто-Туман"
        "stealth_spray" -> "Крипто-Туман"
        "memory_eraser" -> "Стиратель Памяти"
        "memory_wiper" -> "Стиратель Памяти"
        "data_spike" -> "Дата-Шип"
        "tactical_scanner" -> "Тактический Сканер"
        "scanner" -> "Тактический Сканер"
        "cryo_capsule" -> "Крио-Капсула"
        "sync_booster" -> "Ускоритель Синхронизации"
        "sync_accelerator" -> "Ускоритель Синхронизации"
        "purge_sync" -> "Синхрон Очищения"
        "cleanse_sync" -> "Синхрон Очищения"
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
        "credit_slicer" -> "Кредитный Резак"
        "banhammer_shard" -> "Осколок Бан-Хаммера"
        "grandfather_paradox" -> "Парадокс Деда"
        "empath_whip" -> "Хлыст Эмпата"
        "cache_wiper" -> "Стиратель Кэша"
        "error_404_mirror" -> "Зеркало Ошибок 404"
        "judas_shell" -> "Панцирь Иуды"
        "holo_poverty" -> "Голографическая Нищета"
        "schrodinger_armor" -> "Броня Шрёдингера"
        "thermonuclear_shroud" -> "Термоядерный Саван"
        "blood_miner" -> "Майнер на Крови"
        "karma_inversion" -> "Инверсия Кармы"
        "oblivion_chip" -> "Чип Забвения"
        "imposter_syndrome" -> "Синдром Самозванца"
        "kamikaze_protocol" -> "Протокол Камикадзе"
        "architect_eye" -> "Око Архитектора"
        "corrupted_data_cluster" -> "Искаженный Кластер (Глитч-Кэш)"
        else -> id.uppercase().replace("_", " ")
    }
}

/** Фильтр-пилюля категорий рецептов КОВКИ. */
@Composable
fun ForgeRecipeFilterPill(label: String, selected: Boolean, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) EidosCyan.copy(alpha = 0.2f) else Color.Transparent
        ),
        border = androidx.compose.foundation.BorderStroke(1.dp, if (selected) EidosCyan else Color.DarkGray),
        shape = CutCornerShape(4.dp),
        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp)
    ) {
        Text(label, color = if (selected) EidosCyan else Color.Gray, fontSize = 9.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
    }
}

/** Отображаемое имя рецепта: из реестра, иначе из items.json, иначе верхний регистр id. */
fun resolveForgeRecipeName(
    recipe: ForgeRecipeDefinition,
    metadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata>
): String = recipe.name.ifBlank {
    metadata.find { it.id == recipe.targetId }?.name ?: getItemName(recipe.targetId)
}

