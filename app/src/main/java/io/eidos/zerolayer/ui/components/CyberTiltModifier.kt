package io.eidos.zerolayer.ui.components

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext

/**
 * 📳 2. DYNAMIC GYROSCOPIC 3D PARALLAX MODIFIER
 * High-performance shared gyroscope sensor manager for Compose cards and HUDs.
 */
class SharedGyroscopeSensor private constructor(context: Context) : SensorEventListener {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val sensor = sensorManager?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
        ?: sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

    var pitch: Float by mutableFloatStateOf(0f)
        private set
    var roll: Float by mutableFloatStateOf(0f)
        private set

    private var activeSubscribers = 0

    fun start() {
        if (activeSubscribers++ == 0 && sensor != null) {
            sensorManager?.registerListener(this, sensor, SensorManager.SENSOR_DELAY_UI)
        }
    }

    fun stop() {
        if (--activeSubscribers <= 0) {
            activeSubscribers = 0
            sensorManager?.unregisterListener(this)
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_ROTATION_VECTOR) {
            val rotationMatrix = FloatArray(9)
            SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values)
            val orientation = FloatArray(3)
            SensorManager.getOrientation(rotationMatrix, orientation)
            pitch = (Math.toDegrees(orientation[1].toDouble()).toFloat() / 35f).coerceIn(-1f, 1f)
            roll = (Math.toDegrees(orientation[2].toDouble()).toFloat() / 35f).coerceIn(-1f, 1f)
        } else if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            val x = event.values[0] / 9.81f
            val y = event.values[1] / 9.81f
            pitch = y.coerceIn(-1f, 1f)
            roll = (-x).coerceIn(-1f, 1f)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    companion object {
        @Volatile
        private var instance: SharedGyroscopeSensor? = null

        fun get(context: Context): SharedGyroscopeSensor {
            return instance ?: synchronized(this) {
                instance ?: SharedGyroscopeSensor(context.applicationContext).also { instance = it }
            }
        }
    }
}

@Composable
fun rememberGyroscopeTilt(): State<Pair<Float, Float>> {
    val context = LocalContext.current
    val gyro = remember { SharedGyroscopeSensor.get(context) }
    DisposableEffect(gyro) {
        gyro.start()
        onDispose { gyro.stop() }
    }
    return remember(gyro) {
        derivedStateOf { gyro.pitch to gyro.roll }
    }
}

/**
 * 3D Tilt Modifier executing in Compose graphicsLayer (Draw Phase)
 * to avoid recomposing the parent composable tree.
 */
fun Modifier.cyber3DTilt(
    enabled: Boolean = true,
    maxRotationDegrees: Float = 8f,
    depthTranslationDp: Float = 15f
): Modifier = composed {
    if (!enabled) return@composed this

    val context = LocalContext.current
    val gyro = remember { SharedGyroscopeSensor.get(context) }

    DisposableEffect(gyro) {
        gyro.start()
        onDispose { gyro.stop() }
    }

    this.graphicsLayer {
        this.rotationX = gyro.pitch * maxRotationDegrees
        this.rotationY = gyro.roll * maxRotationDegrees
        this.translationX = gyro.roll * depthTranslationDp
        this.translationY = gyro.pitch * depthTranslationDp
        this.cameraDistance = 16f * density
    }
}
