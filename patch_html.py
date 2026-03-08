with open('static/inventory.html', 'r') as f:
    content = f.read()

# Add view-nexus
nexus_html = """
        <section id="view-nexus" class="view active">
            <div id="nexus-grid-content" class="nexus-grid"></div>
        </section>
"""

# Remove active from inventory
content = content.replace('<section id="view-inventory" class="view active">', '<section id="view-inventory" class="view">')

# Insert nexus before inventory
content = content.replace('<section id="view-inventory" class="view">', nexus_html + '\n        <section id="view-inventory" class="view">')

with open('static/inventory.html', 'w') as f:
    f.write(content)
