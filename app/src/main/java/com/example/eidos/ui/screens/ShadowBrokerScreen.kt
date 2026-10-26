package com.example.eidos.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.data.Player
import com.example.eidos.data.GameRepository.ItemMetadata
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.utils.neonGlowPulse
import com.example.eidos.ui.components.CyberGridOverlay
import com.example.eidos.ui.components.EidosImage
import com.example.eidos.data.SupabaseClientManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

object ShadowBrokerManager {
    // 3 hour cycle: 1 hour active (3,600,000 ms), 2 hours inactive (7,200,000 ms)
    const val ACTIVE_DURATION_MS = 3_600_000L
    const val INACTIVE_DURATION_MS = 7_200_000L
    const val TOTAL_CYCLE_MS = ACTIVE_DURATION_MS + INACTIVE_DURATION_MS

    fun isBrokerActive(currentTimeMillis: Long = System.currentTimeMillis()): Boolean {
        val timeInCycle = currentTimeMillis % TOTAL_CYCLE_MS
        return timeInCycle < ACTIVE_DURATION_MS
    }

    fun getTimeRemainingMs(currentTimeMillis: Long = System.currentTimeMillis()): Long {
        val timeInCycle = currentTimeMillis % TOTAL_CYCLE_MS
        return if (timeInCycle < ACTIVE_DURATION_MS) {
            ACTIVE_DURATION_MS - timeInCycle
        } else {
            TOTAL_CYCLE_MS - timeInCycle
        }
    }

    fun formatTime(ms: Long): String {
        val totalSec = (ms / 1000).coerceAtLeast(0)
        val hours = totalSec / 3600
        val mins = (totalSec % 3600) / 60
        val secs = totalSec % 60
        return if (hours > 0) {
            String.format(java.util.Locale.US, "%02d:%02d:%02d", hours, mins, secs)
        } else {
            String.format(java.util.Locale.US, "%02d:%02d", mins, secs)
        }
    }

    fun getActiveWindowSeed(currentTimeMillis: Long = System.currentTimeMillis()): Long {
        return currentTimeMillis / TOTAL_CYCLE_MS
    }

    fun getBrokerAssortment(
        allItems: List<ItemMetadata>,
        currentTimeMillis: Long = System.currentTimeMillis()
    ): List<ItemMetadata> {
        val brokerSpecialIds = setOf("reality_silencer", "karma_inversion", "death_mask")
        val exclusivePool = allItems.filter { item ->
            val r = item.rarity.lowercase()
            r in listOf("epic", "legendary", "relic", "cursed") ||
            item.type == "chip" ||
            item.name.contains("💀") ||
            item.name.contains("👁") ||
            item.name.contains("🔴") ||
            item.name.contains("🟠") ||
            brokerSpecialIds.contains(item.id)
        }

        val pool = if (exclusivePool.size >= 5) exclusivePool else allItems
        if (pool.isEmpty()) return emptyList()

        val seed = getActiveWindowSeed(currentTimeMillis)
        val random = java.util.Random(seed)
        return pool.shuffled(random).take(5)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShadowBrokerScreen(
    player: Player?,
    items: List<ItemMetadata>,
    onBuy: (itemId: String, useBioCoins: Boolean) -> Unit,
    onBack: () -> Unit
) {
    var currentTimeMillis by remember { mutableStateOf(System.currentTimeMillis()) }
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        while (true) {
            delay(1000)
            currentTimeMillis = System.currentTimeMillis()
        }
    }

    val isBrokerActive = ShadowBrokerManager.isBrokerActive(currentTimeMillis) || (player?.is_admin == true)
    val remainingMs = ShadowBrokerManager.getTimeRemainingMs(currentTimeMillis)
    val timeStr = ShadowBrokerManager.formatTime(remainingMs)

    val current5Items = remember(ShadowBrokerManager.getActiveWindowSeed(currentTimeMillis), items) {
        ShadowBrokerManager.getBrokerAssortment(items, currentTimeMillis)
    }

    val purpleAccent = Color(0xFF9C27B0)
    val neonPink = Color(0xFFE040FB)

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "ТЕНЕВОЙ БРОКЕР // ТЕНЕВОЙ ШЛЮЗ",
                            color = neonPink,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            if (isBrokerActive) "🟢 СИГНАЛ АКТИВЕН // ОСТАЛОСЬ: $timeStr" else "🔴 СИГНАЛ ПОТЕРЯН",
                            color = if (isBrokerActive) Color.Green else Color.Red,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = neonPink)
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

