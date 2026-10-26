package io.eidos.zerolayer.ui.utils

import android.content.Context
import android.os.Bundle
import android.util.Log
import com.google.firebase.analytics.FirebaseAnalytics
import com.google.firebase.crashlytics.FirebaseCrashlytics

class EidosTelemetryManager private constructor(context: Context) {

    private var firebaseAnalytics: FirebaseAnalytics? = null
    private var firebaseCrashlytics: FirebaseCrashlytics? = null

    init {
        try {
            firebaseAnalytics = FirebaseAnalytics.getInstance(context)
            firebaseCrashlytics = FirebaseCrashlytics.getInstance()
        } catch (e: Throwable) {
            Log.w("EidosTelemetry", "Firebase services initialized in offline/stub mode: ${e.message}")
        }
    }

    fun logEvent(eventName: String, params: Map<String, Any> = emptyMap()) {
        try {
            val bundle = Bundle()
            params.forEach { (key, value) ->
                when (value) {
                    is String -> bundle.putString(key, value)
                    is Int -> bundle.putInt(key, value)
                    is Long -> bundle.putLong(key, value)
                    is Double -> bundle.putDouble(key, value)
                    is Boolean -> bundle.putBoolean(key, value)
                    else -> bundle.putString(key, value.toString())
                }
            }
            firebaseAnalytics?.logEvent(eventName, bundle)
            Log.d("EidosTelemetry", "Logged event: $eventName ($params)")
        } catch (e: Throwable) {
            Log.w("EidosTelemetry", "Error logging event $eventName: ${e.message}")
        }
    }

    fun logOnboardingStepCompleted(stepIndex: Int, stepName: String) {
        logEvent(
            "onboarding_step_completed",
            mapOf(
                "step_index" to stepIndex,
                "step_name" to stepName
            )
        )
    }

    fun logRaidStarted(depth: Int, initialSignal: Int) {
        logEvent(
            "raid_started",
            mapOf(
                "depth" to depth,
                "signal" to initialSignal
            )
        )
    }

    fun logRaidFailedAtAnomaly(anomalyId: String, depth: Int) {
        logEvent(
            "raid_failed_at_anomaly",
            mapOf(
                "anomaly_id" to anomalyId,
                "depth" to depth
            )
        )
    }

    fun logPurchaseInitiated(skuId: String, priceText: String = "") {
        logEvent(
            "purchase_initiated",
            mapOf(
                "sku_id" to skuId,
                "price" to priceText
            )
        )
    }

    fun logPurchaseSuccess(skuId: String, orderId: String = "", price: Double = 0.0) {
        logEvent(
            "purchase_success",
            mapOf(
                "sku_id" to skuId,
                "order_id" to orderId,
                "price" to price
            )
        )
    }

    fun recordException(throwable: Throwable) {
        try {
            firebaseCrashlytics?.recordException(throwable)
        } catch (e: Throwable) {
            Log.w("EidosTelemetry", "Error recording exception: ${e.message}")
        }
    }

    companion object {
        @Volatile
        private var instance: EidosTelemetryManager? = null

        fun getInstance(context: Context): EidosTelemetryManager {
            return instance ?: synchronized(this) {
                instance ?: EidosTelemetryManager(context.applicationContext).also { instance = it }
            }
        }
    }
}
