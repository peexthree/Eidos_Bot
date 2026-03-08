import re

with open('static/inventory.html', 'r') as f:
    content = f.read()

# Make sure we don't have bottom-nav (grep showed nothing, but double check)
content = re.sub(r'<nav class="bottom-nav">.*?</nav>', '', content, flags=re.DOTALL)

# Let's ensure <section id="view-nexus" class="view active"> has the proper structure from instructions:
# <section id="view-nexus" class="view-panel active">
#     <div class="nexus-grid" id="nexus-grid-tiles">
#     </div>
# </section>

# Current structure:
# <section id="view-nexus" class="view active">
#     <div id="nexus-grid-content" class="nexus-grid"></div>
# </section>

old_nexus = """<section id="view-nexus" class="view active">
            <div id="nexus-grid-content" class="nexus-grid"></div>
        </section>"""

new_nexus = """<section id="view-nexus" class="view-panel active">
            <div class="nexus-grid" id="nexus-grid-tiles"></div>
        </section>"""

content = content.replace(old_nexus, new_nexus)

with open('static/inventory.html', 'w') as f:
    f.write(content)

print("HTML Structure updated")
