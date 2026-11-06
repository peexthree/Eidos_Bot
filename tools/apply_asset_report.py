import sys, io, os, re, json, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Usage: python apply_asset_report.py [path-to-report.json]
REPORT = sys.argv[1] if len(sys.argv) > 1 else 'D:/EDO/canva_raw/eidos_asset_report.json'
if not os.path.exists(REPORT):
    print('report not found:', REPORT)
    print('сохрани отчёт из инструмента в D:/EDO/canva_raw/eidos_asset_report.json')
    sys.exit(1)

rep = json.load(io.open(REPORT, encoding='utf-8'))
DRAW = 'D:/EDO/app/src/main/res/drawable'
DELETED = 'D:/EDO/canva_raw/_deleted'
os.makedirs(DELETED, exist_ok=True)

# Reverse maps: русское имя -> id
items_json = json.load(io.open('D:/EDO/app/src/main/assets/items.json', encoding='utf-8'))
ru_to_item_id = {v.get('name'): k for k, v in items_json.items() if isinstance(v, dict)}
vj = json.load(io.open('D:/EDO/app/src/main/assets/villains.json', encoding='utf-8'))
ru_to_monster_img = {it['name']: it['image'] for it in vj['villains']}

def find_file(base):
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        p = os.path.join(DRAW, base + ext)
        if os.path.exists(p):
            return p
    return None

def resolve_newname_id(new_name):
    """Русское имя из дропдауна -> resource id (item id или monster image id)."""
    if new_name in ru_to_item_id:
        return ru_to_item_id[new_name]
    if new_name in ru_to_monster_img:
        return ru_to_monster_img[new_name]
    # возможно пользователь ввёл уже готовый id
    if re.match(r'^[a-z0-9_]+$', new_name):
        return new_name
    return None

# --- 1. RENAMES: file -> правильная сущность ---
print('=== RENAMES ===')
for r in rep.get('rename', []):
    f = r['file']
    src = find_file(os.path.splitext(f)[0])
    if not src:
        print(f'  ! file not found: {f}')
        continue
    target_id = resolve_newname_id(r.get('newName', ''))
    if not target_id:
        print(f'  ! cannot resolve name "{r.get("newName")}" for {f} - пропустил')
        continue
    target_path = find_file(target_id)
    if target_path and os.path.normpath(target_path) != os.path.normpath(src):
        # Коллизия: целевой id уже занят другой картинкой -> SWAP
        swap_tmp = src + '.swap'
        shutil.move(src, swap_tmp)
        shutil.move(target_path, src)
        shutil.move(swap_tmp, target_path)
        print(f'  SWAP: {os.path.basename(src)} <-> {target_id}{os.path.splitext(target_path)[1]}')
    else:
        dst = os.path.join(DRAW, target_id + os.path.splitext(src)[1])
        shutil.move(src, dst)
        print(f'  RENAME: {os.path.basename(f)} -> {target_id}{os.path.splitext(dst)[1]}')

# --- 2. DELETES: мусор -> canva_raw/_deleted + проверка ссылок ---
print('=== DELETES ===')
code_refs = ''
for root, _, fs in os.walk('D:/EDO/app/src/main/java'):
    for fn in fs:
        try:
            code_refs += io.open(os.path.join(root, fn), encoding='utf-8').read()
        except Exception:
            pass
for f in rep.get('delete', []):
    src = find_file(os.path.splitext(f)[0])
    if not src:
        print(f'  ! not found: {f}')
        continue
    base = os.path.splitext(os.path.basename(src))[0]
    if base in code_refs:
        print(f'  !! {base} УПОМИНАЕТСЯ В КОДЕ - НЕ удаляю, требует ручной проводки')
        continue
    shutil.move(src, os.path.join(DELETED, os.path.basename(src)))
    print(f'  DELETED: {os.path.basename(src)} -> _deleted/')

# --- 3. CONFIRM: просто статистика ---
print(f'=== CONFIRM: {len(rep.get("confirm", []))} файлов подтверждено ===')
print('\nГотово. Пересборка: ./gradlew assembleDebug')
