package io.eidos.zerolayer.domain.raid

enum class SectorRiskLevel(val label: String, val colorHex: Long) {
    LOW("НИЗКИЙ РИСК", 0xFF00E676),
    MEDIUM("УМЕРЕННЫЙ РИСК", 0xFFFFD600),
    HIGH("ВЫСОКИЙ РИСК", 0xFFFF9100),
    EXTREME("ЭКСТРЕМАЛЬНЫЙ РАЗЛОМ", 0xFFFF1744)
}

enum class SectorMutator(
    val id: String,
    val title: String,
    val description: String,
    val icon: String,
    val riskLevel: SectorRiskLevel
) {
    FRAGILE_CORE(
        id = "mutator_fragile_core",
        title = "Хрупкое Ядро",
        description = "Враг наносит +30% урона, но его HP снижено вдвое. Дроп BioCoins x2!",
        icon = "💥",
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    LASER_VAULT(
        id = "mutator_laser_vault",
        title = "Запечатанный Бункер",
        description = "Гарантированный тайник/кэш, но вход сквозь лазерную сеть стоит 10 EP.",
        icon = "🔒",
        riskLevel = SectorRiskLevel.LOW
    ),
    MAXWELL_RIFT(
        id = "mutator_maxwell_rift",
        title = "Разлом Максвелла",
        description = "Алтарь Коррупции / Элитный Фантом. Высокий шанс добыть Осколки Эйдоса!",
        icon = "🌀",
        riskLevel = SectorRiskLevel.EXTREME
    ),
    ANTIGRAVITY(
        id = "mutator_antigravity",
        title = "Антигравитация",
        description = "Навыки и Овердрайв стоят 0 EP, но восстанавливающие аптечки заблокированы.",
        icon = "🌌",
        riskLevel = SectorRiskLevel.HIGH
    ),
    GOLD_RUSH(
        id = "mutator_gold_rush",
        title = "Золотая Лихорадка",
        description = "Каждый удар по врагу выбивает +20-40 BioCoins прямо во время боя!",
        icon = "🪙",
        riskLevel = SectorRiskLevel.LOW
    ),
    ECHOES_PAST(
        id = "mutator_echoes_past",
        title = "Эхо Прошлого",
        description = "Резонанс Бездны: повышенный шанс встретить Цифровую Могилу или Реликвию.",
        icon = "🪦",
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    GLITCH_STORM(
        id = "mutator_glitch_storm",
        title = "Глитч-Шторм",
        description = "Помехи искажают бой, но вероятность выбить Легендарный предмет повышена на +40%!",
        icon = "⚡",
        riskLevel = SectorRiskLevel.HIGH
    ),
    CYBER_VAMPIRISM(
        id = "mutator_cyber_vampirism",
        title = "Кибер-Вампиризм",
        description = "Все атаки восстанавливают +25% HP, но Стойка Защиты расходует 5 EP.",
        icon = "🩸",
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    NEURO_OVERLOAD(
        id = "mutator_neuro_overload",
        title = "Нейро-Перегрузка",
        description = "Овердрайв заряжается в 2 раза быстрее, атаки врагов яростнее (+25% ATK).",
        icon = "🧠",
        riskLevel = SectorRiskLevel.HIGH
    );

    companion object {
        fun fromId(id: String?): SectorMutator? = entries.find { it.id == id }
    }
}

data class QuantumSector(
    val id: String,
    val title: String,
    val subTitle: String,
    val icon: String,
    val eventType: String, // "combat", "cache", "anomaly", "rift", "bunker"
    val riskLevel: SectorRiskLevel,
    val mutator: SectorMutator,
    val isEncrypted: Boolean = false,
    val costEnergy: Int = 5,
    val costHp: Int = 0
)

object QuantumSectorEngine {

    fun generateSectorChoices(
        depth: Int,
        isScanned: Boolean,
        hasCompass: Boolean = false
    ): List<QuantumSector> {
        val mutatorsPool = SectorMutator.entries.shuffled()

        // Sector 1: Combat or Hunting sector
        val s1Mutator = mutatorsPool[0]
        val sector1 = QuantumSector(
            id = "sec_combat",
            title = "ОХОТНИЧИЙ СЕКТОР",
            subTitle = s1Mutator.title,
            icon = "⚔️",
            eventType = "combat",
            riskLevel = s1Mutator.riskLevel,
            mutator = s1Mutator,
            costEnergy = 5
        )

        // Sector 2: Vault / Cache / Resource
        val s2Mutator = mutatorsPool[1]
        val isLaserVault = s2Mutator == SectorMutator.LASER_VAULT
        val sector2 = QuantumSector(
            id = "sec_vault",
            title = if (isLaserVault) "ЗАПЕЧАТАННЫЙ БУНКЕР" else "ТАКТИЧЕСКИЙ ТАЙНИК",
            subTitle = s2Mutator.title,
            icon = if (isLaserVault) "📦" else "🧰",
            eventType = if (isLaserVault) "bunker" else "cache",
            riskLevel = s2Mutator.riskLevel,
            mutator = s2Mutator,
            costEnergy = if (isLaserVault) 10 else 5
        )

        // Sector 3: High-Risk Rift / Anomaly (Encrypted by Fog of War unless scanned)
        val s3Mutator = mutatorsPool[2]
        val shouldEncrypt = !isScanned && !hasCompass
        val sector3 = QuantumSector(
            id = "sec_rift",
            title = if (shouldEncrypt) "ЗАШИФРОВАННЫЙ УЗЕЛ" else "РАЗЛОМ МАКСВЕЛЛА",
            subTitle = if (shouldEncrypt) "СИГНАЛ СКРЫТ // ТРЕБУЕТСЯ СКАН" else s3Mutator.title,
            icon = if (shouldEncrypt) "❓" else "🌀",
            eventType = if (shouldEncrypt) "unknown" else "rift",
            riskLevel = if (shouldEncrypt) SectorRiskLevel.HIGH else s3Mutator.riskLevel,
            mutator = s3Mutator,
            isEncrypted = shouldEncrypt,
            costEnergy = 5
        )

        return listOf(sector1, sector2, sector3)
    }
}
