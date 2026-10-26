import re

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'r') as f:
    content = f.read()

merge_logic = """
    fun mergeItems(itemId: String) {
        viewModelScope.launch {
            repository.mergeItems(_uid.value, itemId)
        }
    }
"""

if "fun mergeItems" not in content:
    content = content.replace("fun dismantle(", merge_logic + "\n    fun dismantle(")

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'w') as f:
    f.write(content)
