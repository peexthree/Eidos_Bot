package io.eidos.zerolayer.ui.components

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.util.lerp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import io.eidos.zerolayer.data.*
import io.eidos.zerolayer.ui.theme.*
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import kotlinx.coroutines.delay

@Composable
fun CyberToastHost(
    toasts: List<CyberToast>,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier.fillMaxSize().padding(16.dp), contentAlignment = Alignment.BottomCenter) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            toasts.forEach { toast ->
                CyberToastItem(toast)
            }
        }
    }
}

@Composable
fun CyberToastItem(toast: CyberToast) {
    val color = when (toast.type) {
        CyberToastType.INFO -> EidosCyan
        CyberToastType.SUCCESS -> EidosNeon
        CyberToastType.ALERT, CyberToastType.DANGER -> EidosRed
    }

    Surface(
        color = Color.Black.copy(alpha = 0.9f),
        shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, color),
        modifier = Modifier
            .fillMaxWidth()
            .shadow(10.dp, ambientColor = color, spotColor = color)
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            val icon = when (toast.type) {
                CyberToastType.INFO -> "ℹ️"
                CyberToastType.SUCCESS -> "✅"
                CyberToastType.ALERT -> "⚠️"
                CyberToastType.DANGER -> "☠️"
            }
            Text(icon, fontSize = 18.sp, modifier = Modifier.padding(end = 12.dp))
            Text(
                text = toast.message.uppercase(),
                color = color,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
fun AchievementPopup(
    achievement: Achievement,
    onClaim: () -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    LaunchedEffect(achievement.id) {
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
            .shadow(24.dp, spotColor = Color(0xFFFFD700)),
        color = Color(0xFF141414),
        shape = CutCornerShape(8.dp),
        border = androidx.compose.foundation.BorderStroke(2.dp, Brush.linearGradient(listOf(Color(0xFFFFD700), Color(0xFFFF0055))))
    ) {
        Column(
            modifier = Modifier
                .padding(14.dp)
                .fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(Color(0xFFFFD700).copy(alpha = 0.2f), RoundedCornerShape(8.dp))
                        .border(1.dp, Color(0xFFFFD700), RoundedCornerShape(8.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(achievement.icon, fontSize = 24.sp)
                }

                Spacer(modifier = Modifier.width(12.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        "${achievement.category.uppercase()} // ДОСТИЖЕНИЕ ПОЛУЧЕНО",
                        color = Color(0xFFFFD700),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        achievement.title.uppercase(),
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        achievement.description,
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        lineHeight = 14.sp
                    )
                }

                IconButton(onClick = onDismiss) {
                    Text("✕", color = Color.Gray, fontSize = 14.sp)
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    color = Color(0xFFFFD700).copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700)),
                    shape = RoundedCornerShape(4.dp)
                ) {
                    Text(
                        text = "НАГРАДА: +${achievement.xpReward} XP",
                        color = Color(0xFFFFD700),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }

                Button(
                    onClick = onClaim,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF0055)),
                    shape = CutCornerShape(4.dp),
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp)
                ) {
                    Text(
                        "⚡️ ЗАБРАТЬ НАГРАДУ",
                        color = Color.White,
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
fun AchievementClaimDialog(
    achievement: Achievement,
    onClaim: () -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }

    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val borderAlpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    LaunchedEffect(achievement.id) {
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(dismissOnBackPress = true, dismissOnClickOutside = false)
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp)
                .shadow(32.dp, spotColor = Color(0xFFFF0055)),
            color = Color(0xFF0F0F14),
            shape = CutCornerShape(12.dp),
            border = androidx.compose.foundation.BorderStroke(
                2.dp,
                Brush.linearGradient(
                    listOf(
                        Color(0xFFFFD700).copy(alpha = borderAlpha),
                        Color(0xFFFF0055).copy(alpha = borderAlpha),
                        Color(0xFF8A2BE2).copy(alpha = borderAlpha)
                    )
                )
            )
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header tag
                Surface(
                    color = Color(0xFFFFD700).copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700)),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        text = "🏆 НОВОЕ ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО",
                        color = Color(0xFFFFD700),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Icon box
                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .background(
                            Brush.radialGradient(
                                listOf(
                                    Color(0xFFFF0055).copy(alpha = 0.35f),
                                    Color.Transparent
                                )
                            ),
                            RoundedCornerShape(36.dp)
                        )
                        .border(2.dp, Color(0xFFFFD700), RoundedCornerShape(36.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(achievement.icon, fontSize = 36.sp)
                }

                Spacer(modifier = Modifier.height(14.dp))

                Text(
                    text = achievement.title.uppercase(),
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center
                )

                Text(
                    text = achievement.category,
                    color = Color(0xFF8A2BE2),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(top = 2.dp)
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = achievement.description,
                    color = Color.LightGray,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                    lineHeight = 16.sp,
                    modifier = Modifier.padding(horizontal = 8.dp)
                )

                Spacer(modifier = Modifier.height(18.dp))

                // Reward Card
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = Color(0xFF1A1A24),
                    shape = RoundedCornerShape(8.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700).copy(alpha = 0.4f))
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "НАГРАДА:",
                            color = Color.Gray,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "+${achievement.xpReward} XP",
                            color = Color(0xFFFFD700),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Primary Claim Button
                Button(
                    onClick = onClaim,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFFFF0055)
                    ),
                    shape = CutCornerShape(6.dp)
                ) {
                    Text(
                        "⚡️ ЗАБРАТЬ НАГРАДУ (+${achievement.xpReward} XP)",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        letterSpacing = 1.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                TextButton(onClick = onDismiss) {
                    Text("Забрать позже в Профиле", color = Color.Gray, fontSize = 11.sp)
                }
            }
        }
    }
}

