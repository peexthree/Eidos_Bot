package io.eidos.zerolayer.ui.screens

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.annotation.OptIn
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import io.eidos.zerolayer.R
import io.eidos.zerolayer.ui.theme.*

@OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
fun OnboardingScreen(
    onComplete: (nickname: String, faction: String) -> Unit,
    onLoginClick: (() -> Unit)? = null
) {
    val context = LocalContext.current
    val audioManager = remember { io.eidos.zerolayer.ui.utils.EidosAudioManager.getInstance(context) }
    var showVideoIntro by remember { mutableStateOf(true) }
    var nickname by remember { mutableStateOf("") }
    var selectedFaction by remember { mutableStateOf("МАТЕРИЯ") }
    var secretCode by remember { mutableStateOf("") }
    var showSecretInput by remember { mutableStateOf(false) }
    var currentStep by remember { mutableIntStateOf(0) } // 0: Lore, 1: Callsign, 2: Faction, 3: Directives, 4: Deployment
    var isVoiceMuted by remember { mutableStateOf(false) }
    var replayTrigger by remember { mutableIntStateOf(0) }

    val scrollState = rememberScrollState()
    val telemetryManager = remember { io.eidos.zerolayer.ui.utils.EidosTelemetryManager.getInstance(context) }

    LaunchedEffect(currentStep) {
        telemetryManager.logOnboardingStepCompleted(currentStep, "step_${currentStep + 1}")
    }

    // Manage background music: Pause during intro video, play BGM during onboarding
    LaunchedEffect(showVideoIntro) {
        if (showVideoIntro) {
            audioManager.pauseMusic()
        } else {
            audioManager.playBgm(io.eidos.zerolayer.ui.utils.EidosAudioManager.BgmTrack.MAIN_MENU)
            audioManager.duckMusic(true)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            audioManager.duckMusic(false)
        }
    }

    // Automatic Voice Playback for each Step using MediaPlayer
    var activeMediaPlayer by remember { mutableStateOf<android.media.MediaPlayer?>(null) }
    var isAudioPlaying by remember { mutableStateOf(false) }

    DisposableEffect(Unit) {
        onDispose {
            try {
                activeMediaPlayer?.stop()
                activeMediaPlayer?.release()
                activeMediaPlayer = null
                audioManager.duckMusic(false)
            } catch (_: Exception) {}
        }
    }

    LaunchedEffect(currentStep, showVideoIntro, isVoiceMuted, replayTrigger) {
        try {
            activeMediaPlayer?.stop()
            activeMediaPlayer?.release()
            activeMediaPlayer = null
            isAudioPlaying = false
            audioManager.duckMusic(false)
        } catch (_: Exception) {}

        if (showVideoIntro || isVoiceMuted) {
            return@LaunchedEffect
        }

        val soundRes = when (currentStep) {
            0 -> R.raw.step1
            1 -> R.raw.step2
            2 -> R.raw.step3
            3 -> R.raw.step4
            4 -> R.raw.step5
            else -> null
        }

        if (soundRes != null) {
            try {
                audioManager.duckMusic(true)
                val mp = android.media.MediaPlayer.create(context, soundRes)
                if (mp != null) {
                    mp.isLooping = false
                    mp.setVolume(1.0f, 1.0f)
                    mp.setOnCompletionListener {
                        isAudioPlaying = false
                        audioManager.duckMusic(false)
                    }
                    mp.setOnErrorListener { _, _, _ ->
                        isAudioPlaying = false
                        audioManager.duckMusic(false)
                        true
                    }
                    mp.start()
                    isAudioPlaying = true
                    activeMediaPlayer = mp
                }
            } catch (e: Exception) {
                e.printStackTrace()
                isAudioPlaying = false
                audioManager.duckMusic(false)
            }
        }
    }

    if (showVideoIntro) {
        LogoVideoIntro(onFinish = { showVideoIntro = false })
    } else {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(ZzzObsidian)
        ) {
            // ZZZ Cyberpunk Grid & Particle Background
            ZzzBackgroundGridCanvas(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                // TOP HEADER BAR
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Logo Banner
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "EIDOS",
                            color = Color.White,
                            fontSize = 22.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.SansSerif,
                            letterSpacing = 2.sp
                        )
                        Text(
                            text = ":",
                            color = ZzzElectricCyan,
                            fontSize = 22.sp,
                            fontWeight = FontWeight.ExtraBold
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Surface(
                            color = ZzzHotMagenta,
                            shape = CutCornerShape(topStart = 4.dp, bottomEnd = 4.dp)
                        ) {
                            Text(
                                text = "CHRONICLES",
                                color = Color.White,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    // Voice Mute Switch Button
                    Surface(
                        onClick = { isVoiceMuted = !isVoiceMuted },
                        color = if (isVoiceMuted) Color(0x33FF007A) else Color(0x3300FFF6),
                        shape = CutCornerShape(6.dp),
                        border = androidx.compose.foundation.BorderStroke(
                            1.5.dp,
                            if (isVoiceMuted) ZzzHotMagenta else ZzzElectricCyan
                        )
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = if (isVoiceMuted) "🔇 ГИД ВЫКЛ" else "🔊 ЕВА-09",
                                color = if (isVoiceMuted) ZzzHotMagenta else ZzzElectricCyan,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                // SPEECH TERMINAL BUBBLE (EVA-09 DIALOGUE)
                val stepTitle = when (currentStep) {
                    0 -> "ШАГ 1: ЛОР И ЭЙДОС"
                    1 -> "ШАГ 2: КРИПТО-ПОЗЫВНОЙ"
                    2 -> "ШАГ 3: ВЫБОР СИНДИКАТА"
                    3 -> "ШАГ 4: БОЕВЫЕ ДИРЕКТИВЫ"
                    else -> "ШАГ 5: ИНИЦИАЛИЗАЦИЯ"
                }

                val stepDialogue = when (currentStep) {
                    0 -> "Привет, Оператор! Я ЕВА-09. Физический мир уничтожен Коллапсом 2099 года. Твоя личность перенесена в квантовую матрицу EIDOS. Готов погрузиться в Нулевой Слой?"
                    1 -> "Системе необходим твой уникальный крипто-позывной для фиксации в локальных реестрах Сетевой Войны."
                    2 -> "Матрица разделена между тремя Синдикатами. Выбери идеологическую доктрину для стартовых характеристик."
                    3 -> "Загружаю фундаментальные директивы выживания. Глубина увеличивает ценность наград, но 0% Сигнала уничтожит все данные."
                    else -> "Синхронизация профиля завершена. Стартовый набор доставлен в буфер. Шлюз открыт. Инициирую погружение!"
                }

                ZzzSpeechBubbleTerminal(
                    stepTag = stepTitle,
                    dialogueText = stepDialogue,
                    isAudioPlaying = isAudioPlaying,
                    onReplayVoice = { replayTrigger++ }
                )

                Spacer(modifier = Modifier.height(6.dp))

                // SEGMENTED HAZARD PROGRESS TRACKER (1/5)
                ZzzSegmentedProgressTracker(
                    currentStep = currentStep,
                    totalSteps = 5
                )

                Spacer(modifier = Modifier.height(6.dp))

                // DYNAMIC STEP CONTENT AREA (WITH ANIMATED CONTENT TRANSITION)
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                ) {
                    AnimatedContent(
                        targetState = currentStep,
                        transitionSpec = {
                            if (targetState > initialState) {
                                (slideInHorizontally { width -> width } + fadeIn()).togetherWith(
                                    slideOutHorizontally { width -> -width } + fadeOut()
                                )
                            } else {
                                (slideInHorizontally { width -> -width } + fadeIn()).togetherWith(
                                    slideOutHorizontally { width -> width } + fadeOut()
                                )
                            }
                        },
                        label = "zzz_step_transition"
                    ) { targetStep ->
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .verticalScroll(scrollState)
                        ) {
                            when (targetStep) {
                                0 -> ZzzPrologueStepContent()
                                1 -> ZzzNicknameStepContent(
                                    nickname = nickname,
                                    onNicknameChange = { nickname = it },
                                    onLoginClick = onLoginClick
                                )
                                2 -> ZzzFactionStepContent(
                                    selectedFaction = selectedFaction,
                                    onSelectFaction = { selectedFaction = it },
                                    showSecretInput = showSecretInput,
                                    onToggleSecret = { showSecretInput = !showSecretInput },
                                    secretCode = secretCode,
                                    onSecretChange = {
                                        secretCode = it
                                        if (it.trim().lowercase() == "admin_key" || it.trim().lowercase() == "architect") {
                                            selectedFaction = "АРХИТЕКТОРЫ"
                                        }
                                    }
                                )
                                3 -> ZzzGameplayDirectivesStepContent()
                                4 -> ZzzStarterKitStepContent(
                                    nickname = nickname,
                                    faction = selectedFaction
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // BOTTOM CONTROLS & TELEMETRY HUD
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom
                ) {
                    // Left: Telemetry HUD
                    ZzzTelemetryHud(
                        isAudioPlaying = isAudioPlaying,
                        onReplayVoice = { replayTrigger++ }
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    // Right: Action Buttons
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        if (currentStep > 0) {
                            Surface(
                                onClick = { currentStep-- },
                                color = ZzzDarkSurface,
                                shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp),
                                border = androidx.compose.foundation.BorderStroke(1.5.dp, Color.Gray.copy(alpha = 0.6f)),
                                modifier = Modifier.padding(end = 6.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        Icons.AutoMirrored.Filled.ArrowBack,
                                        contentDescription = "Назад",
                                        tint = Color.White,
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                        }

                        // Main Vibrant Next Button
                        val buttonText = if (currentStep < 4) "ДАЛЕЕ (ШАГ ${currentStep + 2})" else "ПОГРУЖЕНИЕ"
                        val canProceed = if (currentStep == 1) nickname.isNotBlank() else true

                        ZzzActionNextButton(
                            text = buttonText,
                            enabled = canProceed,
                            onClick = {
                                if (currentStep < 4) {
                                    currentStep++
                                } else {
                                    onComplete(nickname, selectedFaction)
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

// ==================== ZZZ VISUAL COMPONENTS ====================

@Composable
private fun ZzzBackgroundGridCanvas(modifier: Modifier = Modifier) {
    val infiniteTransition = rememberInfiniteTransition(label = "grid_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.15f,
        targetValue = 0.35f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )

    Canvas(modifier = modifier) {
        val width = size.width
        val height = size.height

        // Dark Gradient Vignette
        drawRect(
            brush = Brush.radialGradient(
                colors = listOf(Color(0xFF141A24), ZzzObsidian),
                center = Offset(width * 0.5f, height * 0.4f),
                radius = width * 0.9f
            )
        )

        // Diagonal Cyan Grid Lines
        val step = 45f
        var x = -height
        while (x < width + height) {
            drawLine(
                color = ZzzElectricCyan.copy(alpha = pulseAlpha * 0.25f),
                start = Offset(x, 0f),
                end = Offset(x + height, height),
                strokeWidth = 1f
            )
            x += step
        }

        // Reverse Diagonal Lines
        var rx = -height
        while (rx < width + height) {
            drawLine(
                color = ZzzHotMagenta.copy(alpha = pulseAlpha * 0.15f),
                start = Offset(rx + height, 0f),
                end = Offset(rx, height),
                strokeWidth = 1f
            )
            rx += step * 2
        }

        // Top-Right & Bottom-Left Decorative Slash Accents
        drawPath(
            path = Path().apply {
                moveTo(width - 120f, 0f)
                lineTo(width, 0f)
                lineTo(width, 120f)
                close()
            },
            color = ZzzHotMagenta.copy(alpha = 0.2f)
        )

        drawPath(
            path = Path().apply {
                moveTo(0f, height - 100f)
                lineTo(100f, height)
                lineTo(0f, height)
                close()
            },
            color = ZzzAcidYellow.copy(alpha = 0.15f)
        )
    }
}

@Composable
private fun ZzzSpeechBubbleTerminal(
    stepTag: String,
    dialogueText: String,
    isAudioPlaying: Boolean,
    onReplayVoice: () -> Unit
) {
    Surface(
        color = ZzzDarkSurface.copy(alpha = 0.94f),
        shape = CutCornerShape(topStart = 0.dp, bottomEnd = 16.dp, topEnd = 16.dp, bottomStart = 16.dp),
        border = androidx.compose.foundation.BorderStroke(2.dp, ZzzElectricCyan),
        modifier = Modifier
            .fillMaxWidth()
            .clip(CutCornerShape(topStart = 0.dp, bottomEnd = 16.dp, topEnd = 16.dp, bottomStart = 16.dp))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            // Header tag bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    color = ZzzElectricCyan,
                    shape = CutCornerShape(topStart = 2.dp, bottomEnd = 6.dp)
                ) {
                    Text(
                        text = " $stepTag ",
                        color = Color.Black,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.SansSerif,
                        letterSpacing = 1.sp,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    )
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (isAudioPlaying) {
                        Text(
                            text = "⚡ ВОСПРОИЗВЕДЕНИЕ",
                            color = ZzzToxicGreen,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(end = 6.dp)
                        )
                    }
                    Surface(
                        onClick = onReplayVoice,
                        color = Color(0x3300FFF6),
                        shape = CircleShape,
                        border = androidx.compose.foundation.BorderStroke(1.dp, ZzzElectricCyan)
                    ) {
                        Text(
                            text = " 🔊 ",
                            fontSize = 12.sp,
                            modifier = Modifier.padding(4.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Body Cyrillic Dialogue Text
            Text(
                text = dialogueText,
                color = ZzzTextBody,
                fontSize = 14.5.sp,
                fontWeight = FontWeight.Medium,
                fontFamily = FontFamily.SansSerif,
                lineHeight = 21.sp
            )
        }
    }
}

@Composable
private fun ZzzSegmentedProgressTracker(
    currentStep: Int,
    totalSteps: Int
) {
    Surface(
        color = ZzzDarkSurface.copy(alpha = 0.85f),
        shape = CutCornerShape(8.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x4400FFF6)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Step badge e.g. "1/5"
            Surface(
                color = ZzzHotMagenta,
                shape = CutCornerShape(4.dp)
            ) {
                Text(
                    text = "${currentStep + 1}/$totalSteps",
                    color = Color.White,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            // 5 Segmented Hazard Bars
            Row(
                modifier = Modifier.weight(1f),
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                val stepIcons = listOf("📖", "👤", "⚡", "⚔️", "🎁")

                for (i in 0 until totalSteps) {
                    val isDone = i < currentStep
                    val isActive = i == currentStep

                    val barColor = when {
                        isDone -> ZzzToxicGreen
                        isActive -> ZzzAcidYellow
                        else -> Color(0xFF1E2330)
                    }

                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(20.dp)
                            .background(
                                color = barColor,
                                shape = CutCornerShape(topStart = 4.dp, bottomEnd = 4.dp)
                            )
                            .border(
                                width = if (isActive) 1.5.dp else 0.5.dp,
                                color = if (isActive) ZzzElectricCyan else Color.Transparent,
                                shape = CutCornerShape(topStart = 4.dp, bottomEnd = 4.dp)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        if (isDone) {
                            Icon(
                                Icons.Default.Check,
                                contentDescription = null,
                                tint = Color.Black,
                                modifier = Modifier.size(12.dp)
                            )
                        } else {
                            Text(
                                text = stepIcons.getOrElse(i) { "" },
                                fontSize = 10.sp
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ZzzActionNextButton(
    text: String,
    enabled: Boolean,
    onClick: () -> Unit
) {
    val haptic = LocalHapticFeedback.current
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(if (isPressed) 0.94f else 1.0f, label = "button_scale")
    val shape = CutCornerShape(topStart = 10.dp, bottomEnd = 10.dp, topEnd = 3.dp, bottomStart = 3.dp)

    Surface(
        onClick = {
            if (enabled) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onClick()
            }
        },
        enabled = enabled,
        interactionSource = interactionSource,
        color = Color.Transparent,
        shape = shape,
        modifier = Modifier.scale(scale)
    ) {
        Box(
            modifier = Modifier
                .height(48.dp)
                .clip(shape)
                .padding(horizontal = 20.dp),
            contentAlignment = Alignment.Center
        ) {
            Image(
                painter = painterResource(id = R.drawable.btn_action_primary),
                contentDescription = null,
                contentScale = ContentScale.FillBounds,
                modifier = Modifier
                    .matchParentSize()
                    .alpha(if (enabled) 1.0f else 0.45f)
            )

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "///",
                    color = Color.White.copy(alpha = 0.6f),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(end = 6.dp)
                )

                Text(
                    text = text.uppercase(),
                    color = if (enabled) Color.White else Color.LightGray,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.SansSerif,
                    letterSpacing = 1.sp
                )

                Text(
                    text = " ➔",
                    color = if (enabled) Color.White else Color.LightGray,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.ExtraBold,
                    modifier = Modifier.padding(start = 4.dp)
                )
            }
        }
    }
}

@Composable
private fun ZzzTelemetryHud(
    isAudioPlaying: Boolean,
    onReplayVoice: () -> Unit
) {
    Surface(
        color = ZzzDarkSurface.copy(alpha = 0.9f),
        shape = CutCornerShape(6.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x4400FFF6))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // SIGNAL 85%
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("📶 SIGNAL ", color = Color.Gray, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                    Text("85%", color = ZzzElectricCyan, fontSize = 10.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.ExtraBold)
                }
                Box(
                    modifier = Modifier
                        .width(36.dp)
                        .height(3.dp)
                        .background(ZzzElectricCyan, RoundedCornerShape(1.dp))
                )
            }

            // ENERGY 60%
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("⚡ ENERGY ", color = Color.Gray, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                    Text("60%", color = ZzzAcidYellow, fontSize = 10.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.ExtraBold)
                }
                Box(
                    modifier = Modifier
                        .width(28.dp)
                        .height(3.dp)
                        .background(ZzzAcidYellow, RoundedCornerShape(1.dp))
                )
            }

            // SYNC 72%
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("⚙️ SYNC ", color = Color.Gray, fontSize = 8.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                    Text("72%", color = ZzzHotMagenta, fontSize = 10.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.ExtraBold)
                }
                Box(
                    modifier = Modifier
                        .width(32.dp)
                        .height(3.dp)
                        .background(ZzzHotMagenta, RoundedCornerShape(1.dp))
                )
            }

            // Voice wave audio indicator
            Surface(
                onClick = onReplayVoice,
                color = if (isAudioPlaying) ZzzToxicGreen.copy(alpha = 0.2f) else Color.Transparent,
                shape = CircleShape,
                border = androidx.compose.foundation.BorderStroke(1.dp, if (isAudioPlaying) ZzzToxicGreen else Color.Gray)
            ) {
                Text(
                    text = if (isAudioPlaying) "🎙️🎶" else "🎙️",
                    fontSize = 11.sp,
                    modifier = Modifier.padding(4.dp)
                )
            }
        }
    }
}

// ==================== ZZZ STEP CONTENT CARDS ====================

@Composable
private fun ZzzPrologueStepContent() {
    Column(modifier = Modifier.fillMaxWidth()) {
        ZzzLoreCard(
            tag = "ПРОТОКОЛ 01",
            title = "ИСХОД И ЦИФРОВИЗАЦИЯ",
            description = "После гибели биосферы в 2099 году остатки человечества загрузили сознание в глобальную квантовую сеть EIDOS. Мысль материальна, а выживание измеряется стабильностью Сигнала.",
            borderColor = ZzzElectricCyan
        )

        Spacer(modifier = Modifier.height(8.dp))

        ZzzLoreCard(
            tag = "УГРОЗА 02",
            title = "ЭНТРОПИЯ И БЕЗДНА",
            description = "Критический сбой Первых Архитекторов породил Бездну — зону зараженного машинного кода. Вирусные структуры выжигают цифровые оболочки.",
            borderColor = ZzzHotMagenta
        )

        Spacer(modifier = Modifier.height(8.dp))

        ZzzLoreCard(
            tag = "МИССИЯ 03",
            title = "СТАТУС ОПЕРАТОРА",
            description = "Ты — Оператор. Твоя директива: совершать погружения в Нулевой Слой, ликвидировать угрозы, перековывать лут и расширять влияние в Сети.",
            borderColor = ZzzAcidYellow
        )
    }
}

@Composable
private fun ZzzNicknameStepContent(
    nickname: String,
    onNicknameChange: (String) -> Unit,
    onLoginClick: (() -> Unit)? = null
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = "КРИПТО-ПОЗЫВНОЙ ОПЕРАТОРА:",
            color = ZzzElectricCyan,
            fontSize = 12.sp,
            fontWeight = FontWeight.ExtraBold,
            fontFamily = FontFamily.SansSerif,
            letterSpacing = 1.sp
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = nickname,
            onValueChange = onNicknameChange,
            placeholder = { Text("Например: Phantom_X, Vector_01, Neuromancer", color = Color.Gray, fontSize = 13.sp) },
            leadingIcon = { Icon(Icons.Default.Person, contentDescription = null, tint = ZzzElectricCyan) },
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedBorderColor = ZzzElectricCyan,
                unfocusedBorderColor = Color.Gray.copy(alpha = 0.5f),
                cursorColor = ZzzElectricCyan,
                focusedContainerColor = ZzzDarkSurface,
                unfocusedContainerColor = ZzzDarkSurface
            ),
            shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true
        )

        Spacer(modifier = Modifier.height(10.dp))

        if (onLoginClick != null) {
            Button(
                onClick = onLoginClick,
                colors = ButtonDefaults.buttonColors(containerColor = ZzzElectricCyan.copy(alpha = 0.15f)),
                border = androidx.compose.foundation.BorderStroke(1.dp, ZzzElectricCyan),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "🔓 УЖЕ ЕСТЬ НЕЙРО-АККАУНТ? ВОЙТИ В СЕТЬ",
                    color = ZzzElectricCyan,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(10.dp))
        }

        Surface(
            color = ZzzDarkSurface,
            shape = CutCornerShape(6.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x3300FFF6)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = "ℹ️ ТЕРМИНАЛ РЕГИСТРАЦИИ:",
                    color = ZzzAcidYellow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Позывной фиксируется в криптографической матрице устройства и отображается в турнирных рейтингах и протоколах взлома.",
                    color = ZzzTextBody,
                    fontSize = 12.sp,
                    lineHeight = 18.sp
                )
            }
        }
    }
}

@Composable
private fun ZzzFactionStepContent(
    selectedFaction: String,
    onSelectFaction: (String) -> Unit,
    showSecretInput: Boolean,
    onToggleSecret: () -> Unit,
    secretCode: String,
    onSecretChange: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = "ВЫБЕРИТЕ СИНДИКАТ:",
            color = ZzzElectricCyan,
            fontSize = 12.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = 1.sp
        )

        Spacer(modifier = Modifier.height(8.dp))

        val factions = listOf(
            ZzzFactionData("МАТЕРИЯ", "ФИНАНСОВЫЙ КОНГЛОМЕРАТ", "Контроль ресурсов и удача", "+20% BioCoins во всех секторах\nПовышенный параметр LUCK\nСтарт: 1000 BioCoins", ZzzAcidYellow),
            ZzzFactionData("РАЗУМ", "ОБОРОННЫЙ АЛЬЯНС", "Абсолютная защита нейро-оболочки", "+15 DEF, снижение потерь Сигнала\nКомплект полевой реставрации", ZzzElectricCyan),
            ZzzFactionData("ТЕХНО", "ХАКЕРЫ НУЛЕВОГО СЛОЯ", "Агрессивный брутфорс и дешифрация", "+15 ATK, быстрый взлом кэшей\nШоковый набор и отмычки", ZzzHotMagenta)
        )

        factions.forEach { fact ->
            val isSelected = selectedFaction == fact.id
            Surface(
                onClick = { onSelectFaction(fact.id) },
                color = if (isSelected) fact.color.copy(alpha = 0.15f) else ZzzDarkSurface,
                shape = CutCornerShape(topStart = 8.dp, bottomEnd = 8.dp),
                border = androidx.compose.foundation.BorderStroke(
                    width = if (isSelected) 2.dp else 1.dp,
                    color = if (isSelected) fact.color else Color.Gray.copy(alpha = 0.3f)
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = isSelected,
                        onClick = { onSelectFaction(fact.id) },
                        colors = RadioButtonDefaults.colors(selectedColor = fact.color)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Column {
                        Text(
                            text = "${fact.id} // ${fact.subtitle}",
                            color = fact.color,
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 12.sp,
                            fontFamily = FontFamily.SansSerif
                        )
                        Text(
                            text = fact.perks,
                            color = ZzzTextBody,
                            fontSize = 11.sp,
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "⚡ Ввести мастер-ключ Архитектора?",
            color = Color.Gray,
            fontSize = 11.sp,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.clickable { onToggleSecret() }
        )

        if (showSecretInput) {
            OutlinedTextField(
                value = secretCode,
                onValueChange = onSecretChange,
                placeholder = { Text("Введите мастер-ключ...", color = Color.Gray, fontSize = 12.sp) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = ZzzHotMagenta,
                    unfocusedBorderColor = Color.Gray
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp),
                singleLine = true
            )
            if (selectedFaction == "АРХИТЕКТОРЫ") {
                Text(
                    text = "✓ РЕЖИМ АРХИТЕКТОРОВ АКТИВИРОВАН: Доступ к корневым протоколам (+25 к характеристикам)",
                    color = ZzzToxicGreen,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
        }
    }
}

@Composable
private fun ZzzGameplayDirectivesStepContent() {
    Column(modifier = Modifier.fillMaxWidth()) {
        ZzzDirectiveCard("⚔️", "1. ПОГРУЖЕНИЕ В БЕЗДНУ", "Глубина увеличивает ценность наград. При 0% Сигнала рейд провален. Эвакуируйтесь вовремя!")
        Spacer(modifier = Modifier.height(6.dp))
        ZzzDirectiveCard("🛠️", "2. КУЗНИЦА И МОДДИНГ", "Перековывайте характеристики, ремонтируйте износ и устанавливайте квантовые чипы.")
        Spacer(modifier = Modifier.height(6.dp))
        ZzzDirectiveCard("🔴🟢🔵", "3. РЕЗОНАНС СОКЕТОВ", "Красный (Урон), Зеленый (Защита), Синий (Энергия). Совпадение цвета сокета дает +25% резонанс.")
        Spacer(modifier = Modifier.height(6.dp))
        ZzzDirectiveCard("⚡", "4. СЕТЕВАЯ ВОЙНА (PvP)", "Дуэли на взлом: Брутфорс бьет Файрвол, Файрвол бьет Стелс, Стелс бьет Брутфорс.")
    }
}

@Composable
private fun ZzzStarterKitStepContent(
    nickname: String,
    faction: String
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Surface(
            color = ZzzDarkSurface,
            shape = CutCornerShape(8.dp),
            border = androidx.compose.foundation.BorderStroke(1.5.dp, ZzzElectricCyan),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "ГОТОВНОСТЬ К ПОГРУЖЕНИЮ",
                    color = ZzzElectricCyan,
                    fontWeight = FontWeight.ExtraBold,
                    fontSize = 14.sp,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(8.dp))

                Text("• Оператор: ${if (nickname.isBlank()) "Аноним" else nickname}", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Text("• Синдикат: $faction", color = ZzzAcidYellow, fontSize = 12.sp, fontWeight = FontWeight.Bold)

                Spacer(modifier = Modifier.height(10.dp))
                HorizontalDivider(color = Color(0x3300FFF6))
                Spacer(modifier = Modifier.height(10.dp))

                Text("СТАРТОВЫЙ БУФЕР СНАБЖЕНИЯ:", color = ZzzHotMagenta, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                Text("• Экипированное оружие & броня фракции", color = ZzzTextBody, fontSize = 12.sp)
                Text("• Ремкомплекты и нано-аптечки (5х)", color = ZzzTextBody, fontSize = 12.sp)
                Text("• Стартовый грант BioCoins в кошельке", color = ZzzTextBody, fontSize = 12.sp)
            }
        }
    }
}

// ==================== ZZZ LORE & DIRECTIVE HELPER CARDS ====================

@Composable
private fun ZzzLoreCard(
    tag: String,
    title: String,
    description: String,
    borderColor: Color
) {
    Surface(
        color = ZzzDarkSurface,
        shape = CutCornerShape(topStart = 6.dp, bottomEnd = 6.dp),
        border = androidx.compose.foundation.BorderStroke(1.5.dp, borderColor),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    color = borderColor,
                    shape = CutCornerShape(2.dp)
                ) {
                    Text(
                        text = " $tag ",
                        color = Color.Black,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(vertical = 1.dp)
                    )
                }
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = title,
                    color = borderColor,
                    fontWeight = FontWeight.ExtraBold,
                    fontSize = 12.sp,
                    letterSpacing = 0.5.sp
                )
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = description,
                color = ZzzTextBody,
                fontSize = 12.sp,
                lineHeight = 17.sp
            )
        }
    }
}

@Composable
private fun ZzzDirectiveCard(
    icon: String,
    title: String,
    description: String
) {
    Surface(
        color = ZzzDarkSurface,
        shape = CutCornerShape(6.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x4400FFF6)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(10.dp),
            verticalAlignment = Alignment.Top
        ) {
            Text(icon, fontSize = 18.sp, modifier = Modifier.padding(end = 8.dp, top = 2.dp))
            Column {
                Text(title, color = ZzzElectricCyan, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                Spacer(modifier = Modifier.height(2.dp))
                Text(description, color = ZzzTextBody, fontSize = 11.5.sp, lineHeight = 16.sp)
            }
        }
    }
}

@OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
private fun LogoVideoIntro(
    onFinish: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val logoResId = remember {
        context.resources.getIdentifier("logo", "raw", context.packageName)
    }

    val exoPlayer = remember(logoResId) {
        if (logoResId == 0) null
        else {
            try {
                ExoPlayer.Builder(context).build().apply {
                    val videoUri = android.net.Uri.parse("android.resource://" + context.packageName + "/" + logoResId)
                    setMediaItem(MediaItem.fromUri(videoUri))
                    repeatMode = Player.REPEAT_MODE_OFF
                    videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING
                    prepare()
                    playWhenReady = true
                    volume = 1.0f
                }
            } catch (e: Throwable) {
                null
            }
        }
    }

    LaunchedEffect(exoPlayer) {
        if (exoPlayer == null) {
            onFinish()
            return@LaunchedEffect
        }
        exoPlayer.addListener(object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) {
                    onFinish()
                }
            }
            override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                onFinish()
            }
        })
    }

    DisposableEffect(exoPlayer, lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> exoPlayer?.play()
                Lifecycle.Event.ON_PAUSE -> exoPlayer?.pause()
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            try {
                exoPlayer?.stop()
                exoPlayer?.release()
            } catch (_: Throwable) {}
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        if (exoPlayer != null) {
            AndroidView(
                factory = { ctx ->
                    PlayerView(ctx).apply {
                        player = exoPlayer
                        useController = false
                        resizeMode = AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                        layoutParams = FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        )
                    }
                },
                modifier = Modifier.fillMaxSize()
            )
        }

        // Skip button overlay
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            contentAlignment = Alignment.TopEnd
        ) {
            Surface(
                onClick = onFinish,
                color = Color.Black.copy(alpha = 0.75f),
                shape = CutCornerShape(6.dp),
                border = androidx.compose.foundation.BorderStroke(1.5.dp, ZzzElectricCyan)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "ПРОПУСТИТЬ",
                        color = ZzzElectricCyan,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.SansSerif
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "⏩",
                        fontSize = 12.sp
                    )
                }
            }
        }
    }
}

private data class ZzzFactionData(
    val id: String,
    val subtitle: String,
    val simpleGoal: String,
    val perks: String,
    val color: Color
)
