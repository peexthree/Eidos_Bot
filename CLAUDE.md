# Eidos: Zero Layer - проект

## Стек
Kotlin 2.3.21, Jetpack Compose (BOM 2026.09), AGP 9.2.1, Gradle 9.8.2, Room 2.8.5, built-in Kotlin (без kotlin-android плагина), KSP 2.3.13, compileSdk 37, targetSdk 35, minSdk 26, JDK 17.

## Запуск
- `./gradlew assembleDebug` - сборка, `./gradlew testDebugUnitTest` - 46 тестов
- Секреты в `local.properties` (gitignored): SUPABASE_URL, SUPABASE_ANON_KEY
- Release: keystore.properties (gitignored), fallback на debug-ключ

## Структура
- `app/src/main/java/io/eidos/zerolayer/data/` - GameRepository (главный God-object ~5.3k строк), AuthRepository, Database.kt (Room v14), DailyQuestData, AchievementData
- `app/src/main/java/io/eidos/zerolayer/domain/` - CombatEngine, QuantumSectorEngine, RaidEventDispatcher, PoECraftModels, AnomalyEngine
- `app/src/main/java/io/eidos/zerolayer/ui/screens/` - все экраны; raid/ - подкомпозаблы
- `app/src/main/java/io/eidos/zerolayer/ui/theme/ZzzDesignSystem.kt` - каноническая палитра (ZzzGold, ZzzDangerRed, ZzzCyanBright, ZzzNeonGreen, ZzzWarningOrange, ZzzPurple, ZzzGlassBase)
- `app/src/main/assets/` - items.json (98 предметов), villains.json (25 врагов), content.json (протоколы/события)
- `data/supabase_hardening_v2.sql` - единственный актуальный SQL для БД
- `supabase/functions/` - verify-purchase, gemini-proxy (Edge Functions)
- `docs/` - AUDIT, PRODUCT_PLAN, UX_PLAN, asset_inventory.csv

## Механики
- Смерть: сброс max_depth=0 (старт с поверхности), hp=1 БЕЗ халявы. Лечение: мед-модули или МЕД-КАПСУЛА на шлюзе (2 BC/HP, мин 50)
- Шлем Скорости (relic_speed): шаг = рывок x3/x5/x10 (50/35/15%)
- Гейткиперы каждые 1000м (RaidEventDispatcher), Ключ Биомы в трофей
- World Boss: таблица world_boss_state, месячный цикл, топ-вклад
- Терминал Сингулярности: 3 финала (престиж NG+ +10%/цикл, Вознесение, Бездна)
- Дейлики: DailyQuestData.kt (SharedPreferences), 5 типов, клейм наград
- Мутаторы: все 9 реализованы (GOLD_RUSH шаблон, ANTIGRAVITY=0EP+блок аптечек, GLITCH_STORM=+40% легендарок, ECHOES_PAST=x2 могилы)
- Паттерн репозитория: `dbMutex.withLock { internalUnsafeXxx() }` - НЕ вызывать публичные обёртки из-под мьютекса (Kotlin Mutex нереентерабельный)
- Ежедневные директивы: SPEND wired на buyItem, repairItemBC, buyGachaRoll, buyPvpHardware

## UX
- Инвентарь → ВЕРСТАК: sendToForge → ForgeScreen preselectedItem
- Магазин → НАДЕТЬ СРАЗУ: equipLatestItemById
- Радио-бейдж на аватаре Хаба (unclaimed count)
- Атомарный артовый свап: читать всё в память, потом писать (НЕ последовательные свопы!)

## Остатки
- B3: единый хедер на Inventory/Shop/Forge/Codex/Pvp (паттерн Settings)
- Живые SFX: пользователь зальёт в canva_raw/sfx/
- Retrofit 3.x / OkHttp 5 / Coil 3 миграции (сознательно отложены)
- targetSdk 36 (когда Play потребует)
