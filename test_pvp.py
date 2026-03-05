import re

with open('modules/services/pvp.py', 'r') as f:
    text = f.read()

lines = text.split('\n')
for i, l in enumerate(lines):
    if 'def perform_hack' in l:
        print(f"Line {i}: {l}")
    if 'def find_hack_target' in l:
        print(f"Line {i}: {l}")
