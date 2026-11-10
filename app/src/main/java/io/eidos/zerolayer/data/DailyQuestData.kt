package io.eidos.zerolayer.data

import android.content.Context
import android.content.SharedPreferences
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.random.Random

/**
 * Ежедневные Директивы: 3 квеста в сутки, детерминированно генерируемые из даты.
 * Классический retention-контур: короткие цели с наградой за claim.
 * Хранение в SharedPreferences (как AchievementStorage) - без миграции Room.
 */
data class DailyQuest(
    val id: String,
    val type: String, // KILLS / DEPTH / SYNC / SPEND / CHEST
    val title: String,
    val target: Int,
    val progress: Int = 0,
    val rewardCoins: Long,
    val rewardXp: Long,
    val isClaimed: Boolean = false
)

class DailyQuestStorage private constructor(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("eidos_daily_quests_prefs", Context.MODE_PRIVATE)

    private fun todayKey(): String =
        SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())

    private fun yesterdayKey(): String {
        val cal = java.util.Calendar.getInstance()
        cal.add(java.util.Calendar.DAY_OF_YEAR, -1)
        return SimpleDateFormat("yyyy-MM-dd", Locale.US).format(cal.time)
    }

    private fun daySeed(uid: Long): Int = (todayKey() + "_$uid").hashCode()

    fun isStale(uid: Long): Boolean = prefs.getString(key(uid, "date"), null) != todayKey()

    /** Типы квестов; для одного дня типы не повторяются. */
    fun ensureGenerated(uid: Long, playerLevel: Int) {
        val date = todayKey()
        if (prefs.getString(key(uid, "date"), null) == date) return

        val editor = prefs.edit().putString(key(uid, "date"), date)
        val rng = Random(daySeed(uid))
        val types = QUEST_TYPES.shuffled(rng).take(3)

        types.forEachIndexed { slot, type ->
            val target = targetFor(type, playerLevel, rng)
            editor.putInt(key(uid, "slot_${slot}_target"), target)
            editor.putInt(key(uid, "slot_${slot}_progress"), 0)
            editor.putBoolean(key(uid, "slot_${slot}_claimed"), false)
            editor.putString(key(uid, "slot_${slot}_type"), type)
        }
        editor.apply()
    }

    fun getQuests(uid: Long): List<DailyQuest> {
        val date = prefs.getString(key(uid, "date"), null) ?: return emptyList()
        if (date != todayKey()) return emptyList()
        return (0 until 3).mapNotNull { slot ->
            val type = prefs.getString(key(uid, "slot_${slot}_type"), null) ?: return@mapNotNull null
            val target = prefs.getInt(key(uid, "slot_${slot}_target"), 1)
            val progress = prefs.getInt(key(uid, "slot_${slot}_progress"), 0)
            val claimed = prefs.getBoolean(key(uid, "slot_${slot}_claimed"), false)
            DailyQuest(
                id = "slot_$slot",
                type = type,
                title = titleFor(type, target),
                target = target,
                progress = progress.coerceAtMost(target),
                rewardCoins = rewardCoinsFor(type, target),
                rewardXp = rewardXpFor(type, target),
                isClaimed = claimed
            )
        }
    }

    fun recordProgress(uid: Long, type: String, amount: Int) {
        (0 until 3).forEach { slot ->
            if (prefs.getString(key(uid, "slot_${slot}_type"), null) != type) return@forEach
            if (prefs.getBoolean(key(uid, "slot_${slot}_claimed"), false)) return@forEach
            val target = prefs.getInt(key(uid, "slot_${slot}_target"), 1)
            val current = prefs.getInt(key(uid, "slot_${slot}_progress"), 0)
            val updated = (current + amount).coerceAtMost(target)
            if (updated != current) {
                prefs.edit().putInt(key(uid, "slot_${slot}_progress"), updated).apply()
            }
        }
    }

    fun setClaimed(uid: Long, questId: String) {
        // questId = "slot_N"
        val slot = questId.removePrefix("slot_").toIntOrNull() ?: return
        prefs.edit().putBoolean(key(uid, "slot_${slot}_claimed"), true).apply()
    }

    fun readClaimed(uid: Long, questId: String): Boolean {
        val slot = questId.removePrefix("slot_").toIntOrNull() ?: return true
        return prefs.getBoolean(key(uid, "slot_${slot}_claimed"), false)
    }

    fun readProgress(uid: Long, questId: String): Int {
        val slot = questId.removePrefix("slot_").toIntOrNull() ?: return 0
        val target = prefs.getInt(key(uid, "slot_${slot}_target"), 1)
        return prefs.getInt(key(uid, "slot_${slot}_progress"), 0).coerceAtMost(target)
    }

    // --- Цепочки ачивок: серия "полных дней" (все 3 директивы закрыты) ---

    /**
     * Регистрирует "полный день" (все 3 директивы закрыты и забраны).
     * Серия растет только если предыдущий полный день был вчера,
     * иначе начинается заново с 1. Возвращает актуальную серию.
     */
    fun markFullDay(uid: Long): Long {
        val today = todayKey()
        val lastDate = prefs.getString(key(uid, "full_day_date"), null)
        if (lastDate == today) return getFullDaysStreak(uid)
        val streak = if (lastDate == yesterdayKey()) {
            prefs.getLong(key(uid, "full_day_streak"), 0L) + 1L
        } else {
            1L
        }
        prefs.edit()
            .putString(key(uid, "full_day_date"), today)
            .putLong(key(uid, "full_day_streak"), streak)
            .apply()
        return streak
    }

    /**
     * Текущая серия полных дней. Если последний полный день был не сегодня
     * и не вчера - серия прервана, для прогресса показываем 0
     * (уже открытые ачивки при этом не сбрасываются).
     */
    fun getFullDaysStreak(uid: Long): Long {
        val lastDate = prefs.getString(key(uid, "full_day_date"), null) ?: return 0L
        if (lastDate != todayKey() && lastDate != yesterdayKey()) return 0L
        return prefs.getLong(key(uid, "full_day_streak"), 0L)
    }

    private fun key(uid: Long, suffix: String) = "daily_${uid}_$suffix"

    companion object {
        val QUEST_TYPES = listOf("KILLS", "DEPTH", "SYNC", "SPEND", "CHEST")

        private fun targetFor(type: String, level: Int, rng: Random): Int = when (type) {
            "KILLS" -> 4 + rng.nextInt(4) + level / 3      // 4-9+
            "DEPTH" -> 2 + rng.nextInt(3)                  // сектора: 2-4
            "SYNC" -> 2                                    // синхронизации
            "SPEND" -> (150 + rng.nextInt(150)) * (1 + level / 5) // BC
            "CHEST" -> 1 + rng.nextInt(2)                  // кэши/сундуки
            else -> 3
        }

        fun titleFor(type: String, target: Int): String = when (type) {
            "KILLS" -> "Ликвидировать $target враждебных сущностей"
            "DEPTH" -> "Пройти $target квантовых секторов за рейды"
            "SYNC" -> "Выполнить $target синхронизации протоколов"
            "SPEND" -> "Израсходовать $target BC на оснащение"
            "CHEST" -> "Вскрыть $target кэш-контейнера"
            else -> "Выполнить директиву"
        }

        private fun rewardCoinsFor(type: String, target: Int): Long =
            (when (type) {
                "KILLS" -> 150L
                "DEPTH" -> 200L
                "SYNC" -> 120L
                "SPEND" -> 250L
                "CHEST" -> 180L
                else -> 150L
            } * target) + 100L

        private fun rewardXpFor(type: String, target: Int): Long =
            (when (type) {
                "KILLS" -> 60L
                "DEPTH" -> 90L
                "SYNC" -> 40L
                "SPEND" -> 80L
                "CHEST" -> 70L
                else -> 60L
            } * target)

        @Volatile
        private var INSTANCE: DailyQuestStorage? = null

        fun getInstance(context: Context): DailyQuestStorage =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: DailyQuestStorage(context.applicationContext).also { INSTANCE = it }
            }
    }
}
