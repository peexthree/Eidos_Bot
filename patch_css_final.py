import re

with open('static/css/style.css', 'r') as f:
    content = f.read()

# Fix Jpx); if it exists (though grep didn't find it, let's be safe)
content = content.replace("Jpx);", "15px);")

# Update .views-container or #views-container padding
# We previously added:
# #views-container {
#     padding-top: 110px;
#     padding-bottom: 140px;
#     position: relative;
# }
if "padding-top: 110px;" in content:
    content = content.replace("padding-top: 110px;", "padding-top: 90px;")
if "padding-bottom: 140px;" in content:
    content = content.replace("padding-bottom: 140px;", "padding-bottom: 20px;")

with open('static/css/style.css', 'w') as f:
    f.write(content)

print("CSS cleaned and adjusted")
