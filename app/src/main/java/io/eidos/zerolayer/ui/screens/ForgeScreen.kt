package io.eidos.zerolayer.ui.screens

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
import io.eidos.zerolayer.data.InventoryItem
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.ui.platform.LocalContext
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.CircleShape
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.CyberParticleOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.ParticlePreset

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ForgeScreen(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
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

    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("🧪 СИНТЕЗ", "⚙️ МОДДИНГ СОКЕТОВ", "☣️ КОРРУПЦИЯ")

    // State for interactive recalibration
    var showComparisonDialog by remember { mutableStateOf(false) }
    var currentModItem by remember { mutableStateOf<InventoryItem?>(null) }
    var originalEquipment by remember { mutableStateOf<io.eidos.zerolayer.data.CyberEquipment?>(null) }
    var prospectiveEquipment by remember { mutableStateOf<io.eidos.zerolayer.data.CyberEquipment?>(null) }
    var prospectiveRarity by remember { mutableStateOf("common") }
    var prospectiveCost by remember { mutableStateOf(250L) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("КВАНТОВАЯ КУЗНИЦА EIDOS", color = Color(0xFFFF9800), fontWeight = FontWeight.Black, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                        Text(
                            "Ур. ${player?.level ?: 1} Оператор | 🪙 ${player?.biocoin ?: 0} BC | 💎 ${inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0} Осколков",
                            color = Color.LightGray,
                            fontSize = 8.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color(0xFFFF9800))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0C0904))
            )
        },
        bottomBar = {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .height(52.dp)
                    .border(1.dp, Color(0xFF3A2A1E), CutCornerShape(topStart = 8.dp, topEnd = 8.dp)),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF0D0A06)),
                shape = CutCornerShape(topStart = 8.dp, topEnd = 8.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxSize(),
                    horizontalArrangement = Arrangement.SpaceAround,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("⚒️ КУЗНИЦА", color = Color(0xFFFF9800), fontWeight = FontWeight.Bold, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                    Text("🎒 ИНВЕНТАРЬ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable { onBack() })
                    Text("⚙️ СИГНАЛ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace, modifier = Modifier.clickable { onBack() })
                }
            }
        },
        containerColor = Color(0xFF060402)
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            // Background and VFX
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_forge),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = Alignment.Center
            )
            CyberGridOverlay(modifier = Modifier.fillMaxSize())
            CyberParticleOverlay(preset = ParticlePreset.FORGE_SPARKS)

            Column(modifier = Modifier.fillMaxSize()) {
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
                        0 -> "🧪 СИНТЕЗ: Слияние дубликатов 2-в-1 до высших рангов или крафт снаряжения из осколков Эйдоса."
                        1 -> "⚙️ МОДДИНГ СОКЕТОВ: Настройка гнезд под чипы. Роллируйте статы с фиксацией 🔒 (макс. 2 заморозки, +50% BC за замок)."
                        else -> "☣️ КОРРУПЦИЯ: Заражение предметов хаотическим глитч-кодом. Дает мощнейший скрытый бонус, но полностью блокирует модификацию."
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
                Text(
                    "🎲 [ПЕРЕКАЛИБРОВКА: СРАВНЕНИЕ СТАТОВ]",
                    color = EidosCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace
                )
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
                            "🎲 [СЛАЙСЕР]: Перекалибровка аффиксов в $itemName успешно завершена! Списано $prospectiveCost BC."
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
}

