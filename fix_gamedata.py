with open("app/src/main/java/com/example/eidos/data/GameData.kt", "r") as f:
    text = f.read()

text = text.replace("data class VillainStatic", "data class GameVillainData")
text = text.replace("VillainStatic(", "GameVillainData(")
text = text.replace("data class RandomEvent", "data class GameEventData")
text = text.replace("RandomEvent(", "GameEventData(")

with open("app/src/main/java/com/example/eidos/data/GameData.kt", "w") as f:
    f.write(text)
