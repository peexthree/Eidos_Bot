package io.eidos.zerolayer.domain.combat

object CombatEngine {

    const val AFFIX_THORNS = "affix_thorns"           // 🪞 Отражение урона (20%)
    const val AFFIX_RADIATION = "affix_radiation"     // ☢️ Радиация кода (-8 Сигнала/ход)
    const val AFFIX_DOUBLE_DROP = "affix_double_drop" // 💎 Сингулярный резонанс (x2 Дроп)
    const val AFFIX_WARP = "affix_warp"               // ⚡ Квантовый разрыв (+30% Крит врагов и игрока)

    /**
     * Calculates the dynamic difficulty multiplier:
     * After 1000m, damage and monster stats scale via: multiplier = 1.0f + (depth / 1000f) * 0.75f
     */
    fun getDepthDifficultyMultiplier(depth: Int): Float {
        return if (depth > 1000) {
            1.0f + (depth / 1000f) * 0.75f
        } else {
            1.0f
        }
    }

    /**
     * Calculates proportional reward multiplier for BioCoins and XP with depth stepping.
     */
    fun getDepthRewardMultiplier(depth: Int): Float {
        return 1.0f + (depth / 1000f) * 0.75f
    }

    /**
     * Returns a random room affix for depths 5000+ (Abyssal Singularity).
     */
    fun rollSingularityAffix(depth: Int): String? {
        if (depth < 5000) return null
        val affixes = listOf(AFFIX_THORNS, AFFIX_RADIATION, AFFIX_DOUBLE_DROP, AFFIX_WARP)
        return affixes.random()
    }

    fun getAffixDisplayName(affix: String?): String {
        return when (affix) {
            AFFIX_THORNS -> "🪞 [ОТРАЖЕНИЕ УРОНА: 20%]"
            AFFIX_RADIATION -> "☢️ [РАДИАЦИЯ КОДА: -8 СИГНАЛА/ХОД]"
            AFFIX_DOUBLE_DROP -> "💎 [СИНГУЛЯРНЫЙ РЕЗОНАНС: 2x ДРОП]"
            AFFIX_WARP -> "⚡ [КВАНТОВЫЙ РАЗРЫВ: +30% КРИТ]"
            else -> ""
        }
    }

    /**
     * Calculates the probability of a critical hit based on player attributes and gear.
     */
    fun calculateCritChance(
        baseLuck: Int,
        hasBerserk1: Boolean,
        hasOverclockCrown: Boolean
    ): Float {
        val critChance = (baseLuck * 0.5f) + (if (hasBerserk1) 5f else 0f)
        return if (hasOverclockCrown) critChance * 2f else critChance
    }

    /**
     * Calculates raw player damage on a physical hit, prior to critical strike or special gear modifications.
     */
    fun calculateBasePlayerDamage(
        playerAttack: Int,
        weaponMultiplier: Float,
        villainDef: Int
    ): Int {
        return (playerAttack * weaponMultiplier).toInt() - villainDef
    }

    /**
     * Calculates final player damage applying critical hit scaling.
     */
    fun calculateFinalPlayerDamage(
        baseDamage: Int,
        isCrit: Boolean
    ): Int {
        return if (isCrit) (maxOf(1, baseDamage) * 1.5f).toInt() else maxOf(1, baseDamage)
    }

    /**
     * Calculates evasion probability based on defense values and helmet modules.
     */
    fun calculateEvasionChance(
        playerDefense: Int,
        hasTacticalHelmet: Boolean
    ): Float {
        return ((playerDefense * 0.2f) + (if (hasTacticalHelmet) 10f else 0f)).coerceIn(0f, 75f)
    }

    /**
     * Calculates scalable enemy attack power based on player's overall power levels and dynamic depth scaling.
     */
    fun calculateScaledEnemyAtk(
        villainAtk: Int,
        playerPower: Int,
        depth: Int
    ): Int {
        val powerScale = 1.0f + (playerPower / 150.0f)
        val depthMult = getDepthDifficultyMultiplier(depth)
        val rawAtk = (villainAtk * powerScale) + (depth / 10)
        return (rawAtk * depthMult).toInt()
    }

    /**
     * Calculates raw incoming enemy damage against player defenses.
     */
    fun calculateBaseEnemyDamage(
        scaledEnemyAtk: Int,
        playerDefense: Int
    ): Int {
        return maxOf(1, scaledEnemyAtk - (playerDefense / 2))
    }

    // --- ⚡ 1. OVERDRIVE MECHANICS ---
    const val OVERDRIVE_MAX_CHARGE = 100
    const val CHARGE_NORMAL_ATTACK = 20
    const val CHARGE_CRIT_HIT = 35
    const val CHARGE_DODGE = 25

    /**
     * Calculates Singularity Overdrive damage: deals 250% true critical damage bypassing enemy armor.
     */
    fun calculateOverdriveDamage(playerAttack: Int, weaponMultiplier: Float): Int {
        val base = maxOf(10, (playerAttack * weaponMultiplier).toInt())
        return (base * 2.5f).toInt()
    }

    // --- 🔥 2. OVERCHARGE PROTOCOL (GREED MULTIPLIER) ---
    const val MAX_OVERCHARGE_TIER = 3

    /**
     * Overcharge rewards multiplier: Tier 0 = 1.0x, Tier 1 = 1.5x, Tier 2 = 2.0x, Tier 3 = 2.5x.
     */
    fun getOverchargeLootMultiplier(tier: Int): Float {
        return when (tier.coerceIn(0, MAX_OVERCHARGE_TIER)) {
            0 -> 1.0f
            1 -> 1.5f
            2 -> 2.0f
            3 -> 2.5f
            else -> 1.0f
        }
    }

    /**
     * Overcharge enemy attack multiplier: +20% enemy ATK per tier (1.0x .. 1.6x).
     */
    fun getOverchargeEnemyAtkMultiplier(tier: Int): Float {
        return 1.0f + (tier.coerceIn(0, MAX_OVERCHARGE_TIER) * 0.20f)
    }

    /**
     * Evaluates bonus high-tier loot drop chance based on active Overcharge tier.
     */
    fun rollOverchargeBonusItem(tier: Int, depth: Int): String? {
        if (tier <= 0) return null
        val roll = (0..100).random()
        val dropChance = tier * 18 // Tier 1: 18%, Tier 2: 36%, Tier 3: 54%
        if (roll > dropChance) return null
        val rarePool = when {
            depth >= 5000 -> listOf("oblivion_chip", "eidos_shard", "abyssal_key", "relic_vampire")
            depth >= 2000 -> listOf("chip_green_crit", "stim_nano", "abyssal_key", "eidos_shard")
            else -> listOf("chip_red_atk", "chip_blue_energy", "stim_nano", "encrypted_cache")
        }
        return rarePool.random()
    }
}

