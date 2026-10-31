package io.eidos.zerolayer.domain.anti_cheat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TimeAntiCheatTest {

    @Test
    fun testInitialSetupReturnsValid() {
        val currentWall = 1_700_000_000_000L
        val currentElapsed = 50_000L

        val result = TimeAntiCheat.evaluateTimestampIntegrity(
            currentWallTime = currentWall,
            currentElapsedRealtime = currentElapsed,
            currentBootCount = 1,
            lastKnownWallTime = 0L,
            lastElapsedRealtime = 0L,
            lastBootCount = -1
        )

        assertTrue(result.isValid)
        assertEquals(currentWall, result.sanitizedCurrentTime)
        assertFalse(result.isTimeReversed)
        assertFalse(result.isSuspiciousForwardJump)
        assertFalse(result.isRebootDetected)
    }

    @Test
    fun testNormalProgressionInSameSession() {
        val lastWall = 1_700_000_000_000L
        val lastElapsed = 50_000L

        val currentWall = lastWall + 10_000L
        val currentElapsed = lastElapsed + 10_000L

        val result = TimeAntiCheat.evaluateTimestampIntegrity(
            currentWallTime = currentWall,
            currentElapsedRealtime = currentElapsed,
            currentBootCount = 1,
            lastKnownWallTime = lastWall,
            lastElapsedRealtime = lastElapsed,
            lastBootCount = 1
        )

        assertTrue(result.isValid)
        assertEquals(currentWall, result.sanitizedCurrentTime)
        assertFalse(result.isTimeReversed)
        assertFalse(result.isSuspiciousForwardJump)
    }

    @Test
    fun testBackwardClockRewindDetection() {
        val lastWall = 1_700_000_000_000L
        val lastElapsed = 100_000L

        // Player rewinds clock back by 1 hour
        val currentWall = lastWall - 3_600_000L
        val currentElapsed = lastElapsed + 5_000L // 5 seconds elapsed

        val result = TimeAntiCheat.evaluateTimestampIntegrity(
            currentWallTime = currentWall,
            currentElapsedRealtime = currentElapsed,
            currentBootCount = 1,
            lastKnownWallTime = lastWall,
            lastElapsedRealtime = lastElapsed,
            lastBootCount = 1
        )

        assertFalse(result.isValid)
        assertTrue(result.isTimeReversed)
        assertFalse(result.isSuspiciousForwardJump)
        // Sanitized time should be lastWall + actual elapsed delta
        assertEquals(lastWall + 5_000L, result.sanitizedCurrentTime)
    }

    @Test
    fun testForwardClockJumpDetection() {
        val lastWall = 1_700_000_000_000L
        val lastElapsed = 100_000L

        // Player fast forwards clock by 24 hours while elapsed time is only 10s
        val currentWall = lastWall + 24L * 3600 * 1000L
        val currentElapsed = lastElapsed + 10_000L

        val result = TimeAntiCheat.evaluateTimestampIntegrity(
            currentWallTime = currentWall,
            currentElapsedRealtime = currentElapsed,
            currentBootCount = 1,
            lastKnownWallTime = lastWall,
            lastElapsedRealtime = lastElapsed,
            lastBootCount = 1
        )

        assertFalse(result.isValid)
        assertTrue(result.isSuspiciousForwardJump)
        assertFalse(result.isTimeReversed)
        // Sanitized time should clamp to lastWall + elapsed delta
        assertEquals(lastWall + 10_000L, result.sanitizedCurrentTime)
    }

    @Test
    fun testRebootWithClockRollbackDetection() {
        val lastWall = 1_700_000_000_000L
        val lastElapsed = 500_000L

        // Device rebooted: elapsed resets to 10s, but wall clock was rolled back before reboot
        val currentElapsed = 10_000L
        val currentWall = lastWall - 100_000L

        val result = TimeAntiCheat.evaluateTimestampIntegrity(
            currentWallTime = currentWall,
            currentElapsedRealtime = currentElapsed,
            currentBootCount = 2,
            lastKnownWallTime = lastWall,
            lastElapsedRealtime = lastElapsed,
            lastBootCount = 1
        )

        assertFalse(result.isValid)
        assertTrue(result.isRebootDetected)
        assertTrue(result.isTimeReversed)
        assertEquals(lastWall + currentElapsed, result.sanitizedCurrentTime)
    }

    @Test
    fun testCalculateSafeOfflineDurationCapped() {
        val lastActive = 1_700_000_000_000L
        val maxCap = 24L * 3600 * 1000L // 24 hours

        // Zero or negative delta
        assertEquals(0L, TimeAntiCheat.calculateSafeOfflineDurationMs(lastActive, lastActive - 1000L))
        assertEquals(0L, TimeAntiCheat.calculateSafeOfflineDurationMs(lastActive, lastActive))
        assertEquals(0L, TimeAntiCheat.calculateSafeOfflineDurationMs(0L, lastActive))

        // Normal 1 hour gap
        val oneHour = 3600 * 1000L
        assertEquals(oneHour, TimeAntiCheat.calculateSafeOfflineDurationMs(lastActive, lastActive + oneHour))

        // 3 days offline gap (must be capped at 24 hours)
        val threeDays = 3L * 24 * 3600 * 1000L
        assertEquals(maxCap, TimeAntiCheat.calculateSafeOfflineDurationMs(lastActive, lastActive + threeDays))
    }
}
