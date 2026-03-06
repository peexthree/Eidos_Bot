with open("modules/handlers/menu.py", "r") as f:
    text = f.read()

import re
text = text.replace('db.get_state(m.from_user.id) == "await_dossier_search"', 'cache_db.get_cached_user_state(m.from_user.id) == "await_dossier_search"')
text = text.replace('db.get_state(m.from_user.id) and str(db.get_state(m.from_user.id)).startswith("await_dossier_msg_")', 'str(cache_db.get_cached_user_state(m.from_user.id) or "").startswith("await_dossier_msg_")')

text = text.replace('db.set_state(uid, "await_dossier_search")', 'db.set_state(uid, "await_dossier_search"); cache_db.clear_cache(uid)')
text = text.replace('db.delete_state(uid)\n        return', 'db.delete_state(uid); cache_db.clear_cache(uid)\n        return')
text = text.replace('db.delete_state(uid)\n\n    msg = bot.send_message', 'db.delete_state(uid); cache_db.clear_cache(uid)\n\n    msg = bot.send_message')

text = text.replace('db.set_state(uid, f"await_dossier_msg_{target_uid}")', 'db.set_state(uid, f"await_dossier_msg_{target_uid}"); cache_db.clear_cache(uid)')
text = text.replace('db.delete_state(uid)\n    except:', 'db.delete_state(uid); cache_db.clear_cache(uid)\n    except:')
text = text.replace('db.delete_state(uid)\n\n    safe_msg = ', 'db.delete_state(uid); cache_db.clear_cache(uid)\n\n    safe_msg = ')


with open("modules/handlers/menu.py", "w") as f:
    f.write(text)
print("done")
