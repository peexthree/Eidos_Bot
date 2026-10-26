package com.example.eidos

import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.remember
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Box
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.compose.currentBackStackEntryAsState
import com.example.eidos.ui.MainViewModel
import com.example.eidos.ui.theme.EidosTheme
import com.example.eidos.ui.screens.*
import com.example.eidos.ui.components.*
import com.example.eidos.data.*
import android.os.Build

class MainActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        try {
            val params = window.attributes
            params.preferredRefreshRate = 120f
            window.attributes = params
        } catch (_: Throwable) {}

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }

        setContent {
            EidosTheme {
                EidosApp()
            }
        }
    }

    override fun onPause() {
        super.onPause()
        com.example.eidos.ui.utils.EidosAudioManager.getInstance(this).pauseMusic()
    }

    override fun onResume() {
        super.onResume()
        com.example.eidos.ui.utils.EidosAudioManager.getInstance(this).resumeMusic()
    }

    override fun onStop() {
        super.onStop()
        com.example.eidos.ui.utils.EidosAudioManager.getInstance(this).pauseMusic()
    }

    override fun onDestroy() {
        super.onDestroy()
        com.example.eidos.ui.utils.EidosAudioManager.getInstance(this).stopMusic()
    }
}

@Composable
fun EidosApp(mainViewModel: MainViewModel = viewModel()) {
    val navController = rememberNavController()
    val player by mainViewModel.player.collectAsStateWithLifecycle()
    val raidSession by mainViewModel.raidSession.collectAsStateWithLifecycle()
    val inventory by mainViewModel.inventory.collectAsStateWithLifecycle()
    val logs by mainViewModel.logs.collectAsStateWithLifecycle()
    val radioMessages by mainViewModel.radioMessages.collectAsStateWithLifecycle()
    val unclaimedRadioMessagesCount by mainViewModel.unclaimedRadioMessagesCount.collectAsStateWithLifecycle()
    val overdriveCharge by mainViewModel.overdriveChargeFlow.collectAsStateWithLifecycle()
    val overchargeTier by mainViewModel.overchargeTierFlow.collectAsStateWithLifecycle()

    val context = androidx.compose.ui.platform.LocalContext.current
    val audioManager = remember { com.example.eidos.ui.utils.EidosAudioManager.getInstance(context) }
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current

    androidx.compose.runtime.DisposableEffect(lifecycleOwner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            when (event) {
                androidx.lifecycle.Lifecycle.Event.ON_STOP -> audioManager.pauseMusic()
                androidx.lifecycle.Lifecycle.Event.ON_START, androidx.lifecycle.Lifecycle.Event.ON_RESUME -> audioManager.resumeMusic()
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    androidx.compose.runtime.DisposableEffect(navController) {
        val listener = androidx.navigation.NavController.OnDestinationChangedListener { _, destination, _ ->
            val route = destination.route ?: ""
            if (route.contains("Splash")) {
                audioManager.stopMusic()
            } else if (route.contains("Raid")) {
                audioManager.playBgm(com.example.eidos.ui.utils.EidosAudioManager.BgmTrack.ZERO_LAYER)
            } else {
                audioManager.playBgm(com.example.eidos.ui.utils.EidosAudioManager.BgmTrack.MAIN_MENU)
            }
        }
        navController.addOnDestinationChangedListener(listener)
        onDispose { navController.removeOnDestinationChangedListener(listener) }
    }

    val syncConflict by mainViewModel.syncConflict.collectAsStateWithLifecycle()
    val achievements by mainViewModel.achievements.collectAsStateWithLifecycle()
    val levelUpEvent by mainViewModel.levelUpEvent.collectAsStateWithLifecycle()
    val activeLoot by mainViewModel.activeLoot.collectAsStateWithLifecycle()
    val toasts by mainViewModel.toasts.collectAsStateWithLifecycle()

    if (syncConflict != null) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = {},
            title = { Text("⚠ КОНФЛИКТ СИНХРОНИЗАЦИИ", color = MaterialTheme.colorScheme.error) },
            text = {
                Column {
                    Text("Обнаружено расхождение между локальной версией данных и облачным сохранением.")
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Локальная версия: ${syncConflict?.local?.state_version}")
                    Text("Облачная версия: ${syncConflict?.remote?.stateVersion}")
                }
            },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = { mainViewModel.resolveConflictWithRemote() }) {
                    Text("ВОССТАНОВИТЬ ИЗ ОБЛАКА")
                }
            },
            dismissButton = {
                androidx.compose.material3.TextButton(onClick = { mainViewModel.resolveConflictWithLocal() }) {
                    Text("ПРИМЕНИТЬ ЛОКАЛЬНЫЕ")
                }
            }
        )
    }

    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route ?: ""
    val isBottomBarVisible = currentRoute.isNotBlank() &&
        !currentRoute.contains("Splash") &&
        !currentRoute.contains("Onboarding")

    Box(modifier = Modifier.fillMaxSize()) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            bottomBar = {
                if (isBottomBarVisible) {
                    val selectedTab = when {
                        currentRoute.contains("Inventory") -> "inventory"
                        currentRoute.contains("Raid") -> "matrix"
                        currentRoute.contains("Pvp") -> "pvp"
                        currentRoute.contains("Profile") || currentRoute.contains("EidosSettings") -> "settings"
                        else -> "hub"
                    }
                    CyberHubBottomBar(
                        selectedTab = selectedTab,
                        onTabSelected = { tab ->
                            when (tab) {
                                "hub" -> {
                                    navController.navigate(Hub) {
                                        popUpTo(Hub) { saveState = true }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                                "inventory" -> {
                                    navController.navigate(Inventory) {
                                        launchSingleTop = true
                                    }
                                }
                                "matrix" -> {
                                    if (raidSession == null) mainViewModel.startRaid()
                                    navController.navigate(Raid) {
                                        launchSingleTop = true
                                    }
                                }
                                "pvp" -> {
                                    navController.navigate(Pvp) {
                                        launchSingleTop = true
                                    }
                                }
                                "settings" -> {
                                    navController.navigate(Profile) {
                                        launchSingleTop = true
                                    }
                                }
                            }
                        }
                    )
                }
            }
        ) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = Splash,
                modifier = Modifier.padding(innerPadding)
            ) {
                composable<Splash> {
                    SplashScreen(onFinish = { 
                        val dest = if (player == null || player?.faction == "NONE") Onboarding else Hub
                        navController.navigate(dest) { popUpTo(Splash) { inclusive = true } }
                    })
                }
                composable<Onboarding> {
                    var showOnboardingAuth by remember { androidx.compose.runtime.mutableStateOf(false) }
                    val isAuthLoading by mainViewModel.isAuthLoading.collectAsStateWithLifecycle()
                    val authError by mainViewModel.authError.collectAsStateWithLifecycle()

                    if (showOnboardingAuth) {
                        ZzzAuthDialog(
                            initialMode = AuthDialogMode.LOGIN,
                            isLoading = isAuthLoading,
                            errorMessage = authError,
                            onDismiss = { showOnboardingAuth = false },
                            onLogin = { u, p ->
                                mainViewModel.login(u, p, onSuccess = {
                                    showOnboardingAuth = false
                                    navController.navigate(Hub) { popUpTo(Onboarding) { inclusive = true } }
                                })
                            },
                            onRegister = { u, p ->
                                mainViewModel.register(u, p, onSuccess = {
                                    showOnboardingAuth = false
                                })
                            }
                        )
                    }

                    OnboardingScreen(
                        onComplete = { nickname, faction ->
                            mainViewModel.updateProfile(nickname, faction)
                            navController.navigate(Hub) { popUpTo(Onboarding) { inclusive = true } }
                        },
                        onLoginClick = { showOnboardingAuth = true }
                    )
                }
                composable<Hub> {
                    HubScreen(
                        player = player,
                        onClaimSupplyDrop = { mainViewModel.claimDailySupplyDrop() },
                        onAttackWorldBoss = { mainViewModel.hitWorldBoss() },
                        logs = logs,
                        onRestoreSignal = { mainViewModel.restoreSignal() },
                        onSyncProtocol = { mainViewModel.syncProtocol() },
                        onNavigateToInventory = { navController.navigate(Inventory) },
                        onNavigateToRaid = { 
                            if (raidSession == null) mainViewModel.startRaid()
                            navController.navigate(Raid) 
                        },
                        onNavigateToProfile = { navController.navigate(Profile) },
                        onNavigateToForge = { navController.navigate(Forge) },
                        onNavigateToShop = { navController.navigate(Shop) },
                        onNavigateToPvp = { navController.navigate(Pvp) },
                        onNavigateToShadowBroker = { navController.navigate(ShadowBroker) },
                        onNavigateToEidosGates = { navController.navigate(EidosGates) },
                        onNavigateToCodex = { navController.navigate(Codex) },
                        onBuyMetaUpgrade = { mainViewModel.buyMetaUpgrade(it) }
                    )
                }
                composable<Profile> {
                    androidx.compose.runtime.LaunchedEffect(Unit) {
                        mainViewModel.checkAndGenerateRadioMessages()
                    }
                    ProfileScreen(
                        player = player,
                        inventory = inventory,
                        radioMessages = radioMessages,
                        unclaimedRadioMessagesCount = unclaimedRadioMessagesCount,
                        onClaimRadioMessage = { mainViewModel.claimRadioMessageReward(it) },
                        onUpgradeSkill = { branch, index -> mainViewModel.upgradeSkill(branch, index) },
                        onRespecSkills = { mainViewModel.respecSkills() },
                        onRedeemReferralCode = { mainViewModel.redeemReferralCode(it) },
                        onSendSignal = { to, msg -> mainViewModel.sendSignalToOperator(to, msg) },
                        onClaimAchievement = { mainViewModel.claimAchievement(it) },
                        onTriggerTestLevelUp = { mainViewModel.triggerTestLevelUp() },
                        onBack = { navController.popBackStack() },
                        onNavigateToSettings = { navController.navigate(EidosSettings) }
                    )
                }
                composable<Inventory> {
                    InventoryScreen(
                        player = player,
                        inventory = inventory,
                        allItemsMetadata = mainViewModel.getAllItemsMetadata(),
                        activeRaidSession = raidSession,
                        onReturnToRaid = { navController.navigate(Raid) { launchSingleTop = true } },
                        onEquip = { mainViewModel.equip(it) },
                        onUnequip = { mainViewModel.unequip(it) },
                        onUseConsumable = { mainViewModel.useConsumable(it) },
                        onStartDecryption = { mainViewModel.startDecryption(it) },
                        onInstantDecrypt = { mainViewModel.instantDecrypt(it) },
                        onClaimDecryptedCache = { mainViewModel.claimDecryptedCache(it) },
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<Raid> {
                    RaidScreen(
                        session = raidSession,
                        player = player,
                        logs = logs,
                        anomalyData = mainViewModel.getAnomalyData(raidSession?.current_anomaly_id),
                        inventory = inventory,
                        allItemsMetadata = mainViewModel.getAllItemsMetadata(),
                        overdriveCharge = overdriveCharge,
                        overchargeTier = overchargeTier,
                        combatEventFlow = mainViewModel.combatEventFlow,
                        onNextStep = { mainViewModel.nextStep() },
                        onAnomalyChoice = { mainViewModel.handleAnomaly(it) },
                        onOpenInventory = { navController.navigate(Inventory) },
                        onExitRaid = { 
                            mainViewModel.endRaidWithSafeExtraction()
                            navController.navigate(Hub) { popUpTo(Raid) { inclusive = true } }
                        },
                        onBack = { navController.popBackStack() },
                        onStartRaid = { mainViewModel.startRaid() },
                        onScanSector = { mainViewModel.scanSector() },
                        onUseAbility = { mainViewModel.useActiveAbility() },
                        onTriggerOverdrive = { mainViewModel.triggerOverdrive() },
                        onBoostOvercharge = { mainViewModel.boostOvercharge() },
                        onUseConsumable = { mainViewModel.useConsumable(it) },
                        onAcceptMaxwellContract = { mainViewModel.acceptMaxwellContract(it) },
                        onBetDemonHp = { mainViewModel.betMaxwellDemonHp() },
                        onBetDemonBuffer = { mainViewModel.betMaxwellDemonBuffer() },
                        onIgnoreDemon = { mainViewModel.ignoreMaxwellDemon() },
                        onResolveHardGlitch = { chosen, correct -> mainViewModel.resolveHardGlitch(chosen, correct) }
                    )
                }
                composable<Forge> {
                    ForgeScreen(
                        player = player,
                        inventory = inventory,
                        allItemsMetadata = mainViewModel.getAllItemsMetadata(),
                        onDismantle = { mainViewModel.dismantle(it) },
                        onMerge = { mainViewModel.mergeItems(it.item_id) },
                        onCraft = { mainViewModel.craft(it) },
                        onRepairBC = { mainViewModel.repairBC(it) },
                        onRepairShards = { mainViewModel.repairShards(it) },
                        onRerollChip = { mainViewModel.rerollChipModifiers(it) },
                        onDataSlicer = { mainViewModel.applyDataSlicer(it) },
                        onQuantumTuner = { mainViewModel.applyQuantumTuner(it) },
                        onSocketPuncher = { mainViewModel.applySocketPuncher(it) },
                        onChromaticInjector = { mainViewModel.applyChromaticInjector(it) },
                        onVaalCorruption = { mainViewModel.applyVaalCorruption(it) },
                        onInsertChip = { item, index, chip -> mainViewModel.insertChipToEquipment(item, index, chip) },
                        onRemoveChip = { item, index -> mainViewModel.removeChipFromEquipment(item, index) },
                        onApplyCustomMod = { item, eq, cost, logMsg -> mainViewModel.applyCustomEquipmentMod(item, eq, cost, logMsg) },
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<Shop> {
                    val shopTab by mainViewModel.shopSelectedTab.collectAsStateWithLifecycle()
                    val shopSearch by mainViewModel.shopSearchQuery.collectAsStateWithLifecycle()
                    val fragmentsCount = inventory.find { it.item_id == "data_fragment" }?.quantity ?: 0
                    ShopScreen(
                        player = player,
                        items = mainViewModel.getAllItemsMetadata(),
                        selectedCategory = shopTab,
                        onCategoryChange = { mainViewModel.setShopSelectedTab(it) },
                        searchQuery = shopSearch,
                        onSearchQueryChange = { mainViewModel.setShopSearchQuery(it) },
                        onBuy = { mainViewModel.buyItem(it) },
                        onRollGacha = { mainViewModel.buyGachaRoll() },
                        onSynthesizeFragments = { mainViewModel.synthesizeFragments() },
                        dataFragmentsCount = fragmentsCount,
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<Pvp> {
                    val topPlayers by mainViewModel.topPlayers.collectAsStateWithLifecycle()
                    PvpScreen(
                        player = player,
                        phantoms = topPlayers,
                        onSetupDefense = { p1, p2, p3 -> mainViewModel.setupPvpDefense(p1, p2, p3) },
                        onBuyHardware = { hw -> mainViewModel.buyPvpHardware(hw) },
                        onActivateShield = { hours -> mainViewModel.activatePvpShield(hours) },
                        onActivateProxy = { hours -> mainViewModel.activatePvpProxy(hours) },
                        onExecuteRaid = { target, progs, isRevenge, onResult -> mainViewModel.executePvpRaid(target, progs, isRevenge, onResult) },
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<ShadowBroker> {
                    ShadowBrokerScreen(
                        player = player,
                        items = mainViewModel.getAllItemsMetadata(),
                        onBuy = { itemId, useBioCoins -> mainViewModel.buyShadowBrokerItem(itemId, useBioCoins) },
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<EidosGates> {
                    EidosGatesScreen(
                        player = player,
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<Codex> {
                    val bestiaryList by mainViewModel.bestiaryList.collectAsStateWithLifecycle()
                    val logs by mainViewModel.logs.collectAsStateWithLifecycle()
                    val codexCategory by mainViewModel.codexSelectedCategory.collectAsStateWithLifecycle()
                    CodexScreen(
                        player = player,
                        bestiaryList = bestiaryList,
                        logs = logs,
                        selectedMainCategory = codexCategory,
                        onCategoryChange = { mainViewModel.setCodexSelectedCategory(it) },
                        onBack = { navController.popBackStack() }
                    )
                }
                composable<EidosSettings> {
                    val authSession by mainViewModel.authSession.collectAsStateWithLifecycle()
                    val isAuthLoading by mainViewModel.isAuthLoading.collectAsStateWithLifecycle()
                    val authError by mainViewModel.authError.collectAsStateWithLifecycle()

                    SettingsScreen(
                        player = player,
                        authSession = authSession,
                        isAuthLoading = isAuthLoading,
                        authError = authError,
                        onLogin = { u, p -> mainViewModel.login(u, p) },
                        onRegister = { u, p -> mainViewModel.register(u, p) },
                        onLogout = { mainViewModel.logout() },
                        onSyncCloud = { mainViewModel.syncCloudProfile() },
                        onBuyPremium = { mainViewModel.buyPremium() },
                        onExport = { mainViewModel.exportData() },
                        onImport = { jsonData -> mainViewModel.importData(jsonData) },
                        onBack = { navController.popBackStack() },
                        onGrantAdminResources = { mainViewModel.grantAdminResources() },
                        onGrantGodKit = { mainViewModel.grantGodKit() },
                        onToggleAdminMode = { mainViewModel.toggleAdminMode(it) }
                    )
                }
            }
        }

        // --- JUICE UI OVERLAY ---
        CyberToastHost(toasts = toasts)

        levelUpEvent?.let { event ->
            LevelUpModalDialog(
                event = event,
                onDismiss = { mainViewModel.dismissLevelUp() }
            )
        }

        achievements.firstOrNull()?.let { achievement ->
            AchievementClaimDialog(
                achievement = achievement,
                onClaim = { mainViewModel.claimAchievement(achievement) },
                onDismiss = { mainViewModel.dismissAchievement(achievement.id) }
            )
        }

        activeLoot?.let { loot ->
            LootDropDialog(
                loot = loot,
                allItemsMetadata = mainViewModel.getAllItemsMetadata(),
                onClaim = { mainViewModel.dismissLoot() }
            )
        }
    }
}
