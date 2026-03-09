import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Adjust spacing from top so it sits lower
# <div className="relative z-10 flex flex-col h-full w-full max-w-sm mx-auto pt-24 pb-16 px-4"> -> pt-32 or pt-40
content = content.replace('pt-24', 'pt-32')

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)
