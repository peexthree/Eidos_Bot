import re

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

# Add imports for new screens
imports = """
import com.example.eidos.ui.screens.PvpScreen
import com.example.eidos.ui.screens.AnomalyScreen
import com.example.eidos.ui.screens.ShadowBrokerScreen
"""
content = content.replace("import com.example.eidos.ui.screens.SettingsScreen", imports + "\nimport com.example.eidos.ui.screens.SettingsScreen")

# Add serializable objects
serializables = """
@Serializable object Pvp
@Serializable object Anomaly
@Serializable object ShadowBroker
"""
content = content.replace("@Serializable object EidosSettings", serializables + "\n@Serializable object EidosSettings")

# Add composables
composables = """
            composable<Pvp> {
                PvpScreen(
                    player = player,
                    onWin = { mainViewModel.pvpWin() },
                    onLose = { mainViewModel.pvpLose() },
                    onBack = { navController.popBackStack() }
                )
            }
            composable<Anomaly> {
                AnomalyScreen(
                    player = player,
                    onGambleHP = { mainViewModel.gambleHP() },
                    onGambleLoot = { mainViewModel.gambleLoot() },
                    onBack = { navController.popBackStack() }
                )
            }
            composable<ShadowBroker> {
                ShadowBrokerScreen(
                    player = player,
                    items = mainViewModel.getAllItemsMetadata(),
                    onBuy = { mainViewModel.buyShadowBrokerItem(it) },
                    onBack = { navController.popBackStack() }
                )
            }
"""
content = content.replace("composable<EidosSettings> {", composables + "\n            composable<EidosSettings> {")

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
