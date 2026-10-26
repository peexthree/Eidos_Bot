package io.eidos.zerolayer.domain.anomaly

import io.eidos.zerolayer.data.Player
import kotlin.random.Random

object ZalgoHelper {
    private val ZALGO_UP = listOf(
        '\u030d', '\u030e', '\u0304', '\u0305', '\u033f', '\u0311', '\u0306', '\u0310', '\u0352', '\u0357',
        '\u0351', '\u0307', '\u0308', '\u030a', '\u0342', '\u0343', '\u0344', '\u034a', '\u034b', '\u034c'
    )
    private val ZALGO_DOWN = listOf(
        '\u0316', '\u0317', '\u0318', '\u0319', '\u031c', '\u031d', '\u031e', '\u031f', '\u0320', '\u0324',
        '\u0325', '\u0326', '\u0329', '\u032a', '\u032b', '\u032c', '\u032d', '\u032e', '\u032f', '\u0330'
    )
    private val ZALGO_MID = listOf(
        '\u0315', '\u031b', '\u0340', '\u0341', '\u0358', '\u0321', '\u0322', '\u0327', '\u0328', '\u0334',
        '\u0335', '\u0336', '\u034f', '\u035c', '\u035d', '\u035e', '\u035f', '\u0360', '\u0362', '\u0338'
    )

    fun toZalgo(text: String, intensity: Int = 2): String {
        val sb = StringBuilder()
        for (c in text) {
            sb.append(c)
            if (c.isLetterOrDigit()) {
                repeat(intensity) {
                    sb.append(ZALGO_UP.random())
                    sb.append(ZALGO_MID.random())
                    sb.append(ZALGO_DOWN.random())
                }
            }
        }
        return sb.toString()
    }
}

object AnomalyEngine {
    const val BUFF_OVERLOAD = "overload"
    const val BUFF_STEALTH_NIGHT = "stealth_night"
    const val BUFF_GLITCH_BERSERK = "glitch_berserk"
    const val BUFF_VISUAL_DISTORTION = "visual_distortion"
    const val BUFF_MAXWELL_OVERCLOCK = "maxwell_overclock"
    const val BUFF_MAXWELL_FORTUNE = "maxwell_fortune"
    const val BUFF_MAXWELL_VULNERABILITY = "maxwell_vulnerability"
    const val BUFF_MAXWELL_ENTROPY_SHIELD = "maxwell_entropy_shield"

    const val BUFF_DURATION_SECONDS = 3600L // 1 hour

    data class MicroGlitchResult(
        val buffType: String,
        val title: String,
        val description: String,
        val expiryTimestamp: Long,
        val newGlitchCounter: Int
    )

    fun isBuffActive(player: Player?, buffType: String): Boolean {
        if (player == null) return false
        val nowSec = System.currentTimeMillis() / 1000L
        return player.anomalyBuffType == buffType && nowSec < player.anomalyBuffExpiry
    }

    fun isVisualDistortionActive(player: Player?): Boolean {
        return isBuffActive(player, BUFF_VISUAL_DISTORTION) || player?.isGlitched == true
    }

    fun getActiveBuffRemainingSeconds(player: Player?): Long {
        if (player == null) return 0L
        val nowSec = System.currentTimeMillis() / 1000L
        return maxOf(0L, player.anomalyBuffExpiry - nowSec)
    }

    fun getBuffTitle(buffType: String?): String {
        return when (buffType) {
            BUFF_OVERLOAD -> "⚡ [ПЕРЕГРУЗКА ЯДРА]"
            BUFF_STEALTH_NIGHT -> "🌙 [НОЧНАЯ СКРЫТНОСТЬ]"
            BUFF_GLITCH_BERSERK -> "🔥 [ГЛИТЧ-БЕРСЕРК]"
            BUFF_VISUAL_DISTORTION -> "🌀 [ИСКАЖЕНИЕ РЕАЛЬНОСТИ]"
            BUFF_MAXWELL_OVERCLOCK -> "🩸 [КРОВАВЫЙ ОВЕРКЛОК]"
            BUFF_MAXWELL_FORTUNE -> "🎲 [ИНВЕРСИЯ ФОРТУНЫ]"
            BUFF_MAXWELL_VULNERABILITY -> "⚠️ [УЯЗВИМОСТЬ ЭНТРОПИИ]"
            BUFF_MAXWELL_ENTROPY_SHIELD -> "🛡️ [ЭНТРОПИЙНЫЙ ЩИТ]"
            else -> "✨ [НЕЙРО-АНОМАЛИЯ]"
        }
    }

