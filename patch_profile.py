import re

with open('frontend_v2/src/components/ProfileHeader.jsx', 'r') as f:
    content = f.read()

# Instructions:
# шапку профиля немного ниже спусти на уровне фона города,и кнопки все тоже чуть ниже спустичтобы от нижнего экрана был небольшой отсутп и начинались кнопки..
# аватарку профиля сделай чуть больше и на ней почти не видно уровень его отцентрируй и чуть приподними

# Increase avatar size:
# width: w-16 -> w-20, height: h-16 -> h-20 (or larger)
# Center the level badge and raise it slightly:
# absolute -bottom-2 -right-2 -> absolute -bottom-1 left-1/2 -translate-x-1/2

content = content.replace('w-16 h-16', 'w-20 h-20')
content = content.replace('-bottom-2 -right-2', '-bottom-1 left-1/2 -translate-x-1/2')

with open('frontend_v2/src/components/ProfileHeader.jsx', 'w') as f:
    f.write(content)
