package io.eidos.zerolayer.data

import android.content.Context
import android.content.SharedPreferences

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

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getSession(): AuthSession {
        val isLoggedIn = prefs.getBoolean(KEY_IS_LOGGED_IN, false)
        val isAnonymous = prefs.getBoolean(KEY_IS_ANONYMOUS, false)
        val username = prefs.getString(KEY_USERNAME, null)
        val userId = prefs.getString(KEY_USER_ID, null)
        val accessToken = prefs.getString(KEY_ACCESS_TOKEN, null)
        val refreshToken = prefs.getString(KEY_REFRESH_TOKEN, null)
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
        prefs.edit()
            .putBoolean(KEY_IS_LOGGED_IN, true)
            .putBoolean(KEY_IS_ANONYMOUS, isAnonymous)
            .putString(KEY_USERNAME, username)
            .putString(KEY_USER_ID, userId)
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .putLong(KEY_LAST_SYNC, System.currentTimeMillis())
            .apply()
    }

    fun updateLastSync(timestamp: Long = System.currentTimeMillis()) {
        prefs.edit().putLong(KEY_LAST_SYNC, timestamp).apply()
    }

    fun clearSession() {
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
        private const val PREFS_NAME = "eidos_auth_session_prefs"
        private const val KEY_IS_LOGGED_IN = "key_is_logged_in"
        private const val KEY_IS_ANONYMOUS = "key_is_anonymous"
        private const val KEY_USERNAME = "key_username"
        private const val KEY_USER_ID = "key_user_id"
        private const val KEY_ACCESS_TOKEN = "key_access_token"
        private const val KEY_REFRESH_TOKEN = "key_refresh_token"
        private const val KEY_LAST_SYNC = "key_last_sync"

        @Volatile
        private var INSTANCE: EidosAuthStore? = null

        fun getInstance(context: Context): EidosAuthStore {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: EidosAuthStore(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
}
