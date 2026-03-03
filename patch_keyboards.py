with open('keyboards.py', 'r') as f:
    content = f.read()

content = content.replace(
"""            if not success:
                # Attack failed (Blocked)
                btn_text = f"🛡 {name} | ⛔️ Blocked ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            elif is_revenged:
                # Already revenged
                btn_text = f"✅ {name} | ♻️ {stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            else:
                # Active Target
                btn_text = f"🩸 {name} | -{stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}\"""",
"""            from modules.services.utils import get_vip_prefix
            # Strip tags for buttons
            vip_name = get_vip_prefix(a['attacker_uid'], name).replace('<b>', '').replace('</b>', '')

            if not success:
                # Attack failed (Blocked)
                btn_text = f"🛡 {vip_name} | ⛔️ Blocked ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            elif is_revenged:
                # Already revenged
                btn_text = f"✅ {vip_name} | ♻️ {stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}"
            else:
                # Active Target
                btn_text = f"🩸 {vip_name} | -{stolen} BC ({time_str})"
                cb = f"pvp_log_details_{log_id}\""""
)

with open('keyboards.py', 'w') as f:
    f.write(content)
