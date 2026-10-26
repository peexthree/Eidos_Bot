import re

with open('app/src/main/java/com/example/eidos/MainActivity.kt', 'r') as f:
    content = f.read()

# I need to fix the Unresolved references for Pvp, Anomaly, ShadowBroker in MainActivity
# Maybe they weren't imported because I added them incorrectly
# Wait, they are objects, not screens, but the name is colliding or they are not defined outside the class properly, or not imported if they are declared in another file. 
# Ah, I added @Serializable object Pvp inside MainActivity.kt but where?
