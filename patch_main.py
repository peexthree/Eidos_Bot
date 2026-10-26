import re
with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

# First, remove all `items = mainViewModel.getAllItemsMetadata(),` everywhere
content = content.replace("                    items = mainViewModel.getAllItemsMetadata(),\n", "")
content = content.replace("items = mainViewModel.getAllItemsMetadata(),", "")

# Then, explicitly add it to ShopScreen
shop_pattern = r"composable<Shop> \{\n                ShopScreen\(\n                    player = player,"
shop_repl = "composable<Shop> {\n                ShopScreen(\n                    player = player,\n                    items = mainViewModel.getAllItemsMetadata(),"
content = re.sub(shop_pattern, shop_repl, content)

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
