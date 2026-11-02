package io.eidos.zerolayer.domain.combat

object CombatMath {

    /**
     * Hyperbolic damage mitigation formula:
     * mitigation = 100f / (100f + max(0, targetDef))
     */
    fun calculateMitigation(targetDef: Int): Float {
        val safeDef = maxOf(0, targetDef)
        return 100f / (100f + safeDef)
    }

    /**
     * Calculates final damage from raw attack against target defense:
     * finalDamage = max(1, (rawAtk * mitigation).toInt())
     */
    fun calculateDamage(rawAtk: Float, targetDef: Int): Int {
        val mitigation = calculateMitigation(targetDef)
        return maxOf(1, (rawAtk * mitigation).toInt())
    }

    /**
     * Calculates critical strike chance based strictly on player LUCK:
     * critChance = (5f + playerLuck * 0.25f).coerceIn(0f, 75f)
     * Helmet reality_silencer sets LUCK to -100, resulting in 0% crit chance without dropping base ATK to 1.
     */
    fun calculateCritChance(
        playerLuck: Int,
        hasBerserk1: Boolean = false,
        hasOverclockCrown: Boolean = false
    ): Float {
        var critChance = (5f + playerLuck * 0.25f).coerceIn(0f, 75f)
        if (hasBerserk1) {
            critChance = (critChance + 5f).coerceIn(0f, 75f)
        }
        if (hasOverclockCrown) {
            critChance = (critChance * 2f).coerceIn(0f, 75f)
        }
        return critChance
    }

    /**
     * Critical damage multiplier: 1.75x base, +25% (2.0x) with glitch_berserk buff.
     */
    fun calculateCritMultiplier(hasGlitchBerserk: Boolean = false): Float {
        return if (hasGlitchBerserk) 2.0f else 1.75f
    }

    /**
     * EMP Grenade damage formula:
     * min((enemyCurrentHp * 0.35f).toInt(), (playerAtk * 2.5f).toInt())
     */
    fun calculateEmpDamage(enemyCurrentHp: Int, playerAtk: Int): Int {
        val hpBasedDamage = (enemyCurrentHp * 0.35f).toInt()
        val atkCap = (playerAtk * 2.5f).toInt()
        return maxOf(1, minOf(hpBasedDamage, atkCap))
    }
}
