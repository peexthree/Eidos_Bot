package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.*
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
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
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.ItemSlotUtils
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosGold
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosOrange
import io.eidos.zerolayer.ui.theme.EidosPurple
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.neonGlowPulse
import io.eidos.zerolayer.ui.components.EidosImage
import io.eidos.zerolayer.ui.components.cyberClickable
import io.eidos.zerolayer.ui.components.cyberHudBorder
import io.eidos.zerolayer.ui.components.EidosStatBar

import io.eidos.zerolayer.data.RaidSession

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InventoryScreen(
    player: Player?,
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    activeRaidSession: RaidSession? = null,
    onReturnToRaid: (() -> Unit)? = null,
    onEvacuateRaid: (() -> Unit)? = null,
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
            // Layer 0: Safe Background with solid fallback
            val bgPainter = runCatching {
                androidx.compose.ui.res.painterResource(id = io.eidos.zerolayer.R.drawable.bg_inventory)
            }.getOrNull()

            if (bgPainter != null) {
                androidx.compose.foundation.Image(
                    painter = bgPainter,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                    alignment = androidx.compose.ui.Alignment.Center
                )
            }
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
                // Interactive Equipment Doll
                Text(
                    "АКТИВНАЯ ЭКИПИРОВКА [СЛОТЫ ЯДРА]",
                    color = EidosCyan,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.5.sp,
                    modifier = Modifier.padding(bottom = 6.dp)
                )
                EquipDollSection(inventory, allItemsMetadata, player, activeStats, onUnequip)

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

                // Item Grid Section with Crossfade animation
                Crossfade(targetState = selectedCategory, animationSpec = tween(220), label = "catCrossfade") { currentCat ->
                    val filteredInventory = remember(inventory, allItemsMetadata, currentCat) {
                        inventory.filter { item ->
                            val itemMeta = allItemsMetadata.find { it.id == item.item_id }
                            val slot = ItemSlotUtils.getSlotForItem(item.item_id, itemMeta)
                            when (currentCat) {
                                "all" -> true
                                "weapon" -> slot == "weapon"
                                "armor" -> slot == "armor" || slot == "head"
                                "chip" -> slot == "chip"
                                "consumable" -> isConsumable(item.item_id, itemMeta)
                                else -> true
                            }
                        }
                    }

                    ItemListSection(filteredInventory, allItemsMetadata) { item ->
                        selectedItem = item
                    }
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
                    // Full-width Large Showcase Art Banner (260.dp)
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(260.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF05080E))
                            .border(1.dp, rarityColor.copy(alpha = 0.6f), RoundedCornerShape(8.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        EidosImage(
                            resName = item.item_id,
                            borderColor = Color.Transparent,
                            borderWidth = 0.dp,
                            contentScale = androidx.compose.ui.layout.ContentScale.Fit,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(12.dp)
                        )

                        // Dark gradient overlay at bottom
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(80.dp)
                                .align(Alignment.BottomCenter)
                                .background(
                                    Brush.verticalGradient(
                                        colors = listOf(Color.Transparent, Color(0xFF090F16).copy(alpha = 0.95f))
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
                            progress = { item.durability.toFloat() / 100f },
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
                        val isChip = (item.slot == "chip" || ItemSlotUtils.getSlotForItem(item.item_id, itemMeta) == "chip")
                        val isChipAlreadyEquipped = isChip && inventory.any { it.is_equipped && it.item_id == item.item_id && it.id != item.id }
                        val canEquip = (player == null || player.level >= reqLevel) && !isChipAlreadyEquipped
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
                                    when {
                                        isChipAlreadyEquipped -> "ЧИП УЖЕ УСТАНОВЛЕН"
                                        !canEquip -> "ТРЕБУЕТСЯ LVL $reqLevel"
                                        else -> "ЭКИПИРОВАТЬ"
                                    },
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

            // Operator Stat Bars
            val curHp = player?.hp ?: 100
            val maxHp = maxOf(1, player?.max_hp ?: 100)
            val curEnergy = player?.energy ?: 100
            val maxEnergy = maxOf(1, player?.max_energy ?: 100)

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                EidosStatBar(
                    label = "HP ОПЕРАТОРА",
                    value = curHp,
                    maxValue = maxHp,
                    color = if (curHp < maxHp * 0.3) EidosRed else EidosNeon,
                    modifier = Modifier.weight(1f)
                )
                EidosStatBar(
                    label = "ЭНЕРГИЯ EP",
                    value = curEnergy,
                    maxValue = maxEnergy,
                    color = EidosCyan,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    val bcPainter = runCatching { painterResource(id = R.drawable.ic_biocoin) }.getOrNull()
                    if (bcPainter != null) {
                        Image(
                            painter = bcPainter,
                            contentDescription = "BioCoins",
                            modifier = Modifier.size(14.dp),
                            contentScale = ContentScale.Fit
                        )
                    } else {
                        Text("🪙", fontSize = 11.sp)
                    }
                    Text(
                        "${player?.biocoin ?: 0} BC",
                        color = EidosGold,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Text(
                    "ФРАКЦИЯ: ${player?.faction ?: "НЕОФИТ"}",
                    color = EidosCyan,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    "XP: ${player?.xp ?: 0}",
                    color = EidosNeon,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}

@Composable
fun OperatorEquipmentDeck(
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    player: Player? = null,
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    onUnequip: (InventoryItem) -> Unit
) = EquipDollSection(inventory, allItemsMetadata, player, activeStats, onUnequip)

@Composable
fun EquipDollSection(
    inventory: List<InventoryItem>,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
    player: Player? = null,
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats? = null,
    onUnequip: (InventoryItem) -> Unit
) {
    val head = inventory.find { it.is_equipped && (it.slot == "head" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "head") }
    val armor = inventory.find { it.is_equipped && (it.slot == "armor" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "armor") }
    val weapon = inventory.find { it.is_equipped && (it.slot == "weapon" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "weapon") }
    val chips = inventory.filter { it.is_equipped && (it.slot == "chip" || ItemSlotUtils.getSlotForItem(it.item_id, allItemsMetadata.find { meta -> meta.id == it.item_id }) == "chip") }
        .distinctBy { it.item_id }
        .take(4)

    val playerLvl = (player?.level ?: 1).coerceIn(1, 31)
    val avatarRes = "lvl_$playerLvl"

    val currentAtk = activeStats?.attack ?: player?.attack ?: 10
    val currentDef = activeStats?.defense ?: player?.defense ?: 5
    val currentLuck = activeStats?.luck ?: player?.luck ?: 5

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF060B11).copy(alpha = 0.95f))
            .border(1.dp, EidosCyan.copy(alpha = 0.35f), CutCornerShape(8.dp))
            .padding(8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // LEFT COLUMN: Head, Weapon, Armor (74.dp large tiles)
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                EquipSlotTile(
                    slotLabel = "ШЛЕМ",
                    item = head,
                    meta = head?.let { allItemsMetadata.find { meta -> meta.id == it.item_id } },
                    defaultAccent = EidosCyan,
                    onUnequip = onUnequip
                )
                EquipSlotTile(
                    slotLabel = "ОРУЖИЕ",
                    item = weapon,
                    meta = weapon?.let { allItemsMetadata.find { meta -> meta.id == it.item_id } },
                    defaultAccent = Color(0xFFFF9800),
                    onUnequip = onUnequip
                )
                EquipSlotTile(
                    slotLabel = "БРОНЯ",
                    item = armor,
                    meta = armor?.let { allItemsMetadata.find { meta -> meta.id == it.item_id } },
                    defaultAccent = EidosPurple,
                    onUnequip = onUnequip
                )
            }

            // CENTER: LARGE 265.dp CYBER OPERATOR ART RIG
            Box(
                modifier = Modifier
                    .weight(1.3f)
                    .height(265.dp)
                    .clip(CutCornerShape(8.dp))
                    .background(Color(0xFF091219))
                    .border(1.5.dp, EidosCyan.copy(alpha = 0.6f), CutCornerShape(8.dp)),
                contentAlignment = Alignment.Center
            ) {
                EidosImage(
                    resName = avatarRes,
                    fallbackIcon = Icons.Default.Person,
                    borderColor = Color.Transparent,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(top = 18.dp, bottom = 44.dp)
                )

                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(
                                    Color.Transparent,
                                    Color(0xFF001F2D).copy(alpha = 0.15f),
                                    Color(0xFF000910).copy(alpha = 0.85f)
                                )
                            )
                        )
                )

                Box(
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .fillMaxWidth()
                        .background(Color.Black.copy(alpha = 0.75f))
                        .border(0.5.dp, EidosCyan.copy(alpha = 0.5f))
                        .padding(vertical = 3.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "⚡ ОПЕРАТОР [УР $playerLvl]",
                        color = EidosCyan,
                        fontSize = 8.5.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .background(Color.Black.copy(alpha = 0.85f))
                        .border(0.5.dp, EidosCyan.copy(alpha = 0.5f))
                        .padding(vertical = 4.dp, horizontal = 4.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = player?.username ?: "НЕОФИТ",
                        color = Color.White,
                        fontSize = 9.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text("⚔️ ", fontSize = 8.sp)
                        AnimatedContent(targetState = currentAtk, label = "atkAnim") { atk ->
                            Text("$atk ATK", color = EidosNeon, fontSize = 8.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        }
                        Text(" | 🛡️ ", fontSize = 8.sp)
                        AnimatedContent(targetState = currentDef, label = "defAnim") { def ->
                            Text("$def DEF", color = EidosCyan, fontSize = 8.5.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        }
                    }
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text("🍀 УДАЧА: ", color = Color(0xFFFFD54F), fontSize = 7.5.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                        AnimatedContent(targetState = currentLuck, label = "luckAnim") { luck ->
                            Text("$luck", color = Color(0xFFFFD54F), fontSize = 8.sp, fontWeight = FontWeight.Black, fontFamily = FontFamily.Monospace)
                        }
                    }
                }
            }

            // RIGHT COLUMN: 4 Mod Chips (58.dp tiles)
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                for (i in 0..3) {
                    val chip = chips.getOrNull(i)
                    EquipSlotTile(
                        slotLabel = "ЧИП ${i + 1}",
                        item = chip,
                        meta = chip?.let { allItemsMetadata.find { meta -> meta.id == it.item_id } },
                        defaultAccent = EidosNeon,
                        isCompact = true,
                        onUnequip = onUnequip
                    )
                }
            }
        }
    }
}

@Composable
private fun EquipSlotTile(
    slotLabel: String,
    item: InventoryItem?,
    meta: io.eidos.zerolayer.data.GameRepository.ItemMetadata?,
    defaultAccent: Color,
    isCompact: Boolean = false,
    onUnequip: (InventoryItem) -> Unit
) {
    val rarity = meta?.rarity ?: (item?.let { getItemRarity(it.item_id) } ?: "common")
    val rarityColor = when (rarity) {
        "cursed", "relic" -> EidosRed
        "legendary" -> EidosOrange
        "epic" -> EidosPurple
        "rare" -> EidosCyan
        "uncommon" -> EidosNeon
        else -> defaultAccent
    }

    val tileHeight = if (isCompact) 58.dp else 74.dp
    val iconSize = if (isCompact) 40.dp else 48.dp

    val itemScale by animateFloatAsState(
        targetValue = if (item != null) 1f else 0.85f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "slotScale"
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(tileHeight)
            .clip(CutCornerShape(4.dp))
            .background(if (item != null) Color(0xFF0B141D) else Color(0xFF070B10))
            .border(
                width = 1.dp,
                color = if (item != null) rarityColor.copy(alpha = 0.85f) else Color(0xFF1E2D3D),
                shape = CutCornerShape(4.dp)
            )
            .cyberClickable(enabled = item != null) { item?.let { onUnequip(it) } }
            .padding(horizontal = 4.dp, vertical = 2.dp),
        contentAlignment = Alignment.CenterStart
    ) {
        if (item != null) {
            Row(
                modifier = Modifier.fillMaxSize(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(iconSize)
                        .clip(CutCornerShape(4.dp))
                        .background(Color.Black.copy(alpha = 0.5f))
                        .border(1.dp, rarityColor, CutCornerShape(4.dp))
                        .graphicsLayer {
                            scaleX = itemScale
                            scaleY = itemScale
                        },
                    contentAlignment = Alignment.Center
                ) {
                    EidosImage(
                        resName = item.item_id,
                        borderColor = Color.Transparent,
                        borderWidth = 0.dp,
                        contentScale = ContentScale.Fit,
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(2.dp)
                    )
                }

                Spacer(modifier = Modifier.width(6.dp))

                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(
                        slotLabel,
                        color = rarityColor,
                        fontSize = 7.5.sp,
                        fontWeight = FontWeight.Black,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        meta?.name ?: getItemName(item.item_id),
                        color = Color.White,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        } else {
            Row(
                modifier = Modifier.fillMaxSize(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(iconSize)
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0xFF0F1722))
                        .border(1.dp, Color(0xFF1E2D3D), CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("+", color = Color(0xFF455A64), fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(modifier = Modifier.width(6.dp))
                Column {
                    Text(
                        slotLabel,
                        color = defaultAccent.copy(alpha = 0.6f),
                        fontSize = 7.5.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        "ПУСТО",
                        color = Color(0xFF546E7A),
                        fontSize = 8.5.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

@Composable
fun EquipSlot(
    label: String,
    item: InventoryItem?,
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
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
    allItemsMetadata: List<io.eidos.zerolayer.data.GameRepository.ItemMetadata> = emptyList(),
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
            columns = GridCells.Fixed(2),
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
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
                        .fillMaxWidth()
                        .height(180.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF0A121C))
                        .border(
                            1.dp,
                            if (isEquipped) EidosNeon else rarityColor.copy(alpha = 0.6f),
                            RoundedCornerShape(8.dp)
                        )
                        .cyberHudBorder(
                            color = if (isEquipped) EidosNeon else rarityColor.copy(alpha = 0.8f),
                            cornerLength = 8.dp,
                            strokeWidth = 1.5.dp
                        )
                        .cyberClickable { onItemClick(item) }
                        .padding(8.dp)
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.SpaceBetween
                    ) {
                        // Large 98.dp Art Container with ContentScale.Fit
                        Box(
                            modifier = Modifier
                                .size(98.dp)
                                .clip(RoundedCornerShape(6.dp))
                                .background(Color(0xFF05090F))
                                .border(1.dp, rarityColor.copy(alpha = 0.45f), RoundedCornerShape(6.dp))
                                .padding(4.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            EidosImage(
                                resName = item.item_id,
                                borderColor = Color.Transparent,
                                borderWidth = 0.dp,
                                contentScale = ContentScale.Fit,
                                modifier = Modifier.fillMaxSize()
                            )

                            if (isEquipped) {
                                Box(
                                    modifier = Modifier
                                        .align(Alignment.TopEnd)
                                        .background(EidosNeon, RoundedCornerShape(3.dp))
                                        .padding(horizontal = 5.dp, vertical = 2.dp)
                                ) {
                                    Text(
                                        "НАДЕТО",
                                        fontSize = 7.sp,
                                        color = Color.Black,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }

                        // Bottom Title & Status
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                itemMeta?.name ?: getItemName(item.item_id),
                                fontSize = 9.5.sp,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                textAlign = TextAlign.Center,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    rarity.uppercase(),
                                    fontSize = 7.5.sp,
                                    color = rarityColor,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                if (item.quantity > 1) {
                                    Text(
                                        "x${item.quantity}",
                                        fontSize = 8.5.sp,
                                        color = EidosCyan,
                                        fontWeight = FontWeight.Black,
                                        fontFamily = FontFamily.Monospace
                                    )
                                } else if (item.durability >= 0 && isEquippable(item.item_id, itemMeta)) {
                                    Text(
                                        "${item.durability.toInt()}%",
                                        fontSize = 7.5.sp,
                                        color = if (item.durability < 30) EidosRed else EidosNeon,
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

fun isEquippable(itemId: String, meta: io.eidos.zerolayer.data.GameRepository.ItemMetadata? = null): Boolean {
    return ItemSlotUtils.isEquippable(itemId, meta)
}

fun isConsumable(itemId: String, meta: io.eidos.zerolayer.data.GameRepository.ItemMetadata? = null): Boolean {
    return ItemSlotUtils.isConsumable(itemId, meta)
}

fun getItemType(itemId: String, meta: io.eidos.zerolayer.data.GameRepository.ItemMetadata? = null): String {
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