    fun getBuffDescription(buffType: String?): String {
        return when (buffType) {
            BUFF_OVERLOAD -> "+50% BioCoins во всех событиях добычи лута (1 ч)."
            BUFF_STEALTH_NIGHT -> "30% шанс обойти опасную комнату/патруль без боя и потери Сигнала (1 ч)."
            BUFF_GLITCH_BERSERK -> "+25% к атаке и критическому урону в бою с глитч-эффектом (1 ч)."
            BUFF_VISUAL_DISTORTION -> "Искажает системные заголовки и загадки в Zalgo-стиль (1 ч)."
            BUFF_MAXWELL_OVERCLOCK -> "+35% к урону (ATK) и +15% к шансу крита в текущем рейде."
            BUFF_MAXWELL_FORTUNE -> "x2 шанс выпадения Реликвий и Зашифрованных кэшей."
            BUFF_MAXWELL_VULNERABILITY -> "+25% входящего урона от ловушек и врагов."
            BUFF_MAXWELL_ENTROPY_SHIELD -> "100% иммунитет к урону от любых ловушек в рейде."
            else -> "Пассивный эффект аномалии активен."
        }
    }

    /**
     * Rolls 3% chance on raid steps, crafting, or UI actions.
     * Returns a MicroGlitchResult if triggered, or null.
     */
    fun rollMicroGlitch(player: Player, hasRealitySilencer: Boolean): MicroGlitchResult? {
        if (hasRealitySilencer) return null
        val roll = Random.nextInt(100)
        if (roll >= 3) return null // 3% chance

        val buffs = listOf(BUFF_OVERLOAD, BUFF_STEALTH_NIGHT, BUFF_GLITCH_BERSERK, BUFF_VISUAL_DISTORTION)
        val selectedBuff = buffs.random()
        val expiry = (System.currentTimeMillis() / 1000L) + BUFF_DURATION_SECONDS
        val newGlitchCounter = player.glitchEncounterCounter + 1

        return MicroGlitchResult(
            buffType = selectedBuff,
            title = getBuffTitle(selectedBuff),
            description = getBuffDescription(selectedBuff),
            expiryTimestamp = expiry,
            newGlitchCounter = newGlitchCounter
        )
    }

    /**
     * Condition for Hard Glitch:
     * glitchEncounterCounter >= 3 AND elapsed time >= 24h since lastHardGlitchTimestamp
     */
    fun isHardGlitchReady(player: Player, hasRealitySilencer: Boolean): Boolean {
        if (hasRealitySilencer) return false
        val now = System.currentTimeMillis()
        val passed24h = (now - player.lastHardGlitchTimestamp) >= (24L * 3600 * 1000L)
        return player.glitchEncounterCounter >= 3 && passed24h
    }

    data class HardGlitchQuestion(
        val question: String,
        val options: List<String>,
        val correctIndex: Int,
        val explanation: String
    )

    private val STABILITY_QUESTIONS = listOf(
        HardGlitchQuestion(
            question = "СБОЙ ЭНТРОПИИ: Контрольная сумма нулевого сектора искажена. Выберите протокол выравнивания фазы:",
            options = listOf(
                "Инвертировать квантовый бит четности (PARITY_INVERT)",
                "Сбросить регистр ядра в ноль (NULL_OVERRIDE)",
                "Форсировать переполнение буфера (BUFFER_FORCE)"
            ),
            correctIndex = 0,
            explanation = "Инверсия бита четности восстановила когерентность квантового потока!"
        ),
        HardGlitchQuestion(
            question = "АНОМАЛЬНЫЙ РЕКУРСИВНЫЙ ЦИКЛ: Память зациклена на 0xDEADBEEF. Какое прерывание применить?",
            options = listOf(
                "SIGKILL_DAEMON_SYS",
                "INTERRUPT_VECTOR_0x00 (Сброс таблицы прерываний)",
                "DUMP_CORE_RETRY"
            ),
            correctIndex = 1,
            explanation = "Вектор 0x00 перезапустил адресное пространство без потери данных!"
        ),
        HardGlitchQuestion(
            question = "ГЛИТЧ-ФАНТОМ: Пакеты данных самокопируются. Требуется стабилизировать энтропийный барьер:",
            options = listOf(
                "Отключить сетевой стек",
                "Активировать протокол Максвелла (MAXWELL_SORT_HASH)",
                "Удалить системный загрузчик"
            ),
            correctIndex = 1,
            explanation = "Сортировка хэшей изолировала фантомные пакеты!"
        )
    )

    fun getRandomHardGlitchQuestion(): HardGlitchQuestion {
        return STABILITY_QUESTIONS.random()
    }
}
