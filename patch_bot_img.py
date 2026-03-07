import re

with open('bot.py', 'r') as f:
    content = f.read()

img_route = """
@app.route('/IMG/<path:path>', methods=['GET'])
def send_img(path):
    import os
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/IMG')
    return flask.send_from_directory(static_dir, path)
"""

if '@app.route(\'/IMG/<path:path>\'' not in content:
    content = content.replace("@app.route('/js/<path:path>', methods=['GET'])", img_route + "\n@app.route('/js/<path:path>', methods=['GET'])")

    with open('bot.py', 'w') as f:
        f.write(content)
    print("Patched bot.py successfully")
else:
    print("Already patched")
