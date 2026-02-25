try:
    import modules.services.combat
    print("modules.services.combat imported successfully")
except ImportError as e:
    print(f"Error importing modules.services.combat: {e}")
except SyntaxError as e:
    print(f"SyntaxError in modules.services.combat: {e}")

try:
    import database
    print("database imported successfully")
except ImportError as e:
    print(f"Error importing database: {e}")
except SyntaxError as e:
    print(f"SyntaxError in database: {e}")
