import sys
from unittest.mock import MagicMock

# 1. Mock bot to return the actual function from decorator
mock_bot = MagicMock()
def decorator(func):
    return func
mock_bot.message_handler.return_value = decorator

sys.modules['modules.bot_instance'] = MagicMock()
sys.modules['modules.bot_instance'].bot = mock_bot

sys.modules['cache_db'] = MagicMock()
sys.modules['database'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['modules.services.combat'] = MagicMock()
sys.modules['modules.services.utils'] = MagicMock()
sys.modules['modules.services.user'] = MagicMock()

import modules.handlers.start as start_handler
import database as db

m = MagicMock()
m.from_user.id = 12345
m.text = '/start'

db.get_user.return_value = None
start_handler.start_handler(m)

print(f"db.add_user called: {db.add_user.called}")