@Composable
fun LootDropDialog(
    loot: LootDrop,
    allItemsMetadata: List<GameRepository.ItemMetadata>,
    onClaim: () -> Unit
) {
    val context = LocalContext.current
    val haptics = remember { HapticFeedbackManager.getInstance(context) }
    val audio = remember { EidosAudioManager.getInstance(context) }
    
    Dialog(
        onDismissRequest = { },
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.85f))
                .clickable(enabled = false) { }
        ) {
            CyberParticleOverlay(modifier = Modifier.fillMaxSize(), preset = ParticlePreset.FORGE_SPARKS)
            
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    loot.source.uppercase(),
                    color = EidosCyan,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp
                )
                Text(
                    "ИЗВЛЕЧЕНИЕ ДАННЫХ",
                    color = Color.White,
                    fontSize = 28.sp,
                    fontWeight = FontWeight.ExtraBold,
                    textAlign = TextAlign.Center
                )
                
                Spacer(modifier = Modifier.height(32.dp))
                
                LazyColumn(
                    modifier = Modifier.weight(1f, fill = false),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    items(loot.items.size) { index ->
                        var visible by remember { mutableStateOf(false) }
                        LaunchedEffect(Unit) {
                            delay(index * 300L)
                            visible = true
                            haptics.click()
                        }
                        
                        AnimatedVisibility(
                            visible = visible,
                            enter = fadeIn() + expandVertically() + scaleIn()
                        ) {
                            LootItemCard(loot.items[index], allItemsMetadata)
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(40.dp))
                
                Button(
                    onClick = {
                        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                        onClaim()
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp)
                        .shadow(15.dp, spotColor = EidosNeon),
                    colors = ButtonDefaults.buttonColors(containerColor = EidosNeon),
                    shape = CutCornerShape(8.dp)
                ) {
                    Text(
                        "ЗАБРАТЬ В ИНВЕНТАРЬ",
                        color = Color.Black,
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 16.sp
                    )
                }
            }
        }
    }
}

