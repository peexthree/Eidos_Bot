with open('logic.py', 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'msg_event = f"❤️' in line:
        print(f"Line {i+1}: {repr(line)}")
        print(f"Line {i+2}: {repr(lines[i+1])}")
