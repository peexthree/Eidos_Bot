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
    val id: Long? = null,
    @SerialName("device_id") val deviceId: String,
    val username: String,
    val level: Int = 1,
    val exp: Long = 0,
    val biocoins: Long = 0,
    val hp: Int = 100,
    val energy: Int = 100,
    val rank: String = "Новичок",
    @SerialName("max_depth") val maxDepth: Int = 0,
    @SerialName("defense_program_1") val defense_program_1: String = "SHIELD",
    @SerialName("defense_program_2") val defense_program_2: String = "BRUTEFORCE",
    @SerialName("defense_program_3") val defense_program_3: String = "STEALTH",
    @SerialName("installed_hardware") val installed_hardware: String? = null,
    @SerialName("pvp_proxy_until") val pvp_proxy_until: Long = 0L,
    @SerialName("state_version") val stateVersion: Long = 1,
    @SerialName("updated_at") val updatedAt: Long = System.currentTimeMillis()
)

@Serializable
data class SupabaseInventoryItem(
    val id: Long? = null,
    @SerialName("player_id") val playerId: String,
    @SerialName("item_id") val itemId: String,
    val quantity: Int = 1,
    @SerialName("is_equipped") val isEquipped: Boolean = false
)

@Serializable
data class SupabaseRaidLog(
    val id: Long? = null,
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

object SupabaseClientManager {
    val baseUrl: String = BuildConfig.SUPABASE_URL.trimEnd('/')
    val apiKey: String = BuildConfig.SUPABASE_ANON_KEY

    private val httpClient = OkHttpClient.Builder().build()
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    fun isConfigured(): Boolean = baseUrl.isNotBlank() && apiKey.isNotBlank()

    fun toVirtualEmail(username: String): String {
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

    /**
     * Sign in existing operator in Supabase Auth.
     */
    suspend fun signInWithCredentials(username: String, password: String): AuthResult = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext AuthResult.Error("Supabase не сконфигурирован.")
        val cleanUsername = username.trim()
        if (cleanUsername.isBlank()) return@withContext AuthResult.Error("Введите позывной.")
        if (password.isBlank()) return@withContext AuthResult.Error("Введите пароль.")

        try {
            val email = toVirtualEmail(cleanUsername)
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
                        return@withContext AuthResult.Success(
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
                    return@withContext AuthResult.Error(humanReadableError)
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE_AUTH", "signIn Exception: ${e.message}")
            return@withContext AuthResult.Error("Сетевой сбой при входе: ${e.localizedMessage ?: e.message}")
        }
        return@withContext AuthResult.Error("Не удалось выполнить вход.")
    }

    /**
     * Sign in anonymously using device ID as a guest account.
     */
    suspend fun signInAnonymously(deviceId: String): AuthResult = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext AuthResult.Error("Supabase не сконфигурирован.")
        val cleanDevice = deviceId.ifBlank { "guest_" + System.currentTimeMillis() }
        val anonUsername = "Guest_${cleanDevice.takeLast(6)}"
        val anonPassword = "EidosAnonPassword_${cleanDevice.hashCode()}"

        val signInResult = signInWithCredentials(anonUsername, anonPassword)
        if (signInResult is AuthResult.Success) {
            return@withContext signInResult
        }

        // If guest does not exist yet, register anonymously
        val signUpResult = signUpWithCredentials(anonUsername, anonPassword)
        if (signUpResult is AuthResult.Success) {
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
                .addHeader("Authorization", "Bearer $apiKey")
                .addHeader("Content-Type", "application/json")
                .addHeader("Prefer", "resolution=merge-duplicates,return=representation")
                .post(bodyJson.toRequestBody("application/json".toMediaType()))
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val list = json.decodeFromString<List<SupabasePlayer>>(respStr)
                    return@withContext list.firstOrNull() ?: supabasePlayer
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
                .addHeader("Authorization", "Bearer $apiKey")
                .get()
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val respStr = response.body?.string() ?: ""
                    val list = json.decodeFromString<List<SupabasePlayer>>(respStr)
                    return@withContext list.firstOrNull()
                }
            }
        } catch (e: Exception) {
            Log.e("SUPABASE", "fetchPlayerByDeviceId Exception: ${e.message}")
        }
        return@withContext null
    }

    /**
     * Sync inventory items to `app_inventory`.
     */
    suspend fun syncInventory(playerId: String, items: List<SupabaseInventoryItem>): Boolean = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext false
        try {
            // Delete existing for player and insert current list
            val deleteUrl = "$baseUrl/rest/v1/app_inventory?player_id=eq.$playerId"
            val deleteRequest = Request.Builder()
                .url(deleteUrl)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $apiKey")
                .delete()
                .build()
            httpClient.newCall(deleteRequest).execute().close()

            if (items.isNotEmpty()) {
                val insertUrl = "$baseUrl/rest/v1/app_inventory"
                val bodyJson = json.encodeToString(items)
                val insertRequest = Request.Builder()
                    .url(insertUrl)
                    .addHeader("apikey", apiKey)
                    .addHeader("Authorization", "Bearer $apiKey")
                    .addHeader("Content-Type", "application/json")
                    .post(bodyJson.toRequestBody("application/json".toMediaType()))
                    .build()
                httpClient.newCall(insertRequest).execute().use { resp ->
                    return@withContext resp.isSuccessful
                }
            }
            return@withContext true
        } catch (e: Exception) {
            Log.e("SUPABASE", "syncInventory Exception: ${e.message}")
        }
        return@withContext false
    }

    /**
     * Fetch leaderboard top players from `app_players`.
     */
    suspend fun fetchTopPlayers(limit: Int = 10): List<SupabasePlayer> = withContext(Dispatchers.IO) {
        if (!isConfigured()) return@withContext emptyList()
        try {
            val url = "$baseUrl/rest/v1/app_players?select=*&order=max_depth.desc,level.desc,exp.desc&limit=$limit"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $apiKey")
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
            val url = "$baseUrl/rest/v1/app_players?select=*&device_id=neq.$excludeDeviceId&limit=50"
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $apiKey")
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
        try {
            val url = "$baseUrl/rest/v1/app_raid_logs"
            val logItem = SupabaseRaidLog(playerId = playerId, logText = logText)
            val bodyJson = json.encodeToString(logItem)
            val request = Request.Builder()
                .url(url)
                .addHeader("apikey", apiKey)
                .addHeader("Authorization", "Bearer $apiKey")
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
