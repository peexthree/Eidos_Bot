import os
import sys

for filename in os.listdir('tests'):
    if filename.endswith('.py') and not filename.startswith('__'):
        filepath = os.path.join('tests', filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Mock openai, telebot, etc
        if 'sys.modules["openai"] = MagicMock()' not in content:
            content = "import sys\nfrom unittest.mock import MagicMock\nsys.modules['openai'] = MagicMock()\nsys.modules['sentry_sdk'] = MagicMock()\nsys.modules['sentry_sdk.integrations'] = MagicMock()\nsys.modules['sentry_sdk.integrations.flask'] = MagicMock()\nsys.modules['flask'] = MagicMock()\nsys.modules['telebot'] = MagicMock()\nsys.modules['telebot.types'] = MagicMock()\nsys.modules['telebot.apihelper'] = MagicMock()\n" + content
            with open(filepath, 'w') as f:
                f.write(content)

print("Tests patched.")
