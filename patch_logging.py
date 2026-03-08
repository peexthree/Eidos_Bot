with open("modules/services/ai_worker.py", "r") as f:
    content = f.read()

content = content.replace("        import logging\n", "")

with open("modules/services/ai_worker.py", "w") as f:
    f.write(content)
