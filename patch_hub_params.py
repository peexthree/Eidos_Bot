import re

with open('app/src/main/java/com/example/eidos/ui/screens/HubScreen.kt', 'r') as f:
    content = f.read()

# Update signature
content = content.replace(
    "onNavigateToShop: () -> Unit\n) {",
    "onNavigateToShop: () -> Unit,\n    onNavigateToPvp: () -> Unit,\n    onNavigateToAnomaly: () -> Unit,\n    onNavigateToShadowBroker: () -> Unit\n) {"
)

# Find where to add buttons. Let's look for "ТЕРМИНАЛ (МАГАЗИН)" or similar.
# In HubScreen, there's probably a LazyVerticalGrid or Row with these buttons.

# Let's search for "onNavigateToShop" usage.
# We'll just replace one of the buttons or add below them.
