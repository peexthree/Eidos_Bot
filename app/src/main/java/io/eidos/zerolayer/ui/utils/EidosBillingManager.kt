package io.eidos.zerolayer.ui.utils

import android.app.Activity
import android.content.Context
import android.util.Log
import com.android.billingclient.api.*
import io.eidos.zerolayer.BuildConfig
import io.eidos.zerolayer.data.SupabaseClientManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.ConcurrentHashMap

class EidosBillingManager(
    private val context: Context,
    private val coroutineScope: CoroutineScope
) : PurchasesUpdatedListener {

    private val telemetry = EidosTelemetryManager.getInstance(context)

    // Thin client used only for the fire-and-forget server-side purchase ledger report.
    private val serverReportClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
            .build()
    }

    private val _billingConnected = MutableStateFlow(false)
    val billingConnected: StateFlow<Boolean> = _billingConnected.asStateFlow()

    private val _productDetailsMap = MutableStateFlow<Map<String, ProductDetails>>(emptyMap())
    val productDetailsMap: StateFlow<Map<String, ProductDetails>> = _productDetailsMap.asStateFlow()

    private var onPurchaseSuccessCallback: ((purchaseToken: String, productId: String) -> Unit)? = null
    private var onPurchaseErrorCallback: ((errorMessage: String) -> Unit)? = null

    private val consumedTokensPrefs by lazy {
        context.getSharedPreferences("eidos_consumed_tokens", android.content.Context.MODE_PRIVATE)
    }

    private val consumedTokens: MutableSet<String> = ConcurrentHashMap.newKeySet<String>().apply {
        try {
            val saved = context.getSharedPreferences("eidos_consumed_tokens", android.content.Context.MODE_PRIVATE)
                .getStringSet("tokens", emptySet()) ?: emptySet()
            addAll(saved)
        } catch (_: Throwable) {}
    }

    private val billingClient: BillingClient by lazy {
        // Billing 9: enablePendingPurchases requires explicit params
        BillingClient.newBuilder(context)
            .setListener(this)
            .enablePendingPurchases(
                com.android.billingclient.api.PendingPurchasesParams.newBuilder().build()
            )
            .build()
    }

    fun startConnection(onSuccess: (() -> Unit)? = null) {
        try {
            billingClient.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(billingResult: BillingResult) {
                    if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                        _billingConnected.value = true
                        Log.d("EidosBilling", "Billing setup successful.")
                        querySkuDetails()
                        onSuccess?.invoke()
                    } else {
                        _billingConnected.value = false
                        Log.w("EidosBilling", "Billing setup failed: ${billingResult.debugMessage}")
                    }
                }

                override fun onBillingServiceDisconnected() {
                    _billingConnected.value = false
                    Log.w("EidosBilling", "Billing service disconnected.")
                }
            })
        } catch (e: Throwable) {
            Log.e("EidosBilling", "Error starting billing connection: ${e.message}")
        }
    }

    fun querySkuDetails() {
        if (!_billingConnected.value) return

        val inAppProductList = listOf(
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId("biocoin_pack_1000")
                .setProductType(BillingClient.ProductType.INAPP)
                .build(),
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId("cargo_insurance")
                .setProductType(BillingClient.ProductType.INAPP)
                .build()
        )

        val subProductList = listOf(
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId("neurolink_premium")
                .setProductType(BillingClient.ProductType.SUBS)
                .build()
        )

        val paramsInApp = QueryProductDetailsParams.newBuilder()
            .setProductList(inAppProductList)
            .build()

        val paramsSub = QueryProductDetailsParams.newBuilder()
            .setProductList(subProductList)
            .build()

        // Billing 9: the callback receives a QueryProductDetailsResult wrapper
        // (productDetailsList + unavailableProductList) instead of a bare List.
        billingClient.queryProductDetailsAsync(paramsInApp) { resultInApp, productDetailsResultInApp ->
            val resultMap = _productDetailsMap.value.toMutableMap()
            if (resultInApp.responseCode == BillingClient.BillingResponseCode.OK) {
                productDetailsResultInApp.productDetailsList.forEach { details ->
                    resultMap[details.productId] = details
                }
            }
            billingClient.queryProductDetailsAsync(paramsSub) { resultSub, productDetailsResultSub ->
                if (resultSub.responseCode == BillingClient.BillingResponseCode.OK) {
                    productDetailsResultSub.productDetailsList.forEach { details ->
                        resultMap[details.productId] = details
                    }
                }
                _productDetailsMap.value = resultMap
            }
        }
    }

    fun launchBillingFlow(
        activity: Activity,
        productId: String,
        onError: ((errorMessage: String) -> Unit)? = null,
        onSuccess: (purchaseToken: String, productId: String) -> Unit
    ) {
        val details = _productDetailsMap.value[productId]
        if (details == null) {
            Log.w("EidosBilling", "Product details not found for product: $productId")
            if (BuildConfig.DEBUG && ALLOW_MOCK_BILLING) {
                val mockToken = "simulated_token_$productId"
                if (validatePurchaseToken(mockToken)) {
                    markTokenConsumed(mockToken)
                    onSuccess(mockToken, productId)
                    telemetry.logPurchaseSuccess(productId, "SIMULATED_ORDER", 0.0)
                } else {
                    onError?.invoke("Ошибка симулированного токена.")
                }
            } else {
                val errorMsg = "Платежный шлюз недоступен. Проверьте подключение к сети."
                Log.e("EidosBilling", errorMsg)
                onError?.invoke(errorMsg)
            }
            return
        }

        onPurchaseSuccessCallback = onSuccess
        onPurchaseErrorCallback = onError
        telemetry.logPurchaseInitiated(productId, details.oneTimePurchaseOfferDetails?.formattedPrice ?: "")

        // Subscriptions require an offer token at flow launch (latent bug:
        // without it the flow fails at runtime with an SDK error).
        val detailsParamBuilder = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(details)
        if (details.productType == BillingClient.ProductType.SUBS) {
            val offerToken = details.subscriptionOfferDetails?.firstOrNull()?.offerToken
            if (offerToken == null) {
                val errorMsg = "Нет доступных офферов для подписки $productId."
                Log.e("EidosBilling", errorMsg)
                onError?.invoke(errorMsg)
                return
            }
            detailsParamBuilder.setOfferToken(offerToken)
        }

        val billingFlowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(listOf(detailsParamBuilder.build()))
            .build()

        val responseCode = billingClient.launchBillingFlow(activity, billingFlowParams).responseCode
        if (responseCode != BillingClient.BillingResponseCode.OK) {
            val errorMsg = "Ошибка запуска оплаты (Код: $responseCode)"
            Log.w("EidosBilling", errorMsg)
            onError?.invoke(errorMsg)
        }
    }

    override fun onPurchasesUpdated(billingResult: BillingResult, purchases: MutableList<Purchase>?) {
        if (billingResult.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (purchase in purchases) {
                handlePurchase(purchase)
            }
        } else if (billingResult.responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
            Log.d("EidosBilling", "User canceled purchase flow.")
            onPurchaseErrorCallback?.invoke("Оплата отменена пользователем.")
        } else {
            val errorMsg = "Ошибка оплаты: ${billingResult.debugMessage}"
            Log.w("EidosBilling", errorMsg)
            onPurchaseErrorCallback?.invoke(errorMsg)
        }
    }

    private fun handlePurchase(purchase: Purchase) {
        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
            val token = purchase.purchaseToken
            val signature = purchase.signature
            if (!validatePurchaseToken(token, signature)) {
                // Never log the raw purchase token (sensitive); hash prefix only
                Log.e("EidosBilling", "Invalid, unsigned, or already consumed purchase token: ${hashToken(token).take(12)}…")
                onPurchaseErrorCallback?.invoke("Недействительный, неподписанный или ранее использованный токен покупки.")
                return
            }

            if (!purchase.isAcknowledged) {
                val acknowledgePurchaseParams = AcknowledgePurchaseParams.newBuilder()
                    .setPurchaseToken(token)
                    .build()
                billingClient.acknowledgePurchase(acknowledgePurchaseParams) { ackResult ->
                    if (ackResult.responseCode == BillingClient.BillingResponseCode.OK) {
                        Log.d("EidosBilling", "Purchase acknowledged.")
                    }
                }
            }
            markTokenConsumed(token)
            val productId = purchase.products.firstOrNull() ?: ""
            // Fire-and-forget: register the purchase in the server-side ledger (no effect on
            // local granting). Mock billing tokens are never reported to the server.
            if (!token.startsWith("simulated_token")) {
                CoroutineScope(Dispatchers.IO).launch {
                    runCatching { reportPurchaseToServer(token, productId, purchase.orderId) }
                }
            }
            onPurchaseSuccessCallback?.invoke(token, productId)
            telemetry.logPurchaseSuccess(productId, purchase.orderId ?: "", 0.0)
        }
    }

    /**
     * Fire-and-forget report of a real Google Play purchase to the Supabase Edge Function
     * (verify-purchase) that verifies the purchase and records it in the server-side ledger
     * (app_purchases) for future use. This never changes local biocoin granting:
     * local logic stays exactly as it was. Any failure is logged and ignored.
     */
    private suspend fun reportPurchaseToServer(token: String, productId: String, orderId: String?) {
        try {
            val baseUrl = SupabaseClientManager.baseUrl
            if (baseUrl.isBlank()) return
            val payload = org.json.JSONObject().apply {
                put("purchaseToken", token)
                put("productId", productId)
                put("orderId", orderId ?: org.json.JSONObject.NULL)
            }.toString()

            val requestBuilder = Request.Builder()
                .url("$baseUrl/functions/v1/verify-purchase")
                .addHeader("apikey", SupabaseClientManager.apiKey)
                .addHeader("Content-Type", "application/json")
            val accessToken = SupabaseClientManager.cachedAccessToken
            if (!accessToken.isNullOrBlank()) {
                requestBuilder.addHeader("Authorization", "Bearer $accessToken")
            }
            val request = requestBuilder
                .post(payload.toRequestBody("application/json".toMediaType()))
                .build()

            serverReportClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    // Never log the raw purchase token (sensitive); hash prefix only
                    Log.w("EidosBilling", "reportPurchaseToServer: HTTP ${response.code}, token ${hashToken(token).take(12)}…")
                } else {
                    Log.d("EidosBilling", "reportPurchaseToServer: purchase recorded on server.")
                }
            }
        } catch (e: Exception) {
            Log.w("EidosBilling", "reportPurchaseToServer failed: ${e.message}")
        }
    }

    private fun hashToken(token: String): String {
        val digest = java.security.MessageDigest.getInstance("SHA-256")
        val bytes = digest.digest(("eidos_billing_salt_" + token.trim()).toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }

    fun validatePurchaseToken(token: String, signature: String? = null): Boolean {
        if (token.isBlank()) return false
        val tokenHash = hashToken(token)
        if (consumedTokens.contains(tokenHash) || consumedTokens.contains(token)) return false
        if (token.startsWith("simulated_token")) {
            return BuildConfig.DEBUG && ALLOW_MOCK_BILLING
        }
        // In release builds, real Google Play purchases must have a cryptographically signed payload
        if (!BuildConfig.DEBUG && signature.isNullOrBlank()) {
            Log.w("EidosBilling", "Validation failed: Missing Google Play RSA signature on purchase.")
            return false
        }
        // Google Play purchase tokens are high-entropy base64 strings (typically > 32 characters)
        return token.length >= 32 && !token.contains(" ")
    }

    fun markTokenConsumed(token: String) {
        val tokenHash = hashToken(token)
        consumedTokens.add(tokenHash)
        consumedTokens.add(token)
        try {
            val set = HashSet(consumedTokensPrefs.getStringSet("tokens", emptySet()) ?: emptySet())
            set.add(tokenHash)
            consumedTokensPrefs.edit().putStringSet("tokens", set).apply()
        } catch (_: Throwable) {}
    }

    fun destroy() {
        try {
            billingClient.endConnection()
        } catch (_: Throwable) {}
    }

    companion object {
        const val ALLOW_MOCK_BILLING = false
    }
}
