package com.example.eidos.data

import androidx.compose.ui.graphics.Color
import kotlinx.serialization.Serializable
import kotlin.random.Random

@Serializable
data class VendettaLog(
    val attackerId: Long,
    val attackerName: String,
    val attackerLevel: Int,
    val timestamp: Long,
    val coinsStolen: Long,
    val isAvenged: Boolean = false
)

enum class PvpProgram(val id: String, val label: String, val icon: String, val color: Color) {
    BRUTEFORCE("BRUTEFORCE", "Брутфорс", "🔴", Color(0xFFFF1744)),
    SHIELD("SHIELD", "Файрвол", "🔵", Color(0xFF00E5FF)),
    STEALTH("STEALTH", "Стелс-Обход", "🟢", Color(0xFF00E676));

    val title: String get() = label

    companion object {
        fun fromString(str: String?): PvpProgram = when (str?.uppercase()) {
            "BRUTEFORCE", "ATTACK", "БРУТФОРС" -> BRUTEFORCE
            "SHIELD", "DEFENSE", "ФАЙРВОЛ", "ЗАЩИТА" -> SHIELD
            "STEALTH", "BYPASS", "СТЕЛС", "ОБХОД" -> STEALTH
            else -> BRUTEFORCE
        }
    }
}

enum class HardwareType(
    val id: String,
    val label: String,
    val icon: String,
    val description: String,
    val priceBc: Long = 0L,
    val priceXp: Long = 0L
) {
    FIREWALL(
        id = "firewall",
        label = "Файрвол Военного Класса",
        icon = "🛡",
        description = "Полностью блокирует 1 атаку противника в Сетевой Войне. Сгорает при срабатывании.",
        priceBc = 400L
    ),
    ICE_TRAP(
        id = "ice_trap",
        label = "ICE-Ловушка",
        icon = "❄️",
        description = "При отражении атаки крадет 300 XP у нападающего в пользу владельца деки.",
        priceBc = 600L
    ),
    PROXY_SERVER(
        id = "proxy_server",
        label = "Прокси-Сервер (Анонимность)",
        icon = "🌐",
        description = "Скрывает узел из поиска целей на 24 часа и блокирует атаки по Вендетте.",
        priceBc = 500L,
        priceXp = 500L
    );

    val displayName: String get() = label

    companion object {
        fun fromString(str: String?): HardwareType? = entries.firstOrNull { it.name.equals(str, ignoreCase = true) || it.id.equals(str, ignoreCase = true) }
        fun fromId(id: String): HardwareType? = entries.firstOrNull { it.id.equals(id, ignoreCase = true) }
    }
}

data class PvpRoundDetail(
    val round: Int,
    val attackerProgram: PvpProgram,
    val defenderProgram: PvpProgram,
    val winner: Int // 1: Attacker, 2: Defender, 0: Tie
)

data class PvpMatchResult(
    val isWin: Boolean,
    val playerRoundsWon: Int,
    val defenderRoundsWon: Int,
    val stolenCoins: Long,
    val coinsLost: Long,
    val attackerXpGained: Long,
    val roundResults: List<PvpRoundDetail>,
    val firewallTriggered: Boolean = false,
    val iceTrapTriggered: Boolean = false,
    val xpBurnedByIceTrap: Long = 0L
)

object PvpEngine {
    const val SEARCH_COST_XP = 50L
    const val MIN_PVP_LEVEL = 4
    const val MIN_TARGET_COINS = 500L
    const val SHIELD_DURATION_MS = 4 * 60 * 60 * 1000L // 4 hours
    const val PROXY_DURATION_MS = 24 * 60 * 60 * 1000L // 24 hours
    const val BASE_MINING_REWARD_BC = 25L

    fun resolveRound(playerAction: PvpProgram, enemyAction: PvpProgram): Int {
        // Standard cyber-matrix RPS:
        // BRUTEFORCE (Брутфорс) beats STEALTH (Стелс)
        // STEALTH (Стелс) beats SHIELD (Файрвол)
        // SHIELD (Файрвол) beats BRUTEFORCE (Брутфорс)
        // Returns: 1 if player wins, 2 if enemy wins, 0 if tie
        if (playerAction == enemyAction) return 0
        return when (playerAction) {
            PvpProgram.BRUTEFORCE -> if (enemyAction == PvpProgram.STEALTH) 1 else 2
            PvpProgram.STEALTH -> if (enemyAction == PvpProgram.SHIELD) 1 else 2
            PvpProgram.SHIELD -> if (enemyAction == PvpProgram.BRUTEFORCE) 1 else 2
        }
    }

    fun resolveMatch(
        attacker: Player,
        defender: SupabasePlayer,
        attackerPrograms: List<PvpProgram>,
        defenderPrograms: List<PvpProgram>,
        attackerHardware: List<HardwareType>,
        isRevenge: Boolean = false
    ): PvpMatchResult {
        var playerWins = 0
        var defenderWins = 0
        val roundDetails = mutableListOf<PvpRoundDetail>()

        var hasAttackerFirewall = attackerHardware.contains(HardwareType.FIREWALL)
        var firewallUsed = false

        for (i in 0 until 3) {
            val atkProg = attackerPrograms.getOrElse(i) { PvpProgram.BRUTEFORCE }
            val defProg = defenderPrograms.getOrElse(i) { PvpProgram.SHIELD }
            var win = resolveRound(atkProg, defProg)

            // Hardware: Military Firewall absorbs 1 enemy win into a tie
            if (win == 2 && hasAttackerFirewall) {
                win = 0
                hasAttackerFirewall = false
                firewallUsed = true
            }

            if (win == 1) playerWins++
            else if (win == 2) defenderWins++
            roundDetails.add(PvpRoundDetail(round = i + 1, attackerProgram = atkProg, defenderProgram = defProg, winner = win))
        }

        val isWin = playerWins > defenderWins
        var stolen = 0L
        var lost = 0L
        var xpGained = 0L
        var iceTrapTriggered = false
        var xpBurned = 0L

        if (isWin) {
            val basePercentage = 0.15f
            val revengeMultiplier = if (isRevenge) 1.20f else 1.0f
            val availableCoins = maxOf(0L, defender.biocoins)
            stolen = if (availableCoins > 0) {
                minOf(availableCoins, ((availableCoins * basePercentage) * revengeMultiplier).toLong().coerceIn(10L, 5000L))
            } else 0L
            xpGained = (100L + (defender.level * 15L))
        } else {
            lost = minOf(attacker.biocoin, (attacker.biocoin * 0.10f).toLong().coerceIn(25L, 1000L))
            xpGained = 20L

            // Defender ICE-Trap: burns 300 XP from attacker
            val defHw = defender.installed_hardware ?: ""
            if (defHw.contains("ice_trap", ignoreCase = true)) {
                iceTrapTriggered = true
                xpBurned = minOf(300L, attacker.xp)
            }
        }

        return PvpMatchResult(
            isWin = isWin,
            playerRoundsWon = playerWins,
            defenderRoundsWon = defenderWins,
            stolenCoins = stolen,
            coinsLost = lost,
            attackerXpGained = xpGained,
            roundResults = roundDetails,
            firewallTriggered = firewallUsed,
            iceTrapTriggered = iceTrapTriggered,
            xpBurnedByIceTrap = xpBurned
        )
    }
}
