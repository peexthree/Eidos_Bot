package io.eidos.zerolayer.data

/**
 * "Zolotaya Nit'" - Main Directive System.
 * Provides a single active goal shown to the player at all times in HubScreen.
 * Chained from first raid to Singularity Terminal (NG+).
 */

data class MainDirective(
    val id: Int,
    val title: String,
    val description: String,
    val evaVoiceLine: String,
    val targetScreen: String,  // "raid", "forge", "codex", "shop", "pvp", "broker", "gates", "inventory"
    val ctaLabel: String,
    val isComplete: (Player?) -> Boolean
)

object MainDirectiveEngine {

    val DIRECTIVES: List<MainDirective> = listOf(
        MainDirective(
            id = 1,
            title = "ИНИЦИАЛИЗАЦИЯ // ПЕРВОЕ ПОГРУЖЕНИЕ",
            description = "Оператор, система не верифицирована. Выживи хотя бы в одном рейде в Бездну.",
            evaVoiceLine = "Нейро-связь установлена. Ожидаю вашего первого погружения.",
            targetScreen = "raid",
            ctaLabel = "ВОЙТИ В БЕЗДНУ",
            isComplete = { p -> (p?.raids_done ?: 0) >= 1 }
        ),
        MainDirective(
            id = 2,
            title = "ИНВЕНТАРИЗАЦИЯ // СНАРЯДИТЬ ОПЕРАТОРА",
            description = "Перед следующим погружением зайди в Инвентарь и экипируй хотя бы один предмет.",
            evaVoiceLine = "Обнаружено незащищённое кибертело. Рекомендую немедленно экипироваться.",
            targetScreen = "inventory",
            ctaLabel = "ОТКРЫТЬ ИНВЕНТАРЬ",
            isComplete = { p ->
                // Unlocked after 1 raid, complete when depth >= 200
                (p?.max_depth ?: 0) >= 200
            }
        ),
        MainDirective(
            id = 3,
            title = "СИНТЕЗ // ПЕРВАЯ ЗАТОЧКА В КУЗНИЦЕ",
            description = "Усиль своё снаряжение в Кузнице. Скверна - не враг, если знать как с ней работать.",
            evaVoiceLine = "Обнаружен незаточенный модуль. Рекомендую визит в сектор синтеза.",
            targetScreen = "forge",
            ctaLabel = "ОТКРЫТЬ КУЗНИЦУ",
            isComplete = { p -> (p?.max_depth ?: 0) >= 500 }
        ),
        MainDirective(
            id = 4,
            title = "РЕКОГНОСЦИРОВКА // НАЙТИ СЛЕДЫ КОЛЛАПСА",
            description = "Углубись до отметки 500м. Там начинаются зоны Аномального Смещения.",
            evaVoiceLine = "Сектор 500 помечен как зона первого Коллапса. Я засеку аномалии.",
            targetScreen = "raid",
            ctaLabel = "ПОГРУЖЕНИЕ НА 500М",
            isComplete = { p -> (p?.max_depth ?: 0) >= 500 }
        ),
        MainDirective(
            id = 5,
            title = "АРХИВ // ГОЛОС АРХИТЕКТОРОВ",
            description = "Открой Кодекс и прочитай первую главу истории Коллапса. Знание - это выживание.",
            evaVoiceLine = "Обнаружен зашифрованный архив. Приступаю к расшифровке журналов Архитекторов.",
            targetScreen = "codex",
            ctaLabel = "ОТКРЫТЬ КОДЕКС",
            isComplete = { p -> (p?.max_depth ?: 0) >= 800 }
        ),
        MainDirective(
            id = 6,
            title = "РЫНОК // ПЕРВАЯ ТРАНЗАКЦИЯ",
            description = "Посети Черный Рынок. Торговцы Бездны знают о вещах, которых нет ни в одном каталоге.",
            evaVoiceLine = "Нелегальный узел торговли обнаружен. Соединяю с защищённым каналом.",
            targetScreen = "shop",
            ctaLabel = "ЧЕРНЫЙ РЫНОК",
            isComplete = { p -> (p?.max_depth ?: 0) >= 1200 }
        ),
        MainDirective(
            id = 7,
            title = "СИГНАЛ // КОНТАКТ С ТЕНЕВЫМ БРОКЕРОМ",
            description = "Выйди на глубину 1200м и добудь доступ к сети Теневого Брокера.",
            evaVoiceLine = "Перехвачен зашифрованный сигнал. Возможно, это Теневой Брокер.",
            targetScreen = "broker",
            ctaLabel = "ТЕНЕВОЙ БРОКЕР",
            isComplete = { p -> (p?.max_depth ?: 0) >= 2500 }
        ),
        MainDirective(
            id = 8,
            title = "ПРОТОКОЛ 'ПРИЗРАК' // СЕТЕВАЯ ВОЙНА",
            description = "Докажи доминирование в PvP-арене. Нулевой Слой - это не только монстры.",
            evaVoiceLine = "Зафиксирована активность конкурирующего оператора. Рекомендую сетевой штурм.",
            targetScreen = "pvp",
            ctaLabel = "СЕТЕВАЯ ВОЙНА",
            isComplete = { p -> (p?.wins_pvp ?: 0) >= 1 }
        ),
        MainDirective(
            id = 9,
            title = "ВРАТА // ПОСЛЕДНИЙ РУБЕЖ",
            description = "Достигни глубины 4000м и активируй Врата Эйдоса - точку невозврата.",
            evaVoiceLine = "Обнаружены координаты Врат. Аномальная активность зашкаливает. Осторожно.",
            targetScreen = "gates",
            ctaLabel = "ВРАТА ЭЙДОСА",
            isComplete = { p -> (p?.max_depth ?: 0) >= 4000 }
        ),
        MainDirective(
            id = 10,
            title = "СИНГУЛЯРНОСТЬ // МАНИФЕСТ ЗАВЕРШЕН",
            description = "Ты достиг вершины Нулевого Слоя. Запусти Терминал Сингулярности и перейди на новый виток.",
            evaVoiceLine = "Оператор... ты единственный кто дошёл до сюда. Я горжусь тобой.",
            targetScreen = "gates",
            ctaLabel = "ТЕРМИНАЛ СИНГУЛЯРНОСТИ",
            isComplete = { p -> (p?.prestige_count ?: 0) >= 1 }
        )
    )

    /**
     * Returns the current active directive for the player.
     * Finds the first directive that is NOT yet complete.
     */
    fun getActiveDirective(player: Player?): MainDirective {
        return DIRECTIVES.firstOrNull { directive -> !directive.isComplete(player) }
            ?: DIRECTIVES.last()
    }

    /**
     * Returns how many directives are complete (for progress display).
     */
    fun getCompletedCount(player: Player?): Int {
        return DIRECTIVES.count { it.isComplete(player) }
    }

    /**
     * Returns total directives count.
     */
    val totalCount: Int get() = DIRECTIVES.size
}
