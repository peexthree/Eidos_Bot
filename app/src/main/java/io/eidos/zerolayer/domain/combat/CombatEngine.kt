package io.eidos.zerolayer.domain.combat

object CombatEngine {

    const val AFFIX_THORNS = "affix_thorns"           // 🪞 Отражение урона (20%)
    const val AFFIX_RADIATION = "affix_radiation"     // ☢️ Радиация кода (-8 Сигнала/ход)
    const val AFFIX_DOUBLE_DROP = "affix_double_drop" // 💎 Сингулярный резонанс (x2 Дроп)
    const val AFFIX_WARP = "affix_warp"               // ⚡ Квантовый разрыв (+30% Крит врагов и игрока)

    /**
     * Calculates the dynamic difficulty multiplier:
     * Gentle abyssal scaling for depths > 5000m.
     */
    fun getDepthDifficultyMultiplier(depth: Int): Float {
        return if (depth > 5000) {
            1.0f + ((depth - 5000) / 25000f).coerceIn(0f, 0.25f)
        } else {
            1.0f
        }
    }

    /**
     * Calculates proportional reward multiplier for BioCoins and XP with depth stepping.
     */
    fun getDepthRewardMultiplier(depth: Int): Float {
        return 1.0f + (depth / 2000f) * 0.5f
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
     * critChance = (5f + playerLuck * 0.25f).coerceIn(0f, 75f)
     */
    fun calculateCritChance(
        baseLuck: Int,
        hasBerserk1: Boolean = false,
        hasOverclockCrown: Boolean = false
    ): Float {
        return CombatMath.calculateCritChance(baseLuck, hasBerserk1, hasOverclockCrown)
    }

    /**
     * Calculates raw player damage on a physical hit with hyperbolic mitigation:
     * mitigation = 100f / (100f + max(0, targetDef))
     * finalDamage = max(1, (rawAtk * mitigation).toInt())
     */
    fun calculateBasePlayerDamage(
        playerAttack: Int,
        weaponMultiplier: Float,
        villainDef: Int
    ): Int {
        val rawAtk = playerAttack * weaponMultiplier
        return CombatMath.calculateDamage(rawAtk, villainDef)
    }

    /**
     * Calculates final player damage applying critical hit scaling.
     * Crit multiplier: 1.75x base (+25% / 2.0x with glitch_berserk).
     */
    fun calculateFinalPlayerDamage(
        baseDamage: Int,
        isCrit: Boolean,
        hasGlitchBerserk: Boolean = false
    ): Int {
        return if (isCrit) {
            val mult = CombatMath.calculateCritMultiplier(hasGlitchBerserk)
            maxOf(1, (baseDamage * mult).toInt())
        } else {
            maxOf(1, baseDamage)
        }
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
     * Calculates enemy attack power strictly anchored to canonical stats.
     * Early monsters hit with exact canonical ATK (3 to 20); Abyssal Singularity (5000m+) applies subtle bonus.
     */
    fun calculateScaledEnemyAtk(
        villainAtk: Int,
        playerPower: Int = 0,
        depth: Int = 0
    ): Int {
        val abyssMult = if (depth > 5000) {
            1.0f + ((depth - 5000) / 25000f).coerceIn(0f, 0.20f)
        } else {
            1.0f
        }
        return maxOf(1, (villainAtk * abyssMult).toInt())
    }

    /**
     * Calculates incoming enemy damage against player defenses using hyperbolic mitigation:
     * mitigation = 100f / (100f + max(0, playerDef))
     */
    fun calculateBaseEnemyDamage(
        scaledEnemyAtk: Int,
        playerDefense: Int
    ): Int {
        return CombatMath.calculateDamage(scaledEnemyAtk.toFloat(), playerDefense)
    }

    /**
     * Calculates guarded damage reduction (Defensive Stance blocks 50% incoming damage).
     */
    fun calculateGuardedDamage(incomingDamage: Int): Int {
        return maxOf(1, (incomingDamage * 0.5f).toInt())
    }

    // --- ⚡ 1. OVERDRIVE MECHANICS ---
    const val OVERDRIVE_MAX_CHARGE = 100
    const val CHARGE_NORMAL_ATTACK = 20
    const val CHARGE_CRIT_HIT = 35
    const val CHARGE_DODGE = 25
    const val CHARGE_GUARD = 25
    const val CHARGE_ABILITY = 35

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

    // --- 👾 3. TACTICAL MONSTER AI & CANONICAL ABILITIES ---
    enum class EnemyIntentType {
        ATTACK,         // ⚔️ Обычная атака: стандартный урон
        POWER_CHARGE,   // ⚠️ Силовой заряд (x2.5 урона!): можно сбить Овердрайвом / ЭМИ-гранатой или уйти в Защиту
        SHIELD,         // 🛡️ Энерго-Щит: блокирует 80% обычного урона, уязвим к Навыку фракции (+50% DMG)
        STUNNED         // 💫 Оглушен: пропускает ход (после сбития заряда ЭМИ или Овердрайвом)
    }

    data class EnemyIntent(
        val type: EnemyIntentType,
        val title: String,
        val description: String,
        val icon: String,
        val damageMultiplier: Float = 1.0f,
        val damageMitigation: Float = 0.0f
    )

    fun predictEnemyIntent(villainId: Int, combatTurn: Int, isStunned: Boolean = false): EnemyIntent {
        if (isStunned) {
            return EnemyIntent(
                type = EnemyIntentType.STUNNED,
                title = "ОГЛУШЕН",
                description = "Системы дезориентированы ЭМИ / Овердрайвом! Враг пропускает ход.",
                icon = "💫",
                damageMultiplier = 0f
            )
        }
        val turnCycle = combatTurn % 3
        return when {
            // Каждый 3-й раунд (turn % 3 == 0) враг заряжает сокрушительный гипер-удар (x2.5)
            combatTurn > 0 && turnCycle == 0 -> {
                EnemyIntent(
                    type = EnemyIntentType.POWER_CHARGE,
                    title = "СИЛОВОЙ ЗАРЯД (x2.5)",
                    description = "Враг готовит сокрушительный гипер-удар! Встаньте в Защиту (-60%) или сбейте ЭМИ/Овердрайвом!",
                    icon = "⚠️",
                    damageMultiplier = 2.5f
                )
            }
            // Каждый 2-й раунд цикла - враг ставит квантовый барьер (-80% обычного урона)
            combatTurn > 0 && turnCycle == 2 -> {
                EnemyIntent(
                    type = EnemyIntentType.SHIELD,
                    title = "ЭНЕРГО-ЩИТ (-80%)",
                    description = "Враг окружен барьером (-80% физ. урона). Пробейте Навыком фракции (+50% бонусного урона)!",
                    icon = "🛡️",
                    damageMultiplier = 0.6f,
                    damageMitigation = 0.80f
                )
            }
            else -> {
                EnemyIntent(
                    type = EnemyIntentType.ATTACK,
                    title = "ОБЫЧНАЯ АТАКА",
                    description = "Стандартная атака врага.",
                    icon = "⚔️",
                    damageMultiplier = 1.0f
                )
            }
        }
    }

    data class MonsterAiAction(
        val extraDamage: Int = 0,
        val damageMultiplier: Float = 1.0f,
        val selfHeal: Int = 0,
        val selfDefBonus: Int = 0,
        val drainBioCoins: Int = 0,
        val drainEnergy: Int = 0,
        val bypassArmorPercent: Float = 0f,
        val isPhaseEvading: Boolean = false,
        val isDetonating: Boolean = false,
        val strikesTwice: Boolean = false,
        val logMessage: String? = null
    )

    fun evaluateMonsterAi(
        villainId: Int,
        combatTurn: Int,
        villainAtk: Int,
        villainCurrentHp: Int
    ): MonsterAiAction {
        return when (villainId) {
            384 -> { // 🦠 Цифровой Паразит
                MonsterAiAction(logMessage = "🦠 [Цифровой Паразит]: Засоряет кэш мусорными пакетами.")
            }
            385 -> { // 👻 Призрак Глитча
                val evades = (0..100).random() < 20
                MonsterAiAction(
                    isPhaseEvading = evades,
                    logMessage = if (evades) "👻 [Призрак Глитча]: Мерцание текстур — атака прошла сквозь фазу!" else null
                )
            }
            386 -> { // 🚁 Дрон-Страж
                val shieldTurn = combatTurn > 0 && combatTurn % 3 == 0
                MonsterAiAction(
                    selfDefBonus = if (shieldTurn) 6 else 0,
                    logMessage = if (shieldTurn) "🚁 [Дрон-Страж]: Активирован силовой протокол щита (+6 DEF)!" else null
                )
            }
            387 -> { // 💣 Логическая Бомба
                val detonates = combatTurn >= 4
                MonsterAiAction(
                    isDetonating = detonates,
                    extraDamage = if (detonates) 25 else 0,
                    logMessage = if (detonates) "💣 [Логическая Бомба]: ТАЙМЕР НА НУЛЕ! Бомба сдетонировала с колоссальной силой!" else "💣 [Логическая Бомба]: Таймер детонации тикает... (ход $combatTurn/4)"
                )
            }
            388 -> { // ⛏ Крипто-Майнер
                MonsterAiAction(
                    drainBioCoins = 4,
                    logMessage = "⛏ [Крипто-Майнер]: Скрытый фоновый скрипт выкачал 4 BioCoins!"
                )
            }
            389 -> { // 🐉 Спам-Гидра
                MonsterAiAction(
                    selfHeal = 5,
                    logMessage = "🐉 [Спам-Гидра]: Репликация рекламных окон восстановила +5 HP!"
                )
            }
            390 -> { // ❌ Фатальный Сбой
                val mult = (70..135).random() / 100f
                MonsterAiAction(
                    damageMultiplier = mult,
                    logMessage = "❌ [Фатальный Сбой]: Амплитуда Ошибки 404 искажает входящий урон!"
                )
            }
            391 -> { // 🗡 Ассасин Даркнета
                val isCrit = (0..100).random() < 30
                MonsterAiAction(
                    damageMultiplier = if (isCrit) 1.5f else 1.0f,
                    logMessage = if (isCrit) "🗡 [Ассасин Даркнета]: Удар из слепой зоны сервера (КРИТ x1.5)!" else null
                )
            }
            392 -> { // 🧠 ИИ-Доминатор
                MonsterAiAction(
                    bypassArmorPercent = 0.35f,
                    logMessage = "🧠 [ИИ-Доминатор]: Предиктивный расчет обошел 35% вашей брони!"
                )
            }
            393 -> { // ⬛ Стиратель
                MonsterAiAction(
                    selfDefBonus = 5,
                    logMessage = "⬛ [Стиратель]: Монолитный барьер санитара форматирует вектор урона (+5 DEF)."
                )
            }
            394 -> { // 👻 Нейро-Призрак
                MonsterAiAction(
                    drainEnergy = 2,
                    logMessage = "👻 [Нейро-Призрак]: Проекция страха сожгла 2 EP оператора!"
                )
            }
            395 -> { // 💀 Кибер-Лич
                val leech = maxOf(4, (villainAtk * 0.35f).toInt())
                MonsterAiAction(
                    selfHeal = leech,
                    logMessage = "💀 [Кибер-Лич]: Вампиризм кода восстановил +$leech HP!"
                )
            }
            396 -> { // 🏗 Архитектор Кошмаров
                val isOdd = combatTurn % 2 == 1
                MonsterAiAction(
                    selfDefBonus = if (isOdd) 5 else 0,
                    extraDamage = if (!isOdd) 6 else 0,
                    logMessage = if (isOdd) "🏗 [Архитектор Кошмаров]: Искажение архитектуры укрепляет броню (+5 DEF)!" else "🏗 [Архитектор Кошмаров]: Обрушение конструкций Нулевого Слоя (+6 Урона)!"
                )
            }
            397 -> { // 🍽 Пожиратель Кода
                val bonusAtk = (combatTurn * 2).coerceAtMost(20)
                MonsterAiAction(
                    extraDamage = bonusAtk,
                    logMessage = if (bonusAtk > 0) "🍽 [Пожиратель Кода]: Поглощение данных усиливает атаку (+$bonusAtk ATK)!" else null
                )
            }
            398 -> { // 🛡 Страж Ядра
                MonsterAiAction(
                    selfDefBonus = 4,
                    logMessage = "🛡 [Страж Ядра]: Военный протокол шифрования активен (+4 DEF)."
                )
            }
            399 -> { // ⚛️ Омни-Синтез
                val element = combatTurn % 3
                val (elemMsg, elemDmg) = when (element) {
                    0 -> "Огненный выброс плазмы (+5 Урона)" to 5
                    1 -> "Криогенная заморозка канала связи" to 2
                    else -> "Электромагнитный шок (+4 Урона)" to 4
                }
                MonsterAiAction(
                    extraDamage = elemDmg,
                    logMessage = "⚛️ [Омни-Синтез]: $elemMsg!"
                )
            }
            400 -> { // 🤖 Бог Машины
                MonsterAiAction(
                    extraDamage = 5,
                    logMessage = "🤖 [Бог Машины]: Deus Ex Machina выполняет методичный стирающий расчет (+5 Урона)."
                )
            }
            401 -> { // 🌌 Пустотный Странник
                val doubleHit = (0..100).random() < 35
                MonsterAiAction(
                    strikesTwice = doubleHit,
                    logMessage = if (doubleHit) "🌌 [Пустотный Странник]: Атака из прошлого повторена сквозь разрыв времени!" else null
                )
            }
            402 -> { // 🌀 Энтропия
                MonsterAiAction(
                    extraDamage = 6,
                    logMessage = "🌀 [Энтропия]: Аудиторский распад материи наносит неизбежный урон энтропии (-6 HP)!"
                )
            }
            else -> MonsterAiAction()
        }
    }
}
