package io.eidos.zerolayer.ui.utils

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.SoundPool
import android.os.Build
import android.util.Log
import io.eidos.zerolayer.R
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import kotlin.math.sin

class EidosAudioManager private constructor(private val context: Context) {

    private val prefs = context.getSharedPreferences("eidos_audio_prefs", Context.MODE_PRIVATE)
    private val systemAudioManager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager

    private var soundPool: SoundPool? = null
    private val soundMap = HashMap<SoundType, Int>()

    private var audioFocusRequest: AudioFocusRequest? = null
    private var hasAudioFocus = false
    private var resumeOnFocusGain = false

    private val focusChangeListener = AudioManager.OnAudioFocusChangeListener { focusChange ->
        when (focusChange) {
            AudioManager.AUDIOFOCUS_LOSS -> {
                // Permanent loss of audio focus (e.g. another media app started)
                hasAudioFocus = false
                resumeOnFocusGain = false
                pauseMusic()
            }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> {
                // Temporary loss (e.g. phone call, incoming ringtone, voice message)
                hasAudioFocus = false
                if (mediaPlayer?.isPlaying == true) {
                    resumeOnFocusGain = true
                    pauseMusic()
                }
            }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK -> {
                // Notification, navigation ping -> lower volume
                duckMusic(true)
            }
            AudioManager.AUDIOFOCUS_GAIN -> {
                // Regained focus
                hasAudioFocus = true
                duckMusic(false)
                if (resumeOnFocusGain) {
                    resumeOnFocusGain = false
                    resumeMusic()
                }
            }
        }
    }

    private fun requestAudioFocus(): Boolean {
        if (hasAudioFocus) return true
        val am = systemAudioManager ?: return true

        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val playbackAttributes = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                .build()

            val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(playbackAttributes)
                .setAcceptsDelayedFocusGain(false)
                .setOnAudioFocusChangeListener(focusChangeListener)
                .build()

            audioFocusRequest = request
            val res = am.requestAudioFocus(request)
            hasAudioFocus = (res == AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
            hasAudioFocus
        } else {
            @Suppress("DEPRECATION")
            val res = am.requestAudioFocus(
                focusChangeListener,
                AudioManager.STREAM_MUSIC,
                AudioManager.AUDIOFOCUS_GAIN
            )
            hasAudioFocus = (res == AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
            hasAudioFocus
        }
    }

    private fun abandonAudioFocus() {
        val am = systemAudioManager ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            audioFocusRequest?.let { am.abandonAudioFocusRequest(it) }
        } else {
            @Suppress("DEPRECATION")
            am.abandonAudioFocus(focusChangeListener)
        }
        hasAudioFocus = false
        resumeOnFocusGain = false
    }

    var isSoundEnabled: Boolean
        get() = prefs.getBoolean("sound_enabled", true)
        set(value) = prefs.edit().putBoolean("sound_enabled", value).apply()

    var isMusicEnabled: Boolean
        get() = prefs.getBoolean("music_enabled", true)
        set(value) {
            prefs.edit().putBoolean("music_enabled", value).apply()
            if (!value) {
                pauseMusic()
            } else {
                if (currentTrack != BgmTrack.NONE) {
                    playBgm(currentTrack)
                }
            }
        }

    var musicVolume: Float
        get() = prefs.getFloat("music_volume", 0.7f)
        set(value) {
            val clamped = value.coerceIn(0f, 1f)
            prefs.edit().putFloat("music_volume", clamped).apply()
            try {
                mediaPlayer?.setVolume(clamped, clamped)
            } catch (e: Exception) {
                Log.e("EidosAudio", "Error setting volume", e)
            }
        }

    var effectsVolume: Float
        get() = prefs.getFloat("effects_volume", 0.8f)
        set(value) {
            val clamped = value.coerceIn(0f, 1f)
            prefs.edit().putFloat("effects_volume", clamped).apply()
        }

    enum class SoundType {
        CLICK_CYBER,
        RAID_STEP,
        CRITICAL_STRIKE,
        GLITCH_FOUND,
        HACK_SUCCESS,
        EVAC_WARNING,
        ITEM_CRAFT,
        ERROR_GLITCH,
        ABILITY_ACTIVATE,
        RELIC_UNLOCK,
        TUTORIAL_STEP,
        BOSS_VICTORY,
        ITEM_LOOT,
        DAMAGE_TAKEN,
        DANGER,
        LEVEL_UP
    }

    enum class BgmTrack {
        NONE,
        MAIN_MENU,
        ZERO_LAYER
    }

    private var mediaPlayer: MediaPlayer? = null
    private var currentTrack: BgmTrack = BgmTrack.NONE
    private var isPausedForBackground: Boolean = false

