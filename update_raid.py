import re

with open('app/src/main/java/com/example/eidos/ui/screens/RaidScreen.kt', 'r') as f:
    text = f.read()

# Replace EventCard signature and body
start_pattern = r'@Composable\nfun EventCard\(session: RaidSession\?\) \{'
end_pattern = r'@Composable\nfun RaidControls\('

new_code = """@Composable
fun EventCard(session: RaidSession?, player: com.example.eidos.data.Player?) {
    val eventType = session?.next_event_type ?: "INITIALIZING"
    val enemyId = session?.current_enemy_id
    val enemyHp = session?.current_enemy_hp ?: 0
    val villain = com.example.eidos.data.GameData.VILLAINS.find { it.name == enemyId }
    
    val title = when {
        enemyId != null -> "⚠ ${villain?.name?.uppercase() ?: "ВРАГ"}"
        eventType == "anomaly" -> "⚡ АНОМАЛИЯ СИСТЕМЫ"
        eventType == "loot" -> "📦 ОБНАРУЖЕН ТАЙНИК"
        else -> "📡 СКАНИРОВАНИЕ СЛОЯ..."
    }
    
    val description = when {
        enemyId != null -> villain?.description ?: "Вражеская единица обнаружена."
        eventType == "anomaly" -> "Сработал протокол безопасности. Целостность сигнала под угрозой."
        eventType == "loot" -> "Зашифрованный контейнер данных излучает слабый сигнал."
        else -> "Нейро-связь стабильна. Продолжение спуска."
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(EidosGlass)
            .border(1.dp, Color.White.copy(alpha = 0.2f))
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            title,
            color = if (enemyId != null) EidosRed else EidosCyan,
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center
        )
        
        if (enemyId != null && villain != null) {
            Spacer(modifier = Modifier.height(16.dp))
            
            // Enemy Stats
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("ВРАГ", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text("АТК: ${villain.atk} | ЗАЩ: ${villain.def}", color = Color.White, fontSize = 12.sp)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("ВЫ", color = EidosCyan, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text("АТК: ${player?.attack ?: 0} | ЗАЩ: ${player?.defense ?: 0}", color = Color.White, fontSize = 12.sp)
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            Text("СИГНАЛ ВРАГА: $enemyHp / ${villain.hp}", color = EidosRed, fontSize = 12.sp)
            LinearProgressIndicator(
                progress = { (enemyHp.toFloat() / villain.hp.toFloat()).coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth().height(4.dp),
                color = EidosRed
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        val displayedDescription = ghostTyping(description, speed = if (enemyId != null) 5L else 15L)
        Text(
            displayedDescription,
            color = Color.White.copy(alpha = 0.7f),
            fontSize = 14.sp,
            textAlign = TextAlign.Center,
            modifier = Modifier.heightIn(min = 60.dp)
        )
    }
}

"""

new_text = re.sub(start_pattern + r'.*?(?=@Composable\nfun RaidControls\()', new_code, text, flags=re.DOTALL)

# Also update the call to EventCard in RaidScreen
new_text = new_text.replace('EventCard(session)', 'EventCard(session, player)')

with open('app/src/main/java/com/example/eidos/ui/screens/RaidScreen.kt', 'w') as f:
    f.write(new_text)

