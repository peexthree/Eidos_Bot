package io.eidos.zerolayer.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
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
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.AuthSession
import io.eidos.zerolayer.data.Player
import io.eidos.zerolayer.ui.components.AuthDialogMode
import io.eidos.zerolayer.ui.components.VideoBackground
import io.eidos.zerolayer.ui.components.ZzzAuthDialog
import io.eidos.zerolayer.ui.components.ZzzIcon
import io.eidos.zerolayer.ui.components.ZzzMainButton
import io.eidos.zerolayer.ui.components.ZzzWindowCard
import io.eidos.zerolayer.R
import io.eidos.zerolayer.BuildConfig
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

    Box(modifier = Modifier.fillMaxSize()) {
        // Layer 0: Living hub background video
        VideoBackground(resName = "bg_hub", modifier = Modifier.fillMaxSize())

        // Layer 1: Darkened cyberpunk tint overlay
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF04080F).copy(alpha = 0.7f))
        )

        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text(
                                buildAnnotatedString {
                                    withStyle(SpanStyle(color = EidosCyan)) { append("НАСТРОЙКИ СИСТЕМЫ ") }
                                    withStyle(SpanStyle(color = ZzzAcidYellow)) { append("// ДЕПО") }
                                },
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 14.sp,
                                fontFamily = FontFamily.Monospace,
                                letterSpacing = 1.sp
                            )
                            Text(
                                "КОНФИГУРАЦИЯ ОПЕРАТОРА // ZERO LAYER",
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
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent)
                )
            },
            containerColor = Color.Transparent
        ) { innerPadding ->
            Column(
                modifier = Modifier
                    .padding(innerPadding)
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // ============ SECTION: СИНХРОНИЗАЦИЯ ============
                ZzzSettingsSectionHeader(text = "СИНХРОНИЗАЦИЯ", tag = "SUPABASE AUTH")

                // Supabase Cloud Auth Section
                val isLoggedIn = authSession?.isLoggedIn == true
                ZzzWindowCard(
                    title = "НЕЙРО-АККАУНТ И ОБЛАЧНЫЙ СРЕЗ",
                    subTitle = "SUPABASE AUTH",
                    borderColor = if (isLoggedIn) ZzzToxicGreen else ZzzElectricCyan
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                ZzzIcon(if (isLoggedIn) R.drawable.ic_action_defense else R.drawable.ic_event_unknown, size = 22.dp)
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
                                ZzzMainButton(
                                    text = "СИНХРОНИЗАЦИЯ",
                                    onClick = {
                                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                        onSyncCloud()
                                    },
                                    primaryColor = ZzzElectricCyan.copy(alpha = 0.25f),
                                    borderColor = ZzzElectricCyan,
                                    textColor = ZzzElectricCyan,
                                    useGraphicBackground = false,
                                    showHazardStripes = false,
                                    height = 40.dp,
                                    modifier = Modifier.weight(1f)
                                )

                                io.eidos.zerolayer.ui.components.ZzzDangerButton(
                                    text = "ВЫЙТИ",
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
                                ZzzMainButton(
                                    text = "ВОЙТИ",
                                    onClick = {
                                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                        authModalMode = AuthDialogMode.LOGIN
                                        showAuthModal = true
                                    },
                                    primaryColor = ZzzElectricCyan.copy(alpha = 0.3f),
                                    borderColor = ZzzElectricCyan,
                                    textColor = ZzzElectricCyan,
                                    useGraphicBackground = false,
                                    showHazardStripes = false,
                                    height = 42.dp,
                                    modifier = Modifier.weight(1f)
                                )

                                ZzzMainButton(
                                    text = "СОЗДАТЬ АККАУНТ",
                                    onClick = {
                                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                        authModalMode = AuthDialogMode.REGISTER
                                        showAuthModal = true
                                    },
                                    primaryColor = ZzzAcidYellow.copy(alpha = 0.3f),
                                    borderColor = ZzzAcidYellow,
                                    textColor = ZzzAcidYellow,
                                    useGraphicBackground = false,
                                    showHazardStripes = false,
                                    height = 42.dp,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                        }
                    }
                }

                // SaaS Premium Section
                ZzzWindowCard(
                    title = "ОБЛАЧНАЯ ПОДПИСКА",
                    subTitle = "SAAS",
                    borderColor = if (isPremium) EidosNeon else Color.Gray.copy(alpha = 0.5f)
                ) {
                    if (isPremium) {
                        Text(
                            "СТАТУС: PREMIUM ОПЕРАТОР",
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
                            "СТАТУС: БАЗОВЫЙ ОПЕРАТОР",
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
                        ZzzMainButton(
                            text = "АКТИВИРОВАТЬ PREMIUM // 100 XTR",
                            onClick = onBuyPremium,
                            primaryColor = ZzzGold,
                            borderColor = ZzzGold,
                            textColor = Color.Black,
                            useGraphicBackground = false,
                            showHazardStripes = false,
                            height = 42.dp,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }

                // Data Management Section
                ZzzWindowCard(
                    title = "УПРАВЛЕНИЕ НЕЙРО-ПРОФИЛЕМ",
                    subTitle = "JSON EXPORT",
                    borderColor = EidosCyan.copy(alpha = 0.5f)
                ) {
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
                            ZzzMainButton(
                                text = "ЭКСПОРТ",
                                onClick = {
                                    scope.launch {
                                        dataString = onExport()
                                    }
                                },
                                primaryColor = EidosCyan.copy(alpha = 0.2f),
                                borderColor = EidosCyan,
                                textColor = EidosCyan,
                                useGraphicBackground = false,
                                showHazardStripes = false,
                                height = 42.dp,
                                modifier = Modifier.weight(1f)
                            )
                            ZzzMainButton(
                                text = "ИМПОРТ",
                                onClick = { onImport(dataString) },
                                primaryColor = EidosRed.copy(alpha = 0.2f),
                                borderColor = EidosRed,
                                textColor = EidosRed,
                                useGraphicBackground = false,
                                showHazardStripes = false,
                                height = 42.dp,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }

                // ============ SECTION: АУДИО/ВИБРО ============
                ZzzSettingsSectionHeader(text = "АУДИО/ВИБРО", tag = "120 Гц & HAPTICS")

                // Hardware & Haptics Section
                ZzzWindowCard(
                    title = "ОПТИМИЗАЦИЯ И ЖЕЛЕЗО",
                    subTitle = "120 Гц & HAPTICS",
                    borderColor = EidosCyan.copy(alpha = 0.5f)
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
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
                                Text("Частота обновления экрана", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
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
                                Text("AGSL Glitch Shaders & 3D Gyro Tilt", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
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
                                Text("Фоновое Музыкальное Сопровождение", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
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
                                    Text("Громкость Музыки", color = Color.LightGray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
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
                                Text("Звуковые Эффекты (SFX)", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
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
                                    Text("Громкость Эффектов", color = Color.LightGray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
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
                                Text("Продвинутая Вибрация (Haptics)", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
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

                // ============ SECTION: О ПРОГРАММЕ ============
                ZzzSettingsSectionHeader(text = "О ПРОГРАММЕ", tag = "BUILD INFO")

                ZzzWindowCard(
                    title = "EIDOS: ZERO LAYER CHRONICLES",
                    subTitle = "О ПРОГРАММЕ",
                    borderColor = ZzzAcidYellow.copy(alpha = 0.6f)
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("ВЕРСИЯ СБОРКИ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text(
                                "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
                                color = ZzzElectricCyan,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("ТИП СБОРКИ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text(
                                BuildConfig.BUILD_TYPE.uppercase(),
                                color = if (BuildConfig.DEBUG) ZzzAcidYellow else ZzzToxicGreen,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("СТАТУС ПОДПИСКИ", color = Color.Gray, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                            Text(
                                if (isPremium) "PREMIUM" else "БАЗОВЫЙ",
                                color = if (isPremium) EidosNeon else Color.Gray,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        HorizontalDivider(color = Color.Gray.copy(alpha = 0.25f))
                        Text(
                            "Квантовая матрица EIDOS. Все операции выполняются локально на устройстве оператора, облачный срез данных - по вашему запросу.",
                            color = ZzzTextSecondary,
                            fontSize = 10.sp,
                            lineHeight = 14.sp
                        )
                    }
                }

                // ============ SECTION: DEV // ТОЛЬКО ТЕСТ (DEBUG ONLY, EXPANDABLE) ============
                if (BuildConfig.DEBUG) {
                    var devExpanded by remember { mutableStateOf(false) }

                    Surface(
                        color = Color(0xFF140A00).copy(alpha = 0.85f),
                        shape = CutCornerShape(8.dp),
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (devExpanded) ZzzAcidYellow.copy(alpha = 0.8f) else ZzzAcidYellow.copy(alpha = 0.3f)
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column {
                            // Collapsed header - always visible
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable {
                                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                                        devExpanded = !devExpanded
                                    }
                                    .padding(horizontal = 14.dp, vertical = 12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    ZzzIcon(R.drawable.ic_res_overdrive, size = 16.dp, modifier = Modifier.padding(end = 8.dp))
                                    Text(
                                        "DEV // ТОЛЬКО ТЕСТ",
                                        color = ZzzAcidYellow,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        fontFamily = FontFamily.Monospace,
                                        letterSpacing = 1.sp
                                    )
                                }
                                Text(
                                    if (devExpanded) "[- СВЕРНУТЬ]" else "[+ РАЗВЕРНУТЬ]",
                                    color = ZzzAcidYellow.copy(alpha = 0.7f),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }

                            // Admin / God Mode Section (Restricted to Debug Builds only)
                            AnimatedVisibility(
                                visible = devExpanded,
                                enter = fadeIn() + expandVertically(),
                                exit = fadeOut() + shrinkVertically()
                            ) {
                                Surface(
                                    color = if (isAdmin) Color(0xFF20002A).copy(alpha = 0.9f) else Color(0xFF141414).copy(alpha = 0.8f),
                                    shape = CutCornerShape(8.dp),
                                    border = androidx.compose.foundation.BorderStroke(
                                        1.dp,
                                        if (isAdmin) ZzzGold else Color.Gray.copy(alpha = 0.3f)
                                    ),
                                    modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                ZzzIcon(R.drawable.ic_res_overdrive, size = 18.dp, modifier = Modifier.padding(end = 8.dp))
                                                Column {
                                                    Text("GOD MODE ПРАВА", color = if (isAdmin) ZzzGold else Color.Gray, fontSize = 12.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
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
                                                    colors = ButtonDefaults.buttonColors(containerColor = ZzzGold.copy(alpha = 0.2f)),
                                                    border = androidx.compose.foundation.BorderStroke(1.dp, ZzzGold),
                                                    shape = CutCornerShape(4.dp),
                                                    modifier = Modifier.weight(1f).height(36.dp),
                                                    contentPadding = PaddingValues(2.dp)
                                                ) {
                                                    Text("+100k BC & 1k Осколков", color = ZzzGold, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                                }
                                                Button(
                                                    onClick = onGrantGodKit,
                                                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                                                    border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                                                    shape = CutCornerShape(4.dp),
                                                    modifier = Modifier.weight(1f).height(36.dp),
                                                    contentPadding = PaddingValues(2.dp)
                                                ) {
                                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                                        ZzzIcon(R.drawable.ic_action_attack, size = 10.dp)
                                                        Spacer(Modifier.width(3.dp))
                                                        Text("ВЫДАТЬ GOD KIT", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
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

                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

/**
 * Kit-style section header: yellow "///" slash + cyan monospace title + hazard divider line.
 */
@Composable
private fun ZzzSettingsSectionHeader(text: String, tag: String = "") {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth().padding(top = 4.dp)
    ) {
        Text(
            "///",
            color = ZzzAcidYellow,
            fontSize = 12.sp,
            fontWeight = FontWeight.ExtraBold,
            fontFamily = FontFamily.Monospace
        )
        Spacer(Modifier.width(6.dp))
        Text(
            text,
            color = EidosCyan,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 1.sp
        )
        if (tag.isNotEmpty()) {
            Spacer(Modifier.width(6.dp))
            Text(
                "// $tag",
                color = Color.Gray,
                fontSize = 9.sp,
                fontFamily = FontFamily.Monospace
            )
        }
        Spacer(Modifier.width(8.dp))
        Box(
            modifier = Modifier
                .weight(1f)
                .height(1.dp)
                .background(EidosCyan.copy(alpha = 0.3f))
        )
    }
}
