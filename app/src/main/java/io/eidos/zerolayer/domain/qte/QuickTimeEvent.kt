package io.eidos.zerolayer.domain.qte

import kotlin.random.Random

/**
 * QTE-вставки спуска (quick-time events): короткие интерактивные события
 * с жестами, всплывающие на мирных событиях (обнаружение тайника).
 * Награды/штрафы применяются только через GameRepository.applyQteResult -
 * UI не трогает экономику напрямую. Смерть от QTE невозможна (пол 1 HP).
 */
enum class QteType(
    val id: String,
    val title: String,
    val instruction: String
) {
    STABILIZE(
        id = "qte_stabilize",
        title = "СТАБИЛИЗАЦИЯ ПОТОКА",
        instruction = "ТАПНИ, КОГДА МАРКЕР В ЦЕЛЕВОЙ ЗОНЕ"
    ),
    DODGE(
        id = "qte_dodge",
        title = "УКЛОНЕНИЕ ОТ ИЩЕЙКИ",
        instruction = "СВАЙПНИ В НАПРАВЛЕНИИ СТРЕЛКИ"
    ),
    GLITCH_PURGE(
        id = "qte_glitch_purge",
        title = "ГЛИТЧ-МАРКЕРЫ",
        instruction = "ПОГАСИ ВСЕ МАРКЕРЫ ДО РАСПАДА"
    );

    companion object {
        fun fromId(id: String?): QteType? = entries.find { it.id == id }
    }
}

/** Активная QTE-вставка. id используется и как метка времени создания. */
data class ActiveQte(
    val id: Long,
    val type: QteType,
    val depth: Int,
    val seed: Int,
    val timeoutMs: Long
)

/** Итог QTE, применённый репозиторием (для тостов/флеша UI). */
data class QteOutcome(
    val success: Boolean,
    val coinGain: Long = 0L,
    val xpGain: Long = 0L,
    val energyGain: Int = 0,
    val hpLoss: Int = 0
)

object QteEngine {

    /** Шанс триггера на мирном событии лута. */
    const val TRIGGER_CHANCE = 0.5f

    /** Минимум шагов спуска между QTE. */
    const val COOLDOWN_STEPS = 3

    /** Окно реакции, мс. */
    const val TIMEOUT_MS = 2600L

    /** Экран результата (вспышка УСПЕХ/СРЫВ), мс. */
    const val RESULT_FLASH_MS = 600L

    /** Мирные события, на которых допустима QTE (не бой/аномалия/загадка/форк). */
    val ALLOWED_EVENT_TYPES = setOf("loot", "cursed_loot")

    /** Протухшая QTE (>10с без ответа) принудительно гасится в ViewModel. */
    const val STALE_MS = 10_000L

    fun pickType(rng: Random = Random): QteType = QteType.entries.random(rng)
}
