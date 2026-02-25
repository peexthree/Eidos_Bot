try:
    import modules.handlers.menu
    print("modules.handlers.menu imported successfully")
except ImportError as e:
    print(f"Error importing modules.handlers.menu: {e}")
except SyntaxError as e:
    print(f"SyntaxError in modules.handlers.menu: {e}")

try:
    import database
    print("database imported successfully")
except ImportError as e:
    print(f"Error importing database: {e}")
except SyntaxError as e:
    print(f"SyntaxError in database: {e}")
