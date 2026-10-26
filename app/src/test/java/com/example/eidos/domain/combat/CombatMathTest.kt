package com.example.eidos.domain.combat

import org.junit.Assert.assertEquals
import org.junit.Test

class CombatMathTest {

    @Test
    fun testCalculateCritChance() {
        // Base case
        val chance1 = CombatEngine.calculateCritChance(10, hasBerserk1 = false, hasOverclockCrown = false)
        assertEquals(5f, chance1, 0.01f)

        // Berserk skill activated (+5%)
        val chance2 = CombatEngine.calculateCritChance(10, hasBerserk1 = true, hasOverclockCrown = false)
        assertEquals(10f, chance2, 0.01f)

        // Overclock crown equipped (2x multiplier)
        val chance3 = CombatEngine.calculateCritChance(10, hasBerserk1 = true, hasOverclockCrown = true)
        assertEquals(20f, chance3, 0.01f)
    }

    @Test
    fun testCalculateBasePlayerDamage() {
        // Base damage = (Attack * WeaponMultiplier) - EnemyDefense
        val damage1 = CombatEngine.calculateBasePlayerDamage(20, 1.5f, 5)
        assertEquals(25, damage1)

        val damage2 = CombatEngine.calculateBasePlayerDamage(10, 1.0f, 15)
        assertEquals(-5, damage2) // Negative is expected, handled by final damage clamp
    }

    @Test
    fun testCalculateFinalPlayerDamage() {
        // Non-crit damage
        val dmgNormal = CombatEngine.calculateFinalPlayerDamage(25, isCrit = false)
        assertEquals(25, dmgNormal)

        // Crit damage (1.5x)
        val dmgCrit = CombatEngine.calculateFinalPlayerDamage(20, isCrit = true)
        assertEquals(30, dmgCrit)

        // Negative damage should be clamped to at least 1, then multiplied if crit
        val clampedDmg = CombatEngine.calculateFinalPlayerDamage(-5, isCrit = false)
        assertEquals(1, clampedDmg)

        val clampedDmgCrit = CombatEngine.calculateFinalPlayerDamage(-5, isCrit = true)
        assertEquals(1, clampedDmgCrit) // minOf(1, base) * 1.5 = 1 * 1.5 = 1 in Int division
    }

    @Test
    fun testCalculateEvasionChance() {
        // Evasion = Defense * 0.2 + (10 if TacticalHelmet else 0)
        val chanceNormal = CombatEngine.calculateEvasionChance(30, hasTacticalHelmet = false)
        assertEquals(6f, chanceNormal, 0.01f)

        val chanceWithHelmet = CombatEngine.calculateEvasionChance(30, hasTacticalHelmet = true)
        assertEquals(16f, chanceWithHelmet, 0.01f)
    }

    @Test
    fun testCalculateScaledEnemyAtkAndBaseEnemyDamage() {
        // Player power = Attack + Defense + Luck
        val playerPower = 100 // Scale = 1 + 100/150 = 1.666...
        val scaledAtk = CombatEngine.calculateScaledEnemyAtk(20, playerPower, depth = 50)
        // (20 * 1.666) + 5 = 33 + 5 = 38
        assertEquals(38, scaledAtk)

        // Incoming damage = Max(1, scaledEnemyAtk - playerDefense / 2)
        val incomingDmg = CombatEngine.calculateBaseEnemyDamage(38, playerDefense = 30)
        assertEquals(23, incomingDmg)
    }
}
