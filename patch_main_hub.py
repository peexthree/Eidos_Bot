import re

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

content = content.replace("onNavigateToShop = { navController.navigate(Shop) }", "onNavigateToShop = { navController.navigate(Shop) },\n                    onNavigateToPvp = { navController.navigate(Pvp) },\n                    onNavigateToAnomaly = { navController.navigate(Anomaly) },\n                    onNavigateToShadowBroker = { navController.navigate(ShadowBroker) }")

# Let's fix the HubScreen signature which might be broken if there were extra params or commas missing.
with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
