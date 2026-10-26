package io.eidos.zerolayer.ui.utils

import android.app.Activity
import android.content.Context
import android.util.Log
import com.android.billingclient.api.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

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
        onSuccess: (purchaseToken: String, productId: String) -> Unit
    ) {
        val details = _productDetailsMap.value[productId]
        if (details == null) {
            Log.w("EidosBilling", "Product details not found for product: $productId")
            // Fallback for testing / simulated purchases
            onSuccess("simulated_token_$productId", productId)
            telemetry.logPurchaseSuccess(productId, "SIMULATED_ORDER", 0.0)
            return
        }

        onPurchaseSuccessCallback = onSuccess
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
            Log.w("EidosBilling", "Error launching billing flow: $responseCode")
        }
    }

    override fun onPurchasesUpdated(billingResult: BillingResult, purchases: MutableList<Purchase>?) {
        if (billingResult.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (purchase in purchases) {
                handlePurchase(purchase)
            }
        } else if (billingResult.responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
            Log.d("EidosBilling", "User canceled purchase flow.")
        } else {
            Log.w("EidosBilling", "Purchases updated error: ${billingResult.debugMessage}")
        }
    }

    private fun handlePurchase(purchase: Purchase) {
        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
            if (!purchase.isAcknowledged) {
                val acknowledgePurchaseParams = AcknowledgePurchaseParams.newBuilder()
                    .setPurchaseToken(purchase.purchaseToken)
                    .build()
                billingClient.acknowledgePurchase(acknowledgePurchaseParams) { ackResult ->
                    if (ackResult.responseCode == BillingClient.BillingResponseCode.OK) {
                        Log.d("EidosBilling", "Purchase acknowledged.")
                    }
                }
            }
            val productId = purchase.products.firstOrNull() ?: ""
            onPurchaseSuccessCallback?.invoke(purchase.purchaseToken, productId)
            telemetry.logPurchaseSuccess(productId, purchase.orderId ?: "", 0.0)
        }
    }

    fun destroy() {
        try {
            billingClient.endConnection()
        } catch (_: Throwable) {}
    }
}
