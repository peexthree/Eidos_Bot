package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * ⚛️ 5. COMPOSE CANVAS PARTICLE SYSTEM ENGINE
 * High-speed 60/120 FPS particle canvas renderer for Forge Craft Sparks, Abyss Cyber Dust, and Evacuation Vortex.
 */

enum class ParticlePreset {
    ABYSS_DUST,
    FORGE_SPARKS,
    EVACUATION_VORTEX,
    NEON_STORM
}

private data class CyberParticle(
    var x: Float,
    var y: Float,
    var vx: Float,
    var vy: Float,
    var radius: Float,
    var alpha: Float,
    var color: Color,
    var life: Float,
    var maxLife: Float
)

@Composable
fun CyberParticleOverlay(
    preset: ParticlePreset = ParticlePreset.ABYSS_DUST,
    particleCount: Int = 35,
    modifier: Modifier = Modifier
) {
    val particles = remember(preset, particleCount) {
        ArrayList<CyberParticle>(particleCount).apply {
            repeat(particleCount) {
                add(createParticle(preset, 500f, 800f))
            }
        }
    }

    var frameState by remember { mutableLongStateOf(0L) }
    var lastFrameTimeNanos by remember { mutableLongStateOf(0L) }

    LaunchedEffect(preset, particleCount) {
        while (true) {
            withFrameNanos { frameTime ->
                if (lastFrameTimeNanos != 0L) {
                    val dt = ((frameTime - lastFrameTimeNanos) / 1_000_000_000f).coerceIn(0.001f, 0.05f)
                    
                    for (i in 0 until particles.size) {
                        val p = particles[i]
                        p.life += dt
                        if (p.life >= p.maxLife) {
                            particles[i] = createParticle(preset, 1000f, 1000f)
                        } else {
                            p.x += p.vx * dt * 60f
                            p.y += p.vy * dt * 60f
                            p.alpha = (1f - (p.life / p.maxLife)).coerceIn(0f, 1f)
                        }
                    }
                }
                lastFrameTimeNanos = frameTime
                frameState = frameTime
            }
        }
    }

    Canvas(modifier = modifier.fillMaxSize()) {
        // Reading frameState causes draw phase invalidation only without Composable recomposition
        @Suppress("UNUSED_VARIABLE")
        val currentFrame = frameState
        val width = size.width
        val height = size.height

        for (i in 0 until particles.size) {
            val p = particles[i]
            drawCircle(
                color = p.color.copy(alpha = p.alpha),
                radius = p.radius,
                center = Offset(p.x.coerceIn(0f, width), p.y.coerceIn(0f, height))
            )
        }
    }
}

private fun createParticle(preset: ParticlePreset, width: Float, height: Float): CyberParticle {
    val rng = Random
    return when (preset) {
        ParticlePreset.ABYSS_DUST -> {
            CyberParticle(
                x = rng.nextFloat() * width,
                y = rng.nextFloat() * height,
                vx = (rng.nextFloat() - 0.5f) * 0.8f,
                vy = -rng.nextFloat() * 1.5f - 0.5f,
                radius = rng.nextFloat() * 3f + 1f,
                alpha = rng.nextFloat() * 0.7f + 0.2f,
                color = if (rng.nextBoolean()) EidosCyan else EidosNeon,
                life = 0f,
                maxLife = rng.nextFloat() * 4f + 2f
            )
        }
        ParticlePreset.FORGE_SPARKS -> {
            val angle = rng.nextFloat() * Math.PI.toFloat() * 2f
            val speed = rng.nextFloat() * 4f + 2f
            CyberParticle(
                x = width / 2f,
                y = height / 2f,
                vx = cos(angle) * speed,
                vy = sin(angle) * speed - 2f,
                radius = rng.nextFloat() * 4f + 2f,
                alpha = 1f,
                color = if (rng.nextBoolean()) Color.Yellow else EidosRed,
                life = 0f,
                maxLife = rng.nextFloat() * 1.5f + 0.5f
            )
        }
        ParticlePreset.EVACUATION_VORTEX -> {
            val angle = rng.nextFloat() * Math.PI.toFloat() * 2f
            val radius = rng.nextFloat() * 180f + 50f
            CyberParticle(
                x = width / 2f + cos(angle) * radius,
                y = height / 2f + sin(angle) * radius,
                vx = -cos(angle) * 2f,
                vy = -sin(angle) * 2f,
                radius = rng.nextFloat() * 4f + 1.5f,
                alpha = 0.8f,
                color = EidosCyan,
                life = 0f,
                maxLife = rng.nextFloat() * 2f + 1f
            )
        }
        ParticlePreset.NEON_STORM -> {
            CyberParticle(
                x = rng.nextFloat() * width,
                y = height + 50f,
                vx = (rng.nextFloat() - 0.5f) * 2f,
                vy = -rng.nextFloat() * 8f - 4f,
                radius = rng.nextFloat() * 2f + 1f,
                alpha = 0.9f,
                color = EidosCyan,
                life = 0f,
                maxLife = rng.nextFloat() * 2f + 1f
            )
        }
    }
}