@Composable
fun SynthesisTab(
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    onDismantle: (InventoryItem) -> Unit,
    onMerge: (InventoryItem) -> Unit,
    onCraft: (String) -> Unit
) {
    var subTab by remember { mutableIntStateOf(0) } // 0: РАЗБОР И СЛИЯНИЕ, 1: КОВКА РЕЦЕПТОВ

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
            val dismantleable = inventory.filter { it.item_id != "eidos_shard" }
            if (dismantleable.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("НЕТ ПРЕДМЕТОВ ДЛЯ УТИЛИЗАЦИИ", color = Color.Gray, fontSize = 12.sp)
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(dismantleable, key = { it.id }) { item ->
                        val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                        val name = itemMeta?.name ?: getItemName(item.item_id)
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(EidosGlass)
                                .border(1.dp, Color.White.copy(alpha = 0.1f))
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                Text("В наличии: ${item.quantity} шт.", color = Color.Gray, fontSize = 10.sp)
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (item.quantity >= 3) {
                                    Button(
                                        onClick = { onMerge(item) },
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.2f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                        shape = CutCornerShape(4.dp),
                                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Text("СИНТЕЗ (3)", color = EidosNeon, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                                Button(
                                    onClick = { onDismantle(item) },
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                    shape = CutCornerShape(4.dp),
                                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text("РАЗОБРАТЬ", color = EidosRed, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }
        } else {
            val shards = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0
            val recipes = listOf(
                Recipe("reality_silencer", 10, 2500L, "Глушитель Реальности", mapOf("boss_core" to 1), "Подавляет искажения пространства"),
                Recipe("death_mask", 6, 1500L, "Маска Мертвеца", mapOf("data_spike" to 1), "Смертоносный артефакт Бездны"),
                Recipe("scavenger_mask", 4, 800L, "Маска Мусорщика", mapOf("master_key" to 2), "Повышает шанс ценного лута"),
                Recipe("nomad_goggles", 5, 1000L, "Очки Кочевника", mapOf("compass" to 1), "Облегчает навигацию по секторам"),
                Recipe("karma_inversion", 8, 2000L, "Инверсия Кармы", mapOf("abyssal_key" to 1), "Преобразует урон в щиты"),
                Recipe("holo_poverty", 6, 1200L, "Голографическая Нищета", emptyMap(), "Маскировка от агрессивных программ"),
                Recipe("aegis", 5, 1000L, "Эгида Бессмертия", mapOf("battery" to 1), "Спасает от смертельного удара"),
                Recipe("medkit_small", 15, 100L, "Малая Аптечка", emptyMap(), "Восстанавливает HP"),
                Recipe("battery", 15, 100L, "Энерго-Батарея", emptyMap(), "Заряжает энергоячейки"),
                Recipe("master_key", 20, 200L, "Магнитная Отмычка", emptyMap(), "Взламывает защищенные контейнеры"),
                Recipe("data_spike", 25, 300L, "Дата-Шип", emptyMap(), "Пробивает терминалы"),
                Recipe("compass", 25, 300L, "Компас Пустоши", emptyMap(), "Указывает путь к аномалиям"),
                Recipe("rusty_knife", 30, 250L, "Ржавый Тесак", emptyMap(), "Базовое оружие ближнего боя"),
                Recipe("crowbar", 50, 500L, "Монтировка Хакера", emptyMap(), "Оружие и инструмент"),
                Recipe("hoodie", 40, 400L, "Балахон Сквиттера", emptyMap(), "Легкая защита")
            )

            Column(modifier = Modifier.fillMaxSize()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(EidosGlass)
                        .padding(12.dp)
                ) {
                    Text("КРЕДИТНЫЙ БАЛАНС СКОПЛЕНИЯ: $shards 💎 Осколков", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                }

                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(recipes, key = { it.id }) { recipe ->
                        val hasEnoughShards = shards >= recipe.shardCost
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

                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(EidosGlass)
                                .border(1.dp, if (hasAllIngredients) EidosCyan.copy(alpha = 0.4f) else Color.White.copy(alpha = 0.08f), CutCornerShape(4.dp))
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                                Text(recipe.name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                if (recipe.description.isNotEmpty()) {
                                    Text(recipe.description, color = Color.Gray, fontSize = 9.sp)
                                }
                                Text(
                                    "Требуется: ${recipe.shardCost} 💎 + ${recipe.creditCost} BC",
                                    color = if (hasEnoughShards) EidosNeon else EidosRed,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                                if (ingStatusList.isNotEmpty()) {
                                    Text(
                                        "Материалы: " + ingStatusList.joinToString(", "),
                                        color = if (hasAllIngredients) EidosCyan else Color(0xFFFFB300),
                                        fontSize = 9.sp
                                    )
                                }
                            }
                            Button(
                                onClick = { onCraft(recipe.id) },
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
    val equipmentItems = inventory.filter { it.item_id !in listOf("medkit", "energy_cell", "eidos_shard", "battery", "master_key", "corrupted_data_cluster") }
    val shardsCount = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0

    if (equipmentItems.isEmpty()) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("НЕТ СНАРЯЖЕНИЯ ДЛЯ РЕКАЛИБРОВКИ", color = Color.Gray, fontSize = 12.sp)
        }
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
                val lockedSurcharge = (baseCost * (1.0 + lockedIndices.size * 0.5)).toLong()

                Card(
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(
                            1.dp,
                            if (eq.isCorrupted) Color(0xFFFF1744) else Color.White.copy(alpha = 0.2f),
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
                                    Text("☣️ СКВЕРНА", color = Color(0xFFFF1744), fontWeight = FontWeight.Bold, fontSize = 9.sp)
                                }
                            }
                            Text(
                                rarity.uppercase(),
                                color = when (rarity) {
                                    "legendary" -> Color(0xFFFF9800)
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
                                color = Color(0xFFFF1744).copy(alpha = 0.12f),
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFF1744)),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    eq.implicitAffix,
                                    color = Color(0xFFFF5252),
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
                            Text(
                                "⚡ ИТОГОВЫЙ БОНУС: " + nonZeroStats.entries.joinToString(" | ") { "+${it.value} ${it.key}" },
                                color = EidosNeon,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(6.dp))
                        }

                        // Affixes with locks
                        Text("📊 АФФИКСЫ (ЗАМОК ПАРАМЕТРА 🔒):", color = EidosCyan, fontSize = 9.sp, fontWeight = FontWeight.Bold)
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
                                            "${affix.statType}: +${affix.currentValue} ${if (isPerfect) "✨" else ""}",
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
                                            Text(
                                                if (isLocked) "🔒 ЗАПИСАН" else "🔓 СВОБОДЕН",
                                                color = if (isLocked) EidosCyan else Color.Gray,
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Bold
                                            )
                                        }
                                    }
                                }
                                LinearProgressIndicator(
                                    progress = pct,
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
                            Text("🔌 СОКЕТЫ И ЧИПЫ:", color = io.eidos.zerolayer.ui.theme.ZzzElectricCyan, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, fontFamily = FontFamily.Monospace)
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
                                                val nextChip = io.eidos.zerolayer.data.PoECraftEngine.AVAILABLE_DATA_CHIPS.random()
                                                onInsertChip(item, index, nextChip)
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
                                                Text("⚡ +25%", color = io.eidos.zerolayer.ui.theme.ZzzToxicGreen, fontSize = 8.sp, fontWeight = FontWeight.ExtraBold)
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
                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                        text = "🎲 СЛАЙСЕР ($lockedSurcharge BC)",
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
                                                lockedSurcharge,
                                                rarity
                                            )
                                        },
                                        primaryColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                        borderColor = Color.White,
                                        textColor = Color.Black,
                                        modifier = Modifier.weight(1f),
                                        height = 44.dp
                                    )

                                    // Quantum Tuner ZZZ
                                    io.eidos.zerolayer.ui.components.ZzzMainButton(
                                        text = "⚖️ ТЮНЕР (500 BC+1💎)",
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
                                            containerColor = Color(0xFFFF9800).copy(alpha = 0.2f),
                                            disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                        ),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if (shardsCount >= 1) Color(0xFFFF9800) else Color.DarkGray),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.weight(1f),
                                        contentPadding = PaddingValues(2.dp)
                                    ) {
                                        Text("🔌 Гнезда\n(300 BC+1💎)", color = if (shardsCount >= 1) Color(0xFFFF9800) else Color.Gray, fontSize = 9.sp, fontWeight = FontWeight.Bold)
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
                                        Text("🌈 Спектр\n(150 BC)", color = Color(0xFFE040FB), fontSize = 9.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        } else {
                            Text(
                                "🔒 ПРЕДМЕТ ЗАПЕЧАТАН (СКВЕРНА) - калибровка и сокеты заблокированы!",
                                color = Color(0xFFFF5252),
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

@Composable
fun DataCorruptionTab(
    player: io.eidos.zerolayer.data.Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    onVaalCorruption: (InventoryItem) -> Unit
) {
    val uncorruptedEquipment = inventory.filter {
        it.item_id !in listOf("medkit", "energy_cell", "eidos_shard", "battery", "master_key", "corrupted_data_cluster")
    }
    val shardsCount = inventory.find { it.item_id == "eidos_shard" }?.quantity ?: 0

    Column(modifier = Modifier.fillMaxSize()) {
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1F0C0D)),
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
                .border(1.dp, Color(0xFFFF1744), CutCornerShape(6.dp))
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "⚠️ ОПАСНОСТЬ: ИНЪЕКЦИЯ КОДА СКВЕРНЫ",
                    color = Color(0xFFFF1744),
                    fontWeight = FontWeight.Bold,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Внедрение хаотического вируса в нейроструктуру предмета дает шанс наложить колоссальный СВЕРХ-БОНУС (напр. +30% вампиризма или критического урона).\n\n" +
                    "ОДНАКО предмет будет ЗАПЕЧАТАН НАВЕЧНО! Его сокеты, чипы и аффиксы больше никогда нельзя будет изменить.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "ТРЕБУЕТСЯ: 1000 BC + 2 💎 Осколка Эйдоса",
                    color = Color.Yellow,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        if (uncorruptedEquipment.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("НЕТ СНАРЯЖЕНИЯ ДЛЯ ПРОВЕДЕНИЯ СКВЕРНЫ", color = Color.Gray, fontSize = 12.sp)
            }
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
                                if (eq.isCorrupted) Color(0xFFFF1744) else Color.White.copy(alpha = 0.1f),
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
                                color = if (eq.isCorrupted) Color(0xFFFF1744) else Color.Gray,
                                fontSize = 10.sp
                            )
                        }

                        if (!eq.isCorrupted) {
                            Button(
                                onClick = { onVaalCorruption(item) },
                                enabled = (player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = Color(0xFFFF1744).copy(alpha = 0.2f),
                                    disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                ),
                                border = androidx.compose.foundation.BorderStroke(
                                    width = 1.dp,
                                    color = if ((player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2) Color(0xFFFF1744) else Color.DarkGray
                                ),
                                shape = CutCornerShape(4.dp),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                            ) {
                                Text("☣️ ИСКАЗИТЬ", color = if ((player?.biocoin ?: 0L) >= 1000L && shardsCount >= 2) Color(0xFFFF1744) else Color.Gray, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                            }
                        } else {
                            Text("🔒 ЗАПЕЧАТАН", color = Color(0xFFFF1744), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
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

data class Recipe(
    val id: String,
    val shardCost: Int,
    val creditCost: Long,
    val name: String,
    val additionalIngredients: Map<String, Int> = emptyMap(),
    val description: String = ""
)

