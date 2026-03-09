import re

with open('static/css/style.css', 'r') as f:
    css_content = f.read()

# Add CSS for .modal-large-image, .full-size-img, and adapt modal

css_additions = """
/* ====== ENHANCED MODAL ====== */
.modal-large-image {
    width: 100%;
    max-height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    background: rgba(0, 0, 0, 0.4);
}

.full-size-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 0 5px rgba(255,255,255,0.2));
}

.icon-fallback {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.5;
}

.modal-stats {
    font-family: 'Share Tech Mono', monospace;
    font-size: 14px;
    margin-bottom: 10px;
    background: rgba(0,0,0,0.5);
    padding: 5px;
    border-radius: 4px;
    border: 1px solid rgba(102, 252, 241, 0.2);
    display: inline-block;
}

.modal-lore {
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px;
    color: #c5c6c7;
    text-align: left;
    background: rgba(0,0,0,0.3);
    padding: 10px;
    border-left: 2px solid var(--eidos-cyan);
    margin-top: 10px;
    max-height: 150px;
    overflow-y: auto;
    overscroll-behavior-y: contain;
}

.equipped-item img.full-size-img {
    max-width: 32px;
    max-height: 32px;
}
"""

if "ENHANCED MODAL" not in css_content:
    css_content += "\n" + css_additions

with open('static/css/style.css', 'w') as f:
    f.write(css_content)

print("CSS modal update applied.")
