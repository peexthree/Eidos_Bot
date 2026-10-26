package com.example.eidos.ui.components

import android.graphics.RuntimeShader
import android.os.Build
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosNeon
import com.example.eidos.ui.theme.EidosRed
import kotlin.random.Random

/**
 * 🌌 1. PROCEDURAL AGSL / CANVAS GLITCH SHADER ENGINE
 * High-performance AGSL RuntimeShader for Android 13+ with procedural Compose Canvas fallback.
 */

private const val AGSL_GLITCH_SRC = """
    uniform shader composable;
    uniform float2 resolution;
    uniform float time;
    uniform float glitchIntensity;

    half4 main(float2 fragCoord) {
        float2 uv = fragCoord / resolution;
        
        // Scanlines
        float scanline = sin(uv.y * 800.0 + time * 10.0) * 0.04 * glitchIntensity;
        
        // Chromatic Aberration offset
        float shift = (sin(time * 20.0 + uv.y * 50.0) * 0.008) * glitchIntensity;
        
        half4 colorRed = composable.eval(fragCoord + float2(shift * resolution.x, 0.0));
        half4 colorGreen = composable.eval(fragCoord);
        half4 colorBlue = composable.eval(fragCoord - float2(shift * resolution.x, 0.0));
        
        half4 result = half4(colorRed.r, colorGreen.g, colorBlue.b, colorGreen.a);
        result.rgb -= scanline;
        
        return result;
    }
"""

fun Modifier.cyberGlitchEffect(
    glitchIntensity: Float = 0.5f,
    enabled: Boolean = true
): Modifier = if (!enabled || glitchIntensity <= 0f) this else graphicsLayer {
    clip = false
}.then(
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        Modifier.drawWithCache {
            var shaderBrush: ShaderBrush? = null
            var runtimeShader: RuntimeShader? = null
            try {
                val shader = RuntimeShader(AGSL_GLITCH_SRC)
                runtimeShader = shader
                shaderBrush = ShaderBrush(shader)
            } catch (_: Throwable) {}

            onDrawWithContent {
                val shader = runtimeShader
                if (shader != null) {
                    try {
                        shader.setFloatUniform("resolution", size.width, size.height)
                        shader.setFloatUniform("time", (System.currentTimeMillis() % 1000000) / 1000f)
                        shader.setFloatUniform("glitchIntensity", glitchIntensity)
                    } catch (_: Throwable) {}
                }
                drawContent()
            }
        }
    } else {
        Modifier
    }
)

@Composable
fun CyberGlitchOverlay(
    intensity: Float = 0.5f,
    modifier: Modifier = Modifier
) {
    if (intensity <= 0f) return

    val infiniteTransition = rememberInfiniteTransition(label = "glitch")
    val timeStep by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 100f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "glitchTime"
    )

    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height

        // 1. CRT Scanlines (Optimized spacing for high DPI & mobile GPUs)
        val lineSpacing = 16f
        var y = 0f
        while (y < height) {
            drawLine(
                color = Color.Black.copy(alpha = 0.12f * intensity),
                start = Offset(0f, y),
                end = Offset(width, y),
                strokeWidth = 3f
            )
            y += lineSpacing
        }

        // 2. Random Glitch Slices
        val random = Random((timeStep * 10).toInt())
        if (random.nextFloat() < 0.4f * intensity) {
            val glitchY = random.nextFloat() * height
            val glitchHeight = random.nextFloat() * 20f + 5f
            val offsetX = (random.nextFloat() - 0.5f) * 30f * intensity

            drawRect(
                color = if (random.nextBoolean()) EidosRed.copy(alpha = 0.25f * intensity) else EidosCyan.copy(alpha = 0.25f * intensity),
                topLeft = Offset(offsetX, glitchY),
                size = androidx.compose.ui.geometry.Size(width, glitchHeight)
            )
        }
    }
}
