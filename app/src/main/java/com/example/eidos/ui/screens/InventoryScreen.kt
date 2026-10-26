package com.example.eidos.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.R
import com.example.eidos.data.InventoryItem
import com.example.eidos.data.ItemSlotUtils
import com.example.eidos.data.Player
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosGold
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosOrange
import com.example.eidos.ui.theme.EidosPurple
import com.example.eidos.ui.theme.EidosRed
import com.example.eidos.ui.utils.neonGlowPulse
import com.example.eidos.ui.components.EidosImage
import com.example.eidos.ui.components.cyberClickable
import com.example.eidos.ui.components.cyberHudBorder

import com.example.eidos.data.RaidSession

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InventoryScreen(
    player: Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<com.example.eidos.data.GameRepository.ItemMetadata> = emptyList(),
    activeRaidSession: RaidSession? = null,
    onReturnToRaid: (() -> Unit)? = null,
    onEquip: (InventoryItem) -> Unit,
    onUnequip: (InventoryItem) -> Unit,
    onUseConsumable: (InventoryItem) -> Unit,
    onStartDecryption: (InventoryItem) -> Unit,
    onInstantDecrypt: (InventoryItem) -> Unit,
    onClaimDecryptedCache: (InventoryItem) -> Unit,
    onBack: () -> Unit
) {
    var selectedItem by remember { mutableStateOf<InventoryItem?>(null) }
    var selectedCategory by remember { mutableStateOf("all") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "ИНВЕНТАРЬ // DECK_OS",
                            color = EidosCyan,
                            fontWeight = FontWeight.Black,
                            fontSize = 15.sp,
                            fontFamily = FontFamily.Monospace,
                            letterSpacing = 1.sp
                        )
                        Text(
                            if (activeRaidSession != null) "ПОЛЕВОЙ ДОСТУП В НУЛЕВОМ СЛОЕ" else "СНАРЯЖЕНИЕ & МОДИФИКАЦИИ ЯДРА",
                            color = if (activeRaidSession != null) EidosRed else Color(0xFF78909C),
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
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF070C12))
            )
        },
        containerColor = Color(0xFF05080C)
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            // Layer 0: New PNG Background
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(id = com.example.eidos.R.drawable.bg_inventory),
                contentDescription = null,
                modifier = Modifier.fillMaxSize(),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                alignment = androidx.compose.ui.Alignment.Center
            )
            // Dark Overlay
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.82f))
            )

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp, vertical = 10.dp)
            ) {
                // Active Raid Navigation Banner
                if (activeRaidSession != null && onReturnToRaid != null) {
                    Surface(
                        color = Color(0xFF2A0808),
                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 10.dp)
                            .cyberClickable { onReturnToRaid() }
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text("🚨", fontSize = 14.sp)
                                Column {
                                    Text(
                                        "АКТИВНО ПОГРУЖЕНИЕ В БЕЗДНУ",
                                        color = EidosRed,
                                        fontSize = 10.5.sp,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Text(
                                        "ГЛУБИНА: ${activeRaidSession.depth}м | СИГНАЛ: ${activeRaidSession.signal}%",
                                        color = Color.LightGray,
                                        fontSize = 8.5.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                            Text(
                                "➔ В РЕЙД",
                                color = EidosNeon,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                // Player Core Stats Row
                ProfileSection(player)

                Spacer(modifier = Modifier.height(10.dp))

                // Interactive Equipment Doll
                Text(
                    "АКТИВНАЯ ЭКИПИРОВКА [СЛОТЫ ЯДРА]",
                    color = EidosCyan,
                    fontSize = 10.5.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp,
                    modifier = Modifier.padding(bottom = 6.dp)
                )
                EquipDollSection(inventory, allItemsMetadata, onUnequip)

                Spacer(modifier = Modifier.height(12.dp))

                // Filter Chips Row
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    val categories = listOf(
                        "all" to "ВСЁ",
                        "weapon" to "ОРУЖИЕ",
                        "armor" to "БРОНЯ",
                        "chip" to "ЧИПЫ",
                        "consumable" to "ПРИПАСЫ"
                    )
                    categories.forEach { (catId, catLabel) ->
                        val isSelected = selectedCategory == catId
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(30.dp)
                                .clip(RoundedCornerShape(6.dp))
                                .background(
                                    if (isSelected) EidosCyan.copy(alpha = 0.22f) else Color(0xFF0F1722)
                                )
                                .border(
                                    1.dp,
                                    if (isSelected) EidosCyan else Color(0xFF1E2E3E),
                                    RoundedCornerShape(6.dp)
                                )
                                .cyberClickable { selectedCategory = catId },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = catLabel,
                                color = if (isSelected) EidosCyan else Color(0xFF90A4AE),
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 6.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "КЭШ ПРЕДМЕТОВ [ХРАНИЛИЩЕ]",
                        color = EidosCyan,
                        fontSize = 10.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        "ВСЕГО: ${inventory.size}",
                        color = Color(0xFF78909C),
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Filter inventory
                val filteredInventory = inventory.filter { item ->
                    val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                    val slot = ItemSlotUtils.getSlotForItem(item.item_id, itemMeta)
                    when (selectedCategory) {
                        "all" -> true
                        "weapon" -> slot == "weapon"
                        "armor" -> slot == "armor" || slot == "head"
                        "chip" -> slot == "chip"
                        "consumable" -> isConsumable(item.item_id, itemMeta)
                        else -> true
                    }
                }

                // Item Grid Section
                ItemListSection(filteredInventory, allItemsMetadata) { item ->
                    selectedItem = item
                }
            }
        }
    }

    // Interactive details dialog
    selectedItem?.let { item ->
        val itemMeta = allItemsMetadata.find { it.id == item.item_id }
        val rarity = itemMeta?.rarity ?: getItemRarity(item.item_id)
        val name = itemMeta?.name ?: getItemName(item.item_id)
        val desc = itemMeta?.description ?: getItemDescription(item.item_id)

        val rarityColor = when(rarity) {
            "cursed", "relic" -> EidosRed
            "legendary" -> EidosOrange
            "epic" -> EidosPurple
            "rare" -> EidosCyan
            "uncommon" -> EidosNeon
            else -> Color(0xFFB0BEC5)
        }

        AlertDialog(
            onDismissRequest = { selectedItem = null },
            containerColor = Color(0xFF090F16),
            modifier = Modifier
                .border(1.dp, rarityColor, RoundedCornerShape(10.dp))
                .cyberHudBorder(color = rarityColor, cornerLength = 12.dp, strokeWidth = 2.dp),
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
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color.Black)
                            .border(1.dp, rarityColor.copy(alpha = 0.5f), RoundedCornerShape(8.dp))
                    ) {
                        EidosImage(
                            resName = item.item_id,
                            borderColor = Color.Transparent,
                            borderWidth = 0.dp,
                            contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )

                        // Dark gradient overlay
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(70.dp)
                                .align(Alignment.BottomCenter)
                                .background(
                                    Brush.verticalGradient(
                                        colors = listOf(Color.Transparent, Color(0xFF090F16))
                                    )
                                )
                        )

                        // Rarity Badge top-right
                        Box(
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(8.dp)
                                .background(Color.Black.copy(alpha = 0.85f), RoundedCornerShape(4.dp))
                                .border(1.dp, rarityColor, RoundedCornerShape(4.dp))
                                .padding(horizontal = 8.dp, vertical = 3.dp)
                        ) {
                            Text(
                                "РАНГ: ${rarity.uppercase()}",
                                color = rarityColor,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                        }

                        // Item Name overlaid on bottom-left of banner
                        Text(
                            name,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier
                                .align(Alignment.BottomStart)
                                .padding(10.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    val itemType = getItemType(item.item_id, itemMeta)
                    val reqLevel = itemMeta?.reqLevel ?: 1
                    val canEquip = player == null || player.level >= reqLevel
                    val typeLabel = when(itemType) {
                        "weapon" -> "СНАРЯЖЕНИЕ: ОРУЖИЕ"
                        "armor" -> "СНАРЯЖЕНИЕ: БРОНЯ"
                        "head" -> "СНАРЯЖЕНИЕ: ШЛЕМ"
                        "chip" -> "СНАРЯЖЕНИЕ: ЧИП"
                        "consumable" -> "РАСХОДНЫЙ ПРЕДМЕТ"
                        else -> "МАТЕРИАЛ ДЛЯ КУЗНИЦЫ"
                    }
                    Text(
                        typeLabel,
                        color = EidosCyan,
                        fontSize = 9.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    if (isEquippable(item.item_id, itemMeta)) {
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            "ТРЕБОВАНИЕ ЯДРА: Level $reqLevel ${if (!canEquip) "❌ (Ваш уровень: ${player?.level ?: 1})" else "✅"}",
                            color = if (canEquip) EidosNeon else EidosRed,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        desc,
                        color = Color(0xFFB0BEC5),
                        fontSize = 11.sp,
                        lineHeight = 15.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(10.dp))

                    if (item.durability >= 0 && isEquippable(item.item_id, itemMeta)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                "ПРОЧНОСТЬ ЯДРА",
                                color = Color(0xFF90A4AE),
                                fontSize = 9.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                "${item.durability}/100",
                                color = if (item.durability < 30) EidosRed else EidosNeon,
                                fontSize = 9.5.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        LinearProgressIndicator(
                            progress = item.durability.toFloat() / 100f,
                            color = if (item.durability < 30) EidosRed else EidosCyan,
                            trackColor = Color(0xFF1E2E3E),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp)
                                .height(4.dp)
                                .clip(RoundedCornerShape(2.dp))
                        )
                    } else if (item.quantity > 0) {
                        Text(
                            "В наличии: ${item.quantity} шт.",
                            color = Color.White,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            },
            confirmButton = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (item.item_id == "corrupted_data_cluster") {
                        val custom = item.custom_data
                        if (custom == null || !custom.startsWith("decrypt:")) {
                            Button(
                                onClick = {
                                    onStartDecryption(item)
                                    selectedItem = null
                                },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.25f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text("РАСШИФРОВАТЬ", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            }
                            Button(
                                onClick = {
                                    onInstantDecrypt(item)
                                    selectedItem = null
                                },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.25f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text("УСКОРИТЬ (500 BC)", color = EidosNeon, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            }
                        } else {
                            val endTime = custom.substringAfter("decrypt:").toLongOrNull() ?: 0L
                            val now = System.currentTimeMillis()
                            var timeLeft by remember(endTime) { mutableStateOf(((endTime - now) / 1000).coerceAtLeast(0)) }

                            LaunchedEffect(endTime) {
                                while (timeLeft > 0) {
                                    kotlinx.coroutines.delay(1000)
                                    timeLeft = ((endTime - System.currentTimeMillis()) / 1000).coerceAtLeast(0)
                                }
                            }

                            if (timeLeft <= 0) {
                                Button(
                                    onClick = {
                                        onClaimDecryptedCache(item)
                                        selectedItem = null
                                    },
                                    modifier = Modifier.weight(1f),
                                    colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.35f)),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                    shape = RoundedCornerShape(6.dp)
                                ) {
                                    Text("ОТКРЫТЬ КЭШ", color = EidosNeon, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                }
                            } else {
                                Column(
                                    modifier = Modifier.weight(1f),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Text(
                                        "ПРОГРЕСС: $timeLeft сек.",
                                        color = EidosCyan,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 10.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Button(
                                        onClick = {
                                            onInstantDecrypt(item)
                                            selectedItem = null
                                        },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.25f)),
                                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                        shape = RoundedCornerShape(6.dp)
                                    ) {
                                        Text("УСКОРИТЬ (500 BC)", color = EidosNeon, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                                    }
                                }
                            }
                        }
                    } else if (isEquippable(item.item_id, itemMeta)) {
                        val reqLevel = itemMeta?.reqLevel ?: 1
                        val canEquip = player == null || player.level >= reqLevel
                        if (item.is_equipped) {
                            Button(
                                onClick = {
                                    onUnequip(item)
                                    selectedItem = null
                                },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.25f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text("СНЯТЬ", color = EidosRed, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                            }
                        } else {
                            Button(
                                onClick = {
                                    if (canEquip) {
                                        onEquip(item)
                                        selectedItem = null
                                    }
                                },
                                enabled = canEquip,
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (canEquip) EidosCyan.copy(alpha = 0.25f) else Color(0xFF1B2430)
                                ),
                                border = androidx.compose.foundation.BorderStroke(
                                    1.dp,
                                    if (canEquip) EidosCyan else Color(0xFF37474F)
                                ),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    if (canEquip) "ЭКИПИРОВАТЬ" else "ТРЕБУЕТСЯ LVL $reqLevel",
                                    color = if (canEquip) EidosCyan else Color(0xFF78909C),
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    } else if (isConsumable(item.item_id, itemMeta)) {
                        Button(
                            onClick = {
                                onUseConsumable(item)
                                selectedItem = null
                            },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.25f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                            shape = RoundedCornerShape(6.dp)
                        ) {
                            Text("ИСПОЛЬЗОВАТЬ", color = EidosNeon, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                    }

                    Button(
                        onClick = { selectedItem = null },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF182230)),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("ЗАКРЫТЬ", color = Color(0xFFB0BEC5), fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }
        )
    }
}

@Composable
fun ProfileSection(player: Player?) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(
                Brush.horizontalGradient(
                    colors = listOf(
                        Color(0xFF0C1824).copy(alpha = 0.95f),
                        Color(0xFF070E16).copy(alpha = 0.98f)
                    )
                )
            )
            .border(1.dp, EidosCyan.copy(alpha = 0.45f), RoundedCornerShape(8.dp))
            .cyberHudBorder(color = EidosCyan.copy(alpha = 0.7f), cornerLength = 8.dp, strokeWidth = 1.dp)
            .padding(12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "НЕЙРО-ПРОФИЛЬ // СТАТУС",
                    color = EidosNeon,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    "LVL ${player?.level ?: 1}",
                    color = EidosCyan,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Black,
                    fontFamily = FontFamily.Monospace
                )
            }

            Text(
                player?.username ?: "ОПЕРАТОР",
                color = Color.White,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_biocoin),
                        contentDescription = "BioCoins",
                        modifier = Modifier.size(14.dp),
                        contentScale = ContentScale.Fit
                    )
                    Text(
                        "${player?.biocoin ?: 0} BC",
                        color = EidosGold,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_stat_hp),
                        contentDescription = "HP",
                        modifier = Modifier.size(14.dp),
                        contentScale = ContentScale.Fit
                    )
                    Text(
                        "${player?.hp ?: 100} HP",
                        color = EidosRed,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Image(
                        painter = painterResource(id = R.drawable.ic_neural_exp),
                        contentDescription = "XP",
                        modifier = Modifier.size(14.dp),
                        contentScale = ContentScale.Fit
                    )
                    Text(
                        "${player?.xp ?: 0} XP",
                        color = EidosNeon,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
fun EquipDollSection(
    inventory: List<InventoryItem>,
    allItemsMetadata: List<com.example.eidos.data.GameRepository.ItemMetadata> = emptyList(),
    onUnequip: (InventoryItem) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        val head = inventory.find { it.is_equipped && (it.slot == "head" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "head") }
        val armor = inventory.find { it.is_equipped && (it.slot == "armor" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "armor") }
        val weapon = inventory.find { it.is_equipped && (it.slot == "weapon" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "weapon") }
        val chip = inventory.find { it.is_equipped && (it.slot == "chip" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "chip") }

        EquipSlot("ГОЛОВА", head, allItemsMetadata, onUnequip, Modifier.weight(1f))
        EquipSlot("БРОНЯ", armor, allItemsMetadata, onUnequip, Modifier.weight(1f))
        EquipSlot("ОРУЖИЕ", weapon, allItemsMetadata, onUnequip, Modifier.weight(1f))
        EquipSlot("ЧИП", chip, allItemsMetadata, onUnequip, Modifier.weight(1f))
    }
}

@Composable
fun EquipSlot(
    label: String,
    item: InventoryItem?,
    allItemsMetadata: List<com.example.eidos.data.GameRepository.ItemMetadata> = emptyList(),
    onUnequip: (InventoryItem) -> Unit,
    modifier: Modifier = Modifier
) {
    val itemMeta = item?.let { allItemsMetadata.find { meta -> meta.id == it.item_id } }
    val rarity = itemMeta?.rarity ?: (item?.let { getItemRarity(it.item_id) } ?: "common")
    val rarityColor = when(rarity) {
        "cursed", "relic" -> EidosRed
        "legendary" -> EidosOrange
        "epic" -> EidosPurple
        "rare" -> EidosCyan
        "uncommon" -> EidosNeon
        else -> EidosCyan
    }

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(86.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(Color(0xFF09121B))
                .border(
                    1.dp,
                    if (item != null) rarityColor.copy(alpha = 0.8f) else Color(0xFF1E2E3E),
                    RoundedCornerShape(6.dp)
                )
                .cyberHudBorder(
                    color = if (item != null) rarityColor else Color(0xFF1E2E3E),
                    cornerLength = 6.dp,
                    strokeWidth = 1.dp
                )
                .cyberClickable(enabled = item != null) { item?.let { onUnequip(it) } },
            contentAlignment = Alignment.Center
        ) {
            if (item != null) {
                val name = itemMeta?.name ?: getItemName(item.item_id)

                EidosImage(
                    resName = item.item_id,
                    borderColor = Color.Transparent,
                    borderWidth = 0.dp,
                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )

                // Gradient overlay
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(
                                    Color.Black.copy(alpha = 0.3f),
                                    Color.Black.copy(alpha = 0.85f)
                                )
                            )
                        )
                )

                // Slot label badge top-start
                Box(
                    modifier = Modifier
                        .align(Alignment.TopStart)
                        .padding(3.dp)
                        .background(Color.Black.copy(alpha = 0.8f), RoundedCornerShape(2.dp))
                        .padding(horizontal = 4.dp, vertical = 1.dp)
                ) {
                    Text(
                        label,
                        fontSize = 6.5.sp,
                        color = rarityColor,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // Text written on image
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .padding(bottom = 3.dp, start = 2.dp, end = 2.dp)
                ) {
                    Text(
                        name,
                        fontSize = 8.sp,
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        "${item.durability.toInt()}%",
                        fontSize = 7.sp,
                        color = if (item.durability < 30) EidosRed else EidosNeon,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.Add,
                        contentDescription = null,
                        tint = Color(0xFF37474F),
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        label,
                        fontSize = 8.sp,
                        color = Color(0xFF546E7A),
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
fun ItemListSection(
    inventory: List<InventoryItem>,
    allItemsMetadata: List<com.example.eidos.data.GameRepository.ItemMetadata> = emptyList(),
    onItemClick: (InventoryItem) -> Unit
) {
    if (inventory.isEmpty()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(180.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(Color(0xFF091118))
                .border(1.dp, Color(0xFF1E2E3E), RoundedCornerShape(8.dp)),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(
                    imageVector = Icons.Default.ShoppingCart,
                    contentDescription = null,
                    tint = Color(0xFF37474F),
                    modifier = Modifier.size(32.dp)
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "РЮКЗАК ПУСТ // СЕКТОР ЧИСТ",
                    color = Color(0xFF78909C),
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    } else {
        LazyVerticalGrid(
            columns = GridCells.Fixed(4),
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(inventory, key = { it.id }) { item ->
                val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                val rarity = itemMeta?.rarity ?: getItemRarity(item.item_id)
                val isEquipped = item.is_equipped

                val rarityColor = when (rarity) {
                    "cursed", "relic" -> EidosRed
                    "legendary" -> EidosOrange
                    "epic" -> EidosPurple
                    "rare" -> EidosCyan
                    "uncommon" -> EidosNeon
                    else -> Color(0xFF546E7A)
                }

                Box(
                    modifier = Modifier
                        .aspectRatio(1f)
                        .clip(RoundedCornerShape(6.dp))
                        .background(Color(0xFF0A121C))
                        .border(
                            1.dp,
                            if (isEquipped) EidosNeon else rarityColor.copy(alpha = 0.5f),
                            RoundedCornerShape(6.dp)
                        )
                        .cyberHudBorder(
                            color = if (isEquipped) EidosNeon else rarityColor.copy(alpha = 0.7f),
                            cornerLength = 5.dp,
                            strokeWidth = 1.dp
                        )
                        .cyberClickable { onItemClick(item) }
                        .padding(4.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        EidosImage(
                            resName = item.item_id,
                            borderColor = if (isEquipped) EidosNeon else rarityColor,
                            modifier = Modifier.size(28.dp)
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            itemMeta?.name ?: getItemName(item.item_id),
                            fontSize = 7.sp,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Center,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            fontFamily = FontFamily.Monospace
                        )
                        if (item.quantity > 1) {
                            Text(
                                "x${item.quantity}",
                                fontSize = 7.5.sp,
                                color = EidosCyan,
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

fun isEquippable(itemId: String, meta: com.example.eidos.data.GameRepository.ItemMetadata? = null): Boolean {
    return ItemSlotUtils.isEquippable(itemId, meta)
}

fun isConsumable(itemId: String, meta: com.example.eidos.data.GameRepository.ItemMetadata? = null): Boolean {
    return ItemSlotUtils.isConsumable(itemId, meta)
}

fun getItemType(itemId: String, meta: com.example.eidos.data.GameRepository.ItemMetadata? = null): String {
    val slot = ItemSlotUtils.getSlotForItem(itemId, meta)
    if (slot != null) return slot
    if (isConsumable(itemId, meta)) return "consumable"
    return "material"
}

fun getItemDescription(itemId: String): String {
    return when(itemId) {
        "rusty_knife" -> "Кусок заточенного цифрового лома. Навевает грусть."
        "crowbar" -> "Увесистая железка, способная взломать не только замок, но и череп глитч-моба."
        "data_bat" -> "Бита с нанесенными на нее секторами сырых данных."
        "shock_baton" -> "Подарок от полиции Мыслей. Бьет током и кодами ошибок."
        "cyber_katana" -> "Мономолекулярный клинок, мерцающий неоновым светом."
        "laser_pistol" -> "Высокочастотный лазер, прожигающий файрволы монстров."
        "plasma_rifle" -> "Выпускает сгустки перегретой плазмы, дестабилизируя код врага."
        "nano_blade" -> "Управляемая роем нано-машин сталь, меняющая форму на лету."
        "void_cannon" -> "Ручной ускоритель темной материи. Аннигилирует системные ошибки."
        "singularity_sword" -> "Выкован в эпицентре Ядра. Схлопывает вражеские сигналы в точку."
        "nomad_goggles" -> "Улучшают восприятие глитч-сигналов. +5% к шансу найти лут."
        "scavenger_mask" -> "Защищает от ядовитых испарений сырых данных. Снижает урон от ловушек."
        "tactical_helmet" -> "Тактический шлем с авто-прицелом. +10% шанс уклонения."
        "vampire_visor" -> "Преобразует код поверженных врагов в энергию. Восстанавливает 5% HP при убийстве."
        "cyber_halo" -> "Священный символ кибер-молитв. Дает 20% шанс воскреснуть при смерти."
        "overclock_crown" -> "Удваивает критический шанс, но критические атаки стоят 2% HP."
        "void_walker_hood" -> "Искажает пространство вокруг владельца. 25% шанс пройти шаг без затрат энергии."
        "architect_mask" -> "Часть шлема создателей системы. Возвращает 30% полученного урона атакующему."
        "relic_vampire" -> "Реликвия Сезона. Восстанавливает 2% HP при каждом ударе."
        "relic_speed" -> "Реликвия Сезона. Каждый шаг переносит вас на 2 метра глубже."
        "hoodie" -> "Стандартная одежда жителей Свалки Данных."
        "leather_jacket" -> "Стильная кожаная куртка с кевларовыми вставками."
        "kevlar_vest" -> "Тяжелая защита, списанная со складов корпораций."
        "tactical_suit" -> "Легкий бронекостюм с сервоприводами."
        "exo_skeleton" -> "Промышленный экзоскелет, адаптированный под боевые задачи."
        "nano_suit" -> "Высокотехнологичный костюм из нано-волокон."
        "phantom_cloak" -> "Ткань, поглощающая свет и тепло. Значительно повышает удачу."
        "force_field" -> "Портативный силовой щит, окружающий оператора непроницаемым куполом."
        "reality_armor" -> "Древние плиты, стабилизирующие квантовое состояние носителя."
        "quantum_shield" -> "Экспериментальная защита корпоративных Лордов. Выдерживает любые перегрузки."
        "medkit" -> "Нано-аптечка, быстро восстанавливающая физические повреждения (+50 HP)."
        "energy_cell" -> "Стандартная энергоячейка для подзарядки нейросети (+50 Энергии)."
        "master_key" -> "Высокочастотный дешифратор для открытия стандартных сейфов в рейде."
        "abyssal_key" -> "Используется для открытия проклятых красных сундуков в глубоких секторах."
        "battery" -> "Восстанавливает 30 ед. Энергии и 30 ед. HP."
        "neural_stimulator" -> "Экстренно восстанавливает 60 ед. HP."
        "aegis" -> "Защитный барьер, автоматически спасающий от гибели в рейде (сгорает при срабатывании)."
        "admin_key" -> "Уникальный ключ доступа, позволяющий бесплатно изменить фракцию."
        "eidos_shard" -> "Фрагмент чистого Эйдоса. Используется для ковки и ремонта снаряжения."
        "wasteland_compass", "compass" -> "Древний навигационный прибор. Сканирует вектор движения в пустоши."
        "emp_charge", "emp_grenade" -> "Электромагнитный импульсный заряд. Оглушает вражеских дронов."
        "crypto_fog", "stealth_spray" -> "Защитное маскировочное облако. Позволяет скрыться от аномалий."
        "memory_eraser", "memory_wiper" -> "Устройство форматирования памяти. Сбрасывает агрессию искинов."
        "data_spike" -> "Боевой инжектор вредоносного кода для мгновенного взлома."
        "tactical_scanner", "scanner" -> "Сканер ближнего радиуса. Подсвечивает ценные ресурсы в рейде."
        "cryo_capsule" -> "Замораживающий модуль стазиса. Приостанавливает критические процессы."
        "sync_booster", "sync_accelerator" -> "Ускоритель синхронизации. Мгновенно повышает стабильность канала."
        "purge_sync", "cleanse_sync" -> "Протокол очистки канала. Снимает негативные цифровые эффекты."
        "ram_chip" -> "Базовый модуль памяти. Оптимизирует обработку данных в нейросети."
        "cpu_booster" -> "Акселератор процессора. Повышает тактовую частоту вычислений."
        "glitch_filter" -> "Фильтр системных аномалий. Подавляет посторонние шумы в подсети."
        "ai_core" -> "Автономный мыслительный блок. Помогает прогнозировать вектор атак."
        "overclocker" -> "Экстремальный разгон систем. Ощутимо увеличивает урон ценой нагрузок."
        "backup_drive" -> "Резервное хранилище софта. Предотвращает критические сбои системы."
        "neural_link" -> "Высокоскоростной мост связи с нейросетью."
        "chronometer" -> "Квантовый хронометр. Локально замедляет энтропию в рейде."
        "logic_gate" -> "Высшая логическая схема. Просчитывает уязвимости защиты искинов."
        "god_mode_chip" -> "Легендарный чип с протоколом высшего приоритета доступа."
        "credit_slicer" -> "ПРОКЛЯТЫЙ: Списывает 1% BC за атаку, конвертируя их в огромный урон."
        "banhammer_shard" -> "ПРОКЛЯТЫЙ: Дает 1% шанс мгновенно аннигилировать врага (999 999 урона)."
        "grandfather_paradox" -> "ПРОКЛЯТЫЙ: Накапливает урон первые 3 хода. На 4-й урон сгорает, если враг мертв."
        "empath_whip" -> "ПРОКЛЯТЫЙ: Наносит урон, равный Атаке Врага * 1.5."
        "cache_wiper" -> "ПРОКЛЯТЫЙ: Наносит колоссальный урон, но стирает лут из побежденных врагов."
        "error_404_mirror" -> "ПРОКЛЯТЫЙ: Дает 50% шанс отразить полученный урон обратно во врага."
        "judas_shell" -> "ПРОКЛЯТЫЙ: Дает +150 защиты, но снижает защиту от ловушек до 0."
        "holo_poverty" -> "ПРОКЛЯТЫЙ: Позволяет сбежать из любого боя с вероятностью 95%."
        "schrodinger_armor" -> "ПРОКЛЯТЫЙ: Случайным образом меняет защиту каждый ход (от -50 до +200)."
        "thermonuclear_shroud" -> "ПРОКЛЯТЫЙ: При гибели аннигилирует врага, сохраняя 1% HP, но сжигает накопленный лут."
        "blood_miner" -> "ПРОКЛЯТЫЙ: Каждый шаг дает +50 BC, но отнимает 2% Сигнала."
        "karma_inversion" -> "ПРОКЛЯТЫЙ: Ловушки лечат вас, а лечение наносит чистый урон."
        "oblivion_chip" -> "ПРОКЛЯТЫЙ: Дает +100% опыта, но скрывает показатель Сигнала в рейде."
        "imposter_syndrome" -> "ПРОКЛЯТЫЙ: Копирует параметры сильнейшего Искина в текущем секторе."
        "kamikaze_protocol" -> "ПРОКЛЯТЫЙ: Дает +500 атаки, но если не эвакуироваться за 10 шагов, вы теряете уровень."
        "architect_eye" -> "ПРОКЛЯТЫЙ: Подсвечивает тип события впереди, но удваивает затраты энергии."
        "corrupted_data_cluster" -> "Глитч-объект. Можно запустить процесс расшифровки в инвентаре, либо обойти защиту мгновенно за 500 BioCoin, чтобы извлечь редкий софт или ключи."
        else -> "Секретный технологический артефакт Бездны."
    }
}

