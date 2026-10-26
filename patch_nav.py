import re

with open('app/src/main/java/com/example/eidos/Navigation.kt', 'r') as f:
    content = f.read()

nav_objects = """
@Serializable object Pvp
@Serializable object Anomaly
@Serializable object ShadowBroker
"""
content = content + "\n" + nav_objects

with open('app/src/main/java/com/example/eidos/Navigation.kt', 'w') as f:
    f.write(content)
