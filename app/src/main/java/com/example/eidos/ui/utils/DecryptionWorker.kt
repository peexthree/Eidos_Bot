package com.example.eidos.ui.utils

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Data
import java.util.concurrent.TimeUnit

class DecryptionWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val itemName = inputData.getString("item_name") ?: "Контейнер"
        
        // Use notification manager to send notification
        val notifications = EidosNotificationManager.getInstance(applicationContext)
        notifications.notifyDecryptionFinished(itemName)
        
        return Result.success()
    }

    companion object {
        fun schedule(context: Context, itemName: String, delayMs: Long) {
            val data = Data.Builder()
                .putString("item_name", itemName)
                .build()

            val workRequest = OneTimeWorkRequestBuilder<DecryptionWorker>()
                .setInputData(data)
                .setInitialDelay(maxOf(0L, delayMs), TimeUnit.MILLISECONDS)
                .addTag("decryption_$itemName")
                .build()

            WorkManager.getInstance(context).enqueue(workRequest)
        }
    }
}
