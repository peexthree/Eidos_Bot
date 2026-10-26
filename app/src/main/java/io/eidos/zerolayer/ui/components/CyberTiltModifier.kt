package io.eidos.zerolayer.ui.components

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.launch

/**
 * 📳 2. DYNAMIC GYROSCOPIC 3D PARALLAX MODIFIER
 * Reads device tilt sensors and applies real-time 3D rotation and depth translation to Compose cards and HUDs.
 */

@Composable
fun rememberGyroscopeTilt(): State<Pair<Float, Float>> {
    val context = LocalContext.current
    val tiltState = remember { mutableStateOf(0f to 0f) }

    DisposableEffect(context) {
        val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
        val sensor = sensorManager?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
            ?: sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        if (sensor == null) {
            return@DisposableEffect onDispose { }
        }

        val listener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                if (event.sensor.type == Sensor.TYPE_ROTATION_VECTOR) {
                    val rotationMatrix = FloatArray(9)
                    SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values)
                    val orientation = FloatArray(3)
                    SensorManager.getOrientation(rotationMatrix, orientation)
                    // Azimuth, Pitch, Roll
                    val pitch = Math.toDegrees(orientation[1].toDouble()).toFloat()
                    val roll = Math.toDegrees(orientation[2].toDouble()).toFloat()
                    tiltState.value = (pitch / 45f).coerceIn(-1f, 1f) to (roll / 45f).coerceIn(-1f, 1f)
                } else if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
                    val x = event.values[0] / 9.81f
                    val y = event.values[1] / 9.81f
                    tiltState.value = y.coerceIn(-1f, 1f) to (-x).coerceIn(-1f, 1f)
                }
            }

            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }

        sensorManager?.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_GAME)

        onDispose {
            sensorManager?.unregisterListener(listener)
        }
    }

    return tiltState
}

fun Modifier.cyber3DTilt(
    enabled: Boolean = true,
    maxRotationDegrees: Float = 10f,
    depthTranslationDp: Float = 15f
): Modifier = composed {
    if (!enabled) return@composed this

    val tiltState = rememberGyroscopeTilt()
    val (pitch, roll) = tiltState.value

    val rotationX = remember { Animatable(0f) }
    val rotationY = remember { Animatable(0f) }
    val translationX = remember { Animatable(0f) }
    val translationY = remember { Animatable(0f) }

    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(pitch, roll) {
        coroutineScope.launch {
            rotationX.animateTo(
                targetValue = pitch * maxRotationDegrees,
                animationSpec = spring(stiffness = Spring.StiffnessLow, dampingRatio = Spring.DampingRatioMediumBouncy)
            )
        }
        coroutineScope.launch {
            rotationY.animateTo(
                targetValue = roll * maxRotationDegrees,
                animationSpec = spring(stiffness = Spring.StiffnessLow, dampingRatio = Spring.DampingRatioMediumBouncy)
            )
        }
        coroutineScope.launch {
            translationX.animateTo(
                targetValue = roll * depthTranslationDp,
                animationSpec = spring(stiffness = Spring.StiffnessLow, dampingRatio = Spring.DampingRatioMediumBouncy)
            )
        }
        coroutineScope.launch {
            translationY.animateTo(
                targetValue = pitch * depthTranslationDp,
                animationSpec = spring(stiffness = Spring.StiffnessLow, dampingRatio = Spring.DampingRatioMediumBouncy)
            )
        }
    }

    this.graphicsLayer {
        this.rotationX = rotationX.value
        this.rotationY = rotationY.value
        this.translationX = translationX.value
        this.translationY = translationY.value
        this.cameraDistance = 16f * density
    }
}
