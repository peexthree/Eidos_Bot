import re

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'r') as f:
    content = f.read()

# Replace any usages like dao.addInventory with addInventory directly in GameRepository
content = content.replace("dao.addInventory", "addInventory")
content = content.replace("dao.removeInventory", "removeInventory")

with open('app/src/main/java/com/example/eidos/data/GameRepository.kt', 'w') as f:
    f.write(content)
