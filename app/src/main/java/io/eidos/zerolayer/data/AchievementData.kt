package io.eidos.zerolayer.data

import android.content.Context
import android.content.SharedPreferences
import java.util.Calendar

data class AchievementItem(
    val id: String,
    val category: String,
    val icon: String,
    val title: String,
    val description: String,
    val xpReward: Long,
    val coinReward: Long = 0,
    val target: Long = 1,
    val current: Long = 0,
    val isUnlocked: Boolean = false,
    val isClaimed: Boolean = false
)

data class AchievementStats(
    val totalClicks: Long = 0L,
    val syncrons: Int = 0,
    val quizzesWon: Int = 0,
    val purchases: Int = 0,
    val messagesSent: Int = 0,
    val likesReceived: Int = 0,
    val referrals: Int = 0,
    val zeroLayerEntered: Boolean = false,
    val glitchTriggered: Boolean = false,
    val creatorGazeFound: Boolean = false,
    val nightOperatorUnlocked: Boolean = false
)

object AchievementRegistry {

    data class Def(
        val id: String,
        val category: String,
        val icon: String,
        val title: String,
        val description: String,
        val xpReward: Long,
        val target: Long,
        val getProgress: (Player, AchievementStats) -> Long,
        val isMet: (Player, AchievementStats) -> Boolean
    )