            Column(modifier = Modifier.fillMaxSize()) {
            // Balance Panel
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(EidosGlass)
                    .border(1.dp, purpleAccent.copy(alpha = 0.4f))
                    .padding(horizontal = 16.dp, vertical = 10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("XP БАЛАНС: ${player?.xp ?: 0} XP", color = neonPink, fontWeight = FontWeight.Bold, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                        Text("BC БАЛАНС: ${player?.biocoin ?: 0} BC", color = Color(0xFFFFB300), fontWeight = FontWeight.Bold, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
                    }
                    Surface(
                        color = purpleAccent.copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, neonPink),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            if (isBrokerActive) "⏱️ СЕССИЯ: $timeStr" else "🔴 ОФФЛАЙН",
                            color = Color.White,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            if (!isBrokerActive) {
                // Offline screen view
                Box(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F0818)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.Red.copy(alpha = 0.5f)),
                        shape = CutCornerShape(8.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            Text("🔴 СВЯЗЬ ОБОРВАНА", color = Color.Red, fontSize = 18.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                            Text(
                                "📡 ГОЛОС EIDOS: Теневой Брокер отключился от терминала и меняет частоту связи, чтобы избежать отслеживания ИИ Ищейками.\n\n" +
                                "Он появляется случайно несколько раз в день ровно на 1 час. До следующего подключения осталось:",
                                color = Color.LightGray,
                                fontSize = 12.sp,
                                textAlign = TextAlign.Center,
                                lineHeight = 16.sp
                            )
                            Surface(
                                color = Color.Black,
                                border = androidx.compose.foundation.BorderStroke(1.dp, purpleAccent),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text(
                                    "⏳ ПРИБЫТИЕ ЧЕРЕЗ: $timeStr",
                                    color = neonPink,
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(16.dp),
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            Button(
                                onClick = onBack,
                                colors = ButtonDefaults.buttonColors(containerColor = purpleAccent),
                                shape = CutCornerShape(4.dp)
                            ) {
                                Text("ВЕРНУТЬСЯ В ХАБ", color = Color.White, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            } else {
                // Active screen view with 5 items
                Surface(
                    color = purpleAccent.copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, neonPink),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text(
                        text = "📡 ГОЛОС EIDOS: Секретный Ассортимент Теневого Брокера!\n💡 Условия сделки: В наличии ровно 5 эксклюзивных предметов (реликвии, проклятый шмот, редкие чипы), недоступных в обычном магазине. Успей приобрести их до закрытия шлюза связи!",
                        color = Color.White,
                        fontSize = 10.sp,
                        lineHeight = 14.sp,
                        modifier = Modifier.padding(8.dp),
                        fontFamily = FontFamily.Monospace
                    )
                }

                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    items(current5Items, key = { it.id }) { item ->
                        val rarityColor = when (item.rarity.lowercase()) {
                            "relic" -> Color(0xFFFF1744)
                            "cursed" -> Color(0xFFFF5252)
                            "legendary" -> Color(0xFFFF7043)
                            "epic" -> Color(0xFFAB47BC)
                            else -> neonPink
                        }

                        val xpPrice = com.example.eidos.data.ShadowBrokerPrices.getXpPrice(item)
                        val bcPrice = com.example.eidos.data.ShadowBrokerPrices.getBcPrice(item)

                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .neonGlowPulse(glowColor = rarityColor, shape = CutCornerShape(8.dp)),
                            colors = CardDefaults.cardColors(containerColor = EidosGlass),
                            shape = CutCornerShape(8.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        EidosImage(
                                            resName = item.id,
                                            borderColor = rarityColor,
                                            borderWidth = 1.dp,
                                            modifier = Modifier.size(36.dp)
                                        )
                                        Spacer(modifier = Modifier.width(10.dp))
                                        Text(
                                            item.name,
                                            color = Color.White,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 14.sp,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Surface(
                                        color = rarityColor.copy(alpha = 0.2f),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, rarityColor),
                                        shape = CutCornerShape(3.dp)
                                    ) {
                                        Text(
                                            item.rarity.uppercase(),
                                            color = rarityColor,
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Bold,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    item.description,
                                    color = Color.LightGray,
                                    fontSize = 11.sp,
                                    lineHeight = 15.sp,
                                    fontFamily = FontFamily.Monospace
                                )

                                Spacer(modifier = Modifier.height(12.dp))

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    // Buy with XP
                                    Button(
                                        onClick = {
                                            onBuy(item.id, false)
                                            if (player != null) {
                                                coroutineScope.launch {
                                                    SupabaseClientManager.addRaidLog(
                                                        playerId = player.uid.toString(),
                                                        logText = "🛒 ТЕНЕВАЯ СДЕЛКА: Приобретен [${item.name}] за $xpPrice XP"
                                                    )
                                                }
                                            }
                                        },
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = purpleAccent.copy(alpha = 0.25f),
                                            disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                        ),
                                        enabled = (player?.xp ?: 0) >= xpPrice,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if ((player?.xp ?: 0) >= xpPrice) neonPink else Color.DarkGray),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.weight(1f),
                                        contentPadding = PaddingValues(vertical = 8.dp)
                                    ) {
                                        Text(
                                            "$xpPrice XP",
                                            color = if ((player?.xp ?: 0) >= xpPrice) neonPink else Color.Gray,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                    }

                                    // Buy with BioCoin
                                    Button(
                                        onClick = {
                                            onBuy(item.id, true)
                                            if (player != null) {
                                                coroutineScope.launch {
                                                    SupabaseClientManager.addRaidLog(
                                                        playerId = player.uid.toString(),
                                                        logText = "🛒 ТЕНЕВАЯ СДЕЛКА: Приобретен [${item.name}] за $bcPrice BC"
                                                    )
                                                }
                                            }
                                        },
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = Color(0xFFFFB300).copy(alpha = 0.2f),
                                            disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                        ),
                                        enabled = (player?.biocoin ?: 0) >= bcPrice,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, if ((player?.biocoin ?: 0) >= bcPrice) Color(0xFFFFB300) else Color.DarkGray),
                                        shape = CutCornerShape(4.dp),
                                        modifier = Modifier.weight(1f),
                                        contentPadding = PaddingValues(vertical = 8.dp)
                                    ) {
                                        Text(
                                            "$bcPrice BC",
                                            color = if ((player?.biocoin ?: 0) >= bcPrice) Color(0xFFFFB300) else Color.Gray,
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
}
}
