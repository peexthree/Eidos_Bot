package com.example.eidos.ui.utils

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import kotlinx.coroutines.*
import kotlin.math.sin

/**
 * 🎛️ 4. LOW-LATENCY REAL-TIME AMBIENT DSP SYNTHESIZER
 * Dynamically synthesizes cyberpunk ambient drone soundscapes in real-time on a background audio thread.
 * Modulates base pitch, sub-oscillator harmonic width, and LFO filter pulses based on Abyss Depth & Signal/HP.
 */
class EidosAmbientSynthesizer private constructor() {

    private var audioTrack: AudioTrack? = null
    private var isPlaying = false
    private var synthScope: CoroutineScope? = null

    @Volatile var depthLevel: Int = 1
    @Volatile var signalPercent: Float = 1.0f // 0.0f to 1.0f

    fun startAmbientSynth() {
        if (isPlaying) return
        isPlaying = true

        val sampleRate = 22050
        val bufferSize = AudioTrack.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        ) * 2

        try {
            audioTrack = AudioTrack.Builder()
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_GAME)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build()
                )
                .setAudioFormat(
                    AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(sampleRate)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build()
                )
                .setBufferSizeInBytes(bufferSize)
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()

            audioTrack?.play()
        } catch (_: Exception) {
            isPlaying = false
            audioTrack = null
            return
        }

        synthScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
        synthScope?.launch {
            val pcmBuffer = ShortArray(1024)
            var sampleIndex = 0L

            while (isPlaying && isActive) {
                val baseFreq = 55.0 + (depthLevel % 10) * 2.5 // Low A sub drone
                val subFreq = baseFreq * 1.5 // Perfect fifth
                val pulseLfo = 0.5 + 0.5 * sin(2.0 * Math.PI * 0.4 * sampleIndex / sampleRate)

                // High corruption pulse if signal is low
                val glitchFactor = if (signalPercent < 0.3f) (Math.random() * 0.15).toFloat() else 0f

                for (i in pcmBuffer.indices) {
                    val t = sampleIndex.toDouble() / sampleRate
                    val waveMain = sin(2.0 * Math.PI * baseFreq * t)
                    val waveSub = sin(2.0 * Math.PI * subFreq * t) * 0.4 * pulseLfo
                    
                    val combined = (waveMain + waveSub) * 0.25 * (0.5 + 0.5 * signalPercent) + glitchFactor
                    pcmBuffer[i] = (combined.coerceIn(-1.0, 1.0) * 32767).toInt().toShort()
                    sampleIndex++
                }

                try {
                    val track = audioTrack
                    if (track != null && track.playState == AudioTrack.PLAYSTATE_PLAYING && isPlaying && isActive) {
                        track.write(pcmBuffer, 0, pcmBuffer.size)
                    } else {
                        break
                    }
                } catch (_: Exception) {
                    break
                }
            }
        }
    }

    fun stopAmbientSynth() {
        isPlaying = false
        synthScope?.cancel()
        synthScope = null
        val track = audioTrack
        audioTrack = null
        try {
            if (track != null && track.playState == AudioTrack.PLAYSTATE_PLAYING) {
                track.stop()
            }
            track?.release()
        } catch (_: Exception) {}
    }

    companion object {
        @Volatile
        private var instance: EidosAmbientSynthesizer? = null

        fun getInstance(): EidosAmbientSynthesizer {
            return instance ?: synchronized(this) {
                instance ?: EidosAmbientSynthesizer().also { instance = it }
            }
        }
    }
}
