package io.eidos.zerolayer.data

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

data class AuthSession(
    val isLoggedIn: Boolean,
    val isAnonymous: Boolean = false,
    val username: String?,
    val userId: String?,
    val accessToken: String?,
    val refreshToken: String?,
    val lastSyncTimestamp: Long
)

class EidosAuthStore private constructor(context: Context) {

    private val isSecureStorage: Boolean
    private val prefs: SharedPreferences

    // In-memory token cache used when encrypted storage is unavailable.
    // Tokens are never written to plaintext prefs; they are lost on restart by design.
    @Volatile
    private var memoryAccessToken: String? = null

    @Volatile
    private var memoryRefreshToken: String? = null

    init {
        var secure = false
        prefs = try {
            val masterKey = MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()
            EncryptedSharedPreferences.create(
                context,
                PREFS_NAME,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            ).also { secure = true }
        } catch (e: Exception) {
            Log.e("EidosAuthStore", "Failed to initialize EncryptedSharedPreferences, fallback to standard: ${e.message}")
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        }
        isSecureStorage = secure
    }

    fun getSession(): AuthSession {
        val isLoggedIn = prefs.getBoolean(KEY_IS_LOGGED_IN, false)
        val isAnonymous = prefs.getBoolean(KEY_IS_ANONYMOUS, false)
        val username = prefs.getString(KEY_USERNAME, null)
        val userId = prefs.getString(KEY_USER_ID, null)
        val accessToken: String?
        val refreshToken: String?
        if (isSecureStorage) {
            accessToken = prefs.getString(KEY_ACCESS_TOKEN, null)
            refreshToken = prefs.getString(KEY_REFRESH_TOKEN, null)
        } else {
            // Fallback: tokens only exist in memory
            accessToken = memoryAccessToken
            refreshToken = memoryRefreshToken
        }
        val lastSync = prefs.getLong(KEY_LAST_SYNC, 0L)

        return AuthSession(
            isLoggedIn = isLoggedIn && !accessToken.isNullOrBlank(),
            isAnonymous = isAnonymous,
            username = username,
            userId = userId,
            accessToken = accessToken,
            refreshToken = refreshToken,
            lastSyncTimestamp = lastSync
        )
    }

    fun saveSession(username: String, userId: String, accessToken: String, refreshToken: String?, isAnonymous: Boolean = false) {
        val editor = prefs.edit()
            .putBoolean(KEY_IS_LOGGED_IN, true)
            .putBoolean(KEY_IS_ANONYMOUS, isAnonymous)
            .putString(KEY_USERNAME, username)
            .putString(KEY_USER_ID, userId)
            .putLong(KEY_LAST_SYNC, System.currentTimeMillis())
        if (isSecureStorage) {
            editor.putString(KEY_ACCESS_TOKEN, accessToken)
                .putString(KEY_REFRESH_TOKEN, refreshToken)
        } else {
            // Fallback: keep tokens in memory only, purge any legacy plaintext ones
            memoryAccessToken = accessToken
            memoryRefreshToken = refreshToken
            editor.remove(KEY_ACCESS_TOKEN).remove(KEY_REFRESH_TOKEN)
        }
        editor.apply()
    }

    fun updateLastSync(timestamp: Long = System.currentTimeMillis()) {
        prefs.edit().putLong(KEY_LAST_SYNC, timestamp).apply()
    }

    /**
     * Store the cryptographically random guest password for the device.
     * Persisted only when encrypted storage is available, never in plaintext.
     */
    fun saveGuestPassword(deviceKey: String, password: String) {
        if (!isSecureStorage) return
        prefs.edit().putString(KEY_GUEST_PASSWORD_PREFIX + deviceKey, password).apply()
    }

    /**
     * Return the stored guest password for the device, or null when
     * no password was saved or encrypted storage is unavailable.
     */
    fun loadGuestPassword(deviceKey: String): String? {
        if (!isSecureStorage) return null
        return prefs.getString(KEY_GUEST_PASSWORD_PREFIX + deviceKey, null)
    }

    fun isInventoryInitialized(uid: Long): Boolean {
        return prefs.getBoolean("key_inventory_init_$uid", false)
    }

    fun setInventoryInitialized(uid: Long, initialized: Boolean = true) {
        prefs.edit().putBoolean("key_inventory_init_$uid", initialized).apply()
    }

    fun clearSession() {
        memoryAccessToken = null
        memoryRefreshToken = null
        prefs.edit()
            .putBoolean(KEY_IS_LOGGED_IN, false)
            .putBoolean(KEY_IS_ANONYMOUS, false)
            .remove(KEY_USERNAME)
            .remove(KEY_USER_ID)
            .remove(KEY_ACCESS_TOKEN)
            .remove(KEY_REFRESH_TOKEN)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "eidos_auth_session_encrypted_prefs"
        private const val KEY_IS_LOGGED_IN = "key_is_logged_in"
        private const val KEY_IS_ANONYMOUS = "key_is_anonymous"
        private const val KEY_USERNAME = "key_username"
        private const val KEY_USER_ID = "key_user_id"
        private const val KEY_ACCESS_TOKEN = "key_access_token"
        private const val KEY_REFRESH_TOKEN = "key_refresh_token"
        private const val KEY_LAST_SYNC = "key_last_sync"
        private const val KEY_GUEST_PASSWORD_PREFIX = "key_guest_password_"

        @Volatile
        private var INSTANCE: EidosAuthStore? = null

        fun getInstance(context: Context): EidosAuthStore {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: EidosAuthStore(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
}
