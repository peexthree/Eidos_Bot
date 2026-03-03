with open('modules/handlers/menu.py', 'r') as f:
    content = f.read()

content = content.replace(
"""        accel_status = f"\\n⚡️ Ускоритель: <b>АКТИВЕН ({rem_hours}ч)</b>"

        safe_name = html.escape(u['username'] or u['first_name'] or "Unknown")
        msg = (
            f"👤 <b>ПРОФИЛЬ: {safe_name}</b>\\n\"""",
"""        accel_status = f"\\n⚡️ Ускоритель: <b>АКТИВЕН ({rem_hours}ч)</b>"

        from modules.services.utils import get_vip_prefix
        safe_name = html.escape(u['username'] or u['first_name'] or "Unknown")
        vip_name = get_vip_prefix(uid, safe_name)
        msg = (
            f"<b>ПРОФИЛЬ: {vip_name}</b>\\n\""""
)

content = content.replace(
"""        if i <= 3:
            username = l.get('username')
            if username:
                display_name = f"@{username}"
            else:
                display_name = html.escape(l['first_name'] or "Unknown")
            header = f"{rank_icon} [{detail}] {display_name} <i>({path_icon})</i> — <b>{val}</b>"
            txt += f"{header}\\n"
        else:
            txt += f"<code>{i:<2} {name[:10]:<10} | {detail} | {val}</code>\\n"

    # Footer (Mirror)""",
"""        from modules.services.utils import get_vip_prefix
        # Custom data is fetched in get_leaderboard via JOIN
        custom_data = l.get('eidos_custom_data')

        if i <= 3:
            username = l.get('username')
            if username:
                display_name = f"@{username}"
            else:
                display_name = html.escape(l['first_name'] or "Unknown")

            vip_display = get_vip_prefix(l['uid'], display_name, custom_data=custom_data).replace('<b>', '').replace('</b>', '')
            header = f"{rank_icon} [{detail}] {vip_display} <i>({path_icon})</i> — <b>{val}</b>"
            txt += f"{header}\\n"
        else:
            vip_display = get_vip_prefix(l['uid'], name[:10], custom_data=custom_data).replace('<b>', '').replace('</b>', '')
            txt += f"<code>{i:<2} {vip_display:<10} | {detail} | {val}</code>\\n"

    # Footer (Mirror)"""
)

with open('modules/handlers/menu.py', 'w') as f:
    f.write(content)
