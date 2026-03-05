import re
with open('modules/services/combat.py', 'r') as f:
    text = f.read()

# Replace all occurrences of new_sig with current_signal so that when it updates DB it passes the real health.
text = text.replace('new_sig =', 'current_signal =')
text = text.replace('new_sig <=', 'current_signal <=')

with open('modules/services/combat.py', 'w') as f:
    f.write(text)
