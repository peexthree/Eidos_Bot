import re

with open('static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Retina Hairlines
css = re.sub(
    r'(\.nexus-tile\s*\{[^\}]*)border:\s*1px\s*solid\s*([^;]+);',
    r'\1border: 1px solid \2;\n    border-width: 1px;\n',
    css
)

if '@media (-webkit-min-device-pixel-ratio: 2)' not in css:
    css += '''

/* ====== ULTRA OPTIMIZATIONS ====== */

/* 1. Retina Hairlines (Субпиксельные границы) */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
    .nexus-tile, .modal-content, .equip-slot, .inv-item {
        border-width: 0.5px !important;
    }
}
@media (-webkit-min-device-pixel-ratio: 3), (min-resolution: 288dpi) {
    .nexus-tile, .modal-content, .equip-slot, .inv-item {
        border-width: 0.33px !important;
    }
}
'''

# 3. 120Hz GPU Glassmorphism
css = css.replace(
    'backdrop-filter: blur(20px);',
    'backdrop-filter: blur(20px) saturate(150%);\n    transform: translateZ(0);\n    backface-visibility: hidden;\n    will-change: transform, opacity;'
)
css = css.replace(
    'backdrop-filter: blur(15px);',
    'backdrop-filter: blur(15px) saturate(120%);\n    transform: translateZ(0);\n    backface-visibility: hidden;\n    will-change: transform, opacity;'
)
css = css.replace(
    'backdrop-filter: blur(25px);',
    'backdrop-filter: blur(25px) saturate(180%);\n    transform: translateZ(0);\n    backface-visibility: hidden;\n    will-change: transform, opacity;'
)

# 4. OLED Anti-Smearing (Подавление черного шлейфа)
css = css.replace('--eidos-bg: #030405;', '--oled-deep-black: #020304;\n    --eidos-bg: var(--oled-deep-black);')

# 5. Bezel Bleed Integration
css = css.replace(
    'padding: calc(10px + var(--safe-top)) 15px 10px;',
    'padding-top: max(env(safe-area-inset-top), 24px);\n    padding-left: env(safe-area-inset-left, 15px);\n    padding-right: env(safe-area-inset-right, 15px);\n    padding-bottom: 10px;\n    background: radial-gradient(ellipse 150% 50% at 50% calc(env(safe-area-inset-top, 0px) * -0.5), rgba(102, 252, 241, 0.1) 0%, var(--eidos-glass) 100%);'
)

# 7. DVH Absolute Lock
css = css.replace('height: 100vh;', 'height: 100dvh;\n    min-height: -webkit-fill-available;')

if '-webkit-font-smoothing: antialiased;' not in css:
    css = css.replace('* {\n    box-sizing: border-box;', '* {\n    box-sizing: border-box;\n    -webkit-font-smoothing: antialiased;\n    -moz-osx-font-smoothing: grayscale;\n    text-rendering: optimizeLegibility;')


with open('static/css/style.css', 'w', encoding='utf-8') as f:
    f.write(css)
print("CSS patched with Ultra optimizations.")
