with open('verify_updates.py', 'r') as f:
    content = f.read()

content = "import time\n" + content

with open('verify_updates.py', 'w') as f:
    f.write(content)
