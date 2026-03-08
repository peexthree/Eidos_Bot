import re

with open('database.py', 'r') as f:
    content = f.read()

# Replace get_user
new_get_user = """def get_user(uid, cursor=None):
    def _execute_logic(cur, uid):
        try:
            cur.execute("SELECT * FROM players WHERE uid = %s", (uid,))
            res = cur.fetchone()
            if res:
                if hasattr(res, 'keys'):
                    raw_dict = dict(res)
                else:
                    cols = [desc[0] for desc in cur.description]
                    raw_dict = dict(zip(cols, res))

                sanitized = _sanitize_player_data(raw_dict)
                # Ensure core fields have defaults
                sanitized['xp'] = sanitized.get('xp') or 0
                sanitized['biocoin'] = sanitized.get('biocoin') or 0
                sanitized['level'] = sanitized.get('level') or 1
                return sanitized
            return None
        except Exception as e:
            print(f"/// DB GET_USER ERROR: {e}")
            raise e

    if cursor:
        return _execute_logic(cursor, uid)
    else:
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            if not cur: return None
            return _execute_logic(cur, uid)"""

content = re.sub(r'def get_user\(uid, cursor=None\):.*?return _execute_logic\(cur, uid\)', new_get_user, content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(content)
