package io.eidos.zerolayer.ui.utils

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class EidosAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val notificationManager = EidosNotificationManager.getInstance(context)
        when (intent.action) {
            ACTION_ENERGY_RESTORED -> notificationManager.notifyEnergyRestored()
            ACTION_DAILY_SYNC -> notificationManager.notifySupplyDropReady()
            ACTION_NETWORK_INTRUSION -> notificationManager.notifyPvpAttackAlert("Phantom")
        }
    }

    companion object {
        const val ACTION_ENERGY_RESTORED = "io.eidos.zerolayer.ENERGY_RESTORED"
        const val ACTION_DAILY_SYNC = "io.eidos.zerolayer.DAILY_SYNC"
        const val ACTION_NETWORK_INTRUSION = "io.eidos.zerolayer.NETWORK_INTRUSION"
    }
}
