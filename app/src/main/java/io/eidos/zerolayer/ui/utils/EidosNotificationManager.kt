package io.eidos.zerolayer.ui.utils

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import io.eidos.zerolayer.R

class EidosNotificationManager private constructor(private val context: Context) {

    private val notificationManager =
        context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    companion object {
        const val CHANNEL_ID = "eidos_system_alerts"
        const val CHANNEL_NAME = "EIDOS System Directives"

        @Volatile
        private var instance: EidosNotificationManager? = null

        fun getInstance(context: Context): EidosNotificationManager {
            return instance ?: synchronized(this) {
                instance ?: EidosNotificationManager(context.applicationContext).also { instance = it }
            }
        }
    }

    init {
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            if (notificationManager.getNotificationChannel(CHANNEL_ID) == null) {
                val importance = NotificationManager.IMPORTANCE_HIGH
                val channel = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, importance).apply {
                    description = "Tactical alerts, supply drop notifications, and raid warnings from System EIDOS"
                    enableVibration(true)
                }
                notificationManager.createNotificationChannel(channel)
            }
        }
    }

    fun hasPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                android.Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    fun sendNotification(id: Int, title: String, message: String) {
        if (!hasPermission()) return

        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))

        try {
            notificationManager.notify(id, builder.build())
        } catch (e: SecurityException) {
            // Permission missing or denied at runtime
        }
    }

    fun notifySupplyDropReady() {
        sendNotification(
            1001,
            "📦 EIDOS: Поставка Загружена",
            "Ежедневный контейнер с био-чипами и кэшем готов к активации в Хабе!"
        )
    }

    fun notifySignalRestored() {
        sendNotification(
            1002,
            "⚡ EIDOS: Сигнал Восстановлен",
            "Нейро-Канал восстановлен до 100%. Вы готовы к новому рейду!"
        )
    }

    fun notifyDecryptionFinished(itemName: String) {
        sendNotification(
            1003,
            "🔓 EIDOS: Дешифровка Завершена",
            "Контейнер с предметом «$itemName» успешно разблокирован!"
        )
    }

    fun notifyPvpAttackAlert(attackerName: String) {
        sendNotification(
            1004,
            "🚨 EIDOS: Внимание, Взлом!",
            "Рейдер $attackerName пытался пробить ваши брандмауэры. Проверьте журнал PvP!"
        )
    }

    fun notifyRaidWarning(hazardName: String) {
        sendNotification(
            1005,
            "☣️ EIDOS: Критическая Аномалия",
            "Обнаружена зона повышенной опасности: $hazardName. Будьте предельно осторожны!"
        )
    }

    fun notifyEnergyRestored() {
        sendNotification(
            2001,
            "⚡ СИГНАЛ СТАБИЛЕН",
            "Энергия восполнена (100/100). Нулевой Слой ждет!"
        )
    }

    fun notifyCacheUnlocked() {
        sendNotification(
            2004,
            "🔓 КЭШ ВЗЛОМАН",
            "Дешифрация завершена. Заберите артефакт в Хабе!"
        )
    }

    fun notifyMarketRefresh() {
        sendNotification(
            2005,
            "🛒 ЧЕРНЫЙ РЫНОК",
            "Теневой брокер обновил партию квантового софта!"
        )
    }

    fun notifyRetentionSignal() {
        sendNotification(
            2006,
            "📡 ПЕРЕХВАТ",
            "В секторе Бездны зафиксирована аномалия с ценным лутом."
        )
    }

    fun notifyAchievementUnlocked(title: String) {
        sendNotification(
            3001,
            "🏆 ДОСТИЖЕНИЕ ПОЛУЧЕНО",
            "Вы разблокировали веху: $title!"
        )
    }
}
