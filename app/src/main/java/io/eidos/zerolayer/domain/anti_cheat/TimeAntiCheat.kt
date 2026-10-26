package io.eidos.zerolayer.domain.anti_cheat

import android.content.Context
import android.os.SystemClock
import android.util.Log

/**
 * Anti-Time Cheat Engine.
 *
 * Prevents players from manipulating the system clock to instantly regenerate energy,
 * bypass cache decryption timers, reset daily limits, or accelerate cooldowns.
 *
 * Strategies:
 * 1. Monotonic Clock Delta (SystemClock.elapsedRealtime()):
 *    Tracks time elapsed while device is awake/asleep independent of user system clock changes.
 * 2. Monotonic Wall-Clock Guard (SharedPreferences):
 *    Ensures wall clock timestamp never moves backward relative to recorded events.
 * 3. Max Realistic Offline Gap Protection:
 *    Caps extreme future jumps unless corroborated by network/monotonic time.
 */
object TimeAntiCheat {

    private const val PREFS_NAME = "eidos_time_anti_cheat"
    private const val KEY_LAST_KNOWN_WALL_TIME = "last_known_wall_time"
    private const val KEY_LAST_ELAPSED_REALTIME = "last_elapsed_realtime"
    private const val KEY_LAST_BOOT_COUNT_ESTIMATE = "last_boot_time_estimate"

    data class ValidationResult(
        val isValid: Boolean,
        val sanitizedCurrentTime: Long,
        val isTimeReversed: Boolean,
        val isSuspiciousForwardJump: Boolean,
        val message: String? = null
    )

    /**
     * Validates and returns a secure, tamper-resistant timestamp.
     */
    fun validateAndSanitizeTimestamp(context: Context): ValidationResult {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val currentWallTime = System.currentTimeMillis()
        val currentElapsedRealtime = SystemClock.elapsedRealtime()

        val lastKnownWallTime = prefs.getLong(KEY_LAST_KNOWN_WALL_TIME, 0L)
        val lastElapsedRealtime = prefs.getLong(KEY_LAST_ELAPSED_REALTIME, 0L)

        // Initial setup
        if (lastKnownWallTime == 0L || lastElapsedRealtime == 0L) {
            prefs.edit()
                .putLong(KEY_LAST_KNOWN_WALL_TIME, currentWallTime)
                .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
                .apply()
            return ValidationResult(
                isValid = true,
                sanitizedCurrentTime = currentWallTime,
                isTimeReversed = false,
                isSuspiciousForwardJump = false
            )
        }

        // Check for backward time travel (user rewound clock)
        if (currentWallTime < lastKnownWallTime) {
            val delta = lastKnownWallTime - currentWallTime
            Log.w("TimeAntiCheat", "Detected backward clock rewind! Delta: ${delta}ms")
            
            // Advance by elapsed realtime if valid, else keep last known wall time
            val elapsedDelta = if (currentElapsedRealtime >= lastElapsedRealtime) {
                currentElapsedRealtime - lastElapsedRealtime
            } else {
                0L // Device rebooted
            }
            val sanitized = lastKnownWallTime + elapsedDelta

            prefs.edit()
                .putLong(KEY_LAST_KNOWN_WALL_TIME, sanitized)
                .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
                .apply()

            return ValidationResult(
                isValid = false,
                sanitizedCurrentTime = sanitized,
                isTimeReversed = true,
                isSuspiciousForwardJump = false,
                message = "⚠️ [ХРОНО-ЗАЩИТА]: Обнаружен откат системного времени! Синхронизировано по аппаратному таймеру."
            )
        }

        // Check for forward time jump in the SAME boot session
        if (currentElapsedRealtime >= lastElapsedRealtime) {
            val wallDelta = currentWallTime - lastKnownWallTime
            val elapsedDelta = currentElapsedRealtime - lastElapsedRealtime
            val discrepancy = wallDelta - elapsedDelta

            // If user jumped wall clock forward by more than 2 minutes relative to hardware monotonic timer
            if (discrepancy > 120_000L) {
                Log.w("TimeAntiCheat", "Suspicious forward clock skip! Discrepancy: ${discrepancy}ms")
                val sanitized = lastKnownWallTime + elapsedDelta

                prefs.edit()
                    .putLong(KEY_LAST_KNOWN_WALL_TIME, sanitized)
                    .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
                    .apply()

                return ValidationResult(
                    isValid = false,
                    sanitizedCurrentTime = sanitized,
                    isTimeReversed = false,
                    isSuspiciousForwardJump = true,
                    message = "⚠️ [ХРОНО-ЗАЩИТА]: Обнаружена перемотка времени вперед! Таймеры скорректированы."
                )
            }
        }

        // Update persistent state
        prefs.edit()
            .putLong(KEY_LAST_KNOWN_WALL_TIME, currentWallTime)
            .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
            .apply()

        return ValidationResult(
            isValid = true,
            sanitizedCurrentTime = currentWallTime,
            isTimeReversed = false,
            isSuspiciousForwardJump = false
        )
    }

    /**
     * Calculates offline time safely with hard cap against extreme manipulations.
     * Max allowed offline calculation per single gap: 24 hours.
     */
    fun calculateSafeOfflineDurationMs(
        lastActiveTimestamp: Long,
        currentValidatedTimestamp: Long,
        maxAllowedGapMs: Long = 24L * 3600 * 1000L
    ): Long {
        if (lastActiveTimestamp <= 0L || currentValidatedTimestamp <= lastActiveTimestamp) {
            return 0L
        }
        val rawDiff = currentValidatedTimestamp - lastActiveTimestamp
        return minOf(rawDiff, maxAllowedGapMs)
    }
}
