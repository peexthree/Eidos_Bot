import os

with open('tests/test_villains_image.py', 'r') as f:
    c = f.read()
c = c.replace("import logic", "import modules.services.utils as logic")
with open('tests/test_villains_image.py', 'w') as f:
    f.write(c)

with open('tests/test_villain_stats.py', 'r') as f:
    c = f.read()
c = c.replace("import logic", "import modules.services.utils as logic")
with open('tests/test_villain_stats.py', 'w') as f:
    f.write(c)

with open('tests/test_logic.py', 'r') as f:
    c = f.read()
c = c.replace("import logic", "import modules.services.utils as logic")
with open('tests/test_logic.py', 'w') as f:
    f.write(c)
