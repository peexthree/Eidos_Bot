package io.eidos.zerolayer.data

enum class ConsumableScope {
    PEACE_AND_COMBAT,
    COMBAT_ONLY,
    RAID_ONLY,
    INVENTORY_ONLY,
    PASSIVE_TRIGGER
}

enum class ConsumableType(
    val itemId: String,
    val displayName: String,
    val icon: String,
    val description: String,
    val priceBc: Int = 0,
    val priceXp: Int = 0,
    val maxStack: Int = 99,
    val maxDurability: Int = 1,
    val scope: ConsumableScope = ConsumableScope.INVENTORY_ONLY
) {
    BATTERY(
        itemId = "battery",
        displayName = "Энерго-ячейка",
        icon = "🔋",
        description = "Восстанавливает +30% Сигнала (HP). Доступно в покое и во время боя.",
        priceBc = 250,
        scope = ConsumableScope.PEACE_AND_COMBAT
    ),
    NEURAL_STIMULATOR(
        itemId = "neural_stimulator",
        displayName = "Нейро-стимулятор",
        icon = "💉",
        description = "Восстанавливает +60% Сигнала (HP). Мгновенно стабилизирует нейросеть.",
        priceBc = 300,
        scope = ConsumableScope.PEACE_AND_COMBAT
    ),
    MASTER_KEY(
        itemId = "master_key",
        displayName = "Магнитная отмычка",
        icon = "🗝",
        description = "Открывает Запертые Сундуки (locked_chest) со 100% шансом.",
        priceBc = 75,
        maxStack = 5,
        scope = ConsumableScope.RAID_ONLY
    ),
    ABYSSAL_KEY(
        itemId = "abyssal_key",
        displayName = "Ключ от Бездны",
        icon = "🗝",
        description = "100% открывает Запертый Сундук (с гарантией экипировки) и Проклятый Сундук (cursed_chest).",
        priceBc = 500,
        maxStack = 3,
        scope = ConsumableScope.RAID_ONLY
    ),
    DATA_SPIKE(
        itemId = "data_spike",
        displayName = "Дата-шип",
        icon = "📌",
        description = "Расходник взлома. 80% шанс вскрыть locked_chest, 50% - cursed_chest. При неудаче сгорает.",
        priceBc = 120,
        scope = ConsumableScope.RAID_ONLY
    ),
    COMPASS(
        itemId = "compass",
        displayName = "Компас Пустоши",
        icon = "🧭",
        description = "Прочность 10 зарядов. Открывает превью следующего события в рейде (сканирование комнаты).",
        priceBc = 150,
        maxDurability = 10,
        scope = ConsumableScope.RAID_ONLY
    ),
    TACTICAL_SCANNER(
        itemId = "tactical_scanner",
        displayName = "Тактический сканер",
        icon = "📡",
        description = "Прочность 20 зарядов. Рассчитывает и отображает Winrate % в текущем бою. 10% шанс траты 1 заряда за раунд.",
        priceBc = 300,
        maxDurability = 20,
        scope = ConsumableScope.COMBAT_ONLY
    ),
    AEGIS(
        itemId = "aegis",
        displayName = "Эгида Бессмертия",
        icon = "🛡",
        description = "Пассивный триггер в инвентаре. При падении HP до 0 в рейде блокирует смерть, восстанавливает 1 HP и сгорает.",
        priceBc = 400,
        scope = ConsumableScope.PASSIVE_TRIGGER
    ),
    EMP_GRENADE(
        itemId = "emp_grenade",
        displayName = "ЭМИ-граната",
        icon = "💣",
        description = "Боевой предмет. Наносит 150 единиц чистого неблокируемого урона врагу.",
        priceBc = 200,
        scope = ConsumableScope.COMBAT_ONLY
    ),
    STEALTH_SPRAY(
        itemId = "stealth_spray",
        displayName = "Крипто-туман",
        icon = "🌫",
        description = "100% успешный побег из любого боя (включая боссов) без потери буфера.",
        priceBc = 350,
        scope = ConsumableScope.COMBAT_ONLY
    ),
    MEMORY_WIPER(
        itemId = "memory_wiper",
        displayName = "Стиратель памяти",
        icon = "💽",
        description = "Сбрасывает накопленный модификатор агрессии врагов (Агро) в текущем рейде.",
        priceBc = 400,
        scope = ConsumableScope.RAID_ONLY
    ),
    CRYO(
        itemId = "cryo",
        displayName = "Крио-капсула",
        icon = "❄️",
        description = "Замораживает стрик ежедневной активности при пропуске дня.",
        priceXp = 200,
        scope = ConsumableScope.INVENTORY_ONLY
    ),
    ACCEL(
        itemId = "accel",
        displayName = "Ускоритель синхронизации",
        icon = "⚡️",
        description = "Снижает кулдаун синхронизации до 15 мин на 24 часа.",
        priceXp = 600,
        scope = ConsumableScope.INVENTORY_ONLY
    ),
    DECODER(
        itemId = "decoder",
        displayName = "Дешифратор",
        icon = "🔓",
        description = "Ускоряет таймер расшифровки кэшей в 2 раза (с 4 часов до 2 часов).",
        priceBc = 1000,
        scope = ConsumableScope.INVENTORY_ONLY
    ),
    ENCRYPTED_CACHE(
        itemId = "encrypted_cache",
        displayName = "Зашифрованный кэш",
        icon = "📦",
        description = "Падает в рейдах. Ставится на таймер расшифровки (4ч базово). Дает крупный объем BC и шанс на Legendary/Relic.",
        priceBc = 0,
        scope = ConsumableScope.INVENTORY_ONLY
    ),
    PURIFICATION_SYNC(
        itemId = "purification_sync",
        displayName = "Синхрон Очищения",
        icon = "🌀",
        description = "Hard Reset (сброс уровня до 1, XP до 0, очистка инвентаря, запись рекорда в архив).",
        priceBc = 50000,
        scope = ConsumableScope.INVENTORY_ONLY
    );

    companion object {
        fun fromId(itemId: String): ConsumableType? {
            return entries.firstOrNull { it.itemId.equals(itemId, ignoreCase = true) }
        }
    }
}
