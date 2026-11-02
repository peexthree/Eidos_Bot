package io.eidos.zerolayer.domain.combat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CombatMathTest {

    @Test
    fun testCalculateCritChance() {
        // Base case with LUCK = 10 -> 5 + 10 * 0.25 = 7.5%
        val chance1 = CombatEngine.calculateCritChance(10, hasBerserk1 = false, hasOverclockCrown = false)
        assertEquals(7.5f, chance1, 0.01f)

        // Berserk skill activated (+5%) -> 7.5 + 5 = 12.5%
        val chance2 = CombatEngine.calculateCritChance(10, hasBerserk1 = true, hasOverclockCrown = false)
        assertEquals(12.5f, chance2, 0.01f)

        // Overclock crown equipped (2x multiplier) -> 12.5 * 2 = 25%
        val chance3 = CombatEngine.calculateCritChance(10, hasBerserk1 = true, hasOverclockCrown = true)
        assertEquals(25.0f, chance3, 0.01f)

        // Reality silencer with LUCK = -100 -> 0% crit chance
        val chanceSilencer = CombatEngine.calculateCritChance(-100, hasBerserk1 = false, hasOverclockCrown = false)
        assertEquals(0f, chanceSilencer, 0.01f)
    }

    @Test
    fun testHyperbolicBasePlayerDamage() {
        // rawAtk = 20 * 1.5 = 30. mitigation = 100 / (100 + 5) = 0.95238 -> 28
        val damage1 = CombatEngine.calculateBasePlayerDamage(20, 1.5f, 5)
        assertEquals(28, damage1)

        // High enemy def (100) -> mitigation = 100 / 200 = 0.5. rawAtk = 10 -> 5
        val damage2 = CombatEngine.calculateBasePlayerDamage(10, 1.0f, 100)
        assertEquals(5, damage2)

        // Even with extreme defense, damage is at least 1
        val damageMin = CombatEngine.calculateBasePlayerDamage(10, 1.0f, 9999)
        assertEquals(1, damageMin)
    }

    @Test
    fun testCalculateFinalPlayerDamage() {
        // Non-crit damage
        val dmgNormal = CombatEngine.calculateFinalPlayerDamage(25, isCrit = false)
        assertEquals(25, dmgNormal)

        // Crit damage (1.75x)
        val dmgCrit = CombatEngine.calculateFinalPlayerDamage(20, isCrit = true)
        assertEquals(35, dmgCrit)

        // Crit with Glitch Berserk (2.0x)
        val dmgCritBerserk = CombatEngine.calculateFinalPlayerDamage(20, isCrit = true, hasGlitchBerserk = true)
        assertEquals(40, dmgCritBerserk)
    }

    @Test
    fun testEmpGrenadeDamage() {
        // enemyHp = 1000, playerAtk = 100
        // hpDamage = 350, atkCap = 250 -> min is 250
        val dmg1 = CombatMath.calculateEmpDamage(1000, 100)
        assertEquals(250, dmg1)

        // enemyHp = 200, playerAtk = 100
        // hpDamage = 70, atkCap = 250 -> min is 70
        val dmg2 = CombatMath.calculateEmpDamage(200, 100)
        assertEquals(70, dmg2)
    }

    @Test
    fun testCalculateEvasionChance() {
        val chanceNormal = CombatEngine.calculateEvasionChance(30, hasTacticalHelmet = false)
        assertEquals(6f, chanceNormal, 0.01f)

        val chanceWithHelmet = CombatEngine.calculateEvasionChance(30, hasTacticalHelmet = true)
        assertEquals(16f, chanceWithHelmet, 0.01f)
    }

    @Test
    fun testScaledEnemyAtkAndDamage() {
        val parasiteAtk = CombatEngine.calculateScaledEnemyAtk(villainAtk = 5, depth = 100)
        assertEquals(5, parasiteAtk)

        val entropyAtk = CombatEngine.calculateScaledEnemyAtk(villainAtk = 30, depth = 6000)
        assertTrue(entropyAtk > 30)

        // Enemy damage with hyperbolic mitigation
        val parasiteDmg = CombatEngine.calculateBaseEnemyDamage(parasiteAtk, playerDefense = 4)
        assertTrue(parasiteDmg >= 1)

        val guarded = CombatEngine.calculateGuardedDamage(parasiteDmg)
        assertTrue(guarded <= parasiteDmg)
    }
}
