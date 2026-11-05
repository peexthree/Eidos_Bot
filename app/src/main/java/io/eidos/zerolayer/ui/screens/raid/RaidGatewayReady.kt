package io.eidos.zerolayer.ui.screens.raid

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.R
import io.eidos.zerolayer.data.InventoryItem
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.ui.components.CyberCard
import io.eidos.zerolayer.ui.components.CyberCornerBracketBox
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.screens.getItemNameReadable
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager

/**
 * Механически извлечено из RaidScreen.kt (декомпозиция без изменения поведения).
 * Экран готовности шлюза Нулевого Слоя (когда активной сессии рейда нет).
 */
@Composable
internal fun RaidGatewayReadyContent(
    player: Player?,
    activeStats: io.eidos.zerolayer.data.GameRepository.PlayerStats?,
    inventory: List<InventoryItem>,
    innerPadding: PaddingValues,
    onStartRaid: () -> Unit,
    haptics: HapticFeedbackManager,
    audio: EidosAudioManager
) {
    // Gateway Ready State: Enter Abyss
    val playerCoins = player?.biocoin ?: 0
    val playerHp = player?.hp ?: 100
    val isLowHp = playerHp < 25
    val isEmergencyBreach = playerCoins < 20
    val equippedWeaponName = remember(inventory) {
        inventory.find { it.is_equipped && (it.slot == "weapon" || it.item_id.contains("sword") || it.item_id.contains("blade") || it.item_id.contains("knife") || it.item_id.contains("katana") || it.item_id.contains("cannon") || it.item_id.contains("rifle")) }?.item_id?.let { getItemNameReadable(it) } ?: "Импульсный излучатель"
    }

    Column(
        modifier = Modifier
            .padding(innerPadding)
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CyberCornerBracketBox(
            bracketSize = 22.dp,
            bracketColor = EidosRed,
            modifier = Modifier.fillMaxWidth()
        ) {
            CyberCard(
                modifier = Modifier.fillMaxWidth(),
                borderColor = EidosRed,
                headerText = "ШЛЮЗ НУЛЕВОГО СЛОЯ // ГОТОВНОСТЬ"
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "НЕЙРОННЫЙ КАНАЛ СТАБИЛИЗИРОВАН",
                        color = EidosRed,
                        fontWeight = FontWeight.Black,
                        fontSize = 14.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        text = "Вы находитесь на пороге Нулевого Слоя. Здесь реальность искажена, а программы-фантомы и вирусы охраняют квантовые данные. Подготовьте снаряжение и начните спуск.",
                        color = Color.LightGray,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center,
                        lineHeight = 16.sp
                    )
                    Spacer(modifier = Modifier.height(14.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ЗДОРОВЬЕ", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("${player?.hp ?: 100}/${player?.max_hp ?: 100}", color = if (isLowHp) EidosRed else EidosNeon, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("АТАКА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("${activeStats?.attack ?: player?.attack ?: 10}", color = EidosRed, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("ЗАЩИТА", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("${activeStats?.defense ?: player?.defense ?: 5}", color = EidosCyan, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(androidx.compose.foundation.shape.CutCornerShape(4.dp))
                            .background(Color(0xFF0D1520))
                            .border(0.8.dp, EidosCyan.copy(alpha = 0.4f), androidx.compose.foundation.shape.CutCornerShape(4.dp))
                            .padding(horizontal = 8.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ZzzIcon(iconRes = R.drawable.ic_action_attack, size = 12.dp, tint = EidosCyan)
                            Spacer(Modifier.width(4.dp))
                            Text("ЭКИПИРОВКА:", color = Color.Gray, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                        Text(equippedWeaponName, color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    if (isLowHp) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(androidx.compose.foundation.shape.CutCornerShape(4.dp))
                                .background(EidosRed.copy(alpha = 0.2f))
                                .border(1.dp, EidosRed.copy(alpha = 0.6f), androidx.compose.foundation.shape.CutCornerShape(4.dp))
                                .padding(horizontal = 8.dp, vertical = 6.dp)
                        ) {
                            Text(
                                "⚠️ КРИТИЧЕСКИЙ СИГНАЛ: Здоровье ниже нормы ($playerHp HP). Рекомендуется стабилизировать сигнал в Хабе перед спуском!",
                                color = EidosRed,
                                fontSize = 9.5.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                    }

                    if (isEmergencyBreach) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(androidx.compose.foundation.shape.CutCornerShape(4.dp))
                                .background(EidosCyan.copy(alpha = 0.15f))
                                .border(1.dp, EidosCyan.copy(alpha = 0.6f), androidx.compose.foundation.shape.CutCornerShape(4.dp))
                                .padding(horizontal = 8.dp, vertical = 6.dp)
                        ) {
                            Text(
                                "⚡ ЭКСТРЕННЫЙ ПРОРЫВ: Баланс $playerCoins BC. ИИ ЕВА-09 санкционировала бесплатный аварийный доступ в Бездну.",
                                color = EidosCyan,
                                fontSize = 9.5.sp,
                                fontFamily = FontFamily.Monospace,
                                textAlign = TextAlign.Center
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Button(
                        onClick = {
                            haptics.criticalHit()
                            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                            onStartRaid()
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(54.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = if (isEmergencyBreach) Color(0xFF102838) else Color(0xFF2A0808)),
                        border = androidx.compose.foundation.BorderStroke(2.dp, if (isEmergencyBreach) EidosCyan else EidosRed),
                        shape = androidx.compose.foundation.shape.CutCornerShape(8.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ZzzIcon(iconRes = R.drawable.ic_event_evac, size = 18.dp, tint = if (isEmergencyBreach) EidosCyan else EidosRed)
                            Spacer(Modifier.width(6.dp))
                            Text(
                                if (isEmergencyBreach) "НАЧАТЬ ЭКСТРЕННЫЙ СПУСК (0 BC)" else "НАЧАТЬ ПОГРУЖЕНИЕ В БЕЗДНУ (-20 BC)",
                                color = if (isEmergencyBreach) EidosCyan else EidosRed,
                                fontWeight = FontWeight.Black,
                                fontSize = 12.5.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }
        }
    }
}
