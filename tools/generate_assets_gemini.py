import sys, io, os, re, json, base64, time
import urllib.request, urllib.error

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- Read key: arg > local.properties > env ---
key = None
for a in sys.argv[1:]:
    if a.startswith('key='):
        key = a[4:]
if not key and os.path.exists('D:/EDO/local.properties'):
    for line in io.open('D:/EDO/local.properties', encoding='utf-8'):
        m = re.match(r'\s*GEMINI_API_KEY\s*=\s*(.+)', line)
        if m:
            key = m.group(1).strip().strip('"').strip("'")
            break
if not key:
    key = os.environ.get('GEMINI_API_KEY')
if not key:
    print('NO KEY: передай key=AIza... или впиши GEMINI_API_KEY в local.properties')
    sys.exit(1)
print('key found:', key[:10] + '...')

# --- Load spec ---
import csv
spec = list(csv.DictReader(io.open('D:/EDO/docs/canva_generation_spec.csv', encoding='utf-8')))
print('spec assets:', len(spec))

RAW = 'D:/EDO/canva_raw'
os.makedirs(RAW, exist_ok=True)

# Skip already generated
todo = [r for r in spec if not any(
    os.path.exists(os.path.join(RAW, r['filename'] + e)) for e in ('.png', '.jpg', '.jpeg', '.webp'))]
print('to generate:', len(todo))

# --- Image generation models to try in order ---
MODELS = [
    'gemini-2.5-flash-image',      # nano banana
    'gemini-2.0-flash-exp',        # experimental with image output
]

def gen_image(model, prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    cands = data.get('candidates', [])
    if not cands:
        return None, 'no candidates: ' + json.dumps(data)[:200]
    parts = cands[0].get('content', {}).get('parts', [])
    for p in parts:
        if 'inlineData' in p:
            return base64.b64decode(p['inlineData']['data']), None
    return None, 'no image part: ' + json.dumps(parts)[:200]

ok, fail = 0, 0
model_found = None
for r in todo:
    name, prompt = r['filename'], r['prompt']
    done = False
    for model in MODELS:
        if model_found and model != model_found:
            continue  # after first success stick to the working model
        try:
            img, err = gen_image(model, prompt)
            if img:
                dst = os.path.join(RAW, name + '.png')
                io.open(dst, 'wb').write(img)
                print(f'  + {name} [{model}] {len(img)//1024} KB')
                ok += 1
                model_found = model
                done = True
                break
            else:
                print(f'  ! {name} [{model}]: {err[:120]}')
                if 'not found' in (err or '') or 'not supported' in (err or ''):
                    continue  # try next model
                fail += 1
                break
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')[:200]
            print(f'  ! {name} [{model}]: HTTP {e.code} {body[:120]}')
            if e.code in (404, 400):
                continue  # model unavailable for this key - try next
            if e.code == 429:
                print('  rate limited - sleep 30s and retry once')
                time.sleep(30)
                fail += 1
                break
            fail += 1
            break
        except Exception as e:
            print(f'  ! {name} [{model}]: {e}')
            fail += 1
            break
    if not done and not model_found:
        pass
    time.sleep(2)

print(f'DONE: ok={ok} fail={fail}')
if ok:
    print('Теперь запусти интеграцию: python tools/integrate_canva_assets.py')
