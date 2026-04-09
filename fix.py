import json
with open('frontend_v2/package.json', 'r') as f:
    pkg = json.load(f)

pkg['dependencies']['vite'] = pkg['devDependencies']['vite']
pkg['dependencies']['@vitejs/plugin-react-swc'] = pkg['devDependencies']['@vitejs/plugin-react-swc']
pkg['dependencies']['vite-plugin-svgr'] = pkg['devDependencies']['vite-plugin-svgr']

with open('frontend_v2/package.json', 'w') as f:
    json.dump(pkg, f, indent=2)