    private val playlist = listOf(
        R.raw.bgm_epic_cinematic,
        R.raw.bgm_genesis,
        R.raw.bgm_mirror_of_lies
    )
    private var currentPlaylistIndex = 0

    init {
        initSoundPool()
    }

    fun playBgm(track: BgmTrack) {
        if (track == BgmTrack.NONE) {
            stopMusic()
            currentTrack = BgmTrack.NONE
            return
        }

        if (currentTrack == track && mediaPlayer != null && (mediaPlayer?.isPlaying == true || isPausedForBackground)) {
            return
        }

        currentTrack = track

        if (!isMusicEnabled) {
            stopMusic()
            return
        }

        when (track) {
            BgmTrack.MAIN_MENU -> playPlaylistTrack(currentPlaylistIndex)
            BgmTrack.ZERO_LAYER -> playSingleTrack(R.raw.bgm_genesis, loop = true)
            else -> stopMusic()
        }
    }

    fun skipToNextTrack() {
        if (!isMusicEnabled) return
        currentPlaylistIndex = (currentPlaylistIndex + 1) % playlist.size
        playPlaylistTrack(currentPlaylistIndex)
    }

    private var isDucked: Boolean = false

    fun duckMusic(ducked: Boolean) {
        isDucked = ducked
        val vol = if (isDucked) musicVolume * 0.15f else musicVolume
        try {
            mediaPlayer?.setVolume(vol, vol)
        } catch (e: Exception) {
            Log.e("EidosAudio", "Error setting ducked volume", e)
        }
    }

    private fun playPlaylistTrack(index: Int) {
        if (!isMusicEnabled) return
        requestAudioFocus()
        val safeIndex = if (index in playlist.indices) index else 0
        currentPlaylistIndex = safeIndex
        val resId = playlist[safeIndex]
        try {
            stopMusic()
            mediaPlayer = MediaPlayer.create(context, resId)?.apply {
                isLooping = false
                val vol = if (isDucked) musicVolume * 0.15f else musicVolume
                setVolume(vol, vol)
                setOnErrorListener { mp, what, extra ->
                    Log.w("EidosAudio", "MediaPlayer error in playlist: what=$what extra=$extra")
                    try { mp.reset() } catch (_: Throwable) {}
                    true
                }
                setOnCompletionListener {
                    if (isMusicEnabled && currentTrack == BgmTrack.MAIN_MENU) {
                        currentPlaylistIndex = (currentPlaylistIndex + 1) % playlist.size
                        playPlaylistTrack(currentPlaylistIndex)
                    }
                }
                start()
            }
            isPausedForBackground = false
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error playing playlist track index $safeIndex", e)
            mediaPlayer = null
        }
    }

    private fun playSingleTrack(resId: Int, loop: Boolean) {
        if (!isMusicEnabled) return
        requestAudioFocus()
        try {
            stopMusic()
            mediaPlayer = MediaPlayer.create(context, resId)?.apply {
                isLooping = loop
                val vol = if (isDucked) musicVolume * 0.15f else musicVolume
                setVolume(vol, vol)
                setOnErrorListener { mp, what, extra ->
                    Log.w("EidosAudio", "MediaPlayer error in single track: what=$what extra=$extra")
                    try { mp.reset() } catch (_: Throwable) {}
                    true
                }
                setOnCompletionListener {
                    if (!loop && isMusicEnabled) {
                        skipToNextTrack()
                    }
                }
                start()
            }
            isPausedForBackground = false
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error playing track $resId", e)
            mediaPlayer = null
        }
    }

    fun pauseMusic() {
        try {
            if (mediaPlayer?.isPlaying == true) {
                mediaPlayer?.pause()
                isPausedForBackground = true
            }
        } catch (e: Exception) {
            Log.e("EidosAudio", "Error pausing BGM", e)
        }
    }

    fun resumeMusic() {
        if (!isMusicEnabled) return
        requestAudioFocus()
        try {
            if (isPausedForBackground && mediaPlayer != null) {
                mediaPlayer?.start()
                isPausedForBackground = false
            } else if (currentTrack != BgmTrack.NONE && mediaPlayer == null) {
                playBgm(currentTrack)
            }
        } catch (e: Exception) {
            Log.e("EidosAudio", "Error resuming BGM", e)
        }
    }

    fun stopMusic() {
        try {
            if (mediaPlayer?.isPlaying == true) {
                mediaPlayer?.stop()
            }
            mediaPlayer?.reset()
            mediaPlayer?.release()
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error stopping BGM", e)
        } finally {
            mediaPlayer = null
            abandonAudioFocus()
        }
    }

    fun getCurrentTrack(): BgmTrack = currentTrack

    private fun initSoundPool() {
        try {
            val audioAttributes = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build()

            soundPool = SoundPool.Builder()
                .setMaxStreams(8)
                .setAudioAttributes(audioAttributes)
                .build()

            generateAndLoadCyberSounds()
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Failed to initialize SoundPool", e)
        }
    }

