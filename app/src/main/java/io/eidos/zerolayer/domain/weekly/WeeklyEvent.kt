package io.eidos.zerolayer.domain.weekly

import androidx.annotation.DrawableRes
import io.eidos.zerolayer.R
import io.eidos.zerolayer.domain.raid.SectorRiskLevel

/**
 * Недельные события / вращающиеся модификаторы.
 * Каждую ISO-неделю детерминированно (по seed недели+uid, как дейлики)
 * активируется один модификатор. Эффекты применяются в choke points
 * GameRepository (endRaid, resolveEnemyDefeat, claimChestLoot,
 * performEnemyTurn, спавн врага, regenerateEnergy, утилизация).
 *
 * Мультипликаторы: 1f = эффект отсутствует.
 */
enum class WeeklyEvent(
    val id: String,
    val title: String,
    val description: String,
    @DrawableRes val iconRes: Int,
    val riskLevel: SectorRiskLevel,
    /** Множитель BioCoins за убийства и тайники. */
    val coinMultiplier: Float = 1f,
    /** Множитель XP, списываемого в конце рейда. */
    val xpMultiplier: Float = 1f,
    /** Множитель атаки врагов. */
    val enemyAtkMultiplier: Float = 1f,
    /** Множитель HP врагов при спавне. */
    val enemyHpMultiplier: Float = 1f,
    /** Бонусный шанс (%) форса легендарного лута. */
    val legendaryChanceBonus: Int = 0,
    /** Множитель Осколков Эйдоса из утилизации/разбора. */
    val shardMultiplier: Float = 1f,
    /** Делитель интервала регена Энергии: >1 медленнее, <1 быстрее. */
    val energyRegenDivisor: Float = 1f
) {
    BLOOD_HARVEST(
        id = "weekly_blood_harvest",
        title = "Кровавая Жатва",
        description = "Все трофеи приносят +50% BioCoins, но враждебные программы стали на 25% агрессивнее.",
        iconRes = R.drawable.ic_res_biocoin,
        riskLevel = SectorRiskLevel.MEDIUM,
        coinMultiplier = 1.5f,
        enemyAtkMultiplier = 1.25f
    ),
    HUNGRY_ZERO(
        id = "weekly_hungry_zero",
        title = "Голодный Ноль",
        description = "Нейро-аккумуляторы истощены: реген Энергии на 50% медленнее. Компенсация: +30% трофеев.",
        iconRes = R.drawable.ic_res_overdrive,
        riskLevel = SectorRiskLevel.HIGH,
        coinMultiplier = 1.3f,
        energyRegenDivisor = 1.5f
    ),
    GLITCH_SURGE(
        id = "weekly_glitch_surge",
        title = "Глитч-Прилив",
        description = "Помехи Нулевого Слоя достигли пика: шанс выбить Легендарный предмет повышен на +40%.",
        iconRes = R.drawable.ic_event_danger,
        riskLevel = SectorRiskLevel.MEDIUM,
        legendaryChanceBonus = 40
    ),
    GOLD_RUSH_WEEK(
        id = "weekly_gold_rush",
        title = "Золотая Лихорадка",
        description = "Сеть переполнена кредитами: все трофеи приносят +25% BioCoins. Рисков нет.",
        iconRes = R.drawable.ic_event_anomaly,
        riskLevel = SectorRiskLevel.LOW,
        coinMultiplier = 1.25f
    ),
    NEURAL_BOOST(
        id = "weekly_neural_boost",
        title = "Нейро-Разгон",
        description = "Нейро-архивы открыты для свободного доступа: +30% опыта во всех рейдах.",
        iconRes = R.drawable.ic_action_scan,
        riskLevel = SectorRiskLevel.LOW,
        xpMultiplier = 1.3f
    ),
    DATA_STORM(
        id = "weekly_data_storm",
        title = "Шторм Данных",
        description = "Фрагменты реальности осыпаются дождем: x2 Осколков Эйдоса из утилизации.",
        iconRes = R.drawable.ic_res_eidos_shard,
        riskLevel = SectorRiskLevel.MEDIUM,
        shardMultiplier = 2f
    ),
    HUNTER_PROTOCOL(
        id = "weekly_hunter_protocol",
        title = "Неделя Ищеек",
        description = "Ищейоки активизировались: враги +20% HP и +20% атаки, но +50% опыта за рейд.",
        iconRes = R.drawable.ic_event_evac,
        riskLevel = SectorRiskLevel.HIGH,
        enemyHpMultiplier = 1.2f,
        enemyAtkMultiplier = 1.2f,
        xpMultiplier = 1.5f
    ),
    MERCY_PROTOCOL(
        id = "weekly_mercy_protocol",
        title = "Протокол Милосердия",
        description = "Ядро EIDOS щадит операторов: реген Энергии в 2 раза быстрее.",
        iconRes = R.drawable.ic_action_blood_overdrive,
        riskLevel = SectorRiskLevel.LOW,
        energyRegenDivisor = 0.5f
    );

    companion object {
        fun fromId(id: String?): WeeklyEvent? = entries.find { it.id == id }
    }
}