@Composable
fun LootItemCard(item: InventoryItem, allItemsMetadata: List<GameRepository.ItemMetadata>) {
    val meta = allItemsMetadata.find { it.id == item.item_id } ?: GameRepository.ItemMetadata(item.item_id, "Unknown", "misc", "common")
    val rarityColor = when (meta.rarity.lowercase()) {
        "common" -> Color.Gray
        "rare" -> EidosCyan
        "legendary" -> Color(0xFFFFB300)
        "relic" -> Color(0xFFAA00FF)
        else -> Color.White
    }
    
    val isCritical = meta.rarity.lowercase() in listOf("legendary", "relic")
    
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(90.dp)
            .clip(CutCornerShape(8.dp))
            .background(Color(0xFF121212))
            .border(2.dp, rarityColor.copy(alpha = 0.6f), CutCornerShape(8.dp))
            .padding(12.dp)
    ) {
        if (isCritical) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .border(1.dp, rarityColor.copy(alpha = 0.3f), CutCornerShape(8.dp))
                    .background(
                        Brush.radialGradient(
                            listOf(rarityColor.copy(alpha = 0.1f), Color.Transparent),
                            radius = 300f
                        )
                    )
            )
        }
        
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .background(rarityColor.copy(alpha = 0.1f), RoundedCornerShape(8.dp))
                    .border(1.dp, rarityColor, RoundedCornerShape(8.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(meta.icon, fontSize = 32.sp)
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        meta.name.uppercase(),
                        color = Color.White,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                    if (isCritical) {
                        Spacer(modifier = Modifier.width(8.dp))
                        Surface(
                            color = rarityColor,
                            shape = RoundedCornerShape(4.dp)
                        ) {
                            Text(
                                "КРИТИЧЕСКИЙ ДРОП",
                                color = Color.Black,
                                fontSize = 8.sp,
                                fontWeight = FontWeight.Black,
                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                            )
                        }
                    }
                }
                Text(
                    meta.rarity.uppercase(),
                    color = rarityColor,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    meta.description,
                    color = Color.Gray,
                    fontSize = 10.sp,
                    maxLines = 1
                )
            }
        }
    }
}

