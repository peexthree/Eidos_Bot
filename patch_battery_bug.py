with open('modules/services/raid.py', 'r') as f:
    text = f.read()

# session.get('hp', 0) -> s.get('signal', 0)
text = text.replace("int(session.get('hp', 0))", "int(s.get('signal', 0))")

with open('modules/services/raid.py', 'w') as f:
    f.write(text)
