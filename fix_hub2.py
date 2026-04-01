import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Remove Profile Wrapper properly
# Let's inspect again if it was removed
if '<ProfileHeader />' in content:
    content = re.sub(r'\{\/\*\s*Profile Wrapper\s*\*\/\}[\s\S]*?<\/div>', '', content)

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)