    val ALL_DEFINITIONS: List<Def> = listOf(
        // === 1. Прогресс (уровни) ===
        Def(
            id = "ach_lvl_2",
            category = "Прогресс (уровни)",
            icon = "🐣",
            title = "ВЫХОД ИЗ КОКОНА",
            description = "Достиг 2-го уровня",
            xpReward = 100L,
            target = 2L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 2 }
        ),
        Def(
            id = "ach_lvl_3",
            category = "Прогресс (уровни)",
            icon = "🥚",
            title = "ОПЕРАТОР",
            description = "Достиг 3-го уровня",
            xpReward = 200L,
            target = 3L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 3 }
        ),
        Def(
            id = "ach_lvl_5",
            category = "Прогресс (уровни)",
            icon = "⚡️",
            title = "ЭКВАТОР",
            description = "Достиг 5-го уровня",
            xpReward = 500L,
            target = 5L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 5 }
        ),
        Def(
            id = "ach_lvl_10",
            category = "Прогресс (уровни)",
            icon = "👑",
            title = "АБСОЛЮТ",
            description = "Финал первой фазы (10 lvl)",
            xpReward = 2000L,
            target = 10L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 10 }
        ),
        Def(
            id = "ach_lvl_15",
            category = "Прогресс (уровни)",
            icon = "🔥",
            title = "АРХОНТ",
            description = "Достиг 15-го уровня",
            xpReward = 5000L,
            target = 15L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 15 }
        ),
        Def(
            id = "ach_lvl_20",
            category = "Прогресс (уровни)",
            icon = "⚙️",
            title = "БОГ МАШИНЫ",
            description = "Подчинил алгоритм (20 lvl)",
            xpReward = 10000L,
            target = 20L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 20 }
        ),
        Def(
            id = "ach_lvl_30",
            category = "Прогресс (уровни)",
            icon = "🌌",
            title = "OMNI",
            description = "Стал Всем и Ничем (30 lvl)",
            xpReward = 30000L,
            target = 30L,
            getProgress = { p, _ -> p.level.toLong() },
            isMet = { p, _ -> p.level >= 30 }
        ),

        // === 2. Дисциплина (стрики) ===
        Def(
            id = "ach_streak_3",
            category = "Дисциплина (стрики)",
            icon = "☘️",
            title = "ПРИВЫЧКА",
            description = "3 дня подряд",
            xpReward = 50L,
            target = 3L,
            getProgress = { p, _ -> p.streak.toLong() },
            isMet = { p, _ -> p.streak >= 3 }
        ),
        Def(
            id = "ach_streak_7",
            category = "Дисциплина (стрики)",
            icon = "🔥",
            title = "НЕДЕЛЯ В АДУ",
            description = "7 дней подряд",
            xpReward = 200L,
            target = 7L,
            getProgress = { p, _ -> p.streak.toLong() },
            isMet = { p, _ -> p.streak >= 7 }
        ),
        Def(
            id = "ach_streak_14",
            category = "Дисциплина (стрики)",
            icon = "🌙",
            title = "ПОЛНЫЙ ЦИКЛ",
            description = "14 дней",
            xpReward = 400L,
            target = 14L,
            getProgress = { p, _ -> p.streak.toLong() },
            isMet = { p, _ -> p.streak >= 14 }
        ),
        Def(
            id = "ach_streak_30",
            category = "Дисциплина (стрики)",
            icon = "🧘",
            title = "ВНЕ ВРЕМЕНИ",
            description = "30 дней",
            xpReward = 1000L,
            target = 30L,
            getProgress = { p, _ -> p.streak.toLong() },
            isMet = { p, _ -> p.streak >= 30 }
        ),
        Def(
            id = "ach_streak_100",
            category = "Дисциплина (стрики)",
            icon = "♾️",
            title = "СИСТЕМНЫЙ МОНАХ",
            description = "100 дней",
            xpReward = 3000L,
            target = 100L,
            getProgress = { p, _ -> p.streak.toLong() },
            isMet = { p, _ -> p.streak >= 100 }
        ),

        // === 3. Финансы (XP/биокоины) ===
        Def(
            id = "ach_coins_1000",
            category = "Финансы (XP/биокоины)",
            icon = "🤑",
            title = "БОГАЧ 1000",
            description = "1000 биокоинов",
            xpReward = 200L,
            target = 1000L,
            getProgress = { p, _ -> p.biocoin },
            isMet = { p, _ -> p.biocoin >= 1000L }
        ),
        Def(
            id = "ach_xp_1000",
            category = "Финансы (XP/биокоины)",
            icon = "💸",
            title = "ПЕРВЫЙ КУШ",
            description = "1000 XP",
            xpReward = 100L,
            target = 1000L,
            getProgress = { p, _ -> p.xp },
            isMet = { p, _ -> p.xp >= 1000L }
        ),
        Def(
            id = "ach_xp_10k",
            category = "Финансы (XP/биокоины)",
            icon = "💰",
            title = "БОГАЧ",
            description = "10k XP",
            xpReward = 1000L,
            target = 10000L,
            getProgress = { p, _ -> p.xp },
            isMet = { p, _ -> p.xp >= 10000L }
        ),
        Def(
            id = "ach_xp_50k",
            category = "Финансы (XP/биокоины)",
            icon = "🏦",
            title = "КОРПОРАЦИЯ Я",
            description = "50k XP",
            xpReward = 5000L,
            target = 50000L,
            getProgress = { p, _ -> p.xp },
            isMet = { p, _ -> p.xp >= 50000L }
        ),
        Def(
            id = "ach_xp_100k",
            category = "Финансы (XP/биокоины)",
            icon = "👾",
            title = "ТОП-1 СЕТИ",
            description = "100k XP",
            xpReward = 10000L,
            target = 100000L,
            getProgress = { p, _ -> p.xp },
            isMet = { p, _ -> p.xp >= 100000L }
        ),

        // === 4. Рейды/исследования ===
        Def(
            id = "ach_kills_1",
            category = "Рейды/исследования",
            icon = "🩸",
            title = "ПЕРВАЯ КРОВЬ",
            description = "Первое убийство",
            xpReward = 100L,
            target = 1L,
            getProgress = { p, _ -> p.kills.toLong() },
            isMet = { p, _ -> p.kills >= 1 }
        ),
        Def(
            id = "ach_depth_10",
            category = "Рейды/исследования",
            icon = "👣",
            title = "ПЕРВЫЕ ШАГИ",
            description = "10 глубины",
            xpReward = 100L,
            target = 10L,
            getProgress = { p, _ -> p.max_depth.toLong() },
            isMet = { p, _ -> p.max_depth >= 10 }
        ),
        Def(
            id = "ach_depth_50",
            category = "Рейды/исследования",
            icon = "⚓️",
            title = "СТАЛКЕР",
            description = "50 глубины",
            xpReward = 500L,
            target = 50L,
            getProgress = { p, _ -> p.max_depth.toLong() },
            isMet = { p, _ -> p.max_depth >= 50 }
        ),
        Def(
            id = "ach_depth_100",
            category = "Рейды/исследования",
            icon = "🕳",
            title = "ТЬМА",
            description = "100 глубины",
            xpReward = 2000L,
            target = 100L,
            getProgress = { p, _ -> p.max_depth.toLong() },
            isMet = { p, _ -> p.max_depth >= 100 }
        ),
        Def(
            id = "ach_depth_200",
            category = "Рейды/исследования",
            icon = "🐉",
            title = "ПРОБУЖДЕННЫЙ",
            description = "200+ глубины",
            xpReward = 5000L,
            target = 200L,
            getProgress = { p, _ -> p.max_depth.toLong() },
            isMet = { p, _ -> p.max_depth >= 200 }
        ),
        Def(
            id = "ach_raids_10",
            category = "Рейды/исследования",
            icon = "🔫",
            title = "ВЕТЕРАН",
            description = "10 рейдов",
            xpReward = 400L,
            target = 10L,
            getProgress = { p, _ -> p.raids_done.toLong() },
            isMet = { p, _ -> p.raids_done >= 10 }
        ),
        Def(
            id = "ach_perfect_1",
            category = "Рейды/исследования",
            icon = "⚔️",
            title = "БЕЗУПРЕЧНЫЙ",
            description = "Рейд без потерь",
            xpReward = 1500L,
            target = 1L,
            getProgress = { p, _ -> p.perfect_raids.toLong() },
            isMet = { p, _ -> p.perfect_raids >= 1 }
        ),

        // === 5. Сеть/социальность ===
        Def(
            id = "ach_ref_1",
            category = "Сеть/социальность",
            icon = "🤝",
            title = "ВЕРБОВЩИК",
            description = "1 реферал",
            xpReward = 150L,
            target = 1L,
            getProgress = { _, s -> s.referrals.toLong() },
            isMet = { _, s -> s.referrals >= 1 }
        ),
        Def(
            id = "ach_ref_10",
            category = "Сеть/социальность",
            icon = "📢",
            title = "ПРОПОВЕДНИК",
            description = "10 рефералов",
            xpReward = 2000L,
            target = 10L,
            getProgress = { _, s -> s.referrals.toLong() },
            isMet = { _, s -> s.referrals >= 10 }
        ),
        Def(
            id = "ach_ref_50",
            category = "Сеть/социальность",
            icon = "🕸",
            title = "УЗЕЛ",
            description = "50 рефералов",
            xpReward = 8000L,
            target = 50L,
            getProgress = { _, s -> s.referrals.toLong() },
            isMet = { _, s -> s.referrals >= 50 }
        ),
        Def(
            id = "ach_ref_100",
            category = "Сеть/социальность",
            icon = "🌐",
            title = "НЕЙРОСЕТЬ",
            description = "100 рефералов",
            xpReward = 15000L,
            target = 100L,
            getProgress = { _, s -> s.referrals.toLong() },
            isMet = { _, s -> s.referrals >= 100 }
        ),

        // === 6. Знания/обучение ===
        Def(
            id = "ach_sync_10",
            category = "Знания/обучение",
            icon = "📖",
            title = "УЧЕНИК",
            description = "10 синхронов",
            xpReward = 200L,
            target = 10L,
            getProgress = { _, s -> s.syncrons.toLong() },
            isMet = { _, s -> s.syncrons >= 10 }
        ),
        Def(
            id = "ach_sync_25",
            category = "Знания/обучение",
            icon = "🧩",
            title = "АНАЛИТИК",
            description = "25 синхронов",
            xpReward = 700L,
            target = 25L,
            getProgress = { _, s -> s.syncrons.toLong() },
            isMet = { _, s -> s.syncrons >= 25 }
        ),
        Def(
            id = "ach_sync_50",
            category = "Знания/обучение",
            icon = "🧠",
            title = "ПРОРОК КОДА",
            description = "50+ синхронов",
            xpReward = 2500L,
            target = 50L,
            getProgress = { _, s -> s.syncrons.toLong() },
            isMet = { _, s -> s.syncrons >= 50 }
        ),
        Def(
            id = "ach_quiz_1",
            category = "Знания/обучение",
            icon = "🎯",
            title = "ТОЧНО В ЦЕЛЬ",
            description = "Викторина выиграна",
            xpReward = 500L,
            target = 1L,
            getProgress = { _, s -> s.quizzesWon.toLong() },
            isMet = { _, s -> s.quizzesWon >= 1 }
        ),

        // === 7. Шопинг ===
        Def(
            id = "ach_shop_1",
            category = "Шопинг",
            icon = "🛒",
            title = "ПОТРЕБИТЕЛЬ",
            description = "Первая покупка",
            xpReward = 50L,
            target = 1L,
            getProgress = { _, s -> s.purchases.toLong() },
            isMet = { _, s -> s.purchases >= 1 }
        ),
        Def(
            id = "ach_shop_10",
            category = "Шопинг",
            icon = "💼",
            title = "АКТИВНЫЙ КЛИЕНТ",
            description = "10 покупок",
            xpReward = 300L,
            target = 10L,
            getProgress = { _, s -> s.purchases.toLong() },
            isMet = { _, s -> s.purchases >= 10 }
        ),
        Def(
            id = "ach_shop_100",
            category = "Шопинг",
            icon = "🏗",
            title = "ИНВЕСТОР",
            description = "100 покупок",
            xpReward = 3000L,
            target = 100L,
            getProgress = { _, s -> s.purchases.toLong() },
            isMet = { _, s -> s.purchases >= 100 }
        ),

        // === 8. Социальные ===
        Def(
            id = "ach_msg_1",
            category = "Социальные",
            icon = "💬",
            title = "ПЕРВЫЙ СИГНАЛ",
            description = "Первое сообщение",
            xpReward = 100L,
            target = 1L,
            getProgress = { _, s -> s.messagesSent.toLong() },
            isMet = { _, s -> s.messagesSent >= 1 }
        ),
        Def(
            id = "ach_msg_100",
            category = "Социальные",
            icon = "📡",
            title = "РЕЗОНАТОР",
            description = "100 сообщений",
            xpReward = 600L,
            target = 100L,
            getProgress = { _, s -> s.messagesSent.toLong() },
            isMet = { _, s -> s.messagesSent >= 100 }
        ),
        Def(
            id = "ach_likes_100",
            category = "Социальные",
            icon = "❤️",
            title = "ЛЮБИМЧИК СЕТИ",
            description = "100 лайков",
            xpReward = 700L,
            target = 100L,
            getProgress = { _, s -> s.likesReceived.toLong() },
            isMet = { _, s -> s.likesReceived >= 100 }
        ),

        // === 9. Секретные/пасхалки ===
        Def(
            id = "ach_secret_zero",
            category = "Секретные/пасхалки",
            icon = "🌀",
            title = "НУЛЕВОЙ",
            description = "Скрытый вход в Нулевой Слой",
            xpReward = 2000L,
            target = 1L,
            getProgress = { _, s -> if (s.zeroLayerEntered) 1L else 0L },
            isMet = { _, s -> s.zeroLayerEntered }
        ),
        Def(
            id = "ach_secret_glitch",
            category = "Секретные/пасхалки",
            icon = "⚠️",
            title = "ГЛИТЧ",
            description = "Баг стал фичей",
            xpReward = 1000L,
            target = 1L,
            getProgress = { _, s -> if (s.glitchTriggered) 1L else 0L },
            isMet = { _, s -> s.glitchTriggered }
        ),
        Def(
            id = "ach_secret_creator",
            category = "Секретные/пасхалки",
            icon = "👁",
            title = "ВЗГЛЯД ТВОРЦА",
            description = "След dev в коде",
            xpReward = 5000L,
            target = 1L,
            getProgress = { _, s -> if (s.creatorGazeFound) 1L else 0L },
            isMet = { _, s -> s.creatorGazeFound }
        ),
        Def(
            id = "ach_secret_night",
            category = "Секретные/пасхалки",
            icon = "🌒",
            title = "НОЧНОЙ ОПЕРАТОР",
            description = "Вход после 3:00",
            xpReward = 300L,
            target = 1L,
            getProgress = { _, s -> if (s.nightOperatorUnlocked) 1L else 0L },
            isMet = { _, s -> s.nightOperatorUnlocked }
        ),
        Def(
            id = "ach_secret_clicks",
            category = "Секретные/пасхалки",
            icon = "🔮",
            title = "ПРИЗВАННЫЙ ХАОСОМ",
            description = "1000 кликов",
            xpReward = 700L,
            target = 1000L,
            getProgress = { _, s -> s.totalClicks },
            isMet = { _, s -> s.totalClicks >= 1000L }
        )
    )
}

