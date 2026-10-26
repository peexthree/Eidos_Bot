import re

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'r') as f:
    content = f.read()

features = """
    fun buyShadowBrokerItem(itemId: String) {
        viewModelScope.launch {
            repository.buyShadowBrokerItem(_uid.value, itemId)
        }
    }

    fun gambleHP() {
        viewModelScope.launch { repository.gambleHP(_uid.value) }
    }

    fun gambleLoot() {
        viewModelScope.launch { repository.gambleLoot(_uid.value) }
    }

    fun pvpWin() {
        viewModelScope.launch { repository.onPvpWin(_uid.value) }
    }

    fun pvpLose() {
        viewModelScope.launch { repository.onPvpLose(_uid.value) }
    }
"""

if "fun buyShadowBrokerItem" not in content:
    content = content.replace("fun buyItem", features + "\n    fun buyItem")

with open('app/src/main/java/com/example/eidos/ui/MainViewModel.kt', 'w') as f:
    f.write(content)
