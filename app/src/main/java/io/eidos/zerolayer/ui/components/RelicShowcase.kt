package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import io.eidos.zerolayer.ui.utils.EidosAudioManager

data class EarthRelic(
    val id: String,
    val name: String,
    val type: String,
    val description: String,
    val buffDescription: String,
    val icon: String,
    val isUnlocked: Boolean = true
)

val DEFAULT_EARTH_RELICS = listOf(
    EarthRelic(
        id = "tape_1999",
        name = "Кассета «Echoes 1999»",
        type = "Аудиокассета Земли",
        description = "Аналоговая магнитная лента с записью шума океана и уличного дождя древнего города.",
        buffDescription = "⚡ +10% к получению Биокоинов в рейдах",
        icon = "📼"
    ),
    EarthRelic(
        id = "crystal_arch",
        name = "Кварцевый Якорь Архитекторов",
        type = "Квантовый Кристалл",
        description = "Застывший сгусток чистой информации, извлеченный из центрального процессора Первого Города.",
        buffDescription = "🛡️ +15% к Защите от Скверны",
        icon = "💎"
    ),
    EarthRelic(
        id = "vox_broker",
        name = "Вокс-Рекордер Admin-00",
        type = "Теневая Запись",
        description = "Зашифрованное аудиопослание Теневого Брокера о расположении секретных шлюзов Бездны.",
        buffDescription = "⚔️ +12% к Критическому урону",
        icon = "🎙️"
    ),
    EarthRelic(
        id = "floppy_eidos",
        name = "Дискета «EIDOS 1.0»",
        type = "Реликвия Прошлого",
        description = "Гибкий магнитный диск 3.5 дюйма с исходным кодом первого протокола переноса сознания.",
        buffDescription = "🧠 +20% к получаемому Опыту (XP)",
        icon = "💾"
    ),
    EarthRelic(
        id = "camera_sol",
        name = "Пленочный Фотоаппарат",
        type = "Артефакт Забытых",
        description = "Механический фотоаппарат с невоплощенными снимками солнечного заката.",
        buffDescription = "❤️ +25 к Максимальному Сигналу (HP)",
        icon = "📷"
    )
)

@Composable
fun RelicShowcaseDialog(
    activeRelicId: String?,
    onSelectResonator: (EarthRelic) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val audio = remember { EidosAudioManager.getInstance(context) }
    var selectedRelic by remember { mutableStateOf(DEFAULT_EARTH_RELICS.firstOrNull { it.id == activeRelicId } ?: DEFAULT_EARTH_RELICS.first()) }

    Dialog(onDismissRequest = onDismiss) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(520.dp)
                .background(Color.Black, CutCornerShape(10.dp))
                .border(2.dp, Color.Yellow, CutCornerShape(10.dp))
                .padding(16.dp)
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "📼 СТОЙКА РЕЛИКВИЙ ЗЕМЛИ",
                        color = Color.Yellow,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    TextButton(onClick = onDismiss) {
                        Text("ЗАКРЫТЬ", color = Color.Gray, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                    }
                }

                Text(
                    "Размещайте найденные реликвии прошлого на Стойке Резонатора для получения постоянных усилений вашей матрицы.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )

                // Relics List
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    items(DEFAULT_EARTH_RELICS) { relic ->
                        val isEquipped = relic.id == activeRelicId
                        val isSelected = relic.id == selectedRelic.id

                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = when {
                                    isEquipped -> Color.Yellow.copy(alpha = 0.2f)
                                    isSelected -> EidosGlass
                                    else -> Color(0xFF0F141C)
                                }
                            ),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (isEquipped) Color.Yellow else if (isSelected) EidosCyan else Color.DarkGray
                            ),
                            shape = CutCornerShape(6.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
                                    selectedRelic = relic
                                }
                        ) {
                            Row(
                                modifier = Modifier.padding(10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(relic.icon, fontSize = 22.sp)
                                Spacer(modifier = Modifier.width(10.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Text(
                                            relic.name,
                                            color = if (isEquipped) Color.Yellow else Color.White,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace
                                        )
                                        if (isEquipped) {
                                            SemanticBadge(text = "АКТИВЕН", type = BadgeType.WARNING)
                                        }
                                    }
                                    Text(
                                        relic.type,
                                        color = EidosCyan,
                                        fontSize = 9.sp,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }
                    }
                }

                // Selected Relic Detail Card
                Card(
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.6f)),
                    shape = CutCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        Text(
                            text = selectedRelic.description,
                            color = Color.LightGray,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 14.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "ЭФФЕКТ РЕЗОНАТОРА: ${selectedRelic.buffDescription}",
                            color = EidosNeon,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                Button(
                    onClick = {
                        audio.playSound(EidosAudioManager.SoundType.RELIC_UNLOCK)
                        onSelectResonator(selectedRelic)
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (selectedRelic.id == activeRelicId) Color.DarkGray else Color.Yellow
                    ),
                    enabled = selectedRelic.id != activeRelicId,
                    shape = CutCornerShape(4.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = if (selectedRelic.id == activeRelicId) "РЕЗОНАТОР УЖЕ АКТИВЕН" else "АКТИВИРОВАТЬ РЕЗОНАТОР",
                        color = Color.Black,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}
