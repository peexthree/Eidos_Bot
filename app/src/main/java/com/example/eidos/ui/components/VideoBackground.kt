package com.example.eidos.ui.components

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.annotation.OptIn
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView

@OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
fun VideoBackground(
    resId: Int = 0,
    resName: String? = null,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var isPlayerError by remember { mutableStateOf(false) }

    val resolvedResId = remember(resId, resName) {
        if (resId != 0) resId
        else if (!resName.isNullOrBlank()) {
            context.resources.getIdentifier(resName, "raw", context.packageName)
        } else 0
    }

    val exoPlayer = remember(resolvedResId) {
        if (resolvedResId == 0) {
            isPlayerError = true
            null
        } else {
            try {
                ExoPlayer.Builder(context).build().apply {
                    addListener(object : Player.Listener {
                        override fun onPlayerError(error: androidx.media3.common.PlaybackException) {
                            isPlayerError = true
                        }
                    })
                    val videoUri = android.net.Uri.parse("android.resource://" + context.packageName + "/" + resolvedResId)
                    val mediaItem = MediaItem.fromUri(videoUri)
                    setMediaItem(mediaItem)
                    trackSelectionParameters = trackSelectionParameters
                        .buildUpon()
                        .setTrackTypeDisabled(C.TRACK_TYPE_AUDIO, true)
                        .build()
                    repeatMode = Player.REPEAT_MODE_ALL
                    videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING
                    prepare()
                    playWhenReady = true
                    volume = 0f // Backgrounds should be silent
                }
            } catch (e: Throwable) {
                isPlayerError = true
                null
            }
        }
    }

    DisposableEffect(exoPlayer, lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> {
                    exoPlayer?.play()
                }
                Lifecycle.Event.ON_PAUSE -> {
                    exoPlayer?.pause()
                }
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            try {
                exoPlayer?.stop()
                exoPlayer?.release()
            } catch (e: Throwable) {
                // Ignore release errors
            }
        }
    }

    if (isPlayerError || exoPlayer == null) {
        // High-end animated cybernetic gradient fallback to guarantee crash-free performance
        val infiniteTransition = rememberInfiniteTransition(label = "cyber_bg_pulse")
        val pulseAlpha by infiniteTransition.animateFloat(
            initialValue = 0.3f,
            targetValue = 0.7f,
            animationSpec = infiniteRepeatable(
                animation = tween(2000, easing = LinearEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "pulseAlpha"
        )
        Box(
            modifier = modifier
                .background(
                    androidx.compose.ui.graphics.Brush.verticalGradient(
                        colors = listOf(
                            Color(0xFF02020A),
                            Color(0xFF0D1127).copy(alpha = pulseAlpha),
                            Color(0xFF03030F)
                        )
                    )
                )
        )
    } else {
        AndroidView(
            factory = { ctx ->
                try {
                    PlayerView(ctx).apply {
                        useController = false
                        resizeMode = AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                        player = exoPlayer
                        layoutParams = FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        )
                    }
                } catch (e: Throwable) {
                    FrameLayout(ctx).apply {
                        setBackgroundColor(android.graphics.Color.BLACK)
                    }
                }
            },
            update = { playerView ->
                if (playerView is PlayerView && playerView.player != exoPlayer) {
                    playerView.player = exoPlayer
                }
            },
            modifier = modifier
        )
    }
}
