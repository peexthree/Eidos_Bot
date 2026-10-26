package com.example.eidos.ui.utils

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.ExistingWorkPolicy
import java.util.concurrent.TimeUnit

class EnergyRecoveryWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val notifications = EidosNotificationManager.getInstance(applicationContext)
        notifications.notifyEnergyRestored()
        return Result.success()
    }

    companion object {
        private const val UNIQUE_WORK_NAME = "eidos_energy_recovery_work"

        fun schedule(context: Context, delayMs: Long) {
            if (delayMs <= 0L) return

            val workRequest = OneTimeWorkRequestBuilder<EnergyRecoveryWorker>()
                .setInitialDelay(delayMs, TimeUnit.MILLISECONDS)
                .addTag("energy_recovery")
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                workRequest
            )
        }
    }
}
