import urllib.request

url = "https://github.com/peexthree/Eidos_Bot/actions/runs/41237308233"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    content = resp.read().decode("utf-8")
    idx = content.find("Process completed with exit code 1.")
    if idx != -1:
        start = max(0, idx - 1000)
        end = min(len(content), idx + 1000)
        print(content[start:end])
    else:
        print("Not found")
