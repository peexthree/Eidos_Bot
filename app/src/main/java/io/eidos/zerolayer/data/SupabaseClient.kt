package io.eidos.zerolayer.data

import io.eidos.zerolayer.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import android.content.Context
import android.util.Log

@Serializable
data class AuthSignUpRequest(
    val email: String,
    val password: String,
    val data: Map<String, String> = emptyMap()
)

@Serializable
data class AuthSignInRequest(
    val email: String,
    val password: String
)

@Serializable
data class AuthUser(
    val id: String,
    val email: String? = null,
    @SerialName("user_metadata") val userMetadata: Map<String, String>? = null,
    @SerialName("created_at") val createdAt: String? = null
)

@Serializable
data class AuthResponse(
    @SerialName("access_token") val accessToken: String? = null,
    @SerialName("token_type") val tokenType: String? = null,
    @SerialName("expires_in") val expiresIn: Long? = null,
    @SerialName("refresh_token") val refreshToken: String? = null,
    val user: AuthUser? = null,
    @SerialName("error_description") val errorDescription: String? = null,
    val msg: String? = null,
    val message: String? = null,
    val error: String? = null
)

sealed class AuthResult {
    data class Success(
        val user: AuthUser,
        val accessToken: String,
        val refreshToken: String?,
        val username: String,
        val isNewAccount: Boolean
    ) : AuthResult()

    data class Error(val message: String) : AuthResult()
}

@Serializable
data class SupabasePlayer(
    val id: String? = null,
    @SerialName("device_id") val deviceId: String,
    val username: String,
    val level: Int = 1,
    val exp: Long = 0,
    val biocoins: Long = 0,
    val hp: Int = 100,
    val energy: Int = 100,
    val rank: String = "Новичок",
    @SerialName("max_depth") val maxDepth: Int = 0,
    @SerialName("kills") val kills: Int = 0,
    @SerialName("defense_program_1") val defense_program_1: String = "SHIELD",
    @SerialName("defense_program_2") val defense_program_2: String = "BRUTEFORCE",
    @SerialName("defense_program_3") val defense_program_3: String = "STEALTH",
    @SerialName("installed_hardware") val installed_hardware: String? = null,
    @SerialName("pvp_proxy_until") val pvp_proxy_until: Long = 0L,
    @SerialName("state_version") val stateVersion: Long = 1,
    @SerialName("updated_at") val updatedAt: String? = null
)

@Serializable
data class SupabaseInventoryItem(
    val id: String? = null,
    @SerialName("player_id") val playerId: String,
    @SerialName("item_id") val itemId: String,
    val quantity: Int = 1,
    @SerialName("is_equipped") val isEquipped: Boolean = false
)

@Serializable
data class SupabaseRaidLog(
    val id: String? = null,
    @SerialName("player_id") val playerId: String,
    @SerialName("log_text") val logText: String,
    @SerialName("created_at") val createdAt: String? = null
)

@Serializable
data class RpcRaidRewardRequest(
    @SerialName("p_exp") val exp: Long,
    @SerialName("p_biocoins") val biocoins: Long,
    @SerialName("p_depth") val depth: Int
)

@Serializable
data class RpcRaidRewardResponse(
    val success: Boolean = false,
    val exp: Long = 0,
    val biocoins: Long = 0,
    @SerialName("max_depth") val maxDepth: Int = 0,
    val message: String? = null
)

@Serializable
data class RpcBlackMarketRequest(
    @SerialName("p_item_id") val itemId: String,
    @SerialName("p_cost") val cost: Long,
    @SerialName("p_quantity") val quantity: Int = 1
)

@Serializable
data class RpcBlackMarketResponse(
    val success: Boolean = false,
    @SerialName("item_id") val itemId: String? = null,
    val biocoins: Long = 0,
    val message: String? = null
)

@Serializable
data class RpcSyncInventoryRequest(
    @SerialName("p_player_id") val playerId: String,
    @SerialName("p_items") val items: List<SupabaseInventoryItem>
)

