package com.example.eidos.ui.utils

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.ExistingWorkPolicy
import java.util.concurrent.TimeUnit

class DailyStreakWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val notifications = EidosNotificationManager.getInstance(applicationContext)
        notifications.notifySupplyDropReady()
        return Result.success()
    }

    companion object {
        private const val UNIQUE_WORK_NAME = "eidos_daily_streak_work"

        fun schedule(context: Context, delayMs: Long = 24 * 3600 * 1000L) {
            val workRequest = OneTimeWorkRequestBuilder<DailyStreakWorker>()
                .setInitialDelay(maxOf(1000L, delayMs), TimeUnit.MILLISECONDS)
                .addTag("daily_streak_reminder")
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                workRequest
            )
        }
    }
}
