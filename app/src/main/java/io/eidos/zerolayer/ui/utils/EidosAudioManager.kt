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
        LEVEL_UP,
        SECRET_FOUND,
        TAPE_REWIND,
        FLESH_SHUTDOWN,
        DRONE_RADIO,
        ANOMALY_PULSE,
        VANCE_ARCHIVE
    }

    enum class BgmTrack {
        NONE,
        MAIN_MENU,
        ZERO_LAYER,
        CODEX
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
            BgmTrack.CODEX -> playSingleTrack(R.raw.bgm_mirror_of_lies, loop = true)
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

            loadRawSoundEffects()
            generateAndLoadCyberSounds()
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Failed to initialize SoundPool", e)
        }
    }

    private fun loadRawSoundEffects() {
        try {
            val rawSounds = listOf(
                SoundType.SECRET_FOUND to R.raw.sfx_secret_found,
                SoundType.TAPE_REWIND to R.raw.sfx_tape_rewind,
                SoundType.FLESH_SHUTDOWN to R.raw.sfx_flesh_shutdown,
                SoundType.DRONE_RADIO to R.raw.sfx_drone_radio,
                SoundType.ANOMALY_PULSE to R.raw.sfx_anomaly_pulse,
                SoundType.VANCE_ARCHIVE to R.raw.sfx_vance_archive
            )
            for ((type, resId) in rawSounds) {
                val soundId = soundPool?.load(context, resId, 1) ?: 0
                if (soundId != 0) {
                    soundMap[type] = soundId
                }
            }
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error loading raw sound effects", e)
        }
    }

    private fun generateAndLoadCyberSounds() {
        try {
            val cacheDir = context.cacheDir ?: return
            val soundsToGenerate = listOf(
                SoundType.CLICK_CYBER to createPcmWav(cacheDir, "click_cyber_v2.wav", durationMs = 90) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Crisp UI click: bright pitch-dropping ping + sharp noise tick
                    val ping = sin(2.0 * Math.PI * 1400.0 * (1.0 - t * 0.3) * i / sr) * Math.exp(-t * 22.0)
                    val tick = (Math.random() * 2.0 - 1.0) * Math.exp(-t * 60.0) * 0.5
                    (ping * 0.7 + tick).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.RAID_STEP to createPcmWav(cacheDir, "raid_step_v2.wav", durationMs = 120) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Heavy footstep thud: pitch-dropping sine + gritty noise tail
                    val thud = sin(2.0 * Math.PI * (95.0 - t * 45.0) * i / sr) * Math.exp(-t * 9.0)
                    val grit = (Math.random() * 2.0 - 1.0) * Math.exp(-t * 30.0) * 0.25
                    ((thud * 0.95 + grit) * 0.9).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.CRITICAL_STRIKE to createPcmWav(cacheDir, "critical_strike_v2.wav", durationMs = 320) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Metallic impact: noise crack + descending sweep + sub punch
                    val crack = (Math.random() * 2.0 - 1.0) * Math.exp(-t * 35.0) * 0.6
                    val sweep = sin(2.0 * Math.PI * (700.0 * Math.exp(-t * 4.0) + 90.0) * i / sr) * Math.exp(-t * 6.0)
                    val sub = sin(2.0 * Math.PI * 55.0 * i / sr) * Math.exp(-t * 7.0)
                    ((crack + sweep * 0.5 + sub * 0.7) * 0.95).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.GLITCH_FOUND to createPcmWav(cacheDir, "glitch_found_v2.wav", durationMs = 300) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Digital stutter arpeggio with bitcrush artifacts
                    val step = (t * 10).toInt()
                    val freq = when (step % 5) {
                        0 -> 440.0
                        1 -> 990.0
                        2 -> 660.0
                        3 -> 1320.0
                        else -> 330.0
                    }
                    val gate = if ((step % 2) == 0) 1.0 else 0.35
                    val square = if (sin(2.0 * Math.PI * freq * i / sr) > 0) 0.45 else -0.45
                    val noise = (Math.random() * 2.0 - 1.0) * 0.15
                    ((square + noise) * gate * (1.0 - t * 0.7)).toFloat()
                },
                SoundType.HACK_SUCCESS to createPcmWav(cacheDir, "hack_success_v2.wav", durationMs = 380) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Terminal unlock: two-stage rise C5->G5 with additive harmonics
                    val stage = if (t < 0.5) 523.25 else 783.99
                    val noteT = if (t < 0.5) t / 0.5 else (t - 0.5) / 0.5
                    val envl = Math.sin(noteT * Math.PI)
                    val body = sin(2.0 * Math.PI * stage * i / sr) +
                               0.35 * sin(2.0 * Math.PI * stage * 2 * i / sr) +
                               0.15 * sin(2.0 * Math.PI * stage * 3 * i / sr)
                    val shimmer = sin(2.0 * Math.PI * (stage * 4 + t * 200) * i / sr) * 0.1
                    ((body / 1.5 + shimmer) * 0.8 * envl).toFloat()
                },
                SoundType.EVAC_WARNING to createPcmWav(cacheDir, "evac_warning_v2.wav", durationMs = 500) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Siren: alternating two-tone alarm with fast pulse gating
                    val alt = if (sin(2.0 * Math.PI * 3.0 * t) > 0) 880.0 else 660.0
                    val gate = 0.6 + 0.4 * sin(2.0 * Math.PI * 10.0 * t)
                    val envl = Math.min(1.0, t * 12) * (1.0 - t * 0.25)
                    (sin(2.0 * Math.PI * alt * i / sr) * 0.8 * gate * envl).toFloat()
                },
                SoundType.ITEM_CRAFT to createPcmWav(cacheDir, "item_craft_v2.wav", durationMs = 340) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Anvil clink: bright ping + inharmonic metallic ring + spark noise
                    val clink = sin(2.0 * Math.PI * 2200.0 * i / sr) * Math.exp(-t * 14.0) * 0.5
                    val ring = sin(2.0 * Math.PI * 3170.0 * i / sr) * Math.exp(-t * 9.0) * 0.3
                    val spark = (Math.random() * 2.0 - 1.0) * Math.exp(-t * 45.0) * 0.4
                    ((clink + ring + spark) * 0.9).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.ERROR_GLITCH to createPcmWav(cacheDir, "error_glitch_v2.wav", durationMs = 260) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Digital error: down-chirp + gated buzz stutter
                    val chirp = sin(2.0 * Math.PI * (300.0 - t * 180.0) * i / sr) * Math.exp(-t * 4.0)
                    val stutter = if ((i / (sr / 30)) % 2 == 0) 1.0 else 0.2
                    val buzz = (Math.random() * 2.0 - 1.0) * 0.35 * Math.exp(-t * 5.0)
                    ((chirp * 0.6 + buzz) * stutter * 0.95).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.ABILITY_ACTIVATE to createPcmWav(cacheDir, "ability_activate_v2.wav", durationMs = 420) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Power-up: rising sweep with vibrato and sub layer
                    val base = 350.0 + t * 700.0
                    val vib = Math.sin(2.0 * Math.PI * 9.0 * t) * 25.0
                    val sweep = sin(2.0 * Math.PI * (base + vib) * i / sr)
                    val subS = sin(2.0 * Math.PI * (base * 0.5) * i / sr) * 0.4
                    val envl = Math.sin(t * Math.PI * 0.9)
                    ((sweep * 0.65 + subS) * 0.8 * envl).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.RELIC_UNLOCK to createPcmWav(cacheDir, "relic_unlock_v2.wav", durationMs = 700) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Sacred bell arpeggio: C5-E5-G5-C6 with inharmonic decay
                    val notes = listOf(523.25, 659.25, 783.99, 1046.5)
                    val idx = (t * 4).toInt().coerceIn(0, 3)
                    val noteT = ((t * 4) - idx).coerceIn(0.0, 1.0)
                    val f = notes[idx]
                    val bell = sin(2.0 * Math.PI * f * i / sr) * Math.exp(-noteT * 3.5) +
                               0.4 * sin(2.0 * Math.PI * f * 2.01 * i / sr) * Math.exp(-noteT * 5.0) +
                               0.2 * sin(2.0 * Math.PI * f * 2.99 * i / sr) * Math.exp(-noteT * 7.0)
                    val tail = if (t > 0.75) sin(2.0 * Math.PI * 1046.5 * i / sr) * Math.exp(-(t - 0.75) * 8.0) * 0.3 else 0.0
                    ((bell * 0.5 + tail) * 0.9).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.TUTORIAL_STEP to createPcmWav(cacheDir, "tutorial_step_v2.wav", durationMs = 180) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Soft two-note confirm blip
                    val noteT = if (t < 0.5) t / 0.5 else (t - 0.5) / 0.5
                    val f = if (t < 0.5) 660.0 else 880.0
                    (sin(2.0 * Math.PI * f * i / sr) * 0.6 * Math.sin(noteT * Math.PI)).toFloat()
                },
                SoundType.BOSS_VICTORY to createPcmWav(cacheDir, "boss_victory_v2.wav", durationMs = 900) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Fanfare: rising 3-note lead phrase + full chord swell
                    val phrase = when {
                        t < 0.33 -> 523.25
                        t < 0.66 -> 659.25
                        else -> 783.99
                    }
                    val noteT = (t * 3) % 1.0
                    val lead = (sin(2.0 * Math.PI * phrase * i / sr) +
                                0.3 * sin(2.0 * Math.PI * phrase * 2 * i / sr)) * Math.exp(-noteT * 2.5) * 0.5
                    val swellT = if (t > 0.66) (t - 0.66) / 0.34 else 0.0
                    val chord = (sin(2.0 * Math.PI * 523.25 * i / sr) + sin(2.0 * Math.PI * 659.25 * i / sr) +
                                 sin(2.0 * Math.PI * 783.99 * i / sr) + sin(2.0 * Math.PI * 1046.5 * i / sr)) /
                        4.0 * swellT * 0.8
                    ((lead + chord) * 0.95).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.ITEM_LOOT to createPcmWav(cacheDir, "item_loot_v2.wav", durationMs = 280) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Coin pickup: bright double ping with metallic harmonic
                    val stage = if (t < 0.4) 1320.0 else 1760.0
                    val noteT = if (t < 0.4) t / 0.4 else (t - 0.4) / 0.6
                    val ping = (sin(2.0 * Math.PI * stage * i / sr) +
                                0.4 * sin(2.0 * Math.PI * stage * 1.5 * i / sr)) * Math.exp(-noteT * 5.0)
                    (ping * 0.75).toFloat()
                },
                SoundType.DAMAGE_TAKEN to createPcmWav(cacheDir, "damage_taken_v2.wav", durationMs = 220) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Painful impact: low crunch + noise slam
                    val crunch = sin(2.0 * Math.PI * (180.0 - t * 90.0) * i / sr) * Math.exp(-t * 8.0)
                    val slam = (Math.random() * 2.0 - 1.0) * Math.exp(-t * 25.0) * 0.55
                    ((crunch * 0.7 + slam) * 0.95).toFloat().coerceIn(-1f, 1f)
                },
                SoundType.DANGER to createPcmWav(cacheDir, "danger_v2.wav", durationMs = 450) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Threat drone: dissonant minor-second pulse
                    val pulse = 0.55 + 0.45 * sin(2.0 * Math.PI * 7.0 * t)
                    val drone = sin(2.0 * Math.PI * 220.0 * i / sr) + 0.7 * sin(2.0 * Math.PI * 233.08 * i / sr)
                    val envl = Math.min(1.0, t * 8) * (1.0 - t * 0.3)
                    ((drone / 1.7) * 0.85 * pulse * envl).toFloat()
                },
                SoundType.LEVEL_UP to createPcmWav(cacheDir, "level_up_v2.wav", durationMs = 600) { i, n, sr ->
                    val t = i.toDouble() / n
                    // Ascending arpeggio C5-E5-G5-C6 + shine sweep + chord tail
                    val notes = listOf(523.25, 659.25, 783.99, 1046.5)
                    val idx = (t * 4).toInt().coerceIn(0, 3)
                    val noteT = ((t * 4) - idx).coerceIn(0.0, 1.0)
                    val arp = sin(2.0 * Math.PI * notes[idx] * i / sr) * Math.exp(-noteT * 4.0) * 0.55
                    val shine = sin(2.0 * Math.PI * (1046.5 + t * 800) * i / sr) * (1.0 - t) * 0.18
                    val chordTail = if (t > 0.6) {
                        val ct = (t - 0.6) / 0.4
                        (sin(2.0 * Math.PI * 523.25 * i / sr) + sin(2.0 * Math.PI * 783.99 * i / sr)) / 2.0 * Math.sin(ct * Math.PI) * 0.4
                    } else 0.0
                    ((arp + shine + chordTail) * 0.9).toFloat().coerceIn(-1f, 1f)
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

    fun playSound(type: SoundType, pitch: Float = 1.0f) {
        if (!isSoundEnabled) return
        try {
            val soundId = soundMap[type]
            if (soundId != null && soundId != 0) {
                val vol = effectsVolume
                val clampedPitch = pitch.coerceIn(0.5f, 2.0f)
                val streamId = soundPool?.play(soundId, vol, vol, 1, 0, clampedPitch) ?: 0
                if (streamId == 0) {
                    playFallbackMedia(type)
                }
            } else {
                playFallbackMedia(type)
            }
        } catch (e: Throwable) {
            Log.e("EidosAudio", "Error playing sound effect $type", e)
        }
    }

    private fun playFallbackMedia(type: SoundType) {
        val resId = when (type) {
            SoundType.SECRET_FOUND -> R.raw.sfx_secret_found
            SoundType.TAPE_REWIND -> R.raw.sfx_tape_rewind
            SoundType.FLESH_SHUTDOWN -> R.raw.sfx_flesh_shutdown
            SoundType.DRONE_RADIO -> R.raw.sfx_drone_radio
            SoundType.ANOMALY_PULSE -> R.raw.sfx_anomaly_pulse
            SoundType.VANCE_ARCHIVE -> R.raw.sfx_vance_archive
            else -> null
        } ?: return
        try {
            MediaPlayer.create(context, resId)?.apply {
                val vol = effectsVolume
                setVolume(vol, vol)
                setOnCompletionListener { release() }
                setOnErrorListener { mp, _, _ ->
                    mp.release()
                    true
                }
                start()
            }
        } catch (_: Throwable) {}
    }

    private var voicePlayer: MediaPlayer? = null
    var isVoicePlaying: Boolean = false
        private set

    fun playVoice(resId: Int, onComplete: () -> Unit = {}) {
        stopVoice()
        try {
            duckMusic(true)
            voicePlayer = MediaPlayer.create(context, resId)?.apply {
                isLooping = false
                setVolume(1.0f, 1.0f)
                setOnCompletionListener {
                    isVoicePlaying = false
                    duckMusic(false)
                    onComplete()
                }
                setOnErrorListener { _, _, _ ->
                    isVoicePlaying = false
                    duckMusic(false)
                    true
                }
                start()
                isVoicePlaying = true
            }
        } catch (e: Exception) {
            Log.e("EidosAudio", "Error playing voice $resId", e)
            isVoicePlaying = false
            duckMusic(false)
        }
    }

    enum class EvaCombatVoiceType {
        SIGNAL_CRITICAL,
        OVERDRIVE_READY,
        ANOMALY_FOUND,
        COMBAT_VICTORY
    }

    enum class EvaHubVoiceType {
        WELCOME_BACK,
        DEPOT_READY,
        TIP_FORGE,
        TIP_BROKER
    }

    fun playEvaDirectiveVoice(directiveId: Int, onComplete: () -> Unit = {}) {
        val resId = when (directiveId) {
            1 -> R.raw.eva_directive_init
            3 -> R.raw.eva_directive_forge
            10 -> R.raw.eva_directive_singularity
            else -> null
        }
        if (resId != null) {
            playVoice(resId, onComplete)
        }
    }

    fun playEvaCombatVoice(type: EvaCombatVoiceType, onComplete: () -> Unit = {}) {
        val resId = when (type) {
            EvaCombatVoiceType.SIGNAL_CRITICAL -> R.raw.eva_signal_critical
            EvaCombatVoiceType.OVERDRIVE_READY -> R.raw.eva_overdrive_ready
            EvaCombatVoiceType.ANOMALY_FOUND -> R.raw.eva_anomaly_found
            EvaCombatVoiceType.COMBAT_VICTORY -> R.raw.eva_combat_victory
        }
        playVoice(resId, onComplete)
    }

    fun playEvaHubVoice(type: EvaHubVoiceType, onComplete: () -> Unit = {}) {
        val resId = when (type) {
            EvaHubVoiceType.WELCOME_BACK -> R.raw.eva_welcome_back
            EvaHubVoiceType.DEPOT_READY -> R.raw.eva_depot_ready
            EvaHubVoiceType.TIP_FORGE -> R.raw.eva_tip_forge
            EvaHubVoiceType.TIP_BROKER -> R.raw.eva_tip_broker
        }
        playVoice(resId, onComplete)
    }

    fun playEvaMilestoneVoice(depth: Int, onComplete: () -> Unit = {}) {
        val resId = when (depth) {
            100 -> R.raw.eva_depth_100
            500 -> R.raw.eva_depth_500
            1200 -> R.raw.eva_depth_1200
            2500 -> R.raw.eva_depth_2500
            4000 -> R.raw.eva_depth_4000
            5000 -> R.raw.eva_depth_5000
            else -> null
        }
        if (resId != null) {
            playVoice(resId, onComplete)
        }
    }

    fun playEvaEggVoice(key: String, onComplete: () -> Unit = {}) {
        val clean = key.trim().lowercase()
        val resId = when {
            clean.contains("vance") || clean.contains("вэнс") -> R.raw.eva_egg_vance
            clean.contains("elena") || clean.contains("елена") -> R.raw.eva_egg_elena
            else -> null
        }
        if (resId != null) {
            playVoice(resId, onComplete)
        }
    }

    fun playEvaStepLoop(onComplete: () -> Unit = {}) {
        playVoice(R.raw.eva_step_loop, onComplete)
    }

    fun stopVoice() {
        try {
            voicePlayer?.stop()
            voicePlayer?.release()
            voicePlayer = null
            isVoicePlaying = false
            duckMusic(false)
        } catch (_: Exception) {}
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
