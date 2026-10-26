import re

with open('app/src/main/java/com/example/eidos/ui/screens/RaidScreen.kt', 'r') as f:
    text = f.read()

# Add anomalyData to EventCard
text = text.replace(
    'fun EventCard(session: RaidSession?, player: com.example.eidos.data.Player?) {',
    'fun EventCard(session: RaidSession?, player: com.example.eidos.data.Player?, anomalyData: com.example.eidos.data.GameRepository.AnomalyEvent?) {'
)

# Use anomalyData.description in EventCard
desc_replacement = """        eventType == "anomaly" -> anomalyData?.description ?: "Сработал протокол безопасности. Целостность сигнала под угрозой." """
text = re.sub(r'eventType == "anomaly" -> ".*?"', desc_replacement, text)

# Pass anomalyData from RaidScreen to EventCard
text = text.replace(
    'EventCard(session, player)',
    'EventCard(session, player, anomalyData)'
)

with open('app/src/main/java/com/example/eidos/ui/screens/RaidScreen.kt', 'w') as f:
    f.write(text)

