package com.example.eidos.ui.screens

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
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
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.example.eidos.R
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosNeon

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
fun SplashScreen(onFinish: () -> Unit) {
    val context = LocalContext.current
    var isSkipped by remember { mutableStateOf(false) }

    fun completeIntro() {
        if (!isSkipped) {
            isSkipped = true
            onFinish()
        }
    }

    val introResId = remember {
        val direct = context.resources.getIdentifier("intro", "raw", context.packageName)
        if (direct != 0) direct else context.resources.getIdentifier("INTRO", "raw", context.packageName)
    }

    val exoPlayer = remember(introResId) {
        if (introResId == 0) {
            null
        } else {
            try {
                ExoPlayer.Builder(context).build().apply {
                    val uri = android.net.Uri.parse("android.resource://${context.packageName}/$introResId")
                    val mediaItem = MediaItem.fromUri(uri)
                    setMediaItem(mediaItem)
                    repeatMode = Player.REPEAT_MODE_OFF
                    videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING
                    volume = 1.0f // Maintain native intro video audio without external music
                    playWhenReady = true

                    addListener(object : Player.Listener {
                        override fun onPlaybackStateChanged(playbackState: Int) {
                            if (playbackState == Player.STATE_ENDED) {
                                completeIntro()
                            }
                        }

                        override fun onPlayerError(error: PlaybackException) {
                            completeIntro()
                        }
                    })

                    prepare()
                }
            } catch (_: Throwable) {
                null
            }
        }
    }

    DisposableEffect(exoPlayer) {
        onDispose {
            exoPlayer?.stop()
            exoPlayer?.release()
        }
    }

    // Fallback if video resource is missing
    LaunchedEffect(exoPlayer) {
        if (exoPlayer == null) {
            completeIntro()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null
            ) {
                completeIntro()
            }
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

        // Tap to Skip Prompt Button in bottom-right corner
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            contentAlignment = Alignment.BottomEnd
        ) {
            Surface(
                color = Color.Black.copy(alpha = 0.65f),
                border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.8f)),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.clickable { completeIntro() }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "ПРОПУСТИТЬ [TAP TO SKIP]",
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = "Пропустить заставку",
                        tint = EidosNeon,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
        }
    }
}

