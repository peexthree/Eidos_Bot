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