    private fun generateAndLoadCyberSounds() {
        try {
            val cacheDir = context.cacheDir ?: return
            val soundsToGenerate = listOf(
                SoundType.CLICK_CYBER to createPcmWav(cacheDir, "click_cyber.wav") { sampleIndex, totalSamples, sampleRate ->
                    val freq = 1200.0 - (sampleIndex.toDouble() / totalSamples) * 400.0
                    val env = 1.0 - (sampleIndex.toDouble() / totalSamples)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.7 * env).toFloat()
                },
                SoundType.RAID_STEP to createPcmWav(cacheDir, "raid_step.wav", durationMs = 80) { sampleIndex, totalSamples, sampleRate ->
                    val freq = 150.0 - (sampleIndex.toDouble() / totalSamples) * 80.0
                    val env = Math.pow(1.0 - (sampleIndex.toDouble() / totalSamples), 2.0)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.9 * env).toFloat()
                },
                SoundType.CRITICAL_STRIKE to createPcmWav(cacheDir, "critical_strike.wav", durationMs = 200) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 800.0 * Math.exp(-t * 3.0) + 120.0
                    val sub = sin(2.0 * Math.PI * (freq * 0.5) * sampleIndex / sampleRate)
                    val main = sin(2.0 * Math.PI * freq * sampleIndex / sampleRate)
                    val noise = (Math.random() * 2.0 - 1.0) * 0.2
                    val env = 1.0 - t
                    ((main * 0.6 + sub * 0.3 + noise) * env).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.GLITCH_FOUND to createPcmWav(cacheDir, "glitch_found.wav", durationMs = 250) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val step = (t * 8).toInt()
                    val freq = when (step % 4) {
                        0 -> 440.0
                        1 -> 880.0
                        2 -> 660.0
                        else -> 1320.0
                    }
                    val env = 1.0 - (t % 0.125) / 0.125
                    val squareWave = if (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) > 0) 0.5f else -0.5f
                    (squareWave * env * (1.0 - t)).toFloat()
                },
                SoundType.HACK_SUCCESS to createPcmWav(cacheDir, "hack_success.wav", durationMs = 300) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 523.25 + t * 523.25 // C5 to C6 sweep
                    val env = Math.sin(t * Math.PI)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.8 * env).toFloat()
                },
                SoundType.EVAC_WARNING to createPcmWav(cacheDir, "evac_warning.wav", durationMs = 350) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val pulse = sin(2.0 * Math.PI * 12.0 * t) // 12Hz pulse
                    val freq = 900.0 + (if (pulse > 0) 200.0 else 0.0)
                    val env = 1.0 - t * 0.3
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.8 * env).toFloat()
                },
                SoundType.ITEM_CRAFT to createPcmWav(cacheDir, "item_craft.wav", durationMs = 280) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 300.0 + t * 900.0
                    val env = sin(t * Math.PI)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.7 * env).toFloat()
                },
                SoundType.ERROR_GLITCH to createPcmWav(cacheDir, "error_glitch.wav", durationMs = 200) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 180.0 - t * 80.0
                    val noise = (Math.random() * 2.0 - 1.0) * 0.4
                    val env = 1.0 - t
                    ((sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.6 + noise) * env).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.ABILITY_ACTIVATE to createPcmWav(cacheDir, "ability_activate.wav", durationMs = 320) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 400.0 + Math.sin(t * Math.PI * 4.0) * 200.0 + t * 600.0
                    val env = Math.sin(t * Math.PI)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.85 * env).toFloat()
                },
                SoundType.RELIC_UNLOCK to createPcmWav(cacheDir, "relic_unlock.wav", durationMs = 450) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val chord = sin(2.0 * Math.PI * 523.25 * sampleIndex / sampleRate) +
                                sin(2.0 * Math.PI * 659.25 * sampleIndex / sampleRate) +
                                sin(2.0 * Math.PI * 783.99 * sampleIndex / sampleRate)
                    val env = Math.sin(t * Math.PI)
                    ((chord / 3.0) * 0.9 * env).toFloat()
                },
                SoundType.TUTORIAL_STEP to createPcmWav(cacheDir, "tutorial_step.wav", durationMs = 150) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 880.0 + t * 440.0
                    val env = 1.0 - t
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.75 * env).toFloat()
                },
                SoundType.BOSS_VICTORY to createPcmWav(cacheDir, "boss_victory.wav", durationMs = 500) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val chord = sin(2.0 * Math.PI * 440.0 * sampleIndex / sampleRate) +
                                sin(2.0 * Math.PI * 554.37 * sampleIndex / sampleRate) +
                                sin(2.0 * Math.PI * 659.25 * sampleIndex / sampleRate)
                    val env = Math.sin(t * Math.PI)
                    ((chord / 3.0) * 0.95 * env).toFloat()
                },
                SoundType.ITEM_LOOT to createPcmWav(cacheDir, "item_loot.wav", durationMs = 250) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 600.0 + t * 600.0
                    val env = Math.sin(t * Math.PI)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.8 * env).toFloat()
                },
                SoundType.DAMAGE_TAKEN to createPcmWav(cacheDir, "damage_taken.wav", durationMs = 180) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 220.0 - t * 100.0
                    val noise = (Math.random() * 2.0 - 1.0) * 0.5
                    val env = 1.0 - t
                    ((sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.5 + noise) * env).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.DANGER to createPcmWav(cacheDir, "danger.wav", durationMs = 300) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val pulse = sin(2.0 * Math.PI * 8.0 * t)
                    val freq = 700.0 + (if (pulse > 0) 150.0 else 0.0)
                    val env = 1.0 - t * 0.2
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.8 * env).toFloat()
                },
                SoundType.LEVEL_UP to createPcmWav(cacheDir, "level_up.wav", durationMs = 400) { sampleIndex, totalSamples, sampleRate ->
                    val t = sampleIndex.toDouble() / totalSamples
                    val freq = 440.0 + t * 440.0
                    val env = Math.sin(t * Math.PI)
                    (sin(2.0 * Math.PI * freq * sampleIndex / sampleRate) * 0.85 * env).toFloat()
                }
            )

            for ((type, file) in soundsToGenerate) {
                file?.let {
                    val soundId = soundPool?.load(it.absolutePath, 1) ?: 0
                    if (soundId != 0) {
                        soundMap[type] = soundId
                    }
                }
            }
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error generating or loading sounds", e)
        }
    }

    private fun createPcmWav(
        dir: File,
        filename: String,
        durationMs: Int = 50,
        sampleRate: Int = 22050,
        generator: (sampleIndex: Int, totalSamples: Int, sampleRate: Int) -> Float
    ): File? {
        val file = File(dir, filename)
        if (file.exists() && file.length() > 0) return file

        val totalSamples = (sampleRate * (durationMs / 1000.0)).toInt()
        val pcmData = ByteArray(totalSamples * 2)

        for (i in 0 until totalSamples) {
            val sampleVal = generator(i, totalSamples, sampleRate)
            val shortVal = (sampleVal * 32767.0).toInt().coerceIn(-32768, 32767).toShort()
            pcmData[i * 2] = (shortVal.toInt() and 0x00FF).toByte()
            pcmData[i * 2 + 1] = ((shortVal.toInt() shr 8) and 0x00FF).toByte()
        }

        try {
            FileOutputStream(file).use { out ->
                val dataLen = pcmData.size
                val totalLen = dataLen + 36
                // WAV Header
                out.write("RIFF".toByteArray())
                out.write(intToByteArray(totalLen))
                out.write("WAVE".toByteArray())
                out.write("fmt ".toByteArray())
                out.write(intToByteArray(16)) // Subchunk1Size (16 for PCM)
                out.write(shortToByteArray(1))  // AudioFormat (1 for PCM)
                out.write(shortToByteArray(1))  // NumChannels (1 = Mono)
                out.write(intToByteArray(sampleRate))
                out.write(intToByteArray(sampleRate * 2)) // ByteRate
                out.write(shortToByteArray(2))  // BlockAlign
                out.write(shortToByteArray(16)) // BitsPerSample
                out.write("data".toByteArray())
                out.write(intToByteArray(dataLen))
                out.write(pcmData)
            }
            return file
        } catch (e: IOException) {
            Log.e("EidosAudio", "Failed generating sound $filename", e)
            return null
        }
    }

    private fun intToByteArray(i: Int): ByteArray = byteArrayOf(
        (i and 0xFF).toByte(),
        ((i shr 8) and 0xFF).toByte(),
        ((i shr 16) and 0xFF).toByte(),
        ((i shr 24) and 0xFF).toByte()
    )

    private fun shortToByteArray(s: Int): ByteArray = byteArrayOf(
        (s and 0xFF).toByte(),
        ((s shr 8) and 0xFF).toByte()
    )

    fun playSound(type: SoundType) {
        if (!isSoundEnabled) return
        try {
            soundMap[type]?.let { soundId ->
                val vol = effectsVolume
                soundPool?.play(soundId, vol, vol, 1, 0, 1.0f)
            }
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error playing sound effect $type", e)
        }
    }

    fun release() {
        stopMusic()
        soundPool?.release()
        soundPool = null
    }

    companion object {
        @Volatile
        private var instance: EidosAudioManager? = null

        fun getInstance(context: Context): EidosAudioManager {
            return instance ?: synchronized(this) {
                instance ?: EidosAudioManager(context.applicationContext).also { instance = it }
            }
        }
    }
}
