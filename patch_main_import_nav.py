import re

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

# I added @Serializable object Pvp etc to MainActivity but they should be in Navigation.kt where others are.
# Wait, I previously patched MainActivity.kt and added:
# @Serializable object Pvp
# @Serializable object Anomaly
# @Serializable object ShadowBroker
# Let's remove them from MainActivity if they are there, or just add the import from Navigation.kt.

content = content.replace("@Serializable object Pvp", "")
content = content.replace("@Serializable object Anomaly", "")
content = content.replace("@Serializable object ShadowBroker", "")

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'w') as f:
    f.write(content)
