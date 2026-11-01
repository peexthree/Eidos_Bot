package io.eidos.zerolayer.domain.combat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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

        // Negative damage clamped to at least 1
        val clampedDmg = CombatEngine.calculateFinalPlayerDamage(-5, isCrit = false)
        assertEquals(1, clampedDmg)

        val clampedDmgCrit = CombatEngine.calculateFinalPlayerDamage(-5, isCrit = true)
        assertEquals(1, clampedDmgCrit)
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
    fun testCanonicalMonsterAttackAndDamageMitigation() {
        // Level 1 Parasite (ATK 3) vs player with 4 defense:
        val parasiteAtk = CombatEngine.calculateScaledEnemyAtk(3, playerPower = 20, depth = 50)
        assertEquals(3, parasiteAtk)
        val parasiteDmg = CombatEngine.calculateBaseEnemyDamage(parasiteAtk, playerDefense = 4)
        // 3 - (4 / 2) = 1 damage
        assertEquals(1, parasiteDmg)

        // Level 30 Entropy (ATK 48) vs player with 40 defense:
        val entropyAtk = CombatEngine.calculateScaledEnemyAtk(48, playerPower = 150, depth = 7500)
        val entropyDmg = CombatEngine.calculateBaseEnemyDamage(entropyAtk, playerDefense = 40)
        // 48 * 1.10 = 52 -> 52 - 20 = 32 damage
        assertTrue(entropyDmg in 25..35)

        // Defensive Stance blocks 50% damage:
        val guardedDmg = CombatEngine.calculateGuardedDamage(32)
        assertEquals(16, guardedDmg)
    }

    @Test
    fun testOverdriveCalculation() {
        val overdriveDmg = CombatEngine.calculateOverdriveDamage(playerAttack = 20, weaponMultiplier = 1.5f)
        // base = 30 -> 30 * 2.5 = 75 true damage
        assertEquals(75, overdriveDmg)
    }
}
