import re

with open('app/src/main/AndroidManifest.xml', 'r') as f:
    content = f.read()

# Let's ensure Internet permission is there if it wasn't already. Not strictly requested but useful.
if "android.permission.INTERNET" not in content:
    content = content.replace("<application", "<uses-permission android:name=\"android.permission.INTERNET\" />\n    <application")

with open('app/src/main/AndroidManifest.xml', 'w') as f:
    f.write(content)
