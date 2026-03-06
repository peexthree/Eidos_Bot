import re

with open('database.py', 'r') as f:
    db_content = f.read()

# 1. Update get_user to use Pydantic
new_get_user = """
def get_user(uid, cursor=None):
    from modules.schemas import User

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
                # Pydantic Validation & Fallback
                try:
                    user_model = User(**sanitized)
                    return user_model.model_dump() # Return dict to maintain legacy compatibility
                except Exception as model_err:
                    print(f"/// PYDANTIC VALIDATION ERROR for UID {uid}: {model_err}")
                    return sanitized # Fallback to dict
            return None
        except Exception as e:
            print(f"/// DB GET_USER ERROR: {e}")
            raise e

    if cursor:
        return _execute_logic(cursor, uid)
    else:
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            if not cur: return None
            return _execute_logic(cur, uid)
"""

db_content = re.sub(r'def get_user\(uid, cursor=None\):.*?(?=\ndef add_user)', new_get_user.strip() + '\n', db_content, flags=re.DOTALL)

with open('database.py', 'w') as f:
    f.write(db_content)