class AchievementStorage(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("eidos_achievements_prefs", Context.MODE_PRIVATE)

    fun getUnlockedSet(): Set<String> {
        return prefs.getStringSet("unlocked_achievements_v2", emptySet()) ?: emptySet()
    }

    fun isUnlocked(id: String): Boolean {
        return getUnlockedSet().contains(id)
    }

    fun markUnlocked(id: String) {
        val current = getUnlockedSet().toMutableSet()
        current.add(id)
        prefs.edit().putStringSet("unlocked_achievements_v2", current).apply()
    }

    fun getClaimedSet(): Set<String> {
        return prefs.getStringSet("claimed_achievements_v2", emptySet()) ?: emptySet()
    }

    fun isClaimed(id: String): Boolean {
        return getClaimedSet().contains(id)
    }

    fun markClaimed(id: String) {
        val current = getClaimedSet().toMutableSet()
        current.add(id)
        prefs.edit().putStringSet("claimed_achievements_v2", current).apply()
    }

    fun getStats(): AchievementStats {
        return AchievementStats(
            totalClicks = prefs.getLong("stats_clicks", 0L),
            syncrons = prefs.getInt("stats_syncrons", 0),
            quizzesWon = prefs.getInt("stats_quizzes_won", 0),
            purchases = prefs.getInt("stats_purchases", 0),
            messagesSent = prefs.getInt("stats_messages_sent", 0),
            likesReceived = prefs.getInt("stats_likes_received", 0),
            referrals = prefs.getInt("stats_referrals", 0),
            zeroLayerEntered = prefs.getBoolean("stats_zero_layer", false),
            glitchTriggered = prefs.getBoolean("stats_glitch", false),
            creatorGazeFound = prefs.getBoolean("stats_creator_gaze", false),
            nightOperatorUnlocked = prefs.getBoolean("stats_night_op", false)
        )
    }

    fun incrementClicks(): Long {
        val newVal = prefs.getLong("stats_clicks", 0L) + 1L
        prefs.edit().putLong("stats_clicks", newVal).apply()
        return newVal
    }

    fun incrementSyncrons(): Int {
        val newVal = prefs.getInt("stats_syncrons", 0) + 1
        prefs.edit().putInt("stats_syncrons", newVal).apply()
        return newVal
    }

    fun incrementQuizzesWon(): Int {
        val newVal = prefs.getInt("stats_quizzes_won", 0) + 1
        prefs.edit().putInt("stats_quizzes_won", newVal).apply()
        return newVal
    }

    fun incrementPurchases(): Int {
        val newVal = prefs.getInt("stats_purchases", 0) + 1
        prefs.edit().putInt("stats_purchases", newVal).apply()
        return newVal
    }

    fun incrementMessages(): Int {
        val newVal = prefs.getInt("stats_messages_sent", 0) + 1
        prefs.edit().putInt("stats_messages_sent", newVal).apply()
        return newVal
    }

    fun incrementLikes(amount: Int = 1): Int {
        val newVal = prefs.getInt("stats_likes_received", 0) + amount
        prefs.edit().putInt("stats_likes_received", newVal).apply()
        return newVal
    }

    fun setReferrals(count: Int) {
        prefs.edit().putInt("stats_referrals", count).apply()
    }

    fun setZeroLayerEntered() {
        prefs.edit().putBoolean("stats_zero_layer", true).apply()
    }

    fun setGlitchTriggered() {
        prefs.edit().putBoolean("stats_glitch", true).apply()
    }

    fun setCreatorGazeFound() {
        prefs.edit().putBoolean("stats_creator_gaze", true).apply()
    }

    fun checkNightLogin(): Boolean {
        val hour = Calendar.getInstance().get(Calendar.HOUR_OF_DAY)
        if (hour in 3..5) {
            prefs.edit().putBoolean("stats_night_op", true).apply()
            return true
        }
        return prefs.getBoolean("stats_night_op", false)
    }
}
