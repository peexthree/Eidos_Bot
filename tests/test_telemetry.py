import sys
from unittest.mock import MagicMock
sys.modules['openai'] = MagicMock()
sys.modules['sentry_sdk'] = MagicMock()
sys.modules['sentry_sdk.integrations'] = MagicMock()
sys.modules['sentry_sdk.integrations.flask'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['telebot'] = MagicMock()
sys.modules['telebot.types'] = MagicMock()
sys.modules['telebot.apihelper'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['psycopg2'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['requests'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()
import unittest
from unittest.mock import patch, MagicMock

class TestTelemetry(unittest.TestCase):
    @patch('builtins.print')
    def test_generate_eidos_response_telemetry(self, mock_print):
        from modules.services.ai_worker import generate_eidos_response_worker
        with patch('modules.services.ai_worker.cache_db.check_throttle', return_value=True):
             mock_bot = MagicMock()
             generate_eidos_response_worker(mock_bot, 1234, 5678, 'test_analysis')
             mock_print.assert_any_call("[AI WORKER] Started processing request for UID 5678", flush=True)
