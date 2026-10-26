package io.eidos.zerolayer.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import io.eidos.zerolayer.data.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

import io.eidos.zerolayer.ui.utils.EidosAudioManager
import io.eidos.zerolayer.ui.utils.EidosNotificationManager
import io.eidos.zerolayer.ui.utils.HapticFeedbackManager
import io.eidos.zerolayer.ui.utils.EidosAlarmScheduler

class MainViewModel(
    application: Application,
    private val savedStateHandle: androidx.lifecycle.SavedStateHandle
) : AndroidViewModel(application) {
    private val database = EidosDatabase.getDatabase(application)
    private val repository = GameRepository(application, database.dao())

    // Process Death proof states for search queries and filters
    val codexSelectedCategory = savedStateHandle.getStateFlow("codex_category", "lore_story")
    val shopSearchQuery = savedStateHandle.getStateFlow("shop_search", "")
    val shopSelectedTab = savedStateHandle.getStateFlow("shop_tab", "all")

    fun setCodexSelectedCategory(category: String) {
        savedStateHandle["codex_category"] = category
    }

    fun setShopSearchQuery(query: String) {
        savedStateHandle["shop_search"] = query
    }

    fun setShopSelectedTab(tab: String) {
        savedStateHandle["shop_tab"] = tab
    }

    val haptics = HapticFeedbackManager.getInstance(application)
    val audio = EidosAudioManager.getInstance(application)
    val notifications = EidosNotificationManager.getInstance(application)
    val alarmScheduler = EidosAlarmScheduler(application)
    
    // Generate or retrieve persistent local device UUID
    val deviceUuid: String = run {
        val prefs = application.getSharedPreferences("eidos_device_prefs", android.content.Context.MODE_PRIVATE)
        var uuid = prefs.getString("device_uuid", null)
        if (uuid.isNullOrBlank()) {
            uuid = java.util.UUID.randomUUID().toString()
            prefs.edit().putString("device_uuid", uuid).commit()
        }
        uuid
    }

    private val localUid: Long = Math.abs(deviceUuid.hashCode().toLong()) + 100000L

    private val _uid = MutableStateFlow(localUid)
    val uid: StateFlow<Long> = _uid.asStateFlow()

    val player: StateFlow<Player?> = _uid.flatMapLatest { id ->
        repository.getPlayer(id)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    val inventory: StateFlow<List<InventoryItem>> = _uid.flatMapLatest { id ->
        repository.getInventory(id)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val raidSession: StateFlow<RaidSession?> = _uid.flatMapLatest { id ->
        repository.getRaidSession(id)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    val overdriveChargeFlow: StateFlow<Int> = repository.overdriveChargeFlow
    val overchargeTierFlow: StateFlow<Int> = repository.overchargeTierFlow
    val combatEventFlow: SharedFlow<CombatVisualEvent> = repository.combatEventFlow

    val logs: StateFlow<List<GameLog>> = _uid.flatMapLatest { id ->
        repository.getLogs(id)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val bestiaryList: StateFlow<List<BestiaryEntry>> = repository.getBestiaryFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _topPlayers = MutableStateFlow<List<SupabasePlayer>>(emptyList())
    val topPlayers: StateFlow<List<SupabasePlayer>> = _topPlayers.asStateFlow()

    private val _authSession = MutableStateFlow(repository.getAuthSession())
    val authSession: StateFlow<AuthSession> = _authSession.asStateFlow()

    private val _isAuthLoading = MutableStateFlow(false)
    val isAuthLoading: StateFlow<Boolean> = _isAuthLoading.asStateFlow()

    private val _authError = MutableStateFlow<String?>(null)
    val authError: StateFlow<String?> = _authError.asStateFlow()

    fun login(username: String, password: String, onSuccess: () -> Unit = {}) {
        viewModelScope.launch {
            _isAuthLoading.value = true
            _authError.value = null
            val result = repository.loginOperator(username, password)
            _isAuthLoading.value = false
            when (result) {
                is AuthResult.Success -> {
                    _authSession.value = repository.getAuthSession()
                    audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                    showToast("⚡ ДОБРО ПОЖАЛОВАТЬ, ОПЕРАТОР ${result.username}!", CyberToastType.SUCCESS)
                    onSuccess()
                }
                is AuthResult.Error -> {
                    _authError.value = result.message
                    audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                    showToast("⛔ ОШИБКА ВХОДА: ${result.message}", CyberToastType.ALERT)
                }
            }
        }
    }

    fun register(username: String, password: String, onSuccess: () -> Unit = {}) {
        viewModelScope.launch {
            _isAuthLoading.value = true
            _authError.value = null
            val result = repository.registerOperator(username, password)
            _isAuthLoading.value = false
            when (result) {
                is AuthResult.Success -> {
                    _authSession.value = repository.getAuthSession()
                    audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                    showToast("🛡 НЕЙРО-ПРОФИЛЬ «${result.username}» ЗАРЕГИСТРИРОВАН!", CyberToastType.SUCCESS)
                    onSuccess()
                }
                is AuthResult.Error -> {
                    _authError.value = result.message
                    audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                    showToast("⛔ ОШИБКА РЕГИСТРАЦИИ: ${result.message}", CyberToastType.ALERT)
                }
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            repository.logoutOperator()
            _authSession.value = repository.getAuthSession()
            audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
            showToast("🔌 ВЫХОД ИЗ НЕЙРО-ПРОФИЛЯ ВЫПОЛНЕН", CyberToastType.INFO)
        }
    }

    fun syncCloudProfile() {
        viewModelScope.launch {
            val success = repository.pushPlayerToSupabase(_uid.value)
            _authSession.value = repository.getAuthSession()
            if (success) {
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                showToast("☁️ НЕЙРО-СИНХРОНИЗАЦИЯ С SUPABASE УСПЕШНА!", CyberToastType.SUCCESS)
            } else {
                audio.playSound(EidosAudioManager.SoundType.ERROR_GLITCH)
                showToast("⚠️ НЕ УДАЛОСЬ ВЫПОЛНИТЬ ОБЛАЧНУЮ СИНХРОНИЗАЦИЮ", CyberToastType.ALERT)
            }
        }
    }

    init {
        // Schedule offline background push notifications
        alarmScheduler.scheduleDailySyncNotification()
        alarmScheduler.scheduleNetworkIntrusionNotification()

        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val defaultUsername = "Оператор ${deviceUuid.take(8).uppercase()}"
            repository.ensureDevicePlayerExists(localUid, deviceUuid, defaultUsername)
            
            // Passive Energy Regeneration (offline calculations with Anti-Time Cheat protection)
            val p = repository.getPlayerSync(localUid)
            if (p != null) {
                val validation = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.validateAndSanitizeTimestamp(application)
                val safeNow = validation.sanitizedCurrentTime
                val diffMs = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.calculateSafeOfflineDurationMs(
                    lastActiveTimestamp = p.last_active,
                    currentValidatedTimestamp = safeNow
                )
                val regenIntervalMs = 5 * 60 * 1000L // 5 minutes

                if (validation.message != null) {
                    repository.log(p.uid, validation.message, "error")
                    viewModelScope.launch(kotlinx.coroutines.Dispatchers.Main) {
                        showToast(validation.message, CyberToastType.ALERT)
                    }
                }

                if (diffMs >= regenIntervalMs && p.energy < p.max_energy) {
                    val gained = (diffMs / regenIntervalMs).toInt()
                    if (gained > 0) {
                        val newEnergy = minOf(p.max_energy, p.energy + gained)
                        val updated = p.copy(
                            energy = newEnergy,
                            last_active = safeNow - (diffMs % regenIntervalMs),
                            state_version = p.state_version + 1,
                            updated_at = safeNow
                        )
                        repository.savePlayer(updated)
                        repository.log(p.uid, "⚡ [НЕЙРО-АККУМУЛЯТОР]: В оффлайне восстановлено +$gained ед. Энергии.", "info")
                        if (newEnergy >= p.max_energy) {
                            notifications.notifyEnergyRestored()
                        }
                    }
                } else {
                    repository.savePlayer(p.copy(last_active = safeNow))
                }
            }

            repository.seedIfNeeded()
            repository.getAllItemsMetadata() // Pre-warm the lazy metadata on a background thread

            _topPlayers.value = SupabaseClientManager.fetchRandomPhantoms(10, deviceUuid)

            syncWithSupabase()
        }

        // Periodic Active Energy Regeneration (every 60 seconds with Anti-Time Cheat)
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            while (true) {
                kotlinx.coroutines.delay(60 * 1000L)
                val p = repository.getPlayerSync(_uid.value)
                if (p != null && p.energy < p.max_energy) {
                    val validation = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.validateAndSanitizeTimestamp(application)
                    val safeNow = validation.sanitizedCurrentTime
                    val diffMs = io.eidos.zerolayer.domain.anti_cheat.TimeAntiCheat.calculateSafeOfflineDurationMs(
                        lastActiveTimestamp = p.last_active,
                        currentValidatedTimestamp = safeNow
                    )
                    val regenIntervalMs = 5 * 60 * 1000L // 5 minutes
                    if (diffMs >= regenIntervalMs) {
                        val gained = (diffMs / regenIntervalMs).toInt()
                        if (gained > 0) {
                            val newEnergy = minOf(p.max_energy, p.energy + gained)
                            repository.savePlayer(p.copy(
                                energy = newEnergy,
                                last_active = safeNow - (diffMs % regenIntervalMs),
                                state_version = p.state_version + 1,
                                updated_at = safeNow
                            ))
                            repository.log(p.uid, "⚡ [НЕЙРО-АККУМУЛЯТОР]: Накоплено +$gained ед. Энергии.", "info")
                            if (newEnergy >= p.max_energy) {
                                notifications.notifyEnergyRestored()
                            }
                        }
                    }
                }
            }
        }

        // Monitor player energy transitions to schedule energy restored notification
        viewModelScope.launch {
            player.mapNotNull { it?.energy }
                .distinctUntilChanged()
                .collect { energy ->
                    if (energy <= 0) {
                        alarmScheduler.scheduleEnergyRestoredNotification()
                    }
                }
        }

        // Achievement tracker & Level Up detector
        var lastObservedLevel: Int? = null
        viewModelScope.launch {
            player.collect { p ->
                if (p != null) {
                    val prev = lastObservedLevel
                    if (prev != null && p.level > prev) {
                        val info = PlayerProgressManager.getLevelInfo(p.level)
                        _levelUpEvent.value = LevelUpEvent(
                            fromLevel = prev,
                            toLevel = p.level,
                            levelInfo = info
                        )
                        haptics.lootLegendary()
                        audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
                        notifications.notifyAchievementUnlocked("⚡ LEVEL UP: LVL ${p.level} — ${info.stageTitle}")
                    }
                    lastObservedLevel = p.level
                    checkAchievements(p)
                }
            }
        }
    }

    data class SyncConflict(val local: Player, val remote: SupabasePlayer)
    val syncConflict = MutableStateFlow<SyncConflict?>(null)

    fun resolveConflictWithRemote() {
        val conflict = syncConflict.value ?: return
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val remote = conflict.remote
            repository.savePlayer(conflict.local.copy(
                username = remote.username,
                level = remote.level,
                xp = remote.exp,
                biocoin = remote.biocoins,
                hp = remote.hp,
                energy = remote.energy,
                state_version = remote.stateVersion,
                updated_at = remote.updatedAt
            ))
            syncConflict.value = null
            repository.log(conflict.local.uid, "🔄 [СИНХРОНИЗАЦИЯ]: Прогресс восстановлен из облака (версия ${remote.stateVersion}).", "info")
        }
    }

    fun resolveConflictWithLocal() {
        val conflict = syncConflict.value ?: return
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val updatedLocal = conflict.local.copy(
                state_version = maxOf(conflict.local.state_version, conflict.remote.stateVersion) + 1,
                updated_at = System.currentTimeMillis()
            )
            repository.savePlayer(updatedLocal)
            val sp = SupabasePlayer(
                deviceId = deviceUuid,
                username = updatedLocal.username ?: "Оператор ${deviceUuid.take(8).uppercase()}",
                level = updatedLocal.level,
                exp = updatedLocal.xp,
                biocoins = updatedLocal.biocoin,
                hp = updatedLocal.hp,
                energy = updatedLocal.energy,
                rank = updatedLocal.path,
                stateVersion = updatedLocal.state_version,
                updatedAt = updatedLocal.updated_at
            )
            SupabaseClientManager.syncPlayer(sp)
            syncConflict.value = null
            repository.log(updatedLocal.uid, "🔄 [СИНХРОНИЗАЦИЯ]: Принудительно применен локальный прогресс (версия ${updatedLocal.state_version}).", "info")
        }
    }

    fun syncWithSupabase() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val localPlayer = repository.getPlayerSync(_uid.value) ?: return@launch

            // 1. Fetch remote player from app_players
            val remotePlayer = SupabaseClientManager.fetchPlayerByDeviceId(deviceUuid)
            if (remotePlayer != null) {
                if (remotePlayer.stateVersion > localPlayer.state_version) {
                    // Conflict: Remote has a newer version
                    syncConflict.value = SyncConflict(localPlayer, remotePlayer)
                    repository.log(localPlayer.uid, "⚠ Обнаружен конфликт синхронизации! Облачное сохранение (версия ${remotePlayer.stateVersion}) новее локального (версия ${localPlayer.state_version}).", "error")
                    return@launch
                } else if (localPlayer.state_version > remotePlayer.stateVersion) {
                    // Local is newer: Push local changes to Supabase
                    val sp = SupabasePlayer(
                        deviceId = deviceUuid,
                        username = localPlayer.username ?: "Оператор ${deviceUuid.take(8).uppercase()}",
                        level = localPlayer.level,
                        exp = localPlayer.xp,
                        biocoins = localPlayer.biocoin,
                        hp = localPlayer.hp,
                        energy = localPlayer.energy,
                        rank = localPlayer.path,
                        stateVersion = localPlayer.state_version,
                        updatedAt = localPlayer.updated_at
                    )
                    SupabaseClientManager.syncPlayer(sp)
                } else {
                    // Equal: keep synced
                    repository.savePlayer(localPlayer.copy(
                        username = remotePlayer.username,
                        level = remotePlayer.level,
                        xp = remotePlayer.exp,
                        biocoin = remotePlayer.biocoins,
                        hp = remotePlayer.hp,
                        energy = remotePlayer.energy
                    ))
                }
            } else {
                // Upsert local player to Supabase app_players
                val sp = SupabasePlayer(
                    deviceId = deviceUuid,
                    username = localPlayer.username ?: "Оператор ${deviceUuid.take(8).uppercase()}",
                    level = localPlayer.level,
                    exp = localPlayer.xp,
                    biocoins = localPlayer.biocoin,
                    hp = localPlayer.hp,
                    energy = localPlayer.energy,
                    rank = localPlayer.path,
                    stateVersion = localPlayer.state_version,
                    updatedAt = localPlayer.updated_at
                )
                SupabaseClientManager.syncPlayer(sp)
            }

            // 2. Sync inventory
            val currentInv = repository.getInventory(_uid.value).first()
            val supabaseInvList = currentInv.map { item ->
                SupabaseInventoryItem(
                    playerId = deviceUuid,
                    itemId = item.item_id,
                    quantity = item.quantity,
                    isEquipped = item.is_equipped
                )
            }
            SupabaseClientManager.syncInventory(deviceUuid, supabaseInvList)
        }
    }

    fun startRaid() {
        haptics.step()
        audio.playSound(EidosAudioManager.SoundType.RAID_STEP)
        viewModelScope.launch {
            repository.startRaid(_uid.value, player.value?.max_depth ?: 0)
        }
    }

    fun nextStep() {
        haptics.step()
        audio.playSound(EidosAudioManager.SoundType.RAID_STEP)
        viewModelScope.launch {
            repository.processStep(_uid.value)
        }
    }

    fun endRaid() {
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
        viewModelScope.launch {
            repository.endRaid(_uid.value)
        }
    }

    fun scanSector() {
        haptics.glitchPulse()
        audio.playSound(EidosAudioManager.SoundType.GLITCH_FOUND)
        viewModelScope.launch {
            repository.scanSector(_uid.value)
        }
    }

    fun useActiveAbility() {
        haptics.criticalHit()
        audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
        viewModelScope.launch {
            repository.useActiveAbility(_uid.value)
        }
    }

    fun triggerOverdrive() {
        haptics.criticalHit()
        audio.playSound(EidosAudioManager.SoundType.CRITICAL_STRIKE)
        viewModelScope.launch {
            repository.triggerOverdrive(_uid.value)
        }
    }

    fun boostOvercharge() {
        haptics.glitchPulse()
        audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
        viewModelScope.launch {
            repository.boostOvercharge(_uid.value)
        }
    }

    fun mergeItems(itemId: String) {
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        viewModelScope.launch {
            repository.mergeItems(_uid.value, itemId)
        }
    }

    fun dismantle(item: InventoryItem) {
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
        viewModelScope.launch {
            repository.dismantleItem(_uid.value, item)
        }
    }

    fun craft(targetId: String) {
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        viewModelScope.launch {
            repository.craftItem(_uid.value, targetId)
        }
    }

    
    fun buyShadowBrokerItem(itemId: String, useBioCoins: Boolean = false) {
        viewModelScope.launch {
            repository.buyShadowBrokerItem(_uid.value, itemId, useBioCoins)
        }
    }

    fun gambleHP() {
        viewModelScope.launch { repository.gambleHP(_uid.value) }
    }

    fun gambleLoot() {
        viewModelScope.launch { repository.gambleLoot(_uid.value) }
    }

    fun acceptMaxwellContract(contractId: String) {
        viewModelScope.launch { repository.acceptMaxwellContract(_uid.value, contractId) }
    }

    fun betMaxwellDemonHp() {
        viewModelScope.launch { repository.betMaxwellDemonHp(_uid.value) }
    }

    fun betMaxwellDemonBuffer() {
        viewModelScope.launch { repository.betMaxwellDemonBuffer(_uid.value) }
    }

    fun ignoreMaxwellDemon() {
        viewModelScope.launch { repository.ignoreMaxwellDemon(_uid.value) }
    }

    fun checkAndGenerateRadioMessages() {
        viewModelScope.launch { repository.checkAndGenerateRadioMessages(_uid.value) }
    }

    fun claimRadioMessageReward(messageId: Long) {
        viewModelScope.launch { repository.claimRadioMessageReward(_uid.value, messageId) }
    }

    val radioMessages = _uid.flatMapLatest { uid ->
        repository.getRadioMessagesFlow(uid)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val unclaimedRadioMessagesCount = _uid.flatMapLatest { uid ->
        repository.getUnclaimedRadioMessagesCountFlow(uid)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0)

    fun resolveHardGlitch(chosenIndex: Int, correctIndex: Int) {
        viewModelScope.launch { repository.resolveHardGlitch(_uid.value, chosenIndex, correctIndex) }
    }

    fun pvpWin() {
        viewModelScope.launch { repository.onPvpWin(_uid.value) }
    }

    fun pvpLose() {
        viewModelScope.launch { repository.onPvpLose(_uid.value) }
    }

    fun buyItem(itemId: String) {
        viewModelScope.launch {
            repository.buyItem(_uid.value, itemId)
            trackPurchase()
        }
    }

    suspend fun exportData(): String {
        return repository.exportProfile(_uid.value)
    }

    fun importData(jsonData: String) {
        viewModelScope.launch {
            repository.importProfile(_uid.value, jsonData)
        }
    }

    fun handleAnomaly(optionId: String) {
        viewModelScope.launch {
            repository.handleAnomalyChoice(_uid.value, optionId)
        }
    }

    fun getAnomalyData(id: String?) = id?.let { repository.getAnomaly(it) }
    fun getAllItemsMetadata() = repository.getAllItemsMetadata()

    fun equip(item: InventoryItem) {
        viewModelScope.launch {
            repository.equipItem(_uid.value, item)
        }
    }

    fun unequip(item: InventoryItem) {
        viewModelScope.launch {
            repository.unequipItem(_uid.value, item)
        }
    }

    fun useConsumable(item: InventoryItem) {
        viewModelScope.launch {
            repository.useConsumable(_uid.value, item)
        }
    }

    fun startDecryption(item: InventoryItem) {
        viewModelScope.launch {
            repository.startDecryption(_uid.value, item)
        }
    }

    fun instantDecrypt(item: InventoryItem) {
        viewModelScope.launch {
            repository.instantDecrypt(_uid.value, item)
        }
    }

    fun claimDecryptedCache(item: InventoryItem) {
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        notifications.notifyDecryptionFinished(item.item_id)
        viewModelScope.launch {
            val rewards = repository.claimDecryptedCache(_uid.value, item)
            if (rewards != null && rewards.isNotEmpty()) {
                showLoot(rewards, "ВЗЛОМАННЫЙ КЭШ")
            }
        }
    }

    fun repairBC(item: InventoryItem) {
        viewModelScope.launch {
            repository.repairEquipmentWithFee(_uid.value, item)
        }
    }

    fun repairShards(item: InventoryItem) {
        viewModelScope.launch {
            repository.repairItemShards(_uid.value, item)
        }
    }

    fun endRaidWithSafeExtraction() {
        viewModelScope.launch {
            val result = repository.endRaidWithSafeExtraction(_uid.value)
            if (result != null) {
                val (items, coins, leveledUp) = result
                if (items.isNotEmpty()) {
                    showLoot(items, "ЭВАКУАЦИЯ: ТРОФЕИ")
                }
                if (leveledUp) {
                    showAchievement("НОВЫЙ ГОРИЗОНТ", "Ваше Ядро эволюционировало. Вы стали сильнее.", xp = 500, coins = 1000)
                }
                showToast("📡 ЭВАКУАЦИЯ ЗАВЕРШЕНА: +$coins BC", CyberToastType.SUCCESS)
            }
        }
    }

    fun rerollChipModifiers(item: InventoryItem) {
        viewModelScope.launch {
            repository.rerollChipModifiers(_uid.value, item)
        }
    }

    fun applyDataSlicer(item: InventoryItem) {
        viewModelScope.launch {
            repository.applyDataSlicer(_uid.value, item)
        }
    }

    fun applyQuantumTuner(item: InventoryItem) {
        viewModelScope.launch {
            repository.applyQuantumTuner(_uid.value, item)
        }
    }

    fun applySocketPuncher(item: InventoryItem) {
        viewModelScope.launch {
            repository.applySocketPuncher(_uid.value, item)
        }
    }

    fun applyChromaticInjector(item: InventoryItem) {
        viewModelScope.launch {
            repository.applyChromaticInjector(_uid.value, item)
        }
    }

    fun applyVaalCorruption(item: InventoryItem) {
        viewModelScope.launch {
            repository.applyVaalCorruption(_uid.value, item)
        }
    }

    fun insertChipToEquipment(item: InventoryItem, socketIndex: Int, chip: io.eidos.zerolayer.data.DataChip) {
        viewModelScope.launch {
            repository.insertChipToEquipment(_uid.value, item, socketIndex, chip)
        }
    }

    fun removeChipFromEquipment(item: InventoryItem, socketIndex: Int) {
        viewModelScope.launch {
            repository.removeChipFromEquipment(_uid.value, item, socketIndex)
        }
    }

    fun rechargeEnergy() {
        viewModelScope.launch {
            repository.rechargeEnergy(_uid.value)
        }
    }

    fun claimDailySupplyDrop() {
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        notifications.notifySupplyDropReady()
        viewModelScope.launch {
            val rewards = repository.claimDailySupplyDrop(_uid.value)
            if (rewards != null) {
                showLoot(rewards, "СУТОЧНЫЕ ПРИПАСЫ")
                showToast("📦 ГРУЗ ПОЛУЧЕН", CyberToastType.SUCCESS)
                trackSyncron()
            }
        }
    }

    fun claimDailyStreak() {
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        viewModelScope.launch {
            repository.claimDailyStreak(_uid.value)
            showToast("🎁 СЕТЕВАЯ СИНХРОНИЗАЦИЯ ПОДТВЕРЖДЕНА!", CyberToastType.SUCCESS)
            trackSyncron()
        }
    }

    fun joinFaction(factionName: String) {
        viewModelScope.launch {
            repository.joinFaction(_uid.value, factionName)
        }
    }

    fun recycleItem(item: InventoryItem) {
        viewModelScope.launch {
            repository.recycleItem(_uid.value, item)
        }
    }

    fun pvpDuelAgainstOpponent(opponentName: String, opponentLevel: Int, opponentAtk: Int, opponentDef: Int) {
        viewModelScope.launch {
            repository.pvpDuelAgainstOpponent(_uid.value, opponentName, opponentLevel, opponentAtk, opponentDef)
        }
    }

    // --- GACHA / LOOTBOX ACTIONS ---
    fun buyGachaRoll(onResult: (GachaRollResult?) -> Unit = {}) {
        haptics.click()
        viewModelScope.launch {
            val res = repository.buyGachaRoll(_uid.value)
            if (res != null) {
                audio.playSound(if (res.rarity == GachaRarity.CURSED || res.rarity == GachaRarity.LEGENDARY) EidosAudioManager.SoundType.BOSS_VICTORY else EidosAudioManager.SoundType.ITEM_LOOT)
                showLoot(listOf(InventoryItem(uid = _uid.value, item_id = res.item.id, quantity = 1, durability = 100f)), "КОНТЕЙНЕР БЕЗДНЫ (${res.rarity.name})")
                trackPurchase()
            }
            onResult(res)
        }
    }

    fun synthesizeFragments(onResult: (GameRepository.ItemMetadata?) -> Unit = {}) {
        haptics.click()
        viewModelScope.launch {
            val res = repository.synthesizeFragments(_uid.value)
            if (res != null) {
                audio.playSound(EidosAudioManager.SoundType.BOSS_VICTORY)
                showLoot(listOf(InventoryItem(uid = _uid.value, item_id = res.id, quantity = 1, durability = 100f)), "СИНТЕЗ ФРАГМЕНТОВ ДАННЫХ")
            }
            onResult(res)
        }
    }

    // --- PVP 2.0 ACTIONS ---
    fun setupPvpDefense(p1: PvpProgram, p2: PvpProgram, p3: PvpProgram) {
        haptics.click()
        viewModelScope.launch {
            repository.setupPvpDefense(_uid.value, p1, p2, p3)
            showToast("🛡 Защитная матрица обновлена", CyberToastType.SUCCESS)
        }
    }

    fun buyPvpHardware(hardware: HardwareType) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.buyPvpHardware(_uid.value, hardware)
            if (success) {
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                showToast("💾 Модуль ${hardware.label} установлен!", CyberToastType.SUCCESS)
                trackPurchase()
            }
        }
    }

    fun activatePvpShield(hours: Int = 12) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.activatePvpShield(_uid.value, hours)
            if (success) {
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                showToast("🛡 Кибер-щит активирован на $hours ч!", CyberToastType.SUCCESS)
            }
        }
    }

    fun activatePvpProxy(hours: Int = 24) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.activatePvpProxy(_uid.value, hours)
            if (success) {
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                showToast("🕶 Прокси-цепь включена на $hours ч!", CyberToastType.SUCCESS)
            }
        }
    }

    fun executePvpRaid(
        target: SupabasePlayer,
        programs: List<PvpProgram>,
        isRevenge: Boolean = false,
        onResult: (PvpMatchResult) -> Unit
    ) {
        haptics.heavy()
        viewModelScope.launch {
            try {
                val res = repository.executePvpRaid(_uid.value, target, programs, isRevenge)
                if (res.isWin) {
                    audio.playSound(EidosAudioManager.SoundType.BOSS_VICTORY)
                    showToast("🏆 Взлом успешен! Похищено ${res.stolenCoins} BC", CyberToastType.SUCCESS)
                } else {
                    audio.playSound(EidosAudioManager.SoundType.DAMAGE_TAKEN)
                    showToast("☠️ Взлом отражен льдом цели! Контрудар -${res.coinsLost} BC", CyberToastType.DANGER)
                }
                onResult(res)
            } catch (e: Exception) {
                showToast("Ошибка сетевого рейда: ${e.message}", CyberToastType.DANGER)
            }
        }
    }

    // --- SYNDICATE & REFERRALS ---
    fun redeemReferralCode(code: String) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.redeemReferralCode(_uid.value, code)
            if (success) {
                audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
                showToast("🤝 Реферальный код применен (+300 XP, +200 BC)", CyberToastType.SUCCESS)
                trackReferral()
            }
        }
    }

    fun sendSignalToOperator(targetUid: Long, targetName: String) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.sendSignalToOperator(_uid.value, targetUid, targetName)
            if (success) {
                showToast("📡 Сигнал отправлен $targetName (+10 XP)", CyberToastType.INFO)
                trackMessageSent()
            }
        }
    }

    fun sendSignalToOperator(target: String, message: String) {
        haptics.click()
        viewModelScope.launch {
            val success = repository.sendSignalToOperator(_uid.value, target, message)
            if (success) {
                showToast("📡 Сигнал отправлен $target (+10 XP)", CyberToastType.INFO)
                trackMessageSent()
            }
        }
    }

    fun restoreSignal() {
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        notifications.notifySignalRestored()
        viewModelScope.launch {
            repository.restoreSignal(_uid.value)
            showToast("💚 ВОССТАНОВЛЕНИЕ СИГНАЛА ЗАПУЩЕНО", CyberToastType.INFO)
        }
    }

    fun syncProtocol() {
        viewModelScope.launch {
            repository.syncProtocol(_uid.value)
            showToast("🧬 НЕЙРО-СИНХРОНИЗАЦИЯ ЗАПУЩЕНА", CyberToastType.INFO)
        }
    }

    fun buyPremium() {
        viewModelScope.launch {
            repository.buyPremium(_uid.value)
        }
    }

    fun buyMetaUpgrade(upgradeId: String) {
        viewModelScope.launch {
            repository.buyMetaUpgrade(_uid.value, upgradeId)
        }
    }

    fun upgradeSkill(branch: String, index: Int) {
        viewModelScope.launch {
            repository.upgradeSkill(_uid.value, branch, index)
        }
    }

    fun respecSkills() {
        viewModelScope.launch {
            repository.respecSkills(_uid.value)
        }
    }

    fun hitWorldBoss() {
        viewModelScope.launch {
            repository.hitWorldBoss(_uid.value)
        }
    }

    fun updateProfile(nickname: String, faction: String) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            try {
                val p = repository.getPlayerSync(_uid.value) ?: Player(uid = _uid.value, username = nickname, first_name = nickname)

                val startingBiocoin = when (faction) {
                    "МАТЕРИЯ" -> 1000L
                    "РАЗУМ" -> 500L
                    "ТЕХНО" -> 400L
                    else -> 2000L
                }

                val (startingAtk, startingDef, startingLuck) = when (faction) {
                    "МАТЕРИЯ" -> Triple(10, 5, 15)
                    "РАЗУМ" -> Triple(10, 15, 5)
                    "ТЕХНО" -> Triple(15, 5, 10)
                    else -> Triple(25, 25, 25)
                }

                repository.savePlayer(p.copy(
                    username = nickname,
                    first_name = nickname,
                    faction = faction,
                    biocoin = startingBiocoin,
                    attack = startingAtk,
                    defense = startingDef,
                    luck = startingLuck,
                    energy = 100,
                    max_energy = 100,
                    hp = 100,
                    max_hp = 100
                ))

                // Clear current inventory first to prevent duplication
                val dao = database.dao()
                dao.clearInventory(_uid.value)

                // Insert starter kit items depending on selected faction
                when (faction) {
                    "МАТЕРИЯ" -> {
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "rusty_knife", quantity = 1, durability = 100f, is_equipped = true, slot = "weapon"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "hoodie", quantity = 1, durability = 100f, is_equipped = true, slot = "armor"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "battery", quantity = 3))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "master_key", quantity = 2))
                    }
                    "РАЗУМ" -> {
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "crowbar", quantity = 1, durability = 100f, is_equipped = true, slot = "weapon"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "leather_jacket", quantity = 1, durability = 100f, is_equipped = true, slot = "armor"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "medkit", quantity = 3))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "energy_cell", quantity = 2))
                    }
                    "ТЕХНО" -> {
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "shock_baton", quantity = 1, durability = 100f, is_equipped = true, slot = "weapon"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "nomad_goggles", quantity = 1, durability = 100f, is_equipped = true, slot = "head"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "master_key", quantity = 4))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "battery", quantity = 2))
                    }
                    else -> { // АРХИТЕКТОРЫ
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "cyber_katana", quantity = 1, durability = 100f, is_equipped = true, slot = "weapon"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "kevlar_vest", quantity = 1, durability = 100f, is_equipped = true, slot = "armor"))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "neural_stimulator", quantity = 2))
                        dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "abyssal_key", quantity = 2))
                    }
                }

                repository.log(_uid.value, "Neural link established. Operator nickname is now: $nickname. Selected faction: $faction.", "info")
                repository.log(_uid.value, "🎁 [СИСТЕМА]: Стартовый набор начислен и автоматически экипирован!", "loot")

                syncWithSupabase()
            } catch (e: Throwable) {
                android.util.Log.e("EIDOS", "Error in updateProfile", e)
            }
        }
    }

    fun grantAdminResources() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val p = repository.getPlayerSync(_uid.value) ?: return@launch
            val dao = database.dao()
            repository.savePlayer(p.copy(
                biocoin = p.biocoin + 100000L,
                xp = p.xp + 10000L,
                hp = p.max_hp,
                energy = p.max_energy
            ))
            val inv = repository.getInventory(_uid.value).first()
            val shardItem = inv.find { it.item_id == "eidos_shard" }
            if (shardItem != null) {
                dao.updateInventoryItem(shardItem.copy(quantity = shardItem.quantity + 1000))
            } else {
                dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "eidos_shard", quantity = 1000))
            }
            haptics.lootLegendary()
            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
            repository.log(_uid.value, "👑 [ADMIN]: Выданы супер-ресурсы: +100,000 BC, +10,000 XP, +1,000 Shards, восстановить HP/Энергию!", "loot")
            syncWithSupabase()
        }
    }

    fun grantGodKit() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val dao = database.dao()
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "cyber_katana", quantity = 1, durability = 100f, is_equipped = false))
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "kevlar_vest", quantity = 1, durability = 100f, is_equipped = false))
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "neural_stimulator", quantity = 10))
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "abyssal_key", quantity = 10))
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "glitch_chip", quantity = 5))
            dao.insertInventoryItem(InventoryItem(uid = _uid.value, item_id = "eidos_cache", quantity = 5))
            haptics.lootLegendary()
            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
            repository.log(_uid.value, "👑 [ADMIN]: Выдан комплект снаряжения GOD KIT!", "loot")
            syncWithSupabase()
        }
    }

    fun applyCustomEquipmentMod(item: InventoryItem, updatedEq: io.eidos.zerolayer.data.CyberEquipment, costBc: Long, logMessage: String) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val p = repository.getPlayerSync(_uid.value) ?: return@launch
            if (p.biocoin < costBc) {
                repository.log(_uid.value, "❌ [ВЕРСТАК]: Недостаточно BioCoins для завершения операции.", "error")
                return@launch
            }
            val serialized = io.eidos.zerolayer.data.PoECraftEngine.serializeEquipment(updatedEq)
            repository.savePlayer(p.copy(biocoin = p.biocoin - costBc))
            database.dao().updateInventoryItem(item.copy(custom_data = serialized))
            repository.log(_uid.value, logMessage, "loot")
            haptics.click()
            audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
            syncWithSupabase()
        }
    }

    fun toggleAdminMode(enabled: Boolean) {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val p = repository.getPlayerSync(_uid.value) ?: return@launch
            repository.savePlayer(p.copy(is_admin = enabled))
            if (enabled) {
                haptics.lootLegendary()
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
                repository.log(_uid.value, "👑 [ADMIN]: Режим Разработчика / God Mode ВКЛЮЧЕН", "loot")
            } else {
                haptics.click()
                repository.log(_uid.value, "👑 [ADMIN]: Режим Разработчика ВЫКЛЮЧЕН", "info")
            }
        }
    }

    fun resetTutorial() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val p = repository.getPlayerSync(_uid.value) ?: Player(uid = _uid.value, username = "ГОСТЬ", first_name = "Гость")
            repository.savePlayer(p.copy(faction = "NONE", username = "ГОСТЬ", first_name = "Гость"))
        }
    }

    val achievementStorage = AchievementStorage(application)

    private val _achievements = MutableStateFlow<List<Achievement>>(emptyList())
    val achievements: StateFlow<List<Achievement>> = _achievements.asStateFlow()

    private val _levelUpEvent = MutableStateFlow<LevelUpEvent?>(null)
    val levelUpEvent: StateFlow<LevelUpEvent?> = _levelUpEvent.asStateFlow()

    private val _activeLoot = MutableStateFlow<LootDrop?>(null)
    val activeLoot: StateFlow<LootDrop?> = _activeLoot.asStateFlow()

    private val _toasts = MutableStateFlow<List<CyberToast>>(emptyList())
    val toasts: StateFlow<List<CyberToast>> = _toasts.asStateFlow()

    fun checkAchievements(p: Player) {
        achievementStorage.checkNightLogin()
        val stats = achievementStorage.getStats()

        AchievementRegistry.ALL_DEFINITIONS.forEach { def ->
            if (!achievementStorage.isUnlocked(def.id) && def.isMet(p, stats)) {
                achievementStorage.markUnlocked(def.id)
                notifications.notifyAchievementUnlocked(def.title)
                
                val ach = Achievement(
                    title = def.title,
                    description = def.description,
                    xpReward = def.xpReward,
                    coinReward = 0,
                    icon = def.icon,
                    category = def.category,
                    achievementKey = def.id
                )
                _achievements.value = _achievements.value + ach
                haptics.lootLegendary()
                audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
            }
        }
    }

    fun claimAchievement(achievement: Achievement) {
        val key = achievement.achievementKey.ifBlank { achievement.title }
        achievementStorage.markClaimed(key)
        
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val currentP = repository.getPlayerSync(_uid.value)
            if (currentP != null) {
                val newXp = currentP.xp + achievement.xpReward
                val (updatedP, didLevelUp) = currentP.copy(xp = newXp).checkAndApplyLevelUp()
                repository.savePlayer(updatedP)
                if (didLevelUp) {
                    repository.handleLevelUpRewards(_uid.value, currentP.level, updatedP.level)
                    showToast("🎉 УРОВЕНЬ ПОВЫШЕН: ${updatedP.level}!", CyberToastType.SUCCESS)
                }
            }
        }
        
        showToast("⚡️ Награда получена: +${achievement.xpReward} XP за «${achievement.title}»!", CyberToastType.SUCCESS)
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        dismissAchievement(achievement.id)
    }

    fun trackClick() {
        achievementStorage.incrementClicks()
        player.value?.let { checkAchievements(it) }
    }

    fun trackSyncron() {
        achievementStorage.incrementSyncrons()
        player.value?.let { checkAchievements(it) }
    }

    fun trackQuizWon() {
        achievementStorage.incrementQuizzesWon()
        player.value?.let { checkAchievements(it) }
    }

    fun trackPurchase() {
        achievementStorage.incrementPurchases()
        player.value?.let { checkAchievements(it) }
    }

    fun trackMessageSent() {
        achievementStorage.incrementMessages()
        player.value?.let { checkAchievements(it) }
    }

    fun trackLike(amount: Int = 1) {
        achievementStorage.incrementLikes(amount)
        player.value?.let { checkAchievements(it) }
    }

    fun trackReferral() {
        val curr = achievementStorage.getStats().referrals
        achievementStorage.setReferrals(curr + 1)
        player.value?.let { checkAchievements(it) }
    }

    fun trackZeroLayer() {
        achievementStorage.setZeroLayerEntered()
        player.value?.let { checkAchievements(it) }
    }

    fun trackGlitch() {
        achievementStorage.setGlitchTriggered()
        player.value?.let { checkAchievements(it) }
    }

    fun trackCreatorGaze() {
        achievementStorage.setCreatorGazeFound()
        player.value?.let { checkAchievements(it) }
    }

    fun getProfileAchievements(p: Player?): List<AchievementItem> {
        val playerObj = p ?: Player(uid = 0, username = null, first_name = null)
        val stats = achievementStorage.getStats()
        return AchievementRegistry.ALL_DEFINITIONS.map { def ->
            val isUnlocked = achievementStorage.isUnlocked(def.id) || def.isMet(playerObj, stats)
            val isClaimed = achievementStorage.isClaimed(def.id)
            val curr = def.getProgress(playerObj, stats)
            AchievementItem(
                id = def.id,
                category = def.category,
                icon = def.icon,
                title = def.title,
                description = def.description,
                xpReward = def.xpReward,
                coinReward = 0,
                target = def.target,
                current = curr,
                isUnlocked = isUnlocked,
                isClaimed = isClaimed
            )
        }
    }

    fun showAchievement(title: String, description: String, xp: Long = 0, coins: Long = 0) {
        val achievement = Achievement(title, description, xp, coins)
        _achievements.value = _achievements.value + achievement
        haptics.lootLegendary()
        audio.playSound(EidosAudioManager.SoundType.HACK_SUCCESS)
        notifications.notifyAchievementUnlocked(title)
    }

    fun dismissAchievement(id: String) {
        _achievements.value = _achievements.value.filter { it.id != id }
    }

    fun showLoot(items: List<InventoryItem>, source: String = "СИСТЕМНЫЙ КЭШ") {
        _activeLoot.value = LootDrop(items, source)
        haptics.criticalHit()
    }

    fun dismissLoot() {
        _activeLoot.value = null
        haptics.click()
        audio.playSound(EidosAudioManager.SoundType.CLICK_CYBER)
    }

    fun showToast(message: String, type: CyberToastType = CyberToastType.INFO) {
        val toast = CyberToast(message, type)
        _toasts.value = _toasts.value + toast
        viewModelScope.launch {
            kotlinx.coroutines.delay(3000)
            _toasts.value = _toasts.value.filter { it.id != toast.id }
        }
    }

    fun dismissLevelUp() {
        _levelUpEvent.value = null
    }

    fun triggerTestLevelUp() {
        viewModelScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val currentP = repository.getPlayerSync(_uid.value)
            val currentLvl = currentP?.level ?: 1
            val targetLevel = if (currentLvl >= 31) 1 else currentLvl + 1
            val targetXp = PlayerProgressManager.getLevelInfo(targetLevel).requiredXp
            if (currentP != null) {
                val updated = currentP.copy(xp = targetXp, level = targetLevel)
                repository.savePlayer(updated)
            }
            _levelUpEvent.value = LevelUpEvent(
                fromLevel = currentLvl,
                toLevel = targetLevel,
                levelInfo = PlayerProgressManager.getLevelInfo(targetLevel)
            )
            haptics.lootLegendary()
            audio.playSound(EidosAudioManager.SoundType.LEVEL_UP)
        }
    }
}
