import sys
filepath = 'modules/handlers/gameplay.py'
with open(filepath, 'r') as f:
    content = f.read()

# Fix the broken f-string with double backslashes
content = content.replace('reward_text = f"\\n\\n', 'reward_text = f"\\n\\n')
# Wait, the issue is likely how bash/heredoc handled the double backslash in my previous cat command.
# Let's just use a more robust replacement.

# I will use a multi-line string for replacement to avoid escaping issues in the python script itself.
replacement_proto = r'''
            if glitch:
                xp = int(xp * glitch.get('xp_modifier', 1.5))
                txt = apply_zalgo_effect(txt, 1)
                final_img = glitch.get('image', final_img)
                reward_text = f"\n\n🌀 <b>{glitch['message']}</b>"

                # Apply effects/items
                upd_args = {}
                if glitch.get('effect'):
                    upd_args['anomaly_buff_type'] = glitch['effect']
                    upd_args['anomaly_buff_expiry'] = int(time.time() + glitch.get('effect_duration', 3600))
                    upd_args['is_glitched'] = True

                if glitch.get('reward_item'):
                    import database as db_mod # local import if needed
                    db.add_item_to_inventory(uid, glitch['reward_item'], 1)
                    reward_text += f"\n📦 <b>Получен предмет:</b> {glitch['reward_item']}"

                if upd_args:
                    db.update_user(uid, **upd_args)
'''

# The previous script broke it into `reward_text = f"` and then something else.
# Let's just find the broken part and fix it.
import re
content = re.sub(r'reward_text = f"\\n\\n', 'reward_text = f"\\n\\n', content) # Try to fix what's there

# Actually, I'll just rewrite the whole file with a clean version of the handler.
