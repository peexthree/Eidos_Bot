import re

with open('app/src/main/java/com/example/eidos/ui/screens/HubScreen.kt', 'r') as f:
    content = f.read()

content = content.replace("onNavigateToShop: () -> Unit\n) {", "onNavigateToShop: () -> Unit,\n    onNavigateToPvp: () -> Unit,\n    onNavigateToAnomaly: () -> Unit,\n    onNavigateToShadowBroker: () -> Unit\n) {")

with open('app/src/main/java/com/example/eidos/ui/screens/HubScreen.kt', 'w') as f:
    f.write(content)
