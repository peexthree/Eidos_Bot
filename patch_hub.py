import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Replace main wrapper style
old_wrapper = """    <div style={{
      aspectRatio: '9 / 16',
      width: '100%',
      maxHeight: '100vh',
      position: 'relative',
      margin: '0 auto',
      overflow: 'hidden'
    }}>"""

new_wrapper = """    <div style={{
      position: 'relative',
      width: '100vw',
      maxWidth: '500px',
      aspectRatio: '9 / 16',
      margin: '0 auto',
      overflow: 'hidden',
      backgroundColor: '#000'
    }}>"""

content = content.replace(old_wrapper, new_wrapper)

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)
