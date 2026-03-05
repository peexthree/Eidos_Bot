import re
with open('modules/services/combat.py', 'r') as f:
    text = f.read()

# Look for variable assignment of new_sig vs current_signal
print(len(re.findall(r'new_sig =', text)))
print(len(re.findall(r'current_signal =', text)))
