import re

with open('app/src/main/java/com/example/eidos/ui/screens/ShopScreen.kt', 'r') as f:
    content = f.read()

# Add missing import
content = content.replace("import com.example.eidos.data.Player", "import com.example.eidos.data.Player\nimport com.example.eidos.data.GameRepository.ItemMetadata\nimport androidx.compose.runtime.*")
content = content.replace("fun ShopScreen(\n    player: Player?,\n    onBuy: (String) -> Unit,\n    onBack: () -> Unit\n) {", "fun ShopScreen(\n    player: Player?,\n    items: List<ItemMetadata>,\n    onBuy: (String) -> Unit,\n    onBack: () -> Unit\n) {")

shop_body = """
    val amberColor = Color(0xFFFFB300)
    var selectedCategory by remember { mutableStateOf("weapon") }
    val categories = listOf("weapon" to "ОРУЖИЕ", "armor" to "БРОНЯ", "head" to "ШЛЕМЫ", "consumable" to "РАСХОДНИКИ")
    val filteredItems = items.filter { it.type == selectedCategory }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ЧЕРНЫЙ РЫНОК", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 16.sp) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = amberColor)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Black
    ) { innerPadding ->
        Column(modifier = Modifier.padding(innerPadding).fillMaxSize()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(EidosGlass)
                    .border(1.dp, amberColor.copy(alpha = 0.3f))
                    .padding(16.dp)
            ) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("БАЛАНС:", color = Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text("${player?.biocoin ?: 0} BC", color = amberColor, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                }
            }
            ScrollableTabRow(
                selectedTabIndex = categories.indexOfFirst { it.first == selectedCategory },
                containerColor = Color.Black,
                contentColor = amberColor,
                edgePadding = 8.dp
            ) {
                categories.forEach { (catId, catName) ->
                    Tab(
                        selected = selectedCategory == catId,
                        onClick = { selectedCategory = catId },
                        text = { Text(catName, fontSize = 12.sp, fontWeight = FontWeight.Bold) }
                    )
                }
            }
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(filteredItems) { item ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = EidosGlass),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.1f)),
                        shape = androidx.compose.foundation.shape.CutCornerShape(8.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(item.name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(item.description, color = Color.Gray, fontSize = 11.sp, lineHeight = 14.sp)
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("${item.price} BC", color = amberColor, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Button(
                                onClick = { onBuy(item.id) },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = amberColor.copy(alpha = 0.15f),
                                    disabledContainerColor = Color.DarkGray.copy(alpha = 0.1f)
                                ),
                                enabled = (player?.biocoin ?: 0) >= item.price,
                                border = androidx.compose.foundation.BorderStroke(1.dp, if ((player?.biocoin ?: 0) >= item.price) amberColor else Color.DarkGray),
                                shape = androidx.compose.foundation.shape.CutCornerShape(4.dp),
                                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                            ) {
                                Text("КУПИТЬ", color = if ((player?.biocoin ?: 0) >= item.price) amberColor else Color.Gray, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

pattern = r"    val shopItems = listOf\(.*?    val amberColor = Color\(0xFFFFB300\).*?}\n\n}"
content = re.sub(pattern, shop_body, content, flags=re.DOTALL)
content = re.sub(r"data class ShopItem\(val id: String, val name: String, val price: Int, val desc: String\)", "", content)

with open('app/src/main/java/com/example/eidos/ui/screens/ShopScreen.kt', 'w') as f:
    f.write(content)
