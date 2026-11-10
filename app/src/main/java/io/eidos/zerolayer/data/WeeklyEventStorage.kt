package io.eidos.zerolayer.data

import android.content.Context
import android.content.SharedPreferences
import io.eidos.zerolayer.domain.weekly.WeeklyEvent
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.random.Random

/** Результат синхронизации недельного события: id активного события и признак ротации. */
data class WeeklyEventSync(val eventId: String, val changed: Boolean)

/**
 * Недельные события: один модификатор на ISO-неделю, детерминированно по seed
 * (weekKey + uid), по образцу DailyQuestStorage. Хранение в SharedPreferences -
 * без миграции Room (как и дейлики).
 */
class WeeklyEventStorage private constructor(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("eidos_weekly_event_prefs", Context.MODE_PRIVATE)

    /** ISO-неделя вида "2026-W46". */
    fun weekKey(): String = SimpleDateFormat("yyyy-'W'ww", Locale.US).format(Date())

    /**
     * Ленивая ротация: если хранимая неделя != текущей, выбирается новое событие.
     * @return активное событие и признак "событие сменилось при этом вызове"
     *         (в т.ч. самая первая генерация - для анонса по радио).
     */
    fun syncAndGet(uid: Long): WeeklyEventSync {
        val week = weekKey()
        val storedWeek = prefs.getString(key(uid, "week"), null)
        val storedEvent = prefs.getString(key(uid, "event_id"), null)
        if (storedWeek == week && storedEvent != null) {
            return WeeklyEventSync(storedEvent, changed = false)
        }
        val chosen = WeeklyEvent.entries.random(Random((week + "_$uid").hashCode()))
        prefs.edit()
            .putString(key(uid, "week"), week)
            .putString(key(uid, "event_id"), chosen.id)
            .apply()
        return WeeklyEventSync(chosen.id, changed = true)
    }

    /** Текущее событие без информации о ротации (для эффектов в choke points). */
    fun getCurrentEventId(uid: Long): String = syncAndGet(uid).eventId

    private fun key(uid: Long, suffix: String) = "weekly_${uid}_$suffix"

    companion object {
        @Volatile
        private var INSTANCE: WeeklyEventStorage? = null

        fun getInstance(context: Context): WeeklyEventStorage =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: WeeklyEventStorage(context.applicationContext).also { INSTANCE = it }
            }
    }
}
