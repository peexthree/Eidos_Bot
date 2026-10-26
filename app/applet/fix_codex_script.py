with open("app/src/main/java/com/example/eidos/ui/screens/CodexScreen.kt", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace .strip() with .trim()
content = content.replace(".strip()", ".trim()")

# 2. Add import for CyberGridOverlay if not present
import_target = "import com.example.eidos.data.*"
import_addition = "import com.example.eidos.data.*\nimport com.example.eidos.ui.components.CyberGridOverlay"
if import_addition not in content:
    content = content.replace(import_target, import_addition)

# 3. Replace BestiaryBookSection implementation
old_bestiary_start = "fun BestiaryBookSection("
# Let's find BestiaryBookSection and replace up to AchievementsSection
start_idx = content.find("fun BestiaryBookSection(")
end_idx = content.find("fun AchievementsSection(")

if start_idx != -1 and end_idx != -1:
    new_bestiary = """fun BestiaryBookSection(
    player: Player?,
    bestiaryList: List<BestiaryEntry>
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "👾 БЕСТИАРИЙ СИСТЕМЫ // БАЗА УГРОЗ",
                    color = EidosRed,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Здесь собраны все аномалии, глитчи и вирусные формы жизни, обнаруженные в глубинах Эйдоса. Уничтожайте врагов, чтобы открывать их данные и получать ценные трофеи.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        GameData.VILLAINS.forEach { villain ->
            val entry = bestiaryList.find { it.enemy_id == villain.name }
            val killed = entry?.killed_count ?: 0
            val unlocked = killed > 0 || (entry?.encountered == true)

            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (unlocked) EidosNeon.copy(alpha = 0.5f) else Color.DarkGray
                ),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(
                                text = if (unlocked) villain.name.take(2) else "🔒",
                                fontSize = 24.sp
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = if (unlocked) villain.name else "??? [НЕИЗВЕСТНО]",
                                    color = if (unlocked) Color.White else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "Тип: Аномалия • Уровень ${villain.level}",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Surface(
                            color = if (unlocked) EidosNeon.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (unlocked) EidosNeon else Color.DarkGray
                            ),
                            shape = CutCornerShape(4.dp)
                        ) {
                            Text(
                                text = "УБИТО: $killed",
                                color = if (unlocked) EidosNeon else Color.Gray,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    if (unlocked) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = villain.description,
                            color = Color.LightGray,
                            fontSize = 10.5.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 14.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("HP: ${villain.hp} | ATK: ${villain.atk} | DEF: ${villain.def}", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("XP: +${villain.xp} | Монет: +${villain.coin}", color = Color.Yellow, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                    } else {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "🔒 Сектор заблокирован. Уничтожьте хотя бы одну особь этого типа в Бездне, чтобы расшифровать досье.",
                            color = Color.Gray,
                            fontSize = 9.sp,
                            fontStyle = FontStyle.Italic
                        )
                    }
                }
            }
        }
    }
}

"""
    content = content[:start_idx] + new_bestiary + content[end_idx:]
    print("Successfully replaced BestiaryBookSection dynamically.")
else:
    print("Error locating BestiaryBookSection or AchievementsSection")

with open("app/src/main/java/com/example/eidos/ui/screens/CodexScreen.kt", "w", encoding="utf-8") as f:
    f.write(content)

print("CodexScreen update complete.")
