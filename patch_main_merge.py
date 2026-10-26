import re

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

content = content.replace("onDismantle = { mainViewModel.dismantle(it) },", "onDismantle = { mainViewModel.dismantle(it) },\n                    onMerge = { mainViewModel.mergeItems(it.item_id) },")

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
