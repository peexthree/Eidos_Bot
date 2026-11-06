import sys, io, os, re, json, subprocess, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

RAW = 'D:/EDO/canva_raw'
DRAWABLE = 'D:/EDO/app/src/main/res/drawable'
VILLAINS = 'D:/EDO/app/src/main/assets/villains.json'
FFMPEG = 'ffmpeg'

spec = []
with io.open('D:/EDO/docs/canva_generation_spec.csv', encoding='utf-8') as fh:
    import csv
    spec = list(csv.DictReader(fh))
spec_names = {r['filename'] for r in spec}

# 1. Собираем файлы из canva_raw и матчим по имени (любое расширение)
found = {}
for f in os.listdir(RAW):
    base, ext = os.path.splitext(f)
    if base in spec_names and ext.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
        found[base] = os.path.join(RAW, f)

print(f'matched {len(found)} of {len(spec_names)} spec files')
if not found:
    print('nothing to integrate: put Canva downloads into D:/EDO/canva_raw/')
    sys.exit(0)

# 2. Конвертация: jpg, длинная сторона 768, качество 4 (визуально ~85)
integrated = []
for base, src in sorted(found.items()):
    dst = os.path.join(DRAWABLE, base + '.jpg')
    cmd = [FFMPEG, '-y', '-i', src, '-vf', "scale='min(768,iw)':-2", '-q:v', '4', dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(dst):
        size_kb = os.path.getsize(dst) // 1024
        integrated.append((base, size_kb))
        print(f'  + {base}.jpg ({size_kb} KB)')
    else:
        print(f'  ! FAILED {base}: {r.stderr[-200:] if r.stderr else r.returncode}')

# 3. villains.json: указываем новым элитным врагам их арты
vj = json.load(io.open(VILLAINS, encoding='utf-8'))
integrated_names = {b for b, _ in integrated}
vmap = {
    'Каскадный Сбой': 'monster_20',
    'Отключённый': 'monster_21',
    'Ткач Паутин': 'monster_22',
    'Магнит Внимания': 'monster_23',
    'Обратная Волна': 'monster_24',
    'Монолит Ядра': 'monster_25',
}
updated = 0
for it in vj['villains']:
    for ru, img in vmap.items():
        if it['name'] == f'🖼 {ru}' or it['name'].endswith(ru) or ru in it['name']:
            if img in integrated_names and it['image'] != img:
                it['image'] = img
                updated += 1
io.open(VILLAINS, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(vj, ensure_ascii=False, indent=2))
print(f'villains.json updated: {updated} image refs')

print(f'DONE: {len(integrated)} integrated. Пересобери APK: ./gradlew assembleDebug')
