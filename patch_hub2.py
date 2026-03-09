import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Make sure background video is positioned right
old_video = """        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: 0
        }}"""

new_video = """        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: 0
        }}"""

content = content.replace(old_video, new_video)

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)
