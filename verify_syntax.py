import sys
import os
import py_compile

def check_syntax(path):
    print(f"Checking syntax for: {path}")
    has_error = False
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    py_compile.compile(filepath, doraise=True)
                    # print(f"✅ {filepath}")
                except py_compile.PyCompileError as e:
                    print(f"❌ SYNTAX ERROR: {filepath}\n{e}")
                    has_error = True
                except Exception as e:
                    print(f"⚠️ ERROR: {filepath}\n{e}")
                    has_error = True
    return has_error

if __name__ == "__main__":
    error = check_syntax(".")
    if error:
        sys.exit(1)
    print("✅ All Python files passed syntax check.")
