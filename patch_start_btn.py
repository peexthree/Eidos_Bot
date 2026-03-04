with open("keyboards.py", "r") as f:
    content = f.read()

pattern = """def get_main_reply_keyboard(user):
    from telebot import types
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user.get('level', 1) >= 10:
        m.add(types.KeyboardButton('👁‍🗨 Врата Эйдоса'))
    else:
        m = types.ReplyKeyboardRemove()
    return m"""

replacement = """def get_main_reply_keyboard(user):
    from telebot import types
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user.get('level', 1) >= 10:
        m.add(types.KeyboardButton('👁‍🗨 Врата Эйдоса'), types.KeyboardButton('/start'))
    else:
        m.add(types.KeyboardButton('/start'))
    return m"""

content = content.replace(pattern, replacement)

with open("keyboards.py", "w") as f:
    f.write(content)

print("Patched start button in keyboards.py")
