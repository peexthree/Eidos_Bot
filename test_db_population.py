try:
    import database
    print("Database module imported successfully.")
    if hasattr(database, 'populate_content'):
        print("populate_content function exists.")
    else:
        print("populate_content function missing.")
except Exception as e:
    print(f"Error importing database: {e}")