object SupabaseClientManager {
    val baseUrl: String = BuildConfig.SUPABASE_URL.trimEnd('/')
    val apiKey: String = BuildConfig.SUPABASE_ANON_KEY

    var cachedPlayerUuid: String? = null
    var cachedAccessToken: String? = null

    fun getAuthHeader(): String {
        val token = cachedAccessToken
        return if (!token.isNullOrBlank()) "Bearer $token" else "Bearer $apiKey"
    }

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(10, java.util.concurrent.TimeUnit.SECONDS)
        .callTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
        .build()

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        explicitNulls = false
    }

    fun isConfigured(): Boolean = baseUrl.isNotBlank() && apiKey.isNotBlank()

    fun toVirtualEmail(username: String): String {
        val clean = username.trim().lowercase()
        val digest = java.security.MessageDigest.getInstance("SHA-256")
            .digest(clean.toByteArray(Charsets.UTF_8))
        val hashHex = digest.joinToString("") { "%02x".format(it) }
        return "op_${hashHex.take(32)}@eidos.app"
    }

    fun toLegacyVirtualEmail(username: String): String {
        val clean = username.trim().lowercase()
        val hex = clean.toByteArray(Charsets.UTF_8).joinToString("") { "%02x".format(it) }
        return "op_${hex.take(32)}@eidos.app"
    }

    /**
     * Register new operator in Supabase Auth using virtual email.
     */
    suspend fun signUpWithCredentials(username: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext AuthResult.Error("Supabase не сконфигурирован. Проверьте ключи подключения.")
        val cleanUsername = username.trim()
        if (cleanUsername.length < 3) return@withContext AuthResult.Error("Позывной должен содержать не менее 3 символов.")
        if (password.length < 6) return@withContext AuthResult.Error("Пароль должен содержать минимум 6 символов.")

        try {
            val email = toVirtualEmail(cleanUsername)
            val url = "$baseUrl/auth/v1/signup"
            val reqObj = AuthSignUpRequest(
                email = email,
                password = password,
                data = mapOf("username" to cleanUsername)
            )
            val bodyJson = json.encodeToString(reqObj)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                val respStr = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    val authData = json.decodeFromString<AuthResponse>(respStr)
                    val user = authData.user
                    val token = authData.accessToken ?: ""
                    if (user != null) {
                        cachedPlayerUuid = user.id
                        cachedAccessToken = token
                        return@withContext AuthResult.Success(
                            user = user,
                            accessToken = token,
                            refreshToken = authData.refreshToken,
                            username = cleanUsername,
                            isNewAccount = true
                        )
                    }
                } else {
                    val humanReadableError = when {
                        respStr.contains("User already registered", ignoreCase = true) || respStr.contains("already exists", ignoreCase = true) ->
                            "Оператор с позывным «$cleanUsername» уже зарегистрирован. Выберите Вход."
                        respStr.contains("Password should be at least 6", ignoreCase = true) ->
                            "Пароль должен содержать минимум 6 символов."
                        else -> "Ошибка регистрации: проверьте соединение."
                    }
                    return@withContext AuthResult.Error(humanReadableError)
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE_AUTH", "signUp Exception: ${e.message}")
            return@withContext AuthResult.Error("Сетевая ошибка: ${e.localizedMessage ?: e.message}")
        }
        return@withContext AuthResult.Error("Не удалось зарегистрировать аккаунт.")
    }

    private suspend fun attemptSignInWithEmail(email: String, password: String, cleanUsername: String): AuthResult {
        val url = "$baseUrl/auth/v1/token?grant_type=password"
        val reqObj = AuthSignInRequest(email = email, password = password)
        val bodyJson = json.encodeToString(reqObj)
        val request = Request.Builder()
            .url(url)
            .addHeader("apikey", apiKey)
            .addHeader("Content-Type", "application/json")
            .post(bodyJson.toRequestBody("application/json".toMediaType()))
            .build()

        httpClient.newCall(request).execute().use { response ->
            val respStr = response.body?.string() ?: ""
            if (response.isSuccessful) {
                val authData = json.decodeFromString<AuthResponse>(respStr)
                val user = authData.user
                val token = authData.accessToken ?: ""
                if (user != null && token.isNotBlank()) {
                    cachedPlayerUuid = user.id
                    cachedAccessToken = token
                    return AuthResult.Success(
                        user = user,
                        accessToken = token,
                        refreshToken = authData.refreshToken,
                        username = cleanUsername,
                        isNewAccount = false
                    )
                }
            } else {
                val humanReadableError = when {
                    respStr.contains("Invalid login credentials", ignoreCase = true) ->
                        "Неверный позывной или пароль оператора."
                    respStr.contains("Email not confirmed", ignoreCase = true) ->
                        "В панели Supabase необходимо отключить Confirm Email (Authentication -> Providers -> Email -> Confirm email -> Off)."
                    else -> "Не удалось авторизовать оператора."
                }
                return AuthResult.Error(humanReadableError)
            }
        }
        return AuthResult.Error("Не удалось выполнить вход.")
    }

    /**
     * Sign in existing operator in Supabase Auth (tries SHA-256 virtual email with legacy fallback).
     */
    suspend fun signInWithCredentials(username: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext AuthResult.Error("Supabase не сконфигурирован.")
        val cleanUsername = username.trim()
        if (cleanUsername.isBlank()) return@withContext AuthResult.Error("Введите позывной.")
        if (password.isBlank()) return@withContext AuthResult.Error("Введите пароль.")

        try {
            val primaryEmail = toVirtualEmail(cleanUsername)
            val legacyEmail = toLegacyVirtualEmail(cleanUsername)

            val primaryResult = attemptSignInWithEmail(primaryEmail, password, cleanUsername)
            if (primaryResult is AuthResult.Success) {
                return@withContext primaryResult
            }

            // Fallback to legacy email if primary failed with invalid credentials and emails differ
            if (primaryEmail != legacyEmail) {
                val legacyResult = attemptSignInWithEmail(legacyEmail, password, cleanUsername)
                if (legacyResult is AuthResult.Success) {
                    return@withContext legacyResult
                }
            }

            return@withContext primaryResult
        } catch (e: Exception) {
            Log.e("SUPABASE_AUTH", "signIn Exception: ${e.message}")
            return@withContext AuthResult.Error("Сетевой сбой при входе: ${e.localizedMessage ?: e.message}")
        }
    }

    /**
     * Generate a cryptographically random password (letters + digits).
     */
    private fun generateSecurePassword(length: Int = 32): String {
        val alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        val random = java.security.SecureRandom()
        return buildString {
            repeat(length) {
                append(alphabet[random.nextInt(alphabet.length)])
            }
        }
    }

    /**
     * Sign in anonymously using device ID as a guest account.
     * Tries the locally stored cryptographically random password first, then the
     * legacy deterministic password for existing guest accounts, and finally
     * registers a new guest with a random password (persisted when secure
     * storage is available).
     */
    suspend fun signInAnonymously(deviceId: String, appContext: Context? = null): AuthResult = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext AuthResult.Error("Supabase не сконфигурирован.")
        val cleanDevice = deviceId.ifBlank { "guest_" + System.currentTimeMillis() }
        val anonUsername = "Guest_${cleanDevice.takeLast(6)}"
        val legacyPassword = "EidosAnonPassword_${cleanDevice.hashCode()}"

        val authStore = appContext?.let { EidosAuthStore.getInstance(it) }

        // 1. Prefer the locally stored random password
        val storedPassword = authStore?.loadGuestPassword(cleanDevice)
        if (!storedPassword.isNullOrBlank()) {
            val storedResult = signInWithCredentials(anonUsername, storedPassword)
            if (storedResult is AuthResult.Success) {
                return@withContext storedResult
            }
        }

        // 2. Legacy fallback keeps pre-existing guest accounts accessible
        val legacyResult = signInWithCredentials(anonUsername, legacyPassword)
        if (legacyResult is AuthResult.Success) {
            return@withContext legacyResult
        }

        // 3. Register a new guest with a cryptographically random password
        val anonPassword = generateSecurePassword()
        val signUpResult = signUpWithCredentials(anonUsername, anonPassword)
        if (signUpResult is AuthResult.Success) {
            authStore?.saveGuestPassword(cleanDevice, anonPassword)
            return@withContext signUpResult
        }

        return@withContext AuthResult.Error("Не удалось инициализировать анонимный вход.")
    }

    /**
     * Call PostgreSQL RPC `process_raid_reward` stored procedure.
     */
    suspend fun processRaidRewardRpc(
        accessToken: String,
        exp: Long,
        biocoins: Long,
        depth: Int
    ): RpcRaidRewardResponse? = withContext(Dispatchers.IO) {
        if (!isConfigured() || accessToken.isBlank()) return@withContext null
        try {
            val url = "$baseUrl/rest/v1/rpc/process_raid_reward"
            val reqObj = RpcRaidRewardRequest(exp = exp, biocoins = biocoins, depth = depth)
            val bodyJson = json.encodeToString(reqObj)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $accessToken")
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    return@withContext json.decodeFromString<RpcRaidRewardResponse>(respStr)
                } else {
                    Log.e("SUPABASE_RPC", "processRaidRewardRpc HTTP ${response.code}: ${response.message}")
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE_RPC", "processRaidRewardRpc Exception: ${e.message}")
        }
        return@withContext null
    }

    /**
     * Call PostgreSQL RPC `black_market_purchase` stored procedure.
     */
    suspend fun blackMarketPurchaseRpc(
        accessToken: String,
        itemId: String,
        cost: Long,
        quantity: Int = 1
    ): RpcBlackMarketResponse? = withContext(Dispatchers.IO) {
        if (!isConfigured() || accessToken.isBlank()) return@withContext null
        try {
            val url = "$baseUrl/rest/v1/rpc/black_market_purchase"
            val reqObj = RpcBlackMarketRequest(itemId = itemId, cost = cost, quantity = quantity)
            val bodyJson = json.encodeToString(reqObj)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $accessToken")
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    return@withContext json.decodeFromString<RpcBlackMarketResponse>(respStr)
                } else {
                    Log.e("SUPABASE_RPC", "blackMarketPurchaseRpc HTTP ${response.code}: ${response.message}")
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE_RPC", "blackMarketPurchaseRpc Exception: ${e.message}")
        }
        return@withContext null
    }

    /**
     * Logout active session from Supabase.
     */
    suspend fun logoutSession(accessToken: String): Boolean = withContext(Dispatchers.IO) {
        cachedPlayerUuid = null
        cachedAccessToken = null
        if (!isConfigured() || accessToken.isBlank()) return@withContext true
        try {
            val url = "$baseUrl/auth/v1/logout"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $accessToken")
                .post("".toRequestBody())
                .build()

            httpClient.newCall(request).execute().use { response ->
                return@withContext response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("SUPABASE_AUTH", "logout Exception: ${e.message}")
        }
        return@withContext false
    }

    /**
     * Upsert player into `app_players` table and return synchronized model.
     */
    suspend fun syncPlayer(supabasePlayer: SupabasePlayer): SupabasePlayer? = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext null
        try {
            val url = "$baseUrl/rest/v1/app_players?on_conflict=device_id"
            val bodyJson = json.encodeToString(supabasePlayer)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .addHeader("Content-Type", "application/json")
                .addHeader("Prefer", "resolution=merge-duplicates,return=representation")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val list = json.decodeFromString<List<SupabasePlayer>>(respStr)

                    val synced = list.firstOrNull() ?: supabasePlayer

                    if (synced.id != null) {
                        cachedPlayerUuid = synced.id
                    }

                    return@withContext synced
                } else {
                    Log.e("SUPABASE", "syncPlayer HTTP Error: ${response.code} ${response.message}")
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "syncPlayer Exception: ${e.message}")
        }
        return@withContext null
    }

    /**
     * Fetch player from `app_players` by device_id.
     */
    suspend fun fetchPlayerByDeviceId(deviceId: String): SupabasePlayer? = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext null
        try {
            val url = "$baseUrl/rest/v1/app_players?device_id=eq.$deviceId&select=*"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .get()
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val list = json.decodeFromString<List<SupabasePlayer>>(respStr)

                    val player = list.firstOrNull()

                    if (player?.id != null) {

                        cachedPlayerUuid = player.id

                    }

                    return@withContext player
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "fetchPlayerByDeviceId Exception: ${e.message}")
        }
        return@withContext null
    }

    /**
     * Sync inventory items to `app_inventory` (Atomic PostgreSQL RPC with transactional guarantee).
     */
    suspend fun syncInventory(playerId: String, items: List<SupabaseInventoryItem>): Boolean = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext false
        val validPlayerId = if (playerId.length == 36 && playerId.contains("-")) playerId else cachedPlayerUuid
        if (validPlayerId.isNullOrBlank()) {
            Log.w("SUPABASE", "syncInventory skipped: no valid UUID for player ($playerId)")
            return@withContext false
        }

        try {
            val safeItems = items.map { it.copy(playerId = validPlayerId) }

            // 1. Preferred: Call atomic PostgreSQL stored procedure (single transaction, no data loss window)
            val rpcUrl = "$baseUrl/rest/v1/rpc/sync_player_inventory"
            val rpcReq = RpcSyncInventoryRequest(playerId = validPlayerId, items = safeItems)
            val rpcBody = json.encodeToString(rpcReq)
            val rpcRequest = Request.Builder()
                .url(rpcUrl)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .addHeader("Content-Type", "application/json")
                .post(rpcBody.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(rpcRequest).execute().use { resp ->
                if (resp.isSuccessful) {
                    return@withContext true
                }
                Log.w("SUPABASE", "sync_player_inventory RPC returned ${resp.code}, falling back to REST batch")
            }

            // 2. Fallback in case RPC is not yet deployed on database instance:
            val deleteUrl = "$baseUrl/rest/v1/app_inventory?player_id=eq.$validPlayerId"
            val deleteRequest = Request.Builder()
                .url(deleteUrl)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .delete()
                .build()
            httpClient.newCall(deleteRequest).execute().close()

            if (items.isEmpty()) {
                return@withContext true
            }

            val insertUrl = "$baseUrl/rest/v1/app_inventory"
            val bodyJson = json.encodeToString(safeItems)
            val insertRequest = Request.Builder()
                .url(insertUrl)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()
            httpClient.newCall(insertRequest).execute().use { resp ->
                return@withContext resp.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "syncInventory Exception: ${e.message}")
        }
        return@withContext false
    }

    /**
     * Explicitly delete item(s) from `app_inventory` in Supabase for a player.
     */
    suspend fun deleteInventoryItem(playerId: String, itemId: String): Boolean = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext false
        val validPlayerId = if (playerId.length == 36 && playerId.contains("-")) playerId else cachedPlayerUuid
        if (validPlayerId.isNullOrBlank()) return@withContext false
        try {
            val url = "$baseUrl/rest/v1/app_inventory?player_id=eq.$validPlayerId&item_id=eq.$itemId"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .delete()
                .build()
            httpClient.newCall(request).execute().use { resp ->
                return@withContext resp.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "deleteInventoryItem Exception: ${e.message}")
        }
        return@withContext false
    }

    /**
     * Update `is_equipped` flag for an item in Supabase `app_inventory`.
     */
    suspend fun updateInventoryItemEquipped(playerId: String, itemId: String, isEquipped: Boolean): Boolean = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext false
        val validPlayerId = if (playerId.length == 36 && playerId.contains("-")) playerId else cachedPlayerUuid
        if (validPlayerId.isNullOrBlank()) return@withContext false
        try {
            val url = "$baseUrl/rest/v1/app_inventory?player_id=eq.$validPlayerId&item_id=eq.$itemId"
            val updateJson = """{"is_equipped":$isEquipped}"""
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .addHeader("Content-Type", "application/json")
                .addHeader("Prefer", "return=minimal")
                .patch(updateJson.toRequestBody("application/json".toMediaType()))
                .build()
            httpClient.newCall(request).execute().use { resp ->
                return@withContext resp.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "updateInventoryItemEquipped Exception: ${e.message}")
        }
        return@withContext false
    }

    /**
     * Fetch player inventory items from `app_inventory`.
     */
    suspend fun fetchInventory(playerId: String): List<SupabaseInventoryItem> = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext emptyList()
        val validPlayerId = if (playerId.length == 36 && playerId.contains("-")) playerId else cachedPlayerUuid
        if (validPlayerId.isNullOrBlank()) return@withContext emptyList()
        try {
            val url = "$baseUrl/rest/v1/app_inventory?player_id=eq.$validPlayerId"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .get()
                .build()
            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    return@withContext json.decodeFromString<List<SupabaseInventoryItem>>(respStr)
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "fetchInventory Exception: ${e.message}")
        }
        return@withContext emptyList()
    }

    /**
     * Fetch leaderboard top players from `app_players`.
     */
    suspend fun fetchTopPlayers(limit: Int = 10): List<SupabasePlayer> = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext emptyList()
        try {
            // Явная проекция публичных полей лидерборда вместо select=*.
            // Потребитель (ProfileScreen, вкладка "Глобальный рейтинг") читает:
            // deviceId, username, maxDepth, level, exp.
            val url = "$baseUrl/rest/v1/app_players?select=id,device_id,username,level,exp,biocoins,max_depth,rank,kills,state_version&order=max_depth.desc,level.desc,exp.desc&limit=$limit"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .get()
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    return@withContext json.decodeFromString<List<SupabasePlayer>>(respStr)
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "fetchTopPlayers Exception: ${e.message}")
        }
        return@withContext emptyList()
    }

    /**
     * Fetch random players for PvP (Phantom Rivals).
     */
    suspend fun fetchRandomPhantoms(limit: Int = 10, excludeDeviceId: String): List<SupabasePlayer> = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext emptyList()
        try {
            // In a real scenario we'd use a random seed, but for now we fetch top and shuffle or just fetch a decent chunk and exclude self
            // Явная проекция вместо select=*: поля, реально читаемые PvP-цепочкой
            // (PvpScreen: deviceId, pvp_proxy_until, username, level, rank, biocoins;
            // GameRepository.executePvpRaid: username, pvp_proxy_until, defense_program_1..3;
            // PvpEngine.resolveMatch: biocoins, level, installed_hardware).
            val url = "$baseUrl/rest/v1/app_players?select=device_id,username,level,exp,biocoins,rank,max_depth,defense_program_1,defense_program_2,defense_program_3,installed_hardware,pvp_proxy_until&device_id=neq.$excludeDeviceId&limit=50"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .get()
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val list = json.decodeFromString<List<SupabasePlayer>>(respStr)
                    return@withContext list.shuffled().take(limit)
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "fetchRandomPhantoms Exception: ${e.message}")
        }
        return@withContext emptyList()
    }

    /**
     * Push raid log to `app_raid_logs`.
     */
    suspend fun addRaidLog(playerId: String, logText: String): Boolean = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext false
        val validPlayerId = if (playerId.length == 36 && playerId.contains("-")) playerId else cachedPlayerUuid
        if (validPlayerId.isNullOrBlank()) {
            Log.w("SUPABASE", "addRaidLog skipped: no valid UUID for player ($playerId)")
            return@withContext false
        }
        try {
            val url = "$baseUrl/rest/v1/app_raid_logs"
            val logItem = SupabaseRaidLog(playerId = validPlayerId, logText = logText)
            val bodyJson = json.encodeToString(logItem)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", getAuthHeader())
                .addHeader("Content-Type", "application/json")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                return@withContext response.isSuccessful
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "addRaidLog Exception: ${e.message}")
        }
        return@withContext false
    }
}
