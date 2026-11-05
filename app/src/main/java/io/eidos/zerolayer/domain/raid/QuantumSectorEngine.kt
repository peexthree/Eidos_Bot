package io.eidos.zerolayer.domain.raid

import androidx.annotation.DrawableRes
import io.eidos.zerolayer.R

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
    @DrawableRes val iconRes: Int,
    val riskLevel: SectorRiskLevel
) {
    FRAGILE_CORE(
        id = "mutator_fragile_core",
        title = "Хрупкое Ядро",
        description = "Враг наносит +30% урона, но его HP снижено вдвое. Дроп BioCoins x2!",
        iconRes = R.drawable.ic_action_crit,
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    LASER_VAULT(
        id = "mutator_laser_vault",
        title = "Запечатанный Бункер",
        description = "Гарантированный тайник/кэш, но вход сквозь лазерную сеть стоит 10 EP.",
        iconRes = R.drawable.ic_ui_locked,
        riskLevel = SectorRiskLevel.LOW
    ),
    MAXWELL_RIFT(
        id = "mutator_maxwell_rift",
        title = "Разлом Максвелла",
        description = "Алтарь Коррупции / Элитный Фантом. Высокий шанс добыть Осколки Эйдоса!",
        iconRes = R.drawable.ic_event_anomaly,
        riskLevel = SectorRiskLevel.EXTREME
    ),
    ANTIGRAVITY(
        id = "mutator_antigravity",
        title = "Антигравитация",
        description = "Навыки и Овердрайв стоят 0 EP, но восстанавливающие аптечки заблокированы.",
        iconRes = R.drawable.ic_action_skill,
        riskLevel = SectorRiskLevel.HIGH
    ),
    GOLD_RUSH(
        id = "mutator_gold_rush",
        title = "Золотая Лихорадка",
        description = "Каждый удар по врагу выбивает +20-40 BioCoins прямо во время боя!",
        iconRes = R.drawable.ic_res_biocoin,
        riskLevel = SectorRiskLevel.LOW
    ),
    ECHOES_PAST(
        id = "mutator_echoes_past",
        title = "Эхо Прошлого",
        description = "Резонанс Бездны: повышенный шанс встретить Цифровую Могилу или Реликвию.",
        iconRes = R.drawable.ic_event_grave,
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    GLITCH_STORM(
        id = "mutator_glitch_storm",
        title = "Глитч-Шторм",
        description = "Помехи искажают бой, но вероятность выбить Легендарный предмет повышена на +40%!",
        iconRes = R.drawable.ic_event_danger,
        riskLevel = SectorRiskLevel.HIGH
    ),
    CYBER_VAMPIRISM(
        id = "mutator_cyber_vampirism",
        title = "Кибер-Вампиризм",
        description = "Все атаки восстанавливают +25% HP, но Стойка Защиты расходует 5 EP.",
        iconRes = R.drawable.ic_action_blood_overdrive,
        riskLevel = SectorRiskLevel.MEDIUM
    ),
    NEURO_OVERLOAD(
        id = "mutator_neuro_overload",
        title = "Нейро-Перегрузка",
        description = "Овердрайв заряжается в 2 раза быстрее, атаки врагов яростнее (+25% ATK).",
        iconRes = R.drawable.ic_res_overdrive,
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
    @DrawableRes val iconRes: Int,
    val eventType: String, // "combat", "cache", "anomaly", "rift", "bunker"
    val riskLevel: SectorRiskLevel,
    val mutator: SectorMutator,
    val isEncrypted: Boolean = false,
    val costEnergy: Int = 5,
    val costHp: Int = 0,
    val narrativeAction: String = "",
    val narrativeHint: String = ""
)

data class NarrativeDescentChoice(
    val actionText: String,
    val hintText: String,
    val sector: QuantumSector
)

data class DescentScenario(
    val id: String,
    val title: String,
    val loreDescription: String,
    val choices: List<NarrativeDescentChoice>
)

object QuantumSectorEngine {

    private data class ScenarioTemplate(
        val id: String,
        val title: String,
        val loreDescription: String,
        val action1: String,
        val hint1: String,
        val action2: String,
        val hint2: String,
        val action3: String,
        val hint3: String
    )

    private val SCENARIO_TEMPLATES = listOf(
        ScenarioTemplate(
            id = "pulsing_rift",
            title = "ПУЛЬСИРУЮЩИЙ РАЗЛОМ КОДА",
            loreDescription = "Вы обнаружили пространственный разрыв в топологии сектора. Из дыры в полу бьет пульсирующий синий луч данных, а от стен эхом отражаются низкие частоты системных команд...",
            action1 = "Спуститься в пульсирующую дыру",
            hint1 = "[РАЗЛОМ] Высокий риск • Редкие ядра данных",
            action2 = "Обойти разлом по правому коридору",
            hint2 = "[СТАБИЛЬНОСТЬ] Безопасный переход • Минимум риска",
            action3 = "Взломать консоль стабилизатора рядом",
            hint3 = "[ТАЙНИК] Взлом ячейки • Ценные трофеи (-10 EP)"
        ),
        ScenarioTemplate(
            id = "shattered_gateway",
            title = "РАСКОЛОТЫЙ СЕРВЕРНЫЙ ШЛЮЗ",
            loreDescription = "Коридор упирается в массивную бронированную гермодверь с эмблемой Синдиката. Замки оплавлены, а по периметру мерцают аварийные светодиоды...",
            action1 = "Прорваться сквозь аварийный клапан",
            hint1 = "[БУНКЕР] Запечатанный склад • Гарантированный лут",
            action2 = "Пойти по техническому туннелю слева",
            hint2 = "[ОБХОД] Стандартный вектор • Разведка периметра",
            action3 = "Атаковать заклинивший шлюз напрямую",
            hint3 = "[ОХОТА] Прямой контакт с защитным кодом"
        ),
        ScenarioTemplate(
            id = "warped_crossroad",
            title = "ПЕРЕКРЕСТОК ИСКАЖЕННОЙ РЕАЛЬНОСТИ",
            loreDescription = "Пространство сектора расщепилось на три зеркальных потока. В воздухе зависли застывшие пакеты данных и отзвуки чужих переговоров...",
            action1 = "Шагнуть в центральный световод",
            hint1 = "[АНОМАЛИЯ] Экстремальный риск • Алтарь Максвелла",
            action2 = "Двигаться по затемненному правому рукаву",
            hint2 = "[ШИФРОВАННЫЙ УЗЕЛ] Требуется анализ • Скрытый путь",
            action3 = "Следовать за мерцающей цепочкой данных",
            hint3 = "[РЕСУРСЫ] Поиск потерянных кэшей BioCoins"
        ),
        ScenarioTemplate(
            id = "drone_hive",
            title = "ОХРАННЫЙ ПЕРИМЕТР ДРОНОВ",
            loreDescription = "Датчики фиксируют механический гул автономных дронов-стражей. Они кружат над разрушенной серверной стойкой Архива...",
            action1 = "Атаковать ведущего дрона и зачистить сектор",
            hint1 = "[БОЙ] Охотничий сектор • Опыт и боевые трофеи",
            action2 = "Обойти патруль через нижние служебные лазы",
            hint2 = "[ТИХИЙ СПУСК] Безопасная траектория • Стандартный шаг",
            action3 = "Перехватить частоту управления дронами",
            hint3 = "[ВЗЛОМ] Взлом командной частоты • Кэш данных"
        ),
        ScenarioTemplate(
            id = "entropy_vent",
            title = "МАГИСТРАЛЬ УТЕЧКИ ЭНТРОПИИ",
            loreDescription = "Под ногами вибрирует магистральная шина. Каждые несколько секунд по настилу пробегает волна статических искр, растворяя пиксели в воздухе...",
            action1 = "Совершить стремительный рывок вперед",
            hint1 = "[РИСК] Спуск на пределе скорости • Двойной лут",
            action2 = "Спуститься в дренажный колодец под шиной",
            hint2 = "[ТАЙНИК] Укрытие от перегрузки • Контейнер данных",
            action3 = "Выждать затухание волны и идти размеренно",
            hint3 = "[СТАБИЛЬНОСТЬ] Контроль сигнала • Минимум потерь"
        ),
        ScenarioTemplate(
            id = "ghost_catacombs",
            title = "КЛАДБИЩЕ ОЦИФРОВАННЫХ ДУШ",
            loreDescription = "Вдоль стен выстроились полуразрушенные капсулы спящих разумов. Некоторые мерцают тусклым зеленым светом, другие покрыты черным нагаром Великого Глитча...",
            action1 = "Осмотреть мерцающую зеленую капсулу",
            hint1 = "[РЕСТАВРАЦИЯ] Шанс подзарядки • Восстановление HP",
            action2 = "Спуститься глубже по центральной шахте",
            hint2 = "[СТАНДАРТ] Основной вектор погружения",
            action3 = "Исследовать нагар черного глитча",
            hint3 = "[АНОМАЛИЯ] Погружение в Глитч-Шторм • Опасность"
        ),
        ScenarioTemplate(
            id = "shadow_sanctuary",
            title = "ТАЙНОЕ УБЕЖИЩЕ БРОКЕРА",
            loreDescription = "На стене загорается скрытый неоновый глиф. Перед вами узкий проход, искусно замаскированный под нерабочий шкаф коммутации...",
            action1 = "Свернуть в тайный неоновый проход",
            hint1 = "[БРОКЕР] Черный рынок • Эксклюзивные предложения",
            action2 = "Продолжить движение по главному тракту",
            hint2 = "[СПУСК] Обычный маршрут через сектор",
            action3 = "Оставить метку на терминале и забрать остатки",
            hint3 = "[ДРОП] Дополнительные BioCoins из терминала"
        ),
        ScenarioTemplate(
            id = "photon_bridge",
            title = "ФОТОННЫЙ МОСТ НАД БЕЗДНОЙ",
            loreDescription = "Перед вами обрыв, уходящий в бесконечную черноту Нулевого Слоя. Через пропасть перекинут мерцающий фотонный мост, который периодически отключается...",
            action1 = "Перебежать мост на полной скорости",
            hint1 = "[ДИНАМИКА] Быстрый переход на глубину",
            action2 = "Искать обходной карниз вдоль левой стены",
            hint2 = "[ОСТОРОЖНОСТЬ] Надежный путь без риска падения",
            action3 = "Подключиться к генератору моста и замкнуть цепь",
            hint3 = "[ВЗЛОМ] Стабилизация моста • Защищенный кэш"
        )
    )

    fun generateDescentScenario(
        depth: Int,
        isScanned: Boolean,
        hasCompass: Boolean = false
    ): DescentScenario {
        val template = SCENARIO_TEMPLATES.random()
        val mutatorsPool = SectorMutator.entries.shuffled()

        // Choice 1: Action 1
        val s1Mutator = mutatorsPool[0]
        val sector1 = QuantumSector(
            id = "sec_choice_1",
            title = template.action1.uppercase(),
            subTitle = s1Mutator.title,
            iconRes = R.drawable.ic_action_attack,
            eventType = "combat",
            riskLevel = s1Mutator.riskLevel,
            mutator = s1Mutator,
            costEnergy = 5,
            narrativeAction = template.action1,
            narrativeHint = template.hint1
        )

        // Choice 2: Action 2
        val s2Mutator = mutatorsPool[1]
        val isLaserVault = s2Mutator == SectorMutator.LASER_VAULT
        val sector2 = QuantumSector(
            id = "sec_choice_2",
            title = template.action2.uppercase(),
            subTitle = s2Mutator.title,
            iconRes = R.drawable.ic_event_chest,
            eventType = if (isLaserVault) "bunker" else "cache",
            riskLevel = s2Mutator.riskLevel,
            mutator = s2Mutator,
            costEnergy = if (isLaserVault) 10 else 5,
            narrativeAction = template.action2,
            narrativeHint = template.hint2
        )

        // Choice 3: Action 3 (Encrypted by Fog of War unless scanned)
        val s3Mutator = mutatorsPool[2]
        val shouldEncrypt = !isScanned && !hasCompass
        val sector3 = QuantumSector(
            id = "sec_choice_3",
            title = if (shouldEncrypt) "ЗАШИФРОВАННЫЙ ВЕКТОР" else template.action3.uppercase(),
            subTitle = if (shouldEncrypt) "СИГНАЛ СКРЫТ // ТРЕБУЕТСЯ СКАН" else s3Mutator.title,
            iconRes = if (shouldEncrypt) R.drawable.ic_event_unknown else R.drawable.ic_event_anomaly,
            eventType = if (shouldEncrypt) "unknown" else "rift",
            riskLevel = if (shouldEncrypt) SectorRiskLevel.HIGH else s3Mutator.riskLevel,
            mutator = s3Mutator,
            isEncrypted = shouldEncrypt,
            costEnergy = 5,
            narrativeAction = if (shouldEncrypt) "Исследовать неизвестный вектор" else template.action3,
            narrativeHint = if (shouldEncrypt) "[ТУМАН ВОЙНЫ] Нужен тактический сканер" else template.hint3
        )

        val choices = listOf(
            NarrativeDescentChoice(sector1.narrativeAction, sector1.narrativeHint, sector1),
            NarrativeDescentChoice(sector2.narrativeAction, sector2.narrativeHint, sector2),
            NarrativeDescentChoice(sector3.narrativeAction, sector3.narrativeHint, sector3)
        )

        return DescentScenario(
            id = template.id,
            title = template.title,
            loreDescription = template.loreDescription,
            choices = choices
        )
    }

    fun generateSectorChoices(
        depth: Int,
        isScanned: Boolean,
        hasCompass: Boolean = false
    ): List<QuantumSector> {
        return generateDescentScenario(depth, isScanned, hasCompass).choices.map { it.sector }
    }
}

