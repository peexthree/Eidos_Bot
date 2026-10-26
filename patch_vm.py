import re

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'r') as f:
    content = f.read()

pattern = r"fun getAnomalyData\(id: String\?\) = id\?\.let \{ repository\.getAnomaly\(it\) \}"
replacement = "fun getAnomalyData(id: String?) = id?.let { repository.getAnomaly(it) }\n    fun getAllItemsMetadata() = repository.getAllItemsMetadata()"
content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'w') as f:
    f.write(content)
