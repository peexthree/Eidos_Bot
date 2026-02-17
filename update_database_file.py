import os

with open('database.py', 'r') as f:
    lines = f.readlines()

# Definition of populate_content
populate_func = '''
def populate_content():
    """Заполнение базы контентом для уровней 5+"""
    from content_presets import CONTENT_DATA
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            for lvl, items in CONTENT_DATA.items():
                for item in items:
                    cur.execute("SELECT 1 FROM content WHERE text = %s", (item['text'],))
                    if not cur.fetchone():
                        cur.execute("INSERT INTO content (type, path, text, level) VALUES (%s, %s, %s, %s)",
                                    (item['type'], item['path'], item['text'], lvl))
                        print(f"/// ADDED CONTENT LVL {lvl}: {item['text'][:20]}...")
            conn.commit()
    except Exception as e:
        print(f"/// CONTENT POPULATION ERROR: {e}")
    finally: conn.close()
'''

# Append function to end of file
lines.append(populate_func)

# Insert call inside init_db
# Find line 124 (index 123) and check if it is conn.close()
if "conn.close()" in lines[123]:
    lines.insert(124, "    populate_content()\n")
else:
    print("Warning: Line 124 is not conn.close(). Searching for it.")
    for i, line in enumerate(lines):
        if line.strip() == "conn.close()" and line.startswith("    conn.close()"):
            # This is likely inside init_db as it is the first function
            lines.insert(i+1, "    populate_content()\n")
            print(f"Inserted at line {i+2}")
            break

with open('database.py', 'w') as f:
    f.writelines(lines)
