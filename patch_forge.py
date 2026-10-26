import re

with open('app/src/main/java/com/example/eidos/ui/screens/ForgeScreen.kt', 'r') as f:
    content = f.read()

# Update signature
content = content.replace("fun ForgeScreen(\n    inventory: List<InventoryItem>,\n    onDismantle: (InventoryItem) -> Unit,", "fun ForgeScreen(\n    inventory: List<InventoryItem>,\n    onDismantle: (InventoryItem) -> Unit,\n    onMerge: (InventoryItem) -> Unit,")

content = content.replace("DismantleSection(inventory, onDismantle)", "DismantleSection(inventory, onDismantle, onMerge)")
content = content.replace("fun DismantleSection(inventory: List<InventoryItem>, onDismantle: (InventoryItem) -> Unit)", "fun DismantleSection(inventory: List<InventoryItem>, onDismantle: (InventoryItem) -> Unit, onMerge: (InventoryItem) -> Unit)")

button_code = """
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        if (item.quantity >= 3) {
                            Button(
                                onClick = { onMerge(item) },
                                colors = ButtonDefaults.buttonColors(containerColor = EidosNeon.copy(alpha = 0.2f)),
                                border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon),
                                shape = androidx.compose.foundation.shape.CutCornerShape(4.dp),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                            ) {
                                Text("СИНТЕЗ (3)", color = EidosNeon, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                        Button(
                            onClick = { onDismantle(item) },
                            colors = ButtonDefaults.buttonColors(containerColor = EidosRed.copy(alpha = 0.2f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed),
                            shape = androidx.compose.foundation.shape.CutCornerShape(4.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                        ) {
                            Text("РАЗОБРАТЬ", color = EidosRed, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                    }
"""

content = re.sub(
    r"Button\(\s*onClick = \{ onDismantle\(item\) \},.*?\{.*?\}",
    button_code.strip(),
    content,
    flags=re.DOTALL
)

with open('app/src/main/java/com/example/eidos/ui/screens/ForgeScreen.kt', 'w') as f:
    f.write(content)
