package io.eidos.zerolayer.domain.anti_cheat

import android.content.Context
import android.os.SystemClock
import android.provider.Settings
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
 * 2. Reboot & BOOT_COUNT Detection:
 *    Detects device restarts when SystemClock.elapsedRealtime resets or BOOT_COUNT changes.
 * 3. Monotonic Wall-Clock Guard (SharedPreferences):
 *    Ensures wall clock timestamp never moves backward or jumps suspiciously relative to recorded events.
 * 4. Server Time Verification:
 *    Resets trusted baseline whenever server time is fetched.
 */
object TimeAntiCheat {

    private const val PREFS_NAME = "eidos_time_anti_cheat"
    private const val KEY_LAST_KNOWN_WALL_TIME = "last_known_wall_time"
    private const val KEY_LAST_ELAPSED_REALTIME = "last_elapsed_realtime"
    private const val KEY_LAST_BOOT_COUNT = "last_boot_count"

    const val MAX_SUSPICIOUS_FORWARD_JUMP_MS = 120_000L // 2 minutes in same boot
    const val MAX_REBOOT_UNTRUSTED_FORWARD_GAP_MS = 24 * 3600 * 1000L // 24 hours max gap after reboot without server verification

    data class ValidationResult(
        val isValid: Boolean,
        val sanitizedCurrentTime: Long,
        val isTimeReversed: Boolean,
        val isSuspiciousForwardJump: Boolean,
        val isRebootDetected: Boolean = false,
        val message: String? = null
    )

    /**
     * Pure validation logic decoupled from Android Context / SharedPreferences.
     */
    fun evaluateTimestampIntegrity(
        currentWallTime: Long,
        currentElapsedRealtime: Long,
        currentBootCount: Int,
        lastKnownWallTime: Long,
        lastElapsedRealtime: Long,
        lastBootCount: Int
    ): ValidationResult {
        // Initial setup
        if (lastKnownWallTime == 0L || lastElapsedRealtime == 0L) {
            return ValidationResult(
                isValid = true,
                sanitizedCurrentTime = currentWallTime,
                isTimeReversed = false,
                isSuspiciousForwardJump = false
            )
        }

        val isReboot = (currentElapsedRealtime < lastElapsedRealtime) ||
                (currentBootCount != -1 && lastBootCount != -1 && currentBootCount != lastBootCount)

        // Case 1: Device Rebooted
        if (isReboot) {
            val wallDelta = currentWallTime - lastKnownWallTime

            if (wallDelta < 0) {
                // System clock was rewound before/during reboot
                val sanitized = lastKnownWallTime + currentElapsedRealtime
                return ValidationResult(
                    isValid = false,
                    sanitizedCurrentTime = sanitized,
                    isTimeReversed = true,
                    isSuspiciousForwardJump = false,
                    isRebootDetected = true,
                    message = "⚠️ [ХРОНО-ЗАЩИТА]: Обнаружен откат времени после перезагрузки! Время скорректировано."
                )
            } else if (wallDelta > MAX_REBOOT_UNTRUSTED_FORWARD_GAP_MS) {
                // System clock jumped forward suspiciously across reboot
                val sanitized = lastKnownWallTime + MAX_REBOOT_UNTRUSTED_FORWARD_GAP_MS
                return ValidationResult(
                    isValid = false,
                    sanitizedCurrentTime = sanitized,
                    isTimeReversed = false,
                    isSuspiciousForwardJump = true,
                    isRebootDetected = true,
                    message = "⚠️ [ХРОНО-ЗАЩИТА]: Пересказ времени после перезагрузки превышает лимит offline! Синхронизируйтесь с сетью."
                )
            } else {
                // Reasonable wallDelta post-reboot
                return ValidationResult(
                    isValid = true,
                    sanitizedCurrentTime = currentWallTime,
                    isTimeReversed = false,
                    isSuspiciousForwardJump = false,
                    isRebootDetected = true
                )
            }
        }

        // Case 2: Same Boot Session - Backward Time Travel
        if (currentWallTime < lastKnownWallTime) {
            val elapsedDelta = (currentElapsedRealtime - lastElapsedRealtime).coerceAtLeast(0L)
            val sanitized = lastKnownWallTime + elapsedDelta

            return ValidationResult(
                isValid = false,
                sanitizedCurrentTime = sanitized,
                isTimeReversed = true,
                isSuspiciousForwardJump = false
            )
        }

        // Case 3: Same Boot Session - Forward Time Jump
        val wallDelta = currentWallTime - lastKnownWallTime
        val elapsedDelta = currentElapsedRealtime - lastElapsedRealtime
        val discrepancy = wallDelta - elapsedDelta

        if (discrepancy > MAX_SUSPICIOUS_FORWARD_JUMP_MS) {
            val sanitized = lastKnownWallTime + elapsedDelta

            return ValidationResult(
                isValid = false,
                sanitizedCurrentTime = sanitized,
                isTimeReversed = false,
                isSuspiciousForwardJump = true,
                message = "⚠️ [ХРОНО-ЗАЩИТА]: Обнаружена перемотка времени вперед! Таймеры скорректированы."
            )
        }

        return ValidationResult(
            isValid = true,
            sanitizedCurrentTime = currentWallTime,
            isTimeReversed = false,
            isSuspiciousForwardJump = false
        )
    }

    /**
     * Validates and returns a secure, tamper-resistant timestamp.
     */
    fun validateAndSanitizeTimestamp(context: Context): ValidationResult {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val currentWallTime = System.currentTimeMillis()
        val currentElapsedRealtime = SystemClock.elapsedRealtime()

        val currentBootCount = try {
            Settings.Global.getInt(context.contentResolver, Settings.Global.BOOT_COUNT, -1)
        } catch (_: Throwable) {
            -1
        }

        val lastKnownWallTime = prefs.getLong(KEY_LAST_KNOWN_WALL_TIME, 0L)
        val lastElapsedRealtime = prefs.getLong(KEY_LAST_ELAPSED_REALTIME, 0L)
        val lastBootCount = prefs.getInt(KEY_LAST_BOOT_COUNT, -1)

        val result = evaluateTimestampIntegrity(
            currentWallTime = currentWallTime,
            currentElapsedRealtime = currentElapsedRealtime,
            currentBootCount = currentBootCount,
            lastKnownWallTime = lastKnownWallTime,
            lastElapsedRealtime = lastElapsedRealtime,
            lastBootCount = lastBootCount
        )

        // Persist evaluated/sanitized state
        prefs.edit()
            .putLong(KEY_LAST_KNOWN_WALL_TIME, result.sanitizedCurrentTime)
            .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
            .putInt(KEY_LAST_BOOT_COUNT, currentBootCount)
            .apply()

        return result
    }

    /**
     * Resets trusted baseline using authenticated server timestamp from Supabase/API.
     */
    fun syncWithServerTimestamp(context: Context, serverTimeMs: Long) {
        if (serverTimeMs <= 0L) return
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val currentElapsedRealtime = SystemClock.elapsedRealtime()
        val currentBootCount = try {
            Settings.Global.getInt(context.contentResolver, Settings.Global.BOOT_COUNT, -1)
        } catch (_: Throwable) {
            -1
        }

        prefs.edit()
            .putLong(KEY_LAST_KNOWN_WALL_TIME, serverTimeMs)
            .putLong(KEY_LAST_ELAPSED_REALTIME, currentElapsedRealtime)
            .putInt(KEY_LAST_BOOT_COUNT, currentBootCount)
            .apply()
        Log.i("TimeAntiCheat", "Successfully synced baseline with server timestamp: $serverTimeMs")
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
