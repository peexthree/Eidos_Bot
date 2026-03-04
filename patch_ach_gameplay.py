with open("modules/handlers/gameplay.py", "r") as f:
    content = f.read()

# Replace protocol
old_proto = """            ach_text = ""
            new_achs = check_achievements(uid)
            if new_achs:
                for a in new_achs:
                    ach_text += f"\\n🏆 <b>ДОСТИЖЕНИЕ: {a['name']}</b> (+{a['xp']} XP)"

            final_txt = f"💠 <b>СИНХРОНИЗАЦИЯ:</b>\\n\\n{txt}{reward_text}\\n\\n⚡️ +{xp} XP{ach_text}"
            threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()"""

new_proto = """            new_achs = check_achievements(uid)
            if new_achs:
                for a in new_achs:
                    bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО: {a['name']}</b>\\n(+{a['xp']} XP)", parse_mode="HTML")

            final_txt = f"💠 <b>СИНХРОНИЗАЦИЯ:</b>\\n\\n{txt}{reward_text}\\n\\n⚡️ +{xp} XP"
            threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()"""
content = content.replace(old_proto, new_proto)

# Replace signal
old_sig = """             ach_text = ""
             new_achs = check_achievements(uid)
             if new_achs:
                 for a in new_achs:
                     ach_text += f"\\n🏆 <b>ДОСТИЖЕНИЕ: {a['name']}</b> (+{a['xp']} XP)"

             final_txt = f"📡 <b>СИГНАЛ:</b>\\n\\n{txt}{reward_text}\\n\\n⚡️ +{xp} XP{ach_text}"
             threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()"""

new_sig = """             new_achs = check_achievements(uid)
             if new_achs:
                 for a in new_achs:
                     bot.send_message(uid, f"🏆 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО: {a['name']}</b>\\n(+{a['xp']} XP)", parse_mode="HTML")

             final_txt = f"📡 <b>СИГНАЛ:</b>\\n\\n{txt}{reward_text}\\n\\n⚡️ +{xp} XP"
             threading.Thread(target=loading_effect, args=(call.message.chat.id, call.message.message_id, final_txt, kb.back_button(), final_img)).start()"""
content = content.replace(old_sig, new_sig)

with open("modules/handlers/gameplay.py", "w") as f:
    f.write(content)
