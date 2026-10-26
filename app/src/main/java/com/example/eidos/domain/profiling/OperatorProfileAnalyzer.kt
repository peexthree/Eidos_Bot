package com.example.eidos.domain.profiling

import com.example.eidos.data.Player

data class Archetype(
    val name: String,
    val title: String,
    val description: String,
    val statsBonus: String,
    val recommendedStyle: String,
    val matchingQuote: String
)

object OperatorProfileAnalyzer {

    val archetypes = listOf(
        Archetype(
            name = "Хакер-Призрак",
            title = "GHOST_HACKER_V4",
            description = "Скрытный манипулятор программного кода. Предпочитает обходить защитные протоколы Бездны напрямую, используя уязвимости и стелс-интерфейсы. Вы атакуете систему в обход лобовой брони.",
            statsBonus = "⚡ +15% Удачи (Luck) и +10% Защиты (Defense)",
            recommendedStyle = "Использование Data Slicer и переролл сокетов под Синий цвет для взлома.",
            matchingQuote = "«Вирус — это не враг, это просто неоптимизированный сосед по памяти.»"
        ),
        Archetype(
            name = "Тактик Обороны",
            title = "DEFENSIVE_TACTICIAN_SEC",
            description = "Мастер выживания и энерго-барьеров. Вы тщательно рассчитываете каждый шаг в рейде, своевременно восстанавливаете уровень HP и минимизируете риски при встрече с опасными вирусными Личами.",
            statsBonus = "🛡️ +20% Макс. ОЗ (Max HP) и +15% Защиты (Defense)",
            recommendedStyle = "Установка модулей восстановления и сокетов Зеленого цвета.",
            matchingQuote = "«Ни одна Бездна не сможет уничтожить то, что защищено тройным шифрованием.»"
        ),
        Archetype(
            name = "Авантюрист Бездны",
            title = "ABYSS_ADVENTURER_99",
            description = "Безумный исследователь глубоких квантовых слоев. Для вас Бездна — это не угроза, а дом. Ваша сигнатура резонирует с аномалиями, позволяя находить редчайшие реликвии там, где другие погибают.",
            statsBonus = "🔮 +15% Критического Удара (Crit) и +15% Удачи (Luck)",
            recommendedStyle = "Рейды на глубину 10+ секторов, ставки на Аномалии.",
            matchingQuote = "«Глубина не пугает, если твоё ядро синхронизировано со скоростью света.»"
        ),
        Archetype(
            name = "Кибер-Берсерк",
            title = "CYBER_BERSERKER_RAW",
            description = "Бескомпромиссный разрушитель вирусного кода. Черпает атакующую мощь в ярости схватки. Ваши модификации нацелены на сокрушительный разовый урон и ликвидацию угроз до того, как они успеют ответить.",
            statsBonus = "⚔️ +20% Атаки (Attack) и +10% Критического Урона",
            recommendedStyle = "Прокачка навыка Berserk и установка Красных чипов силы.",
            matchingQuote = "«Лучшая антивирусная защита — это полное стирание зараженного сектора.»"
        ),
        Archetype(
            name = "Гладиатор Сети",
            title = "NET_GLADIATOR_PRO",
            description = "Закаленный ветеран PvP арен. Ваша сигнатура была проверена в бесчисленных дуэлях с другими Операторами за права администрирования локальных подсетей. Отличный тактик в поединках 1-на-1.",
            statsBonus = "🔥 +15% Атаки (Attack) и +10% Защиты (Defense)",
            recommendedStyle = "Постоянное участие в битвах PvP Арены и дуэлях.",
            matchingQuote = "«Твой пинг слишком высок, чтобы успеть заблокировать мой выстрел.»"
        ),
        Archetype(
            name = "Прагматик-Синдикат",
            title = "SYNDICATE_PRAGMATIST",
            description = "Расчетливый агент корпораций. Вы не рискуете ради славы. Главное для вас — оптимизация доходности, поиск зашифрованных кэшей, выгода при сделках со Shadow Broker и экономия BioCoins.",
            statsBonus = "💎 +20% К шансу выпадения ценностей и +5% Атаки",
            recommendedStyle = "Сбор кэшей, покупка скидок у торговца, эвакуация вовремя.",
            matchingQuote = "«Всё имеет свою цену, даже код Бездны. Главное — выгодно его продать.»"
        )
    )

    fun analyze(player: Player?): Archetype {
        if (player == null) return archetypes.last()

        val hackerPower = player.skill_hacker_1 + player.skill_hacker_2 + player.skill_hacker_3
        val berserkPower = player.skill_berserk_1 + player.skill_berserk_2 + player.skill_berserk_3
        val medicPower = player.skill_medic_1 + player.skill_medic_2 + player.skill_medic_3
        val pvpCount = player.wins_pvp + player.losses_pvp

        // Calculate scores for each archetype based on stats
        val hackerScore = hackerPower * 3 + (if (player.faction == "ТЕХНО") 5 else 0)
        val medicScore = medicPower * 3 + player.defense / 2 + (if (player.faction == "МАТЕРИЯ") 5 else 0)
        val adventurerScore = player.max_depth * 2 + player.perfect_raids * 3
        val berserkScore = berserkPower * 3 + player.kills / 5 + player.attack / 3
        val gladiatorScore = pvpCount * 3 + player.wins_pvp * 4
        val pragmatistScore = (player.biocoin / 100 + player.total_spent / 500).toInt()

        val maxScore = listOf(hackerScore, medicScore, adventurerScore, berserkScore, gladiatorScore, pragmatistScore).maxOrNull() ?: 0

        return when {
            maxScore == hackerScore && hackerScore > 0 -> archetypes[0] // Хакер-Призрак
            maxScore == medicScore && medicScore > 0 -> archetypes[1] // Тактик Обороны
            maxScore == adventurerScore && adventurerScore > 0 -> archetypes[2] // Авантюрист Бездны
            maxScore == berserkScore && berserkScore > 0 -> archetypes[3] // Кибер-Берсерк
            maxScore == gladiatorScore && gladiatorScore > 0 -> archetypes[4] // Гладиатор Сети
            else -> archetypes[5] // Прагматик-Синдикат
        }
    }
}
