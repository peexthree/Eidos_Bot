import sys
import traceback
from unittest.mock import MagicMock

# MOCK EVERYTHING
sys.modules['modules.bot_instance'] = MagicMock()
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

# Force it to run
print(f"Handler function: {start_handler.start_handler}")
start_handler.start_handler(m)

print(f"db.get_user.called: {db.get_user.called}")
