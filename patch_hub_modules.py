import re

with open('app/src/main/java/com/example/eidos/ui/screens/HubScreen.kt', 'r') as f:
    content = f.read()

# I will add a new Row with PvP and Anomaly below the existing one.
new_row = """
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    ModuleButton(
                        title = "СЕТЕВАЯ ВОЙНА",
                        subtitle = "PvP Взлом",
                        icon = Icons.Default.Warning,
                        color = EidosRed,
                        onClick = onNavigateToPvp,
                        modifier = Modifier.weight(1f)
                    )
                    ModuleButton(
                        title = "ТЕНЕВОЙ БРОКЕР",
                        subtitle = "Редкие вещи за XP",
                        icon = Icons.Default.Star,
                        color = Color(0xFF673AB7),
                        onClick = onNavigateToShadowBroker,
                        modifier = Modifier.weight(1f)
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    ModuleButton(
                        title = "АНОМАЛИЯ",
                        subtitle = "Сделка с Демоном",
                        icon = Icons.Default.Info,
                        color = Color(0xFF9C27B0),
                        onClick = onNavigateToAnomaly,
                        modifier = Modifier.weight(1f)
                    )
                }
"""

content = content.replace("                // Secondary System Actions", new_row + "\n                // Secondary System Actions")

with open('app/src/main/java/com/example/eidos/ui/screens/HubScreen.kt', 'w') as f:
    f.write(content)
