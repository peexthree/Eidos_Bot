import re
with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

content = re.sub(r"onExport = \{.*?\},", "onExport = { mainViewModel.exportData() },", content)

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
