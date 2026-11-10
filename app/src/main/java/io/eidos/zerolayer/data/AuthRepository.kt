package io.eidos.zerolayer.data

import android.content.Context
import kotlinx.coroutines.sync.Mutex

/**
 * Аутентификация и облачная синхронизация профиля оператора.
 *
 * Выделен из GameRepository (расщепление God-object). Методы перенесены
 * дословно, без изменений логики.
 *
 * Важно про мьютекс: сюда передаётся ТОТ ЖЕ экземпляр dbMutex, что и в
 * GameRepository. Kotlin Mutex нереентерабельный, поэтому AuthRepository
 * НЕ имеет ссылки на GameRepository и не должен вызывать его публичные
 * методы, берущие мьютекс. Связь с GameRepository идёт только через
 * переданные провайдеры (activeUidProvider, logProvider), которые сами
 * по себе мьютекс не захватывают.
 */
class AuthRepository(
    private val context: Context,
    // Та же обёртка над originalDao, что и в GameRepository
    // (автоинкремент state_version при insert/update/upsert Player).
    private val dao: EidosDao,
    // Тот же экземпляр Mutex, что и в GameRepository. Задел на будущее:
    // текущие методы кластера не захватывали dbMutex и в GameRepository.
    private val dbMutex: Mutex,
    val authStore: EidosAuthStore,
    activeUidProvider: () -> Long,
    logProvider: suspend (uid: Long, message: String, type: String) -> Unit
) {

    private val activeUidProvider = activeUidProvider
    private val logProvider = logProvider

    // Локальные обёртки с теми же именами, что в GameRepository, чтобы
    // тела перенесённых методов остались дословными.
    private fun getActiveUid(): Long = activeUidProvider()

    private suspend fun log(uid: Long, message: String, type: String = "info") {
        logProvider(uid, message, type)
    }

    fun getAuthSession(): AuthSession = authStore.getSession()

    fun isInventoryInitialized(uid: Long): Boolean = authStore.isInventoryInitialized(uid)
    fun setInventoryInitialized(uid: Long, initialized: Boolean = true) = authStore.setInventoryInitialized(uid, initialized)

    suspend fun registerOperator(username: String, password: String, targetUid: Long = 0L): AuthResult {
        val clean = username.trim()
        if (clean.length < 3) return AuthResult.Error("Позывной должен содержать не менее 3 символов.")
        if (password.length < 4) return AuthResult.Error("Пароль должен содержать минимум 4 символа.")

        var res = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.signUpWithCredentials(clean, password)
        } else {
            AuthResult.Error("Offline")
        }

        if (res !is AuthResult.Success) {
            // Smooth offline registration fallback
            val offlineUserId = "local_${System.currentTimeMillis()}"
            res = AuthResult.Success(
                user = AuthUser(id = offlineUserId),
                accessToken = "local_token_$offlineUserId",
                refreshToken = null,
                username = clean,
                isNewAccount = true
            )
        }

        authStore.saveSession(res.username, res.user.id, res.accessToken, res.refreshToken)
        val target = if (targetUid > 0L) targetUid else getActiveUid()
        val p = dao.getPlayer(target)
        if (p != null) {
            val updated = p.copy(username = res.username, first_name = res.username)
            dao.updatePlayer(updated)
            if (SupabaseClientManager.isConfigured()) {
                pushPlayerToSupabase(p.uid, res.user.id, res.username)
            }
        }
        log(target, "🛡 [НЕЙРО-ПРОФИЛЬ]: Оператор ${res.username} успешно зарегистрирован в Сети Эйдос!", "info")
        return res
    }

    suspend fun loginOperator(username: String, password: String, targetUid: Long = 0L): AuthResult {
        val clean = username.trim()
        if (clean.isBlank()) return AuthResult.Error("Введите позывной оператора.")
        if (password.isBlank()) return AuthResult.Error("Введите пароль.")

        var res = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.signInWithCredentials(clean, password)
        } else {
            AuthResult.Error("Offline")
        }

        // Локальная сессия ТОЛЬКО когда Supabase не настроен (оффлайн-режим).
        // Раньше любой провал (в т.ч. неверный пароль) молча подменялся успехом -
        // вход "работал" с чужим/несуществующим аккаунтом.
        if (!SupabaseClientManager.isConfigured() && res !is AuthResult.Success) {
            val offlineUserId = "local_${clean.hashCode()}"
            res = AuthResult.Success(
                user = AuthUser(id = offlineUserId),
                accessToken = "local_token_$offlineUserId",
                refreshToken = null,
                username = clean,
                isNewAccount = false
            )
        }

        // Реальная ошибка авторизации (неверный пароль, сеть) возвращается как есть
        if (res !is AuthResult.Success) return res

        authStore.saveSession(res.username, res.user.id, res.accessToken, res.refreshToken)

        // Try to restore or sync cloud player profile
        val cloudPlayer = if (SupabaseClientManager.isConfigured()) {
            SupabaseClientManager.fetchPlayerByDeviceId(res.user.id)
                ?: SupabaseClientManager.fetchPlayerByDeviceId(res.username)
        } else null

        val target = if (targetUid > 0L) targetUid else getActiveUid()
        val localPlayer = dao.getPlayer(target)
        if (cloudPlayer != null) {
            val restored = (localPlayer ?: Player(uid = target, username = res.username, first_name = res.username)).copy(
                username = cloudPlayer.username,
                first_name = cloudPlayer.username,
                level = cloudPlayer.level,
                xp = cloudPlayer.exp,
                biocoin = cloudPlayer.biocoins,
                hp = cloudPlayer.hp,
                energy = cloudPlayer.energy,
                max_depth = cloudPlayer.maxDepth,
                defense_program_1 = cloudPlayer.defense_program_1,
                defense_program_2 = cloudPlayer.defense_program_2,
                defense_program_3 = cloudPlayer.defense_program_3,
                updated_at = System.currentTimeMillis()
            )
            if (localPlayer != null) {
                dao.updatePlayer(restored)
            } else {
                dao.insertPlayer(restored)
            }
            log(target, "☁️ [НЕЙРО-СИНХРОНИЗАЦИЯ]: Профиль оператора ${cloudPlayer.username} (Уровень ${cloudPlayer.level}) загружен из облака!", "loot")
        } else if (localPlayer != null) {
            val updated = localPlayer.copy(username = res.username, first_name = res.username)
            dao.updatePlayer(updated)
            if (SupabaseClientManager.isConfigured()) {
                pushPlayerToSupabase(localPlayer.uid, res.user.id, res.username)
            }
            log(target, "🔓 [СЕТЕВОЙ ВХОД]: Нейро-сессия активирована. Профиль «${res.username}» готов к вылазкам.", "info")
        }
        return res
    }

    suspend fun logoutOperator(): Boolean {
        val session = authStore.getSession()
        if (!session.accessToken.isNullOrBlank()) {
            SupabaseClientManager.logoutSession(session.accessToken)
        }
        authStore.clearSession()
        log(getActiveUid(), "🔌 [ОТКЛЮЧЕНИЕ]: Выход из нейро-профиля выполнен. Переход в автономный режим.", "info")
        return true
    }

    suspend fun pushPlayerToSupabase(uid: Long, customDeviceId: String? = null, customUsername: String? = null): Boolean {
        val p = dao.getPlayer(uid) ?: return false
        val session = authStore.getSession()
        val deviceId = customDeviceId ?: session.userId ?: (android.provider.Settings.Secure.getString(context.contentResolver, android.provider.Settings.Secure.ANDROID_ID) ?: "device_$uid")
        val username = customUsername ?: session.username ?: p.username ?: "Operator_$uid"

        val sp = SupabasePlayer(
            deviceId = deviceId,
            username = username,
            level = p.level,
            exp = p.xp,
            biocoins = p.biocoin,
            hp = p.hp,
            energy = p.energy,
            rank = if (p.level > 10) "Элита" else "Оператор",
            maxDepth = p.max_depth,
            kills = p.kills,
            defense_program_1 = p.defense_program_1,
            defense_program_2 = p.defense_program_2,
            defense_program_3 = p.defense_program_3,
            stateVersion = p.state_version
        )
        val res = SupabaseClientManager.syncPlayer(sp)
        if (res != null) {
            val targetUuid = res.id ?: SupabaseClientManager.cachedPlayerUuid
            if (targetUuid != null) {
                val currentInv = dao.getInventorySync(uid)
                val supabaseInvList = currentInv.map {
                    SupabaseInventoryItem(
                        playerId = targetUuid,
                        itemId = it.item_id,
                        quantity = it.quantity,
                        isEquipped = it.is_equipped
                    )
                }
                SupabaseClientManager.syncInventory(targetUuid, supabaseInvList)
            }
            authStore.updateLastSync()
            return true
        }
        return false
    }
}
