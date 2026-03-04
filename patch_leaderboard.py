with open("database.py", "r") as f:
    content = f.read()

pattern = """    elif sort_by == 'spent':
        order_clause = "total_spent DESC, xp DESC, uid ASC"

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        # Using format string for ORDER BY is necessary as it cannot be parameterized directly.
        # sort_by is controlled by code logic, not user input directly (enum-like), so it's safe-ish.
        # Join with user_equipment to fetch eidos_shard custom_data
        query = f\"\"\"
            SELECT p.uid, p.first_name, p.username, COALESCE(p.xp, 0) as xp, COALESCE(p.level, 1) as level,
                   COALESCE(p.max_depth, 0) as max_depth, COALESCE(p.biocoin, 0) as biocoin, COALESCE(p.total_spent, 0) as total_spent, p.path,
                   ue.custom_data as eidos_custom_data
            FROM players p
            LEFT JOIN user_equipment ue ON p.uid = ue.uid AND ue.slot = 'eidos_shard'
            ORDER BY {order_clause.replace('uid', 'p.uid').replace('xp', 'p.xp').replace('level', 'p.level').replace('max_depth', 'p.max_depth').replace('biocoin', 'p.biocoin').replace('total_spent', 'p.total_spent')} LIMIT %s
        \"\"\""""

replacement = """    elif sort_by == 'spent':
        order_clause = "COALESCE(total_spent, 0) DESC, xp DESC, uid ASC"

    with db_cursor(cursor_factory=RealDictCursor) as cur:
        if not cur: return []
        # Using format string for ORDER BY is necessary as it cannot be parameterized directly.
        # sort_by is controlled by code logic, not user input directly (enum-like), so it's safe-ish.
        # Join with user_equipment to fetch eidos_shard custom_data
        query = f\"\"\"
            SELECT p.uid, p.first_name, p.username, COALESCE(p.xp, 0) as xp, COALESCE(p.level, 1) as level,
                   COALESCE(p.max_depth, 0) as max_depth, COALESCE(p.biocoin, 0) as biocoin, COALESCE(p.total_spent, 0) as total_spent, p.path,
                   ue.custom_data as eidos_custom_data
            FROM players p
            LEFT JOIN user_equipment ue ON p.uid = ue.uid AND ue.slot = 'eidos_shard'
            ORDER BY {order_clause.replace('uid', 'p.uid').replace('xp', 'p.xp').replace('level', 'p.level').replace('max_depth', 'p.max_depth').replace('biocoin', 'p.biocoin').replace('total_spent', 'p.total_spent')} LIMIT %s
        \"\"\""""

content = content.replace(pattern, replacement)

with open("database.py", "w") as f:
    f.write(content)

print("Patched leaderboard in database.py")
