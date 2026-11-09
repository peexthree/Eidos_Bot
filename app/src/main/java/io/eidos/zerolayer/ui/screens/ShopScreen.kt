package io.eidos.zerolayer.ui.screens

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
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.GameRepository.ItemMetadata
import io.eidos.zerolayer.ui.theme.*
import io.eidos.zerolayer.ui.MainViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import io.eidos.zerolayer.ui.utils.neonGlowPulse
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.VideoBackground
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.cyberClickable
import io.eidos.zerolayer.ui.components.cyberHudBorder
import io.eidos.zerolayer.ui.components.EidosGlassCard
import io.eidos.zerolayer.ui.components.EidosRarityBadge
import io.eidos.zerolayer.ui.components.rarityColor
import io.eidos.zerolayer.ui.components.EidosButton
import io.eidos.zerolayer.ui.components.EidosButtonVariant
import io.eidos.zerolayer.ui.components.ZzzIcon

/** Item types that count as equipment for the loot acquisition ceremony. */
private val EQUIPMENT_ITEM_TYPES = listOf("weapon", "armor", "head", "chip")

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
    onEquipNow: (String) -> Unit = {},
    onRollGacha: () -> Unit = {},
    onSynthesizeFragments: () -> Unit = {},
    dataFragmentsCount: Int = 0,
    onBack: () -> Unit
) {
    val amberColor = ZzzGold

    // QoL: живой поток инвентаря оператора для пометки "В НАЛИЧИИ" (тот же паттерн viewModel(), что в HubScreen)
    val mainViewModel: MainViewModel = viewModel()
    val shopInventory by mainViewModel.inventory.collectAsState()

    var sortBy by remember { mutableStateOf("price_asc") } // "price_asc", "price_desc", "name"
    var selectedInspectItem by remember { mutableStateOf<ItemMetadata?>(null) }
    var buyQuantity by remember { mutableStateOf(1) }
    var pendingConfirmItem by remember { mutableStateOf<ItemMetadata?>(null) }
    var pendingConfirmCost by remember { mutableLongStateOf(0L) }
    var pendingConfirmQuantity by remember { mutableIntStateOf(1) }
    var acquiredCelebrationItem by remember { mutableStateOf<ItemMetadata?>(null) }

    val categories = listOf(
        "all" to "ВСЕ ТОВАРЫ",
        "gacha" to "ЛУТБОКСЫ",
        "billing" to "IAP ДОНАТ",
        "weapon" to "ОРУЖИЕ",
        "armor" to "БРОНЯ",
        "head" to "ШЛЕМЫ",
        "chip" to "ЧИПЫ",
        "consumable" to "РАСХОДНИКИ",
        "material" to "РЕСУРСЫ"
    )

    val shopSpecialIds = remember { setOf("scavenger_mask", "nomad_goggles", "aegis") }
    val filteredItems = remember(items, selectedCategory, searchQuery, sortBy) {
        items
            .distinctBy { it.id }
            .filter { selectedCategory == "all" || it.type == selectedCategory }
            .filter {
                val rarityLower = it.rarity.lowercase()
                val isShopSpecial = shopSpecialIds.contains(it.id)
                (isShopSpecial || rarityLower in listOf("common", "uncommon", "rare"))
            }
            .filter { it.name.contains(searchQuery, ignoreCase = true) || it.description.contains(searchQuery, ignoreCase = true) }
            .sortedWith { a, b ->
                when (sortBy) {
                    "price_asc" -> a.price.compareTo(b.price)
                    "price_desc" -> b.price.compareTo(a.price)
                    else -> a.name.compareTo(b.name)
                }
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
                            buildAnnotatedString {
                                withStyle(SpanStyle(color = EidosCyan)) { append("ЧЁРНЫЙ РЫНОК ") }
                                withStyle(SpanStyle(color = ZzzAcidYellow)) { append("// ТОРГОВЛЯ") }
                            },
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
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
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosCyan)
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
            io.eidos.zerolayer.ui.components.FirstTimeTooltip(
                prefKey = "tooltip_shown_shop",
                text = "Трать BioCoin на расходники, защитные протоколы и редкие кибердеки.",
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
            )
            // Balance Panel with animated BioCoins counter
            val targetBioCoins = (player?.biocoin ?: 0L).coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
            val animatedBioCoins by animateIntAsState(
                targetValue = targetBioCoins,
                animationSpec = tween(durationMillis = 600, easing = FastOutSlowInEasing),
                label = "animatedBioCoins"
            )

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
                        ZzzIcon(
                            iconRes = R.drawable.ic_res_biocoin,
                            size = 20.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("БАЛАНС ТЕРМИНАЛА:", color = Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }
                    Text("$animatedBioCoins BC", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 18.sp, fontFamily = FontFamily.Monospace)
                }
            }

            // Shadow Broker Welcoming Atmosphere Header
            CyberCornerBracketBox(
                bracketSize = 14.dp,
                bracketColor = amberColor,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = CutCornerShape(8.dp),
                    border = androidx.compose.foundation.BorderStroke(1.2.dp, amberColor.copy(alpha = 0.65f)),
                    colors = CardDefaults.cardColors(containerColor = Color(0xF2080D14))
                ) {
                    Box(modifier = Modifier.fillMaxWidth()) {
                        // Background Art ui_gemini_generated_imag
                        Image(
                            painter = painterResource(id = R.drawable.ui_gemini_generated_imag),
                            contentDescription = "Теневой Брокер",
                            contentScale = ContentScale.Crop,
                            modifier = Modifier
                                .matchParentSize()
                                .alpha(0.35f)
                        )

                        Box(
                            modifier = Modifier
                                .matchParentSize()
                                .background(
                                    Brush.horizontalGradient(
                                        listOf(
                                            Color.Black.copy(alpha = 0.90f),
                                            Color.Black.copy(alpha = 0.65f),
                                            amberColor.copy(alpha = 0.20f)
                                        )
                                    )
                                )
                        )

                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            // Broker Portrait Box
                            Box(
                                modifier = Modifier
                                    .size(54.dp)
                                    .clip(CutCornerShape(6.dp))
                                    .background(Color.Black)
                                    .border(1.2.dp, amberColor, CutCornerShape(6.dp)),
                                contentAlignment = Alignment.Center
                            ) {
                                Image(
                                    painter = painterResource(id = R.drawable.ui_gemini_generated_imag),
                                    contentDescription = "Broker Portrait",
                                    contentScale = ContentScale.Crop,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }

                            Column(modifier = Modifier.weight(1f)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_menu_market, size = 12.dp)
                                    Spacer(Modifier.width(4.dp))
                                    Text(
                                        "ТЕНЕВОЙ БРОКЕР // АНКЛАВ ЧЕРНОГО РЫНКА",
                                        color = amberColor,
                                        fontWeight = FontWeight.Black,
                                        fontSize = 11.5.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                                Spacer(Modifier.height(3.dp))
                                Text(
                                    "«Рад видеть живого оператора в моем анклаве. Трать BioCoins с умом: здесь лучшее оружие, чипы и аптечки. Нулевой Слой не прощает дилетантов!»",
                                    color = Color(0xFFE2E8F0),
                                    fontSize = 9.5.sp,
                                    fontFamily = FontFamily.Monospace,
                                    lineHeight = 13.sp
                                )
                            }
                        }
                    }
                }
            }

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
                        io.eidos.zerolayer.ui.components.ZzzWindowCard(
                            title = "ЧЕРНЫЙ РЫНОК (GACHA)",
                            subTitle = "VOID CACHE 1000 BC",
                            headerBadge = "GACHA CUBE",
                            borderColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
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

                                    // gacha_cube_lootbox exists in drawable - safe to call directly
                                    val gachaPainter = painterResource(id = R.drawable.gacha_cube_lootbox)
                                    if (gachaPainter != null) {
                                        Image(
                                            painter = gachaPainter,
                                            contentDescription = "Void Gacha Cube",
                                            modifier = Modifier
                                                .size(120.dp)
                                                .graphicsLayer {
                                                    scaleX = cubeScale
                                                    scaleY = cubeScale
                                                },
                                            contentScale = ContentScale.Fit
                                        )
                                    } else {
                                        ZzzIcon(iconRes = R.drawable.ic_event_chest, size = 64.dp)
                                    }
                                }

                                Spacer(modifier = Modifier.height(6.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(iconRes = R.drawable.ic_event_chest, size = 16.dp)
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("ЛУТБОКС", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, fontFamily = FontFamily.SansSerif)
                                    }
                                    Text(
                                        "GACHA ROLL CHANCES:\n1% CURSED | 4% LEGENDARY",
                                        color = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                io.eidos.zerolayer.ui.components.ZzzMainButton(
                                    text = "ОТКРЫТЬ (1000 BC) >",
                                    onClick = onRollGacha,
                                    primaryColor = io.eidos.zerolayer.ui.theme.ZzzElectricCyan,
                                    borderColor = io.eidos.zerolayer.ui.theme.ZzzAcidYellow,
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
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(iconRes = R.drawable.ic_res_energy, size = 16.dp)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("СИНТЕЗАТОР ДАННЫХ (DATA SYNTHESIS)", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                }
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
            } else if (selectedCategory == "billing") {
                val context = androidx.compose.ui.platform.LocalContext.current
                val activity = context as? android.app.Activity
                val coroutineScope = rememberCoroutineScope()
                val billingManager = remember { io.eidos.zerolayer.ui.utils.EidosBillingManager(context, coroutineScope) }
                val telemetryManager = remember { io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context) }

                LaunchedEffect(Unit) {
                    billingManager.startConnection()
                }

                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    item {
                        // 1. Neurolink Premium Subscription
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(1.5.dp, EidosNeon, CutCornerShape(8.dp)),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF0C1412)),
                            shape = CutCornerShape(8.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        ZzzIcon(iconRes = R.drawable.ic_res_overdrive, size = 16.dp)
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("ПОДПИСКА «НЕЙРО-ЛИНК ПРЕМИУМ»", color = EidosNeon, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                    }
                                    Text("SUBSCRIPTION", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                }
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "• +50% XP во всех рейд-сессиях\n" +
                                    "• Эксклюзивная неоновая статус-аура профиля\n" +
                                    "• Двойной суточный депо-припас в Хабе\n" +
                                    "• Бесплатный сброс навыков у Теневого Брокера",
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    lineHeight = 16.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Button(
                                    onClick = {
                                        telemetryManager.logPurchaseInitiated("neurolink_premium")
                                        if (activity != null) {
                                            billingManager.launchBillingFlow(
                                                activity = activity,
                                                productId = "neurolink_premium",
                                                onError = {},
                                                onSuccess = { token, sku ->
                                                    if (billingManager.validatePurchaseToken(token)) {
                                                        telemetryManager.logPurchaseSuccess(sku, token)
                                                        onBuy("neurolink_premium")
                                                    }
                                                }
                                            )
                                        }
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("ОФОРМИТЬ ПРЕМИУМ", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }

                    item {
                        // 2. Biocoin Pack 1000
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(1.5.dp, ZzzGold, CutCornerShape(8.dp)),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF141008)),
                            shape = CutCornerShape(8.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(iconRes = R.drawable.ic_res_biocoin, size = 16.dp)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("ПАКЕТ 1000 BIOCOINS", color = ZzzGold, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                }
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "Мгновенное зачисление +1000 BioCoins на баланс терминала для покупки оружия, чипов и ремкомплектов.",
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    lineHeight = 15.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Button(
                                    onClick = {
                                        telemetryManager.logPurchaseInitiated("biocoin_pack_1000")
                                        if (activity != null) {
                                            billingManager.launchBillingFlow(
                                                activity = activity,
                                                productId = "biocoin_pack_1000",
                                                onError = {},
                                                onSuccess = { token, sku ->
                                                    if (billingManager.validatePurchaseToken(token)) {
                                                        telemetryManager.logPurchaseSuccess(sku, token)
                                                        onBuy("biocoin_pack_1000")
                                                    }
                                                }
                                            )
                                        }
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = ZzzGold),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("ПРИОБРЕСТИ +1000 BC", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }

                    item {
                        // 3. Cargo Insurance
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(1.5.dp, EidosCyan, CutCornerShape(8.dp)),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF081216)),
                            shape = CutCornerShape(8.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(iconRes = R.drawable.ic_event_chest, size = 16.dp)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("СТРАХОВКА ГРУЗА БЕЗДНЫ", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 14.sp, fontFamily = FontFamily.Monospace)
                                }
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    "Автоматическое сокрытие буфера при 0% Сигнала. Вся найденная добыча сохраняется при провале рейда.",
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    lineHeight = 15.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Button(
                                    onClick = {
                                        telemetryManager.logPurchaseInitiated("cargo_insurance")
                                        if (activity != null) {
                                            billingManager.launchBillingFlow(
                                                activity = activity,
                                                productId = "cargo_insurance",
                                                onError = {},
                                                onSuccess = { token, sku ->
                                                    if (billingManager.validatePurchaseToken(token)) {
                                                        telemetryManager.logPurchaseSuccess(sku, token)
                                                        onBuy("cargo_insurance")
                                                    }
                                                }
                                            )
                                        }
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("АКТИВИРОВАТЬ СТРАХОВКУ", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                                }
                            }
                        }
                    }
                }
            } else if (filteredItems.isEmpty()) {
                // Empty search/filter result: signal-lost terminal state with reset action
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    CyberCornerBracketBox(
                        bracketSize = 14.dp,
                        bracketColor = amberColor.copy(alpha = 0.7f),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color(0xFF090F17).copy(alpha = 0.7f))
                                .border(1.dp, amberColor.copy(alpha = 0.35f), CutCornerShape(8.dp))
                                .padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            ZzzIcon(
                                iconRes = R.drawable.ic_action_scan,
                                size = 32.dp,
                                tint = amberColor.copy(alpha = 0.8f)
                            )
                            Text(
                                "СИГНАЛ ПОТЕРЯН // НИЧЕГО НЕ НАЙДЕНО",
                                color = amberColor,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                            Text(
                                "ПО ПОИСКОВОМУ ЗАПРОСУ НЕ ОБНАРУЖЕНО ПРЕДМЕТОВ.\nПРОВЕРЬ ФИЛЬТРЫ ИЛИ СБРОСЬ КАТАЛОГ.",
                                color = Color.Gray,
                                fontSize = 10.sp,
                                lineHeight = 14.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                            Button(
                                onClick = {
                                    onSearchQueryChange("")
                                    onCategoryChange("all")
                                    sortBy = "price_asc"
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = amberColor.copy(alpha = 0.25f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, amberColor),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text(
                                    "СБРОС ФИЛЬТРОВ",
                                    color = amberColor,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Fixed(2),
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(filteredItems, key = { it.id }) { item ->
                        val itemRarityColor = rarityColor(item.rarity)
                        // QoL: сколько единиц товара уже лежит в инвентаре оператора
                        val ownedCount = shopInventory
                            .filter { it.item_id == item.id }
                            .sumOf { it.quantity.coerceAtLeast(1) }
                        val effectivePrice = if (item.price > 0) item.price else when (item.rarity.lowercase()) {
                            "uncommon" -> 350
                            "rare" -> 1200
                            "epic" -> 3500
                            "legendary" -> 10000
                            "relic" -> 25000
                            "cursed" -> 50000
                            else -> 100
                        }

                        val canAfford = (player?.biocoin ?: 0L) >= effectivePrice.toLong()
                        val meetsLevel = (player?.level ?: 1) >= item.reqLevel
                        val canBuy = canAfford && meetsLevel

                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .background(Color(0xFF090F17).copy(alpha = 0.70f))
                                .border(1.dp, itemRarityColor.copy(alpha = 0.65f), RoundedCornerShape(8.dp))
                                .cyberHudBorder(
                                    color = itemRarityColor.copy(alpha = 0.85f),
                                    cornerLength = 8.dp,
                                    strokeWidth = 1.5.dp
                                )
                                .cyberClickable { selectedInspectItem = item }
                                .padding(8.dp)
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                // Large 110.dp Showcase Art Container
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .height(110.dp)
                                        .clip(RoundedCornerShape(6.dp))
                                        .background(
                                            Brush.verticalGradient(
                                                colors = listOf(
                                                    itemRarityColor.copy(alpha = 0.12f),
                                                    Color(0xFF04070C)
                                                )
                                            )
                                        )
                                        .border(1.dp, itemRarityColor.copy(alpha = 0.35f), RoundedCornerShape(6.dp)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    EidosImage(
                                        resName = item.id,
                                        borderColor = Color.Transparent,
                                        borderWidth = 0.dp,
                                        contentScale = ContentScale.Crop,
                                        modifier = Modifier.fillMaxSize()
                                    )

                                    // Rarity Badge top-end
                                    Box(
                                        modifier = Modifier
                                            .align(Alignment.TopEnd)
                                            .background(Color.Black.copy(alpha = 0.8f), RoundedCornerShape(3.dp))
                                            .border(0.5.dp, itemRarityColor, RoundedCornerShape(3.dp))
                                            .padding(horizontal = 4.dp, vertical = 1.dp)
                                    ) {
                                        Text(
                                            item.rarity.uppercase(),
                                            color = itemRarityColor,
                                            fontSize = 7.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(6.dp))

                                // Item Name
                                Text(
                                    item.name,
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    fontFamily = FontFamily.Monospace,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    textAlign = TextAlign.Center
                                )

                                Spacer(modifier = Modifier.height(3.dp))

                                // QoL: пометка о наличии в инвентаре оператора
                                Text(
                                    "В НАЛИЧИИ: $ownedCount",
                                    color = if (ownedCount > 0) EidosNeon else Color.Gray,
                                    fontSize = 8.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )

                                Spacer(modifier = Modifier.height(3.dp))

                                // Stat Badges
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    if (item.bonusAttack > 0) {
                                        Text("+${item.bonusAttack} ATK", color = EidosRed, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                                    }
                                    if (item.bonusDefense > 0) {
                                        Text("+${item.bonusDefense} DEF", color = EidosCyan, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                                    }
                                    if (item.bonusLuck > 0) {
                                        Text("+${item.bonusLuck} LUCK", color = EidosGold, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                                    }
                                }

                                Spacer(modifier = Modifier.height(6.dp))

                                // Price & Requirements
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                        ZzzIcon(iconRes = R.drawable.ic_res_biocoin, size = 12.dp)
                                        Text(
                                            "$effectivePrice BC",
                                            color = amberColor,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Black,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                    if (item.reqLevel > 1) {
                                        Text(
                                            "LVL ${item.reqLevel}",
                                            color = if (meetsLevel) EidosCyan else ZzzDangerRed,
                                            fontSize = 8.5.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(6.dp))

                                // Instant Buy Button
                                Button(
                                    onClick = {
                                        pendingConfirmItem = item
                                        pendingConfirmCost = effectivePrice.toLong()
                                        pendingConfirmQuantity = 1
                                    },
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = if (canBuy) amberColor.copy(alpha = 0.25f) else Color.DarkGray.copy(alpha = 0.15f),
                                        disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                    ),
                                    enabled = canBuy,
                                    border = androidx.compose.foundation.BorderStroke(1.dp, if (canBuy) amberColor else Color.DarkGray),
                                    shape = CutCornerShape(4.dp),
                                    contentPadding = PaddingValues(vertical = 4.dp),
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .height(34.dp)
                                ) {
                                    val btnText = when {
                                        !meetsLevel -> "УР ${item.reqLevel}"
                                        !canAfford -> "НЕТ BC"
                                        else -> "КУПИТЬ"
                                    }
                                    Text(
                                        btnText,
                                        color = if (canBuy) amberColor else Color.Gray,
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
}

    // Holographic Item Inspection Modal
    selectedInspectItem?.let { inspect ->
        val inspectRarityColor = when (inspect.rarity.lowercase()) {
            "uncommon" -> Color(0xFF1E88E5)
            "rare" -> ZzzGold
            "epic" -> Color(0xFFAB47BC)
            "legendary" -> Color(0xFFFF7043)
            "relic" -> ZzzDangerRed
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

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_action_scan, size = 12.dp)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("ХАРАКТЕРИСТИКИ И ПОТЕНЦИАЛ:", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }
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
                                    val effectiveInspectPrice = if (inspect.price > 0) inspect.price else when (inspect.rarity.lowercase()) {
                                        "uncommon" -> 350
                                        "rare" -> 1200
                                        "epic" -> 3500
                                        "legendary" -> 10000
                                        "relic" -> 25000
                                        "cursed" -> 50000
                                        else -> 100
                                    }
                                    val priceLong = maxOf(1L, effectiveInspectPrice.toLong())
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

                    val effectiveInspectPrice = if (inspect.price > 0) inspect.price else when (inspect.rarity.lowercase()) {
                        "uncommon" -> 350
                        "rare" -> 1200
                        "epic" -> 3500
                        "legendary" -> 10000
                        "relic" -> 25000
                        "cursed" -> 50000
                        else -> 100
                    }
                    val totalCost = effectiveInspectPrice * buyQuantity.toLong()
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_res_biocoin, size = 12.dp)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("СТОИМОСТЬ ПОКУПКИ:", color = amberColor, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }
                    Text(if (buyQuantity > 1) "$totalCost BioCoins ($effectiveInspectPrice BC/шт)" else "$effectiveInspectPrice BioCoins", color = amberColor, fontSize = 16.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                }
            },
            confirmButton = {
                val effectiveInspectPrice = if (inspect.price > 0) inspect.price else when (inspect.rarity.lowercase()) {
                    "uncommon" -> 350
                    "rare" -> 1200
                    "epic" -> 3500
                    "legendary" -> 10000
                    "relic" -> 25000
                    "cursed" -> 50000
                    else -> 100
                }
                val totalCost = effectiveInspectPrice * buyQuantity.toLong()
                Button(
                    onClick = {
                        pendingConfirmItem = inspect
                        pendingConfirmCost = totalCost
                        pendingConfirmQuantity = buyQuantity
                        selectedInspectItem = null
                    },
                    enabled = (player?.biocoin ?: 0L) >= totalCost,
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

    // Modal: Confirmation Dialog for Spending Currency
    if (pendingConfirmItem != null) {
        val item = pendingConfirmItem!!
        CurrencySpendConfirmDialog(
            itemName = if (pendingConfirmQuantity > 1) "${item.name} (${pendingConfirmQuantity} шт)" else item.name,
            cost = pendingConfirmCost,
            currencyName = "BioCoins",
            currentBalance = player?.biocoin ?: 0L,
            onConfirm = {
                repeat(pendingConfirmQuantity) { onBuy(item.id) }
                pendingConfirmItem = null
                // Unified loot acquisition ceremony: only for equipment, not consumables/materials
                if (item.type in EQUIPMENT_ITEM_TYPES) {
                    acquiredCelebrationItem = item
                }
            },
            onDismiss = {
                pendingConfirmItem = null
                pendingConfirmQuantity = 1
            }
        )
    }

    // Modal: Dopamine Celebration Dialog on Acquired Item
    if (acquiredCelebrationItem != null) {
        ItemAcquiredCelebrationDialog(
            item = acquiredCelebrationItem!!,
            onEquipNow = if (acquiredCelebrationItem!!.type in EQUIPMENT_ITEM_TYPES) {
                {
                    onEquipNow(acquiredCelebrationItem!!.id)
                    acquiredCelebrationItem = null
                }
            } else null,
            onDismiss = { acquiredCelebrationItem = null }
        )
    }
}

@Composable
fun CurrencySpendConfirmDialog(
    itemName: String,
    cost: Long,
    currencyName: String = "BioCoins",
    currentBalance: Long,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    val remaining = currentBalance - cost
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ZzzIcon(iconRes = R.drawable.ic_event_danger, size = 16.dp)
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    "ПОДТВЕРЖДЕНИЕ ТРАНЗАКЦИИ",
                    color = ZzzGold,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    "Вы действительно хотите списать средства со счета терминала?",
                    color = Color.LightGray,
                    fontSize = 11.5.sp,
                    fontFamily = FontFamily.Monospace
                )

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0xFF0F151C))
                        .border(1.dp, ZzzGold.copy(alpha = 0.5f), CutCornerShape(4.dp))
                        .padding(10.dp)
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("ОБЪЕКТ: $itemName", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f), thickness = 0.5.dp)
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Текущий баланс:", color = Color.Gray, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text("$currentBalance $currencyName", color = Color.White, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Стоимость:", color = ZzzGold, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text("-$cost $currencyName", color = ZzzGold, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Остаток:", color = if (remaining >= 0) EidosNeon else ZzzDangerRed, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            Text("$remaining $currencyName", color = if (remaining >= 0) EidosNeon else ZzzDangerRed, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                enabled = remaining >= 0,
                colors = ButtonDefaults.buttonColors(containerColor = ZzzGold),
                shape = CutCornerShape(4.dp)
            ) {
                Text("ПОДТВЕРДИТЬ", color = Color.Black, fontWeight = FontWeight.Black, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("ОТМЕНА", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
            }
        },
        containerColor = Color(0xFF090E14),
        shape = CutCornerShape(8.dp)
    )
}

@Composable
fun ItemAcquiredCelebrationDialog(
    item: ItemMetadata,
    onEquipNow: (() -> Unit)? = null,
    onDismiss: () -> Unit
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val haptics = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }
    val audio = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }

    LaunchedEffect(item.id) {
        haptics.lootLegendary()
        audio.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.ITEM_LOOT)
    }

    val itemRarityColor = rarityColor(item.rarity)
    val infiniteTransition = rememberInfiniteTransition(label = "dopamine_pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.96f,
        targetValue = 1.04f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glow"
    )

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_event_chest, size = 18.dp)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        "ПРЕДМЕТ ПОЛУЧЕН!",
                        color = itemRarityColor,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 1.sp
                    )
                }
                Text(
                    "РАСПАКОВКА И ЗАПИСЬ В БАЗУ ДАННЫХ DECK_OS",
                    color = Color.Gray,
                    fontSize = 8.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        },
        text = {
            Box(modifier = Modifier.fillMaxWidth()) {
                VideoBackground(resName = "gacha_open", modifier = Modifier.matchParentSize())
                Box(modifier = Modifier.matchParentSize().background(Color.Black.copy(alpha = 0.70f)))

                Column(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                // Dopamine Big Item Visual with glowing border
                Box(
                    modifier = Modifier
                        .size(100.dp)
                        .graphicsLayer(scaleX = pulseScale, scaleY = pulseScale)
                        .clip(CutCornerShape(8.dp))
                        .background(Color(0xFF0A0F16))
                        .border(2.dp, itemRarityColor.copy(alpha = glowAlpha), CutCornerShape(8.dp))
                        .shadow(elevation = 12.dp, shape = CutCornerShape(8.dp), ambientColor = itemRarityColor, spotColor = itemRarityColor),
                    contentAlignment = Alignment.Center
                ) {
                    EidosImage(
                        resName = item.id,
                        fallbackIcon = Icons.Default.Star,
                        borderColor = Color.Transparent,
                        borderWidth = 0.dp,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize()
                    )
                }

                // Item Name & Rarity Badge
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        item.name.uppercase(),
                        color = Color.White,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    EidosRarityBadge(rarity = item.rarity)
                }

                // Stats preview box
                if (item.bonusAttack > 0 || item.bonusDefense > 0 || item.bonusLuck > 0) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(CutCornerShape(4.dp))
                            .background(Color(0xFF101820))
                            .border(1.dp, itemRarityColor.copy(alpha = 0.3f), CutCornerShape(4.dp))
                            .padding(vertical = 6.dp, horizontal = 10.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        if (item.bonusAttack > 0) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(iconRes = R.drawable.ic_action_attack, size = 12.dp)
                                Spacer(modifier = Modifier.width(3.dp))
                                Text("+${item.bonusAttack} ATK", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                        if (item.bonusDefense > 0) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(iconRes = R.drawable.ic_action_defense, size = 12.dp)
                                Spacer(modifier = Modifier.width(3.dp))
                                Text("+${item.bonusDefense} DEF", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                        if (item.bonusLuck > 0) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                ZzzIcon(iconRes = R.drawable.ic_action_crit, size = 12.dp)
                                Spacer(modifier = Modifier.width(3.dp))
                                Text("+${item.bonusLuck} LUCK", color = ZzzGold, fontWeight = FontWeight.Bold, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }
                }

                // Description & Lore
                Text(
                    text = item.description,
                    color = Color.LightGray,
                    fontSize = 11.sp,
                    lineHeight = 15.sp,
                    fontFamily = FontFamily.Monospace,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        }
    },
    confirmButton = {
        Column(modifier = Modifier.fillMaxWidth()) {
            if (onEquipNow != null) {
                Button(
                    onClick = {
                        haptics.click()
                        audio.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.ITEM_CRAFT)
                        onEquipNow()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ZzzCyanBright),
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(44.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        ZzzIcon(iconRes = R.drawable.ic_nav_inventory, size = 16.dp, tint = Color.Black)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            "НАДЕТЬ СРАЗУ",
                            color = Color.Black,
                            fontWeight = FontWeight.Black,
                            fontSize = 12.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
            }
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = itemRarityColor),
                shape = CutCornerShape(4.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    ZzzIcon(iconRes = R.drawable.ic_nav_inventory, size = 16.dp, tint = Color.Black)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        "ПРИНЯТЬ В ИНВЕНТАРЬ",
                        color = Color.Black,
                        fontWeight = FontWeight.Black,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    },
        containerColor = Color(0xFF070B10),
        shape = CutCornerShape(10.dp),
        modifier = Modifier.border(1.5.dp, itemRarityColor.copy(alpha = 0.8f), CutCornerShape(10.dp))
    )
}
