package com.example.eidos.ui.utils

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build

class EidosAlarmScheduler(private val context: Context) {

    private val alarmManager: AlarmManager? = try {
        context.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
    } catch (_: Throwable) {
        null
    }

    fun scheduleEnergyRestoredNotification(delayMillis: Long = 2 * 60 * 60 * 1000L) {
        try {
            val intent = Intent(context, EidosAlarmReceiver::class.java).apply {
                action = EidosAlarmReceiver.ACTION_ENERGY_RESTORED
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                101,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            val triggerAtMs = System.currentTimeMillis() + delayMillis
            scheduleExactOrInexact(triggerAtMs, pendingIntent)
        } catch (_: Throwable) {}
    }

    fun scheduleDailySyncNotification(delayMillis: Long = 24 * 60 * 60 * 1000L) {
        try {
            val intent = Intent(context, EidosAlarmReceiver::class.java).apply {
                action = EidosAlarmReceiver.ACTION_DAILY_SYNC
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                102,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            val triggerAtMs = System.currentTimeMillis() + delayMillis
            scheduleExactOrInexact(triggerAtMs, pendingIntent)
        } catch (_: Throwable) {}
    }

    fun scheduleNetworkIntrusionNotification(delayMillis: Long = 4 * 60 * 60 * 1000L) {
        try {
            val intent = Intent(context, EidosAlarmReceiver::class.java).apply {
                action = EidosAlarmReceiver.ACTION_NETWORK_INTRUSION
            }
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                103,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            val triggerAtMs = System.currentTimeMillis() + delayMillis
            scheduleExactOrInexact(triggerAtMs, pendingIntent)
        } catch (_: Throwable) {}
    }

    private fun scheduleExactOrInexact(triggerAtMs: Long, pendingIntent: PendingIntent) {
        val manager = alarmManager ?: return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMs, pendingIntent)
            } else {
                manager.set(AlarmManager.RTC_WAKEUP, triggerAtMs, pendingIntent)
            }
        } catch (_: Throwable) {
            try {
                manager.set(AlarmManager.RTC_WAKEUP, triggerAtMs, pendingIntent)
            } catch (_: Throwable) {}
        }
    }
}