@Composable
fun LevelUpModalDialog(
    event: LevelUpEvent,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    val haptics = remember { HapticFeedbackManager.getInstance(context) }

    LaunchedEffect(event.toLevel) {
        audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
        haptics.lootLegendary()
    }

    val infiniteTransition = rememberInfiniteTransition(label = "levelup_infinite")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.95f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )

    val rotationAnim by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(12000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "rotation"
    )

    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glow"
    )

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            dismissOnBackPress = false,
            dismissOnClickOutside = false,
            usePlatformDefaultWidth = false
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.88f))
                .clickable(onClick = {}),
            contentAlignment = Alignment.Center
        ) {
            // Rotating Cosmic Aura / Starburst
            Canvas(
                modifier = Modifier
                    .size(340.dp)
                    .graphicsLayer { rotationZ = rotationAnim }
            ) {
                val center = Offset(size.width / 2f, size.height / 2f)
                val rayCount = 16
                val rayLength = size.width / 2f
                for (i in 0 until rayCount) {
                    val angle = (i * (360f / rayCount)) * (Math.PI / 180f).toFloat()
                    val end = Offset(
                        center.x + kotlin.math.cos(angle) * rayLength,
                        center.y + kotlin.math.sin(angle) * rayLength
                    )
                    drawLine(
                        brush = Brush.linearGradient(
                            listOf(Color(0xFFFFD700).copy(alpha = glowAlpha * 0.4f), Color(0xFFFF0055).copy(alpha = 0f)),
                            start = center,
                            end = end
                        ),
                        start = center,
                        end = end,
                        strokeWidth = 6.dp.toPx()
                    )
                }
            }

            // Main Level Up Card
            Card(
                modifier = Modifier
                    .fillMaxWidth(0.92f)
                    .wrapContentHeight()
                    .graphicsLayer {
                        scaleX = pulseScale
                        scaleY = pulseScale
                    }
                    .shadow(30.dp, ambientColor = Color(0xFFFFD700), spotColor = Color(0xFFFF0055)),
                shape = CutCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF0D0D12)),
                border = androidx.compose.foundation.BorderStroke(2.dp, Brush.linearGradient(
                    listOf(Color(0xFFFFD700), Color(0xFFFF0055), EidosCyan)
                ))
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Header Tag
                    Surface(
                        color = Color(0xFFFFD700).copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700)),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            text = "⚡️ LEVEL UP COMPLETED ⚡️",
                            color = Color(0xFFFFD700),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Black,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Big Emoji & Level Transition Badge
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text(event.levelInfo.icon, fontSize = 42.sp)
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(horizontalAlignment = Alignment.Start) {
                            Text(
                                "LVL ${event.fromLevel} ➔ LVL ${event.toLevel}",
                                color = Color.White,
                                fontSize = 24.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace
                            )
                            Text(
                                "РАНГ: ${event.levelInfo.rankTitle}",
                                color = EidosCyan,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    // Character Level Artwork
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(130.dp)
                            .clip(CutCornerShape(8.dp))
                            .border(1.dp, Color(0xFFFFD700).copy(alpha = 0.5f), CutCornerShape(8.dp))
                    ) {
                        EidosImage(
                            resName = "lvl_${event.toLevel.coerceIn(1, 30)}",
                            borderColor = Color.Transparent,
                            borderWidth = 0.dp,
                            contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Slogan Box
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = Color(0xFF16161F),
                        shape = CutCornerShape(8.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.15f))
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = "${event.levelInfo.icon} LVL ${event.toLevel}: ${event.levelInfo.stageTitle}",
                                    color = Color(0xFFFFD700),
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Black,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = event.levelInfo.sloganText,
                                color = Color.LightGray,
                                fontSize = 12.sp,
                                lineHeight = 16.sp
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Unlocked Perk
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = EidosCyan.copy(alpha = 0.08f),
                        shape = CutCornerShape(6.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.4f))
                    ) {
                        Row(
                            modifier = Modifier.padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("🔓", fontSize = 20.sp, modifier = Modifier.padding(end = 10.dp))
                            Column {
                                Text(
                                    "ПЕРК: ${event.levelInfo.perkTitle.uppercase()}",
                                    color = EidosCyan,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    event.levelInfo.perkDescription,
                                    color = Color.White,
                                    fontSize = 10.sp,
                                    lineHeight = 14.sp
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Instant Level-Up Rewards
                    Text(
                        "ПОЛУЧЕННЫЕ НАГРАДЫ И УСИЛЕНИЯ:",
                        color = Color.Gray,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp)
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Surface(
                            modifier = Modifier.weight(1f),
                            color = Color(0xFFFFB300).copy(alpha = 0.15f),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFB300))
                        ) {
                            Column(
                                modifier = Modifier.padding(6.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text("🪙 +${event.levelInfo.rewardBioCoins} BC", color = Color(0xFFFFB300), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }

                        Surface(
                            modifier = Modifier.weight(1f),
                            color = EidosRed.copy(alpha = 0.15f),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed)
                        ) {
                            Column(
                                modifier = Modifier.padding(6.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text("❤️ +${event.levelInfo.bonusHp} HP", color = EidosRed, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }

                        Surface(
                            modifier = Modifier.weight(1f),
                            color = EidosNeon.copy(alpha = 0.15f),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon)
                        ) {
                            Column(
                                modifier = Modifier.padding(6.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text("⚔️ +${event.levelInfo.bonusAtk} ATK", color = EidosNeon, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }

                        if (event.levelInfo.rewardShards > 0) {
                            Surface(
                                modifier = Modifier.weight(1f),
                                color = EidosCyan.copy(alpha = 0.15f),
                                shape = CutCornerShape(4.dp),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan)
                            ) {
                                Column(
                                    modifier = Modifier.padding(6.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Text("💎 +${event.levelInfo.rewardShards}", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(18.dp))

                    // Claim Button
                    Button(
                        onClick = {
                            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                            haptics.click()
                            onDismiss()
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp)
                            .shadow(16.dp, spotColor = Color(0xFFFF0055)),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF0055)),
                        shape = CutCornerShape(6.dp)
                    ) {
                        Text(
                            "⚡️ УТВЕРДИТЬ СТАТУС ЯДРА",
                            color = Color.White,
                            fontWeight = FontWeight.Black,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
