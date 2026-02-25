import sys
import traceback

files_to_check = [
    "database",
    "modules.services.combat",
    "modules.handlers.gameplay"
]

print("Starting syntax verification...")
has_error = False

for module in files_to_check:
    try:
        __import__(module)
        print(f"✅ {module}: OK")
    except ImportError as e:
        # Mock missing modules if needed for syntax check only?
        # But we are checking syntax, so import error is fine if it's dependency missing, but SyntaxError is bad.
        # Actually, SyntaxError is raised during import.
        # But if ImportError happens first (e.g. missing package), we might miss SyntaxError later in the file.
        # But Python parses the file before executing.
        print(f"⚠️ {module}: Import Error ({e}) - Assuming syntax is OK if error is not SyntaxError")
    except SyntaxError as e:
        print(f"❌ {module}: SYNTAX ERROR: {e}")
        has_error = True
    except Exception as e:
        print(f"⚠️ {module}: Runtime Error during import ({e}) - Syntax likely OK")

if has_error:
    sys.exit(1)
print("Verification complete.")
