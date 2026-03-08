import re

with open('static/css/style.css', 'r') as f:
    content = f.read()

css_additions = """
/* ====== MICRO-ANIMATIONS ====== */
.stat-up {
    animation: statUp 0.8s ease;
    text-shadow: 0 0 10px #00ff41;
}
.stat-down {
    animation: statDown 0.8s ease;
    text-shadow: 0 0 10px #ff003c;
}

@keyframes statUp {
    0% { transform: translateY(0); }
    50% { transform: translateY(-5px); color: #00ff41; }
    100% { transform: translateY(0); }
}
@keyframes statDown {
    0% { transform: translateX(0); }
    20% { transform: translateX(-2px); color: #ff003c; }
    40% { transform: translateX(2px); }
    60% { transform: translateX(-2px); }
    80% { transform: translateX(2px); }
    100% { transform: translateX(0); }
}

.overheatPulse {
    animation: overheatPulseAnim 1.5s infinite alternate;
}
@keyframes overheatPulseAnim {
    from { box-shadow: inset 0 0 10px rgba(255,102,0,0.5), 0 0 5px rgba(255,102,0,0.5); }
    to { box-shadow: inset 0 0 25px rgba(255,51,0,0.8), 0 0 15px rgba(255,51,0,0.8); border-color: #ff3300 !important; }
}
"""

if ".stat-up" not in content:
    content += css_additions

# Update #views-container padding
# Ensure #views-container padding respects padding-bottom: 140px; padding-top: 110px;
if "#views-container {" in content:
    content = re.sub(r'#views-container \{[^}]*\}',
                     '#views-container {\n    padding-top: 110px;\n    padding-bottom: 140px;\n    position: relative;\n}', content)
elif ".views-container" in content:
    content = re.sub(r'\.views-container \{[^}]*\}',
                     '.views-container {\n    padding-top: 110px;\n    padding-bottom: 140px;\n    position: relative;\n}', content)
else:
    content += "\n#views-container {\n    padding-top: 110px;\n    padding-bottom: 140px;\n    position: relative;\n}\n"


# Update modal overlay z-index
if ".modal-overlay {" in content:
    content = re.sub(r'\.modal-overlay \{([^\}]*z-index:\s*\d+;[^\}]*)\}',
                     lambda m: '.modal-overlay {' + re.sub(r'z-index:\s*\d+;', 'z-index: 90000;', m.group(1)) + '}',
                     content)

with open('static/css/style.css', 'w') as f:
    f.write(content)

print("CSS updated")
