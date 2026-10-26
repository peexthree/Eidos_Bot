package com.example.eidos.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.R
import com.example.eidos.data.Player
import com.example.eidos.data.GameRepository.ItemMetadata
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.utils.neonGlowPulse
import com.example.eidos.ui.components.CyberGridOverlay
import com.example.eidos.ui.components.EidosImage
import com.example.eidos.ui.components.cyberClickable

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShopScreen(
    player: Player?,
    items: List<ItemMetadata>,
    selectedCategory: String = "all",
    onCategoryChange: (String) -> Unit = {},
    searchQuery: String = "",
    onSearchQueryChange: (String) -> Unit = {},
    onBuy: (String) -> Unit,
    onRollGacha: () -> Unit = {},
    onSynthesizeFragments: () -> Unit = {},
    dataFragmentsCount: Int = 0,
    onBack: () -> Unit
) {
    val amberColor = Color(0xFFFFB300)
    var sortBy by remember { mutableStateOf("price_asc") } // "price_asc", "price_desc", "name"
    var selectedInspectItem by remember { mutableStateOf<ItemMetadata?>(null) }
    var buyQuantity by remember { mutableStateOf(1) }

    val categories = listOf(
        "all" to "ВСЕ ТОВАРЫ",
        "gacha" to "🎁 ЛУТБОКСЫ",
        "weapon" to "🗡️ ОРУЖИЕ",
        "armor" to "🛡️ БРОНЯ",
        "head" to "🪖 ШЛЕМЫ",
        "chip" to "💾 ЧИПЫ",
        "consumable" to "🧪 РАСХОДНИКИ",
        "material" to "📦 РЕСУРСЫ"
    )

    val shopSpecialIds = setOf("scavenger_mask", "nomad_goggles", "aegis")
    val filteredItems = items
        .distinctBy { it.id }
        .filter { selectedCategory == "all" || it.type == selectedCategory }
        .filter {
            val rarityLower = it.rarity.lowercase()
            val isShopSpecial = shopSpecialIds.contains(it.id)
            (isShopSpecial || rarityLower in listOf("common", "uncommon", "rare")) &&
            (isShopSpecial || (!it.name.contains("💀") && !it.name.contains("👁") && !it.name.contains("🔴") && !it.name.contains("🟠")))
        }
        .filter { it.name.contains(searchQuery, ignoreCase = true) || it.description.contains(searchQuery, ignoreCase = true) }
        .sortedWith { a, b ->
            when (sortBy) {
                "price_asc" -> a.price.compareTo(b.price)
                "price_desc" -> b.price.compareTo(a.price)
                else -> a.name.compareTo(b.name)
            }
        }

    BackHandler(enabled = selectedInspectItem != null) {
        selectedInspectItem = null
        buyQuantity = 1
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "ЧЕРНЫЙ РЫНОК // ТОРГОВЫЙ ТЕРМИНАЛ",
                            color = amberColor,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            "ПРЯМАЯ ПОСТАВКА ИЗ СЕКТОРОВ Z-LAYER",
                            color = Color.Gray,
                            fontSize = 9.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = amberColor)
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
            CyberGridOverlay(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier.fillMaxSize()
            ) {
            // Balance Panel
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(EidosGlass)
                    .border(1.dp, amberColor.copy(alpha = 0.3f))
                    .padding(horizontal = 16.dp, vertical = 10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(
                            painter = painterResource(id = R.drawable.ic_biocoin),
                            contentDescription = "BioCoins",
                            modifier = Modifier.size(20.dp),
                            contentScale = ContentScale.Fit
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("БАЛАНС ТЕРМИНАЛА:", color = Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }
                    Text("${player?.biocoin ?: 0} BC", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 18.sp, fontFamily = FontFamily.Monospace)
                }
            }

            // EVA-09 Assistant Explanation Banner
            com.example.eidos.ui.components.ZzzHazardBanner(
                title = "📡 ГОЛОС EIDOS // ТОРГОВЫЙ ШЛЮЗ",
                message = "Корпоративные Архивы открыты! Трать накопленные байты BioCoins на мощное оружие, защитные бронеплиты и восстанавливающие нано-аптечки для повышения Атаки и Защиты в рейдах.",
                borderColor = amberColor,
                icon = "📦",
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
            )

            // Category Tabs
            ScrollableTabRow(
                selectedTabIndex = categories.indexOfFirst { it.first == selectedCategory }.coerceAtLeast(0),
                containerColor = Color.Black,
                contentColor = amberColor,
                edgePadding = 8.dp
            ) {
                categories.forEach { (catId, catName) ->
                    Tab(
                        selected = selectedCategory == catId,
                        onClick = { onCategoryChange(catId) },
                        text = { Text(catName, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace) },
                        selectedContentColor = amberColor,
                        unselectedContentColor = Color.Gray
                    )
                }
            }

            // Search and Sort Control Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { onSearchQueryChange(it) },
                    placeholder = { Text("Поиск по каталогу...", color = Color.Gray, fontSize = 11.sp) },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = amberColor,
                        unfocusedBorderColor = Color.DarkGray,
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White
                    )
                )

                IconButton(
                    onClick = {
                        sortBy = when (sortBy) {
                            "price_asc" -> "price_desc"
                            "price_desc" -> "name"
                            else -> "price_asc"
                        }
                    },
                    modifier = Modifier
                        .border(1.dp, amberColor.copy(alpha = 0.5f), CutCornerShape(4.dp))
                        .background(EidosGlass)
                ) {
                    Icon(
                        imageVector = when (sortBy) {
                            "price_asc" -> Icons.Default.KeyboardArrowUp
                            "price_desc" -> Icons.Default.KeyboardArrowDown
                            else -> Icons.Default.Menu
                        },
                        contentDescription = "Sort",
                        tint = amberColor
                    )
                }
            }

            // Items Catalog
            if (selectedCategory == "gacha") {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    item {
                        // ZZZ 3D Neon Lootbox Card
                        com.example.eidos.ui.components.ZzzWindowCard(
                            title = "ЧЕРНЫЙ РЫНОК (GACHA)",
                            subTitle = "VOID CACHE 1000 BC",
                            headerBadge = "GACHA CUBE",
                            borderColor = com.example.eidos.ui.theme.ZzzElectricCyan,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                // 3D-styled Neon Lootbox Cube Box
                                Box(
                                    modifier = Modifier
                                        .size(130.dp)
                                        .padding(4.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    val infiniteTransition = rememberInfiniteTransition(label = "cube_glow")
                                    val cubeScale by infiniteTransition.animateFloat(
                                        initialValue = 0.95f,
                                        targetValue = 1.05f,
                                        animationSpec = infiniteRepeatable(
                                            animation = tween(1400, easing = FastOutSlowInEasing),
                                            repeatMode = RepeatMode.Reverse
                                        ),
                                        label = "cubeScale"
                                    )

                                    Image(
                                        painter = painterResource(id = R.drawable.gacha_cube_lootbox),
                                        contentDescription = "Void Gacha Cube",
                                        modifier = Modifier
                                            .size(120.dp)
                                            .graphicsLayer {
                                                scaleX = cubeScale
                                                scaleY = cubeScale
                                            },
                                        contentScale = ContentScale.Fit
                                    )
                                }

                                Spacer(modifier = Modifier.height(6.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("[🎁] ЛУТБОКС", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, fontFamily = FontFamily.SansSerif)
                                    Text(
                                        "GACHA ROLL CHANCES:\n1% CURSED | 4% LEGENDARY",
                                        color = com.example.eidos.ui.theme.ZzzAcidYellow,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                com.example.eidos.ui.components.ZzzMainButton(
                                    text = "ОТКРЫТЬ (1000 BC) ➔",
                                    onClick = onRollGacha,
                                    primaryColor = com.example.eidos.ui.theme.ZzzElectricCyan,
                                    borderColor = com.example.eidos.ui.theme.ZzzAcidYellow,
                                    textColor = Color.Black,
                                    height = 48.dp,
                                    modifier = Modifier.fillMaxWidth()
                                )
                            }
                        }
                    }

                    item {
                        // Synthesis Card
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(1.dp, amberColor.copy(alpha = 0.5f), CutCornerShape(8.dp)),
                            colors = CardDefaults.cardColors(containerColor = Color.Black),
                            shape = CutCornerShape(8.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Text("⚡ СИНТЕЗАТОР ДАННЫХ (DATA SYNTHESIS)", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                Text("Объедините 5 Фрагментов Данных в гарантированный ЛЕГЕНДАРНЫЙ предмет!", color = Color.Gray, fontSize = 10.sp)
                                Spacer(modifier = Modifier.height(10.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("ВАШИ ФРАГМЕНТЫ:", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                    Text("$dataFragmentsCount / 5", color = if (dataFragmentsCount >= 5) EidosNeon else Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                }

                                Spacer(modifier = Modifier.height(12.dp))

                                Button(
                                    onClick = onSynthesizeFragments,
                                    enabled = dataFragmentsCount >= 5,
                                    modifier = Modifier.fillMaxWidth().height(46.dp),
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = amberColor.copy(alpha = 0.25f),
                                        disabledContainerColor = Color.DarkGray.copy(alpha = 0.2f)
                                    ),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, if (dataFragmentsCount >= 5) amberColor else Color.DarkGray),
                                    shape = CutCornerShape(4.dp)
                                ) {
                                    Text("СИНТЕЗИРОВАТЬ ЛЕГЕНДУ", color = if (dataFragmentsCount >= 5) amberColor else Color.Gray, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(filteredItems, key = { it.id }) { item ->
                    val rarityColor = when (item.rarity.lowercase()) {
                        "uncommon" -> Color(0xFF1E88E5)
                        "rare" -> Color(0xFFFFD54F)
                        "epic" -> Color(0xFFAB47BC)
                        "legendary" -> Color(0xFFFF7043)
                        "relic" -> Color(0xFFFF1744)
                        else -> Color.LightGray
                    }

                    val isLegendaryOrRelic = item.rarity.lowercase() in listOf("legendary", "relic", "cursed")

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .then(
                                if (isLegendaryOrRelic) {
                                    Modifier.neonGlowPulse(
                                        glowColor = rarityColor,
                                        shape = CutCornerShape(6.dp)
                                    )
                                } else {
                                    Modifier.border(1.dp, rarityColor.copy(alpha = 0.4f), CutCornerShape(6.dp))
                                }
                            )
                            .clickable { selectedInspectItem = item },
                        colors = CardDefaults.cardColors(containerColor = Color.Black),
                        shape = CutCornerShape(6.dp)
                    ) {
                        Box(modifier = Modifier.fillMaxWidth()) {
                            // Full background banner image
                            EidosImage(
                                resName = item.id,
                                borderColor = Color.Transparent,
                                borderWidth = 0.dp,
                                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                                modifier = Modifier.matchParentSize()
                            )

                            // Cybernetic dark overlay for perfect text contrast
                            Box(
                                modifier = Modifier
                                    .matchParentSize()
                                    .background(
                                        androidx.compose.ui.graphics.Brush.verticalGradient(
                                            colors = listOf(
                                                Color.Black.copy(alpha = 0.80f),
                                                Color.Black.copy(alpha = 0.90f)
                                            )
                                        )
                                    )
                            )

                            Column(modifier = Modifier.padding(14.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        EidosImage(
                                            resName = item.id,
                                            borderColor = rarityColor,
                                            borderWidth = 1.dp,
                                            modifier = Modifier.size(28.dp)
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(item.name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Surface(
                                            color = rarityColor.copy(alpha = 0.25f),
                                            border = androidx.compose.foundation.BorderStroke(1.dp, rarityColor),
                                            shape = CutCornerShape(3.dp)
                                        ) {
                                            Text(
                                                item.rarity.uppercase(),
                                                color = rarityColor,
                                                fontSize = 8.sp,
                                                fontWeight = FontWeight.Bold,
                                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                            )
                                        }
                                    }
                                    Text("${item.price} BC", color = amberColor, fontSize = 14.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                }

                                Spacer(modifier = Modifier.height(8.dp))
                                Text(item.description, color = Color.LightGray, fontSize = 11.sp, lineHeight = 14.sp, fontFamily = FontFamily.Monospace)

                                Spacer(modifier = Modifier.height(10.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("🔍 Нажмите для подробностей / осмотра", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)

                                    Button(
                                        onClick = { onBuy(item.id) },
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = amberColor.copy(alpha = 0.25f),
                                            disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                        ),
                                        enabled = (player?.biocoin ?: 0) >= item.price,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if ((player?.biocoin ?: 0) >= item.price) amberColor else Color.DarkGray),
                                        shape = CutCornerShape(4.dp),
                                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp)
                                    ) {
                                        Text(" КУПИТЬ ", color = if ((player?.biocoin ?: 0) >= item.price) amberColor else Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
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

    // Holographic Item Inspection Modal
    selectedInspectItem?.let { inspect ->
        val inspectRarityColor = when (inspect.rarity.lowercase()) {
            "uncommon" -> Color(0xFF1E88E5)
            "rare" -> Color(0xFFFFD54F)
            "epic" -> Color(0xFFAB47BC)
            "legendary" -> Color(0xFFFF7043)
            "relic" -> Color(0xFFFF1744)
            else -> Color.LightGray
        }

        AlertDialog(
            onDismissRequest = { selectedInspectItem = null },
            containerColor = Color.Black,
            modifier = Modifier.border(1.dp, inspectRarityColor, CutCornerShape(8.dp)),
            title = null,
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState())
                ) {
                    // Full-width Image Banner
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(180.dp)
                            .background(Color.Black)
                            .border(1.dp, inspectRarityColor.copy(alpha = 0.5f), CutCornerShape(6.dp))
                    ) {
                        EidosImage(
                            resName = inspect.id,
                            borderColor = Color.Transparent,
                            borderWidth = 0.dp,
                            contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )

                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(60.dp)
                                .align(Alignment.BottomCenter)
                                .background(
                                    androidx.compose.ui.graphics.Brush.verticalGradient(
                                        colors = listOf(Color.Transparent, Color.Black)
                                    )
                                )
                        )

                        Box(
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(8.dp)
                                .background(Color.Black.copy(alpha = 0.85f), CutCornerShape(4.dp))
                                .border(1.dp, inspectRarityColor, CutCornerShape(4.dp))
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                "КЛАСС: ${inspect.rarity.uppercase()}",
                                color = inspectRarityColor,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                        }

                        Text(
                            inspect.name,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                            modifier = Modifier
                                .align(Alignment.BottomStart)
                                .padding(12.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(inspect.description, color = Color.LightGray, fontSize = 11.sp, lineHeight = 15.sp, fontFamily = FontFamily.Monospace)
                    Spacer(modifier = Modifier.height(12.dp))

                    Text("📊 ХАРАКТЕРИСТИКИ И ПОТЕНЦИАЛ:", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "• Тип: ${inspect.type.uppercase()}\n" +
                        "• Диапазон статов: При покупке выпадают рандомные роли в [10–35]!\n" +
                        "• Сокеты под чипы: Поддерживает до ${if (inspect.type == "weapon" || inspect.type == "armor") "3" else "2"} сокетов\n" +
                        "• Поддержка модификаций: Совместим со Слайсером, Квантовой Настройкой и Скверной Бездны",
                        color = Color.Gray,
                        fontSize = 10.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    if (inspect.type in listOf("consumable", "material")) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text("КОЛИЧЕСТВО:", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            IconButton(
                                onClick = { if (buyQuantity > 1) buyQuantity-- },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Text("–", color = amberColor, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                            }
                            Text("$buyQuantity", color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            IconButton(
                                onClick = {
                                    val priceLong = maxOf(1L, inspect.price.toLong())
                                    val maxAfford = ((player?.biocoin ?: 0L) / priceLong).toInt()
                                    if (buyQuantity < minOf(99, maxOf(1, maxAfford))) buyQuantity++
                                },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Text("+", color = amberColor, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                    }

                    val totalCost = inspect.price * buyQuantity.toLong()
                    Text("🪙 СТОИМОСТЬ ПОКУПКИ:", color = amberColor, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    Text(if (buyQuantity > 1) "$totalCost BioCoins (${inspect.price} BC/шт)" else "${inspect.price} BioCoins", color = amberColor, fontSize = 16.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                }
            },
            confirmButton = {
                val totalCost = inspect.price * buyQuantity.toLong()
                Button(
                    onClick = {
                        repeat(buyQuantity) { onBuy(inspect.id) }
                        selectedInspectItem = null
                        buyQuantity = 1
                    },
                    enabled = (player?.biocoin ?: 0) >= totalCost,
                    colors = ButtonDefaults.buttonColors(containerColor = amberColor),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text(if (buyQuantity > 1) "КУПИТЬ ($buyQuantity ШТ)" else "КУПИТЬ В 1 КЛИК", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            },
            dismissButton = {
                TextButton(onClick = { selectedInspectItem = null; buyQuantity = 1 }) {
                    Text("ЗАКРЫТЬ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                }
            }
        )
    }
}
