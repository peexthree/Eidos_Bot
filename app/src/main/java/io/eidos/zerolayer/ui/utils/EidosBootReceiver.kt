package io.eidos.zerolayer.ui.utils

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Handles device boot completion to reschedule game alarms and background notifications.
 * Explicitly guarded by android.permission.RECEIVE_BOOT_COMPLETED.
 */
class EidosBootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED,
            "android.intent.action.QUICKBOOT_POWERON" -> {
                try {
                    val scheduler = EidosAlarmScheduler(context)
                    scheduler.scheduleDailySyncNotification()
                    scheduler.scheduleNetworkIntrusionNotification()
                } catch (_: Throwable) {}
            }
        }
    }
}
