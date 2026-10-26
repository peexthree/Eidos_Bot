package com.example.eidos.ui.utils

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
        const val ACTION_ENERGY_RESTORED = "com.example.eidos.ENERGY_RESTORED"
        const val ACTION_DAILY_SYNC = "com.example.eidos.DAILY_SYNC"
        const val ACTION_NETWORK_INTRUSION = "com.example.eidos.NETWORK_INTRUSION"
    }
}
