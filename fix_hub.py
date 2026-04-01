import re

with open('frontend_v2/src/pages/Hub.jsx', 'r') as f:
    content = f.read()

# Remove import
content = content.replace("import ProfileHeader from '../components/ProfileHeader';", "")

# Remove Profile Wrapper
content = re.sub(r'\{\/\* Profile Wrapper \*\/}.*?<\/div>', '', content, flags=re.DOTALL)

# Update nadpis.png
content = content.replace(
    "<img src=\"/video/nadpis.png\" style={{ position: 'absolute', top: '3%', left: '10%', width: '80%', objectFit: 'contain', zIndex: 10, pointerEvents: 'none' }} />",
    "<img src=\"/video/nadpis.png\" style={{ position: 'absolute', top: '3%', left: '15%', width: '70%', objectFit: 'contain', zIndex: 10, pointerEvents: 'none' }} />"
)

# Update signa.png
content = content.replace(
    "<img\n          src=\"/video/signa.png\"\n          className={btnHoverActiveStyle}\n          style={{ position: 'absolute', top: '15%', left: '4%', width: '28%', cursor: 'pointer', zIndex: 10 }}",
    "<img\n          src=\"/video/signa.png\"\n          className={btnHoverActiveStyle}\n          style={{ position: 'absolute', top: '23%', left: '4%', width: '25%', cursor: 'pointer', zIndex: 10 }}"
)

# Update sinxr.png
content = content.replace(
    "<img\n          src=\"/video/sinxr.png\"\n          className={btnHoverActiveStyle}\n          style={{ position: 'absolute', top: '15%', left: '33%', width: '34%', cursor: 'pointer', zIndex: 10 }}",
    "<img\n          src=\"/video/sinxr.png\"\n          className={btnHoverActiveStyle}\n          style={{ position: 'absolute', top: '15%', left: '33%', width: '34%', cursor: 'pointer', zIndex: 10 }}"
) # It's actually the same as original except the instruction says:
# Style: `{ position: 'absolute', top: '15%', left: '33%', width: '34%', cursor: 'pointer', zIndex: 10 }`

with open('frontend_v2/src/pages/Hub.jsx', 'w') as f:
    f.write(content)

print("Done")
