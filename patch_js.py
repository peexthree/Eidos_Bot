import re

with open('static/js/app.js', 'r') as f:
    content = f.read()

# Replace getHeaders
old_headers = """function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': window.tg && tg.initData ? tg.initData : ''
    };
}"""

new_headers = """function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': window.tg && tg.initData ? tg.initData : (uid ? `query_id=mock&user=%7B%22id%22%3A${uid}%7D` : '')
    };
}"""

content = content.replace(old_headers, new_headers)

with open('static/js/app.js', 'w') as f:
    f.write(content)
