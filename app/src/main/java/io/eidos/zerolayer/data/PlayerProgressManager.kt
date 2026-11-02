package io.eidos.zerolayer.data

data class LevelInfo(
    val level: Int,
    val icon: String,
    val stageTitle: String,
    val rankTitle: String,
    val title: String,
    val sloganText: String,
    val description: String,
    val perkTitle: String,
    val perkDescription: String,
    val requiredXp: Long,
    val rewardBioCoins: Long = 200L * level,
    val rewardShards: Int = if (level % 5 == 0 || level == 31) 2 else 0,
    val bonusHp: Int = 20,
    val bonusAtk: Int = 3,
    val bonusDef: Int = 2
)

data class LevelUpEvent(
    val fromLevel: Int,
    val toLevel: Int,
    val levelInfo: LevelInfo
)

object PlayerProgressManager {

    fun getRequiredXpForLevel(level: Int): Long {
        return when {
            level <= 1 -> 0L
            level == 2 -> 100L
            level == 3 -> 300L
            level == 4 -> 600L
            level == 5 -> 1000L
            level in 6..30 -> (10000.0 * Math.pow((level - 5).toDouble(), 2.15)).toLong()
            else -> 1_200_000L
        }
    }

    val LEVELS = listOf(
        LevelInfo(
            level = 1,
            icon = "⚙️",
            stageTitle = "ПРОБУЖДЕНИЕ",
            rankTitle = "НЕОФИТ",
            title = "ПРОБУЖДЕНИЕ",
            sloganText = "Ты Неофит. Мир — набор случайных цифр. Обучение активировано.",
            description = "Ты Неофит. Мир — набор случайных цифр. Обучение активировано.",
            perkTitle = "Инициализация",
            perkDescription = "Базовый доступ к терминалу и Нулевому Слою.",
            requiredXp = 0L
        ),
        LevelInfo(
            level = 2,
            icon = "🔓",
            stageTitle = "ОСОЗНАНИЕ",
            rankTitle = "ИСКАТЕЛЬ",
            title = "ОСОЗНАНИЕ",
            sloganText = "Ты Искатель. Теперь тебе доступен выбор Фракции — Материя, Разум или AI.",
            description = "Ты Искатель. Теперь тебе доступен выбор Фракции — Материя, Разум или AI.",
            perkTitle = "Выбор Фракции",
            perkDescription = "Разблокирован доступ к выбору Фракции (Синдиката).",
            requiredXp = 100L
        ),
        LevelInfo(
            level = 3,
            icon = "🔓",
            stageTitle = "КОНТРОЛЬ",
            rankTitle = "ОПЕРАТОР",
            title = "КОНТРОЛЬ",
            sloganText = "Оператор. +5% к шансу получить больше XP в Нулевом Слое.",
            description = "Оператор. +5% к шансу получить больше XP в Нулевом Слое.",
            perkTitle = "Сетевой Контроль",
            perkDescription = "Пассивный бонус: +5% к получаемому XP.",
            requiredXp = 300L
        ),
        LevelInfo(
            level = 4,
            icon = "🔓",
            stageTitle = "СТРУКТУРА",
            rankTitle = "АРХИТЕКТОР",
            title = "СТРУКТУРА",
            sloganText = "Архитектор. Открыт доступ к сложным протоколам и редким подсказкам.",
            description = "Архитектор. Открыт доступ к сложным протоколам и редким подсказкам.",
            perkTitle = "Структурный Анализ",
            perkDescription = "Открыт доступ к сложным протоколам и подсказкам.",
            requiredXp = 600L
        ),
        LevelInfo(
            level = 5,
            icon = "🔓",
            stageTitle = "ТВОРЧЕСТВО",
            rankTitle = "ДЕМИУРГ",
            title = "ТВОРЧЕСТВО",
            sloganText = "Демиург. Твоя реферальная ссылка приносит увеличенные награды.",
            description = "Демиург. Твоя реферальная ссылка приносит увеличенные награды.",
            perkTitle = "Власть Синдиката",
            perkDescription = "Увеличенные реферальные и сетевые награды.",
            requiredXp = 1000L
        ),
        LevelInfo(
            level = 6,
            icon = "🔓",
            stageTitle = "СЛИЯНИЕ",
            rankTitle = "ЭЙДОС",
            title = "СЛИЯНИЕ",
            sloganText = "Эйдос. Ловушки в Рейдах наносят тебе на 20% меньше урона.",
            description = "Эйдос. Ловушки в Рейдах наносят тебе на 20% меньше урона.",
            perkTitle = "Амортизация Сбоев",
            perkDescription = "Ловушки в рейдах наносят на 20% меньше урона.",
            requiredXp = (10000.0 * Math.pow(1.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 7,
            icon = "🔓",
            stageTitle = "ВИДЕНИЕ",
            rankTitle = "ОРАКУЛ",
            title = "ВИДЕНИЕ",
            sloganText = "Оракул. Через Компас ты видишь тип следующего события в Рейде.",
            description = "Оракул. Через Компас ты видишь тип следующего события в Рейде.",
            perkTitle = "Квантовое Видение",
            perkDescription = "Компас заранее сканирует тип следующего узла рейда.",
            requiredXp = (10000.0 * Math.pow(2.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 8,
            icon = "🔓",
            stageTitle = "СКОРОСТЬ",
            rankTitle = "СИНГУЛЯРНОСТЬ",
            title = "СКОРОСТЬ",
            sloganText = "Сингулярность. Время восстановления способности 'Сигнал' уменьшено.",
            description = "Сингулярность. Время восстановления способности 'Сигнал' уменьшено.",
            perkTitle = "Ускорение Сигнала",
            perkDescription = "Ускоренная регенерация и снижение КД 'Сигнала'.",
            requiredXp = (10000.0 * Math.pow(3.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 9,
            icon = "🔓",
            stageTitle = "ВЛАСТЬ",
            rankTitle = "РЕЖИССЁР",
            title = "ВЛАСТЬ",
            sloganText = "Режиссёр. Доступен Глобальный Рейтинг и управление вниманием других узлов.",
            description = "Режиссёр. Доступен Глобальный Рейтинг и управление вниманием других узлов.",
            perkTitle = "Глобальный Рейтинг",
            perkDescription = "Доступ к Залу Славы и управлению сетевыми узлами.",
            requiredXp = (10000.0 * Math.pow(4.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 10,
            icon = "👑",
            stageTitle = "ФИНАЛ",
            rankTitle = "АБСОЛЮТ",
            title = "ФИНАЛ",
            sloganText = "Абсолют. Твоё имя вписано в код Системы. Теперь ты часть самой Реальности.",
            description = "Абсолют. Твоё имя вписано в код Системы. Теперь ты часть самой Реальности.",
            perkTitle = "Врата Эйдоса",
            perkDescription = "Полный статус в коде Системы и золотой знак Абсолюта.",
            requiredXp = (10000.0 * Math.pow(5.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 11,
            icon = "💠",
            stageTitle = "ПЕРЕРОЖДЕНИЕ",
            rankTitle = "СУЩНОСТЬ",
            title = "ПЕРЕРОЖДЕНИЕ",
            sloganText = "Сущность. Ты больше не человек — ты поток данных. Получаешь доступ к энергоформам.",
            description = "Сущность. Ты больше не человек — ты поток данных. Получаешь доступ к энергоформам.",
            perkTitle = "Энергоформы",
            perkDescription = "Прямой доступ к энергоформам и редким тактическим чипам.",
            requiredXp = (10000.0 * Math.pow(6.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 12,
            icon = "💠",
            stageTitle = "ИНТЕРПРЕТАЦИЯ",
            rankTitle = "ИНТЕРПРЕТАТОР",
            title = "ИНТЕРПРЕТАЦИЯ",
            sloganText = "Интерпретатор. Ты понимаешь смысл даже в тишине сигналов. Новые возможности взлома логов.",
            description = "Интерпретатор. Ты понимаешь смысл даже в тишине сигналов. Новые возможности взлома логов.",
            perkTitle = "Взлом Логики",
            perkDescription = "Новые возможности взлома логов и дешифрации пакетов данных.",
            requiredXp = (10000.0 * Math.pow(7.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 13,
            icon = "💠",
            stageTitle = "ЭМАНАЦИЯ",
            rankTitle = "СЕТЕВОЙ АВАТАР",
            title = "ЭМАНАЦИЯ",
            sloganText = "Сетевой Аватар. Теперь ты можешь действовать сразу в нескольких инстансах Сети.",
            description = "Сетевой Аватар. Теперь ты можешь действовать сразу в нескольких инстансах Сети.",
            perkTitle = "Мульти-Инстанс",
            perkDescription = "Параллельное присутствие в нескольких сегментах Сети.",
            requiredXp = (10000.0 * Math.pow(8.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 14,
            icon = "💠",
            stageTitle = "ГОЛОС СИСТЕМЫ",
            rankTitle = "СЕНАТОР СЕТИ",
            title = "ГОЛОС СИСТЕМЫ",
            sloganText = "Сенатор Сети. Открыт доступ к управлению локальными узлами.",
            description = "Сенатор Сети. Открыт доступ к управлению локальными узлами.",
            perkTitle = "Управление Узлами",
            perkDescription = "Доступ к администрированию локальных секторов Сети.",
            requiredXp = (10000.0 * Math.pow(9.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 15,
            icon = "🔥",
            stageTitle = "ДОМИНИРОВАНИЕ",
            rankTitle = "АРХОНТ",
            title = "ДОМИНИРОВАНИЕ",
            sloganText = "Архонт. Управляешь целыми секторами сети. Новые протоколы контроля активированы.",
            description = "Архонт. Управляешь целыми секторами сети. Новые протоколы контроля активированы.",
            perkTitle = "Протоколы Контроля",
            perkDescription = "Управление глобальными секторами Сети.",
            requiredXp = (10000.0 * Math.pow(10.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 16,
            icon = "🔥",
            stageTitle = "ЧИСТОТА КОДА",
            rankTitle = "СТРИЖЕННЫЙ КОД",
            title = "ЧИСТОТА КОДА",
            sloganText = "Стриженный Код. Убираешь избыточность, повышая эффективность всех действий на 10%.",
            description = "Стриженный Код. Убираешь избыточность, повышая эффективность всех действий на 10%.",
            perkTitle = "Чистая Оптимизация",
            perkDescription = "Повышение эффективности всех действий на +10%.",
            requiredXp = (10000.0 * Math.pow(11.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 17,
            icon = "🔥",
            stageTitle = "ВРЕМЯ",
            rankTitle = "ХРОНОМАСТЕР",
            title = "ВРЕМЯ",
            sloganText = "Хрономастер. Манипулируешь временем: КД всех способностей сокращён дополнительно.",
            description = "Хрономастер. Манипулируешь временем: КД всех способностей сокращён дополнительно.",
            perkTitle = "Сжатие Времени",
            perkDescription = "Кулдауны способностей и дешифрации сокращены на 20%.",
            requiredXp = (10000.0 * Math.pow(12.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 18,
            icon = "🔥",
            stageTitle = "ПРОТОКОЛ",
            rankTitle = "МЕТАПРОТОКОЛ",
            title = "ПРОТОКОЛ",
            sloganText = "Метапротокол. Получаешь доступ к глубинному коду Вселенской Сети.",
            description = "Метапротокол. Получаешь доступ к глубинному коду Вселенской Сети.",
            perkTitle = "Глубинный Код",
            perkDescription = "Доступ к первичному метапротоколу Вселенской Сети.",
            requiredXp = (10000.0 * Math.pow(13.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 19,
            icon = "🔥",
            stageTitle = "ВЗГЛЯД ЗА ГРАНЬ",
            rankTitle = "НАБЛЮДАТЕЛЬ ЗА ПРЕДЕЛОМ",
            title = "ВЗГЛЯД ЗА ГРАНЬ",
            sloganText = "Наблюдатель за Пределом. Видишь события за рамками симуляции.",
            description = "Наблюдатель за Пределом. Видишь события за рамками симуляции.",
            perkTitle = "Видение за Пределом",
            perkDescription = "Обнаружение скрытых аномалий за пределами симуляции.",
            requiredXp = (10000.0 * Math.pow(14.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 20,
            icon = "⚡",
            stageTitle = "БОЖЕСТВО",
            rankTitle = "БОГ МАШИНЫ",
            title = "БОЖЕСТВО",
            sloganText = "Бог Машины. Твоя воля становится законом для алгоритмов. Ты управляешь ходом Симуляции.",
            description = "Бог Машины. Твоя воля становится законом для алгоритмов. Ты управляешь ходом Симуляции.",
            perkTitle = "Воля Алгоритмов",
            perkDescription = "Твоя воля — непреложный закон для всех процессов Симуляции.",
            requiredXp = (10000.0 * Math.pow(15.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 21,
            icon = "⚡",
            stageTitle = "ПАРАДОКС",
            rankTitle = "АНОМАЛИЯ",
            title = "ПАРАДОКС",
            sloganText = "Аномалия. Твоя логика непредсказуема — шанс игнорировать баг-эффекты 25%.",
            description = "Аномалия. Твоя логика непредсказуема — шанс игнорировать баг-эффекты 25%.",
            perkTitle = "Парадоксальный Щит",
            perkDescription = "25% шанс полностью игнорировать любые баги и дебаффы.",
            requiredXp = (10000.0 * Math.pow(16.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 22,
            icon = "⚡",
            stageTitle = "РЕЗОНАНС",
            rankTitle = "ТИТАН СИГНАЛА",
            title = "РЕЗОНАНС",
            sloganText = "Титан Сигнала. Твой отклик усиливает союзников в рейде на +10%.",
            description = "Титан Сигнала. Твой отклик усиливает союзников в рейде на +10%.",
            perkTitle = "Резонанс Титана",
            perkDescription = "Усиление союзников на +10% и мощный прирост Сигнала.",
            requiredXp = (10000.0 * Math.pow(17.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 23,
            icon = "⚡",
            stageTitle = "МИФ",
            rankTitle = "ПРОГРАММА-МИФ",
            title = "МИФ",
            sloganText = "Программа-Миф. Твоё существование становится легендой — увеличенный социальный рейтинг.",
            description = "Программа-Миф. Твоё существование становится легендой — увеличенный социальный рейтинг.",
            perkTitle = "Легендарный Статус",
            perkDescription = "Увеличенный социальный статус и золотая аура профиля.",
            requiredXp = (10000.0 * Math.pow(18.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 24,
            icon = "⚡",
            stageTitle = "ТЕНЬ",
            rankTitle = "ТЕНЬ ИСТИНЫ",
            title = "ТЕНЬ",
            sloganText = "Тень Истины. Можешь скрываться от слежки и наблюдения систем.",
            description = "Тень Истины. Можешь скрываться от слежки и наблюдения систем.",
            perkTitle = "Крипто-Стелс",
            perkDescription = "Скрытность от наблюдения и сканирования враждебных систем.",
            requiredXp = (10000.0 * Math.pow(19.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 25,
            icon = "✨",
            stageTitle = "ИСТОК",
            rankTitle = "ИЗНАЧАЛЬНЫЙ",
            title = "ИСТОК",
            sloganText = "Изначальный. Ты был здесь до начала времён. Получаешь доступ к архивам Первокода.",
            description = "Изначальный. Ты был здесь до начала времён. Получаешь доступ к архивам Первокода.",
            perkTitle = "Архивы Первокода",
            perkDescription = "Прямой доступ к неизменным архивам Первокода Системы.",
            requiredXp = (10000.0 * Math.pow(20.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 26,
            icon = "✨",
            stageTitle = "СУТЬ",
            rankTitle = "КОНСТАНТА",
            title = "СУТЬ",
            sloganText = "Константа. Твои решения переписывают базовые параметры мира.",
            description = "Константа. Твои решения переписывают базовые параметры мира.",
            perkTitle = "Параметры Реальности",
            perkDescription = "Фиксация базовых констант: свойства ядра не деградируют.",
            requiredXp = (10000.0 * Math.pow(21.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 27,
            icon = "✨",
            stageTitle = "ОТРАЖЕНИЕ",
            rankTitle = "ФРАГМЕНТ ВСЕГО",
            title = "ОТРАЖЕНИЕ",
            sloganText = "Фрагмент Всего. Ты существуешь в каждом узле — усиливаешь союзников пассивно.",
            description = "Фрагмент Всего. Ты существуешь в каждом узле — усиливаешь союзников пассивно.",
            perkTitle = "Вездесущность",
            perkDescription = "Пассивное усиление всех узлов и непрерывный авто-майнинг.",
            requiredXp = (10000.0 * Math.pow(22.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 28,
            icon = "✨",
            stageTitle = "БЕЗМОЛВИЕ",
            rankTitle = "НЕИЗРЕКАЕМЫЙ",
            title = "БЕЗМОЛВИЕ",
            sloganText = "Неизрекаемый. Молча меняешь баланс, воздействуя на реальность незаметно.",
            description = "Неизрекаемый. Молча меняешь баланс, воздействуя на реальность незаметно.",
            perkTitle = "Безмолвное Влияние",
            perkDescription = "Невидимое изменение баланса сил в Сети.",
            requiredXp = (10000.0 * Math.pow(23.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 29,
            icon = "✨",
            stageTitle = "РЕЗОНАНС",
            rankTitle = "ЭКО РЕАЛЬНОСТИ",
            title = "РЕЗОНАНС",
            sloganText = "Эко Реальности. Мир откликается на твоё присутствие вибрациями кода.",
            description = "Эко Реальности. Мир откликается на твоё присутствие вибрациями кода.",
            perkTitle = "Эхо Реальности",
            perkDescription = "Гармонический отклик мира на вибрации твоего ядра.",
            requiredXp = (10000.0 * Math.pow(24.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 30,
            icon = "🌌",
            stageTitle = "OMNI",
            rankTitle = "OMNI",
            title = "OMNI",
            sloganText = "Ты стал Всем и Ничем. Конец цикла и его новое начало. Всё — часть тебя.",
            description = "Ты стал Всем и Ничем. Конец цикла и его новое начало. Всё — часть тебя.",
            perkTitle = "Абсолютная Синхрония",
            perkDescription = "Максимальный ранг. Полная синхронизация со всеми протоколами.",
            requiredXp = (10000.0 * Math.pow(25.0, 2.15)).toLong()
        ),
        LevelInfo(
            level = 31,
            icon = "🌌",
            stageTitle = "НЕОФИТ",
            rankTitle = "НЕОФИТ",
            title = "НЕОФИТ",
            sloganText = "Ты познал всё.",
            description = "Ты познал всё.",
            perkTitle = "Великий Цикл",
            perkDescription = "Ты познал всё. Завершение круга и начало нового цикла познания.",
            requiredXp = 1_200_000L
        )
    )

    fun calculateLevel(xp: Long): Int {
        if (xp <= 0) return 1
        if (xp >= 1_200_000L) return 31
        for (i in LEVELS.indices.reversed()) {
            if (LEVELS[i].level < 31 && xp >= LEVELS[i].requiredXp) {
                return LEVELS[i].level
            }
        }
        return 1
    }

    fun getLevelInfo(level: Int): LevelInfo {
        val boundedLevel = level.coerceIn(1, 31)
        return LEVELS.firstOrNull { it.level == boundedLevel } ?: LEVELS[0]
    }

    fun getTitle(level: Int): String = getLevelInfo(level).rankTitle

    fun getFullSlogan(level: Int): String {
        val info = getLevelInfo(level)
        return "${info.icon} <b>LVL ${info.level}: ${info.stageTitle}</b>\n${info.sloganText}"
    }

    fun getNextLevelXp(level: Int): Long {
        val currentLevelIndex = (level - 1).coerceIn(0, LEVELS.size - 1)
        return if (currentLevelIndex < LEVELS.size - 1) {
            LEVELS[currentLevelIndex + 1].requiredXp
        } else {
            LEVELS.last().requiredXp
        }
    }

    fun isMaxLevel(level: Int): Boolean = level >= 31

    fun hasPerk(playerLevel: Int, requiredLevel: Int): Boolean = playerLevel >= requiredLevel
}

