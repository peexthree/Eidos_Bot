package io.eidos.zerolayer.ui.screens

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
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.data.GameRepository.ItemMetadata
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.ZzzGold
import io.eidos.zerolayer.ui.theme.ZzzDangerRed
import io.eidos.zerolayer.ui.utils.neonGlowPulse
import io.eidos.zerolayer.ui.components.CyberGridOverlay
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.data.SupabaseClientManager
import io.eidos.zerolayer.ui.components.EvaSpeechBanner
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import androidx.compose.ui.platform.LocalContext
import android.widget.Toast
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
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val haptics = remember { HapticFeedbackManager.getInstance(context) }

    LaunchedEffect(Unit) {
        val tutorialPrefs = context.getSharedPreferences("eidos_tutorial_prefs", android.content.Context.MODE_PRIVATE)
        if (!tutorialPrefs.getBoolean("eva_tip_broker_played", false)) {
            tutorialPrefs.edit().putBoolean("eva_tip_broker_played", true).apply()
            audio.playEvaHubVoice(EidosAudioManager.EvaHubVoiceType.TIP_BROKER)
        }
    }

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
                            if (isBrokerActive) "СИГНАЛ АКТИВЕН // ОСТАЛОСЬ: $timeStr" else "СИГНАЛ ПОТЕРЯН",
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
                        Text(
                            "ДОСТУПНЫЕ СРЕДСТВА",
                            color = Color.LightGray,
                            fontSize = 9.5.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            "${player?.biocoin ?: 0} BC",
                            color = ZzzGold,
                            fontWeight = FontWeight.Black,
                            fontSize = 17.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Surface(
                        color = purpleAccent.copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, neonPink),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            if (isBrokerActive) "СЕССИЯ: $timeStr" else "ОФФЛАЙН",
                            color = Color.White,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            // DIR-3: Нарративный статус гибели Теневого Брокера (Глубина 4000м+)
            if ((player?.max_depth ?: 0) >= 4000) {
                Surface(
                    color = Color(0x33FF0055),
                    shape = CutCornerShape(6.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFF0055)),
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp)
                ) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        Text(
                            "⚠️ [ПЕРЕХВАТ 95.0 GHz // ПОСЛЕДНИЙ ЛОГ ADMIN-00]:",
                            color = Color(0xFFFF0055),
                            fontWeight = FontWeight.Bold,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(Modifier.height(2.dp))
                        Text(
                            "«Инквизиторы Ядра взломали мой узел под ледником. Мой аватар форматируют... Но этот терминал автономного сбыта останется работать для тебя вечно. Забирай всё, что сможешь. И помни Землю.»",
                            color = Color.White,
                            fontSize = 9.5.sp,
                            lineHeight = 14.sp,
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
                            Text("СВЯЗЬ ОБОРВАНА", color = Color.Red, fontSize = 18.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                            Text(
                                "ГОЛОС EIDOS: Теневой Брокер отключился от терминала и меняет частоту связи, чтобы избежать отслеживания ИИ Ищейками.\n\n" +
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
                                    "ПРИБЫТИЕ ЧЕРЕЗ: $timeStr",
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
                EvaSpeechBanner(
                    text = "Оператор, связь с Теневым Брокером нестабильна. Доступно 5 эксклюзивных протоколов. Все расчеты ведутся строго в BioCoin. Выбирай осторожно.",
                    isSpeaking = false,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                )

                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    items(current5Items, key = { it.id }) { item ->
                        val rarityColor = when (item.rarity.lowercase()) {
                            "relic" -> ZzzDangerRed
                            "cursed" -> ZzzDangerRed
                            "legendary" -> Color(0xFFFF7043)
                            "epic" -> Color(0xFFAB47BC)
                            else -> neonPink
                        }

                        val bcPrice = io.eidos.zerolayer.data.ShadowBrokerPrices.getBcPrice(item)
                        val canAfford = (player?.biocoin ?: 0) >= bcPrice

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

                                Button(
                                    onClick = {
                                        if (canAfford) {
                                            onBuy(item.id, true)
                                            audio.playSound(EidosAudioManager.SoundType.ITEM_LOOT)
                                            haptics.click()
                                            Toast.makeText(context, "Приобретено: ${item.name}", Toast.LENGTH_SHORT).show()
                                            if (player != null) {
                                                coroutineScope.launch {
                                                    SupabaseClientManager.addRaidLog(
                                                        playerId = player.uid.toString(),
                                                        logText = "ТЕНЕВАЯ СДЕЛКА: Приобретен [${item.name}] за $bcPrice BC"
                                                    )
                                                }
                                            }
                                        } else {
                                            audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                                            haptics.puzzleError()
                                            Toast.makeText(context, "Недостаточно BioCoin! Нужно $bcPrice BC (У вас: ${player?.biocoin ?: 0} BC)", Toast.LENGTH_SHORT).show()
                                        }
                                    },
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = if (canAfford) ZzzGold.copy(alpha = 0.25f) else Color.DarkGray.copy(alpha = 0.15f),
                                        disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                    ),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, if (canAfford) ZzzGold else Color.DarkGray),
                                    shape = CutCornerShape(4.dp),
                                    modifier = Modifier.fillMaxWidth(),
                                    contentPadding = PaddingValues(vertical = 10.dp)
                                ) {
                                    Text(
                                        text = if (canAfford) "КУПИТЬ ЗА $bcPrice BC" else "ТРЕБУЕТСЯ $bcPrice BC",
                                        color = if (canAfford) ZzzGold else Color.Gray,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace,
                                        letterSpacing = 0.5.sp
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
