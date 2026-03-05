import re

with open('modules/services/raid.py', 'r') as f:
    text = f.read()

# Look for variable assignment
print(re.findall(r'session\.get\(\'hp\'', text))
print(re.findall(r'session', text))
print(re.findall(r's\[\'signal\'\]', text))
