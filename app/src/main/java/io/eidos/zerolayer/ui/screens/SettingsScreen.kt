package io.eidos.zerolayer.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.AuthSession
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.ui.components.AuthDialogMode
import io.eidos.zerolayer.ui.components.ZzzAuthDialog
import io.eidos.zerolayer.ui.theme.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    player: Player?,
    authSession: AuthSession? = null,
    isAuthLoading: Boolean = false,
    authError: String? = null,
    onLogin: (String, String) -> Unit = { _, _ -> },
    onRegister: (String, String) -> Unit = { _, _ -> },
    onLogout: () -> Unit = {},
    onSyncCloud: () -> Unit = {},
    onBuyPremium: () -> Unit,
    onExport: suspend () -> String,
    onImport: (String) -> Unit,
    onBack: () -> Unit,
    onGrantAdminResources: () -> Unit = {},
    onGrantGodKit: () -> Unit = {},
    onToggleAdminMode: (Boolean) -> Unit = {}
) {
    var dataString by remember { mutableStateOf("") }
    var showAuthModal by remember { mutableStateOf(false) }
    var authModalMode by remember { mutableStateOf(AuthDialogMode.LOGIN) }
    val scope = rememberCoroutineScope()
    val haptics = LocalHapticFeedback.current
    val isPremium = player?.is_premium ?: false
    val isAdmin = player?.is_admin == true

    if (showAuthModal) {
        ZzzAuthDialog(
            initialMode = authModalMode,
            isLoading = isAuthLoading,
            errorMessage = authError,
            onDismiss = { showAuthModal = false },
            onLogin = { user, pass ->
                onLogin(user, pass)
            },
            onRegister = { user, pass ->
                onRegister(user, pass)
            }
        )
    }

    // Auto-close modal when logged in
    LaunchedEffect(authSession?.isLoggedIn) {
        if (authSession?.isLoggedIn == true) {
            showAuthModal = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("НАСТРОЙКИ СИСТЕМЫ // ДЕПО", color = Color.Gray, fontWeight = FontWeight.Bold, fontSize = 16.sp) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.Gray)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Black
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Supabase Cloud Auth Section
            Text("НЕЙРО-АККАУНТ И ОБЛАЧНЫЙ СРЕЗ // SUPABASE AUTH", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)

            val isLoggedIn = authSession?.isLoggedIn == true
            Surface(
                color = Color(0xFF0C101A),
                shape = CutCornerShape(8.dp),
                border = androidx.compose.foundation.BorderStroke(1.5.dp, if (isLoggedIn) ZzzToxicGreen else ZzzElectricCyan),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text(if (isLoggedIn) "🛡" else "☁️", fontSize = 22.sp)
                            Column {
                                Text(
                                    text = if (isLoggedIn) "ОПЕРАТОР: ${authSession?.username?.uppercase() ?: "ONLINE"}" else "SUPABASE CLOUD AUTH",
                                    color = if (isLoggedIn) ZzzToxicGreen else EidosCyan,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = if (isLoggedIn) {
                                        "Статус: Активен (Виртуальный аккаунт Eidos)"
                                    } else {
                                        "Статус: Гостевой режим (Оффлайн)"
                                    },
                                    color = Color.White.copy(alpha = 0.85f),
                                    fontSize = 11.sp
                                )
                            }
                        }

                        Surface(
                            color = (if (isLoggedIn) ZzzToxicGreen else ZzzAcidYellow).copy(alpha = 0.2f),
                            shape = CutCornerShape(4.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, if (isLoggedIn) ZzzToxicGreen else ZzzAcidYellow)
                        ) {
                            Text(
                                text = if (isLoggedIn) "ONLINE // LINKED" else "GUEST // LOCAL",
                                color = if (isLoggedIn) ZzzToxicGreen else ZzzAcidYellow,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.ExtraBold,
                                fontFamily = FontFamily.Monospace,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 3.dp)
                            )
                        }
                    }

                    if (isLoggedIn) {
                        val lastSyncStr = if ((authSession?.lastSyncTimestamp ?: 0L) > 0) {
                            SimpleDateFormat("HH:mm:ss dd.MM.yyyy", Locale.getDefault()).format(Date(authSession!!.lastSyncTimestamp))
                        } else "Не выполнялась"

                        Text(
                            text = "Последний срез данных: $lastSyncStr",
                            color = ZzzTextSecondary,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = {
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                    onSyncCloud()
                                },
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = ZzzElectricCyan.copy(alpha = 0.25f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzElectricCyan),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("☁ СИНХРОНИЗАЦИЯ", color = ZzzElectricCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }

                            io.eidos.zerolayer.ui.components.ZzzDangerButton(
                                text = "⏏ ВЫЙТИ",
                                onClick = {
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                    onLogout()
                                },
                                modifier = Modifier.weight(1f),
                                height = 40.dp
                            )
                        }
                    } else {
                        Text(
                            text = "Войдите или зарегистрируйтесь по позывному и паролю, чтобы сохранять персонажа в облако и восстанавливать прогресс на любых устройствах.",
                            color = ZzzTextBody,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = {
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                    authModalMode = AuthDialogMode.LOGIN
                                    showAuthModal = true
                                },
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = ZzzElectricCyan.copy(alpha = 0.3f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzElectricCyan),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("🔓 ВОЙТИ", color = ZzzElectricCyan, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold)
                            }

                            Button(
                                onClick = {
                                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                    authModalMode = AuthDialogMode.REGISTER
                                    showAuthModal = true
                                },
                                shape = CutCornerShape(4.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = ZzzAcidYellow.copy(alpha = 0.3f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzAcidYellow),
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("🛡 СОЗДАТЬ АККАУНТ", color = ZzzAcidYellow, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold)
                            }
                        }
                    }
                }
            }

            // SaaS Premium Section
            Text("ОБЛАЧНАЯ ПОДПИСКА (SaaS)", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = EidosGlass),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (isPremium) EidosNeon else Color.Gray.copy(alpha = 0.5f)),
                shape = CutCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    if (isPremium) {
                        Text(
                            "★ СТАТУС: PREMIUM ОПЕРАТОР ★",
                            color = EidosNeon,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "Доступ к расширенным нейросетям активен. Стоимость шагов в рейдах снижена до 10 ед. Энергии. Ежедневные контейнеры поставляются без задержек.",
                            color = Color.LightGray,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                    } else {
                        Text(
                            "★ СТАТУС: БАЗОВЫЙ ОПЕРАТОР ★",
                            color = Color.Gray,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            "Преимущества статуса Premium:",
                            color = Color.Gray,
                            fontSize = 11.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "• Стоимость шага в рейде снижена с 15 до 10 Энергии.\n• Повышенный шанс нахождения редкого лута.\n• Ежедневный сброс припасов синхронизируется мгновенно.",
                            color = Color.LightGray,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(
                            onClick = onBuyPremium,
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFFB300)),
                            shape = CutCornerShape(4.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("АКТИВИРОВАТЬ PREMIUM // 100 XTR", color = Color.Black, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                        }
                    }
                }
            }

            // Hardware & Haptics Section
            Text("ОПТИМИЗАЦИЯ И ЖЕЛЕЗО // 120 Гц & HAPTICS", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = EidosGlass),
                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.5f)),
                shape = CutCornerShape(8.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    val context = androidx.compose.ui.platform.LocalContext.current
                    val audioManager = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }
                    val hapticsManager = remember { io.eidos.zerolayer.ui.utils.HapticFeedbackManager.getInstance(context) }

                    var soundEnabled by remember { mutableStateOf(audioManager.isSoundEnabled) }
                    var musicEnabled by remember { mutableStateOf(audioManager.isMusicEnabled) }
                    var musicVolume by remember { mutableFloatStateOf(audioManager.musicVolume) }
                    var effectsVolume by remember { mutableFloatStateOf(audioManager.effectsVolume) }
                    var hapticsEnabled by remember { mutableStateOf(hapticsManager.isHapticsEnabled) }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("⚡ Частота обновления экрана", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text("120 Гц High Refresh Rate & Particle Canvas", color = EidosNeon, fontSize = 11.sp)
                        }
                        Badge(containerColor = EidosNeon.copy(alpha = 0.2f), contentColor = EidosNeon) {
                            Text("120 FPS", fontWeight = FontWeight.Bold)
                        }
                    }

                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("🌌 AGSL Glitch Shaders & 3D Gyro Tilt", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text("Аппаратный шейдерный движок и датчик наклона", color = EidosCyan, fontSize = 11.sp)
                        }
                        Badge(containerColor = EidosCyan.copy(alpha = 0.2f), contentColor = EidosCyan) {
                            Text("AGSL 3D", fontWeight = FontWeight.Bold)
                        }
                    }

                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f))

                    // BGM Control Switch
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("🎵 Фоновое Музыкальное Сопровождение", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text("Цикличная музыка в меню и Нулевом Слое", color = EidosNeon, fontSize = 11.sp)
                        }
                        Switch(
                            checked = musicEnabled,
                            onCheckedChange = {
                                musicEnabled = it
                                audioManager.isMusicEnabled = it
                            },
                            colors = SwitchDefaults.colors(checkedThumbColor = EidosNeon, checkedTrackColor = EidosNeon.copy(alpha = 0.3f))
                        )
                    }

                    if (musicEnabled) {
                        Column(modifier = Modifier.fillMaxWidth()) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("🔊 Громкость Музыки", color = Color.LightGray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                Text("${(musicVolume * 100).toInt()}%", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                            Slider(
                                value = musicVolume,
                                onValueChange = {
                                    musicVolume = it
                                    audioManager.musicVolume = it
                                },
                                valueRange = 0f..1f,
                                colors = SliderDefaults.colors(
                                    thumbColor = EidosCyan,
                                    activeTrackColor = EidosCyan,
                                    inactiveTrackColor = Color.DarkGray
                                )
                            )
                        }
                    }

                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("🔊 Звуковые Эффекты (SFX)", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text("Низколатентный аудиосинтез в реальном времени", color = Color.Gray, fontSize = 11.sp)
                        }
                        Switch(
                            checked = soundEnabled,
                            onCheckedChange = {
                                soundEnabled = it
                                audioManager.isSoundEnabled = it
                                if (it) audioManager.playSound(io.eidos.zerolayer.ui.utils.EidosAudioManager.SoundType.CLICK_CYBER)
                            },
                            colors = SwitchDefaults.colors(checkedThumbColor = EidosCyan, checkedTrackColor = EidosCyan.copy(alpha = 0.3f))
                        )
                    }

                    if (soundEnabled) {
                        Column(modifier = Modifier.fillMaxWidth()) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("🔊 Громкость Эффектов", color = Color.LightGray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                Text("${(effectsVolume * 100).toInt()}%", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                            }
                            Slider(
                                value = effectsVolume,
                                onValueChange = {
                                    effectsVolume = it
                                    audioManager.effectsVolume = it
                                },
                                valueRange = 0f..1f,
                                colors = SliderDefaults.colors(
                                    thumbColor = EidosCyan,
                                    activeTrackColor = EidosCyan,
                                    inactiveTrackColor = Color.DarkGray
                                )
                            )
                        }
                    }

                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.3f))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("📳 Продвинутая Вибрация (Haptics)", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text("VibratorManager с пресетами кликов и шагов", color = Color.Gray, fontSize = 11.sp)
                        }
                        Switch(
                            checked = hapticsEnabled,
                            onCheckedChange = {
                                hapticsEnabled = it
                                hapticsManager.isHapticsEnabled = it
                                if (it) hapticsManager.click()
                            },
                            colors = SwitchDefaults.colors(checkedThumbColor = EidosNeon, checkedTrackColor = EidosNeon.copy(alpha = 0.3f))
                        )
                    }
                }
            }

            // Admin / God Mode Section
            Text("РЕЖИМ АДМИНИСТРАТОРА // GOD MODE", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)

            Surface(
                color = if (isAdmin) Color(0xFF20002A).copy(alpha = 0.9f) else Color(0xFF141414).copy(alpha = 0.8f),
                shape = CutCornerShape(8.dp),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (isAdmin) Color(0xFFFFD700) else Color.Gray.copy(alpha = 0.3f)
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("👑", fontSize = 18.sp, modifier = Modifier.padding(end = 8.dp))
                            Column {
                                Text("GOD MODE ПРАВА", color = if (isAdmin) Color(0xFFFFD700) else Color.Gray, fontSize = 12.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
                                Text(if (isAdmin) "АДМИНИСТРАТОР СЕТИ АКТИВЕН" else "ТЕСТОВЫЙ РЕЖИМ ОТКЛЮЧЕН", color = if (isAdmin) EidosNeon else Color.DarkGray, fontSize = 10.sp)
                            }
                        }
                        TextButton(onClick = { onToggleAdminMode(!isAdmin) }) {
                            Text(if (isAdmin) "ВЫКЛ" else "ВКЛ ТЕСТ", color = EidosCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    if (isAdmin) {
                        Spacer(modifier = Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                            Button(
                                onClick = onGrantAdminResources,
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFFD700).copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD700)),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.weight(1f).height(36.dp),
                                contentPadding = PaddingValues(2.dp)
                            ) {
                                Text("+100k BC & 1k 💎", color = Color(0xFFFFD700), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }
                            Button(
                                onClick = onGrantGodKit,
                                colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                shape = CutCornerShape(4.dp),
                                modifier = Modifier.weight(1f).height(36.dp),
                                contentPadding = PaddingValues(2.dp)
                            ) {
                                Text("⚔️ ВЫДАТЬ GOD KIT", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            // Data Management Section
            Text("УПРАВЛЕНИЕ НЕЙРО-ПРОФИЛЕМ", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)

            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Экспортируйте или импортируйте слепок вашей личности (JSON). Сбросы PvP сезонов сохраняют ваши премиум привилегии.", color = Color.Gray, fontSize = 11.sp, lineHeight = 15.sp)
                OutlinedTextField(
                    value = dataString,
                    onValueChange = { dataString = it },
                    modifier = Modifier.fillMaxWidth().heightIn(max = 140.dp),
                    label = { Text("Код структуры данных") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = EidosCyan,
                        unfocusedBorderColor = Color.Gray
                    )
                )
                Spacer(modifier = Modifier.height(4.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            scope.launch {
                                dataString = onExport()
                            }
                        },
                        modifier = Modifier.weight(1f),
                        shape = CutCornerShape(4.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan)
                    ) {
                        Text("ЭКСПОРТ", color = EidosCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                    Button(
                        onClick = { onImport(dataString) },
                        modifier = Modifier.weight(1f),
                        shape = CutCornerShape(4.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed)
                    ) {
                        Text("ИМПОРТ", color = EidosRed, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

