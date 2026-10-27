package io.eidos.zerolayer.ui.utils

import android.app.Activity
import android.content.Context
import android.util.Log
import com.android.billingclient.api.*
import io.eidos.zerolayer.BuildConfig
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.ConcurrentHashMap

class EidosBillingManager(
    private val context: Context,
    private val coroutineScope: CoroutineScope
) : PurchasesUpdatedListener {

    private val telemetry = EidosTelemetryManager.getInstance(context)

    private val _billingConnected = MutableStateFlow(false)
    val billingConnected: StateFlow<Boolean> = _billingConnected.asStateFlow()

    private val _productDetailsMap = MutableStateFlow<Map<String, ProductDetails>>(emptyMap())
    val productDetailsMap: StateFlow<Map<String, ProductDetails>> = _productDetailsMap.asStateFlow()

    private var onPurchaseSuccessCallback: ((purchaseToken: String, productId: String) -> Unit)? = null
    private var onPurchaseErrorCallback: ((errorMessage: String) -> Unit)? = null

    private val consumedTokens: MutableSet<String> = ConcurrentHashMap.newKeySet()

    private val billingClient: BillingClient by lazy {
        BillingClient.newBuilder(context)
            .setListener(this)
            .enablePendingPurchases()
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

        billingClient.queryProductDetailsAsync(paramsInApp) { resultInApp, productDetailsListInApp ->
            val resultMap = _productDetailsMap.value.toMutableMap()
            if (resultInApp.responseCode == BillingClient.BillingResponseCode.OK) {
                productDetailsListInApp.forEach { details ->
                    resultMap[details.productId] = details
                }
            }
            billingClient.queryProductDetailsAsync(paramsSub) { resultSub, productDetailsListSub ->
                if (resultSub.responseCode == BillingClient.BillingResponseCode.OK) {
                    productDetailsListSub.forEach { details ->
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

        val productDetailsParamsList = listOf(
            BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(details)
                .build()
        )

        val billingFlowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(productDetailsParamsList)
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
            if (!validatePurchaseToken(token)) {
                Log.e("EidosBilling", "Invalid or already consumed purchase token: $token")
                onPurchaseErrorCallback?.invoke("Недействительный или ранее использованный токен покупки.")
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
            onPurchaseSuccessCallback?.invoke(token, productId)
            telemetry.logPurchaseSuccess(productId, purchase.orderId ?: "", 0.0)
        }
    }

    fun validatePurchaseToken(token: String): Boolean {
        if (token.isBlank()) return false
        if (consumedTokens.contains(token)) return false
        if (token.startsWith("simulated_token")) {
            return BuildConfig.DEBUG && ALLOW_MOCK_BILLING
        }
        return token.length >= 10
    }

    fun markTokenConsumed(token: String) {
        consumedTokens.add(token)
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
